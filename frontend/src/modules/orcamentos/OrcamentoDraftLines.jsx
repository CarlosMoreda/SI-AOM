export default function OrcamentoDraftLines({
  countDraftLines,
  draftMatForm,
  setDraftMatForm,
  catalogMateriais,
  onAddDraftMaterial,
  draftMateriais,
  onRemoveDraftMaterial,
  draftOpForm,
  setDraftOpForm,
  catalogOperacoes,
  onAddDraftOperacao,
  draftOperacoes,
  onRemoveDraftOperacao,
  draftSvcForm,
  setDraftSvcForm,
  catalogServicos,
  onAddDraftServico,
  draftServicos,
  onRemoveDraftServico,
}) {
  return (
    <div className="draft-lines-panel">
      <div className="draft-lines-head">
        <strong>Linhas para criar com o orcamento</strong>
        <span className="draft-lines-count">Total: {countDraftLines}</span>
      </div>

      <div className="draft-lines-grid">
        <div>
          <h4 className="draft-section-title">Materiais</h4>
          <div className="add-line-form">
            <select
              value={draftMatForm.id_material}
              onChange={(e) => setDraftMatForm((f) => ({ ...f, id_material: e.target.value }))}
            >
              <option value="">Selecionar material</option>
              {catalogMateriais.map((m) => (
                <option key={m.id_material} value={m.id_material}>{m.codigo} - {m.nome}</option>
              ))}
            </select>
            <input
              type="number"
              step="0.001"
              min="0.001"
              placeholder="Qtd"
              value={draftMatForm.quantidade}
              onChange={(e) => setDraftMatForm((f) => ({ ...f, quantidade: e.target.value }))}
            />
            <input
              type="number"
              step="0.01"
              min="0"
              placeholder="Desperdicio %"
              value={draftMatForm.desperdicio_percent}
              onChange={(e) => setDraftMatForm((f) => ({ ...f, desperdicio_percent: e.target.value }))}
            />
            <input
              placeholder="Obs."
              value={draftMatForm.observacoes}
              onChange={(e) => setDraftMatForm((f) => ({ ...f, observacoes: e.target.value }))}
            />
            <button type="button" onClick={onAddDraftMaterial}>Adicionar</button>
          </div>

          {draftMateriais.length > 0 && (
            <div className="table-scroll draft-lines-table">
              <table>
                <thead>
                  <tr>
                    <th>Material</th>
                    <th>Qtd</th>
                    <th>Desperd.%</th>
                    <th>Obs.</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {draftMateriais.map((linha, idx) => (
                    <tr key={`dmat-${idx}`}>
                      <td>{linha.label}</td>
                      <td>{linha.quantidade}</td>
                      <td>{linha.desperdicio_percent}%</td>
                      <td>{linha.observacoes || '-'}</td>
                      <td>
                        <button type="button" className="btn-xs btn-danger" onClick={() => onRemoveDraftMaterial(idx)}>
                          X
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div>
          <h4 className="draft-section-title">Operacoes</h4>
          <div className="add-line-form">
            <select
              value={draftOpForm.id_operacao}
              onChange={(e) => setDraftOpForm((f) => ({ ...f, id_operacao: e.target.value }))}
            >
              <option value="">Selecionar operacao</option>
              {catalogOperacoes.map((o) => (
                <option key={o.id_operacao} value={o.id_operacao}>{o.codigo} - {o.nome}</option>
              ))}
            </select>
            <input
              type="number"
              step="0.01"
              min="0.01"
              placeholder="Horas"
              value={draftOpForm.horas}
              onChange={(e) => setDraftOpForm((f) => ({ ...f, horas: e.target.value }))}
            />
            <input
              type="number"
              step="0.01"
              min="0"
              placeholder="Setup h"
              value={draftOpForm.tempo_setup_h}
              onChange={(e) => setDraftOpForm((f) => ({ ...f, tempo_setup_h: e.target.value }))}
            />
            <input
              placeholder="Obs."
              value={draftOpForm.observacoes}
              onChange={(e) => setDraftOpForm((f) => ({ ...f, observacoes: e.target.value }))}
            />
            <button type="button" onClick={onAddDraftOperacao}>Adicionar</button>
          </div>

          {draftOperacoes.length > 0 && (
            <div className="table-scroll draft-lines-table">
              <table>
                <thead>
                  <tr>
                    <th>Operacao</th>
                    <th>Horas</th>
                    <th>Setup h</th>
                    <th>Obs.</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {draftOperacoes.map((linha, idx) => (
                    <tr key={`dop-${idx}`}>
                      <td>{linha.label}</td>
                      <td>{linha.horas}</td>
                      <td>{linha.tempo_setup_h}</td>
                      <td>{linha.observacoes || '-'}</td>
                      <td>
                        <button type="button" className="btn-xs btn-danger" onClick={() => onRemoveDraftOperacao(idx)}>
                          X
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div>
          <h4 className="draft-section-title">Servicos</h4>
          <div className="add-line-form">
            <select
              value={draftSvcForm.id_servico}
              onChange={(e) => setDraftSvcForm((f) => ({ ...f, id_servico: e.target.value }))}
            >
              <option value="">Selecionar servico</option>
              {catalogServicos.map((s) => (
                <option key={s.id_servico} value={s.id_servico}>{s.codigo} - {s.nome}</option>
              ))}
            </select>
            <input
              type="number"
              step="0.001"
              min="0.001"
              placeholder="Qtd"
              value={draftSvcForm.quantidade}
              onChange={(e) => setDraftSvcForm((f) => ({ ...f, quantidade: e.target.value }))}
            />
            <input
              placeholder="Obs."
              value={draftSvcForm.observacoes}
              onChange={(e) => setDraftSvcForm((f) => ({ ...f, observacoes: e.target.value }))}
            />
            <button type="button" onClick={onAddDraftServico}>Adicionar</button>
          </div>

          {draftServicos.length > 0 && (
            <div className="table-scroll draft-lines-table">
              <table>
                <thead>
                  <tr>
                    <th>Servico</th>
                    <th>Qtd</th>
                    <th>Obs.</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {draftServicos.map((linha, idx) => (
                    <tr key={`dsv-${idx}`}>
                      <td>{linha.label}</td>
                      <td>{linha.quantidade}</td>
                      <td>{linha.observacoes || '-'}</td>
                      <td>
                        <button type="button" className="btn-xs btn-danger" onClick={() => onRemoveDraftServico(idx)}>
                          X
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
