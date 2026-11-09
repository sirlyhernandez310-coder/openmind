import { useId, useState } from 'react'

export default function FormField({ label, error, hint, type = 'text', optional = false, ...inputProps }) {
  const id = useId()
  const [visible, setVisible] = useState(false)
  const isPassword = type === 'password'

  return (
    <div className={`field ${error ? 'field--error' : ''}`}>
      <label htmlFor={id}>
        {label}
        {optional && <span className="field-optional"> (opcional)</span>}
      </label>
      <div className="field-control">
        <input
          id={id}
          type={isPassword && visible ? 'text' : type}
          aria-invalid={Boolean(error)}
          aria-describedby={error || hint ? `${id}-msg` : undefined}
          {...inputProps}
        />
        {isPassword && (
          <button
            type="button"
            className="field-toggle"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
          >
            {visible ? 'Ocultar' : 'Ver'}
          </button>
        )}
      </div>
      {(error || hint) && (
        <small id={`${id}-msg`} className={error ? 'field-error' : 'field-hint'}>
          {error || hint}
        </small>
      )}
    </div>
  )
}
