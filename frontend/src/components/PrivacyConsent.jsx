import { Link } from 'react-router-dom'

export const PRIVACY_REQUIRED = 'Debes aceptar la política de tratamiento de datos personales.'

// OM3-26: autorización del tratamiento de datos (Ley 1581 de 2012) al crear la cuenta
export default function PrivacyConsent({ checked, onChange, error }) {
  return (
    <div className={`consent ${error ? 'consent--error' : ''}`}>
      <label>
        <input type="checkbox" name="accept_privacy" checked={checked} onChange={(e) => onChange(e.target.checked)} />
        <span>
          Autorizo el tratamiento de mis datos personales según la{' '}
          <Link to="/privacidad" target="_blank" rel="noopener">política de privacidad</Link> (Ley 1581 de 2012).
        </span>
      </label>
      {error && <span className="field-error">{error}</span>}
    </div>
  )
}
