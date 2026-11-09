// Reglas que también valida el backend (Django password validators)
export const passwordRules = [
  { label: 'Mínimo 8 caracteres', test: (p) => p.length >= 8 },
  { label: 'Al menos una letra', test: (p) => /[A-Za-zÁÉÍÓÚáéíóúÑñ]/.test(p) },
  { label: 'Al menos un número', test: (p) => /\d/.test(p) },
]

export default function PasswordChecklist({ password }) {
  return (
    <ul className="checklist" aria-label="Requisitos de la contraseña">
      {passwordRules.map((rule) => {
        const ok = rule.test(password)
        return (
          <li key={rule.label} className={ok ? 'ok' : ''}>
            <span aria-hidden="true">{ok ? '✓' : '•'}</span> {rule.label}
          </li>
        )
      })}
    </ul>
  )
}
