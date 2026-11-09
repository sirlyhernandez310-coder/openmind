import { useEffect, useState } from 'react'
import { professionalsApi } from '../../api/professionals'
import Alert from '../../components/Alert'
import Avatar from '../../components/Avatar'
import PageHeader from '../../components/PageHeader'
import { formatDate } from '../../format'

const FILTERS = [
  { value: undefined, label: 'Todos' },
  { value: false, label: 'Pendientes' },
  { value: true, label: 'Verificados' },
]

export default function ProfessionalsPage() {
  const [items, setItems] = useState(null)
  const [filter, setFilter] = useState(false)
  const [error, setError] = useState('')
  const [openId, setOpenId] = useState(null)

  useEffect(() => {
    setItems(null)
    professionalsApi.list(filter).then(setItems).catch((err) => setError(err.message))
  }, [filter])

  const toggle = async (profile) => {
    try {
      const updated = await professionalsApi.verify(profile.id, !profile.is_verified)
      setItems((list) => list.map((p) => (p.id === updated.id ? updated : p)))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <PageHeader eyebrow="Administración" title="Profesionales">
        Revisa la tarjeta profesional de cada psicólogo antes de habilitarlo para atender emergencias.
      </PageHeader>
      <Alert>{error}</Alert>
      <section className="card">
        <div className="card-head">
          <h2>Psicólogos registrados</h2>
          <div className="chips" role="group" aria-label="Filtrar">
            {FILTERS.map((f) => (
              <button key={f.label} type="button" className={`chip ${filter === f.value ? 'chip--active' : ''}`} onClick={() => setFilter(f.value)}>
                {f.label}
              </button>
            ))}
          </div>
        </div>
        {!items ? (
          <p className="muted">Cargando…</p>
        ) : !items.length ? (
          <p className="muted">No hay profesionales en esta lista.</p>
        ) : (
          <ul className="pro-list">
            {items.map((p) => (
              <li key={p.id} className="pro">
                <div className="pro-main">
                  <Avatar user={p.user} size={48} shape="rounded" />
                  <div className="pro-info">
                    <strong>{p.user.full_name}</strong>
                    <span className="tiny muted">{p.specialty_display} · {p.years_experience} años · TP {p.license_number}</span>
                  </div>
                  <span className={`verify-pill ${p.is_verified ? 'verify-pill--ok' : ''}`}>{p.is_verified ? '✓ Verificado' : 'Pendiente'}</span>
                  <button type="button" className="btn btn--ghost btn--sm" onClick={() => setOpenId(openId === p.id ? null : p.id)}>
                    {openId === p.id ? 'Ocultar' : 'Ver perfil'}
                  </button>
                  <button type="button" className={`btn btn--sm ${p.is_verified ? 'btn--ghost' : 'btn--primary'}`} onClick={() => toggle(p)}>
                    {p.is_verified ? 'Retirar' : 'Verificar'}
                  </button>
                </div>
                {openId === p.id && (
                  <div className="pro-detail">
                    <p><strong>Correo:</strong> {p.user.email} · <strong>Universidad:</strong> {p.university || '—'} · <strong>Registro:</strong> {formatDate(p.created_at)}</p>
                    <p><strong>Descripción:</strong> {p.description}</p>
                    {p.experience && <p><strong>Experiencia:</strong> {p.experience}</p>}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  )
}
