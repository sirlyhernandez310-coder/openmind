import { formatShortDate } from '../format'

// Evolución del índice de malestar (0-100) en el tiempo. Más bajo = mejor.
export default function TrendChart({ items }) {
  const points = [...items].reverse() // de la más antigua a la más reciente
  const W = 640
  const H = 220
  const pad = { top: 16, right: 40, bottom: 32, left: 40 }
  const innerW = W - pad.left - pad.right
  const innerH = H - pad.top - pad.bottom
  const x = (i) => pad.left + (points.length === 1 ? innerW / 2 : (i * innerW) / (points.length - 1))
  const y = (v) => pad.top + innerH * (1 - v / 100)
  const path = points.map((p, i) => `${i ? 'L' : 'M'}${x(i)},${y(p.percentage)}`).join(' ')
  const bands = [
    { from: 0, to: 25, cls: 'band--mint' },
    { from: 25, to: 50, cls: 'band--sky' },
    { from: 50, to: 75, cls: 'band--lilac' },
    { from: 75, to: 100, cls: 'band--peach' },
  ]
  const labelEvery = Math.ceil(points.length / 6)

  return (
    <svg className="trend" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Evolución de tu índice de malestar">
      {bands.map((b) => (
        <rect key={b.from} className={`band ${b.cls}`} x={pad.left} width={innerW} y={y(b.to)} height={y(b.from) - y(b.to)} />
      ))}
      {[0, 25, 50, 75, 100].map((v) => (
        <text key={v} x={pad.left - 8} y={y(v)} className="trend-axis" textAnchor="end" dominantBaseline="central">{v}</text>
      ))}
      <path d={path} className="trend-line" />
      {points.map((p, i) => (
        <g key={p.id}>
          <circle cx={x(i)} cy={y(p.percentage)} r="5" className="trend-dot">
            <title>{`${formatShortDate(p.created_at)}: ${p.percentage}% · ${p.level_display}`}</title>
          </circle>
          {(i % labelEvery === 0 || i === points.length - 1) && (
            <text x={x(i)} y={H - 8} className="trend-axis" textAnchor="middle">{formatShortDate(p.created_at)}</text>
          )}
        </g>
      ))}
    </svg>
  )
}
