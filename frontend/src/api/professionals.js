import { apiFetch } from './client'

export const professionalsApi = {
  specialties: () => apiFetch('/professionals/specialties/', { auth: false }),
  register: (data) => apiFetch('/professionals/register/', { method: 'POST', body: data, auth: false }),
  // OM3-14: listado con búsqueda opcional por nombre o especialidad
  directory: (q = '') => apiFetch(`/professionals/directory/${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  // OM3-15: perfil de un psicólogo
  directoryDetail: (id) => apiFetch(`/professionals/directory/${id}/`),
  myProfile: () => apiFetch('/professionals/me/'),
  updateMyProfile: (data) => apiFetch('/professionals/me/', { method: 'PATCH', body: data }),
  list: (verified) => apiFetch(`/professionals/${verified === undefined ? '' : `?verified=${verified}`}`),
  verify: (id, isVerified) =>
    apiFetch(`/professionals/${id}/verify/`, { method: 'POST', body: { is_verified: isVerified } }),
}
