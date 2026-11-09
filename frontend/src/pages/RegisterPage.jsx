import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Alert from '../components/Alert'
import AuthLayout from '../components/AuthLayout'
import FormField from '../components/FormField'
import PasswordChecklist from '../components/PasswordChecklist'
import { useAuth } from '../context/auth-context'
import { REQUIRED, compact, validateEmail } from '../validation'

const EMPTY = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  birth_date: '',
  password: '',
  password_confirm: '',
}

function validate(form) {
  return compact({
    first_name: form.first_name.trim() ? null : REQUIRED,
    last_name: form.last_name.trim() ? null : REQUIRED,
    email: validateEmail(form.email),
    phone: form.phone && !/^\+?[\d\s-]{7,20}$/.test(form.phone) ? 'Ingresa un teléfono válido.' : null,
    password: form.password ? (form.password.length < 8 ? 'Debe tener al menos 8 caracteres.' : null) : REQUIRED,
    password_confirm: !form.password_confirm
      ? REQUIRED
      : form.password_confirm !== form.password
        ? 'Las contraseñas no coinciden.'
        : null,
  })
}

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const update = (event) => {
    const { name, value } = event.target
    setForm((f) => ({ ...f, [name]: value }))
    setErrors((e) => ({ ...e, [name]: undefined }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setMessage('')
    const found = validate(form)
    setErrors(found)
    if (Object.keys(found).length) {
      setMessage('Revisa los campos marcados en rojo.')
      return
    }

    setSubmitting(true)
    try {
      const payload = { ...form, email: form.email.trim() }
      if (!payload.birth_date) payload.birth_date = null
      const data = await register(payload)
      // la cuenta queda pendiente hasta que confirme su correo
      navigate('/verifica-tu-correo', { replace: true, state: { email: data.email } })
    } catch (error) {
      setErrors(error.fieldErrors ?? {})
      setMessage(error.message.startsWith('Error') ? 'Revisa los campos marcados en rojo.' : error.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Crea tu cuenta"
      subtitle="Empieza a cuidar tu bienestar emocional. Solo toma un minuto."
      mood="happy"
      footer={<>¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link><br />¿Eres psicólogo? <Link to="/registro-profesional">Regístrate como profesional</Link></>}
    >
      <Alert>{message}</Alert>
      {errors.email?.includes('aún no ha sido confirmado') && (
        <Alert type="info">
          <Link to="/verifica-tu-correo" state={{ email: form.email.trim().toLowerCase() }}>Reenviar el enlace de confirmación</Link>
        </Alert>
      )}
      {errors.email?.includes('ya se encuentra registrado') && (
        <Alert type="info">
          Ese correo ya tiene una cuenta. <Link to="/login" state={{ email: form.email }}>Inicia sesión</Link> o{' '}
          <Link to="/recuperar-contrasena">recupera tu contraseña</Link>.
        </Alert>
      )}
      <form onSubmit={handleSubmit} noValidate>
        <div className="grid-2">
          <FormField label="Nombres" name="first_name" autoComplete="given-name" value={form.first_name} onChange={update} error={errors.first_name} />
          <FormField label="Apellidos" name="last_name" autoComplete="family-name" value={form.last_name} onChange={update} error={errors.last_name} />
        </div>
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
        <div className="grid-2">
          <FormField label="Teléfono" name="phone" type="tel" optional autoComplete="tel" placeholder="300 123 4567" value={form.phone} onChange={update} error={errors.phone} />
          <FormField label="Fecha de nacimiento" name="birth_date" type="date" optional value={form.birth_date} onChange={update} error={errors.birth_date} />
        </div>
        <FormField
          label="Contraseña"
          name="password"
          type="password"
          autoComplete="new-password"
          value={form.password}
          onChange={update}
          error={errors.password}
        />
        <PasswordChecklist password={form.password} />
        <FormField
          label="Confirmar contraseña"
          name="password_confirm"
          type="password"
          autoComplete="new-password"
          value={form.password_confirm}
          onChange={update}
          error={errors.password_confirm}
        />
        <button type="submit" className="btn btn--primary btn--block" disabled={submitting}>
          {submitting ? 'Creando cuenta…' : 'Crear cuenta'}
        </button>
      </form>
    </AuthLayout>
  )
}
