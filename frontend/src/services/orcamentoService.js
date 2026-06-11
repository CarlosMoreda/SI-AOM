import { apiRequest, apiRequestPaged, API_BASE_URL, ApiError } from './apiClient.js'
import { formatVersionLabel } from '../utils/formatters.js'

export async function listOrcamentos(token) {
  return apiRequest('/orcamentos/', { token })
}

/** Lista paginada de orçamentos (filtro opcional por projeto): { items, total }. */
export async function listOrcamentosPaged(token, { idProjeto = '', limit = 30, offset = 0 } = {}) {
  return apiRequestPaged('/orcamentos/', {
    token,
    params: { id_projeto: idProjeto, limit, offset },
  })
}

/**
 * Faz download do PDF do orçamento. Como o endpoint devolve binário,
 * não podemos usar o apiRequest (que assume JSON). Em vez disso fazemos
 * fetch direto e tratamos a resposta como Blob.
 */
export async function downloadOrcamentoPdf(token, idOrcamento, versao) {
  const url = `${API_BASE_URL}/orcamentos/${idOrcamento}/pdf`
  let response
  try {
    response = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new ApiError(
      'Não foi possível contactar o servidor para gerar o PDF.',
      { status: 0, code: 'network' },
    )
  }
  if (!response.ok) {
    let detail = `Erro HTTP ${response.status}`
    try {
      const body = await response.json()
      if (body?.detail) detail = body.detail
    } catch { /* corpo não é JSON, ignora */ }
    throw new ApiError(detail, { status: response.status, code: 'http' })
  }
  const blob = await response.blob()
  const objectUrl = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objectUrl
  a.download = `orcamento_${idOrcamento}_${formatVersionLabel(versao || '1')}.pdf`
  document.body.appendChild(a)
  a.click()
  a.remove()
  // libertar memória do blob após o browser iniciar o download
  setTimeout(() => window.URL.revokeObjectURL(objectUrl), 1000)
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
