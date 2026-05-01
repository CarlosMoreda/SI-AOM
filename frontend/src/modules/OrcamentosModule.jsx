import { useCallback, useEffect, useState } from 'react'

import { formatDate, formatMoney } from '../utils/formatters'
import { listProjects } from '../services/projectService'
import {
  createOrcamento,
  deleteOrcamento,
  listOrcamentos,
  updateOrcamento,
  listOrcamentoMateriais,
  addOrcamentoMaterial,
  deleteOrcamentoMaterial,
  listOrcamentoOperacoes,
  addOrcamentoOperacao,
  deleteOrcamentoOperacao,
  listOrcamentoServicos,
  addOrcamentoServico,
  deleteOrcamentoServico,
} from '../services/orcamentoService'
import { listMateriais } from '../services/materialService'
import { listOperacoes } from '../services/operacaoService'
import { listServicos } from '../services/servicoService'
import OrcamentoDetailsPanel from './orcamentos/OrcamentoDetailsPanel'
import OrcamentoDraftLines from './orcamentos/OrcamentoDraftLines'

const ESTADOS_ORC = ['rascunho', 'em_revisao', 'aprovado', 'rejeitado']

const EMPTY_ORC_FORM = {
  id_projeto: '',
  versao: '',
  estado: 'rascunho',
  margem_percentual: '',
  observacoes: '',
}

const EMPTY_DRAFT_MAT_FORM = {
  id_material: '',
  quantidade: '',
  desperdicio_percent: '0',
  observacoes: '',
}

const EMPTY_DRAFT_OP_FORM = {
  id_operacao: '',
  horas: '',
  tempo_setup_h: '0',
  observacoes: '',
}

const EMPTY_DRAFT_SVC_FORM = {
  id_servico: '',
  quantidade: '',
  observacoes: '',
}

