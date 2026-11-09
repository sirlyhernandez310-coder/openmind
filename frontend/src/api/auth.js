import { apiFetch } from './client'

export const authApi = {
  register: (data) => apiFetch('/auth/register/', { method: 'POST', body: data, auth: false }),
  login: (email, password) => apiFetch('/auth/login/', { method: 'POST', body: { email, password }, auth: false }),
  logout: (refresh) => apiFetch('/auth/logout/', { method: 'POST', body: { refresh } }),
  me: () => apiFetch('/auth/me/'),
  uploadAvatar: (file) => {
    const form = new FormData()
    form.append('avatar', file)
    return apiFetch('/auth/me/avatar/', { method: 'PUT', body: form })
  },
  removeAvatar: () => apiFetch('/auth/me/avatar/', { method: 'DELETE' }),
  verifyEmail: (token) => apiFetch('/auth/verify-email/', { method: 'POST', body: { token }, auth: false }),
  resendVerification: (email) =>
    apiFetch('/auth/verify-email/resend/', { method: 'POST', body: { email }, auth: false }),
  users: (role) => apiFetch(`/auth/users/${role ? `?role=${role}` : ''}`),
  requestPasswordReset: (email) =>
    apiFetch('/auth/password-reset/', { method: 'POST', body: { email }, auth: false }),
  validateResetLink: (uid, token) =>
    apiFetch('/auth/password-reset/validate/', { method: 'POST', body: { uid, token }, auth: false }),
  confirmPasswordReset: (data) =>
    apiFetch('/auth/password-reset/confirm/', { method: 'POST', body: data, auth: false }),
}
