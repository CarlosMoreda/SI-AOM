import { apiRequest } from './apiClient.js'

export async function login(email, password) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: { email, password },
  })
}

export async function getCurrentUser(token) {
  return apiRequest('/auth/me', { token })
}
