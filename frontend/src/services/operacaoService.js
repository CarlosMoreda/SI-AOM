import { apiRequest, apiRequestPaged } from './apiClient.js'

export async function listOperacoes(token) {
  return apiRequest('/operacoes/', { token })
}

/** Lista paginada de operações: devolve { items, total }. */
export async function listOperacoesPaged(token, { q = '', limit = 30, offset = 0 } = {}) {
  return apiRequestPaged('/operacoes/', { token, params: { q, limit, offset } })
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
