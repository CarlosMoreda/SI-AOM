import assert from 'node:assert/strict'
import test from 'node:test'

import { apiRequest } from '../src/services/apiClient.js'
import { createCliente, deleteCliente, updateCliente } from '../src/services/clienteService.js'
import { getBudgetComparison } from '../src/services/comparisonService.js'
import { getDashboardKpis, getRecentBudgets } from '../src/services/dashboardService.js'
import { createMaterial, deleteMaterial, updateMaterial } from '../src/services/materialService.js'
import { getCustoOptions, trainCustoModels } from '../src/services/mlService.js'
import {
  addOrcamentoMaterial,
  addOrcamentoOperacao,
  addOrcamentoServico,
  deleteOrcamentoMaterial,
  deleteOrcamentoOperacao,
  deleteOrcamentoServico,
  listOrcamentoMateriais,
  listOrcamentoOperacoes,
  listOrcamentoServicos,
  updateOrcamentoMaterial,
  updateOrcamentoOperacao,
  updateOrcamentoServico,
} from '../src/services/orcamentoService.js'
import { createOperacao, deleteOperacao, updateOperacao } from '../src/services/operacaoService.js'
import {
  createRealizadoMaterial,
  createRealizadoOperacao,
  createRealizadoServico,
  deleteRealizadoMaterial,
  deleteRealizadoOperacao,
  deleteRealizadoServico,
  getRealizadoResumo,
  listRealizadoMaterial,
  listRealizadoOperacao,
  listRealizadoServico,
  updateRealizadoMaterial,
  updateRealizadoOperacao,
  updateRealizadoServico,
} from '../src/services/realizadoService.js'
import { createServico, deleteServico, updateServico } from '../src/services/servicoService.js'
import { clearToken, readToken, writeToken } from '../src/services/tokenStorage.js'

function mockFetch(payload = {}, status = 200, headers = { 'Content-Type': 'application/json' }) {
  const calls = []

  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return new Response(
      payload === null ? null : JSON.stringify(payload),
      { status, headers },
    )
  }

  return calls
}

function lastCall(calls) {
  return calls.at(-1)
}

function pathAndSearch(call) {
  const url = new URL(call.url)
  return `${url.pathname}${url.search}`
}

function bodyOf(call) {
  return call.options.body ? JSON.parse(call.options.body) : undefined
}

test('orcamento services cobrem linhas de materiais operacoes e servicos', async () => {
  const calls = mockFetch({ ok: true })
  const token = 'token-abc'

  await listOrcamentoMateriais(token, 10)
  assert.equal(pathAndSearch(lastCall(calls)), '/orcamentos/10/materiais')
  assert.equal(lastCall(calls).options.method, 'GET')

  await addOrcamentoMaterial(token, 10, { id_material: 2, quantidade: 3 })
  assert.equal(pathAndSearch(lastCall(calls)), '/orcamentos/10/materiais')
  assert.equal(lastCall(calls).options.method, 'POST')
  assert.deepEqual(bodyOf(lastCall(calls)), { id_material: 2, quantidade: 3 })

  await updateOrcamentoMaterial(token, 7, { quantidade: 4 })
  assert.equal(pathAndSearch(lastCall(calls)), '/orcamentos/materiais/7')
  assert.equal(lastCall(calls).options.method, 'PUT')

  await deleteOrcamentoMaterial(token, 7)
  assert.equal(pathAndSearch(lastCall(calls)), '/orcamentos/materiais/7')
  assert.equal(lastCall(calls).options.method, 'DELETE')

  await listOrcamentoOperacoes(token, 10)
  await addOrcamentoOperacao(token, 10, { id_operacao: 3, horas: 2 })
  await updateOrcamentoOperacao(token, 8, { horas: 5 })
  await deleteOrcamentoOperacao(token, 8)
  assert.equal(pathAndSearch(calls.at(-4)), '/orcamentos/10/operacoes')
  assert.equal(pathAndSearch(calls.at(-3)), '/orcamentos/10/operacoes')
  assert.equal(pathAndSearch(calls.at(-2)), '/orcamentos/operacoes/8')
  assert.equal(pathAndSearch(calls.at(-1)), '/orcamentos/operacoes/8')

  await listOrcamentoServicos(token, 10)
  await addOrcamentoServico(token, 10, { id_servico: 4, quantidade: 1 })
  await updateOrcamentoServico(token, 9, { quantidade: 2 })
  await deleteOrcamentoServico(token, 9)
  assert.equal(pathAndSearch(calls.at(-4)), '/orcamentos/10/servicos')
  assert.equal(pathAndSearch(calls.at(-3)), '/orcamentos/10/servicos')
  assert.equal(pathAndSearch(calls.at(-2)), '/orcamentos/servicos/9')
  assert.equal(pathAndSearch(calls.at(-1)), '/orcamentos/servicos/9')
})

