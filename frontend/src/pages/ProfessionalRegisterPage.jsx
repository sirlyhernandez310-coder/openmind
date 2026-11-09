import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { professionalsApi } from '../api/professionals'
import Alert from '../components/Alert'
import AuthLayout from '../components/AuthLayout'
import FormField from '../components/FormField'
import PasswordChecklist from '../components/PasswordChecklist'
import ProfessionalFields, { validateProfessional } from '../components/ProfessionalFields'
import { REQUIRED, compact, validateEmail } from '../validation'

const EMPTY = {
  first_name: '', last_name: '', email: '', phone: '', password: '', password_confirm: '',
  specialty: '', years_experience: '', license_number: '', university: '', experience: '', description: '',
}

export default function ProfessionalRegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [specialties, setSpecialties] = useState([])
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    professionalsApi.specialties().then(setSpecialties).catch(() => {})
  }, [])

  const update = (event) => {
    const { name, value } = event.target
    setForm((f) => ({ ...f, [name]: value }))
    setErrors((e) => ({ ...e, [name]: undefined }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setMessage('')
    const found = {
      ...compact({
        first_name: form.first_name.trim() ? null : REQUIRED,
        last_name: form.last_name.trim() ? null : REQUIRED,
        email: validateEmail(form.email),
        password: form.password ? (form.password.length < 8 ? 'Debe tener al menos 8 caracteres.' : null) : REQUIRED,
        password_confirm: !form.password_confirm ? REQUIRED : form.password_confirm !== form.password ? 'Las contraseñas no coinciden.' : null,
      }),
      ...validateProfessional(form),
    }
    setErrors(found)
    if (Object.keys(found).length) {
      setMessage('Revisa los campos marcados en rojo.')
      return
    }
    setSubmitting(true)
    try {
      const data = await professionalsApi.register({ ...form, email: form.email.trim(), years_experience: Number(form.years_experience) })
      navigate('/verifica-tu-correo', { replace: true, state: { email: data.email } })
    } catch (err) {
      setErrors(err.fieldErrors ?? {})
      setMessage(err.message.startsWith('Error') ? 'Revisa los campos marcados en rojo.' : err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Únete como profesional"
      subtitle="Registra tu perfil de psicólogo para acompañar a pacientes en OpenMind."
      mood="thinking"
      wide
      footer={<>¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link> · ¿Buscas ayuda? <Link to="/registro">Regístrate como paciente</Link></>}
    >
      <Alert>{message}</Alert>
      <form onSubmit={handleSubmit} noValidate>
        <h2 className="form-section">1. Tus datos</h2>
        <div className="grid-2">
          <FormField label="Nombres" name="first_name" autoComplete="given-name" value={form.first_name} onChange={update} error={errors.first_name} />
          <FormField label="Apellidos" name="last_name" autoComplete="family-name" value={form.last_name} onChange={update} error={errors.last_name} />
        </div>
        <div className="grid-2">
          <FormField label="Correo electrónico" name="email" type="email" autoComplete="email" value={form.email} onChange={update} error={errors.email} />
          <FormField label="Teléfono" name="phone" type="tel" optional value={form.phone} onChange={update} error={errors.phone} />
        </div>
        <div className="grid-2">
          <FormField label="Contraseña" name="password" type="password" autoComplete="new-password" value={form.password} onChange={update} error={errors.password} />
          <FormField label="Confirmar contraseña" name="password_confirm" type="password" autoComplete="new-password" value={form.password_confirm} onChange={update} error={errors.password_confirm} />
        </div>
        <PasswordChecklist password={form.password} />

        <h2 className="form-section">2. Datos profesionales</h2>
        <ProfessionalFields form={form} errors={errors} specialties={specialties} onChange={update} />

        <p className="tiny muted">Un administrador verificará tu tarjeta profesional antes de que puedas atender emergencias.</p>
        <button type="submit" className="btn btn--primary btn--block" disabled={submitting}>
          {submitting ? 'Registrando…' : 'Crear mi perfil profesional'}
        </button>
      </form>
    </AuthLayout>
  )
}
