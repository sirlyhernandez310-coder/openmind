import { apiFetch } from './client'

// Sprint 3: horarios disponibles, reservas y mis sesiones
export const appointmentsApi = {
  // OM3-16: horarios libres de un psicólogo agrupados por día
  slots: (psychologistId) => apiFetch(`/appointments/psychologists/${psychologistId}/slots/`),
  // OM3-17: reservar una cita
  book: (data) => apiFetch('/appointments/', { method: 'POST', body: data }),
  // OM3-18: mis sesiones (scope: upcoming | past | all)
  list: (scope = 'upcoming') => apiFetch(`/appointments/?scope=${scope}`),
  // OM3-20 Videollamada: estado de la sala y señalización (join | offer | answer | leave)
  call: (id) => apiFetch(`/appointments/${id}/call/`),
  callSignal: (id, action, sdp = '') => apiFetch(`/appointments/${id}/call/`, { method: 'POST', body: { action, sdp } }),
  // Psicólogo: su horario semanal de atención
  myAvailability: () => apiFetch('/appointments/availability/'),
  saveAvailability: (items) => apiFetch('/appointments/availability/', { method: 'PUT', body: { items } }),
}
