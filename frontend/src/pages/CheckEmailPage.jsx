import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { authApi } from '../api/auth'
import Alert from '../components/Alert'
import AuthLayout from '../components/AuthLayout'
import FormField from '../components/FormField'
import { validateEmail } from '../validation'

const COOLDOWN = 60

// Pantalla que se muestra después de registrarse: "revisa tu correo"
export default function CheckEmailPage() {
  const location = useLocation()
  const [email, setEmail] = useState(location.state?.email ?? '')
  const [known] = useState(Boolean(location.state?.email))
  const [message, setMessage] = useState({ type: 'error', text: '' })
  const [error, setError] = useState('')
  const [wait, setWait] = useState(known ? COOLDOWN : 0)
  const [sending, setSending] = useState(false)

  useEffect(() => {
    if (wait <= 0) return undefined
    const id = setTimeout(() => setWait((w) => w - 1), 1000)
    return () => clearTimeout(id)
  }, [wait])

  const resend = async () => {
    const emailError = validateEmail(email)
    setError(emailError ?? '')
    if (emailError) return
    setSending(true)
    try {
      const data = await authApi.resendVerification(email.trim())
      setMessage({ type: 'success', text: data.detail })
      setWait(COOLDOWN)
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setSending(false)
    }
  }

  return (
    <AuthLayout title="Confirma tu correo" mood="happy" footer={<Link to="/login">← Ir a iniciar sesión</Link>}>
      <div className="sent">
        <div className="sent-icon" aria-hidden="true">✉</div>
        {known ? (
          <p>Te enviamos un enlace a <strong>{email}</strong>. Ábrelo para activar tu cuenta.</p>
        ) : (
          <p>Escribe el correo con el que te registraste y te enviaremos un nuevo enlace de confirmación.</p>
        )}
        <p className="muted">El enlace vence en 24 horas. Si no lo ves, revisa la carpeta de spam o correo no deseado.</p>
      </div>
      <Alert type={message.type}>{message.text}</Alert>
      {!known && (
        <FormField label="Correo electrónico" name="email" type="email" value={email}
          onChange={(e) => { setEmail(e.target.value); setError('') }} error={error} />
      )}
      <button type="button" className="btn btn--ghost btn--block mt" onClick={resend} disabled={sending || wait > 0}>
        {sending ? 'Enviando…' : wait > 0 ? `Reenviar enlace en ${wait} s` : known ? 'Reenviar enlace' : 'Enviar enlace'}
      </button>
    </AuthLayout>
  )
}
