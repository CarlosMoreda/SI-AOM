import { useCallback, useEffect, useState } from 'react'

import { formatDate, formatMoney, formatStatusLabel, formatVersionLabel } from '../utils/formatters'
import Pagination from '../components/Pagination'
import { listProjects, listProjectBudgets } from '../services/projectService'
import {
  createOrcamento,
  deleteOrcamento,
  downloadOrcamentoPdf,
  listOrcamentosPaged,
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

// Transições válidas do ciclo de vida do orçamento (relatório 3.5 / Figura 4).
// Espelha o mapa do backend: o dropdown de edição só mostra o estado atual
// e os estados seguintes permitidos.
const TRANSICOES_ORC = {
  em_preparacao: ['em_revisao'],
  em_revisao: ['em_preparacao', 'validado'],
  validado: ['enviado'],
  enviado: ['adjudicado', 'rejeitado'],
  adjudicado: ['em_execucao'],
  em_execucao: ['concluido'],
  concluido: ['arquivado'],
  rejeitado: ['em_preparacao', 'arquivado'],
  arquivado: [],
}

function estadosPermitidos(estadoAtual) {
  const atual = String(estadoAtual || 'em_preparacao')
  return [atual, ...(TRANSICOES_ORC[atual] || [])]
}

const EMPTY_ORC_FORM = {
  id_projeto: '',
  versao: '',
  estado: 'em_preparacao',
  margem_percentual: '',
  quantidade_unidades: '1',
  observacoes: '',
}

const EMPTY_DRAFT_MAT_FORM = {
  id_material: '',
  quantidade: '',
  peso_kg: '',
  area_m2: '',
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

const PAGE_SIZE = 30

export default function OrcamentosModule({ token }) {
  const [projects, setProjects] = useState([])
  const [orcamentos, setOrcamentos] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
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
  // Estado original (BD) do orcamento em edicao: ancora as transicoes validas.
  const [editingOrcEstado, setEditingOrcEstado] = useState('em_preparacao')

  // Draft lines for "create everything" flow
  const [draftMateriais, setDraftMateriais] = useState([])
  const [draftOperacoes, setDraftOperacoes] = useState([])
  const [draftServicos, setDraftServicos] = useState([])
  const [draftMatForm, setDraftMatForm] = useState(EMPTY_DRAFT_MAT_FORM)
  const [draftOpForm, setDraftOpForm] = useState(EMPTY_DRAFT_OP_FORM)
  const [draftSvcForm, setDraftSvcForm] = useState(EMPTY_DRAFT_SVC_FORM)

  // Details panel
  const [selectedOrc, setSelectedOrc] = useState(null)
  const [exportingPdf, setExportingPdf] = useState(false)
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
  const [addMatForm, setAddMatForm] = useState({ id_material: '', quantidade: '', peso_kg: '', area_m2: '', desperdicio_percent: '0', observacoes: '' })
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
      setError(e.message || 'Não foi possível carregar catálogos')
    }
  }, [token])

  // Projetos: lista completa (dropdowns de filtro e de criacao).
  const loadProjects = useCallback(async () => {
    if (!token) return
    try {
      setProjects(await listProjects(token))
    } catch (e) {
      setError(e.message)
    }
  }, [token])

  // Orcamentos: paginados server-side, com filtro opcional por projeto.
  const loadOrcamentos = useCallback(async (p, idProjeto) => {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      const res = await listOrcamentosPaged(token, {
        idProjeto,
        limit: PAGE_SIZE,
        offset: (p - 1) * PAGE_SIZE,
      })
      setOrcamentos(res.items)
      setTotal(res.total)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadProjects()
    loadCatalogs()
  }, [loadProjects, loadCatalogs])

  useEffect(() => {
    loadOrcamentos(page, filterProjectId)
  }, [page, filterProjectId, loadOrcamentos])

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

  // Calcula a proxima versao a partir da lista de orcamentos de UM projeto.
  function computeNextVersion(existing) {
    const existingVersions = new Set(
      existing.map((o) => String(o.versao || '').trim().toLowerCase()),
    )
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
  }

  // Vai buscar TODOS os orcamentos do projeto (independente da paginacao da
  // lista) para sugerir uma versao que nao colida com as existentes.
  const fetchSuggestedVersion = useCallback(async (projectId) => {
    if (!projectId) return ''
    try {
      const budgets = await listProjectBudgets(token, Number(projectId))
      return computeNextVersion(budgets)
    } catch {
      return 'v1'
    }
  }, [token])

  const buildCreateForm = useCallback(
    (projectIdCandidate) => {
      const fallbackProjectId = projects[0] ? String(projects[0].id_projeto) : ''
      const idProjeto = projectIdCandidate || fallbackProjectId

      return {
        ...EMPTY_ORC_FORM,
        id_projeto: idProjeto,
        versao: '',
      }
    },
    [projects],
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

  async function openCreate() {
    setEditingOrcId(null)
    setAutoOpenAfterCreate(false)
    setCreateWithLines(false)
    resetDraftLines()
    const baseForm = buildCreateForm(filterProjectId)
    setOrcForm(baseForm)
    setShowOrcForm(true)
    setSuccess('')
    setError('')
    if (baseForm.id_projeto) {
      const v = await fetchSuggestedVersion(baseForm.id_projeto)
      setOrcForm((f) => (
        String(f.id_projeto) === String(baseForm.id_projeto) && !f.versao
          ? { ...f, versao: v }
          : f
      ))
    }
  }

  function openEdit(orc, e) {
    e.stopPropagation()
    setEditingOrcId(orc.id_orcamento)
    setEditingOrcEstado(orc.estado ?? 'em_preparacao')
    setAutoOpenAfterCreate(false)
    setCreateWithLines(false)
    resetDraftLines()
    setOrcForm({
      id_projeto: String(orc.id_projeto),
      versao: orc.versao ?? '',
      estado: orc.estado ?? 'em_preparacao',
      margem_percentual: orc.margem_percentual ?? '',
      quantidade_unidades: String(orc.quantidade_unidades ?? 1),
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
    const pesoKg = draftMatForm.peso_kg !== '' ? Number(draftMatForm.peso_kg) : null
    const areaM2 = draftMatForm.area_m2 !== '' ? Number(draftMatForm.area_m2) : null

    if (!idMaterial || !Number.isFinite(quantidade) || quantidade <= 0) {
      setError('Preencha material e quantidade válidos.')
      return
    }

    const material = catalogMateriais.find((m) => Number(m.id_material) === idMaterial)
    setDraftMateriais((prev) => [
      ...prev,
      {
        id_material: idMaterial,
        quantidade,
        peso_kg: pesoKg !== null && Number.isFinite(pesoKg) ? pesoKg : null,
        area_m2: areaM2 !== null && Number.isFinite(areaM2) ? areaM2 : null,
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
      setError('Preencha operação e horas válidas.')
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
      setError('Preencha serviço e quantidade válidos.')
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
        peso_kg: linha.peso_kg,
        area_m2: linha.area_m2,
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

  async function handleOrcProjectChange(projectId) {
    if (editingOrcId) {
      setOrcForm((f) => ({ ...f, id_projeto: projectId }))
      return
    }

    setOrcForm((f) => ({ ...f, id_projeto: projectId, versao: '' }))
    if (projectId) {
      const v = await fetchSuggestedVersion(projectId)
      setOrcForm((f) => (
        String(f.id_projeto) === String(projectId) ? { ...f, versao: v } : f
      ))
    }
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
      (orcForm.id_projeto ? await fetchSuggestedVersion(orcForm.id_projeto) : '')

    if (!orcForm.id_projeto) {
      setError('Projeto obrigatório.')
      setSaving(false)
      return
    }

    if (!resolvedVersao) {
      setError('Versão obrigatória para criar o orçamento.')
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
      // Criacao comeca sempre em preparacao (ciclo de vida); na edicao o
      // estado vem do dropdown restrito as transicoes validas.
      estado: isCreate ? 'em_preparacao' : orcForm.estado,
      margem_percentual: orcForm.margem_percentual !== '' ? Number(orcForm.margem_percentual) : null,
      quantidade_unidades: orcForm.quantidade_unidades !== '' ? Number(orcForm.quantidade_unidades) : 1,
      observacoes: orcForm.observacoes || null,
    }

    let created = null
    try {
      if (editingOrcId) {
        await updateOrcamento(token, editingOrcId, payload)
        setSuccess('Orçamento atualizado.')
      } else {
        created = await createOrcamento(token, payload)

        if (shouldCreateWithLines && countDraftLines > 0) {
          await createDraftLinesForOrcamento(created.id_orcamento)
        }

        setSuccess(
          shouldCreateWithLines
            ? `Orçamento completo criado com ${countDraftLines} linhas.`
            : shouldAutoOpen
              ? 'Orçamento criado do zero. Adicione agora as linhas de detalhe.'
              : 'Orçamento criado.',
        )
      }
      cancelForm()
      await loadOrcamentos(page, filterProjectId)

      if (created && (shouldAutoOpen || shouldCreateWithLines)) {
        setFilterProjectId(String(created.id_projeto))
        selectOrcamento(created)
      }
    } catch (e) {
      if (isCreate && created) {
        setFilterProjectId(String(created.id_projeto))
        selectOrcamento(created)
        setShowOrcForm(false)
        setError(`Orçamento #${created.id_orcamento} criado, mas falhou ao inserir todas as linhas: ${e.message}`)
      } else if (isCreate) {
        setError(`Falha ao criar orçamento completo: ${e.message}`)
      } else {
        setError(e.message)
      }
    } finally {
      setSaving(false)
    }
  }

  async function handleDeleteOrc(orc, e) {
    e.stopPropagation()
    if (!window.confirm(`Eliminar orçamento #${orc.id_orcamento} ${formatVersionLabel(orc.versao)}?`)) return
    setError('')
    setSuccess('')
    try {
      await deleteOrcamento(token, orc.id_orcamento)
      if (selectedOrc?.id_orcamento === orc.id_orcamento) setSelectedOrc(null)
      setSuccess('Orçamento eliminado.')
      await loadOrcamentos(page, filterProjectId)
    } catch (e) {
      setError(e.message)
    }
  }

  // Add line items
  async function handleAddMaterial(e) {
    e.preventDefault()
    if (!selectedOrc) return
    setError('')
    setSuccess('')
    try {
      await addOrcamentoMaterial(token, selectedOrc.id_orcamento, {
        id_material: Number(addMatForm.id_material),
        quantidade: Number(addMatForm.quantidade),
        peso_kg: addMatForm.peso_kg !== '' ? Number(addMatForm.peso_kg) : null,
        area_m2: addMatForm.area_m2 !== '' ? Number(addMatForm.area_m2) : null,
        desperdicio_percent: Number(addMatForm.desperdicio_percent || 0),
        observacoes: addMatForm.observacoes || null,
      })
      setAddMatForm({ id_material: '', quantidade: '', peso_kg: '', area_m2: '', desperdicio_percent: '0', observacoes: '' })
      setSuccess('Linha de material adicionada.')
      await loadLinhas(selectedOrc)
      await loadOrcamentos(page, filterProjectId)
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleDeleteMaterial(idLinha) {
    if (!window.confirm('Remover esta linha de material do orçamento?')) return
    setError('')
    setSuccess('')
    try {
      await deleteOrcamentoMaterial(token, idLinha)
      setSuccess('Linha de material removida.')
      await loadLinhas(selectedOrc)
      await loadOrcamentos(page, filterProjectId)
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleAddOperacao(e) {
    e.preventDefault()
    if (!selectedOrc) return
    setError('')
    setSuccess('')
    try {
      await addOrcamentoOperacao(token, selectedOrc.id_orcamento, {
        id_operacao: Number(addOpForm.id_operacao),
        horas: Number(addOpForm.horas),
        tempo_setup_h: Number(addOpForm.tempo_setup_h || 0),
        observacoes: addOpForm.observacoes || null,
      })
      setAddOpForm({ id_operacao: '', horas: '', tempo_setup_h: '0', observacoes: '' })
      setSuccess('Linha de operação adicionada.')
      await loadLinhas(selectedOrc)
      await loadOrcamentos(page, filterProjectId)
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleDeleteOperacao(idLinha) {
    if (!window.confirm('Remover esta linha de operação do orçamento?')) return
    setError('')
    setSuccess('')
    try {
      await deleteOrcamentoOperacao(token, idLinha)
      setSuccess('Linha de operação removida.')
      await loadLinhas(selectedOrc)
      await loadOrcamentos(page, filterProjectId)
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleAddServico(e) {
    e.preventDefault()
    if (!selectedOrc) return
    setError('')
    setSuccess('')
    try {
      await addOrcamentoServico(token, selectedOrc.id_orcamento, {
        id_servico: Number(addSvcForm.id_servico),
        quantidade: Number(addSvcForm.quantidade),
        observacoes: addSvcForm.observacoes || null,
      })
      setAddSvcForm({ id_servico: '', quantidade: '', observacoes: '' })
      setSuccess('Linha de serviço adicionada.')
      await loadLinhas(selectedOrc)
      await loadOrcamentos(page, filterProjectId)
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleDeleteServico(idLinha) {
    if (!window.confirm('Remover esta linha de serviço do orçamento?')) return
    setError('')
    setSuccess('')
    try {
      await deleteOrcamentoServico(token, idLinha)
      setSuccess('Linha de serviço removida.')
      await loadLinhas(selectedOrc)
      await loadOrcamentos(page, filterProjectId)
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleExportPdf() {
    if (!selectedOrc) return
    setError('')
    setSuccess('')
    setExportingPdf(true)
    try {
      await downloadOrcamentoPdf(token, selectedOrc.id_orcamento, selectedOrc.versao)
      setSuccess('PDF gerado e descarregado.')
    } catch (e) {
      setError(e.message || 'Falha ao gerar PDF')
    } finally {
      setExportingPdf(false)
    }
  }

  // O filtro por projeto e a paginacao sao feitos server-side; `orcamentos`
  // ja vem filtrado e paginado.
  function handleFilterChange(value) {
    setFilterProjectId(value)
    setPage(1)
  }

  return (
    <div className="module-layout">
      <div className="panel">
        <div className="panel-head">
          <h3>Orçamentos</h3>
          <span>{loading ? 'A carregar...' : `${total} registos`}</span>
        </div>

        {error && <p className="message error">{error}</p>}
        {success && <p className="message success">{success}</p>}

        <div className="module-toolbar">
          <select value={filterProjectId} onChange={(e) => handleFilterChange(e.target.value)}>
            <option value="">Todos os projetos</option>
            {projects.map((p) => (
              <option key={p.id_projeto} value={p.id_projeto}>
                #{p.id_projeto} - {p.designacao}
              </option>
            ))}
          </select>
          <div className="module-inline-actions">
            <button type="button" onClick={openCreate}>
              + Novo orçamento
            </button>
          </div>
        </div>

        {showOrcForm && (
          <form className="inline-form" onSubmit={handleSubmitOrc}>
            {!editingOrcId && autoOpenAfterCreate && !createWithLines && (
              <p className="message form-message">
                Fluxo do zero ativo: após criar, o orçamento abre automaticamente para adicionar linhas.
              </p>
            )}

            {!editingOrcId && createWithLines && (
              <p className="message form-message">
                Fluxo completo ativo: o sistema cria o orçamento e todas as linhas num único passo.
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
                {editingOrcId ? 'Versão *' : 'Versão (opcional)'}
                <input
                  value={orcForm.versao}
                  onChange={(e) => setOrcForm((f) => ({ ...f, versao: e.target.value }))}
                  placeholder="ex.: v1, v2 (sugerida automaticamente)"
                  required={Boolean(editingOrcId)}
                />
              </label>
              <label>
                Estado
                {editingOrcId ? (
                  <select
                    value={orcForm.estado}
                    onChange={(e) => setOrcForm((f) => ({ ...f, estado: e.target.value }))}
                    title="Apenas transições válidas do ciclo de vida"
                  >
                    {estadosPermitidos(editingOrcEstado).map((s) => (
                      <option key={s} value={s}>{formatStatusLabel(s)}</option>
                    ))}
                  </select>
                ) : (
                  <input value={formatStatusLabel('em_preparacao')} disabled title="Um orçamento novo começa sempre em preparação" />
                )}
              </label>
              <label>
                Margem %
                <input type="number" step="0.01" value={orcForm.margem_percentual} onChange={(e) => setOrcForm((f) => ({ ...f, margem_percentual: e.target.value }))} />
              </label>
              <label>
                Nº de unidades
                <input
                  type="number"
                  step="1"
                  min="1"
                  value={orcForm.quantidade_unidades}
                  onChange={(e) => setOrcForm((f) => ({ ...f, quantidade_unidades: e.target.value }))}
                  title="Nº de estruturas iguais. As linhas são por unidade; os totais são multiplicados por este valor."
                />
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
                  Abrir detalhes após criar para lançar linhas de detalhe
                </label>

                <label>
                  <input
                    type="checkbox"
                    checked={createWithLines}
                    onChange={(e) => toggleCreateWithLines(e.target.checked)}
                  />
                  Criar tudo agora (materiais, operações e serviços)
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
              Observações
              <input value={orcForm.observacoes} onChange={(e) => setOrcForm((f) => ({ ...f, observacoes: e.target.value }))} />
            </label>
            <div className="form-actions">
              <button type="submit" disabled={saving}>{saving ? 'A gravar...' : editingOrcId ? 'Guardar' : 'Criar'}</button>
              <button type="button" className="btn-secondary" onClick={cancelForm}>Cancelar</button>
            </div>
          </form>
        )}

        <div className="table-scroll fit-table-wrap">
          <table className="fit-table orcamentos-fit">
            <thead>
              <tr>
                <th>ID</th>
                <th>Projeto</th>
                <th>Versão</th>
                <th>Uni.</th>
                <th>Estado</th>
                <th>Margem%</th>
                <th>Custo Total</th>
                <th>Preço Venda</th>
                <th>Criado</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {orcamentos.map((o) => (
                <tr
                  key={o.id_orcamento}
                  className={selectedOrc?.id_orcamento === o.id_orcamento ? 'row-selected' : 'row-clickable'}
                  onClick={() => selectOrcamento(o)}
                >
                  <td>{o.id_orcamento}</td>
                  <td>#{o.id_projeto}</td>
                  <td>{o.versao}</td>
                  <td>{o.quantidade_unidades ?? 1}</td>
                  <td><span className={`badge badge-${o.estado}`}>{formatStatusLabel(o.estado)}</span></td>
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
              {orcamentos.length === 0 && (
                <tr><td colSpan={10}>{loading ? 'A carregar...' : 'Sem orçamentos.'}</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <Pagination
          page={page}
          pageSize={PAGE_SIZE}
          total={total}
          loading={loading}
          onPageChange={setPage}
        />
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
          onExportPdf={handleExportPdf}
          exportingPdf={exportingPdf}
        />
      )}

    </div>
  )
}
