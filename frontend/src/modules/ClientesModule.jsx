import { useCallback, useEffect, useState } from 'react'

import { formatDate } from '../utils/formatters'
import Pagination from '../components/Pagination'
import {
  createCliente,
  deleteCliente,
  listClientesPaged,
  updateCliente,
} from '../services/clienteService'

const PAGE_SIZE = 30

const EMPTY_FORM = {
  nome: '',
  nif: '',
  email: '',
  telefone: '',
  morada: '',
  observacoes: '',
  ativo: true,
}

function emptyToNull(value) {
  const normalized = String(value ?? '').trim()
  return normalized ? normalized : null
}

export default function ClientesModule({ token }) {
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
      const res = await listClientesPaged(token, {
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
    setEditingId(item.id_cliente)
    setForm({
      nome: item.nome ?? '',
      nif: item.nif ?? '',
      email: item.email ?? '',
      telefone: item.telefone ?? '',
      morada: item.morada ?? '',
      observacoes: item.observacoes ?? '',
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
      nome: form.nome.trim(),
      nif: emptyToNull(form.nif),
      email: emptyToNull(form.email),
      telefone: emptyToNull(form.telefone),
      morada: emptyToNull(form.morada),
      observacoes: emptyToNull(form.observacoes),
      ativo: form.ativo,
    }

    try {
      if (editingId) {
        await updateCliente(token, editingId, payload)
        setSuccess('Cliente atualizado.')
      } else {
        await createCliente(token, payload)
        setSuccess('Cliente criado.')
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
    if (!window.confirm(`Eliminar cliente "${item.nome}"?`)) return
    setError('')
    setSuccess('')
    try {
      await deleteCliente(token, item.id_cliente)
      setSuccess('Cliente eliminado.')
      await load(page, debouncedSearch)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="module-layout">
      <div className="panel">
        <div className="panel-head">
          <h3>Clientes</h3>
          <span>{loading ? 'A carregar...' : `${total} registos`}</span>
        </div>

        {error && <p className="message error">{error}</p>}
        {success && <p className="message success">{success}</p>}

        <div className="module-toolbar">
          <input
            placeholder="Pesquisar nome, NIF ou e-mail..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="button" onClick={openCreate}>+ Novo cliente</button>
        </div>

        {showForm && (
          <form className="inline-form" onSubmit={handleSubmit}>
            <div className="form-row">
              <label>
                Nome *
                <input value={form.nome} onChange={(e) => setField('nome', e.target.value)} required />
              </label>
              <label>
                NIF
                <input value={form.nif} onChange={(e) => setField('nif', e.target.value)} />
              </label>
              <label>
                E-mail
                <input type="email" value={form.email} onChange={(e) => setField('email', e.target.value)} />
              </label>
              <label>
                Telefone
                <input value={form.telefone} onChange={(e) => setField('telefone', e.target.value)} />
              </label>
              <label>
                Ativo
                <select value={String(form.ativo)} onChange={(e) => setField('ativo', e.target.value === 'true')}>
                  <option value="true">Sim</option>
                  <option value="false">Não</option>
                </select>
              </label>
            </div>
            <label>
              Morada
              <input value={form.morada} onChange={(e) => setField('morada', e.target.value)} />
            </label>
            <label>
              Observações
              <input value={form.observacoes} onChange={(e) => setField('observacoes', e.target.value)} />
            </label>
            <div className="form-actions">
              <button type="submit" disabled={saving}>
                {saving ? 'A gravar...' : editingId ? 'Guardar alterações' : 'Criar cliente'}
              </button>
              <button type="button" className="btn-secondary" onClick={cancelForm}>Cancelar</button>
            </div>
          </form>
        )}

        <div className="table-scroll fit-table-wrap">
          <table className="fit-table clientes-fit">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nome</th>
                <th>NIF</th>
                <th>E-mail</th>
                <th>Telefone</th>
                <th>Morada</th>
                <th>Ativo</th>
                <th>Criado</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id_cliente}>
                  <td>{i.id_cliente}</td>
                  <td>{i.nome}</td>
                  <td>{i.nif || '-'}</td>
                  <td>{i.email || '-'}</td>
                  <td>{i.telefone || '-'}</td>
                  <td>{i.morada || '-'}</td>
                  <td>{i.ativo ? 'Sim' : 'Não'}</td>
                  <td>{formatDate(i.criado_em)}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="btn-xs" onClick={() => openEdit(i)}>Editar</button>
                      <button type="button" className="btn-xs btn-danger" onClick={() => handleDelete(i)}>Eliminar</button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && <tr><td colSpan={9}>{loading ? 'A carregar...' : 'Sem clientes.'}</td></tr>}
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
