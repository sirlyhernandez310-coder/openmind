export const ROLES = {
  PACIENTE: 'PACIENTE',
  PSICOLOGO: 'PSICOLOGO',
  ADMINISTRADOR: 'ADMINISTRADOR',
}

export const ROLE_LABELS = {
  PACIENTE: 'Paciente',
  PSICOLOGO: 'Psicólogo',
  ADMINISTRADOR: 'Administrador',
}

// cada rol tiene su propia interfaz
const HOME_BY_ROLE = {
  [ROLES.PACIENTE]: '/paciente',
  [ROLES.PSICOLOGO]: '/psicologo',
  [ROLES.ADMINISTRADOR]: '/admin',
}

export function homeForRole(role) {
  return HOME_BY_ROLE[role] ?? '/login'
}
