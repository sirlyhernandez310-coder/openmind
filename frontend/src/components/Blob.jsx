// Personajes de OpenMind: nubes suaves que expresan una emoción.
// mood: alegria | calma | ansiedad | tristeza | enojo | curiosa
// (también acepta los nombres antiguos happy, calm, thinking, sleepy)

const CLOUD =
  'M30 98c-14 0-24-10-24-23 0-12 9-21 20-22 1-15 13-27 28-27 9 0 17 4 22 11 3-2 7-3 11-3 14 0 25 11 25 25v1c8 3 13 10 13 19 0 11-9 19-20 19z'
const INK = '#4A1858'

const ALIASES = { happy: 'alegria', calm: 'calma', thinking: 'curiosa', sleepy: 'tristeza' }

const LABELS = {
  alegria: 'Alegría',
  calma: 'Calma',
  ansiedad: 'Ansiedad',
  tristeza: 'Tristeza',
  enojo: 'Enojo',
  curiosa: 'Nube curiosa',
}

const Cheeks = ({ color = '#FF8FB1', opacity = 0.7, y = 78 }) => (
  <>
    <ellipse cx="45" cy={y} rx="5.5" ry="3.2" fill={color} opacity={opacity} />
    <ellipse cx="87" cy={y} rx="5.5" ry="3.2" fill={color} opacity={opacity} />
  </>
)

const stroke = { stroke: INK, strokeWidth: 3.5, fill: 'none', strokeLinecap: 'round', strokeLinejoin: 'round' }
const limb = { stroke: INK, strokeWidth: 5, fill: 'none', strokeLinecap: 'round', strokeLinejoin: 'round' }

