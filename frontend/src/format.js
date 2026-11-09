const dateFmt = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'long', year: 'numeric' })
const shortFmt = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short' })
const timeFmt = new Intl.DateTimeFormat('es-CO', { hour: 'numeric', minute: '2-digit' })

export const formatDate = (value) => dateFmt.format(new Date(value))
export const formatShortDate = (value) => shortFmt.format(new Date(value))
export const formatTime = (value) => timeFmt.format(new Date(value))
export const formatDateTime = (value) => `${formatDate(value)}, ${formatTime(value)}`

// Color, nube y texto de cada nivel de la evaluación
export const LEVELS = {
  ESTABLE: { label: 'Bienestar estable', tone: 'sun', mood: 'alegria' },
  LEVE: { label: 'Malestar leve', tone: 'mint', mood: 'calma' },
  MODERADO: { label: 'Malestar moderado', tone: 'lilac', mood: 'ansiedad' },
  ALTO: { label: 'Malestar alto', tone: 'blue', mood: 'tristeza' },
}

// En malestar moderado, si lo que más pesa es el estrés, la nube que aparece es Enojo
export function moodFor(level, focusDimension) {
  if (level === 'MODERADO' && focusDimension === 'Estrés') return 'enojo'
  return LEVELS[level]?.mood ?? 'calma'
}

// Fechas de citas (Sprint 3)
const weekdayFmt = new Intl.DateTimeFormat('es-CO', { weekday: 'long' })
const weekdayShortFmt = new Intl.DateTimeFormat('es-CO', { weekday: 'short' })
const longDayFmt = new Intl.DateTimeFormat('es-CO', { weekday: 'long', day: 'numeric', month: 'long' })
const capitalize = (text) => text.charAt(0).toUpperCase() + text.slice(1)

// "2026-11-03" se interpreta como fecha local (no UTC) para no correrse un día
const asLocalDate = (value) => (/^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T12:00:00`) : new Date(value))

export const formatWeekday = (value) => capitalize(weekdayFmt.format(asLocalDate(value)))
export const formatWeekdayShort = (value) => capitalize(weekdayShortFmt.format(asLocalDate(value)).replace('.', ''))
export const formatLongDay = (value) => capitalize(longDayFmt.format(asLocalDate(value)))
export const dayNumber = (value) => asLocalDate(value).getDate()
export const formatTimeRange = (start, end) => `${formatTime(start)} – ${formatTime(end)}`

// "Hoy", "Mañana" o "Martes 4 de noviembre"
export function friendlyDay(value) {
  const date = asLocalDate(value)
  const today = new Date()
  const tomorrow = new Date()
  tomorrow.setDate(today.getDate() + 1)
  if (date.toDateString() === today.toDateString()) return 'Hoy'
  if (date.toDateString() === tomorrow.toDateString()) return 'Mañana'
  return formatLongDay(value)
}
const monthShortFmt = new Intl.DateTimeFormat('es-CO', { month: 'short' })
export const formatMonthShort = (value) => monthShortFmt.format(asLocalDate(value)).replace('.', '')
