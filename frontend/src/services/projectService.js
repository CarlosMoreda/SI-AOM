import { apiRequest } from './apiClient.js'

export async function listProjects(token) {
  return apiRequest('/projetos/', { token })
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
