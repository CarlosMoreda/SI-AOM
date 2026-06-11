import { apiRequest, apiRequestPaged } from './apiClient.js'

export async function listMateriais(token) {
  return apiRequest('/materiais/', { token })
}

/** Lista paginada de materiais: devolve { items, total }. */
export async function listMateriaisPaged(token, { q = '', limit = 30, offset = 0 } = {}) {
  return apiRequestPaged('/materiais/', { token, params: { q, limit, offset } })
}

export async function createMaterial(token, payload) {
  return apiRequest('/materiais/', { method: 'POST', token, body: payload })
}

export async function updateMaterial(token, id, payload) {
  return apiRequest(`/materiais/${id}`, { method: 'PUT', token, body: payload })
}

export async function deleteMaterial(token, id) {
  return apiRequest(`/materiais/${id}`, { method: 'DELETE', token })
}
