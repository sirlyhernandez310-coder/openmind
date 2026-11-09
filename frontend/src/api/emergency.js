import { apiFetch } from './client'

export const emergencyApi = {
  info: () => apiFetch('/emergency/info/', { auth: false }),
  chats: (status) => apiFetch(`/emergency/chats/${status ? `?status=${status}` : ''}`),
  chat: (id) => apiFetch(`/emergency/chats/${id}/`),
  open: () => apiFetch('/emergency/chats/', { method: 'POST' }),
  take: (id) => apiFetch(`/emergency/chats/${id}/take/`, { method: 'POST' }),
  close: (id) => apiFetch(`/emergency/chats/${id}/close/`, { method: 'POST' }),
  messages: (id, after) => apiFetch(`/emergency/chats/${id}/messages/${after ? `?after=${after}` : ''}`),
  send: (id, text) => apiFetch(`/emergency/chats/${id}/messages/`, { method: 'POST', body: { text } }),
}
