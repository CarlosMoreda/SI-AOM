import { apiRequest } from './apiClient.js'

const RESUMO_BATCH_SIZE = 500

export function normalizeOrcamentoIds(idsOrcamento) {
  return [...new Set((idsOrcamento || [])
    .map((id) => Number(id))
    .filter((id) => Number.isInteger(id) && id > 0))]
}

function chunkIds(ids, size) {
  const chunks = []
  for (let index = 0; index < ids.length; index += size) {
    chunks.push(ids.slice(index, index + size))
  }
  return chunks
}

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

export async function getRealizadoResumo(token, idOrcamento) {
  return apiRequest(`/realizado/orcamento/${idOrcamento}/resumo`, { token })
}

export async function getRealizadoResumoBatch(token, idsOrcamento) {
  const ids = normalizeOrcamentoIds(idsOrcamento)
  if (ids.length === 0) return []

  const responses = await Promise.all(
    chunkIds(ids, RESUMO_BATCH_SIZE).map((chunk) => (
      apiRequest('/realizado/orcamentos/resumo', {
        method: 'POST',
        token,
        body: { ids_orcamento: chunk },
      })
    )),
  )

  return responses.flat()
}
