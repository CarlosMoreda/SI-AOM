import { apiRequest } from './apiClient.js'

export async function listClientes(token) {
  return apiRequest('/clientes/', { token })
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
