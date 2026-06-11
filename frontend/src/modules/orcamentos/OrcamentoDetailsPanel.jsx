import { formatMoney, formatStatusLabel, formatVersionLabel } from '../../utils/formatters'

const DETAIL_TABS = ['materiais', 'operacoes', 'servicos']

const DETAIL_TAB_LABELS = {
  materiais: 'Materiais',
  operacoes: 'Operações',
  servicos: 'Serviços',
}

export default function OrcamentoDetailsPanel({
  selectedOrc,
  activeTab,
  setActiveTab,
  loadingLinhas,
  addMatForm,
  setAddMatForm,
  catalogMateriais,
  onAddMaterial,
  linhasMateriais,
  onDeleteMaterial,
  addOpForm,
  setAddOpForm,
  catalogOperacoes,
  onAddOperacao,
  linhasOperacoes,
  onDeleteOperacao,
  addSvcForm,
  setAddSvcForm,
  catalogServicos,
  onAddServico,
  linhasServicos,
  onDeleteServico,
  onExportPdf,
  exportingPdf,
}) {
  if (!selectedOrc) return null

  // Lookups id -> item do catalogo, para mostrar codigo + nome nas linhas
  // (mais legivel do que apenas o id).
  const matById = new Map(catalogMateriais.map((m) => [m.id_material, m]))
  const opById = new Map(catalogOperacoes.map((o) => [o.id_operacao, o]))
  const svcById = new Map(catalogServicos.map((s) => [s.id_servico, s]))

  const nomeMaterial = (id) => {
    const m = matById.get(id)
    return m ? `${m.codigo} - ${m.nome}` : `#${id}`
  }
  const nomeOperacao = (id) => {
    const o = opById.get(id)
    return o ? `${o.codigo} - ${o.nome}` : `#${id}`
  }
  const nomeServico = (id) => {
    const s = svcById.get(id)
    return s ? `${s.codigo} - ${s.nome}` : `#${id}`
  }

  // Linhas so sao editaveis em preparacao/revisao (espelha a regra do backend;
  // a partir de validado o orcamento e imutavel: alteracoes implicam nova versao).
  const linhasEditaveis = ['em_preparacao', 'em_revisao'].includes(selectedOrc.estado)

  return (
    <div className="panel orc-details-panel">
      <div className="panel-head">
        <h3>Orçamento #{selectedOrc.id_orcamento} - {formatVersionLabel(selectedOrc.versao)}</h3>
        <div className="orc-details-badges">
          {(selectedOrc.quantidade_unidades ?? 1) > 1 && (
            <span className="kpi-mini" title="As linhas abaixo são por unidade; os totais já estão multiplicados pelo nº de unidades.">
              {selectedOrc.quantidade_unidades} unidades (linhas por unidade)
            </span>
          )}
          <span className="kpi-mini">Materiais: {formatMoney(selectedOrc.custo_total_materiais)}</span>
          <span className="kpi-mini">Operações: {formatMoney(selectedOrc.custo_total_operacoes)}</span>
          <span className="kpi-mini">Serviços: {formatMoney(selectedOrc.custo_total_servicos)}</span>
          {onExportPdf && (
            <button
              type="button"
              className="btn-xs"
              onClick={onExportPdf}
              disabled={exportingPdf}
              title="Exportar este orçamento para PDF"
            >
              {exportingPdf ? 'A gerar PDF...' : 'Exportar PDF'}
            </button>
          )}
        </div>
      </div>

      <div className="tab-bar">
        {DETAIL_TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {DETAIL_TAB_LABELS[tab] || tab}
          </button>
        ))}
      </div>

      {loadingLinhas && <p className="muted-text">A carregar linhas...</p>}

      {!linhasEditaveis && (
        <p className="muted-text">
          Linhas bloqueadas: o orçamento está em "{formatStatusLabel(selectedOrc.estado)}".
          Só é possível alterar linhas em preparação ou em revisão — para alterar, crie uma nova versão.
        </p>
      )}

      {activeTab === 'materiais' && (
        <div>
          {linhasEditaveis && (
          <form className="add-line-form" onSubmit={onAddMaterial}>
            <select
              value={addMatForm.id_material}
              onChange={(e) => setAddMatForm((f) => ({ ...f, id_material: e.target.value }))}
              required
            >
              <option value="">Selecionar material</option>
              {catalogMateriais.map((m) => (
                <option key={m.id_material} value={m.id_material}>{m.codigo} - {m.nome}</option>
              ))}
            </select>
            <input
              type="number"
              step="0.001"
              placeholder="Qtd"
              min="0.001"
              value={addMatForm.quantidade}
              onChange={(e) => setAddMatForm((f) => ({ ...f, quantidade: e.target.value }))}
              required
            />
            <input
              type="number"
              step="0.01"
              placeholder="Peso (kg)"
              min="0"
              value={addMatForm.peso_kg ?? ''}
              onChange={(e) => setAddMatForm((f) => ({ ...f, peso_kg: e.target.value }))}
            />
            <input
              type="number"
              step="0.01"
              placeholder="Área (m2)"
              min="0"
              value={addMatForm.area_m2 ?? ''}
              onChange={(e) => setAddMatForm((f) => ({ ...f, area_m2: e.target.value }))}
            />
            <input
              type="number"
              step="0.01"
              placeholder="Desperdício %"
              min="0"
              value={addMatForm.desperdicio_percent}
              onChange={(e) => setAddMatForm((f) => ({ ...f, desperdicio_percent: e.target.value }))}
            />
            <input
              placeholder="Obs."
              value={addMatForm.observacoes}
              onChange={(e) => setAddMatForm((f) => ({ ...f, observacoes: e.target.value }))}
            />
            <button type="submit">Adicionar</button>
          </form>
          )}

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>ID Linha</th>
                  <th>Material</th>
                  <th>Qtd</th>
                  <th>Peso (kg)</th>
                  <th>Área (m2)</th>
                  <th>Desperdício %</th>
                  <th>Preço Unit.</th>
                  <th>Custo Total</th>
                  <th>Obs.</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {linhasMateriais.map((linha) => (
                  <tr key={linha.id_linha_material}>
                    <td>{linha.id_linha_material}</td>
                    <td title={nomeMaterial(linha.id_material)}>{nomeMaterial(linha.id_material)}</td>
                    <td>{linha.quantidade}</td>
                    <td>{linha.peso_kg ?? '-'}</td>
                    <td>{linha.area_m2 ?? '-'}</td>
                    <td>{linha.desperdicio_percent}%</td>
                    <td>{formatMoney(linha.preco_unitario_snapshot)}</td>
                    <td>{formatMoney(linha.custo_total)}</td>
                    <td>{linha.observacoes || '-'}</td>
                    <td>
                      {linhasEditaveis && (
                        <button
                          type="button"
                          className="btn-xs btn-danger"
                          onClick={() => onDeleteMaterial(linha.id_linha_material)}
                        >
                          X
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {linhasMateriais.length === 0 && <tr><td colSpan={10}>Sem linhas de material.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'operacoes' && (
        <div>
          {linhasEditaveis && (
          <form className="add-line-form" onSubmit={onAddOperacao}>
            <select
              value={addOpForm.id_operacao}
              onChange={(e) => setAddOpForm((f) => ({ ...f, id_operacao: e.target.value }))}
              required
            >
              <option value="">Selecionar operação</option>
              {catalogOperacoes.map((o) => (
                <option key={o.id_operacao} value={o.id_operacao}>{o.codigo} - {o.nome}</option>
              ))}
            </select>
            <input
              type="number"
              step="0.01"
              placeholder="Horas"
              min="0.01"
              value={addOpForm.horas}
              onChange={(e) => setAddOpForm((f) => ({ ...f, horas: e.target.value }))}
              required
            />
            <input
              type="number"
              step="0.01"
              placeholder="Setup h"
              min="0"
              value={addOpForm.tempo_setup_h}
              onChange={(e) => setAddOpForm((f) => ({ ...f, tempo_setup_h: e.target.value }))}
            />
            <input
              placeholder="Obs."
              value={addOpForm.observacoes}
              onChange={(e) => setAddOpForm((f) => ({ ...f, observacoes: e.target.value }))}
            />
            <button type="submit">Adicionar</button>
          </form>
          )}

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>ID Linha</th>
                  <th>Operação</th>
                  <th>Horas</th>
                  <th>Setup h</th>
                  <th>Custo/h</th>
                  <th>Custo Total</th>
                  <th>Obs.</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {linhasOperacoes.map((linha) => (
                  <tr key={linha.id_linha_operacao}>
                    <td>{linha.id_linha_operacao}</td>
                    <td title={nomeOperacao(linha.id_operacao)}>{nomeOperacao(linha.id_operacao)}</td>
                    <td>{linha.horas}</td>
                    <td>{linha.tempo_setup_h}</td>
                    <td>{formatMoney(linha.custo_hora_snapshot)}</td>
                    <td>{formatMoney(linha.custo_total)}</td>
                    <td>{linha.observacoes || '-'}</td>
                    <td>
                      {linhasEditaveis && (
                        <button
                          type="button"
                          className="btn-xs btn-danger"
                          onClick={() => onDeleteOperacao(linha.id_linha_operacao)}
                        >
                          X
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {linhasOperacoes.length === 0 && <tr><td colSpan={8}>Sem linhas de operação.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'servicos' && (
        <div>
          {linhasEditaveis && (
          <form className="add-line-form" onSubmit={onAddServico}>
            <select
              value={addSvcForm.id_servico}
              onChange={(e) => setAddSvcForm((f) => ({ ...f, id_servico: e.target.value }))}
              required
            >
              <option value="">Selecionar serviço</option>
              {catalogServicos.map((s) => (
                <option key={s.id_servico} value={s.id_servico}>{s.codigo} - {s.nome}</option>
              ))}
            </select>
            <input
              type="number"
              step="0.001"
              placeholder="Qtd"
              min="0.001"
              value={addSvcForm.quantidade}
              onChange={(e) => setAddSvcForm((f) => ({ ...f, quantidade: e.target.value }))}
              required
            />
            <input
              placeholder="Obs."
              value={addSvcForm.observacoes}
              onChange={(e) => setAddSvcForm((f) => ({ ...f, observacoes: e.target.value }))}
            />
            <button type="submit">Adicionar</button>
          </form>
          )}

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>ID Linha</th>
                  <th>Serviço</th>
                  <th>Qtd</th>
                  <th>Preço Unit.</th>
                  <th>Custo Total</th>
                  <th>Obs.</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {linhasServicos.map((linha) => (
                  <tr key={linha.id_linha_servico}>
                    <td>{linha.id_linha_servico}</td>
                    <td title={nomeServico(linha.id_servico)}>{nomeServico(linha.id_servico)}</td>
                    <td>{linha.quantidade}</td>
                    <td>{formatMoney(linha.preco_unitario_snapshot)}</td>
                    <td>{formatMoney(linha.custo_total)}</td>
                    <td>{linha.observacoes || '-'}</td>
                    <td>
                      {linhasEditaveis && (
                        <button
                          type="button"
                          className="btn-xs btn-danger"
                          onClick={() => onDeleteServico(linha.id_linha_servico)}
                        >
                          X
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {linhasServicos.length === 0 && <tr><td colSpan={7}>Sem linhas de serviço.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
