import { apiRequest } from './apiClient.js'

export async function listServicos(token) {
  return apiRequest('/servicos/', { token })
}

export async function createServico(token, payload) {
  return apiRequest('/servicos/', { method: 'POST', token, body: payload })
}

export async function updateServico(token, id, payload) {
  return apiRequest(`/servicos/${id}`, { method: 'PUT', token, body: payload })
}

export async function deleteServico(token, id) {
  return apiRequest(`/servicos/${id}`, { method: 'DELETE', token })
}
