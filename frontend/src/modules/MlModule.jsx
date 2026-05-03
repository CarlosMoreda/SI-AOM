import { useCallback, useEffect, useState } from 'react'

import { formatMoney } from '../utils/formatters'
import { getCustoOptions, predictCusto, trainCustoModels } from '../services/mlService'

const DEFAULT_OPTIONS = {
  tipologias: [],
  complexidades: [],
  materiais: [],
  tratamentos: [],
  processos_corte: [],
  feature_ranges: {},
  feature_defaults: {},
  features_usadas: [],
  dataset_linhas: null,
  source: 'indisponivel',
}

const EMPTY_PARAMS = {
  tipologia: '',
  complexidade: '',
  peso_total_kg: '',
  numero_pecas: '',
  material_principal: '',
  tratamento_superficie: '',
  processo_corte: '',
  lead_time: '',
}

const OPTION_KEYS_BY_FIELD = {
  tipologia: 'tipologias',
  complexidade: 'complexidades',
  material_principal: 'materiais',
  tratamento_superficie: 'tratamentos',
  processo_corte: 'processos_corte',
}

const NUMERIC_FIELDS = {
  peso_total_kg: { integer: false, fallbackMin: 0.01, fallbackPlaceholder: 'ex: 4500.5' },
  numero_pecas: { integer: true, fallbackMin: 1, fallbackPlaceholder: 'ex: 12' },
  lead_time: { integer: true, fallbackMin: 1, fallbackPlaceholder: 'ex: 30' },
}

function numericInputValue(field, value) {
  if (value === null || value === undefined || value === '') return ''
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return ''
  return NUMERIC_FIELDS[field]?.integer ? String(Math.round(numeric)) : String(Number(numeric.toFixed(2)))
}

function formatRangeValue(field, value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return ''
  return NUMERIC_FIELDS[field]?.integer ? String(Math.round(numeric)) : numeric.toFixed(2)
}

function sourceLabel(source) {
  if (source === 'dataset_csv') return 'CSV do dataset'
  if (source === 'base_dados') return 'dataset gerado da BD'
  if (source === 'modelo') return 'modelo treinado'
  return 'indisponivel'
}

