import { useCallback, useEffect, useState } from 'react'

import { formatMoney } from '../utils/formatters'
import {
  createServico,
  deleteServico,
  listServicos,
  updateServico,
} from '../services/servicoService'

const EMPTY_FORM = {
  codigo: '',
  nome: '',
  unidade: '',
  preco_unitario_default: '',
  ativo: true,
}

export default function ServicosModule({ token }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [search, setSearch] = useState('')

  const load = useCallback(async () => {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      setItems(await listServicos(token))
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    load()
  }, [load])

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
        setSuccess('Servico atualizado.')
      } else {
        await createServico(token, payload)
        setSuccess('Servico criado.')
      }
      cancelForm()
      await load()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(item) {
    if (!window.confirm(`Eliminar servico "${item.nome}"?`)) return
    setError('')
    setSuccess('')
    try {
      await deleteServico(token, item.id_servico)
      setSuccess('Servico eliminado.')
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  const filtered = items.filter(
    (i) =>
      !search ||
      i.codigo?.toLowerCase().includes(search.toLowerCase()) ||
      i.nome?.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="module-layout">
      <div className="panel">
        <div className="panel-head">
          <h3>Servicos</h3>
          <span>{loading ? 'A carregar...' : `${items.length} registos`}</span>
        </div>

        {error && <p className="message error">{error}</p>}
        {success && <p className="message success">{success}</p>}

        <div className="module-toolbar">
          <input
            placeholder="Pesquisar codigo ou nome..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="button" onClick={openCreate}>+ Novo servico</button>
        </div>

        {showForm && (
          <form className="inline-form" onSubmit={handleSubmit}>
            <div className="form-row">
              <label>
                Codigo *
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
                Preco unit. *
                <input type="number" step="0.0001" min="0" value={form.preco_unitario_default} onChange={(e) => setField('preco_unitario_default', e.target.value)} required />
              </label>
              <label>
                Ativo
                <select value={String(form.ativo)} onChange={(e) => setField('ativo', e.target.value === 'true')}>
                  <option value="true">Sim</option>
                  <option value="false">Nao</option>
                </select>
              </label>
            </div>
            <div className="form-actions">
              <button type="submit" disabled={saving}>{saving ? 'A gravar...' : editingId ? 'Guardar' : 'Criar'}</button>
              <button type="button" className="btn-secondary" onClick={cancelForm}>Cancelar</button>
            </div>
          </form>
        )}

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Codigo</th>
                <th>Nome</th>
                <th>Unidade</th>
                <th>Preco Unit.</th>
                <th>Ativo</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((i) => (
                <tr key={i.id_servico}>
                  <td>{i.id_servico}</td>
                  <td>{i.codigo}</td>
                  <td>{i.nome}</td>
                  <td>{i.unidade}</td>
                  <td>{formatMoney(i.preco_unitario_default)}</td>
                  <td>{i.ativo ? 'Sim' : 'Nao'}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="btn-xs" onClick={() => openEdit(i)}>Editar</button>
                      <button type="button" className="btn-xs btn-danger" onClick={() => handleDelete(i)}>Eliminar</button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan={7}>Sem servicos.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
