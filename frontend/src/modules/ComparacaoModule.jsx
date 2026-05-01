import { useCallback, useState } from 'react'

import { formatMoney } from '../utils/formatters'
import { getBudgetComparison } from '../services/comparisonService'

function DesvioCell({ value }) {
  const n = Number(value)
  return <span className={getDesvioClass(n)}>{formatMoney(value)}</span>
}

function PercentCell({ value }) {
  const n = Number(value)
  return <span className={getDesvioClass(n)}>{n.toFixed(2)}%</span>
}

function getDesvioClass(value) {
  if (value > 0) return 'comparison-value-positive'
  if (value < 0) return 'comparison-value-negative'
  return ''
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
          <h3>Comparacao Orcado vs Real</h3>
          <span>Analise de desvios por orcamento</span>
        </div>

        {error && <p className="message error">{error}</p>}

        <form className="comparison-form" onSubmit={handleSubmit}>
          <label>
            ID do Orcamento
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
            {loading ? 'A carregar...' : 'Ver comparacao'}
          </button>
        </form>

        {data && (
          <div className="comparison-result">
            <p className="comparison-subtitle">Orcamento #{data.id_orcamento}</p>

            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Categoria</th>
                    <th>Orcado</th>
                    <th>Real</th>
                    <th>Desvio Abs.</th>
                    <th>Desvio %</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: 'Materiais', bloco: data.materiais },
                    { label: 'Operacoes', bloco: data.operacoes },
                    { label: 'Servicos', bloco: data.servicos },
                    { label: 'Total', bloco: data.total },
                  ].map(({ label, bloco }) => (
                    <tr key={label}>
                      <td><strong>{label}</strong></td>
                      <td>{formatMoney(bloco.orcado)}</td>
                      <td>{formatMoney(bloco.real)}</td>
                      <td><DesvioCell value={bloco.desvio_abs} /></td>
                      <td><PercentCell value={bloco.desvio_percent} /></td>
                    </tr>
                  ))}
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
                  <strong className={getDesvioClass(Number(data.horas.desvio_abs))}>
                    {Number(data.horas.desvio_abs).toFixed(2)} h
                  </strong>
                </div>
                <div>
                  <p>Desvio %</p>
                  <strong className={getDesvioClass(Number(data.horas.desvio_percent))}>
                    {Number(data.horas.desvio_percent).toFixed(2)}%
                  </strong>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
