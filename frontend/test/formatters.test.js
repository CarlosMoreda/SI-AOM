import assert from 'node:assert/strict'
import test from 'node:test'

import { formatDate, formatMoney } from '../src/utils/formatters.js'

test('formatMoney devolve euro mesmo com valores invalidos', () => {
  assert.match(formatMoney(12.5), /^12,50/)
  assert.match(formatMoney('abc'), /^0,00/)
})

test('formatDate devolve fallback para datas vazias ou invalidas', () => {
  assert.equal(formatDate(null), '-')
  assert.equal(formatDate('valor-invalido'), 'valor-invalido')
})
