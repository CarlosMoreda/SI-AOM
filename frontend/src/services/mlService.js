import { apiRequest } from './apiClient.js'

export async function predictCusto(token, payload) {
  return apiRequest('/ml/orcamento/prever', {
    method: 'POST',
    token,
    body: payload,
  })
}

export async function getCustoOptions(token) {
  return apiRequest('/ml/orcamento/opcoes', {
    method: 'GET',
    token,
  })
}

export async function trainCustoModels(token, payload = {}) {
  return apiRequest('/ml/orcamento/treinar', {
    method: 'POST',
    token,
    body: payload,
  })
}
