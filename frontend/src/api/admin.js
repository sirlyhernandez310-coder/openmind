import { apiFetch } from './client'

const query = (params) => {
  const search = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null))
  return search.toString() ? `?${search}` : ''
}

// Sprint 4: gestión de usuarios (OM3-24) y estadísticas (OM3-25), solo administrador
export const adminApi = {
  users: (params = {}) => apiFetch(`/admin/users/${query(params)}`),
  user: (id) => apiFetch(`/admin/users/${id}/`),
  setStatus: (id, isActive, reason = '') =>
    apiFetch(`/admin/users/${id}/status/`, { method: 'POST', body: { is_active: isActive, reason } }),
  logs: (userId) => apiFetch(`/admin/logs/${query({ user: userId })}`),
  stats: () => apiFetch('/admin/stats/'),
}
