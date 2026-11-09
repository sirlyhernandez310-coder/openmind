import { apiFetch } from './client'

export const evaluationsApi = {
  questionnaire: () => apiFetch('/evaluations/questions/'),
  submit: (answers) => apiFetch('/evaluations/', { method: 'POST', body: { answers } }),
  history: () => apiFetch('/evaluations/'),
  detail: (id) => apiFetch(`/evaluations/${id}/`),
}
