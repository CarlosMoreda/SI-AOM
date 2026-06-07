import assert from 'node:assert/strict'
import test from 'node:test'

import { formatDate, formatMoney, formatStatusLabel, formatVersionLabel } from '../src/utils/formatters.js'

test('formatMoney devolve euro mesmo com valores invalidos', () => {
  assert.match(formatMoney(12.5), /^12,50/)
  assert.match(formatMoney('abc'), /^0,00/)
})

test('formatDate devolve fallback para datas vazias ou invalidas', () => {
  assert.equal(formatDate(null), '-')
  assert.equal(formatDate('valor-invalido'), 'valor-invalido')
})

test('formatStatusLabel apresenta estados em portugues legivel', () => {
  assert.equal(formatStatusLabel('em_analise'), 'Em análise')
  assert.equal(formatStatusLabel('em_execucao'), 'Em execução')
  assert.equal(formatStatusLabel('estado_personalizado'), 'Estado personalizado')
})

test('formatVersionLabel evita duplicar o prefixo v', () => {
  assert.equal(formatVersionLabel('v1'), 'v1')
  assert.equal(formatVersionLabel('1'), 'v1')
  assert.equal(formatVersionLabel('V2'), 'V2')
  assert.equal(formatVersionLabel(''), '-')
})
