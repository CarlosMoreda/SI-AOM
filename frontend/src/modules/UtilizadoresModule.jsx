import { useCallback, useEffect, useState } from 'react'

import { formatDate } from '../utils/formatters'
import {
  createUtilizador,
  deleteUtilizador,
  listUtilizadores,
  updateUtilizador,
} from '../services/utilizadorService'

const PERFIS = ['administrador', 'orcamentista', 'producao', 'gestor']

const EMPTY_FORM = {
  nome: '',
  email: '',
  password: '',
  perfil: 'orcamentista',
  ativo: true,
}

export default function UtilizadoresModule({ token }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      setItems(await listUtilizadores(token))
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
    setEditingId(item.id_utilizador)
    setForm({
      nome: item.nome ?? '',
      email: item.email ?? '',
      password: '',
      perfil: item.perfil ?? 'orcamentista',
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
    try {
      if (editingId) {
        const payload = {
          nome: form.nome,
          perfil: form.perfil,
          ativo: form.ativo,
        }
        if (form.password) payload.password = form.password
        await updateUtilizador(token, editingId, payload)
        setSuccess('Utilizador atualizado.')
      } else {
        await createUtilizador(token, {
          nome: form.nome,
          email: form.email,
          password: form.password,
          perfil: form.perfil,
          ativo: form.ativo,
        })
        setSuccess('Utilizador criado.')
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
    if (!window.confirm(`Eliminar utilizador "${item.nome}"?`)) return
    setError('')
    setSuccess('')
    try {
      await deleteUtilizador(token, item.id_utilizador)
      setSuccess('Utilizador eliminado.')
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="module-layout">
      <div className="panel">
        <div className="panel-head">
          <h3>Utilizadores</h3>
          <span>{loading ? 'A carregar...' : `${items.length} registos`}</span>
        </div>

        {error && <p className="message error">{error}</p>}
        {success && <p className="message success">{success}</p>}

        <div className="module-toolbar">
          <button type="button" onClick={openCreate}>+ Novo utilizador</button>
        </div>

        {showForm && (
          <form className="inline-form" onSubmit={handleSubmit}>
            <div className="form-row">
              <label>
                Nome *
                <input value={form.nome} onChange={(e) => setField('nome', e.target.value)} required />
              </label>
              {!editingId && (
                <label>
                  Email *
                  <input type="email" value={form.email} onChange={(e) => setField('email', e.target.value)} required />
                </label>
              )}
              <label>
                {editingId ? 'Nova password (opcional)' : 'Password *'}
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setField('password', e.target.value)}
                  required={!editingId}
                />
              </label>
              <label>
                Perfil
                <select value={form.perfil} onChange={(e) => setField('perfil', e.target.value)}>
                  {PERFIS.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
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
                <th>Nome</th>
                <th>Email</th>
                <th>Perfil</th>
                <th>Ativo</th>
                <th>Criado</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id_utilizador}>
                  <td>{i.id_utilizador}</td>
                  <td>{i.nome}</td>
                  <td>{i.email}</td>
                  <td><span className={`badge badge-${i.perfil}`}>{i.perfil}</span></td>
                  <td>{i.ativo ? 'Sim' : 'Nao'}</td>
                  <td>{formatDate(i.criado_em)}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="btn-xs" onClick={() => openEdit(i)}>Editar</button>
                      <button type="button" className="btn-xs btn-danger" onClick={() => handleDelete(i)}>Eliminar</button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && <tr><td colSpan={7}>Sem utilizadores.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
