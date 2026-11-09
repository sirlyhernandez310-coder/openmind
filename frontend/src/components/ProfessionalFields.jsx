import { useId } from 'react'
import FormField from './FormField'

// Campos profesionales compartidos entre el registro y la edición del perfil
export default function ProfessionalFields({ form, errors, specialties, onChange }) {
  const selectId = useId()
  const descId = useId()
  const expId = useId()
  return (
    <>
      <div className={`field ${errors.specialty ? 'field--error' : ''}`}>
        <label htmlFor={selectId}>Especialidad</label>
        <select id={selectId} name="specialty" value={form.specialty} onChange={onChange} aria-invalid={Boolean(errors.specialty)}>
          <option value="">Selecciona tu especialidad</option>
          {specialties.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        {errors.specialty && <small className="field-error">{errors.specialty}</small>}
      </div>

      <div className="grid-2">
        <FormField label="Años de experiencia" name="years_experience" type="number" min="0" max="60" inputMode="numeric"
          value={form.years_experience} onChange={onChange} error={errors.years_experience} />
        <FormField label="Tarjeta profesional" name="license_number" placeholder="Ej: TP-123456" autoComplete="off"
          value={form.license_number} onChange={onChange} error={errors.license_number}
          hint={errors.license_number ? undefined : 'Número de tu tarjeta profesional de psicólogo.'} />
      </div>

      <FormField label="Universidad" name="university" optional value={form.university} onChange={onChange} error={errors.university} />

      <div className={`field ${errors.experience ? 'field--error' : ''}`}>
        <label htmlFor={expId}>Experiencia <span className="field-optional">(opcional)</span></label>
        <textarea id={expId} name="experience" rows={3} maxLength={1000} value={form.experience} onChange={onChange}
          placeholder="Lugares donde has trabajado, poblaciones que has atendido, enfoques…" />
        {errors.experience && <small className="field-error">{errors.experience}</small>}
      </div>

      <div className={`field ${errors.description ? 'field--error' : ''}`}>
        <label htmlFor={descId}>Descripción profesional</label>
        <textarea id={descId} name="description" rows={4} maxLength={1000} value={form.description} onChange={onChange}
          placeholder="Cuéntale a los pacientes cómo trabajas y en qué puedes ayudarles." aria-invalid={Boolean(errors.description)} />
        <small className={errors.description ? 'field-error' : 'field-hint'}>
          {errors.description || `${form.description.length}/1000 · mínimo 30 caracteres`}
        </small>
      </div>
    </>
  )
}

export function validateProfessional(form) {
  const errors = {}
  if (!form.specialty) errors.specialty = 'Selecciona tu especialidad.'
  if (form.years_experience === '' || form.years_experience === null) errors.years_experience = 'Este campo es obligatorio.'
  else if (Number(form.years_experience) < 0 || Number(form.years_experience) > 60) errors.years_experience = 'Ingresa un número entre 0 y 60.'
  if (!form.license_number.trim()) errors.license_number = 'Este campo es obligatorio.'
  else if (!/^[A-Za-z0-9-\s]{4,30}$/.test(form.license_number.trim())) errors.license_number = 'Solo letras, números y guiones (4 a 30).'
  if (form.description.trim().length < 30) errors.description = 'Escribe al menos 30 caracteres.'
  return errors
}