test('realizado services cobrem registo consulta resumo atualizacao e eliminacao', async () => {
  const calls = mockFetch({ ok: true })
  const token = 'token-abc'

  await listRealizadoMaterial(token, 1)
  await createRealizadoMaterial(token, { id_linha_material: 1, quantidade: 2 })
  await updateRealizadoMaterial(token, 5, { quantidade: 3 })
  await deleteRealizadoMaterial(token, 5)
  await listRealizadoOperacao(token, 2)
  await createRealizadoOperacao(token, { id_linha_operacao: 2, horas: 4 })
  await updateRealizadoOperacao(token, 6, { horas: 5 })
  await deleteRealizadoOperacao(token, 6)
  await listRealizadoServico(token, 3)
  await createRealizadoServico(token, { id_linha_servico: 3, quantidade: 1 })
  await updateRealizadoServico(token, 7, { quantidade: 2 })
  await deleteRealizadoServico(token, 7)
  await getRealizadoResumo(token, 99)

  assert.equal(pathAndSearch(calls[0]), '/realizado/material/linha/1')
  assert.equal(pathAndSearch(calls[1]), '/realizado/material')
  assert.equal(calls[1].options.method, 'POST')
  assert.equal(pathAndSearch(calls[4]), '/realizado/operacao/linha/2')
  assert.equal(pathAndSearch(calls[8]), '/realizado/servico/linha/3')
  assert.equal(pathAndSearch(lastCall(calls)), '/realizado/orcamento/99/resumo')
})

test('catalogos dashboard comparacao e ML usam os endpoints protegidos esperados', async () => {
  const calls = mockFetch({ ok: true })
  const token = 'token-abc'

  await createCliente(token, { nome: 'Cliente' })
  await updateCliente(token, 1, { nome: 'Cliente 2' })
  await deleteCliente(token, 1)
  await createMaterial(token, { codigo: 'M1' })
  await updateMaterial(token, 2, { codigo: 'M2' })
  await deleteMaterial(token, 2)
  await createOperacao(token, { codigo: 'O1' })
  await updateOperacao(token, 3, { codigo: 'O2' })
  await deleteOperacao(token, 3)
  await createServico(token, { codigo: 'S1' })
  await updateServico(token, 4, { codigo: 'S2' })
  await deleteServico(token, 4)
  await getDashboardKpis(token)
  await getRecentBudgets(token, 7)
  await getBudgetComparison(token, 12)
  await getCustoOptions(token)
  await trainCustoModels(token, { refresh_dataset: false })

  assert.equal(pathAndSearch(calls[0]), '/clientes/')
  assert.equal(calls[0].options.method, 'POST')
  assert.equal(pathAndSearch(calls[3]), '/materiais/')
  assert.equal(pathAndSearch(calls[6]), '/operacoes/')
  assert.equal(pathAndSearch(calls[9]), '/servicos/')
  assert.equal(pathAndSearch(calls[12]), '/dashboard/kpis')
  assert.equal(pathAndSearch(calls[13]), '/dashboard/orcamentos_recentes?limit=7')
  assert.equal(pathAndSearch(calls[14]), '/comparacao/orcamento/12')
  assert.equal(pathAndSearch(calls[15]), '/ml/orcamento/opcoes')
  assert.equal(pathAndSearch(calls[16]), '/ml/orcamento/treinar')
  assert.deepEqual(bodyOf(calls[16]), { refresh_dataset: false })
})

test('apiRequest suporta respostas 204 sem corpo e erros sem JSON', async () => {
  mockFetch(null, 204, {})
  assert.equal(await apiRequest('/delete-ok', { method: 'DELETE' }), null)

  mockFetch('erro interno', 500, { 'Content-Type': 'text/plain' })
  await assert.rejects(
    () => apiRequest('/falha'),
    /Erro no servidor/,
  )
})

test('tokenStorage persiste le e limpa o token da sessao local', () => {
  const store = new Map()
  globalThis.localStorage = {
    getItem: (key) => store.get(key) || null,
    setItem: (key, value) => store.set(key, String(value)),
    removeItem: (key) => store.delete(key),
  }

  assert.equal(readToken(), '')
  writeToken('token-xyz')
  assert.equal(readToken(), 'token-xyz')
  clearToken()
  assert.equal(readToken(), '')
})
