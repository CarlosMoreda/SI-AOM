import { apiRequest } from './apiClient.js'

export async function listUtilizadores(token) {
  return apiRequest('/utilizadores/', { token })
}

export async function createUtilizador(token, payload) {
  return apiRequest('/utilizadores/', { method: 'POST', token, body: payload })
}

export async function updateUtilizador(token, id, payload) {
  return apiRequest(`/utilizadores/${id}`, { method: 'PUT', token, body: payload })
}

export async function deleteUtilizador(token, id) {
  return apiRequest(`/utilizadores/${id}`, { method: 'DELETE', token })
}
