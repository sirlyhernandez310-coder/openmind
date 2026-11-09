import { useEffect, useMemo, useState } from 'react'
import { authApi } from '../../api/auth'
import Alert from '../../components/Alert'
import PageHeader from '../../components/PageHeader'
import { ROLES, ROLE_LABELS } from '../../constants/roles'
import { useAuth } from '../../context/auth-context'

const FILTERS = [{ value: '', label: 'Todos' }, ...Object.values(ROLES).map((r) => ({ value: r, label: ROLE_LABELS[r] }))]

export default function AdminHomePage() {
  const { user } = useAuth()
  const [users, setUsers] = useState([])
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    authApi
      .users()
      .then(setUsers)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const counts = useMemo(() => {
    const result = { total: users.length }
    for (const role of Object.values(ROLES)) result[role] = users.filter((u) => u.role === role).length
    return result
  }, [users])

  const visible = filter ? users.filter((u) => u.role === filter) : users

  return (
    <>
      <PageHeader eyebrow="Administración" title={`Hola, ${user.first_name}`}>
        Gestiona las cuentas registradas en la plataforma.
      </PageHeader>

      <section className="stats">
        <div className="stat"><span>{counts.total}</span>Usuarios</div>
        <div className="stat stat--lilac"><span>{counts.PACIENTE ?? 0}</span>Pacientes</div>
        <div className="stat stat--mint"><span>{counts.PSICOLOGO ?? 0}</span>Psicólogos</div>
        <div className="stat stat--peach"><span>{counts.ADMINISTRADOR ?? 0}</span>Administradores</div>
      </section>

      <section className="card">
        <div className="card-head">
          <h2>Usuarios registrados</h2>
          <div className="chips" role="group" aria-label="Filtrar por rol">
            {FILTERS.map((f) => (
              <button
                key={f.value}
                type="button"
                className={`chip ${filter === f.value ? 'chip--active' : ''}`}
                onClick={() => setFilter(f.value)}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
        <Alert>{error}</Alert>
        {loading ? (
          <p className="muted">Cargando usuarios…</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Nombre</th><th>Correo</th><th>Rol</th><th>Registro</th></tr>
              </thead>
              <tbody>
                {visible.map((u) => (
                  <tr key={u.id}>
                    <td>{u.full_name}</td>
                    <td>{u.email}</td>
                    <td><span className={`role-pill role-pill--${u.role.toLowerCase()}`}>{ROLE_LABELS[u.role]}</span></td>
                    <td>{new Date(u.date_joined).toLocaleDateString('es-CO')}</td>
                  </tr>
                ))}
                {!visible.length && (
                  <tr><td colSpan="4" className="muted center">No hay usuarios con este rol.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}
