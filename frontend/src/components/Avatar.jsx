import { mediaUrl } from '../api/client'

const TONES = ['#FFD166', '#A8E0D6', '#D6B4EC', '#9DBDF0', '#FF9A7A']

// Foto de perfil; si no hay foto muestra las iniciales sobre un color fijo por persona
export default function Avatar({ user, size = 44, shape = 'circle', className = '' }) {
  const name = user?.full_name || `${user?.first_name ?? ''} ${user?.last_name ?? ''}`.trim() || '?'
  const initials = name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')
  const tone = TONES[(user?.id ?? name.length) % TONES.length]
  const radius = shape === 'rounded' ? Math.round(size * 0.27) : '50%'
  const style = { width: size, height: size, borderRadius: radius, fontSize: Math.round(size * 0.36) }

  if (user?.avatar_url) {
    return <img className={`avatar ${className}`} src={mediaUrl(user.avatar_url)} alt={`Foto de ${name}`} style={style} />
  }
  return (
    <span className={`avatar avatar--initials ${className}`} style={{ ...style, background: tone }} role="img" aria-label={name}>
      {initials}
    </span>
  )
}
