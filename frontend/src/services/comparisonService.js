import { apiRequest } from './apiClient.js'

export async function getBudgetComparison(token, budgetId) {
  return apiRequest(`/comparacao/orcamento/${budgetId}`, { token })
}
