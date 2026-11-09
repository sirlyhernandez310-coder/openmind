export const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

export const REQUIRED = 'Este campo es obligatorio.'
export const INVALID_EMAIL = 'Ingresa un correo electrónico válido (ej: nombre@correo.com).'

export function validateEmail(value) {
  if (!value.trim()) return REQUIRED
  if (!EMAIL_REGEX.test(value.trim())) return INVALID_EMAIL
  return null
}

// quita las claves sin error
export function compact(errors) {
  return Object.fromEntries(Object.entries(errors).filter(([, v]) => v))
}
