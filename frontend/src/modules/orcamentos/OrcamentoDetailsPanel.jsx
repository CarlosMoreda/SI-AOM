import { formatMoney } from '../../utils/formatters'

const DETAIL_TABS = ['materiais', 'operacoes', 'servicos']

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
}) {
  if (!selectedOrc) return null

  return (
    <div className="panel orc-details-panel">
      <div className="panel-head">
        <h3>Orcamento #{selectedOrc.id_orcamento} - v{selectedOrc.versao}</h3>
        <div className="orc-details-badges">
          <span className="kpi-mini">Materiais: {formatMoney(selectedOrc.custo_total_materiais)}</span>
          <span className="kpi-mini">Operacoes: {formatMoney(selectedOrc.custo_total_operacoes)}</span>
          <span className="kpi-mini">Servicos: {formatMoney(selectedOrc.custo_total_servicos)}</span>
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
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {loadingLinhas && <p className="muted-text">A carregar linhas...</p>}

      {activeTab === 'materiais' && (
        <div>
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
              placeholder="Desperdicio %"
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

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>ID Linha</th>
                  <th>ID Material</th>
                  <th>Qtd</th>
                  <th>Desperd.%</th>
                  <th>Preco Unit.</th>
                  <th>Custo Total</th>
                  <th>Obs.</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {linhasMateriais.map((linha) => (
                  <tr key={linha.id_linha_material}>
                    <td>{linha.id_linha_material}</td>
                    <td>{linha.id_material}</td>
                    <td>{linha.quantidade}</td>
                    <td>{linha.desperdicio_percent}%</td>
                    <td>{formatMoney(linha.preco_unitario_snapshot)}</td>
                    <td>{formatMoney(linha.custo_total)}</td>
                    <td>{linha.observacoes || '-'}</td>
                    <td>
                      <button
                        type="button"
                        className="btn-xs btn-danger"
                        onClick={() => onDeleteMaterial(linha.id_linha_material)}
                      >
                        X
                      </button>
                    </td>
                  </tr>
                ))}
                {linhasMateriais.length === 0 && <tr><td colSpan={8}>Sem linhas de material.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'operacoes' && (
        <div>
          <form className="add-line-form" onSubmit={onAddOperacao}>
            <select
              value={addOpForm.id_operacao}
              onChange={(e) => setAddOpForm((f) => ({ ...f, id_operacao: e.target.value }))}
              required
            >
              <option value="">Selecionar operacao</option>
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

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>ID Linha</th>
                  <th>ID Operacao</th>
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
                    <td>{linha.id_operacao}</td>
                    <td>{linha.horas}</td>
                    <td>{linha.tempo_setup_h}</td>
                    <td>{formatMoney(linha.custo_hora_snapshot)}</td>
                    <td>{formatMoney(linha.custo_total)}</td>
                    <td>{linha.observacoes || '-'}</td>
                    <td>
                      <button
                        type="button"
                        className="btn-xs btn-danger"
                        onClick={() => onDeleteOperacao(linha.id_linha_operacao)}
                      >
                        X
                      </button>
                    </td>
                  </tr>
                ))}
                {linhasOperacoes.length === 0 && <tr><td colSpan={8}>Sem linhas de operacao.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'servicos' && (
        <div>
          <form className="add-line-form" onSubmit={onAddServico}>
            <select
              value={addSvcForm.id_servico}
              onChange={(e) => setAddSvcForm((f) => ({ ...f, id_servico: e.target.value }))}
              required
            >
              <option value="">Selecionar servico</option>
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

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>ID Linha</th>
                  <th>ID Servico</th>
                  <th>Qtd</th>
                  <th>Preco Unit.</th>
                  <th>Custo Total</th>
                  <th>Obs.</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {linhasServicos.map((linha) => (
                  <tr key={linha.id_linha_servico}>
                    <td>{linha.id_linha_servico}</td>
                    <td>{linha.id_servico}</td>
                    <td>{linha.quantidade}</td>
                    <td>{formatMoney(linha.preco_unitario_snapshot)}</td>
                    <td>{formatMoney(linha.custo_total)}</td>
                    <td>{linha.observacoes || '-'}</td>
                    <td>
                      <button
                        type="button"
                        className="btn-xs btn-danger"
                        onClick={() => onDeleteServico(linha.id_linha_servico)}
                      >
                        X
                      </button>
                    </td>
                  </tr>
                ))}
                {linhasServicos.length === 0 && <tr><td colSpan={7}>Sem linhas de servico.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
