import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { professionalsApi } from '../../api/professionals'
import Alert from '../../components/Alert'
import Avatar from '../../components/Avatar'
import Blob from '../../components/Blob'
import Icon from '../../components/Icon'
import PageHeader from '../../components/PageHeader'
import { formatTime, friendlyDay } from '../../format'

const TONES = ['mint', 'lilac', 'sun', 'blue', 'coral']

// OM3-14 Buscar psicólogos: listado de profesionales verificados con buscador
export default function PsychologistsPage() {
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('')
  const [specialties, setSpecialties] = useState([])

  // busca en el backend 300 ms después de que la persona deja de escribir
  useEffect(() => {
    const timer = setTimeout(() => {
      professionalsApi
        .directory(query.trim())
        .then((list) => {
          setItems(list)
          setError('')
          if (!query.trim()) {
            const map = new Map(list.map((p) => [p.specialty, p.specialty_display]))
            setSpecialties([...map.entries()])
          }
        })
        .catch((err) => setError(err.message))
    }, query ? 300 : 0)
    return () => clearTimeout(timer)
  }, [query])

  const visible = useMemo(
    () => (filter ? (items ?? []).filter((p) => p.specialty === filter) : items ?? []),
    [items, filter],
  )

  return (
    <div className="stack">
      <PageHeader eyebrow="Psicólogos" title="Quienes te acompañan" mood="calma">
        Todos están verificados con su tarjeta profesional. Entra a su perfil y reserva una sesión.
      </PageHeader>
      <Alert>{error}</Alert>

      <div className="search-row">
        <label className="search-box">
          <Icon name="search" size={20} />
          <span className="sr-only">Buscar psicólogo</span>
          <input type="search" value={query} onChange={(e) => setQuery(e.target.value)}
            placeholder="Busca por nombre o especialidad (ej. ansiedad, infantil)" />
        </label>
        {specialties.length > 1 && (
          <div className="chips" role="group" aria-label="Filtrar por especialidad">
            <button type="button" className={`chip ${!filter ? 'chip--active' : ''}`} onClick={() => setFilter('')}>Todos</button>
            {specialties.map(([value, label]) => (
              <button key={value} type="button" className={`chip ${filter === value ? 'chip--active' : ''}`} onClick={() => setFilter(value)}>
                {label}
              </button>
            ))}
          </div>
        )}
      </div>

      {!items ? (
        <p className="muted">Cargando psicólogos…</p>
      ) : !visible.length ? (
        <section className="card empty">
          <Blob mood="curiosa" size={110} />
          <h2>{query ? 'No encontramos coincidencias' : 'Pronto tendremos psicólogos aquí'}</h2>
          <p className="muted">
            {query ? 'Prueba con otro nombre o especialidad.' : 'Mientras tanto puedes usar el chat de emergencia.'}
          </p>
        </section>
      ) : (
        <section className="psy-grid">
          {visible.map((p) => (
            <Link key={p.id} to={`/paciente/psicologos/${p.id}`} className="psy-card psy-card--link">
              <Avatar user={p} size={96} shape="rounded" />
              <div className="psy-card-body">
                <h3>{p.full_name}</h3>
                <span className={`level-pill level-pill--${TONES[p.id % TONES.length]}`}>
                  {p.specialty_display} · {p.years_experience} {p.years_experience === 1 ? 'año' : 'años'}
                </span>
                <p className="clamp-2">{p.description}</p>
                <span className={`next-slot ${p.next_available ? '' : 'next-slot--none'}`}>
                  <Icon name="clock" size={16} />
                  {p.next_available
                    ? `Próximo horario: ${friendlyDay(p.next_available)}, ${formatTime(p.next_available)}`
                    : 'Sin horarios disponibles por ahora'}
                </span>
                <span className="link-btn">Ver perfil y reservar <Icon name="arrow" size={16} /></span>
              </div>
            </Link>
          ))}
        </section>
      )}

      <section className="support">
        <div>
          <h2>¿Necesitas hablar ahora?</h2>
          <p>El primer psicólogo disponible se unirá a tu conversación.</p>
        </div>
        <Link to="/paciente/emergencia" className="btn btn--sun">Abrir chat de emergencia</Link>
      </section>
    </div>
  )
}
