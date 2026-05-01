import { useCallback, useEffect, useState } from 'react'

import { formatMoney } from '../utils/formatters'
import {
  createOperacao,
  deleteOperacao,
  listOperacoes,
  updateOperacao,
} from '../services/operacaoService'

const EMPTY_FORM = {
  codigo: '',
  nome: '',
  categoria: '',
  custo_hora_default: '',
  setup_hora_default: '0',
  ativo: true,
}

export default function OperacoesModule({ token }) {
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
      setItems(await listOperacoes(token))
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
    setEditingId(item.id_operacao)
    setForm({
      codigo: item.codigo ?? '',
      nome: item.nome ?? '',
      categoria: item.categoria ?? '',
      custo_hora_default: item.custo_hora_default ?? '',
      setup_hora_default: item.setup_hora_default ?? '0',
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
      categoria: form.categoria || null,
      custo_hora_default: Number(form.custo_hora_default),
      setup_hora_default: Number(form.setup_hora_default || 0),
      ativo: form.ativo,
    }
    try {
      if (editingId) {
        await updateOperacao(token, editingId, payload)
        setSuccess('Operacao atualizada.')
      } else {
        await createOperacao(token, payload)
        setSuccess('Operacao criada.')
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
    if (!window.confirm(`Eliminar operacao "${item.nome}"?`)) return
    setError('')
    setSuccess('')
    try {
      await deleteOperacao(token, item.id_operacao)
      setSuccess('Operacao eliminada.')
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
          <h3>Operacoes</h3>
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
          <button type="button" onClick={openCreate}>+ Nova operacao</button>
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
                Categoria
                <input value={form.categoria} onChange={(e) => setField('categoria', e.target.value)} />
              </label>
              <label>
                Custo/hora *
                <input type="number" step="0.01" min="0" value={form.custo_hora_default} onChange={(e) => setField('custo_hora_default', e.target.value)} required />
              </label>
              <label>
                Setup hora
                <input type="number" step="0.01" min="0" value={form.setup_hora_default} onChange={(e) => setField('setup_hora_default', e.target.value)} />
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
                <th>Categoria</th>
                <th>Custo/hora</th>
                <th>Setup h</th>
                <th>Ativo</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((i) => (
                <tr key={i.id_operacao}>
                  <td>{i.id_operacao}</td>
                  <td>{i.codigo}</td>
                  <td>{i.nome}</td>
                  <td>{i.categoria || '-'}</td>
                  <td>{formatMoney(i.custo_hora_default)}</td>
                  <td>{i.setup_hora_default}</td>
                  <td>{i.ativo ? 'Sim' : 'Nao'}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="btn-xs" onClick={() => openEdit(i)}>Editar</button>
                      <button type="button" className="btn-xs btn-danger" onClick={() => handleDelete(i)}>Eliminar</button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan={8}>Sem operacoes.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
