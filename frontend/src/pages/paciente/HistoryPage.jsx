import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { evaluationsApi } from '../../api/evaluations'
import Alert from '../../components/Alert'
import Blob from '../../components/Blob'
import PageHeader from '../../components/PageHeader'
import TrendChart from '../../components/TrendChart'
import { LEVELS, formatDate, formatTime } from '../../format'

export default function HistoryPage() {
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    evaluationsApi.history().then(setItems).catch((err) => setError(err.message))
  }, [])

  if (error) return <Alert>{error}</Alert>
  if (!items) return <p className="muted">Cargando historial…</p>

  return (
    <>
      <PageHeader eyebrow="Historial emocional" title="Tu evolución" mood="thinking">
        Aquí están todas tus evaluaciones. Solo tú puedes verlas.
      </PageHeader>

      {items.length === 0 ? (
        <section className="card empty">
          <Blob mood="sleepy" size={96} />
          <h2>Aún no tienes evaluaciones</h2>
          <p className="muted">Haz tu primera evaluación para empezar a ver tu evolución.</p>
          <Link to="/paciente/evaluacion" className="btn btn--primary">Hacer mi primera evaluación</Link>
        </section>
      ) : (
        <>
          <section className="card">
            <div className="card-head">
              <h2>Índice de malestar en el tiempo</h2>
              <span className="tiny muted">Más bajo = más bienestar</span>
            </div>
            <TrendChart items={items} />
          </section>

          <section className="card">
            <div className="card-head">
              <h2>Evaluaciones realizadas ({items.length})</h2>
              <Link to="/paciente/evaluacion" className="btn btn--primary btn--sm">Nueva evaluación</Link>
            </div>
            <ul className="history">
              {items.map((item) => {
                const level = LEVELS[item.level]
                return (
                  <li key={item.id}>
                    <Link to={`/paciente/historial/${item.id}`} className="history-item">
                      <span className={`history-dot history-dot--${level.tone}`} aria-hidden="true" />
                      <span className="history-date">
                        <strong>{formatDate(item.created_at)}</strong>
                        <span className="muted tiny">{formatTime(item.created_at)}</span>
                      </span>
                      <span className={`level-pill level-pill--${level.tone}`}>{item.level_display}</span>
                      <span className="history-score">{item.percentage}%</span>
                      <span className="history-arrow" aria-hidden="true">→</span>
                    </Link>
                  </li>
                )
              })}
            </ul>
          </section>
        </>
      )}
    </>
  )
}
