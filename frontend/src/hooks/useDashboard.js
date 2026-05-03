import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { normalizePerfil } from '../components/menuConfig'
import { listBudgets } from '../services/budgetService'
import { listMateriais } from '../services/materialService'
import { listOperacoes } from '../services/operacaoService'
import {
  listOrcamentoMateriais,
  listOrcamentoOperacoes,
  listOrcamentoServicos,
} from '../services/orcamentoService'
import {
  listProjectBudgets,
  listProjects,
} from '../services/projectService'
import { getRealizadoResumoBatch, normalizeOrcamentoIds } from '../services/realizadoService'
import { listServicos } from '../services/servicoService'

const EMPTY_PROJECT_ANALYSIS = {
  totalOrcado: 0,
  totalLinhas: 0,
  totalMateriais: 0,
  totalOperacoes: 0,
  totalServicos: 0,
  linhas: [],
}

const SOLDADURA_KEYWORDS = [
  'solda',
  'soldadura',
  'soldagem',
  'weld',
  'mig',
  'mag',
  'tig',
  'gmaw',
  'gtaw',
  'smaw',
  'eletrodo',
  'electrodo',
  'brasagem',
  'braz',
  'arco',
  'spot',
]
const PINGAMENTO_KEYWORDS = [
  'pingamento',
  'pinga',
  'ping',
  'pint',
  'pintura',
  'paint',
  'coating',
  'powder',
  'epoxi',
  'epoxy',
  'primer',
  'verniz',
  'zinc',
  'zincagem',
  'jato',
  'metaliz',
  'acabamento',
  'galvan',
  'lacag',
]

