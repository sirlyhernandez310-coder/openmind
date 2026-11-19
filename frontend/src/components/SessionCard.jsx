import { Link } from 'react-router-dom'
import { dayNumber, formatLongDay, formatMonthShort, formatTime, formatTimeRange, friendlyDay } from '../format'
import Avatar from './Avatar'
import Icon from './Icon'

const STATUS_TONE = { PROGRAMADA: 'mint', REALIZADA: 'lilac', CANCELADA: 'coral' }

// Una cita: fecha, hora y la otra persona (el psicólogo para el paciente, el paciente para el psicólogo)
export default function SessionCard({ appointment, viewer = 'PACIENTE' }) {
  const person = viewer === 'PACIENTE' ? appointment.psychologist : appointment.patient
  const longDay = formatLongDay(appointment.start)
  const near = friendlyDay(appointment.start)
  return (
    <article className="session-card">
      <div className="session-date" aria-hidden="true">
        <span>{formatMonthShort(appointment.start)}</span>
        <strong>{dayNumber(appointment.start)}</strong>
      </div>
      <div className="session-body">
        <span className="session-day">{near === longDay ? longDay : `${near} · ${longDay}`}</span>
        <span className="session-time"><Icon name="clock" size={16} /> {formatTimeRange(appointment.start, appointment.end)}</span>
        {appointment.reason && <p className="session-reason">“{appointment.reason}”</p>}
      </div>
      <div className="session-person">
        <Avatar user={person} size={48} />
        <div>
          <strong>{person.full_name}</strong>
          <span>{viewer === 'PACIENTE' ? person.specialty : 'Paciente'}</span>
        </div>
      </div>
      <span className={`level-pill level-pill--${STATUS_TONE[appointment.status] ?? 'lilac'}`}>{appointment.status_display}</span>
      <CallAccess appointment={appointment} />
    </article>
  )
}

// OM3-20 CA1: la videollamada se abre desde la sesión programada
function CallAccess({ appointment }) {
  if (appointment.status !== 'PROGRAMADA' || !appointment.call_opens_at) return null
  const now = Date.now()
  const opens = Date.parse(appointment.call_opens_at)
  if (now > Date.parse(appointment.end)) return null
  if (now >= opens) {
    return (
      <Link to={`/sesion/${appointment.id}/videollamada`} className="btn btn--sun btn--sm session-call">
        <Icon name="video" size={18} /> Entrar a la videollamada
      </Link>
    )
  }
  return (
    <span className="session-call session-call--soon">
      <Icon name="video" size={16} /> Videollamada disponible desde las {formatTime(appointment.call_opens_at)}
      {friendlyDay(appointment.call_opens_at) !== friendlyDay(appointment.start) && ` del ${formatLongDay(appointment.call_opens_at)}`}
    </span>
  )
}
