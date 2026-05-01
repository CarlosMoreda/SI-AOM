import assert from 'node:assert/strict'
import test from 'node:test'

import { getVisibleMenuItems } from '../src/components/menuConfig.js'

function keysFor(perfil) {
  return getVisibleMenuItems(perfil).map((item) => item.key)
}

test('menu de administrador inclui administracao e todos os modulos operacionais', () => {
  const keys = keysFor('administrador')

  assert.ok(keys.includes('dashboard'))
  assert.ok(keys.includes('clientes'))
  assert.ok(keys.includes('orcamentos'))
  assert.ok(keys.includes('ml'))
  assert.ok(keys.includes('utilizadores'))
})

test('menu de orcamentista esconde utilizadores e realizado', () => {
  const keys = keysFor('orcamentista')

  assert.ok(keys.includes('dashboard'))
  assert.ok(keys.includes('clientes'))
  assert.ok(keys.includes('materiais'))
  assert.ok(keys.includes('ml'))
  assert.equal(keys.includes('utilizadores'), false)
  assert.equal(keys.includes('realizado'), false)
})

test('menu de gestor foca planeamento e analise', () => {
  const keys = keysFor('gestor')

  assert.ok(keys.includes('dashboard'))
  assert.ok(keys.includes('clientes'))
  assert.ok(keys.includes('comparacao'))
  assert.equal(keys.includes('materiais'), false)
  assert.equal(keys.includes('realizado'), false)
})

test('menu de producao abre apenas areas permitidas', () => {
  const keys = keysFor('producao')

  assert.deepEqual(keys, ['realizado', 'comparacao', 'definicoes'])
})
