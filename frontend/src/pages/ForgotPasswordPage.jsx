import { useState } from 'react'
import { Link } from 'react-router-dom'
import { authApi } from '../api/auth'
import Alert from '../components/Alert'
import AuthLayout from '../components/AuthLayout'
import FormField from '../components/FormField'
import { validateEmail } from '../validation'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [sentTo, setSentTo] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setMessage('')
    const emailError = validateEmail(email)
    setError(emailError ?? '')
    if (emailError) return

    setSubmitting(true)
    try {
      await authApi.requestPasswordReset(email.trim())
      setSentTo(email.trim().toLowerCase())
    } catch (err) {
      setError(err.fieldErrors?.email ?? '')
      setMessage(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (sentTo) {
    return (
      <AuthLayout title="Revisa tu correo" mood="happy" footer={<Link to="/login">← Volver a iniciar sesión</Link>}>
        <div className="sent">
          <div className="sent-icon" aria-hidden="true">✉</div>
          <p>
            Enviamos las instrucciones para recuperar tu contraseña a <strong>{sentTo}</strong>.
          </p>
          <p className="muted">
            El enlace vence en 1 hora. Si no lo ves, revisa la carpeta de spam o correo no deseado.
          </p>
          <button type="button" className="btn btn--ghost btn--block" onClick={() => setSentTo(null)}>
            Usar otro correo
          </button>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      title="¿Olvidaste tu contraseña?"
      subtitle="Escribe el correo con el que te registraste y te enviaremos las instrucciones."
      mood="thinking"
      footer={<Link to="/login">← Volver a iniciar sesión</Link>}
    >
      <Alert>{message}</Alert>
      {message.includes('No encontramos') && (
        <Alert type="info">
          ¿Aún no tienes cuenta? <Link to="/registro">Regístrate aquí</Link>.
        </Alert>
      )}
      <form onSubmit={handleSubmit} noValidate>
        <FormField
          label="Correo electrónico"
          name="email"
          type="email"
          autoComplete="email"
          placeholder="nombre@correo.com"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            setError('')
          }}
          error={error}
        />
        <button type="submit" className="btn btn--primary btn--block" disabled={submitting}>
          {submitting ? 'Enviando…' : 'Enviar instrucciones'}
        </button>
      </form>
    </AuthLayout>
  )
}
