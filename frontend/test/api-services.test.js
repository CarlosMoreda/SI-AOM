import assert from 'node:assert/strict'
import test from 'node:test'

import { login } from '../src/services/authService.js'
import { listClientes } from '../src/services/clienteService.js'
import { createOrcamento } from '../src/services/orcamentoService.js'
import { createProject } from '../src/services/projectService.js'
import { predictCusto } from '../src/services/mlService.js'

function mockFetch(payload = {}) {
  const calls = []

  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    return new Response(JSON.stringify(payload), {
      status: 200,
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
