import assert from 'node:assert/strict'
import test from 'node:test'

import { login } from '../src/services/authService.js'
import { apiRequest } from '../src/services/apiClient.js'
import { listClientes } from '../src/services/clienteService.js'
import { createOrcamento } from '../src/services/orcamentoService.js'
import { createProject } from '../src/services/projectService.js'
import { predictCusto } from '../src/services/mlService.js'
import { getRealizadoResumoBatch, normalizeOrcamentoIds } from '../src/services/realizadoService.js'
import { createUtilizador } from '../src/services/utilizadorService.js'

function mockFetch(payload = {}, status = 200) {
  const calls = []

  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return new Response(JSON.stringify(payload), {
      status,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  return calls
}

function lastCall(calls) {
  return calls.at(-1)
}

function pathOf(call) {
  return new URL(call.url).pathname
}

test('login envia credenciais para /auth/login', async () => {
  const calls = mockFetch({ access_token: 'token' })

  await login('admin@aom.pt', 'secret')

  const call = lastCall(calls)
  assert.equal(pathOf(call), '/auth/login')
  assert.equal(call.options.method, 'POST')
  assert.deepEqual(JSON.parse(call.options.body), {
    email: 'admin@aom.pt',
    password: 'secret',
  })
})

test('clientes usa o endpoint protegido correto', async () => {
  const calls = mockFetch([])

  await listClientes('token-123')

  const call = lastCall(calls)
  assert.equal(pathOf(call), '/clientes/')
  assert.equal(call.options.method, 'GET')
  assert.equal(call.options.headers.Authorization, 'Bearer token-123')
})

test('projetos cria registos no endpoint correto', async () => {
  const calls = mockFetch({ id_projeto: 1 })
  const payload = { referencia: 'P-001', designacao: 'Estrutura', estado: 'em_analise' }

  await createProject('token-123', payload)

  const call = lastCall(calls)
  assert.equal(pathOf(call), '/projetos/')
  assert.equal(call.options.method, 'POST')
  assert.deepEqual(JSON.parse(call.options.body), payload)
})

test('orcamentos cria registos no endpoint correto', async () => {
  const calls = mockFetch({ id_orcamento: 2 })
  const payload = { id_projeto: 1, versao: 'v1', estado: 'rascunho' }

  await createOrcamento('token-123', payload)

  const call = lastCall(calls)
  assert.equal(pathOf(call), '/orcamentos/')
  assert.equal(call.options.method, 'POST')
  assert.deepEqual(JSON.parse(call.options.body), payload)
})

test('ML envia previsoes para o endpoint principal', async () => {
  const calls = mockFetch({ custo_total: 100 })
  const payload = { tipologia: 'estrutura', peso_total_kg: 1200 }

  await predictCusto('token-123', payload)

  const call = lastCall(calls)
  assert.equal(pathOf(call), '/ml/orcamento/prever')
  assert.equal(call.options.method, 'POST')
  assert.deepEqual(JSON.parse(call.options.body), payload)
})

test('utilizadores cria registos no endpoint de administracao', async () => {
  const calls = mockFetch({ id_utilizador: 3 })
  const payload = {
    nome: 'Novo Utilizador',
    email: 'novo@siaom.local',
    perfil: 'orcamentista',
    password: 'Admin@123',
  }

  await createUtilizador('token-123', payload)

  const call = lastCall(calls)
  assert.equal(pathOf(call), '/utilizadores/')
  assert.equal(call.options.method, 'POST')
  assert.equal(call.options.headers.Authorization, 'Bearer token-123')
  assert.deepEqual(JSON.parse(call.options.body), payload)
})

test('realizado batch envia lista de orcamentos no formato esperado pelo backend', async () => {
  const calls = mockFetch([])

  await getRealizadoResumoBatch('token-123', [1, 2, 3])

  const call = lastCall(calls)
  assert.equal(pathOf(call), '/realizado/orcamentos/resumo')
  assert.equal(call.options.method, 'POST')
  assert.deepEqual(JSON.parse(call.options.body), { ids_orcamento: [1, 2, 3] })
})

test('realizado batch limpa IDs invalidos antes de enviar', async () => {
  const calls = mockFetch([])

  await getRealizadoResumoBatch('token-123', [1, '2', 0, null, 2, 'abc'])

  const call = lastCall(calls)
  assert.deepEqual(JSON.parse(call.options.body), { ids_orcamento: [1, 2] })
})

test('realizado batch divide listas grandes para respeitar limite da API', async () => {
  const calls = mockFetch([])
  const ids = Array.from({ length: 501 }, (_, index) => index + 1)

  await getRealizadoResumoBatch('token-123', ids)

  assert.equal(calls.length, 2)
  assert.equal(JSON.parse(calls[0].options.body).ids_orcamento.length, 500)
  assert.deepEqual(JSON.parse(calls[1].options.body), { ids_orcamento: [501] })
})

test('normalizeOrcamentoIds remove duplicados e valores invalidos', () => {
  assert.deepEqual(normalizeOrcamentoIds([3, '3', '4', 0, -1, null, undefined, 'x']), [3, 4])
})

test('apiRequest transforma erros de validacao FastAPI em mensagem legivel', async () => {
  mockFetch({ detail: [{ msg: 'Campo obrigatorio' }, { msg: 'Valor invalido' }] }, 422)

  await assert.rejects(
    () => apiRequest('/teste', { method: 'POST', body: { a: 1 } }),
    /Campo obrigatorio; Valor invalido/,
  )
})
