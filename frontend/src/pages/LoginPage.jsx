import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import Alert from '../components/Alert'
import AuthLayout from '../components/AuthLayout'
import FormField from '../components/FormField'
import { homeForRole } from '../constants/roles'
import { useAuth } from '../context/auth-context'
import { REQUIRED, compact, validateEmail } from '../validation'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: location.state?.email ?? '', password: '' })
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [unverified, setUnverified] = useState(null)

  const update = (event) => {
    const { name, value } = event.target
    setForm((f) => ({ ...f, [name]: value }))
    setErrors((e) => ({ ...e, [name]: undefined }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setMessage('')
    setUnverified(null)
    const found = compact({ email: validateEmail(form.email), password: form.password ? null : REQUIRED })
    setErrors(found)
    if (Object.keys(found).length) return

    setSubmitting(true)
    try {
      const user = await login(form.email.trim(), form.password)
      // el sistema identifica el tipo de usuario y abre su interfaz
      navigate(homeForRole(user.role), { replace: true })
    } catch (error) {
      if (error.data?.code === 'email_not_verified') {
        setUnverified(error.data.email)
        return
      }
      setErrors(error.fieldErrors ?? {})
      setMessage(error.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Bienvenido de nuevo"
      subtitle="Ingresa con tu correo y contraseña para continuar."
      footer={<>¿Aún no tienes cuenta? <Link to="/registro">Regístrate</Link><br />¿Eres psicólogo? <Link to="/registro-profesional">Únete como profesional</Link></>}
    >
      {location.state?.success && <Alert type="success">{location.state.success}</Alert>}
      <Alert>{message}</Alert>
      {unverified && (
        <Alert type="info">
          Debes confirmar tu correo antes de iniciar sesión.{' '}
          <Link to="/verifica-tu-correo" state={{ email: unverified }}>Reenviar el enlace a {unverified}</Link>
        </Alert>
      )}
      <form onSubmit={handleSubmit} noValidate>
        <FormField
          label="Correo electrónico"
          name="email"
          type="email"
          autoComplete="email"
          placeholder="nombre@correo.com"
          value={form.email}
          onChange={update}
          error={errors.email}
        />
        <FormField
          label="Contraseña"
          name="password"
          type="password"
          autoComplete="current-password"
          placeholder="Tu contraseña"
          value={form.password}
          onChange={update}
          error={errors.password}
        />
        <div className="form-row-end">
          <Link to="/recuperar-contrasena" className="link-sm">¿Olvidaste tu contraseña?</Link>
        </div>
        <button type="submit" className="btn btn--primary btn--block" disabled={submitting}>
          {submitting ? 'Ingresando…' : 'Iniciar sesión'}
        </button>
      </form>
    </AuthLayout>
  )
}
