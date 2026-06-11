import { useCallback, useEffect, useState } from 'react'

import { formatMoney } from '../utils/formatters'
import Pagination from '../components/Pagination'
import {
  createServico,
  deleteServico,
  listServicosPaged,
  updateServico,
} from '../services/servicoService'

const PAGE_SIZE = 30

const EMPTY_FORM = {
  codigo: '',
  nome: '',
  unidade: '',
  preco_unitario_default: '',
  ativo: true,
}

export default function ServicosModule({ token }) {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')

  const load = useCallback(async (p, q) => {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      const res = await listServicosPaged(token, {
        q,
        limit: PAGE_SIZE,
        offset: (p - 1) * PAGE_SIZE,
      })
      setItems(res.items)
      setTotal(res.total)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    load(page, debouncedSearch)
  }, [page, debouncedSearch, load])

  function openCreate() {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setShowForm(true)
    setSuccess('')
    setError('')
  }

  function openEdit(item) {
    setEditingId(item.id_servico)
    setForm({
      codigo: item.codigo ?? '',
      nome: item.nome ?? '',
      unidade: item.unidade ?? '',
      preco_unitario_default: item.preco_unitario_default ?? '',
      ativo: item.ativo ?? true,
    })
    setShowForm(true)
    setSuccess('')
    setError('')
  }

  function cancelForm() {
    setShowForm(false)
    setEditingId(null)
    setForm(EMPTY_FORM)
  }

  function setField(key, value) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')
    const payload = {
      codigo: form.codigo,
      nome: form.nome,
      unidade: form.unidade,
      preco_unitario_default: Number(form.preco_unitario_default),
      ativo: form.ativo,
    }
    try {
      if (editingId) {
        await updateServico(token, editingId, payload)
        setSuccess('Serviço atualizado.')
      } else {
        await createServico(token, payload)
        setSuccess('Serviço criado.')
      }
      cancelForm()
      await load(page, debouncedSearch)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(item) {
    if (!window.confirm(`Eliminar serviço "${item.nome}"?`)) return
    setError('')
    setSuccess('')
    try {
      await deleteServico(token, item.id_servico)
      setSuccess('Serviço eliminado.')
      await load(page, debouncedSearch)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="module-layout">
      <div className="panel">
        <div className="panel-head">
          <h3>Serviços</h3>
          <span>{loading ? 'A carregar...' : `${total} registos`}</span>
        </div>

        {error && <p className="message error">{error}</p>}
        {success && <p className="message success">{success}</p>}

        <div className="module-toolbar">
          <input
            placeholder="Pesquisar código ou nome..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="button" onClick={openCreate}>+ Novo serviço</button>
        </div>

        {showForm && (
          <form className="inline-form" onSubmit={handleSubmit}>
            <div className="form-row">
              <label>
                Código *
                <input value={form.codigo} onChange={(e) => setField('codigo', e.target.value)} required />
              </label>
              <label>
                Nome *
                <input value={form.nome} onChange={(e) => setField('nome', e.target.value)} required />
              </label>
              <label>
                Unidade *
                <input value={form.unidade} onChange={(e) => setField('unidade', e.target.value)} required />
              </label>
              <label>
                Preço unit. *
                <input type="number" step="0.0001" min="0" value={form.preco_unitario_default} onChange={(e) => setField('preco_unitario_default', e.target.value)} required />
              </label>
              <label>
                Ativo
                <select value={String(form.ativo)} onChange={(e) => setField('ativo', e.target.value === 'true')}>
                  <option value="true">Sim</option>
                  <option value="false">Não</option>
                </select>
              </label>
            </div>
            <div className="form-actions">
              <button type="submit" disabled={saving}>{saving ? 'A gravar...' : editingId ? 'Guardar' : 'Criar'}</button>
              <button type="button" className="btn-secondary" onClick={cancelForm}>Cancelar</button>
            </div>
          </form>
        )}

        <div className="table-scroll fit-table-wrap">
          <table className="fit-table servicos-fit">
            <thead>
              <tr>
                <th>ID</th>
                <th>Código</th>
                <th>Nome</th>
                <th>Unidade</th>
                <th>Preço Unit.</th>
                <th>Ativo</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id_servico}>
                  <td>{i.id_servico}</td>
                  <td>{i.codigo}</td>
                  <td>{i.nome}</td>
                  <td>{i.unidade}</td>
                  <td>{formatMoney(i.preco_unitario_default)}</td>
                  <td>{i.ativo ? 'Sim' : 'Não'}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="btn-xs" onClick={() => openEdit(i)}>Editar</button>
                      <button type="button" className="btn-xs btn-danger" onClick={() => handleDelete(i)}>Eliminar</button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && <tr><td colSpan={7}>{loading ? 'A carregar...' : 'Sem serviços.'}</td></tr>}
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
    </div>
  )
}
