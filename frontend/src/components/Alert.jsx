const ICONS = { error: '!', success: '✓', info: 'i' }

export default function Alert({ type = 'error', children }) {
  if (!children) return null
  return (
    <div className={`alert alert--${type}`} role={type === 'error' ? 'alert' : 'status'}>
      <span className="alert-icon" aria-hidden="true">{ICONS[type]}</span>
      <div>{children}</div>
    </div>
  )
}
