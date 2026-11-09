import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { appointmentsApi } from '../../api/appointments'
import { evaluationsApi } from '../../api/evaluations'
import Alert from '../../components/Alert'
import Avatar from '../../components/Avatar'
import Blob, { emotionLabel } from '../../components/Blob'
import Icon from '../../components/Icon'
import LoopPattern from '../../components/LoopPattern'
import PhotoCard from '../../components/PhotoCard'
import { useAuth } from '../../context/auth-context'
import { LEVELS, formatDate, formatTimeRange, friendlyDay, moodFor } from '../../format'

const MOODS = ['alegria', 'calma', 'ansiedad', 'tristeza', 'enojo']
const MOOD_REPLY = {
  alegria: '¡Qué bueno! Aprovecha esa energía y cuídala.',
  calma: 'Qué lindo sentir calma. Regálate un momento para disfrutarla.',
  ansiedad: 'Respira lento: inhala 4 segundos y exhala 6. Estamos aquí si lo necesitas.',
  tristeza: 'Está bien no estar bien. Hablar con alguien puede ayudar.',
  enojo: 'Tu enojo es válido. Una pausa corta antes de actuar puede ayudarte.',
}

function greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Buenos días'
  if (hour < 19) return 'Buenas tardes'
  return 'Buenas noches'
}

export default function PatientHomePage() {
  const { user } = useAuth()
  const location = useLocation()
  const [last, setLast] = useState(undefined)
  const [mood, setMood] = useState(null)
  const [nextSession, setNextSession] = useState(undefined)

  useEffect(() => {
    evaluationsApi.history().then((items) => setLast(items[0] ?? null)).catch(() => setLast(null))
    appointmentsApi.list('upcoming').then((items) => setNextSession(items[0] ?? null)).catch(() => setNextSession(null))
  }, [])

  const level = last ? LEVELS[last.level] : null
  const needsHelp = mood === 'tristeza' || mood === 'ansiedad'

  return (
    <div className="stack">
      {location.state?.welcome && (
        <Alert type="success">¡Tu correo fue confirmado y tu cuenta está activa! Bienvenido a Open Mind.</Alert>
      )}

      <section className="hero panel-lilac">
        <LoopPattern variant="wide" />
        <div className="hero-text">
          <span className="eyebrow">{greeting()}, {user.first_name}</span>
          <h1>¿Cómo te sientes hoy?</h1>
          <p>{mood ? MOOD_REPLY[mood] : 'Toca la nube que más se parece a ti ahora.'}</p>
          {mood && (
            <div className="hero-actions">
              <Link to="/paciente/evaluacion" className="btn btn--primary btn--sm">Hacer la evaluación completa</Link>
              {needsHelp && <Link to="/paciente/emergencia" className="btn btn--light btn--sm">Hablar con un psicólogo</Link>}
            </div>
          )}
        </div>
        <div className="mood-picker" role="radiogroup" aria-label="¿Cómo te sientes hoy?">
          {MOODS.map((m) => (
            <button key={m} type="button" role="radio" aria-checked={mood === m}
              className={`mood ${mood === m ? 'mood--selected' : ''}`} onClick={() => setMood(m)}>
              <Blob mood={m} size={66} limbs={false} decor={false} />
              {emotionLabel(m)}
            </button>
          ))}
        </div>
      </section>

      <section className="features">
        <Link to="/paciente/evaluacion" className="feature feature--sun">
          <span className="feature-icon"><Icon name="smile" size={24} /></span>
          <h3>Evaluación emocional</h3>
          <p>12 preguntas, 3 minutos. Conoce tu estado de hoy.</p>
          <span className="feature-cta">Empezar <Icon name="arrow" size={16} /></span>
        </Link>
        <Link to="/paciente/historial" className="feature feature--white">
          <span className="feature-icon feature-icon--mint"><Icon name="chart" size={24} /></span>
          <h3>Mi historial</h3>
          <p>Mira cómo ha cambiado tu bienestar en el tiempo.</p>
          <span className="feature-cta">Ver historial <Icon name="arrow" size={16} /></span>
        </Link>
        <Link to="/paciente/emergencia" className="feature feature--coral">
          <span className="feature-icon"><Icon name="chat" size={24} /></span>
          <h3>Chat de emergencia</h3>
          <p>Habla ahora con un psicólogo disponible.</p>
          <span className="feature-cta">Abrir chat <Icon name="arrow" size={16} /></span>
        </Link>
      </section>

      <section className="grid-auto">
        {last ? (
          <Link to={`/paciente/historial/${last.id}`} className="card last-result">
            <Blob mood={moodFor(last.level)} size={110} />
            <div>
              <span className="tiny muted">Tu última evaluación · {formatDate(last.created_at)}</span>
              <strong className="last-result-title">{emotionLabel(moodFor(last.level))}</strong>
              <span className={`level-pill level-pill--${level.tone}`}>{level.label} · {last.percentage} %</span>
            </div>
          </Link>
        ) : (
          <Link to="/paciente/psicologos" className="card last-result">
            <Blob mood="curiosa" size={110} />
            <div>
              <span className="tiny muted">Conoce a quienes te acompañan</span>
              <strong className="last-result-title">Nuestros psicólogos</strong>
              <span className="feature-cta">Ver psicólogos <Icon name="arrow" size={16} /></span>
            </div>
          </Link>
        )}
        {nextSession ? (
          <Link to="/paciente/sesiones" className="card next-session">
            <span className="tiny muted">Tu próxima sesión</span>
            <strong className="last-result-title">{friendlyDay(nextSession.start)}</strong>
            <span className="next-slot"><Icon name="clock" size={16} /> {formatTimeRange(nextSession.start, nextSession.end)}</span>
            <span className="next-session-psy">
              <Avatar user={nextSession.psychologist} size={40} /> con {nextSession.psychologist.full_name}
            </span>
          </Link>
        ) : nextSession === null && (
          <Link to="/paciente/psicologos" className="card next-session next-session--empty">
            <span className="feature-icon feature-icon--mint"><Icon name="calendar" size={24} /></span>
            <strong className="last-result-title">Reserva una sesión</strong>
            <span className="muted">Elige un psicólogo, mira sus horarios libres y agenda tu cita.</span>
            <span className="feature-cta">Buscar psicólogo <Icon name="arrow" size={16} /></span>
          </Link>
        )}
        <PhotoCard hint="Así tu psicólogo te reconoce en el chat. JPG, PNG o WEBP, hasta 5 MB." />
      </section>
    </div>
  )
}
