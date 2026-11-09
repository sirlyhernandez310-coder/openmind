// Isotipo de OpenMind: medio cerebro + medio corazón unidos por una línea que fluye
export function Isotipo({ size = 40, ink = '#4A1858', line = '#FFF8EE', dot = '#FFD166', className = '', animated = false }) {
  return (
    <svg className={`isotipo ${animated ? 'isotipo--animated' : ''} ${className}`} width={size} height={size} viewBox="0 0 120 120" aria-hidden="true">
      <path className="iso-brain" fill={ink} d="M58 20C49 12 35 14 31 25C19 25 12 37 16 47C7 54 9 69 19 73C17 85 27 95 39 93C45 103 54 104 58 100Z" />
      <path className="iso-heart" fill={ink} d="M62 32C67 17 86 13 98 24C111 36 107 57 95 71L62 104Z" />
      <path className="iso-line" d="M12 66C25 52 40 54 43 62C46 70 37 74 35 67C33 58 50 50 60 58C71 67 86 52 96 34" fill="none" stroke={line} strokeWidth="5.5" strokeLinecap="round" />
      <circle className="iso-dot" cx="96" cy="34" r="5" fill={dot} />
    </svg>
  )
}

export default function Logo({ size = 'md', light = false }) {
  const iso = { sm: 30, md: 38, lg: 64 }[size] ?? 38
  return (
    <span className={`logo logo--${size} ${light ? 'logo--light' : ''}`}>
      <Isotipo size={iso} ink={light ? '#FFF8EE' : '#4A1858'} line={light ? '#FFD166' : '#C9A8EF'} />
      <span className="logo-word">Open Mind</span>
    </span>
  )
}
