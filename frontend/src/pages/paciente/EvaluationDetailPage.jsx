import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { evaluationsApi } from '../../api/evaluations'
import Alert from '../../components/Alert'
import Blob, { emotionLabel } from '../../components/Blob'
import ScoreRing from '../../components/ScoreRing'
import { LEVELS, formatDateTime, moodFor } from '../../format'

export default function EvaluationDetailPage() {
  const { id } = useParams()
  const location = useLocation()
  const fresh = location.state?.fresh
  const [evaluation, setEvaluation] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    evaluationsApi.detail(id).then(setEvaluation).catch((err) => setError(err.status === 404 ? 'Esta evaluación no existe.' : err.message))
  }, [id])

  if (error) {
    return (
      <>
        <Alert>{error}</Alert>
        <Link to="/paciente/historial" className="btn btn--ghost">← Volver al historial</Link>
      </>
    )
  }
  if (!evaluation) return <p className="muted">Cargando resultado…</p>

  const level = LEVELS[evaluation.level]
  const { interpretation } = evaluation
  const mood = moodFor(evaluation.level, interpretation.focus_dimension)

  return (
    <div className="result">
      <Link to="/paciente/historial" className="link-sm back">← Historial emocional</Link>

      <section className={`card result-hero result-hero--${level.tone}`}>
        <div className="result-hero-text">
          <span className="eyebrow">{fresh ? 'Tu resultado de hoy' : 'Resultado de la evaluación'}</span>
          <h1>{level.label}</h1>
          <span className={`level-pill level-pill--${level.tone}`}>Tu nube de hoy: {emotionLabel(mood)}</span>
          <p>{interpretation.summary}</p>
          <span className="muted tiny">{formatDateTime(evaluation.created_at)} · {evaluation.total_score} de {evaluation.max_score} puntos</span>
        </div>
        <div className="result-hero-visual">
          <Blob mood={mood} size={150} className="float" title={emotionLabel(mood)} />
          <div className="result-score">
            <ScoreRing value={evaluation.percentage} tone={level.tone} size={110} />
            <span className="tiny muted">Índice de malestar</span>
          </div>
        </div>
      </section>

      {evaluation.needs_support && (
        <section className="support">
          <div>
            <h2>No tienes que pasar por esto solo(a)</h2>
            <p>Tus respuestas sugieren que hablar con alguien ahora podría ayudarte.</p>
          </div>
          <div className="support-actions">
            <Link to="/paciente/emergencia" className="btn btn--sun">Abrir chat de emergencia</Link>
            <a href="tel:106" className="btn btn--light">Llamar a la Línea 106</a>
          </div>
        </section>
      )}

      <div className="result-grid">
        <section className="card">
          <h2>Por dimensión</h2>
          <ul className="bars">
            {Object.entries(evaluation.dimension_scores).map(([key, dim]) => (
              <li key={key}>
                <div className="bars-head">
                  <span>{dim.label}</span>
                  <span className={`level-pill level-pill--${LEVELS[dim.level].tone}`}>{LEVELS[dim.level].label}</span>
                </div>
                <div className="bar"><span className={`bar-fill bar-fill--${LEVELS[dim.level].tone}`} style={{ width: `${Math.max(dim.percentage, 3)}%` }} /></div>
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h2>Recomendaciones</h2>
          {interpretation.focus_dimension && (
            <p className="muted">Tu área con más malestar es <strong>{interpretation.focus_dimension.toLowerCase()}</strong>.</p>
          )}
          <ul className="tips">
            {interpretation.recommendations.map((tip) => <li key={tip}>{tip}</li>)}
          </ul>
        </section>
      </div>

      <details className="card answers">
        <summary>Ver mis respuestas</summary>
        <ol>
          {evaluation.answers.map((a) => (
            <li key={a.question}>
              <span>{a.question_text}</span>
              <strong>{a.value_label}</strong>
            </li>
          ))}
        </ol>
      </details>

      <p className="tiny muted center">{interpretation.disclaimer}</p>
      <div className="center">
        <Link to="/paciente/evaluacion" className="btn btn--ghost">Hacer una nueva evaluación</Link>
      </div>
    </div>
  )
}
