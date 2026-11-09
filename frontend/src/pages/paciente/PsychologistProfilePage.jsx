import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { professionalsApi } from '../../api/professionals'
import Avatar from '../../components/Avatar'
import Blob from '../../components/Blob'
import Icon from '../../components/Icon'
import LoopPattern from '../../components/LoopPattern'
import { formatTime, friendlyDay } from '../../format'

// OM3-15 Consultar perfil del psicólogo
export default function PsychologistProfilePage() {
  const { id } = useParams()
  const [psy, setPsy] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    professionalsApi
      .directoryDetail(id)
      .then(setPsy)
      .catch((err) => setError(err.status === 404 ? 'Este psicólogo no está disponible.' : err.message))
  }, [id])

  if (error) {
    return (
      <div className="stack">
        <Link to="/paciente/psicologos" className="back-link"><Icon name="back" size={18} /> Volver a psicólogos</Link>
        <section className="card empty">
          <Blob mood="tristeza" size={110} />
          <h2>{error}</h2>
        </section>
      </div>
    )
  }
  if (!psy) return <p className="muted">Cargando perfil…</p>

  return (
    <div className="stack">
      <Link to="/paciente/psicologos" className="back-link"><Icon name="back" size={18} /> Volver a psicólogos</Link>

      <section className="profile-hero panel-lilac">
        <LoopPattern variant="wide" />
        <Avatar user={psy} size={150} shape="rounded" className="profile-photo" />
        <div className="profile-hero-text">
          <span className="eyebrow">Psicólogo verificado <Icon name="shield" size={16} /></span>
          <h1>{psy.full_name}</h1>
          <div className="chips">
            <span className="chip chip--static">{psy.specialty_display}</span>
            <span className="chip chip--static">
              {psy.years_experience} {psy.years_experience === 1 ? 'año' : 'años'} de experiencia
            </span>
          </div>
          <Link to={`/paciente/psicologos/${psy.id}/reservar`} className="btn btn--primary">
            <Icon name="calendar" size={18} /> Reservar sesión
          </Link>
        </div>
      </section>

      <section className="grid-auto">
        <article className="card profile-info">
          <h2>Sobre mí</h2>
          <p>{psy.description || 'Este psicólogo aún no ha escrito su descripción.'}</p>
          {psy.experience && (
            <>
              <h3>Experiencia</h3>
              <p>{psy.experience}</p>
            </>
          )}
        </article>
        <article className="card profile-info">
          <h2>Información profesional</h2>
          <dl className="info-list">
            <div><dt><Icon name="user" size={18} /> Especialidad</dt><dd>{psy.specialty_display}</dd></div>
            <div><dt><Icon name="chart" size={18} /> Experiencia</dt><dd>{psy.years_experience} {psy.years_experience === 1 ? 'año' : 'años'}</dd></div>
            {psy.university && <div><dt><Icon name="school" size={18} /> Universidad</dt><dd>{psy.university}</dd></div>}
            <div><dt><Icon name="shield" size={18} /> Tarjeta profesional</dt><dd>Verificada por OpenMind</dd></div>
            <div>
              <dt><Icon name="clock" size={18} /> Próximo horario</dt>
              <dd>{psy.next_available ? `${friendlyDay(psy.next_available)}, ${formatTime(psy.next_available)}` : 'Sin horarios por ahora'}</dd>
            </div>
          </dl>
        </article>
      </section>

      <section className="support">
        <div>
          <h2>¿Quieres hablar con {psy.first_name}?</h2>
          <p>Elige un día y un horario libre. Cada sesión dura 1 hora.</p>
        </div>
        <Link to={`/paciente/psicologos/${psy.id}/reservar`} className="btn btn--sun">Ver horarios disponibles</Link>
      </section>
    </div>
  )
}
