import { apiRequest } from './apiClient.js'

export async function getDashboardKpis(token) {
  return apiRequest('/dashboard/kpis', { token })
}

export async function getRecentBudgets(token, limit = 5) {
  return apiRequest(`/dashboard/orcamentos_recentes?limit=${limit}`, { token })
}
