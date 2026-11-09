import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { appointmentsApi } from '../../api/appointments'
import Alert from '../../components/Alert'
import Blob from '../../components/Blob'
import PageHeader from '../../components/PageHeader'
import SessionCard from '../../components/SessionCard'

const TABS = [
  { value: 'upcoming', label: 'Próximas' },
  { value: 'past', label: 'Pasadas' },
]

// OM3-18 Consultar mis sesiones
export default function MySessionsPage() {
  const [scope, setScope] = useState('upcoming')
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    appointmentsApi
      .list(scope)
      .then((list) => active && setItems(list))
      .catch((err) => active && setError(err.message))
    return () => { active = false }
  }, [scope])

  const changeScope = (value) => {
    setItems(null)
    setScope(value)
  }

  return (
    <div className="stack">
      <PageHeader eyebrow="Mis sesiones" title="Tus citas con psicólogos" mood="alegria">
        Aquí ves la fecha, la hora y el psicólogo de cada sesión que reservaste.
      </PageHeader>
      <Alert>{error}</Alert>

      <div className="card-head">
        <div className="chips" role="tablist" aria-label="Tipo de sesiones">
          {TABS.map((tab) => (
            <button key={tab.value} type="button" role="tab" aria-selected={scope === tab.value}
              className={`chip ${scope === tab.value ? 'chip--active' : ''}`} onClick={() => changeScope(tab.value)}>
              {tab.label}
            </button>
          ))}
        </div>
        <Link to="/paciente/psicologos" className="btn btn--primary btn--sm">Reservar nueva sesión</Link>
      </div>

      {!items ? (
        <p className="muted">Cargando sesiones…</p>
      ) : !items.length ? (
        <section className="card empty">
          <Blob mood={scope === 'upcoming' ? 'curiosa' : 'calma'} size={110} />
          <h2>{scope === 'upcoming' ? 'Aún no tienes sesiones programadas' : 'Todavía no tienes sesiones pasadas'}</h2>
          <p className="muted">Busca un psicólogo, revisa su perfil y elige el horario que mejor te quede.</p>
          {scope === 'upcoming' && <Link to="/paciente/psicologos" className="btn btn--sun btn--sm">Buscar psicólogo</Link>}
        </section>
      ) : (
        <section className="session-list">
          {items.map((a) => <SessionCard key={a.id} appointment={a} />)}
        </section>
      )}
    </div>
  )
}
