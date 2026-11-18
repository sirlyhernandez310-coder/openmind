import { useEffect, useState } from 'react'
import { professionalsApi } from '../../api/professionals'
import Alert from '../../components/Alert'
import Avatar from '../../components/Avatar'
import FormField from '../../components/FormField'
import Icon from '../../components/Icon'
import PhotoCard from '../../components/PhotoCard'
import PageHeader from '../../components/PageHeader'
import ProfessionalFields, { validateProfessional } from '../../components/ProfessionalFields'
import { useAuth } from '../../context/auth-context'
import { formatDate } from '../../format'
import { REQUIRED, compact } from '../../validation'

// Datos que el psicólogo puede modificar (el correo y la tarjeta profesional no)
const FIELDS = ['first_name', 'last_name', 'phone', 'specialty', 'years_experience', 'license_number', 'university', 'experience', 'description']
const years = (n) => `${n} ${n === 1 ? 'año' : 'años'}`

function validate(form) {
  return {
    ...compact({
      first_name: form.first_name.trim() ? null : REQUIRED,
      last_name: form.last_name.trim() ? null : REQUIRED,
      phone: form.phone && !/^\+?[\d\s]{7,20}$/.test(form.phone.trim()) ? 'Ingresa un teléfono válido (solo números).' : null,
    }),
    ...validateProfessional(form),
  }
}

// OM3-22 Gestionar perfil profesional
export default function ProfessionalProfilePage() {
  const { user, updateUser } = useAuth()
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState(null)
  const [specialties, setSpecialties] = useState([])
  const [editing, setEditing] = useState(false)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState({ type: 'error', text: '' })
  const [saving, setSaving] = useState(false)

  const load = (data) => {
    setProfile(data)
    setForm(Object.fromEntries(FIELDS.map((f) => [f, data[f] ?? ''])))
  }

  useEffect(() => {
    professionalsApi.myProfile().then(load).catch((err) => setMessage({ type: 'error', text: err.message }))
    professionalsApi.specialties().then(setSpecialties).catch(() => {})
  }, [])

  if (!profile) return message.text ? <Alert>{message.text}</Alert> : <p className="muted">Cargando perfil…</p>

  const update = (event) => {
    const { name, value } = event.target
    setForm((f) => ({ ...f, [name]: value }))
    setErrors((e) => ({ ...e, [name]: undefined }))
  }

  const save = async (event) => {
    event.preventDefault()
    const found = validate(form)
    setErrors(found)
    if (Object.keys(found).length) {
      setMessage({ type: 'error', text: 'Revisa los campos marcados en rojo.' })
      return
    }
    setSaving(true)
    try {
      const { license_number: _ignored, ...changes } = form
      const saved = await professionalsApi.updateMyProfile({ ...changes, years_experience: Number(form.years_experience) })
      load(saved)
      // el nombre nuevo también se ve en la barra superior
      updateUser({ ...user, first_name: saved.first_name, last_name: saved.last_name, full_name: saved.user.full_name, phone: saved.phone })
      setEditing(false)
      setMessage({ type: 'success', text: '¡Listo! Tus cambios quedaron guardados y ya los ven los pacientes.' })
    } catch (err) {
      setErrors(err.fieldErrors ?? {})
      setMessage({ type: 'error', text: err.message.startsWith('Error') ? 'Revisa los campos marcados en rojo.' : err.message })
    } finally {
      setSaving(false)
    }
  }

  const cancel = () => {
    setEditing(false)
    setErrors({})
    setMessage({ type: 'error', text: '' })
    load(profile)
  }

  return (
    <div className="stack">
      <PageHeader eyebrow="Perfil profesional" title={profile.user.full_name} aside={<Avatar user={user} size={120} className="page-header-avatar" />}>
        {profile.specialty_display} · {years(profile.years_experience)} de experiencia
      </PageHeader>
      <Alert type={message.type}>{message.text}</Alert>

      {editing ? (
        <section className="card">
          <h2>Editar mi perfil</h2>
          <form onSubmit={save} noValidate className="form-spaced">
            <h3 className="form-section">1. Datos personales</h3>
            <div className="grid-2">
              <FormField label="Nombres" name="first_name" value={form.first_name} onChange={update} error={errors.first_name} />
              <FormField label="Apellidos" name="last_name" value={form.last_name} onChange={update} error={errors.last_name} />
            </div>
            <div className="grid-2">
              <FormField label="Teléfono" name="phone" type="tel" optional value={form.phone} onChange={update} error={errors.phone} />
              <FormField label="Correo electrónico" name="email" value={profile.user.email} readOnly
                hint="Es tu usuario para iniciar sesión; no se puede cambiar." />
            </div>
            <h3 className="form-section">2. Datos profesionales</h3>
            <ProfessionalFields form={form} errors={errors} specialties={specialties} onChange={update} licenseLocked />
            <div className="form-actions">
              <button type="button" className="btn btn--ghost" onClick={cancel}>Cancelar</button>
              <button type="submit" className="btn btn--primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar cambios'}</button>
            </div>
          </form>
        </section>
      ) : (
        <div className="profile-layout">
          <section className="card profile-card">
            <div className="card-head">
              <h2>Mi información</h2>
              <div className="card-head-actions">
                <span className={`verify-pill ${profile.is_verified ? 'verify-pill--ok' : ''}`}>
                  {profile.is_verified ? '✓ Verificado' : 'Pendiente de verificación'}
                </span>
                <button type="button" className="btn btn--primary btn--sm" onClick={() => setEditing(true)}>Editar perfil</button>
              </div>
            </div>
            <dl>
              <div><dt>Nombre</dt><dd>{profile.user.full_name}</dd></div>
              <div><dt>Correo</dt><dd>{profile.user.email}</dd></div>
              <div><dt>Teléfono</dt><dd>{profile.phone || '—'}</dd></div>
              <div><dt>Especialidad</dt><dd>{profile.specialty_display}</dd></div>
              <div><dt>Experiencia</dt><dd>{years(profile.years_experience)}</dd></div>
              <div><dt>Tarjeta profesional</dt><dd>{profile.license_number}</dd></div>
              <div><dt>Universidad</dt><dd>{profile.university || '—'}</dd></div>
              <div><dt>Registrado</dt><dd>{formatDate(profile.created_at)}</dd></div>
              <div><dt>Última actualización</dt><dd>{formatDate(profile.updated_at)}</dd></div>
            </dl>
            <h3 className="profile-subtitle">Descripción</h3>
            <p className="profile-text">{profile.description}</p>
            {profile.experience && (
              <>
                <h3 className="profile-subtitle">Experiencia</h3>
                <p className="profile-text">{profile.experience}</p>
              </>
            )}
          </section>

          <aside className="stack">
            <section className="card preview-card">
              <span className="eyebrow"><Icon name="users" size={16} /> Así te ven los pacientes</span>
              <div className="psy-card">
                <Avatar user={user} size={96} shape="rounded" />
                <div className="psy-card-body">
                  <h3>{profile.user.full_name}</h3>
                  <span className="level-pill level-pill--mint">{profile.specialty_display} · {years(profile.years_experience)}</span>
                  <p className="clamp-2">{profile.description}</p>
                </div>
              </div>
              {!profile.is_verified && <p className="tiny muted">Aparecerás en el directorio cuando el administrador verifique tu tarjeta.</p>}
            </section>
            <PhotoCard hint="Los pacientes verán tu foto en el directorio, en sus citas y en el chat." />
          </aside>
        </div>
      )}
    </div>
  )
}