export default function MlModule({ token, user }) {
  const isAdmin = user?.perfil === 'administrador'

  const [activeTab, setActiveTab] = useState('prever')

  const [params, setParams] = useState(EMPTY_PARAMS)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [options, setOptions] = useState(DEFAULT_OPTIONS)
  const [optionsLoading, setOptionsLoading] = useState(false)
  const [optionsError, setOptionsError] = useState('')

  const [trainLoading, setTrainLoading] = useState(false)
  const [trainError, setTrainError] = useState('')
  const [trainResult, setTrainResult] = useState(null)

  function setParam(key, value) {
    setParams((p) => ({ ...p, [key]: value }))
  }

  function optionsFor(key) {
    return Array.isArray(options[key]) ? options[key] : []
  }

  function featureRange(field) {
    const range = options.feature_ranges?.[field]
    if (!range) return null
    const min = Number(range.min)
    const max = Number(range.max)
    if (!Number.isFinite(min) || !Number.isFinite(max)) return null
    return { min, max }
  }

  function rangePlaceholder(field) {
    const range = featureRange(field)
    if (!range) return NUMERIC_FIELDS[field]?.fallbackPlaceholder || ''
    return `${formatRangeValue(field, range.min)} - ${formatRangeValue(field, range.max)}`
  }

  function rangeText(field) {
    const range = featureRange(field)
    if (!range) return ''
    return `Dataset: ${formatRangeValue(field, range.min)} a ${formatRangeValue(field, range.max)}`
  }

  function getQualityLabel(quality) {
    if (quality === 'boa') return 'Boa'
    if (quality === 'aceitavel') return 'Aceitavel'
    if (quality === 'fraca') return 'Fraca'
    return 'Indeterminada'
  }

  function getConfidenceLabel(confidence) {
    if (confidence >= 70) return 'Confianca alta'
    if (confidence >= 45) return 'Confianca media'
    return 'Confianca baixa'
  }

  useEffect(() => {
    if (!token) return
    let cancelled = false

    async function loadOptions() {
      setOptionsLoading(true)
      setOptionsError('')
      try {
        const res = await getCustoOptions(token)
        if (!cancelled) {
          setOptions({ ...DEFAULT_OPTIONS, ...(res || {}) })
        }
      } catch (err) {
        if (!cancelled) {
          setOptionsError(err.message || 'Erro ao carregar opcoes de ML.')
          setOptions(DEFAULT_OPTIONS)
        }
      } finally {
        if (!cancelled) setOptionsLoading(false)
      }
    }

    loadOptions()
    return () => {
      cancelled = true
    }
  }, [token])

  useEffect(() => {
    const defaults = options.feature_defaults || {}
    setParams((current) => {
      const next = { ...current }
      let changed = false

      Object.entries(OPTION_KEYS_BY_FIELD).forEach(([field, optionKey]) => {
        if (next[field]) return
        const values = Array.isArray(options[optionKey]) ? options[optionKey] : []
        if (values.length === 0) return
        const defaultValue = defaults[field] !== undefined && defaults[field] !== null ? String(defaults[field]) : ''
        next[field] = defaultValue && values.includes(defaultValue) ? defaultValue : values[0]
        changed = true
      })

      Object.keys(NUMERIC_FIELDS).forEach((field) => {
        if (next[field]) return
        const value = numericInputValue(field, defaults[field])
        if (!value) return
        next[field] = value
        changed = true
      })

      return changed ? next : current
    })
  }, [options])

  const handlePredict = useCallback(
    async (e) => {
      e.preventDefault()
      setLoading(true)
      setError('')
      setResult(null)
      try {
        const payload = {
          tipologia: params.tipologia || null,
          complexidade: params.complexidade || null,
          peso_total_kg: params.peso_total_kg !== '' ? Number(params.peso_total_kg) : null,
          numero_pecas: params.numero_pecas !== '' ? Number(params.numero_pecas) : null,
          material_principal: params.material_principal || null,
          tratamento_superficie: params.tratamento_superficie || null,
          processo_corte: params.processo_corte || null,
          lead_time: params.lead_time !== '' ? Number(params.lead_time) : null,
        }
        setResult(await predictCusto(token, payload))
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    },
    [token, params],
  )

  const handleTrain = useCallback(
    async (e) => {
      e.preventDefault()
      if (!window.confirm('Iniciar treino dos modelos de previsao de orcamento?')) return
      setTrainLoading(true)
      setTrainError('')
      setTrainResult(null)
      try {
        const res = await trainCustoModels(token)
        setTrainResult(res)
        // Se todos falharam, mostra o primeiro erro como mensagem principal
        if (res.success === 0) {
          const firstErr = res.results.find((r) => r.status === 'error')
          if (firstErr) setTrainError(firstErr.detail)
        }
      } catch (err) {
        // err.message pode vir do apiClient (ja trata arrays de validacao)
        setTrainError(err.message || 'Erro desconhecido ao contactar o servidor.')
      } finally {
        setTrainLoading(false)
      }
    },
    [token],
  )

  return (
    <div className="module-layout">
      <div className="tab-bar">
        <button
          type="button"
          className={`tab-btn ${activeTab === 'prever' ? 'active' : ''}`}
          onClick={() => setActiveTab('prever')}
        >
          Prever Orcamento
        </button>
        {isAdmin && (
          <button
            type="button"
            className={`tab-btn ${activeTab === 'treino' ? 'active' : ''}`}
            onClick={() => setActiveTab('treino')}
          >
            Treinar Modelos
          </button>
        )}
      </div>

      {activeTab === 'prever' && (
        <div className="panel">
          <div className="panel-head">
            <h3>Previsao de Orcamento</h3>
            <span>Fluxo principal: estimativa inicial do custo (materiais, operacoes e servicos)</span>
          </div>

          {error && (
            <p className="message error">
              {error}
              {error.includes('nao foram treinados') && isAdmin && (
                <> - <button type="button" className="btn-xs ml-train-link" onClick={() => setActiveTab('treino')}>Ir para Treino</button></>
              )}
            </p>
          )}
          {error && error.includes('nao foram treinados') && !isAdmin && (
            <p className="ml-hint ml-train-hint">Contacte um administrador para treinar os modelos.</p>
          )}
          {optionsError && <p className="message error">{optionsError}</p>}
          {!optionsError && (options.dataset_linhas || options.source !== 'indisponivel') && (
            <div className="ml-dataset-meta">
              <span>Origem: {sourceLabel(options.source)}</span>
              {options.dataset_linhas ? <span>{options.dataset_linhas} linhas</span> : null}
            </div>
          )}

          <form onSubmit={handlePredict}>
            <fieldset className="ml-fieldset">
              <legend>Caracteristicas do Projeto</legend>
              <div className="form-row">
                <label>
                  Tipologia
                  <select required disabled={optionsLoading} value={params.tipologia} onChange={(e) => setParam('tipologia', e.target.value)}>
                    <option value="">{optionsLoading ? 'A carregar...' : 'Selecionar'}</option>
                    {optionsFor('tipologias').map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </label>
                <label>
                  Complexidade
                  <select required disabled={optionsLoading} value={params.complexidade} onChange={(e) => setParam('complexidade', e.target.value)}>
                    <option value="">{optionsLoading ? 'A carregar...' : 'Selecionar'}</option>
                    {optionsFor('complexidades').map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </label>
                <label>
                  Peso total (kg)
                  <input
                    required
                    type="number" step="0.01" min={featureRange('peso_total_kg')?.min ?? 0.01} max={featureRange('peso_total_kg')?.max ?? undefined}
                    value={params.peso_total_kg}
                    onChange={(e) => setParam('peso_total_kg', e.target.value)}
                    placeholder={rangePlaceholder('peso_total_kg')}
                  />
                  {rangeText('peso_total_kg') && <small className="ml-range-note">{rangeText('peso_total_kg')}</small>}
                </label>
                <label>
                  N. de pecas
                  <input
                    required
                    type="number" min={featureRange('numero_pecas')?.min ?? 1} max={featureRange('numero_pecas')?.max ?? undefined}
                    value={params.numero_pecas}
                    onChange={(e) => setParam('numero_pecas', e.target.value)}
                    placeholder={rangePlaceholder('numero_pecas')}
                  />
                  {rangeText('numero_pecas') && <small className="ml-range-note">{rangeText('numero_pecas')}</small>}
                </label>
                <label>
                  Material principal
                  <select required disabled={optionsLoading} value={params.material_principal} onChange={(e) => setParam('material_principal', e.target.value)}>
                    <option value="">{optionsLoading ? 'A carregar...' : 'Selecionar'}</option>
                    {optionsFor('materiais').map((m) => <option key={m} value={m}>{m}</option>)}
                  </select>
                </label>
                <label>
                  Tratamento superficie
                  <select required disabled={optionsLoading} value={params.tratamento_superficie} onChange={(e) => setParam('tratamento_superficie', e.target.value)}>
                    <option value="">{optionsLoading ? 'A carregar...' : 'Selecionar'}</option>
                    {optionsFor('tratamentos').map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </label>
                <label>
                  Processo de corte
                  <select required disabled={optionsLoading} value={params.processo_corte} onChange={(e) => setParam('processo_corte', e.target.value)}>
                    <option value="">{optionsLoading ? 'A carregar...' : 'Selecionar'}</option>
                    {optionsFor('processos_corte').map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </label>
                <label>
                  Lead time (dias)
                  <input
                    required
                    type="number" min={featureRange('lead_time')?.min ?? 1} max={featureRange('lead_time')?.max ?? undefined}
                    value={params.lead_time}
                    onChange={(e) => setParam('lead_time', e.target.value)}
                    placeholder={rangePlaceholder('lead_time')}
                  />
                  {rangeText('lead_time') && <small className="ml-range-note">{rangeText('lead_time')}</small>}
                </label>
              </div>
            </fieldset>

            <div className="ml-action-row">
              <button type="submit" disabled={loading} className="ml-submit-button">
                {loading ? 'A calcular...' : 'Prever orcamento'}
              </button>
            </div>
          </form>

          {result && (
            <div className="ml-result-box">
              <div className="ml-result-header">
                <span>Orcamento Previsto pelo ML</span>
                <span className="ml-modelo">
                  {result.modelo_utilizado}
                  {result.modelo_versao ? ` - v${result.modelo_versao}` : ''}
                  {result.qualidade_modelo ? ` - qualidade ${getQualityLabel(result.qualidade_modelo)}` : ''}
                </span>
              </div>

              <div className="ml-confidence-box">
                <div className="ml-confidence-head">
                  <span>Confianca da previsao</span>
                  <strong>{Number(result.confianca_percentual || 0)}%</strong>
                </div>
                <div
                  className="ml-confidence-track"
                  role="progressbar"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={Number(result.confianca_percentual || 0)}
                >
                  <div
                    className="ml-confidence-fill"
                    style={{ width: `${Math.max(0, Math.min(100, Number(result.confianca_percentual || 0)))}%` }}
                  />
                </div>
                <small>{getConfidenceLabel(Number(result.confianca_percentual || 0))}</small>
              </div>

              {result.aviso_faixa_treino && (
                <div className="ml-range-warning">
                  <p className="message error">{result.aviso_faixa_treino}</p>
                  {Array.isArray(result.alertas_faixa_treino) && result.alertas_faixa_treino.length > 0 && (
                    <ul>
                      {result.alertas_faixa_treino.map((alerta) => (
                        <li key={alerta}>{alerta}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {result.aviso_qualidade && (
                <p className={result.qualidade_modelo === 'fraca' ? 'message error' : 'ml-hint'}>
                  {result.aviso_qualidade}
                </p>
              )}

              <div className="ml-result-grid">
                <div className="ml-result-card">
                  <p>Materiais</p>
                  <strong>{formatMoney(result.custo_materiais)}</strong>
                  <small>
                    {result.custo_total > 0
                      ? `${((result.custo_materiais / result.custo_total) * 100).toFixed(1)}% do total`
                      : '-'}
                  </small>
                </div>
                <div className="ml-result-card">
                  <p>Operacoes</p>
                  <strong>{formatMoney(result.custo_operacoes)}</strong>
                  <small>
                    {result.custo_total > 0
                      ? `${((result.custo_operacoes / result.custo_total) * 100).toFixed(1)}% do total`
                      : '-'}
                  </small>
                </div>
                <div className="ml-result-card">
                  <p>Servicos</p>
                  <strong>{formatMoney(result.custo_servicos)}</strong>
                  <small>
                    {result.custo_total > 0
                      ? `${((result.custo_servicos / result.custo_total) * 100).toFixed(1)}% do total`
                      : '-'}
                  </small>
                </div>
                <div className="ml-result-card ml-card-total">
                  <p>Custo Total Previsto</p>
                  <strong>{formatMoney(result.custo_total)}</strong>
                </div>
              </div>

              {result.custo_total > 0 && (
                <>
                  <div className="ml-barra-custos">
                    <div
                      className="ml-barra-seg ml-barra-mat"
                      style={{ width: `${(result.custo_materiais / result.custo_total) * 100}%` }}
                      title={`Materiais: ${formatMoney(result.custo_materiais)}`}
                    />
                    <div
                      className="ml-barra-seg ml-barra-op"
                      style={{ width: `${(result.custo_operacoes / result.custo_total) * 100}%` }}
                      title={`Operacoes: ${formatMoney(result.custo_operacoes)}`}
                    />
                    <div
                      className="ml-barra-seg ml-barra-svc"
                      style={{ width: `${(result.custo_servicos / result.custo_total) * 100}%` }}
                      title={`Servicos: ${formatMoney(result.custo_servicos)}`}
                    />
                  </div>
                  <div className="ml-barra-legenda">
                    <span className="ml-leg-mat">Materiais</span>
                    <span className="ml-leg-op">Operacoes</span>
                    <span className="ml-leg-svc">Servicos</span>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}

      {isAdmin && activeTab === 'treino' && (
        <div className="panel">
          <div className="panel-head">
            <h3>Treinar Modelos de Previsao</h3>
            <span>Apenas administradores - Treina o pipeline principal de custo de orcamento</span>
          </div>

          <div className="panel ml-train-summary">
            <p className="ml-train-copy">
              O treino usa todos os orcamentos existentes na BD (com custo_total_orcado &gt; 0) para aprender a relacao entre as caracteristicas do projeto e os custos.<br />
              <strong>Recomendado treinar sempre que existirem novos orcamentos.</strong>
            </p>
          </div>

          {trainError && <p className="message error">{trainError}</p>}

          <form onSubmit={handleTrain}>
            <button type="submit" disabled={trainLoading} className="ml-train-button">
              {trainLoading ? 'A treinar... (aguarde)' : 'Treinar modelos de previsao'}
            </button>
          </form>

          {trainResult && (
            <div className="ml-train-result">
              <p className="ml-train-result-title">
                {trainResult.success} de {trainResult.total} modelos treinados com sucesso.
              </p>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr><th>Modelo</th><th>Estado</th><th>Detalhe</th></tr>
                  </thead>
                  <tbody>
                    {trainResult.results.map((r, i) => (
                      <tr key={i}>
                        <td>{r.dataset_type}</td>
                        <td>
                          <span className={`badge ${r.status === 'ok' ? 'badge-aprovado' : 'badge-rejeitado'}`}>
                            {r.status === 'ok' ? 'ok' : 'erro'}
                          </span>
                        </td>
                        <td className="ml-train-detail">{r.detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {trainResult.success === trainResult.total && (
                <p className="message success message-spaced">
                  Modelos prontos. Ja pode usar a previsao de orcamento.
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}



