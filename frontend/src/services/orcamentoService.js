import { apiRequest } from './apiClient.js'

export async function listOrcamentos(token) {
  return apiRequest('/orcamentos/', { token })
}

export async function createOrcamento(token, payload) {
  return apiRequest('/orcamentos/', { method: 'POST', token, body: payload })
}

export async function updateOrcamento(token, id, payload) {
  return apiRequest(`/orcamentos/${id}`, { method: 'PUT', token, body: payload })
}

export async function deleteOrcamento(token, id) {
  return apiRequest(`/orcamentos/${id}`, { method: 'DELETE', token })
}

export async function listOrcamentoMateriais(token, idOrcamento) {
  return apiRequest(`/orcamentos/${idOrcamento}/materiais`, { token })
}

export async function addOrcamentoMaterial(token, idOrcamento, payload) {
  return apiRequest(`/orcamentos/${idOrcamento}/materiais`, { method: 'POST', token, body: payload })
}

export async function updateOrcamentoMaterial(token, idLinha, payload) {
  return apiRequest(`/orcamentos/materiais/${idLinha}`, { method: 'PUT', token, body: payload })
}

export async function deleteOrcamentoMaterial(token, idLinha) {
  return apiRequest(`/orcamentos/materiais/${idLinha}`, { method: 'DELETE', token })
}

export async function listOrcamentoOperacoes(token, idOrcamento) {
  return apiRequest(`/orcamentos/${idOrcamento}/operacoes`, { token })
}

export async function addOrcamentoOperacao(token, idOrcamento, payload) {
  return apiRequest(`/orcamentos/${idOrcamento}/operacoes`, { method: 'POST', token, body: payload })
}

export async function updateOrcamentoOperacao(token, idLinha, payload) {
  return apiRequest(`/orcamentos/operacoes/${idLinha}`, { method: 'PUT', token, body: payload })
}

export async function deleteOrcamentoOperacao(token, idLinha) {
  return apiRequest(`/orcamentos/operacoes/${idLinha}`, { method: 'DELETE', token })
}

export async function listOrcamentoServicos(token, idOrcamento) {
  return apiRequest(`/orcamentos/${idOrcamento}/servicos`, { token })
}

export async function addOrcamentoServico(token, idOrcamento, payload) {
  return apiRequest(`/orcamentos/${idOrcamento}/servicos`, { method: 'POST', token, body: payload })
}

export async function updateOrcamentoServico(token, idLinha, payload) {
  return apiRequest(`/orcamentos/servicos/${idLinha}`, { method: 'PUT', token, body: payload })
}

export async function deleteOrcamentoServico(token, idLinha) {
  return apiRequest(`/orcamentos/servicos/${idLinha}`, { method: 'DELETE', token })
}