const CHARACTERS = {
  alegria: {
    color: '#FFD166',
    arms: 'M16 76c-7-5-10-13-8-21M116 76c7-5 10-13 8-21',
    face: (
      <>
        <path d="M50 70c2-4 8-4 10 0M72 70c2-4 8-4 10 0" {...stroke} />
        <path d="M60 77c2 7 10 7 12 0z" fill={INK} />
        <Cheeks y={79} />
      </>
    ),
    extra: (
      <path
        className="blob-sparkle"
        d="M118 18l2 5 5 2-5 2-2 5-2-5-5-2 5-2zM14 22l1.5 3.5 3.5 1.5-3.5 1.5-1.5 3.5-1.5-3.5-3.5-1.5 3.5-1.5z"
        fill="#F2B200"
      />
    ),
  },
  calma: {
    color: '#A8E0D6',
    arms: 'M24 86c10 8 22 9 32 3M108 86c-10 8-22 9-32 3',
    face: (
      <>
        <path d="M50 68c2 3 8 3 10 0M72 68c2 3 8 3 10 0" {...stroke} />
        <path d="M61 77c2 2.5 8 2.5 10 0" {...stroke} />
        <Cheeks y={77} />
      </>
    ),
    extra: <path d="M112 26c-5-3.5-8-6-8-9a3.5 3.5 0 0 1 8-1.5 3.5 3.5 0 0 1 8 1.5c0 3-3 5.5-8 9z" fill="#FF8FB1" />,
  },
  ansiedad: {
    color: '#C9A8EF',
    legs: 'M56 98l-3 7 3 7M78 98l3 7-3 7M50 113h8M76 113h8',
    arms: 'M14 82c-6 2-8 8-5 12M118 82c6 2 8 8 5 12',
    face: (
      <>
        <ellipse cx="55" cy="68" rx="5.5" ry="6.5" fill={INK} />
        <ellipse cx="77" cy="68" rx="5.5" ry="6.5" fill={INK} />
        <circle cx="57" cy="65.5" r="2" fill="#FFFFFF" />
        <circle cx="79" cy="65.5" r="2" fill="#FFFFFF" />
        <path d="M57 82c2-2 4 2 6 0s4 2 6 0 4 2 6 0" {...stroke} strokeWidth="3" />
        <Cheeks />
      </>
    ),
    extra: (
      <>
        <path d="M104 40c3 5 4.5 7.5 2.5 10a3.4 3.4 0 0 1-5.5-3c0-2 1.5-4 3-7z" fill="#8EC5F2" />
        <path d="M56 14c3-6 10-2 7 3s-9 0-4-5 12-2 13 4" stroke="#7A4E88" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      </>
    ),
  },
  tristeza: {
    color: '#9DBDF0',
    arms: 'M14 82c-3 7-3 13 1 17M118 82c3 7 3 13-1 17',
    face: (
      <>
        <path d="M50 67c3-2 7-2 10 1M72 68c3-3 7-3 10-1" {...stroke} />
        <path d="M53 72c2 4 3 6 1 8a2.6 2.6 0 0 1-4.4-2c0-2 1.6-4 3.4-6z" fill="#FFFFFF" />
        <path d="M59 81c3-3 11-3 14 0" {...stroke} />
        <Cheeks opacity={0.6} y={77} />
      </>
    ),
    extra: (
      <path
        className="blob-rain"
        d="M36 6c2.5 4 3.5 6 2 8a2.5 2.5 0 0 1-4-2c0-2 1-4 2-6zM96 4c2.5 4 3.5 6 2 8a2.5 2.5 0 0 1-4-2c0-2 1-4 2-6zM118 22c2.5 4 3.5 6 2 8a2.5 2.5 0 0 1-4-2c0-2 1-4 2-6z"
        fill="#7FA6E8"
      />
    ),
  },
  enojo: {
    color: '#FF9A7A',
    legs: 'M56 98l-3 14M78 98l3 14M46 113h8M78 113h8',
    arms: 'M14 80L4 90l12 6M118 80l10 10-12 6',
    face: (
      <>
        <path d="M47 60l12 5M85 60l-12 5" stroke={INK} strokeWidth="4" strokeLinecap="round" />
        <ellipse cx="55" cy="70" rx="4" ry="4.5" fill={INK} />
        <ellipse cx="77" cy="70" rx="4" ry="4.5" fill={INK} />
        <path d="M58 83c4-4 12-4 16 0" {...stroke} />
        <Cheeks color="#E8573A" opacity={0.45} y={79} />
      </>
    ),
    extra: (
      <path d="M52 16c-4-4 4-6 0-11M66 14c-4-4 4-6 0-11M80 16c-4-4 4-6 0-11" stroke="#FF9A7A" strokeWidth="3.5" fill="none" strokeLinecap="round" />
    ),
  },
  curiosa: {
    color: '#E3CAF3',
    arms: 'M16 84c-6-2-9-8-8-13M116 80c6-8 4-16-1-20',
    face: (
      <>
        <ellipse cx="56" cy="66" rx="4" ry="5" fill={INK} />
        <ellipse cx="78" cy="66" rx="4" ry="5" fill={INK} />
        <circle cx="57.5" cy="64" r="1.5" fill="#FFFFFF" />
        <circle cx="79.5" cy="64" r="1.5" fill="#FFFFFF" />
        <ellipse cx="67" cy="80" rx="3.5" ry="4" fill={INK} />
        <Cheeks />
      </>
    ),
    extra: <path d="M116 26c0-6 8-6 8 0 0 4-4 4-4 8M120 40v.5" stroke="#7A4E88" strokeWidth="3" fill="none" strokeLinecap="round" />,
  },
}

export function emotionLabel(mood) {
  return LABELS[ALIASES[mood] ?? mood] ?? LABELS.calma
}

export default function Blob({ mood = 'calma', size = 120, className = '', title, limbs = true, decor = true }) {
  const key = ALIASES[mood] ?? mood
  const c = CHARACTERS[key] ?? CHARACTERS.calma
  const viewBox = limbs || decor ? '0 0 132 130' : '4 22 124 80'
  const height = limbs || decor ? Math.round((size * 130) / 132) : Math.round((size * 80) / 124)
  return (
    <svg
      className={`blob blob--${key} ${className}`}
      width={size}
      height={height}
      viewBox={viewBox}
      role={title ? 'img' : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
    >
      {limbs && (
        <>
          <ellipse cx="66" cy="122" rx="30" ry="4" fill={INK} opacity="0.1" />
          <path d={c.legs ?? 'M56 98v14M78 98v14M50 113h8M76 113h8'} {...limb} />
          <path className="blob-arms" d={c.arms} {...limb} />
        </>
      )}
      <path className="blob-body" fill={c.color} d={CLOUD} />
      <g className="blob-face">{c.face}</g>
      {decor && c.extra}
    </svg>
  )
}
