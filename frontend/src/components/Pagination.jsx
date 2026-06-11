/**
 * Controlo de paginação reutilizável (server-side).
 * Mostra "Página X de Y (N registos)" e botões Anterior/Seguinte.
 */
export default function Pagination({ page, pageSize, total, onPageChange, loading = false }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const safePage = Math.min(Math.max(1, page), totalPages)
  const inicio = total === 0 ? 0 : (safePage - 1) * pageSize + 1
  const fim = Math.min(safePage * pageSize, total)

  if (total <= pageSize) {
    // Uma página só: mostra apenas o resumo, sem botões.
    return (
      <div className="pagination">
        <span className="pagination-info">{total} registo{total === 1 ? '' : 's'}</span>
      </div>
    )
  }

  return (
    <div className="pagination">
      <span className="pagination-info">
        {inicio}–{fim} de {total} · Página {safePage}/{totalPages}
      </span>
      <div className="pagination-actions">
        <button
          type="button"
          className="btn-xs"
          onClick={() => onPageChange(safePage - 1)}
          disabled={loading || safePage <= 1}
        >
          « Anterior
        </button>
        <button
          type="button"
          className="btn-xs"
          onClick={() => onPageChange(safePage + 1)}
          disabled={loading || safePage >= totalPages}
        >
          Seguinte »
        </button>
      </div>
    </div>
  )
}
