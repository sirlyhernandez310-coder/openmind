// Fondo de líneas con bucles (va detrás del contenido de los paneles lila)
const PATHS = {
  tall: 'M-60 140C40 60 150 170 100 240c-40 56-120 10-90-40 30-50 130-20 160 60 40 110 170 60 240 120 70 60-20 150 60 210 80 60 200-40 240 40M140-40c40 90 160 60 190 140 30 80-60 130-10 170 50 40 120-40 90-80-30-40-120 10-110 90M-40 600c80-70 160 30 120 110-30 60-110 20-80-30 40-60 160-10 200 60 40 70 160 40 220-20 50-50 150-30 200 60M520-30c-40 80 30 150 120 120',
  wide: 'M-40 260C40 160 140 280 100 330M60-30c40 80 150 60 170 130 20 70-70 100-40 140 30 40 100-20 80-60-20-40-110-10-120 70M380 360c30-90 140-120 200-60 50 50-10 110-50 80-40-30 20-110 100-110 90 0 120 90 200 70s90-140 180-170 120 60 200 30M700-40c-20 70 60 110 120 80 50-26 20-90-20-70-36 18-10 90 70 100 70 10 120-60 180-30',
  small: 'M300-30c-20 70 60 100 100 60 30-30-10-70-40-50-34 22 0 90 80 90 70 0 90-60 110-90M260 260c40-70 130-60 150-10 16 40-40 60-56 30-18-34 40-70 90-50s60 70 100 50M-30 60c50-60 120 10 90 60-24 40-80 10-60-30',
}
const BOXES = { tall: '0 0 600 820', wide: '0 0 1100 320', small: '0 0 520 220' }

export default function LoopPattern({ variant = 'wide', color = 'var(--lines)', width = 32, animated = false }) {
  return (
    <svg className={`loops ${animated ? 'loops--animated' : ''}`} viewBox={BOXES[variant]} preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <path d={PATHS[variant]} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