function toNumber(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function normalizeText(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

function includesAnyKeyword(text, keywords) {
  return keywords.some((keyword) => {
    if (keyword.length <= 4) {
      const expression = new RegExp(`\\b${keyword}\\b`)
      return expression.test(text)
    }
    return text.includes(keyword)
  })
}

function resolveOperacaoProcesso(operacao, linha) {
  const source = normalizeText([
    operacao?.codigo,
    operacao?.nome,
    operacao?.categoria,
    linha?.observacoes,
  ].join(' '))

  if (includesAnyKeyword(source, SOLDADURA_KEYWORDS)) {
    return 'soldadura'
  }

  if (includesAnyKeyword(source, PINGAMENTO_KEYWORDS)) {
    return 'pingamento'
  }

  return 'outro'
}

function buildProjectAnalysis(details, catalogs) {
  const materialById = new Map(catalogs.materiais.map((row) => [row.id_material, row]))
  const operacaoById = new Map(catalogs.operacoes.map((row) => [row.id_operacao, row]))
  const servicoById = new Map(catalogs.servicos.map((row) => [row.id_servico, row]))

  let totalOrcado = 0
  let totalMateriais = 0
  let totalOperacoes = 0
  let totalServicos = 0

  const linhas = []

  details.forEach((detail) => {
    const budget = detail.budget
    const budgetLabel = `#${budget.id_orcamento} v${budget.versao}`

    totalOrcado += toNumber(budget.custo_total_orcado)
    detail.materiais.forEach((linha) => {
      const item = materialById.get(linha.id_material)
      const custo = toNumber(linha.custo_total)
      const quantidade = toNumber(linha.quantidade)
      totalMateriais += custo

      linhas.push({
        id: `mat-${linha.id_linha_material}`,
        tipo: 'material',
        id_orcamento: budget.id_orcamento,
        orcamentoLabel: budgetLabel,
        itemLabel: item ? `${item.codigo} - ${item.nome}` : `Material #${linha.id_material}`,
        processoLabel: 'Materiais',
        quantidadeLabel: `${quantidade.toFixed(2)} un`,
        quantidadeValor: quantidade,
        custo,
      })
    })

    detail.operacoes.forEach((linha) => {
      const item = operacaoById.get(linha.id_operacao)
      const custo = toNumber(linha.custo_total)
      const horas = toNumber(linha.horas) + toNumber(linha.tempo_setup_h)
      const processo = resolveOperacaoProcesso(item, linha)

      totalOperacoes += custo

      linhas.push({
        id: `op-${linha.id_linha_operacao}`,
        tipo: 'operacao',
        id_orcamento: budget.id_orcamento,
        orcamentoLabel: budgetLabel,
        itemLabel: item ? `${item.codigo} - ${item.nome}` : `Operacao #${linha.id_operacao}`,
        processoLabel:
          processo === 'soldadura'
            ? 'Soldadura'
            : processo === 'pingamento'
              ? 'Pingamento'
              : item?.categoria || 'Outras operacoes',
        quantidadeLabel: `${horas.toFixed(2)} h`,
        quantidadeValor: horas,
        horasValor: horas,
        custo,
      })
    })

    detail.servicos.forEach((linha) => {
      const item = servicoById.get(linha.id_servico)
      const custo = toNumber(linha.custo_total)
      const quantidade = toNumber(linha.quantidade)
      totalServicos += custo

      linhas.push({
        id: `svc-${linha.id_linha_servico}`,
        tipo: 'servico',
        id_orcamento: budget.id_orcamento,
        orcamentoLabel: budgetLabel,
        itemLabel: item ? `${item.codigo} - ${item.nome}` : `Servico #${linha.id_servico}`,
        processoLabel: 'Servicos',
        quantidadeLabel: `${quantidade.toFixed(2)} un`,
        quantidadeValor: quantidade,
        custo,
      })
    })
  })

  linhas.sort((a, b) => {
    if (a.id_orcamento !== b.id_orcamento) {
      return b.id_orcamento - a.id_orcamento
    }
    return a.tipo.localeCompare(b.tipo)
  })

  return {
    totalOrcado,
    totalLinhas: linhas.length,
    totalMateriais,
    totalOperacoes,
    totalServicos,
    linhas,
  }
}

export function useDashboard(token, perfil) {
  const [projects, setProjects] = useState([])
  const [budgets, setBudgets] = useState([])
  const [projectBudgets, setProjectBudgets] = useState([])
  const [projectAnalysis, setProjectAnalysis] = useState(EMPTY_PROJECT_ANALYSIS)
  const [projectAnalysisLoading, setProjectAnalysisLoading] = useState(false)
  const [projectAnalysisError, setProjectAnalysisError] = useState('')
  const [selectedProjectId, setSelectedProjectId] = useState('')

  const [loadingData, setLoadingData] = useState(false)
  const [dataError, setDataError] = useState('')

  const [budgetRealTotals, setBudgetRealTotals] = useState({})
  const [budgetRealLoading, setBudgetRealLoading] = useState(false)
  const [budgetRealError, setBudgetRealError] = useState('')

  const catalogsRef = useRef(null)

  const canLoadDashboard = useMemo(() => {
    if (!token || !perfil) return false
    return ['administrador', 'orcamentista', 'gestor'].includes(normalizePerfil(perfil))
  }, [perfil, token])

  const getCatalogs = useCallback(async () => {
    if (catalogsRef.current) {
      return catalogsRef.current
    }

    const [materiais, operacoes, servicos] = await Promise.all([
      listMateriais(token),
      listOperacoes(token),
      listServicos(token),
    ])

    const catalogs = { materiais, operacoes, servicos }
    catalogsRef.current = catalogs
    return catalogs
  }, [token])

  const totalOrcado = useMemo(
    () => budgets.reduce((acc, item) => acc + Number(item.custo_total_orcado || 0), 0),
    [budgets],
  )

  const loadBudgetRealTotals = useCallback(async (budgetRows) => {
    if (!token) return

    if (!Array.isArray(budgetRows) || budgetRows.length === 0) {
      setBudgetRealTotals({})
      setBudgetRealError('')
      return
    }

    setBudgetRealLoading(true)
    setBudgetRealError('')

    try {
      const idsOrcamento = normalizeOrcamentoIds(budgetRows.map((budget) => budget.id_orcamento))
      if (idsOrcamento.length === 0) {
        setBudgetRealTotals({})
        return
      }

      const rows = await getRealizadoResumoBatch(token, idsOrcamento)
      const totalsByBudget = Object.fromEntries(idsOrcamento.map((id) => [id, 0]))

      rows.forEach((row) => {
        totalsByBudget[row.id_orcamento] = toNumber(row.custo_total_real)
      })

      setBudgetRealTotals(totalsByBudget)
    } catch (err) {
      setBudgetRealTotals(Object.fromEntries(budgetRows.map((budget) => [budget.id_orcamento, 0])))
      setBudgetRealError(err.message || 'Nao foi possivel carregar custos reais dos orcamentos.')
    } finally {
      setBudgetRealLoading(false)
    }
  }, [token])

  const refreshCoreData = useCallback(async () => {
    if (!token || !canLoadDashboard) return

    setLoadingData(true)
    setDataError('')
    try {
      const [projectRows, budgetRows] = await Promise.all([
        listProjects(token),
        listBudgets(token),
      ])
      setProjects(projectRows)
      setBudgets(budgetRows)
      await loadBudgetRealTotals(budgetRows)
    } catch (err) {
      setDataError(err.message || 'Nao foi possivel carregar dados')
    } finally {
      setLoadingData(false)
    }
  }, [canLoadDashboard, loadBudgetRealTotals, token])

  useEffect(() => {
    if (!token || !canLoadDashboard) {
      setProjects([])
      setBudgets([])
      setProjectBudgets([])
      setProjectAnalysis(EMPTY_PROJECT_ANALYSIS)
      setProjectAnalysisError('')
      setSelectedProjectId('')
      setDataError('')
      setBudgetRealTotals({})
      setBudgetRealLoading(false)
      setBudgetRealError('')
      catalogsRef.current = null
      return
    }

    refreshCoreData()
  }, [canLoadDashboard, token, refreshCoreData])

  useEffect(() => {
    if (!selectedProjectId || !token || !canLoadDashboard) {
      setProjectBudgets([])
      setProjectAnalysis(EMPTY_PROJECT_ANALYSIS)
      setProjectAnalysisError('')
      return
    }

    let ignore = false

    const loadRows = async () => {
      setProjectAnalysisLoading(true)
      setProjectAnalysisError('')

      try {
        const rows = await listProjectBudgets(token, selectedProjectId)
        if (ignore) return

        setProjectBudgets(rows)

        if (rows.length === 0) {
          setProjectAnalysis(EMPTY_PROJECT_ANALYSIS)
          return
        }

        const catalogs = await getCatalogs()
        if (ignore) return

        const details = await Promise.all(
          rows.map(async (budget) => {
            const [materiais, operacoes, servicos] = await Promise.all([
              listOrcamentoMateriais(token, budget.id_orcamento),
              listOrcamentoOperacoes(token, budget.id_orcamento),
              listOrcamentoServicos(token, budget.id_orcamento),
            ])

            return {
              budget,
              materiais,
              operacoes,
              servicos,
            }
          }),
        )

        if (ignore) return

        setProjectAnalysis(buildProjectAnalysis(details, catalogs))
      } catch (err) {
        if (!ignore) {
          setProjectAnalysisError(err.message || 'Falha ao analisar o projeto selecionado')
          setProjectBudgets([])
          setProjectAnalysis(EMPTY_PROJECT_ANALYSIS)
        }
      } finally {
        if (!ignore) {
          setProjectAnalysisLoading(false)
        }
      }
    }

    loadRows()

    return () => {
      ignore = true
    }
  }, [canLoadDashboard, getCatalogs, selectedProjectId, token])

  return {
    projects,
    budgets,
    projectBudgets,
    projectAnalysis,
    projectAnalysisLoading,
    projectAnalysisError,
    selectedProjectId,
    setSelectedProjectId,
    loadingData,
    dataError,
    totalOrcado,
    budgetRealTotals,
    budgetRealLoading,
    budgetRealError,
  }
}
