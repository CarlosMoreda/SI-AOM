import { apiRequest, apiRequestPaged } from './apiClient.js'

export async function listClientes(token) {
  return apiRequest('/clientes/', { token })
}

/** Lista paginada de clientes: devolve { items, total }. */
export async function listClientesPaged(token, { q = '', limit = 30, offset = 0 } = {}) {
  return apiRequestPaged('/clientes/', { token, params: { q, limit, offset } })
}

export async function createCliente(token, payload) {
  return apiRequest('/clientes/', { method: 'POST', token, body: payload })
}

export async function updateCliente(token, id, payload) {
  return apiRequest(`/clientes/${id}`, { method: 'PUT', token, body: payload })
}

export async function deleteCliente(token, id) {
  return apiRequest(`/clientes/${id}`, { method: 'DELETE', token })
}
