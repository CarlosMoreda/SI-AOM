import { apiRequest } from './apiClient.js'

// ── Material ─────────────────────────────────────────────────────────────────

export async function listRealizadoMaterial(token, idLinhaMaterial) {
  return apiRequest(`/realizado/material/linha/${idLinhaMaterial}`, { token })
}

export async function createRealizadoMaterial(token, payload) {
  return apiRequest('/realizado/material', { method: 'POST', token, body: payload })
}

export async function updateRealizadoMaterial(token, id, payload) {
  return apiRequest(`/realizado/material/${id}`, { method: 'PUT', token, body: payload })
}

export async function deleteRealizadoMaterial(token, id) {
  return apiRequest(`/realizado/material/${id}`, { method: 'DELETE', token })
}

// ── Operacao ─────────────────────────────────────────────────────────────────

export async function listRealizadoOperacao(token, idLinhaOperacao) {
  return apiRequest(`/realizado/operacao/linha/${idLinhaOperacao}`, { token })
}

export async function createRealizadoOperacao(token, payload) {
  return apiRequest('/realizado/operacao', { method: 'POST', token, body: payload })
}

export async function updateRealizadoOperacao(token, id, payload) {
  return apiRequest(`/realizado/operacao/${id}`, { method: 'PUT', token, body: payload })
}

export async function deleteRealizadoOperacao(token, id) {
  return apiRequest(`/realizado/operacao/${id}`, { method: 'DELETE', token })
}

// ── Servico ──────────────────────────────────────────────────────────────────

export async function listRealizadoServico(token, idLinhaServico) {
  return apiRequest(`/realizado/servico/linha/${idLinhaServico}`, { token })
}

export async function createRealizadoServico(token, payload) {
  return apiRequest('/realizado/servico', { method: 'POST', token, body: payload })
}

export async function updateRealizadoServico(token, id, payload) {
  return apiRequest(`/realizado/servico/${id}`, { method: 'PUT', token, body: payload })
}

export async function deleteRealizadoServico(token, id) {
  return apiRequest(`/realizado/servico/${id}`, { method: 'DELETE', token })
}

// ── Resumo por orcamento ─────────────────────────────────────────────────────

export async function getRealizadoResumo(token, idOrcamento) {
  return apiRequest(`/realizado/orcamento/${idOrcamento}/resumo`, { token })
}

export async function getRealizadoResumoBatch(token, idsOrcamento) {
  return apiRequest('/realizado/orcamentos/resumo', {
    method: 'POST',
    token,
    body: { ids_orcamento: idsOrcamento },
  })
}
