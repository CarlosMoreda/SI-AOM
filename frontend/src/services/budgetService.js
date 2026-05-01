import { apiRequest } from './apiClient.js'

export async function listBudgets(token) {
  return apiRequest('/orcamentos/', { token })
}
