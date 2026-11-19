import { useEffect, useState } from 'react'
import { adminApi } from '../../api/admin'
import Alert from '../../components/Alert'
import Icon from '../../components/Icon'
import PageHeader from '../../components/PageHeader'

const monthLabel = (value) => {
  const [y, m] = value.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString('es-CO', { month: 'short' }).replace('.', '')
}
const percent = (part, total) => (total ? Math.round((part / total) * 100) : 0)

// Barras horizontales: una fila por categoría (nombre, barra y valor)
function BarList({ items, ordinal = false }) {
  const max = Math.max(1, ...items.map((i) => i.count))
  const total = items.reduce((sum, i) => sum + i.count, 0)
  return (
    <ul className="bar-list">
      {items.map((item, index) => (
        <li key={item.key}>
          <span className="bar-label">{item.label}</span>
          <span className="bar-track" title={`${item.label}: ${item.count} (${percent(item.count, total)} %)`}>
            <span
              className="bar-fill"
              style={{
                width: `${(item.count / max) * 100}%`,
                // escala ordinal (por ejemplo niveles de malestar): un solo tono, de claro a oscuro
                ...(ordinal ? { background: `var(--seq-${index + 1})` } : {}),
              }}
            />
          </span>
          <span className="bar-value">{item.count}</span>
        </li>
      ))}
    </ul>
  )
}

// Columnas por mes con tooltip al pasar el mouse o con el teclado
function MonthlyChart({ title, series, unit }) {
  const max = Math.max(1, ...series.map((s) => s.count))
  const total = series.reduce((sum, s) => sum + s.count, 0)
  return (
    <article className="card chart-card">
      <div className="chart-head">
        <h3>{title}</h3>
        <span className="muted tiny">{total} en 6 meses</span>
      </div>
      <div className="month-chart" role="img" aria-label={`${title}: ${series.map((s) => `${monthLabel(s.month)} ${s.count}`).join(', ')}`}>
        {series.map((s, i) => (
          <div key={s.month} className="month-col" tabIndex={0}>
            <span className="month-tip">{s.count} {unit}</span>
            <span className="month-bar-wrap">
              <span className={`month-bar ${i === series.length - 1 ? 'month-bar--current' : ''}`} style={{ height: `${Math.max(2, (s.count / max) * 100)}%` }} />
            </span>
            <span className="month-label">{monthLabel(s.month)}</span>
          </div>
        ))}
      </div>
    </article>
  )
}

// OM3-25 Consultar estadísticas
export default function StatsPage() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    adminApi.stats().then(setStats).catch((err) => setError(err.message))
  }, [])

  if (!stats) {
    return (
      <div className="stack">
        <PageHeader eyebrow="Estadísticas" title="Cómo va OpenMind" mood="curiosa" />
        {error ? <Alert>{error}</Alert> : <p className="muted">Calculando estadísticas…</p>}
      </div>
    )
  }

  const { users, psychologists, evaluations, appointments, emergency, monthly } = stats
  const generated = new Date(stats.generated_at).toLocaleString('es-CO', { dateStyle: 'long', timeStyle: 'short' })

  return (
    <div className="stack">
      <PageHeader eyebrow="Estadísticas" title="Cómo va OpenMind" mood="curiosa">
        Datos calculados en este momento a partir de la información registrada en la plataforma.
      </PageHeader>

      <section className="kpi-grid">
        <div className="kpi">
          <Icon name="users" size={22} />
          <strong>{users.total}</strong>
          <span>Usuarios registrados</span>
          <small>+{users.new_last_30_days} en los últimos 30 días</small>
        </div>
        <div className="kpi">
          <Icon name="shield" size={22} />
          <strong>{psychologists.verified}</strong>
          <span>Psicólogos verificados</span>
          <small>{psychologists.pending} pendientes de verificación</small>
        </div>
        <div className="kpi">
          <Icon name="smile" size={22} />
          <strong>{evaluations.total}</strong>
          <span>Evaluaciones emocionales</span>
          <small>Malestar promedio: {evaluations.average_percentage} %</small>
        </div>
        <div className="kpi">
          <Icon name="calendar" size={22} />
          <strong>{appointments.total}</strong>
          <span>Citas reservadas</span>
          <small>{appointments.upcoming} próximas</small>
        </div>
      </section>

      <section className="chart-grid">
        <MonthlyChart title="Nuevos usuarios por mes" series={monthly.registrations} unit="usuarios" />
        <MonthlyChart title="Evaluaciones por mes" series={monthly.evaluations} unit="evaluaciones" />
        <MonthlyChart title="Citas reservadas por mes" series={monthly.appointments} unit="citas" />
      </section>

      <section className="chart-grid">
        <article className="card chart-card">
          <div className="chart-head">
            <h3>Usuarios por rol</h3>
            <span className="muted tiny">{users.active} activos · {users.inactive} desactivados</span>
          </div>
          <BarList items={users.by_role} />
        </article>
        <article className="card chart-card">
          <div className="chart-head">
            <h3>Resultados de las evaluaciones</h3>
            <span className="muted tiny">{evaluations.needs_support} requirieron apoyo</span>
          </div>
          <BarList items={evaluations.by_level} ordinal />
        </article>
        <article className="card chart-card">
          <div className="chart-head">
            <h3>Citas por estado</h3>
            <span className="muted tiny">{appointments.total} en total</span>
          </div>
          <BarList items={appointments.by_status} />
        </article>
        <article className="card chart-card">
          <div className="chart-head">
            <h3>Chats de emergencia</h3>
            <span className="muted tiny">{emergency.total} en total</span>
          </div>
          <BarList items={emergency.by_status} />
        </article>
      </section>

      <details className="card table-toggle">
        <summary>Ver los datos mensuales como tabla</summary>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Mes</th><th>Nuevos usuarios</th><th>Evaluaciones</th><th>Citas</th></tr></thead>
            <tbody>
              {monthly.registrations.map((row, i) => (
                <tr key={row.month}>
                  <td>{monthLabel(row.month)} {row.month.slice(0, 4)}</td>
                  <td>{row.count}</td>
                  <td>{monthly.evaluations[i].count}</td>
                  <td>{monthly.appointments[i].count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      <p className="muted tiny center"><Icon name="lock" size={14} /> Solo los administradores ven esta información. Actualizado: {generated}.</p>
    </div>
  )
}
