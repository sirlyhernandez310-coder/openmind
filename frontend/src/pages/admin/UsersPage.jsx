import { useCallback, useEffect, useMemo, useState } from 'react'
import { adminApi } from '../../api/admin'
import Alert from '../../components/Alert'
import Avatar from '../../components/Avatar'
import Icon from '../../components/Icon'
import PageHeader from '../../components/PageHeader'
import { ROLES, ROLE_LABELS } from '../../constants/roles'
import { useAuth } from '../../context/auth-context'
import { formatDate } from '../../format'

const ROLE_FILTERS = [{ value: '', label: 'Todos' }, ...Object.values(ROLES).map((r) => ({ value: r, label: ROLE_LABELS[r] }))]
const STATUS_FILTERS = [
  { value: '', label: 'Todas' },
  { value: 'active', label: 'Activas' },
  { value: 'inactive', label: 'Desactivadas' },
]
const ACTION_TONE = { USER_ACTIVATED: 'mint', USER_DEACTIVATED: 'coral', PROFESSIONAL_VERIFIED: 'mint', PROFESSIONAL_UNVERIFIED: 'sun' }
const dateTime = (value) => new Date(value).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })

// OM3-24 Gestionar usuarios
export default function UsersPage() {
  const { user: me } = useAuth()
  const [users, setUsers] = useState(null)
  const [logs, setLogs] = useState([])
  const [filters, setFilters] = useState({ q: '', role: '', status: '' })
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [pending, setPending] = useState(null) // usuario que se va a desactivar
  const [reason, setReason] = useState('')
  const [reasonError, setReasonError] = useState('')
  const [saving, setSaving] = useState(false)

  const loadLogs = () => adminApi.logs().then(setLogs).catch(() => {})

  const loadUsers = useCallback(
    () => adminApi.users(filters).then(setUsers).catch((err) => setError(err.message)),
    [filters],
  )

  useEffect(() => {
    const timer = setTimeout(loadUsers, filters.q ? 300 : 0)
    return () => clearTimeout(timer)
  }, [filters, loadUsers])

  useEffect(() => { loadLogs() }, [])

  const counts = useMemo(() => {
    const list = users ?? []
    return { total: list.length, active: list.filter((u) => u.is_active).length, inactive: list.filter((u) => !u.is_active).length }
  }, [users])

  const setFilter = (name, value) => setFilters((f) => ({ ...f, [name]: value }))

  const changeStatus = async (target, isActive, why = '') => {
    setSaving(true)
    setError('')
    setReasonError('')
    try {
      const updated = await adminApi.setStatus(target.id, isActive, why)
      setUsers((list) => list.map((u) => (u.id === updated.id ? updated : u)))
      setNotice(`La cuenta de ${updated.full_name} quedó ${updated.is_active ? 'activa' : 'desactivada'}. La acción quedó registrada.`)
      setPending(null)
      setReason('')
      loadLogs()
    } catch (err) {
      if (err.fieldErrors?.reason) setReasonError(err.fieldErrors.reason)
      else {
        setError(err.message)
        setPending(null)
      }
    } finally {
      setSaving(false)
    }
  }

  const canManage = (u) => u.id !== me.id && u.role !== ROLES.ADMINISTRADOR

  return (
    <div className="stack">
      <PageHeader eyebrow="Administración" title="Usuarios registrados" mood="calma">
        Consulta las cuentas de la plataforma, activa o desactiva el acceso y revisa el registro de acciones.
      </PageHeader>

      <section className="stats">
        <div className="stat"><span>{counts.total}</span>En la lista</div>
        <div className="stat stat--mint"><span>{counts.active}</span>Activas</div>
        <div className="stat stat--peach"><span>{counts.inactive}</span>Desactivadas</div>
      </section>

      <Alert type="success">{notice}</Alert>
      <Alert>{error}</Alert>

      <section className="card">
        <div className="admin-filters">
          <label className="search-box">
            <Icon name="search" size={20} />
            <span className="sr-only">Buscar usuario</span>
            <input type="search" value={filters.q} onChange={(e) => setFilter('q', e.target.value)} placeholder="Buscar por nombre o correo" />
          </label>
          <div className="chips" role="group" aria-label="Filtrar por rol">
            {ROLE_FILTERS.map((f) => (
              <button key={f.value} type="button" className={`chip ${filters.role === f.value ? 'chip--active' : ''}`} onClick={() => setFilter('role', f.value)}>
                {f.label}
              </button>
            ))}
          </div>
          <div className="chips" role="group" aria-label="Filtrar por estado">
            {STATUS_FILTERS.map((f) => (
              <button key={f.value} type="button" className={`chip ${filters.status === f.value ? 'chip--active' : ''}`} onClick={() => setFilter('status', f.value)}>
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {!users ? (
          <p className="muted">Cargando usuarios…</p>
        ) : (
          <div className="table-wrap">
            <table className="users-table">
              <thead>
                <tr><th>Usuario</th><th>Rol</th><th>Estado</th><th>Registro</th><th>Último ingreso</th><th><span className="sr-only">Acciones</span></th></tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className={u.is_active ? '' : 'row-inactive'}>
                    <td>
                      <div className="user-cell">
                        <Avatar user={u} size={40} />
                        <div>
                          <strong>{u.full_name}</strong>
                          <span>{u.email}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`role-pill role-pill--${u.role.toLowerCase()}`}>{u.role_display}</span>
                      {u.is_verified === false && <span className="tiny muted block">Sin verificar</span>}
                    </td>
                    <td>
                      <span className={`status-pill ${u.is_active ? 'status-pill--on' : 'status-pill--off'}`}>{u.is_active ? 'Activa' : 'Desactivada'}</span>
                      {!u.email_verified && <span className="tiny muted block">Correo sin confirmar</span>}
                    </td>
                    <td>{formatDate(u.date_joined)}</td>
                    <td>{u.last_login ? dateTime(u.last_login) : <span className="muted">Nunca</span>}</td>
                    <td className="cell-actions">
                      {canManage(u) ? (
                        u.is_active ? (
                          <button type="button" className="btn btn--ghost btn--sm" onClick={() => { setPending(u); setReason(''); setReasonError('') }}>Desactivar</button>
                        ) : (
                          <button type="button" className="btn btn--primary btn--sm" disabled={saving} onClick={() => changeStatus(u, true)}>Activar</button>
                        )
                      ) : (
                        <span className="tiny muted">{u.id === me.id ? 'Tu cuenta' : 'Administrador'}</span>
                      )}
                    </td>
                  </tr>
                ))}
                {!users.length && <tr><td colSpan="6" className="muted center">No hay usuarios con estos filtros.</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="card">
        <div className="card-head">
          <div>
            <h2>Registro de acciones</h2>
            <p className="muted tiny">Cada cambio que hace un administrador queda guardado y no se puede editar ni borrar.</p>
          </div>
        </div>
        {!logs.length ? (
          <p className="muted">Todavía no hay acciones registradas.</p>
        ) : (
          <ul className="log-list">
            {logs.slice(0, 15).map((log) => (
              <li key={log.id}>
                <span className={`log-dot log-dot--${ACTION_TONE[log.action] ?? 'lilac'}`} />
                <div>
                  <strong>{log.action_display}</strong> · {log.target_email}
                  {log.reason && <span className="log-reason">“{log.reason}”</span>}
                  <span className="tiny muted block">{log.actor_email ?? 'Administrador eliminado'} · {dateTime(log.created_at)}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {pending && (
        <div className="modal-backdrop" role="presentation" onClick={() => !saving && setPending(null)}>
          <form className="modal card" role="dialog" aria-modal="true" aria-labelledby="deactivate-title"
            onClick={(e) => e.stopPropagation()}
            onSubmit={(e) => { e.preventDefault(); changeStatus(pending, false, reason) }}>
            <h2 id="deactivate-title">¿Desactivar la cuenta de {pending.full_name}?</h2>
            <p className="muted">No podrá iniciar sesión hasta que la vuelvas a activar. Sus datos no se borran.</p>
            <div className={`field ${reasonError ? 'field--error' : ''}`}>
              <label htmlFor="reason">Motivo</label>
              <textarea id="reason" value={reason} maxLength={300} autoFocus onChange={(e) => setReason(e.target.value)}
                placeholder="Ej.: solicitud del usuario, uso indebido del chat…" />
              {reasonError && <span className="field-error">{reasonError}</span>}
            </div>
            <div className="form-actions">
              <button type="button" className="btn btn--ghost" onClick={() => setPending(null)} disabled={saving}>Cancelar</button>
              <button type="submit" className="btn btn--danger" disabled={saving}>{saving ? 'Guardando…' : 'Desactivar cuenta'}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
