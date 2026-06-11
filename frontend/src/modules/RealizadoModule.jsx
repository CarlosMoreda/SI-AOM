import { useCallback, useEffect, useMemo, useState } from 'react'

import { formatDate, formatMoney, formatStatusLabel, formatVersionLabel } from '../utils/formatters'
import { listProjectBudgets, listProjects } from '../services/projectService'
import { listOrcamentos, listOrcamentoMateriais, listOrcamentoOperacoes, listOrcamentoServicos } from '../services/orcamentoService'
import { listMateriais } from '../services/materialService'
import { listOperacoes } from '../services/operacaoService'
import { listServicos } from '../services/servicoService'
import {
  createRealizadoMaterial,
  deleteRealizadoMaterial,
  listRealizadoMaterial,
  createRealizadoOperacao,
  deleteRealizadoOperacao,
  listRealizadoOperacao,
  createRealizadoServico,
  deleteRealizadoServico,
  listRealizadoServico,
  getRealizadoResumo,
} from '../services/realizadoService'

const TAB_LABELS = {
  materiais: 'Materiais',
  operacoes: 'Operações',
  servicos: 'Serviços',
}

// Em execucao: registo normal. Concluido: correcoes pos-fecho continuam
// possiveis (espelha a regra do backend).
const ESTADOS_REALIZADO_PERMITIDOS = new Set(['em_execucao', 'concluido'])

function permiteRealizadoPorEstado(estado) {
  return ESTADOS_REALIZADO_PERMITIDOS.has(String(estado || '').toLowerCase())
}