export default function OrcamentosModule({ token }) {
  const [projects, setProjects] = useState([])
  const [orcamentos, setOrcamentos] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [filterProjectId, setFilterProjectId] = useState('')
  const [showOrcForm, setShowOrcForm] = useState(false)
  const [editingOrcId, setEditingOrcId] = useState(null)
  const [orcForm, setOrcForm] = useState(EMPTY_ORC_FORM)
  const [saving, setSaving] = useState(false)
  const [autoOpenAfterCreate, setAutoOpenAfterCreate] = useState(false)
  const [createWithLines, setCreateWithLines] = useState(false)

  // Draft lines for "create everything" flow
  const [draftMateriais, setDraftMateriais] = useState([])
  const [draftOperacoes, setDraftOperacoes] = useState([])
  const [draftServicos, setDraftServicos] = useState([])
  const [draftMatForm, setDraftMatForm] = useState(EMPTY_DRAFT_MAT_FORM)
  const [draftOpForm, setDraftOpForm] = useState(EMPTY_DRAFT_OP_FORM)
  const [draftSvcForm, setDraftSvcForm] = useState(EMPTY_DRAFT_SVC_FORM)

  // Details panel
  const [selectedOrc, setSelectedOrc] = useState(null)
  const [activeTab, setActiveTab] = useState('materiais')

  // Catalog data for dropdowns
  const [catalogMateriais, setCatalogMateriais] = useState([])
  const [catalogOperacoes, setCatalogOperacoes] = useState([])
  const [catalogServicos, setCatalogServicos] = useState([])

  // Line items
  const [linhasMateriais, setLinhasMateriais] = useState([])
  const [linhasOperacoes, setLinhasOperacoes] = useState([])
  const [linhasServicos, setLinhasServicos] = useState([])
  const [loadingLinhas, setLoadingLinhas] = useState(false)

  // Add-line forms
  const [addMatForm, setAddMatForm] = useState({ id_material: '', quantidade: '', desperdicio_percent: '0', observacoes: '' })
  const [addOpForm, setAddOpForm] = useState({ id_operacao: '', horas: '', tempo_setup_h: '0', observacoes: '' })
  const [addSvcForm, setAddSvcForm] = useState({ id_servico: '', quantidade: '', observacoes: '' })

  const loadCatalogs = useCallback(async () => {
    if (!token) return
    try {
      const [mats, ops, svcs] = await Promise.all([
        listMateriais(token),
        listOperacoes(token),
        listServicos(token),
      ])
      setCatalogMateriais(mats)
      setCatalogOperacoes(ops)
      setCatalogServicos(svcs)
    } catch (e) {
      setError(e.message || 'Nao foi possivel carregar catalogos')
    }
  }, [token])

  const load = useCallback(async () => {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      const [projs, orcs] = await Promise.all([listProjects(token), listOrcamentos(token)])
      setProjects(projs)
      setOrcamentos(orcs)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    load()
    loadCatalogs()
  }, [load, loadCatalogs])

  const loadLinhas = useCallback(async (orc) => {
    if (!orc || !token) return
    setLoadingLinhas(true)
    try {
      const [mats, ops, svcs] = await Promise.all([
        listOrcamentoMateriais(token, orc.id_orcamento),
        listOrcamentoOperacoes(token, orc.id_orcamento),
        listOrcamentoServicos(token, orc.id_orcamento),
      ])
      setLinhasMateriais(mats)
      setLinhasOperacoes(ops)
      setLinhasServicos(svcs)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoadingLinhas(false)
    }
  }, [token])

  const getProjectOrcamentos = useCallback(
    (projectId) => orcamentos.filter((o) => Number(o.id_projeto) === Number(projectId)),
    [orcamentos],
  )

  const getNextVersionForProject = useCallback(
    (projectId) => {
      const existing = getProjectOrcamentos(projectId)
      const existingVersions = new Set(existing.map((o) => String(o.versao || '').trim().toLowerCase()))

      const numericVersions = existing
        .map((o) => {
          const m = String(o.versao || '').trim().match(/^v?(\d+)$/i)
          return m ? Number(m[1]) : null
        })
        .filter((v) => Number.isFinite(v))

      const initialNumber = numericVersions.length > 0
        ? Math.max(...numericVersions) + 1
        : existing.length + 1

      let candidateNumber = Math.max(1, initialNumber)
      let candidate = `v${candidateNumber}`
      while (existingVersions.has(candidate.toLowerCase())) {
        candidateNumber += 1
        candidate = `v${candidateNumber}`
      }

      return candidate
    },
    [getProjectOrcamentos],
  )

  const buildCreateForm = useCallback(
    (projectIdCandidate) => {
      const fallbackProjectId = projects[0] ? String(projects[0].id_projeto) : ''
      const idProjeto = projectIdCandidate || fallbackProjectId

      return {
        ...EMPTY_ORC_FORM,
        id_projeto: idProjeto,
        versao: idProjeto ? getNextVersionForProject(Number(idProjeto)) : '',
      }
    },
    [getNextVersionForProject, projects],
  )

  const resetDraftLines = useCallback(() => {
    setDraftMateriais([])
    setDraftOperacoes([])
    setDraftServicos([])
    setDraftMatForm(EMPTY_DRAFT_MAT_FORM)
    setDraftOpForm(EMPTY_DRAFT_OP_FORM)
    setDraftSvcForm(EMPTY_DRAFT_SVC_FORM)
  }, [])

  const countDraftLines = draftMateriais.length + draftOperacoes.length + draftServicos.length

  function selectOrcamento(orc) {
    setSelectedOrc(orc)
    setActiveTab('materiais')
    loadLinhas(orc)
  }

  function openCreate() {
    setEditingOrcId(null)
    setAutoOpenAfterCreate(false)
    setCreateWithLines(false)
    resetDraftLines()
    setOrcForm(buildCreateForm(filterProjectId))
    setShowOrcForm(true)
    setSuccess('')
    setError('')
  }

  function openCreateFromScratch() {
    setEditingOrcId(null)
    setAutoOpenAfterCreate(true)
    setCreateWithLines(true)
    resetDraftLines()
    setOrcForm(buildCreateForm(filterProjectId))
    setShowOrcForm(true)
    setSuccess('')
    setError('')
  }

  function openEdit(orc, e) {
    e.stopPropagation()
    setEditingOrcId(orc.id_orcamento)
    setAutoOpenAfterCreate(false)
    setCreateWithLines(false)
    resetDraftLines()
    setOrcForm({
      id_projeto: String(orc.id_projeto),
      versao: orc.versao ?? '',
      estado: orc.estado ?? 'rascunho',
      margem_percentual: orc.margem_percentual ?? '',
      observacoes: orc.observacoes ?? '',
    })
    setShowOrcForm(true)
    setSuccess('')
    setError('')
  }

  function cancelForm() {
    setShowOrcForm(false)
    setEditingOrcId(null)
    setAutoOpenAfterCreate(false)
    setCreateWithLines(false)
    resetDraftLines()
    setOrcForm(EMPTY_ORC_FORM)
  }

  function toggleCreateWithLines(checked) {
    setCreateWithLines(checked)
    if (!checked) {
      resetDraftLines()
    }
  }

  function handleAddDraftMaterial() {

    const idMaterial = Number(draftMatForm.id_material)
    const quantidade = Number(draftMatForm.quantidade)
    const desperdicioPercent = Number(draftMatForm.desperdicio_percent || 0)

    if (!idMaterial || !Number.isFinite(quantidade) || quantidade <= 0) {
      setError('Preencha material e quantidade validos.')
      return
    }

    const material = catalogMateriais.find((m) => Number(m.id_material) === idMaterial)
    setDraftMateriais((prev) => [
      ...prev,
      {
        id_material: idMaterial,
        quantidade,
        desperdicio_percent: Number.isFinite(desperdicioPercent) ? desperdicioPercent : 0,
        observacoes: draftMatForm.observacoes || null,
        label: material ? `${material.codigo} - ${material.nome}` : String(idMaterial),
      },
    ])
    setDraftMatForm(EMPTY_DRAFT_MAT_FORM)
    setError('')
  }

  function handleAddDraftOperacao() {

    const idOperacao = Number(draftOpForm.id_operacao)
    const horas = Number(draftOpForm.horas)
    const tempoSetup = Number(draftOpForm.tempo_setup_h || 0)

    if (!idOperacao || !Number.isFinite(horas) || horas <= 0) {
      setError('Preencha operacao e horas validas.')
      return
    }

    const operacao = catalogOperacoes.find((o) => Number(o.id_operacao) === idOperacao)
    setDraftOperacoes((prev) => [
      ...prev,
      {
        id_operacao: idOperacao,
        horas,
        tempo_setup_h: Number.isFinite(tempoSetup) ? tempoSetup : 0,
        observacoes: draftOpForm.observacoes || null,
        label: operacao ? `${operacao.codigo} - ${operacao.nome}` : String(idOperacao),
      },
    ])
    setDraftOpForm(EMPTY_DRAFT_OP_FORM)
    setError('')
  }

  function handleAddDraftServico() {

    const idServico = Number(draftSvcForm.id_servico)
    const quantidade = Number(draftSvcForm.quantidade)

    if (!idServico || !Number.isFinite(quantidade) || quantidade <= 0) {
      setError('Preencha servico e quantidade validos.')
      return
    }

    const servico = catalogServicos.find((s) => Number(s.id_servico) === idServico)
    setDraftServicos((prev) => [
      ...prev,
      {
        id_servico: idServico,
        quantidade,
        observacoes: draftSvcForm.observacoes || null,
        label: servico ? `${servico.codigo} - ${servico.nome}` : String(idServico),
      },
    ])
    setDraftSvcForm(EMPTY_DRAFT_SVC_FORM)
    setError('')
  }

  function removeDraftMaterial(index) {
    setDraftMateriais((prev) => prev.filter((_, i) => i !== index))
  }

  function removeDraftOperacao(index) {
    setDraftOperacoes((prev) => prev.filter((_, i) => i !== index))
  }

  function removeDraftServico(index) {
    setDraftServicos((prev) => prev.filter((_, i) => i !== index))
  }

  async function createDraftLinesForOrcamento(idOrcamento) {
    for (const linha of draftMateriais) {
      await addOrcamentoMaterial(token, idOrcamento, {
        id_material: linha.id_material,
        quantidade: linha.quantidade,
        desperdicio_percent: linha.desperdicio_percent,
        observacoes: linha.observacoes,
      })
    }

    for (const linha of draftOperacoes) {
      await addOrcamentoOperacao(token, idOrcamento, {
        id_operacao: linha.id_operacao,
        horas: linha.horas,
        tempo_setup_h: linha.tempo_setup_h,
        observacoes: linha.observacoes,
      })
    }

    for (const linha of draftServicos) {
      await addOrcamentoServico(token, idOrcamento, {
        id_servico: linha.id_servico,
        quantidade: linha.quantidade,
        observacoes: linha.observacoes,
      })
    }
  }

  function handleOrcProjectChange(projectId) {
    if (editingOrcId) {
      setOrcForm((f) => ({ ...f, id_projeto: projectId }))
      return
    }

    setOrcForm((f) => ({
      ...f,
      id_projeto: projectId,
      versao: projectId ? getNextVersionForProject(Number(projectId)) : '',
    }))
  }

  async function handleSubmitOrc(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')

    const isCreate = !editingOrcId
    const shouldAutoOpen = isCreate && autoOpenAfterCreate
    const shouldCreateWithLines = isCreate && createWithLines
    const resolvedVersao =
      String(orcForm.versao || '').trim() ||
      (orcForm.id_projeto ? getNextVersionForProject(Number(orcForm.id_projeto)) : '')

    if (!orcForm.id_projeto) {
      setError('Projeto obrigatorio.')
      setSaving(false)
      return
    }

    if (!resolvedVersao) {
      setError('Versao obrigatoria para criar o orcamento.')
      setSaving(false)
      return
    }

    if (shouldCreateWithLines && countDraftLines === 0) {
      setError('No modo completo, adicione pelo menos uma linha de detalhe antes de criar.')
      setSaving(false)
      return
    }

    const payload = {
      id_projeto: Number(orcForm.id_projeto),
      versao: resolvedVersao,
      estado: orcForm.estado,
      margem_percentual: orcForm.margem_percentual !== '' ? Number(orcForm.margem_percentual) : null,
      observacoes: orcForm.observacoes || null,
    }

    let created = null
    try {
      if (editingOrcId) {
        await updateOrcamento(token, editingOrcId, payload)
        setSuccess('Orcamento atualizado.')
      } else {
        created = await createOrcamento(token, payload)

        if (shouldCreateWithLines && countDraftLines > 0) {
          await createDraftLinesForOrcamento(created.id_orcamento)
        }

        setSuccess(
          shouldCreateWithLines
            ? `Orcamento completo criado com ${countDraftLines} linhas.`
            : shouldAutoOpen
              ? 'Orcamento criado do zero. Adicione agora as linhas de detalhe.'
              : 'Orcamento criado.',
        )
      }
      cancelForm()
      await load()

      if (created && (shouldAutoOpen || shouldCreateWithLines)) {
        setFilterProjectId(String(created.id_projeto))
        selectOrcamento(created)
      }
    } catch (e) {
      if (isCreate && created) {
        setFilterProjectId(String(created.id_projeto))
        selectOrcamento(created)
        setShowOrcForm(false)
        setError(`Orcamento #${created.id_orcamento} criado, mas falhou ao inserir todas as linhas: ${e.message}`)
      } else if (isCreate) {
        setError(`Falha ao criar orcamento completo: ${e.message}`)
      } else {
        setError(e.message)
      }
    } finally {
      setSaving(false)
    }
  }

  async function handleDeleteOrc(orc, e) {
    e.stopPropagation()
    if (!window.confirm(`Eliminar orcamento #${orc.id_orcamento} v${orc.versao}?`)) return
    setError('')
    setSuccess('')
    try {
      await deleteOrcamento(token, orc.id_orcamento)
      if (selectedOrc?.id_orcamento === orc.id_orcamento) setSelectedOrc(null)
      setSuccess('Orcamento eliminado.')
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  // Add line items
  async function handleAddMaterial(e) {
    e.preventDefault()
    if (!selectedOrc) return
    try {
      await addOrcamentoMaterial(token, selectedOrc.id_orcamento, {
        id_material: Number(addMatForm.id_material),
        quantidade: Number(addMatForm.quantidade),
        desperdicio_percent: Number(addMatForm.desperdicio_percent || 0),
        observacoes: addMatForm.observacoes || null,
      })
      setAddMatForm({ id_material: '', quantidade: '', desperdicio_percent: '0', observacoes: '' })
      await loadLinhas(selectedOrc)
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleDeleteMaterial(idLinha) {
    if (!window.confirm('Remover linha de material?')) return
    try {
      await deleteOrcamentoMaterial(token, idLinha)
      await loadLinhas(selectedOrc)
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleAddOperacao(e) {
    e.preventDefault()
    if (!selectedOrc) return
    try {
      await addOrcamentoOperacao(token, selectedOrc.id_orcamento, {
        id_operacao: Number(addOpForm.id_operacao),
        horas: Number(addOpForm.horas),
        tempo_setup_h: Number(addOpForm.tempo_setup_h || 0),
        observacoes: addOpForm.observacoes || null,
      })
      setAddOpForm({ id_operacao: '', horas: '', tempo_setup_h: '0', observacoes: '' })
      await loadLinhas(selectedOrc)
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleDeleteOperacao(idLinha) {
    if (!window.confirm('Remover linha de operacao?')) return
    try {
      await deleteOrcamentoOperacao(token, idLinha)
      await loadLinhas(selectedOrc)
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleAddServico(e) {
    e.preventDefault()
    if (!selectedOrc) return
    try {
      await addOrcamentoServico(token, selectedOrc.id_orcamento, {
        id_servico: Number(addSvcForm.id_servico),
        quantidade: Number(addSvcForm.quantidade),
        observacoes: addSvcForm.observacoes || null,
      })
      setAddSvcForm({ id_servico: '', quantidade: '', observacoes: '' })
      await loadLinhas(selectedOrc)
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleDeleteServico(idLinha) {
    if (!window.confirm('Remover linha de servico?')) return
    try {
      await deleteOrcamentoServico(token, idLinha)
      await loadLinhas(selectedOrc)
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  const filteredOrcs = orcamentos.filter(
    (o) => !filterProjectId || String(o.id_projeto) === filterProjectId,
  )

  return (
    <div className="module-layout">
      <div className="panel">
        <div className="panel-head">
          <h3>Orcamentos</h3>
          <span>{loading ? 'A carregar...' : `${orcamentos.length} registos`}</span>
        </div>

        {error && <p className="message error">{error}</p>}
        {success && <p className="message success">{success}</p>}

        <div className="module-toolbar">
          <select value={filterProjectId} onChange={(e) => setFilterProjectId(e.target.value)}>
            <option value="">Todos os projetos</option>
            {projects.map((p) => (
              <option key={p.id_projeto} value={p.id_projeto}>
                #{p.id_projeto} - {p.designacao}
              </option>
            ))}
          </select>
          <div className="module-inline-actions">
            <button type="button" onClick={openCreate}>
              + Novo orcamento
            </button>
            <button type="button" className="btn-secondary" onClick={openCreateFromScratch}>
              + Novo do zero
            </button>
          </div>
        </div>

        {showOrcForm && (
          <form className="inline-form" onSubmit={handleSubmitOrc}>
            {!editingOrcId && autoOpenAfterCreate && !createWithLines && (
              <p className="message form-message">
                Fluxo do zero ativo: apos criar, o orcamento abre automaticamente para adicionar linhas.
              </p>
            )}

            {!editingOrcId && createWithLines && (
              <p className="message form-message">
                Fluxo completo ativo: o sistema cria o orcamento e todas as linhas em um unico passo.
              </p>
            )}

            <div className="form-row">
              <label>
                Projeto *
                <select value={orcForm.id_projeto} onChange={(e) => handleOrcProjectChange(e.target.value)} required>
                  <option value="">Selecionar projeto</option>
                  {projects.map((p) => (
                    <option key={p.id_projeto} value={p.id_projeto}>#{p.id_projeto} - {p.designacao}</option>
                  ))}
                </select>
              </label>
              <label>
                {editingOrcId ? 'Versao *' : 'Versao (opcional)'}
                <input
                  value={orcForm.versao}
                  onChange={(e) => setOrcForm((f) => ({ ...f, versao: e.target.value }))}
                  placeholder={
                    !editingOrcId && orcForm.id_projeto
                      ? `Sugestao: ${getNextVersionForProject(Number(orcForm.id_projeto))}`
                      : ''
                  }
                  required={Boolean(editingOrcId)}
                />
              </label>
              <label>
                Estado
                <select value={orcForm.estado} onChange={(e) => setOrcForm((f) => ({ ...f, estado: e.target.value }))}>
                  {ESTADOS_ORC.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </label>
              <label>
                Margem %
                <input type="number" step="0.01" value={orcForm.margem_percentual} onChange={(e) => setOrcForm((f) => ({ ...f, margem_percentual: e.target.value }))} />
              </label>
            </div>

            {!editingOrcId && (
              <div className="form-inline-options">
                <label>
                  <input
                    type="checkbox"
                    checked={autoOpenAfterCreate}
                    onChange={(e) => setAutoOpenAfterCreate(e.target.checked)}
                    disabled={createWithLines}
                  />
                  Abrir detalhes apos criar para lancar linhas de detalhe
                </label>

                <label>
                  <input
                    type="checkbox"
                    checked={createWithLines}
                    onChange={(e) => toggleCreateWithLines(e.target.checked)}
                  />
                  Criar tudo agora (materiais, operacoes e servicos)
                </label>
              </div>
            )}

            {!editingOrcId && createWithLines && (
              <OrcamentoDraftLines
                countDraftLines={countDraftLines}
                draftMatForm={draftMatForm}
                setDraftMatForm={setDraftMatForm}
                catalogMateriais={catalogMateriais}
                onAddDraftMaterial={handleAddDraftMaterial}
                draftMateriais={draftMateriais}
                onRemoveDraftMaterial={removeDraftMaterial}
                draftOpForm={draftOpForm}
                setDraftOpForm={setDraftOpForm}
                catalogOperacoes={catalogOperacoes}
                onAddDraftOperacao={handleAddDraftOperacao}
                draftOperacoes={draftOperacoes}
                onRemoveDraftOperacao={removeDraftOperacao}
                draftSvcForm={draftSvcForm}
                setDraftSvcForm={setDraftSvcForm}
                catalogServicos={catalogServicos}
                onAddDraftServico={handleAddDraftServico}
                draftServicos={draftServicos}
                onRemoveDraftServico={removeDraftServico}
              />
            )}

            <label>
              Observacoes
              <input value={orcForm.observacoes} onChange={(e) => setOrcForm((f) => ({ ...f, observacoes: e.target.value }))} />
            </label>
            <div className="form-actions">
              <button type="submit" disabled={saving}>{saving ? 'A gravar...' : editingOrcId ? 'Guardar' : 'Criar'}</button>
              <button type="button" className="btn-secondary" onClick={cancelForm}>Cancelar</button>
            </div>
          </form>
        )}

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Projeto</th>
                <th>Versao</th>
                <th>Estado</th>
                <th>Margem%</th>
                <th>Custo Total</th>
                <th>Preco Venda</th>
                <th>Criado</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrcs.map((o) => (
                <tr
                  key={o.id_orcamento}
                  className={selectedOrc?.id_orcamento === o.id_orcamento ? 'row-selected' : 'row-clickable'}
                  onClick={() => selectOrcamento(o)}
                >
                  <td>{o.id_orcamento}</td>
                  <td>#{o.id_projeto}</td>
                  <td>{o.versao}</td>
                  <td><span className={`badge badge-${o.estado}`}>{o.estado}</span></td>
                  <td>{o.margem_percentual != null ? `${o.margem_percentual}%` : '-'}</td>
                  <td>{formatMoney(o.custo_total_orcado)}</td>
                  <td>{formatMoney(o.preco_venda)}</td>
                  <td>{formatDate(o.data_criacao)}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <div className="row-actions">
                      <button type="button" className="btn-xs" onClick={(e) => openEdit(o, e)}>Editar</button>
                      <button type="button" className="btn-xs btn-danger" onClick={(e) => handleDeleteOrc(o, e)}>Eliminar</button>
                    </div>
                  </td>
                </tr>
              ))}
              {filteredOrcs.length === 0 && (
                <tr><td colSpan={9}>Sem orcamentos.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selectedOrc && (
        <OrcamentoDetailsPanel
          selectedOrc={selectedOrc}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          loadingLinhas={loadingLinhas}
          addMatForm={addMatForm}
          setAddMatForm={setAddMatForm}
          catalogMateriais={catalogMateriais}
          onAddMaterial={handleAddMaterial}
          linhasMateriais={linhasMateriais}
          onDeleteMaterial={handleDeleteMaterial}
          addOpForm={addOpForm}
          setAddOpForm={setAddOpForm}
          catalogOperacoes={catalogOperacoes}
          onAddOperacao={handleAddOperacao}
          linhasOperacoes={linhasOperacoes}
          onDeleteOperacao={handleDeleteOperacao}
          addSvcForm={addSvcForm}
          setAddSvcForm={setAddSvcForm}
          catalogServicos={catalogServicos}
          onAddServico={handleAddServico}
          linhasServicos={linhasServicos}
          onDeleteServico={handleDeleteServico}
        />
      )}

    </div>
  )
}
