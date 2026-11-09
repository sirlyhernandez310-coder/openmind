import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { evaluationsApi } from '../../api/evaluations'
import Alert from '../../components/Alert'
import Blob from '../../components/Blob'
import Icon from '../../components/Icon'

// la nube reacciona a la respuesta elegida
const ANSWER_MOODS = ['alegria', 'calma', 'ansiedad', 'tristeza']

export default function EvaluationPage() {
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [started, setStarted] = useState(false)
  const [index, setIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    evaluationsApi.questionnaire().then(setData).catch((err) => setError(err.message))
  }, [])

  if (error && !data) return <Alert>{error}</Alert>
  if (!data) return <p className="muted">Cargando evaluación…</p>

  const { questions, scale, instructions } = data
  const total = questions.length
  const question = questions[index]
  const answeredCount = Object.keys(answers).length
  const isLast = index === total - 1

  const choose = (value) => {
    setAnswers((a) => ({ ...a, [question.id]: value }))
    if (!isLast) setTimeout(() => setIndex((i) => Math.min(i + 1, total - 1)), 220)
  }

  const submit = async () => {
    const missing = questions.filter((q) => answers[q.id] === undefined)
    if (missing.length) {
      setError(`Te falta responder ${missing.length === 1 ? 'la pregunta' : 'las preguntas'} ${missing.map((q) => q.order).join(', ')}.`)
      setIndex(questions.indexOf(missing[0]))
      return
    }
    setError('')
    setSubmitting(true)
    try {
      const payload = questions.map((q) => ({ question: q.id, value: answers[q.id] }))
      const result = await evaluationsApi.submit(payload)
      navigate(`/paciente/historial/${result.id}`, { replace: true, state: { fresh: true } })
    } catch (err) {
      setError(err.fieldErrors?.answers || err.message)
      setSubmitting(false)
    }
  }

  // CA1: pantalla para iniciar la evaluación
  if (!started) {
    return (
      <section className="card eval-intro">
        <Blob mood="curiosa" size={150} className="float" />
        <span className="eyebrow">Evaluación emocional</span>
        <h1>¿Cómo has estado últimamente?</h1>
        <p className="muted">
          Son {total} preguntas cortas sobre tu ánimo, ansiedad, estrés, sueño y energía. Te tomará unos 3 minutos.
          No hay respuestas correctas o incorrectas: responde con sinceridad.
        </p>
        <ul className="eval-facts">
          <li><Icon name="smile" size={18} /> 3 minutos</li>
          <li><Icon name="shield" size={18} /> Solo tú ves tus resultados</li>
          <li><Icon name="chart" size={18} /> Se guarda en tu historial</li>
        </ul>
        <button type="button" className="btn btn--primary" onClick={() => setStarted(true)}>
          Iniciar evaluación
        </button>
        <p className="tiny muted">Es una herramienta orientativa y no reemplaza un diagnóstico profesional.</p>
      </section>
    )
  }

  // CA2 y CA3: preguntas una por una
  return (
    <section className="card eval">
      <div className="eval-top">
        <span className="muted">Pregunta {index + 1} de {total}</span>
        <span className="muted">{answeredCount}/{total} respondidas</span>
      </div>
      <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={answeredCount}>
        <span style={{ width: `${(answeredCount / total) * 100}%` }} />
      </div>

      <p className="eval-instructions">{instructions}</p>
      <div className="eval-question-row">
        <div>
          <span className="chip chip--static">{question.dimension_display}</span>
          <h2 className="eval-question" key={question.id}>{question.text}</h2>
        </div>
        <Blob mood={ANSWER_MOODS[answers[question.id]] ?? 'curiosa'} size={92} limbs={false} className="eval-blob" />
      </div>

      <div className="options" role="radiogroup" aria-label={question.text}>
        {scale.map((option) => {
          const selected = answers[question.id] === option.value
          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={selected}
              className={`option ${selected ? 'option--selected' : ''}`}
              onClick={() => choose(option.value)}
            >
              <span className="option-dot" aria-hidden="true">{option.value}</span>
              {option.label}
            </button>
          )
        })}
      </div>

      <Alert>{error}</Alert>

      <div className="eval-nav">
        <button type="button" className="btn btn--ghost" disabled={index === 0} onClick={() => setIndex((i) => i - 1)}>
          ← Anterior
        </button>
        {isLast ? (
          <button type="button" className="btn btn--primary" onClick={submit} disabled={submitting}>
            {submitting ? 'Procesando…' : 'Ver mi resultado'}
          </button>
        ) : (
          <button
            type="button"
            className="btn btn--primary"
            disabled={answers[question.id] === undefined}
            onClick={() => setIndex((i) => i + 1)}
          >
            Siguiente →
          </button>
        )}
      </div>
      <Link to="/paciente" className="link-sm eval-cancel">Cancelar evaluación</Link>
    </section>
  )
}
