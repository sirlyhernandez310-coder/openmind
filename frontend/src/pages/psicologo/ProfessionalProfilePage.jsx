import { useEffect, useState } from 'react'
import { professionalsApi } from '../../api/professionals'
import Alert from '../../components/Alert'
import Avatar from '../../components/Avatar'
import PhotoCard from '../../components/PhotoCard'
import PageHeader from '../../components/PageHeader'
import ProfessionalFields, { validateProfessional } from '../../components/ProfessionalFields'
import { useAuth } from '../../context/auth-context'
import { formatDate } from '../../format'

const FIELDS = ['specialty', 'years_experience', 'license_number', 'university', 'experience', 'description']

export default function ProfessionalProfilePage() {
  const { user } = useAuth()
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
    const found = validateProfessional(form)
    setErrors(found)
    if (Object.keys(found).length) return
    setSaving(true)
    try {
      load(await professionalsApi.updateMyProfile({ ...form, years_experience: Number(form.years_experience) }))
      setEditing(false)
      setMessage({ type: 'success', text: 'Tu perfil fue actualizado.' })
    } catch (err) {
      setErrors(err.fieldErrors ?? {})
      setMessage({ type: 'error', text: err.message.startsWith('Error') ? '' : err.message })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="stack">
      <PageHeader eyebrow="Perfil profesional" title={profile.user.full_name} aside={<Avatar user={user} size={120} className="page-header-avatar" />}>
        {profile.specialty_display} · {profile.years_experience} {profile.years_experience === 1 ? 'año' : 'años'} de experiencia
      </PageHeader>
      <Alert type={message.type}>{message.text}</Alert>
      <PhotoCard hint="Los pacientes verán tu foto en el directorio de psicólogos y en el chat." />

      {editing ? (
        <section className="card">
          <h2>Editar datos profesionales</h2>
          <form onSubmit={save} noValidate className="form-spaced">
            <ProfessionalFields form={form} errors={errors} specialties={specialties} onChange={update} />
            <div className="form-actions">
              <button type="button" className="btn btn--ghost" onClick={() => { setEditing(false); load(profile) }}>Cancelar</button>
              <button type="submit" className="btn btn--primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar cambios'}</button>
            </div>
          </form>
        </section>
      ) : (
        <section className="card profile-card">
          <div className="card-head">
            <h2>Tu perfil</h2>
            <div className="card-head-actions">
              <span className={`verify-pill ${profile.is_verified ? 'verify-pill--ok' : ''}`}>
                {profile.is_verified ? '✓ Verificado' : 'Pendiente de verificación'}
              </span>
              <button type="button" className="btn btn--ghost btn--sm" onClick={() => setEditing(true)}>Editar</button>
            </div>
          </div>
          <dl>
            <div><dt>Especialidad</dt><dd>{profile.specialty_display}</dd></div>
            <div><dt>Experiencia</dt><dd>{profile.years_experience} años</dd></div>
            <div><dt>Tarjeta profesional</dt><dd>{profile.license_number}</dd></div>
            <div><dt>Universidad</dt><dd>{profile.university || '—'}</dd></div>
            <div><dt>Correo</dt><dd>{profile.user.email}</dd></div>
            <div><dt>Registrado</dt><dd>{formatDate(profile.created_at)}</dd></div>
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
      )}
    </div>
  )
}
