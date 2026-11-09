import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { authApi } from '../api/auth'
import Alert from '../components/Alert'
import AuthLayout from '../components/AuthLayout'
import FormField from '../components/FormField'
import PasswordChecklist from '../components/PasswordChecklist'
import { REQUIRED, compact } from '../validation'

export default function ResetPasswordPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const uid = params.get('uid') ?? ''
  const token = params.get('token') ?? ''

  const [status, setStatus] = useState(uid && token ? 'checking' : 'invalid') // checking | ready | invalid
  const [email, setEmail] = useState('')
  const [form, setForm] = useState({ password: '', password_confirm: '' })
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // al abrir el enlace verificamos que siga vigente
  useEffect(() => {
    if (!uid || !token) return
    authApi
      .validateResetLink(uid, token)
      .then((data) => {
        setEmail(data.email)
        setStatus('ready')
      })
      .catch((err) => {
        setMessage(err.message)
        setStatus('invalid')
      })
  }, [uid, token])

  const update = (event) => {
    const { name, value } = event.target
    setForm((f) => ({ ...f, [name]: value }))
    setErrors((e) => ({ ...e, [name]: undefined }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setMessage('')
    const found = compact({
      password: form.password ? null : REQUIRED,
      password_confirm: !form.password_confirm
        ? REQUIRED
        : form.password_confirm !== form.password
          ? 'Las contraseñas no coinciden.'
          : null,
    })
    setErrors(found)
    if (Object.keys(found).length) return

    setSubmitting(true)
    try {
      const data = await authApi.confirmPasswordReset({ uid, token, ...form })
      navigate('/login', { replace: true, state: { success: data.detail, email } })
    } catch (err) {
      setErrors(err.fieldErrors ?? {})
      setMessage(err.message.startsWith('Error') ? '' : err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (status === 'checking') {
    return (
      <AuthLayout title="Un momento…" mood="thinking">
        <p className="muted">Estamos verificando tu enlace de recuperación.</p>
      </AuthLayout>
    )
  }

  if (status === 'invalid') {
    return (
      <AuthLayout title="Enlace no válido" mood="sleepy" footer={<Link to="/login">← Volver a iniciar sesión</Link>}>
        <Alert>{message || 'El enlace de recuperación no es válido o ya expiró. Solicita uno nuevo.'}</Alert>
        <Link to="/recuperar-contrasena" className="btn btn--primary btn--block">Solicitar un nuevo enlace</Link>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      title="Crea una nueva contraseña"
      subtitle={<>Para la cuenta <strong>{email}</strong>.</>}
      footer={<Link to="/login">← Volver a iniciar sesión</Link>}
    >
      <Alert>{message}</Alert>
      <form onSubmit={handleSubmit} noValidate>
        <FormField label="Nueva contraseña" name="password" type="password" autoComplete="new-password" value={form.password} onChange={update} error={errors.password} />
        <PasswordChecklist password={form.password} />
        <FormField label="Confirmar contraseña" name="password_confirm" type="password" autoComplete="new-password" value={form.password_confirm} onChange={update} error={errors.password_confirm} />
        <button type="submit" className="btn btn--primary btn--block" disabled={submitting}>
          {submitting ? 'Guardando…' : 'Guardar contraseña'}
        </button>
      </form>
    </AuthLayout>
  )
}