export default function RealizadoModule({ token }) {
  const [projects, setProjects] = useState([])
  const [orcamentos, setOrcamentos] = useState([])
  const [filterProjectId, setFilterProjectId] = useState('')
  const [selectedOrcId, setSelectedOrcId] = useState('')

  const [activeTab, setActiveTab] = useState('materiais')

  // Catalogos para enriquecer os nomes dos itens nas linhas.
  const [catalogMateriais, setCatalogMateriais] = useState([])
  const [catalogOperacoes, setCatalogOperacoes] = useState([])
  const [catalogServicos, setCatalogServicos] = useState([])

  const [linhasMateriais, setLinhasMateriais] = useState([])
  const [linhasOperacoes, setLinhasOperacoes] = useState([])
  const [linhasServicos, setLinhasServicos] = useState([])

  const [realizadosByLinhaMat, setRealizadosByLinhaMat] = useState({})
  const [realizadosByLinhaOp, setRealizadosByLinhaOp] = useState({})
  const [realizadosByLinhaSvc, setRealizadosByLinhaSvc] = useState({})

  const [resumo, setResumo] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingOrcamentos, setLoadingOrcamentos] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Add forms for each line
  const [addMatForms, setAddMatForms] = useState({})
  const [addOpForms, setAddOpForms] = useState({})
  const [addSvcForms, setAddSvcForms] = useState({})

  function clearSelectedOrcamento() {
    setSelectedOrcId('')
    setLinhasMateriais([])
    setLinhasOperacoes([])
    setLinhasServicos([])
    setRealizadosByLinhaMat({})
    setRealizadosByLinhaOp({})
    setRealizadosByLinhaSvc({})
    setResumo(null)
    setAddMatForms({})
    setAddOpForms({})
    setAddSvcForms({})
  }

  const loadBase = useCallback(async () => {
    if (!token) return
    try {
      const [projs, orcs, mats, ops, svcs] = await Promise.all([
        listProjects(token),
        listOrcamentos(token),
        listMateriais(token),
        listOperacoes(token),
        listServicos(token),
      ])
      setProjects(projs)
      setOrcamentos(orcs)
      setCatalogMateriais(mats)
      setCatalogOperacoes(ops)
      setCatalogServicos(svcs)
    } catch (e) {
      setError(e.message)
    }
  }, [token])

  useEffect(() => {
    loadBase()
  }, [loadBase])

  const materialById = useMemo(
    () => new Map(catalogMateriais.map((m) => [m.id_material, m])),
    [catalogMateriais],
  )
  const operacaoById = useMemo(
    () => new Map(catalogOperacoes.map((o) => [o.id_operacao, o])),
    [catalogOperacoes],
  )
  const servicoById = useMemo(
    () => new Map(catalogServicos.map((s) => [s.id_servico, s])),
    [catalogServicos],
  )
  const projectById = useMemo(
    () => new Map(projects.map((p) => [String(p.id_projeto), p])),
    [projects],
  )
  const projectsComRealizado = useMemo(
    () => projects.filter((p) => permiteRealizadoPorEstado(p.estado)),
    [projects],
  )

  function describeMaterial(idMaterial) {
    const mat = materialById.get(idMaterial)
    if (!mat) return `Material #${idMaterial}`
    return mat.codigo ? `${mat.codigo} - ${mat.nome}` : mat.nome
  }
  function describeOperacao(idOperacao) {
    const op = operacaoById.get(idOperacao)
    if (!op) return `Operação #${idOperacao}`
    return op.codigo ? `${op.codigo} - ${op.nome}` : op.nome
  }
  function describeServico(idServico) {
    const svc = servicoById.get(idServico)
    if (!svc) return `Serviço #${idServico}`
    return svc.codigo ? `${svc.codigo} - ${svc.nome}` : svc.nome
  }

  const filteredOrcs = orcamentos.filter((o) => {
    if (filterProjectId && String(o.id_projeto) !== filterProjectId) return false

    const projeto = projectById.get(String(o.id_projeto))
    return (
      permiteRealizadoPorEstado(projeto?.estado)
      && permiteRealizadoPorEstado(o.estado)
    )
  })

  async function handleProjectChange(projectId) {
    setFilterProjectId(projectId)
    clearSelectedOrcamento()
    setError('')
    setLoadingOrcamentos(true)
    try {
      const nextOrcamentos = projectId
        ? await listProjectBudgets(token, projectId)
        : await listOrcamentos(token)
      setOrcamentos(nextOrcamentos)
    } catch (e) {
      setError(e.message)
      setOrcamentos([])
    } finally {
      setLoadingOrcamentos(false)
    }
  }

  const loadOrcDetails = useCallback(async (orcId) => {
    if (!orcId || !token) return
    setLoading(true)
    setError('')
    try {
      const [mats, ops, svcs, rsm] = await Promise.all([
        listOrcamentoMateriais(token, orcId),
        listOrcamentoOperacoes(token, orcId),
        listOrcamentoServicos(token, orcId),
        getRealizadoResumo(token, orcId),
      ])
      setLinhasMateriais(mats)
      setLinhasOperacoes(ops)
      setLinhasServicos(svcs)
      setResumo(rsm)

      // Load realizado for each line
      const matMap = {}
      for (const l of mats) {
        try {
          matMap[l.id_linha_material] = await listRealizadoMaterial(token, l.id_linha_material)
        } catch {
          matMap[l.id_linha_material] = []
        }
      }
      setRealizadosByLinhaMat(matMap)

      const opMap = {}
      for (const l of ops) {
        try {
          opMap[l.id_linha_operacao] = await listRealizadoOperacao(token, l.id_linha_operacao)
        } catch {
          opMap[l.id_linha_operacao] = []
        }
      }
      setRealizadosByLinhaOp(opMap)

      const svcMap = {}
      for (const l of svcs) {
        try {
          svcMap[l.id_linha_servico] = await listRealizadoServico(token, l.id_linha_servico)
        } catch {
          svcMap[l.id_linha_servico] = []
        }
      }
      setRealizadosByLinhaSvc(svcMap)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [token])

  async function handleSelectOrc(orcId) {
    setSelectedOrcId(orcId)
    setRealizadosByLinhaMat({})
    setRealizadosByLinhaOp({})
    setRealizadosByLinhaSvc({})
    setResumo(null)
    if (orcId) await loadOrcDetails(orcId)
  }

  // Material realizado
  async function handleAddRealizadoMat(idLinha) {
    const f = addMatForms[idLinha] || { quantidade: '', peso_kg: '', custo_unitario_real: '', observacoes: '' }
    if (!f.quantidade) return
    setError('')
    try {
      await createRealizadoMaterial(token, {
        id_linha_material: idLinha,
        quantidade: Number(f.quantidade),
        peso_kg: f.peso_kg !== '' ? Number(f.peso_kg) : null,
        custo_unitario_real: f.custo_unitario_real !== '' ? Number(f.custo_unitario_real) : null,
        observacoes: f.observacoes || null,
      })
      setAddMatForms((prev) => ({ ...prev, [idLinha]: { quantidade: '', peso_kg: '', custo_unitario_real: '', observacoes: '' } }))
      setSuccess('Realizado registado.')
      await loadOrcDetails(selectedOrcId)
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleDeleteRealizadoMat(id) {
    if (!window.confirm('Remover este registo de material realizado?')) return
    setError('')
    setSuccess('')
    try {
      await deleteRealizadoMaterial(token, id)
      setSuccess('Registo de material removido.')
      await loadOrcDetails(selectedOrcId)
    } catch (e) {
      setError(e.message)
    }
  }

  // Operação realizada
  async function handleAddRealizadoOp(idLinha) {
    const f = addOpForms[idLinha] || { horas: '', custo_hora_real: '', observacoes: '' }
    if (!f.horas) return
    setError('')
    try {
      await createRealizadoOperacao(token, {
        id_linha_operacao: idLinha,
        horas: Number(f.horas),
        custo_hora_real: f.custo_hora_real !== '' ? Number(f.custo_hora_real) : null,
        observacoes: f.observacoes || null,
      })
      setAddOpForms((prev) => ({ ...prev, [idLinha]: { horas: '', custo_hora_real: '', observacoes: '' } }))
      setSuccess('Realizado registado.')
      await loadOrcDetails(selectedOrcId)
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleDeleteRealizadoOp(id) {
    if (!window.confirm('Remover este registo de operação realizada?')) return
    setError('')
    setSuccess('')
    try {
      await deleteRealizadoOperacao(token, id)
      setSuccess('Registo de operação removido.')
      await loadOrcDetails(selectedOrcId)
    } catch (e) {
      setError(e.message)
    }
  }

  // Serviço realizado
  async function handleAddRealizadoSvc(idLinha) {
    const f = addSvcForms[idLinha] || { quantidade: '', preco_unitario_real: '', observacoes: '' }
    if (!f.quantidade) return
    setError('')
    try {
      await createRealizadoServico(token, {
        id_linha_servico: idLinha,
        quantidade: Number(f.quantidade),
        preco_unitario_real: f.preco_unitario_real !== '' ? Number(f.preco_unitario_real) : null,
        observacoes: f.observacoes || null,
      })
      setAddSvcForms((prev) => ({ ...prev, [idLinha]: { quantidade: '', preco_unitario_real: '', observacoes: '' } }))
      setSuccess('Realizado registado.')
      await loadOrcDetails(selectedOrcId)
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleDeleteRealizadoSvc(id) {
    if (!window.confirm('Remover este registo de serviço realizado?')) return
    setError('')
    setSuccess('')
    try {
      await deleteRealizadoServico(token, id)
      setSuccess('Registo de serviço removido.')
      await loadOrcDetails(selectedOrcId)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="module-layout">
      <div className="panel">
        <div className="panel-head">
          <h3>Realizado</h3>
          <span>Registo de custos reais</span>
        </div>

        {error && <p className="message error">{error}</p>}
        {success && <p className="message success">{success}</p>}

        <div className="module-toolbar">
          <select value={filterProjectId} onChange={(e) => handleProjectChange(e.target.value)}>
            <option value="">Todos os projetos</option>
            {projectsComRealizado.map((p) => (
              <option key={p.id_projeto} value={p.id_projeto}>#{p.id_projeto} - {p.designacao}</option>
            ))}
          </select>
          <select value={selectedOrcId} onChange={(e) => handleSelectOrc(e.target.value)} disabled={loadingOrcamentos}>
            <option value="">{loadingOrcamentos ? 'A carregar orçamentos...' : 'Selecionar orçamento'}</option>
            {filteredOrcs.map((o) => (
              <option key={o.id_orcamento} value={o.id_orcamento}>
                #{o.id_orcamento} - {formatVersionLabel(o.versao)} ({formatStatusLabel(o.estado)})
              </option>
            ))}
          </select>
        </div>

        {resumo && (
          <div className="compare-grid realizado-summary-grid">
            <div><p>Real Materiais</p><strong>{formatMoney(resumo.custo_total_real_materiais)}</strong></div>
            <div><p>Real Operações</p><strong>{formatMoney(resumo.custo_total_real_operacoes)}</strong></div>
            <div><p>Real Serviços</p><strong>{formatMoney(resumo.custo_total_real_servicos)}</strong></div>
            <div><p>Total real</p><strong>{formatMoney(resumo.custo_total_real)}</strong></div>
          </div>
        )}

        {selectedOrcId && (
          <>
            <div className="tab-bar">
              {['materiais', 'operacoes', 'servicos'].map((t) => (
                <button
                  key={t}
                  type="button"
                  className={`tab-btn ${activeTab === t ? 'active' : ''}`}
                  onClick={() => setActiveTab(t)}
                >
                  {TAB_LABELS[t] || t}
                </button>
              ))}
            </div>

            {loading && <p className="muted-text">A carregar...</p>}

            {activeTab === 'materiais' && (
              <div>
                {linhasMateriais.map((linha) => {
                  const realizados = realizadosByLinhaMat[linha.id_linha_material] || []
                  const f = addMatForms[linha.id_linha_material] || { quantidade: '', peso_kg: '', custo_unitario_real: '', observacoes: '' }
                  return (
                    <div key={linha.id_linha_material} className="realizado-linha">
                      <div className="realizado-linha-head">
                        <strong>{describeMaterial(linha.id_material)}</strong>
                        <span>Linha #{linha.id_linha_material} | Orçado: {linha.quantidade} un | {formatMoney(linha.custo_total)}</span>
                      </div>
                      <div className="add-line-form">
                        <input
                          type="number" step="0.001" placeholder="Qtd real"
                          value={f.quantidade}
                          onChange={(e) => setAddMatForms((p) => ({ ...p, [linha.id_linha_material]: { ...f, quantidade: e.target.value } }))}
                        />
                        <input
                          type="number" step="0.01" placeholder="Peso real (kg)"
                          value={f.peso_kg ?? ''}
                          onChange={(e) => setAddMatForms((p) => ({ ...p, [linha.id_linha_material]: { ...f, peso_kg: e.target.value } }))}
                        />
                        <input
                          type="number" step="0.0001" placeholder="Custo unit. real (opcional)"
                          value={f.custo_unitario_real}
                          onChange={(e) => setAddMatForms((p) => ({ ...p, [linha.id_linha_material]: { ...f, custo_unitario_real: e.target.value } }))}
                        />
                        <input
                          placeholder="Obs."
                          value={f.observacoes}
                          onChange={(e) => setAddMatForms((p) => ({ ...p, [linha.id_linha_material]: { ...f, observacoes: e.target.value } }))}
                        />
                        <button type="button" onClick={() => handleAddRealizadoMat(linha.id_linha_material)}>Registar</button>
                      </div>
                      {realizados.length > 0 && (
                        <div className="table-scroll">
                          <table>
                            <thead>
                              <tr><th>Data</th><th>Qtd</th><th>Peso (kg)</th><th>Custo unit.</th><th>Total real</th><th>Obs.</th><th></th></tr>
                            </thead>
                            <tbody>
                              {realizados.map((r) => (
                                <tr key={r.id_realizado_material}>
                                  <td>{formatDate(r.data_registo)}</td>
                                  <td>{r.quantidade}</td>
                                  <td>{r.peso_kg ?? '-'}</td>
                                  <td>{formatMoney(r.custo_unitario_real)}</td>
                                  <td>{formatMoney(r.custo_total_real)}</td>
                                  <td>{r.observacoes || '-'}</td>
                                  <td><button type="button" className="btn-xs btn-danger" onClick={() => handleDeleteRealizadoMat(r.id_realizado_material)}>X</button></td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )
                })}
                {linhasMateriais.length === 0 && !loading && (
                  <p className="realizado-empty">Sem linhas de material neste orçamento.</p>
                )}
              </div>
            )}

            {activeTab === 'operacoes' && (
              <div>
                {linhasOperacoes.map((linha) => {
                  const realizados = realizadosByLinhaOp[linha.id_linha_operacao] || []
                  const f = addOpForms[linha.id_linha_operacao] || { horas: '', custo_hora_real: '', observacoes: '' }
                  return (
                    <div key={linha.id_linha_operacao} className="realizado-linha">
                      <div className="realizado-linha-head">
                        <strong>{describeOperacao(linha.id_operacao)}</strong>
                        <span>Linha #{linha.id_linha_operacao} | Orçado: {linha.horas}h | {formatMoney(linha.custo_total)}</span>
                      </div>
                      <div className="add-line-form">
                        <input
                          type="number" step="0.01" placeholder="Horas reais"
                          value={f.horas}
                          onChange={(e) => setAddOpForms((p) => ({ ...p, [linha.id_linha_operacao]: { ...f, horas: e.target.value } }))}
                        />
                        <input
                          type="number" step="0.01" placeholder="Custo/hora real (opcional)"
                          value={f.custo_hora_real}
                          onChange={(e) => setAddOpForms((p) => ({ ...p, [linha.id_linha_operacao]: { ...f, custo_hora_real: e.target.value } }))}
                        />
                        <input
                          placeholder="Obs."
                          value={f.observacoes}
                          onChange={(e) => setAddOpForms((p) => ({ ...p, [linha.id_linha_operacao]: { ...f, observacoes: e.target.value } }))}
                        />
                        <button type="button" onClick={() => handleAddRealizadoOp(linha.id_linha_operacao)}>Registar</button>
                      </div>
                      {realizados.length > 0 && (
                        <div className="table-scroll">
                          <table>
                            <thead>
                              <tr><th>Data</th><th>Horas</th><th>Custo/h</th><th>Total real</th><th>Obs.</th><th></th></tr>
                            </thead>
                            <tbody>
                              {realizados.map((r) => (
                                <tr key={r.id_realizado_operacao}>
                                  <td>{formatDate(r.data_registo)}</td>
                                  <td>{r.horas}</td>
                                  <td>{formatMoney(r.custo_hora_real)}</td>
                                  <td>{formatMoney(r.custo_total_real)}</td>
                                  <td>{r.observacoes || '-'}</td>
                                  <td><button type="button" className="btn-xs btn-danger" onClick={() => handleDeleteRealizadoOp(r.id_realizado_operacao)}>X</button></td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )
                })}
                {linhasOperacoes.length === 0 && !loading && (
                  <p className="realizado-empty">Sem linhas de operação neste orçamento.</p>
                )}
              </div>
            )}

            {activeTab === 'servicos' && (
              <div>
                {linhasServicos.map((linha) => {
                  const realizados = realizadosByLinhaSvc[linha.id_linha_servico] || []
                  const f = addSvcForms[linha.id_linha_servico] || { quantidade: '', preco_unitario_real: '', observacoes: '' }
                  return (
                    <div key={linha.id_linha_servico} className="realizado-linha">
                      <div className="realizado-linha-head">
                        <strong>{describeServico(linha.id_servico)}</strong>
                        <span>Linha #{linha.id_linha_servico} | Orçado: {linha.quantidade} un | {formatMoney(linha.custo_total)}</span>
                      </div>
                      <div className="add-line-form">
                        <input
                          type="number" step="0.001" placeholder="Qtd real"
                          value={f.quantidade}
                          onChange={(e) => setAddSvcForms((p) => ({ ...p, [linha.id_linha_servico]: { ...f, quantidade: e.target.value } }))}
                        />
                        <input
                          type="number" step="0.0001" placeholder="Preço unit. real (opcional)"
                          value={f.preco_unitario_real}
                          onChange={(e) => setAddSvcForms((p) => ({ ...p, [linha.id_linha_servico]: { ...f, preco_unitario_real: e.target.value } }))}
                        />
                        <input
                          placeholder="Obs."
                          value={f.observacoes}
                          onChange={(e) => setAddSvcForms((p) => ({ ...p, [linha.id_linha_servico]: { ...f, observacoes: e.target.value } }))}
                        />
                        <button type="button" onClick={() => handleAddRealizadoSvc(linha.id_linha_servico)}>Registar</button>
                      </div>
                      {realizados.length > 0 && (
                        <div className="table-scroll">
                          <table>
                            <thead>
                              <tr><th>Data</th><th>Qtd</th><th>Preço unit.</th><th>Total real</th><th>Obs.</th><th></th></tr>
                            </thead>
                            <tbody>
                              {realizados.map((r) => (
                                <tr key={r.id_realizado_servico}>
                                  <td>{formatDate(r.data_registo)}</td>
                                  <td>{r.quantidade}</td>
                                  <td>{formatMoney(r.preco_unitario_real)}</td>
                                  <td>{formatMoney(r.custo_total_real)}</td>
                                  <td>{r.observacoes || '-'}</td>
                                  <td><button type="button" className="btn-xs btn-danger" onClick={() => handleDeleteRealizadoSvc(r.id_realizado_servico)}>X</button></td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )
                })}
                {linhasServicos.length === 0 && !loading && (
                  <p className="realizado-empty">Sem linhas de serviço neste orçamento.</p>
                )}
              </div>
            )}
          </>
        )}

        {!selectedOrcId && (
          <p className="realizado-select-hint">Selecione um orçamento para registar custos reais.</p>
        )}
      </div>
    </div>
  )
}
