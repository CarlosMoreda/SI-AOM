import { apiRequest, apiRequestPaged } from './apiClient.js'

export async function listProjects(token) {
  return apiRequest('/projetos/', { token })
}

/** Lista paginada de projetos: devolve { items, total }. */
export async function listProjectsPaged(token, { q = '', limit = 30, offset = 0 } = {}) {
  return apiRequestPaged('/projetos/', { token, params: { q, limit, offset } })
}

export async function createProject(token, payload) {
  return apiRequest('/projetos/', {
    method: 'POST',
    token,
    body: payload,
  })
}

export async function updateProject(token, id, payload) {
  return apiRequest(`/projetos/${id}`, { method: 'PUT', token, body: payload })
}

export async function deleteProject(token, id) {
  return apiRequest(`/projetos/${id}`, { method: 'DELETE', token })
}

export async function listProjectBudgets(token, projectId) {
  return apiRequest(`/projetos/${projectId}/orcamentos`, { token })
}
