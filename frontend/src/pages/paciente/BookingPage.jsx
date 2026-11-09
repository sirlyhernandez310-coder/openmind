import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { appointmentsApi } from '../../api/appointments'
import { professionalsApi } from '../../api/professionals'
import Alert from '../../components/Alert'
import Avatar from '../../components/Avatar'
import Blob from '../../components/Blob'
import Icon from '../../components/Icon'
import { dayNumber, formatLongDay, formatTime, formatTimeRange, formatWeekdayShort } from '../../format'

// OM3-16 Consultar disponibilidad + OM3-17 Reservar cita
export default function BookingPage() {
  const { id } = useParams()
  const [psy, setPsy] = useState(null)
  const [days, setDays] = useState(null)
  const [dayIndex, setDayIndex] = useState(0)
  const [selected, setSelected] = useState(null)
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [booked, setBooked] = useState(null)

  const loadSlots = useCallback(
    () => appointmentsApi.slots(id).then((data) => setDays(data.days)).catch((err) => setError(err.message)),
    [id],
  )

  useEffect(() => {
    professionalsApi.directoryDetail(id).then(setPsy).catch((err) => setError(err.message))
    loadSlots()
  }, [id, loadSlots])

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!selected) return
    setSaving(true)
    setError('')
    try {
      const appointment = await appointmentsApi.book({ psychologist: Number(id), start: selected.start, reason })
      setBooked(appointment)
    } catch (err) {
      // si alguien más tomó el horario, se recargan los horarios libres
      setError(err.fieldErrors.start || err.fieldErrors.psychologist || err.message)
      setSelected(null)
      loadSlots()
    } finally {
      setSaving(false)
    }
  }

  if (booked) {
    return (
      <section className="card booked">
        <Blob mood="alegria" size={130} className="float" />
        <span className="eyebrow">Reserva confirmada</span>
        <h1>¡Tu sesión quedó agendada!</h1>
        <div className="booked-summary">
          <Avatar user={booked.psychologist} size={64} />
          <div>
            <strong>{booked.psychologist.full_name}</strong>
            <span>{booked.psychologist.specialty}</span>
          </div>
          <div className="booked-when">
            <span><Icon name="calendar" size={18} /> {formatLongDay(booked.start)}</span>
            <span><Icon name="clock" size={18} /> {formatTimeRange(booked.start, booked.end)}</span>
          </div>
        </div>
        <p className="muted">Puedes verla cuando quieras en <strong>Mis sesiones</strong>.</p>
        <div className="hero-actions">
          <Link to="/paciente/sesiones" className="btn btn--primary">Ir a mis sesiones</Link>
          <Link to="/paciente/psicologos" className="btn btn--ghost">Volver a psicólogos</Link>
        </div>
      </section>
    )
  }

  const day = days?.[dayIndex]

  return (
    <div className="stack">
      <Link to={`/paciente/psicologos/${id}`} className="back-link"><Icon name="back" size={18} /> Volver al perfil</Link>

      <header className="booking-head">
        {psy && <Avatar user={psy} size={72} shape="rounded" />}
        <div>
          <span className="eyebrow">Reservar sesión</span>
          <h1>{psy ? psy.full_name : 'Cargando…'}</h1>
          {psy && <p className="muted">{psy.specialty_display} · Sesiones de 1 hora</p>}
        </div>
      </header>

      <Alert>{error}</Alert>

      {!days ? (
        <p className="muted">Buscando horarios disponibles…</p>
      ) : !days.length ? (
        <section className="card empty">
          <Blob mood="tristeza" size={110} />
          <h2>No hay horarios disponibles</h2>
          <p className="muted">Este psicólogo no tiene espacios libres en los próximos 14 días. Prueba con otro profesional.</p>
          <Link to="/paciente/psicologos" className="btn btn--primary btn--sm">Ver otros psicólogos</Link>
        </section>
      ) : (
        <form className="booking" onSubmit={handleSubmit}>
          <section className="card">
            <h2 className="step-title"><span>1</span> Elige el día</h2>
            <div className="day-tabs" role="tablist" aria-label="Días con horarios disponibles">
              {days.map((d, i) => (
                <button key={d.date} type="button" role="tab" aria-selected={i === dayIndex}
                  className={`day-tab ${i === dayIndex ? 'day-tab--active' : ''}`}
                  onClick={() => { setDayIndex(i); setSelected(null) }}>
                  <span>{formatWeekdayShort(d.date)}</span>
                  <strong>{dayNumber(d.date)}</strong>
                  <small>{d.slots.length} {d.slots.length === 1 ? 'libre' : 'libres'}</small>
                </button>
              ))}
            </div>

            <h2 className="step-title"><span>2</span> Elige la hora</h2>
            <p className="muted tiny">{formatLongDay(day.date)} · solo se muestran los horarios libres</p>
            <div className="slot-grid" role="radiogroup" aria-label="Horarios disponibles">
              {day.slots.map((slot) => (
                <button key={slot.start} type="button" role="radio" aria-checked={selected?.start === slot.start}
                  className={`slot ${selected?.start === slot.start ? 'slot--active' : ''}`}
                  onClick={() => setSelected(slot)}>
                  {formatTime(slot.start)}
                </button>
              ))}
            </div>
          </section>

          <aside className="card booking-summary">
            <h2 className="step-title"><span>3</span> Confirma</h2>
            {selected ? (
              <div className="booking-when">
                <span><Icon name="calendar" size={18} /> {formatLongDay(selected.start)}</span>
                <span><Icon name="clock" size={18} /> {formatTimeRange(selected.start, selected.end)}</span>
              </div>
            ) : (
              <p className="muted">Selecciona un día y una hora para continuar.</p>
            )}
            <div className="field">
              <label htmlFor="reason">¿Qué te gustaría trabajar? <span className="field-optional">(opcional)</span></label>
              <textarea id="reason" maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)}
                placeholder="Ej.: quiero aprender a manejar la ansiedad antes de los exámenes" />
            </div>
            <button type="submit" className="btn btn--primary btn--block" disabled={!selected || saving}>
              {saving ? 'Reservando…' : 'Confirmar reserva'}
            </button>
          </aside>
        </form>
      )}
    </div>
  )
}
