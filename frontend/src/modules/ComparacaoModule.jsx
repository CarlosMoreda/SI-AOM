import { useCallback, useState } from 'react'

import { formatMoney } from '../utils/formatters'
import { getBudgetComparison } from '../services/comparisonService'

const NO_DATA = '—'

function DesvioCell({ value, hasRealizado }) {
  if (!hasRealizado) return <span className="comparison-value-empty">{NO_DATA}</span>
  const n = Number(value)
  return <span className={getDesvioClass(n)}>{formatMoney(value)}</span>
}

function PercentCell({ value, hasRealizado }) {
  if (!hasRealizado) return <span className="comparison-value-empty">{NO_DATA}</span>
  const n = Number(value)
  return <span className={getDesvioClass(n)}>{n.toFixed(2)}%</span>
}

function getDesvioClass(value) {
  if (value > 0) return 'comparison-value-positive'
  if (value < 0) return 'comparison-value-negative'
  return ''
}

function hasRealizadoValue(value) {
  return Number(value) > 0
}

const CATEGORIA_LABEL = {
  materiais: 'Materiais',
  operacoes: 'Operações',
  servicos: 'Serviços',
  total: 'Total',
  horas: 'Horas',
}

function AlertasDesvio({ alertas, limiar }) {
  if (!alertas || alertas.length === 0) return null

  return (
    <div className="alertas-desvio">
      <p className="alertas-desvio-head">
        <strong>Alertas de desvio</strong>
        <small>limiar aplicado: {Number(limiar).toFixed(2)}%</small>
      </p>
      <ul>
        {alertas.map((a) => {
          const isHoras = a.categoria === 'horas'
          const desvioAbs = isHoras
            ? `${Number(a.desvio_abs).toFixed(2)} h`
            : formatMoney(a.desvio_abs)
          const cls = a.severidade === 'alta'
            ? 'message error'
            : 'message warning'
          return (
            <li key={a.categoria} className={cls}>
              <strong>{CATEGORIA_LABEL[a.categoria] || a.categoria}</strong>:
              {' '}desvio de {Number(a.desvio_percent).toFixed(2)}% ({desvioAbs})
              {' '}— severidade <strong>{a.severidade}</strong>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default function ComparacaoModule({ token }) {
  const [budgetId, setBudgetId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)

  const handleSubmit = useCallback(
    async (event) => {
      event.preventDefault()
      if (!budgetId) return
      setLoading(true)
      setError('')
      setData(null)
      try {
        const result = await getBudgetComparison(token, budgetId)
        setData(result)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    },
    [token, budgetId],
  )

  return (
    <div className="module-layout">
      <div className="panel">
        <div className="panel-head">
          <h3>Comparação Orçado vs Real</h3>
          <span>Análise de desvios por orçamento</span>
        </div>

        {error && <p className="message error">{error}</p>}

        <form className="comparison-form" onSubmit={handleSubmit}>
          <label>
            ID do Orçamento
            <input
              type="number"
              min="1"
              value={budgetId}
              onChange={(e) => setBudgetId(e.target.value)}
              required
              placeholder="Ex: 1"
            />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? 'A carregar...' : 'Ver comparação'}
          </button>
        </form>

        {data && (() => {
          const semRealizadoTotal = !hasRealizadoValue(data.total.real)
            && !hasRealizadoValue(data.horas.reais)
          const horasHasRealizado = hasRealizadoValue(data.horas.reais)

          return (
            <div className="comparison-result">
              <p className="comparison-subtitle">Orçamento #{data.id_orcamento}</p>

              {semRealizadoTotal && (
                <p className="message info comparison-empty-notice">
                  Sem realizado registado. Este orçamento ainda não tem custos reais
                  imputados — a análise de desvios fica disponível assim que a produção
                  registar os primeiros valores.
                </p>
              )}

              <AlertasDesvio
                alertas={data.alertas}
                limiar={data.limiar_aplicado_percent}
              />

              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Categoria</th>
                      <th>Orçado</th>
                      <th>Real</th>
                      <th>Desvio Abs.</th>
                      <th>Desvio %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { label: 'Materiais', bloco: data.materiais },
                      { label: 'Operações', bloco: data.operacoes },
                      { label: 'Serviços', bloco: data.servicos },
                      { label: 'Total', bloco: data.total },
                    ].map(({ label, bloco }) => {
                      const hasReal = hasRealizadoValue(bloco.real)
                      return (
                        <tr key={label}>
                          <td><strong>{label}</strong></td>
                          <td>{formatMoney(bloco.orcado)}</td>
                          <td>{formatMoney(bloco.real)}</td>
                          <td><DesvioCell value={bloco.desvio_abs} hasRealizado={hasReal} /></td>
                          <td><PercentCell value={bloco.desvio_percent} hasRealizado={hasReal} /></td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              <div className="panel comparison-nested-panel">
                <div className="panel-head">
                  <h3>Horas</h3>
                  <span>Previstas vs Reais</span>
                </div>
                <div className="compare-grid">
                  <div>
                    <p>Previstas</p>
                    <strong>{Number(data.horas.previstas).toFixed(2)} h</strong>
                  </div>
                  <div>
                    <p>Reais</p>
                    <strong>{Number(data.horas.reais).toFixed(2)} h</strong>
                  </div>
                  <div>
                    <p>Desvio Abs.</p>
                    {horasHasRealizado ? (
                      <strong className={getDesvioClass(Number(data.horas.desvio_abs))}>
                        {Number(data.horas.desvio_abs).toFixed(2)} h
                      </strong>
                    ) : (
                      <strong className="comparison-value-empty">{NO_DATA}</strong>
                    )}
                  </div>
                  <div>
                    <p>Desvio %</p>
                    {horasHasRealizado ? (
                      <strong className={getDesvioClass(Number(data.horas.desvio_percent))}>
                        {Number(data.horas.desvio_percent).toFixed(2)}%
                      </strong>
                    ) : (
                      <strong className="comparison-value-empty">{NO_DATA}</strong>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })()}
      </div>
    </div>
  )
}
