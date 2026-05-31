import { apiRequest } from './apiClient.js'

export async function requestPasswordReset(email) {
  return apiRequest('/auth/password-reset/request', {
    method: 'POST',
    body: { email },
  })
}

export async function confirmPasswordReset(token, novaPassword) {
  return apiRequest('/auth/password-reset/confirm', {
    method: 'POST',
    body: { token, nova_password: novaPassword },
  })
}
