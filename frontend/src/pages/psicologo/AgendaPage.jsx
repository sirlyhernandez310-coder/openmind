import { useEffect, useState } from 'react'
import { appointmentsApi } from '../../api/appointments'
import Alert from '../../components/Alert'
import Blob from '../../components/Blob'
import Icon from '../../components/Icon'
import PageHeader from '../../components/PageHeader'
import SessionCard from '../../components/SessionCard'
import { useAuth } from '../../context/auth-context'

const WEEKDAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
const short = (t) => t.slice(0, 5) // "08:00:00" -> "08:00"

// Agenda del psicólogo: sus próximas citas (solo consulta) y su horario semanal de atención
export default function AgendaPage() {
  const { user } = useAuth()
  const [appointments, setAppointments] = useState(null)
  const [rules, setRules] = useState(null)
  const [error, setError] = useState('')
  const [scheduleError, setScheduleError] = useState('')
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    appointmentsApi.list('upcoming').then(setAppointments).catch((err) => setError(err.message))
    appointmentsApi
      .myAvailability()
      .then((list) => setRules(list.map((r) => ({ weekday: r.weekday, start_time: short(r.start_time), end_time: short(r.end_time) }))))
      .catch((err) => setError(err.message))
  }, [])

  const update = (index, field, value) => {
    setSaved(false)
    setRules((current) => current.map((r, i) => (i === index ? { ...r, [field]: value } : r)))
  }
  const add = (weekday) => {
    setSaved(false)
    setRules((current) => [...current, { weekday, start_time: '08:00', end_time: '12:00' }])
  }
  const remove = (index) => {
    setSaved(false)
    setRules((current) => current.filter((_, i) => i !== index))
  }

  const save = async () => {
    setSaving(true)
    setScheduleError('')
    try {
      const list = await appointmentsApi.saveAvailability(rules)
      setRules(list.map((r) => ({ weekday: r.weekday, start_time: short(r.start_time), end_time: short(r.end_time) })))
      setSaved(true)
    } catch (err) {
      const message = err.data?.items
      setScheduleError(
        typeof message?.[0] === 'string' ? message.join(' ')
          : message ? 'Revisa que todas las franjas tengan hora de inicio y de fin.'
            : err.message,
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="stack">
      <PageHeader eyebrow="Agenda" title="Tus sesiones y horarios" mood="calma">
        Define los horarios en que atiendes; los pacientes solo podrán reservar dentro de ellos.
      </PageHeader>
      <Alert>{error}</Alert>
      {!user.is_verified && (
        <Alert type="info">Mientras tu perfil no esté verificado, los pacientes aún no pueden reservar contigo.</Alert>
      )}

      <section className="card">
        <div className="card-head"><h2>Próximas sesiones</h2></div>
        {!appointments ? (
          <p className="muted">Cargando…</p>
        ) : !appointments.length ? (
          <div className="empty">
            <Blob mood="curiosa" size={90} />
            <p className="muted">Aún no tienes sesiones reservadas.</p>
          </div>
        ) : (
          <div className="session-list">
            {appointments.map((a) => <SessionCard key={a.id} appointment={a} viewer="PSICOLOGO" />)}
          </div>
        )}
      </section>

      <section className="card">
        <div className="card-head">
          <div>
            <h2>Horario semanal de atención</h2>
            <p className="muted tiny">Cada sesión dura 1 hora. Ej.: de 08:00 a 12:00 se ofrecen 4 sesiones.</p>
          </div>
          <button type="button" className="btn btn--primary btn--sm" onClick={save} disabled={!rules || saving}>
            {saving ? 'Guardando…' : 'Guardar horario'}
          </button>
        </div>
        {saved && <Alert type="success">¡Horario guardado! Los pacientes ya ven tus nuevos horarios.</Alert>}
        <Alert>{scheduleError}</Alert>

        {!rules ? (
          <p className="muted">Cargando…</p>
        ) : (
          <div className="week-editor">
            {WEEKDAYS.map((name, weekday) => {
              const dayRules = rules.map((r, index) => ({ ...r, index })).filter((r) => r.weekday === weekday)
              return (
                <div key={name} className="week-day">
                  <strong>{name}</strong>
                  <div className="week-ranges">
                    {!dayRules.length && <span className="muted tiny">No atiendes</span>}
                    {dayRules.map((r) => (
                      <div key={r.index} className="week-range">
                        <input type="time" step="1800" aria-label={`${name} desde`} value={r.start_time}
                          onChange={(e) => update(r.index, 'start_time', e.target.value)} />
                        <span>a</span>
                        <input type="time" step="1800" aria-label={`${name} hasta`} value={r.end_time}
                          onChange={(e) => update(r.index, 'end_time', e.target.value)} />
                        <button type="button" className="icon-btn" onClick={() => remove(r.index)} aria-label={`Quitar franja del ${name}`}>
                          <Icon name="trash" size={18} />
                        </button>
                      </div>
                    ))}
                  </div>
                  <button type="button" className="link-btn" onClick={() => add(weekday)}>
                    <Icon name="plus" size={16} /> Agregar franja
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
