import { useCallback, useEffect, useState } from 'react'

import { formatMoney } from '../utils/formatters'
import Pagination from '../components/Pagination'
import {
  createMaterial,
  deleteMaterial,
  listMateriaisPaged,
  updateMaterial,
} from '../services/materialService'

const PAGE_SIZE = 30

const EMPTY_FORM = {
  codigo: '',
  nome: '',
  unidade: '',
  tipo: '',
  qualidade_material: '',
  custo_unitario_default: '',
  ativo: true,
}

export default function MateriaisModule({ token }) {
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
      const res = await listMateriaisPaged(token, {
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

  // Debounce da pesquisa: ao mudar, volta à página 1.
  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(t)
  }, [search])

  // Fetch sempre que a página ou a pesquisa (debounced) mudam.
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
    setEditingId(item.id_material)
    setForm({
      codigo: item.codigo ?? '',
      nome: item.nome ?? '',
      unidade: item.unidade ?? '',
      tipo: item.tipo ?? '',
      qualidade_material: item.qualidade_material ?? '',
      custo_unitario_default: item.custo_unitario_default ?? '',
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
      tipo: form.tipo || null,
      qualidade_material: form.qualidade_material || null,
      custo_unitario_default: Number(form.custo_unitario_default),
      ativo: form.ativo,
    }
    try {
      if (editingId) {
        await updateMaterial(token, editingId, payload)
        setSuccess('Material atualizado.')
      } else {
        await createMaterial(token, payload)
        setSuccess('Material criado.')
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
    if (!window.confirm(`Eliminar material "${item.nome}"?`)) return
    setError('')
    setSuccess('')
    try {
      await deleteMaterial(token, item.id_material)
      setSuccess('Material eliminado.')
      await load(page, debouncedSearch)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="module-layout">
      <div className="panel">
        <div className="panel-head">
          <h3>Materiais</h3>
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
          <button type="button" onClick={openCreate}>+ Novo material</button>
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
                Tipo
                <input value={form.tipo} onChange={(e) => setField('tipo', e.target.value)} />
              </label>
              <label>
                Qualidade
                <input value={form.qualidade_material} onChange={(e) => setField('qualidade_material', e.target.value)} />
              </label>
              <label>
                Custo unit. *
                <input type="number" step="0.0001" min="0" value={form.custo_unitario_default} onChange={(e) => setField('custo_unitario_default', e.target.value)} required />
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
          <table className="fit-table materiais-fit">
            <thead>
              <tr>
                <th>ID</th>
                <th>Código</th>
                <th>Nome</th>
                <th>Unidade</th>
                <th>Tipo</th>
                <th>Qualidade</th>
                <th>Custo Unit.</th>
                <th>Ativo</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id_material}>
                  <td>{i.id_material}</td>
                  <td>{i.codigo}</td>
                  <td>{i.nome}</td>
                  <td>{i.unidade}</td>
                  <td>{i.tipo || '-'}</td>
                  <td>{i.qualidade_material || '-'}</td>
                  <td>{formatMoney(i.custo_unitario_default)}</td>
                  <td>{i.ativo ? 'Sim' : 'Não'}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="btn-xs" onClick={() => openEdit(i)}>Editar</button>
                      <button type="button" className="btn-xs btn-danger" onClick={() => handleDelete(i)}>Eliminar</button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && <tr><td colSpan={9}>{loading ? 'A carregar...' : 'Sem materiais.'}</td></tr>}
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
