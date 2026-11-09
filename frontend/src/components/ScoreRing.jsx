export default function ScoreRing({ value, tone = 'lilac', size = 150 }) {
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - value / 100)
  return (
    <svg className={`ring ring--${tone}`} width={size} height={size} viewBox="0 0 140 140" role="img"
      aria-label={`Índice de malestar: ${value} %`}>
      <circle cx="70" cy="70" r={radius} className="ring-track" />
      <circle
        cx="70" cy="70" r={radius} className="ring-value"
        strokeDasharray={circumference} strokeDashoffset={offset}
        transform="rotate(-90 70 70)"
      />
      <text x="70" y="70" textAnchor="middle" dominantBaseline="central" className="ring-text">{value}%</text>
    </svg>
  )
}
