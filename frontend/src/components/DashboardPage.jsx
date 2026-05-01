import { useMemo, useState } from 'react'

import SiaomMenu from './SiaomMenu'
import { getVisibleMenuItems } from './menuConfig'
import { formatDate, formatMoney } from '../utils/formatters'
import ClientesModule from '../modules/ClientesModule'
import ProjetosModule from '../modules/ProjetosModule'
import OrcamentosModule from '../modules/OrcamentosModule'
import MateriaisModule from '../modules/MateriaisModule'
import OperacoesModule from '../modules/OperacoesModule'
import ServicosModule from '../modules/ServicosModule'
import RealizadoModule from '../modules/RealizadoModule'
import ComparacaoModule from '../modules/ComparacaoModule'
import MlModule from '../modules/MlModule'
import UtilizadoresModule from '../modules/UtilizadoresModule'

function toNumber(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function percent(value, total) {
  if (!total || total <= 0) return 0
  return Math.max(0, Math.min(100, (value / total) * 100))
}

const LINES_PER_PAGE = 12

function BudgetTrendChart({ rows }) {
  if (rows.length === 0) {
    return <p className="analytics-empty">Sem orcamentos para desenhar o grafico.</p>
  }

  const maxValue = rows.reduce((acc, row) => {
    const current = Math.max(toNumber(row.custo_total_orcado), toNumber(row.custo_total_real))
    return Math.max(acc, current)
  }, 1)

  return (
    <div className="trend-list">
      {rows.map((row) => {
        const orcado = toNumber(row.custo_total_orcado)
        const venda = toNumber(row.custo_total_real)

        return (
          <article className="trend-item" key={row.id_orcamento}>
            <div className="trend-head">
              <p>Orcamento #{row.id_orcamento} - v{row.versao}</p>
            </div>

            <div className="trend-bar-row">
              <span>Orcado</span>
              <div className="trend-track">
                <div
                  className="trend-fill trend-fill-orcado"
                  style={{ width: `${percent(orcado, maxValue)}%` }}
                />
              </div>
              <strong>{formatMoney(orcado)}</strong>
            </div>

            <div className="trend-bar-row">
              <span>Real</span>
              <div className="trend-track">
                <div
                  className="trend-fill trend-fill-venda"
                  style={{ width: `${percent(venda, maxValue)}%` }}
                />
              </div>
              <strong>{formatMoney(venda)}</strong>
            </div>
          </article>
        )
      })}
    </div>
  )
}

function StatusChart({ statusRows }) {
  if (statusRows.length === 0) {
    return <p className="analytics-empty">Sem projetos para analisar.</p>
  }

  const maxCount = statusRows.reduce((acc, row) => Math.max(acc, row.count), 1)

  return (
    <div className="status-chart-list">
      {statusRows.map((row) => (
        <div key={row.estado} className="status-chart-row">
          <div className="status-chart-head">
            <span>{row.estado}</span>
            <strong>{row.count}</strong>
          </div>
          <div className="status-chart-track">
            <div
              className="status-chart-fill"
              style={{ width: `${percent(row.count, maxCount)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

export default function DashboardPage({
  user,
  token,
  authError,
  onLogout,
  projects,
  budgets,
  totalOrcado,
  loadingData,
  dataError,
  selectedProjectId,
  setSelectedProjectId,
  projectBudgets,
  projectAnalysis,
  projectAnalysisLoading,
  projectAnalysisError,
  budgetRealTotals,
  budgetRealLoading,
  budgetRealError,
}) {
  const [selectedModule, setSelectedModule] = useState('dashboard')
  const [lineTypeFilter, setLineTypeFilter] = useState('all')
  const [lineSearchTerm, setLineSearchTerm] = useState('')
  const [lineSortKey, setLineSortKey] = useState('custo:desc')
  const [linePage, setLinePage] = useState(1)

  const visibleMenuItems = useMemo(
    () => getVisibleMenuItems(user?.perfil || 'administrador'),
    [user?.perfil],
  )
  const visibleModuleKeys = useMemo(
    () => new Set(visibleMenuItems.map((item) => item.key)),
    [visibleMenuItems],
  )

  const activeModule = visibleModuleKeys.has(selectedModule)
    ? selectedModule
    : visibleMenuItems[0]?.key || 'definicoes'

  const selectedProject = useMemo(
    () => projects.find((project) => String(project.id_projeto) === String(selectedProjectId)) || null,
    [projects, selectedProjectId],
  )

  const budgetsWithReal = useMemo(
    () =>
      budgets.map((budget) => ({
        ...budget,
        custo_total_real: toNumber(budgetRealTotals[budget.id_orcamento]),
      })),
    [budgets, budgetRealTotals],
  )

  const projectBudgetsWithReal = useMemo(
    () =>
      projectBudgets.map((budget) => ({
        ...budget,
        custo_total_real: toNumber(budgetRealTotals[budget.id_orcamento]),
      })),
    [projectBudgets, budgetRealTotals],
  )

  const trendRows = useMemo(
    () => [...budgetsWithReal].sort((a, b) => b.id_orcamento - a.id_orcamento).slice(0, 7).reverse(),
    [budgetsWithReal],
  )

  const statusRows = useMemo(() => {
    const counts = projects.reduce((acc, project) => {
      const key = project.estado || 'sem_estado'
      acc[key] = (acc[key] || 0) + 1
      return acc
    }, {})

    return Object.entries(counts)
      .map(([estado, count]) => ({ estado, count }))
      .sort((a, b) => b.count - a.count)
  }, [projects])

  const ticketMedio = useMemo(() => {
    if (budgets.length === 0) return 0
    return totalOrcado / budgets.length
  }, [budgets.length, totalOrcado])

  const totalReal = useMemo(
    () => budgetsWithReal.reduce((acc, budget) => acc + toNumber(budget.custo_total_real), 0),
    [budgetsWithReal],
  )

  const desvioRealMedio = useMemo(() => {
    if (totalOrcado <= 0) return 0
    return ((totalReal - totalOrcado) / totalOrcado) * 100
  }, [totalOrcado, totalReal])

  const totalProjetoReal = useMemo(
    () => projectBudgetsWithReal.reduce((acc, budget) => acc + toNumber(budget.custo_total_real), 0),
    [projectBudgetsWithReal],
  )

  const automaticProcessRows = useMemo(() => {
    const processMap = {}

    projectAnalysis.linhas.forEach((line) => {
      if (line.tipo !== 'operacao') return

      const processo = line.processoLabel || 'Outras operacoes'
      const horas = toNumber(line.horasValor ?? line.quantidadeValor)

      if (!processMap[processo]) {
        processMap[processo] = {
          processo,
          custo: 0,
          horas: 0,
          linhas: 0,
        }
      }

      processMap[processo].custo += toNumber(line.custo)
      processMap[processo].horas += horas
      processMap[processo].linhas += 1
    })

    return Object.values(processMap).sort((a, b) => b.custo - a.custo)
  }, [projectAnalysis.linhas])

  const filteredLinesByType = useMemo(() => {
    if (lineTypeFilter === 'all') return projectAnalysis.linhas
    return projectAnalysis.linhas.filter((linha) => linha.tipo === lineTypeFilter)
  }, [lineTypeFilter, projectAnalysis.linhas])

  const searchedLines = useMemo(() => {
    const term = lineSearchTerm.trim().toLowerCase()
    if (!term) return filteredLinesByType

    return filteredLinesByType.filter((linha) =>
      [
        linha.orcamentoLabel,
        linha.tipo,
        linha.itemLabel,
        linha.processoLabel,
        linha.quantidadeLabel,
      ]
        .join(' ')
        .toLowerCase()
        .includes(term),
    )
  }, [filteredLinesByType, lineSearchTerm])

  const sortedLines = useMemo(() => {
    const [field, direction] = lineSortKey.split(':')
    const order = direction === 'asc' ? 1 : -1

    return [...searchedLines].sort((a, b) => {
      if (field === 'custo') {
        return (toNumber(a.custo) - toNumber(b.custo)) * order
      }

      if (field === 'orcamento') {
        return (toNumber(a.id_orcamento) - toNumber(b.id_orcamento)) * order
      }

      if (field === 'tipo') {
        return a.tipo.localeCompare(b.tipo) * order
      }

      if (field === 'processo') {
        return a.processoLabel.localeCompare(b.processoLabel) * order
      }

      return a.itemLabel.localeCompare(b.itemLabel) * order
    })
  }, [searchedLines, lineSortKey])

  const totalLinePages = useMemo(
    () => Math.max(1, Math.ceil(sortedLines.length / LINES_PER_PAGE)),
    [sortedLines.length],
  )

  const currentLinePage = Math.min(linePage, totalLinePages)

  const paginatedLines = useMemo(() => {
    const start = (currentLinePage - 1) * LINES_PER_PAGE
    return sortedLines.slice(start, start + LINES_PER_PAGE)
  }, [sortedLines, currentLinePage])

  const projectCostTotal =
    projectAnalysis.totalMateriais + projectAnalysis.totalOperacoes + projectAnalysis.totalServicos

  function renderModule() {
    switch (activeModule) {
      case 'projetos':
        return <ProjetosModule token={token} />
      case 'clientes':
        return <ClientesModule token={token} />
      case 'orcamentos':
        return <OrcamentosModule token={token} />
      case 'materiais':
        return <MateriaisModule token={token} />
      case 'operacoes':
        return <OperacoesModule token={token} />
      case 'servicos':
        return <ServicosModule token={token} />
      case 'realizado':
        return <RealizadoModule token={token} />
      case 'comparacao':
        return <ComparacaoModule token={token} />
      case 'ml':
        return <MlModule token={token} user={user} />
      case 'utilizadores':
        return <UtilizadoresModule token={token} />
      case 'definicoes':
        return (
          <div className="panel">
            <div className="panel-head">
              <h3>Definicoes</h3>
              <span>Configuracoes do sistema</span>
            </div>
            <p className="settings-card">
              Utilizador: <strong>{user?.nome}</strong> ({user?.email})<br />
              Perfil: <strong>{user?.perfil}</strong><br />
              Estado: <strong>{user?.ativo ? 'Ativo' : 'Inativo'}</strong>
            </p>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">SI-AOM</p>
          <h2>Dashboard Analitico</h2>
        </div>
        <div className="user-box">
          <p className="user-name">{user?.nome || user?.email}</p>
          <p className="role">{user?.perfil}</p>
          <button type="button" className="logout-button" onClick={onLogout}>Terminar sessao</button>
        </div>
      </header>

      {authError && <p className="message error">{authError}</p>}
      {dataError && <p className="message error">{dataError}</p>}
      {budgetRealError && <p className="message error">{budgetRealError}</p>}

      <section className="workspace-grid">
        <SiaomMenu selected={activeModule} onSelect={setSelectedModule} perfil={user?.perfil || 'administrador'} />

        <div className="workspace-content">
          {activeModule === 'dashboard' ? (
            <>
              <section className="kpi-grid analytics-kpi-grid">
                <article className="kpi-card">
                  <p className="kpi-label">Projetos</p>
                  <p className="kpi-value">{projects.length}</p>
                </article>
                <article className="kpi-card">
                  <p className="kpi-label">Orcamentos</p>
                  <p className="kpi-value">{budgets.length}</p>
                </article>
                <article className="kpi-card">
                  <p className="kpi-label">Total orcado</p>
                  <p className="kpi-value">{formatMoney(totalOrcado)}</p>
                </article>
                <article className="kpi-card">
                  <p className="kpi-label">Total real</p>
                  <p className="kpi-value">{formatMoney(totalReal)}</p>
                </article>
                <article className="kpi-card">
                  <p className="kpi-label">Ticket medio</p>
                  <p className="kpi-value">{formatMoney(ticketMedio)}</p>
                </article>
                <article className="kpi-card">
                  <p className="kpi-label">Desvio medio real</p>
                  <p className="kpi-value">{desvioRealMedio.toFixed(2)}%</p>
                </article>
              </section>

              <section className="analytics-main-grid">
                <article className="panel analytics-panel-large">
                  <div className="panel-head">
                    <h3>Orcado vs Real por Orcamento</h3>
                    <span>Ultimos 7 orcamentos</span>
                  </div>

                  {budgetRealLoading && <p className="analytics-empty">A carregar custos reais dos orcamentos...</p>}

                  <BudgetTrendChart rows={trendRows} />
                </article>

                <article className="panel">
                  <div className="panel-head">
                    <h3>Grafico: Projetos por Estado</h3>
                    <span>{projects.length} projetos</span>
                  </div>

                  <StatusChart statusRows={statusRows} />
                </article>
              </section>

              <section className="analytics-project-grid">
                <article className="panel analytics-panel-large">
                  <div className="panel-head">
                    <h3>Analise de Projeto</h3>
                    <span>{loadingData ? 'A atualizar dados base...' : 'Selecionar projeto para detalhes'}</span>
                  </div>

                  <label className="inline-field analytics-inline-field">
                    Projeto
                    <select
                      value={selectedProjectId}
                      onChange={(event) => {
                        setSelectedProjectId(event.target.value)
                        setLineTypeFilter('all')
                        setLineSearchTerm('')
                        setLineSortKey('custo:desc')
                        setLinePage(1)
                      }}
                    >
                      <option value="">Escolher projeto</option>
                      {projects.map((project) => (
                        <option key={project.id_projeto} value={project.id_projeto}>
                          #{project.id_projeto} - {project.designacao}
                        </option>
                      ))}
                    </select>
                  </label>

                  {projectAnalysisError && <p className="message error">{projectAnalysisError}</p>}

                  {!selectedProjectId && (
                    <p className="analytics-empty">Escolhe um projeto para veres os detalhes automáticos do orçamento e as linhas de detalhe.</p>
                  )}

                  {selectedProjectId && projectAnalysisLoading && (
                    <p className="analytics-empty">A analisar orcamentos e linhas do projeto...</p>
                  )}

                  {selectedProjectId && !projectAnalysisLoading && selectedProject && (
                    <>
                      <div className="project-summary-header">
                        <div>
                          <h4>#{selectedProject.id_projeto} - {selectedProject.designacao}</h4>
                          <p>
                            {selectedProject.referencia} | {selectedProject.estado} | criado em {formatDate(selectedProject.criado_em)}
                          </p>
                        </div>
                        <div className="project-summary-meta">
                          <span>{projectBudgets.length} orcamentos</span>
                          <span>{projectAnalysis.totalLinhas} linhas</span>
                        </div>
                      </div>

                      <div className="project-kpi-grid">
                        <article className="kpi-card">
                          <p className="kpi-label">Orcado do projeto</p>
                          <p className="kpi-value">{formatMoney(projectAnalysis.totalOrcado)}</p>
                        </article>
                        <article className="kpi-card">
                          <p className="kpi-label">Real do projeto</p>
                          <p className="kpi-value">{formatMoney(totalProjetoReal)}</p>
                        </article>
                        <article className="kpi-card">
                          <p className="kpi-label">Linhas do projeto</p>
                          <p className="kpi-value">{projectAnalysis.totalLinhas}</p>
                        </article>
                        <article className="kpi-card">
                          <p className="kpi-label">Materiais</p>
                          <p className="kpi-value">{formatMoney(projectAnalysis.totalMateriais)}</p>
                        </article>
                        <article className="kpi-card">
                          <p className="kpi-label">Operacoes</p>
                          <p className="kpi-value">{formatMoney(projectAnalysis.totalOperacoes)}</p>
                        </article>
                        <article className="kpi-card">
                          <p className="kpi-label">Servicos</p>
                          <p className="kpi-value">{formatMoney(projectAnalysis.totalServicos)}</p>
                        </article>
                      </div>

                      <div className="cost-breakdown-panel">
                        <div className="panel-head">
                          <h3>Composicao de custos do projeto</h3>
                          <span>{formatMoney(projectCostTotal)}</span>
                        </div>

                        <div className="cost-breakdown-bar">
                          <span
                            className="cost-breakdown-fill materiais"
                            style={{ width: `${percent(projectAnalysis.totalMateriais, projectCostTotal)}%` }}
                            title={`Materiais: ${formatMoney(projectAnalysis.totalMateriais)}`}
                          />
                          <span
                            className="cost-breakdown-fill operacoes"
                            style={{ width: `${percent(projectAnalysis.totalOperacoes, projectCostTotal)}%` }}
                            title={`Operacoes: ${formatMoney(projectAnalysis.totalOperacoes)}`}
                          />
                          <span
                            className="cost-breakdown-fill servicos"
                            style={{ width: `${percent(projectAnalysis.totalServicos, projectCostTotal)}%` }}
                            title={`Servicos: ${formatMoney(projectAnalysis.totalServicos)}`}
                          />
                        </div>

                        <div className="cost-breakdown-legend">
                          <span>Materiais: {formatMoney(projectAnalysis.totalMateriais)}</span>
                          <span>Operacoes: {formatMoney(projectAnalysis.totalOperacoes)}</span>
                          <span>Servicos: {formatMoney(projectAnalysis.totalServicos)}</span>
                        </div>
                      </div>

                      <div className="cost-breakdown-panel">
                        <div className="panel-head">
                          <h3>Processos detectados automaticamente</h3>
                          <span>{automaticProcessRows.length} processo(s)</span>
                        </div>

                        {automaticProcessRows.length === 0 && (
                          <p className="analytics-empty">Sem operacoes para calcular processos automaticamente.</p>
                        )}

                        {automaticProcessRows.length > 0 && (
                          <div className="auto-process-list">
                            {automaticProcessRows.map((processo) => (
                              <article key={processo.processo} className="auto-process-item">
                                <div className="auto-process-head">
                                  <strong>{processo.processo}</strong>
                                  <span>{processo.linhas} linhas</span>
                                </div>
                                <div className="auto-process-meta">
                                  <span>{processo.horas.toFixed(2)} h</span>
                                  <strong>{formatMoney(processo.custo)}</strong>
                                </div>
                              </article>
                            ))}
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </article>

                <article className="panel">
                  <div className="panel-head">
                    <h3>Linhas dos Orcamentos do Projeto</h3>
                    <span>{sortedLines.length} linhas</span>
                  </div>

                  <div className="analytics-lines-controls">
                    <label className="inline-field analytics-inline-field">
                      Tipo de linha
                      <select
                        value={lineTypeFilter}
                        onChange={(event) => {
                          setLineTypeFilter(event.target.value)
                          setLinePage(1)
                        }}
                        disabled={!selectedProjectId}
                      >
                        <option value="all">Todas</option>
                        <option value="material">Materiais</option>
                        <option value="operacao">Operacoes</option>
                        <option value="servico">Servicos</option>
                      </select>
                    </label>

                    <label className="inline-field analytics-inline-field">
                      Pesquisar linhas
                      <input
                        value={lineSearchTerm}
                        onChange={(event) => {
                          setLineSearchTerm(event.target.value)
                          setLinePage(1)
                        }}
                        placeholder="Item, processo, tipo ou orcamento"
                        disabled={!selectedProjectId}
                      />
                    </label>

                    <label className="inline-field analytics-inline-field">
                      Ordenar por
                      <select
                        value={lineSortKey}
                        onChange={(event) => {
                          setLineSortKey(event.target.value)
                          setLinePage(1)
                        }}
                        disabled={!selectedProjectId}
                      >
                        <option value="custo:desc">Custo (maior para menor)</option>
                        <option value="custo:asc">Custo (menor para maior)</option>
                        <option value="orcamento:desc">Orcamento (mais recente)</option>
                        <option value="orcamento:asc">Orcamento (mais antigo)</option>
                        <option value="tipo:asc">Tipo (A-Z)</option>
                        <option value="processo:asc">Processo (A-Z)</option>
                        <option value="item:asc">Item (A-Z)</option>
                      </select>
                    </label>
                  </div>

                  {!selectedProjectId && (
                    <p className="analytics-empty">Seleciona um projeto para ver as linhas dos orcamentos.</p>
                  )}

                  {selectedProjectId && projectAnalysisLoading && (
                    <p className="analytics-empty">A carregar linhas...</p>
                  )}

                  {selectedProjectId && !projectAnalysisLoading && (
                    <>
                      <div className="table-scroll analytics-lines-table">
                        <table>
                          <thead>
                            <tr>
                              <th>Orcamento</th>
                              <th>Tipo</th>
                              <th>Item</th>
                              <th>Processo</th>
                              <th>Quantidade/Horas</th>
                              <th>Custo</th>
                            </tr>
                          </thead>
                          <tbody>
                            {paginatedLines.map((line) => (
                              <tr key={line.id}>
                                <td>{line.orcamentoLabel}</td>
                                <td>
                                  <span className={`badge badge-${line.tipo}`}>{line.tipo}</span>
                                </td>
                                <td>{line.itemLabel}</td>
                                <td>{line.processoLabel}</td>
                                <td>{line.quantidadeLabel}</td>
                                <td>{formatMoney(line.custo)}</td>
                              </tr>
                            ))}

                            {sortedLines.length === 0 && (
                              <tr>
                                <td colSpan={6}>Sem linhas para os filtros aplicados.</td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>

                      {sortedLines.length > 0 && (
                        <div className="analytics-lines-pagination">
                          <span>
                            Pagina {currentLinePage} de {totalLinePages} - {sortedLines.length} linhas
                          </span>
                          <div className="analytics-lines-pagination-actions">
                            <button
                              type="button"
                              onClick={() => setLinePage((page) => Math.max(1, page - 1))}
                              disabled={currentLinePage <= 1}
                            >
                              Anterior
                            </button>
                            <button
                              type="button"
                              onClick={() => setLinePage((page) => Math.min(totalLinePages, page + 1))}
                              disabled={currentLinePage >= totalLinePages}
                            >
                              Seguinte
                            </button>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </article>
              </section>

              {selectedProjectId && !projectAnalysisLoading && projectBudgets.length > 0 && (
                <article className="panel analytics-budget-list-panel">
                  <div className="panel-head">
                    <h3>Orcamentos do Projeto Selecionado</h3>
                    <span>{projectBudgets.length} registos</span>
                  </div>

                  <ul className="budget-list">
                    {projectBudgetsWithReal.map((budget) => (
                      <li key={budget.id_orcamento}>
                        <strong>Orcamento #{budget.id_orcamento}</strong>
                        <span>Versao {budget.versao}</span>
                        <span>Estado: {budget.estado}</span>
                        <span>Total orcado: {formatMoney(budget.custo_total_orcado)}</span>
                        <span>Total real: {formatMoney(budget.custo_total_real)}</span>
                      </li>
                    ))}
                  </ul>
                </article>
              )}

              {selectedProjectId && !projectAnalysisLoading && projectBudgets.length === 0 && (
                <article className="panel analytics-budget-list-panel">
                  <div className="panel-head">
                    <h3>Orcamentos do Projeto Selecionado</h3>
                  </div>
                  <p className="analytics-empty">Este projeto ainda nao tem orcamentos.</p>
                </article>
              )}

              {loadingData && <p className="analytics-empty">A sincronizar dados do dashboard...</p>}
            </>
          ) : (
            renderModule()
          )}
        </div>
      </section>
    </main>
  )
}
