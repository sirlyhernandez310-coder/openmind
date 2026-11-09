import { dayNumber, formatLongDay, formatMonthShort, formatTimeRange, friendlyDay } from '../format'
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
    </article>
  )
}
