import { apiRequest } from './apiClient.js'

export async function listOperacoes(token) {
  return apiRequest('/operacoes/', { token })
}

export async function createOperacao(token, payload) {
  return apiRequest('/operacoes/', { method: 'POST', token, body: payload })
}

export async function updateOperacao(token, id, payload) {
  return apiRequest(`/operacoes/${id}`, { method: 'PUT', token, body: payload })
}

export async function deleteOperacao(token, id) {
  return apiRequest(`/operacoes/${id}`, { method: 'DELETE', token })
}
