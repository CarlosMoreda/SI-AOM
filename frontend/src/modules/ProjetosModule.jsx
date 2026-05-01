import { useCallback, useEffect, useMemo, useState } from 'react'

import { formatDate } from '../utils/formatters'
import { listClientes } from '../services/clienteService'
import {
  createProject,
  deleteProject,
  listProjects,
  updateProject,
} from '../services/projectService'

const ESTADOS = ['em_analise', 'aprovado', 'em_execucao', 'concluido']

const EMPTY_FORM = {
  referencia: '',
  designacao: '',
  id_cliente: '',
  tipologia: '',
  estado: 'em_analise',
  data_inicio: '',
  data_entrega_prevista: '',
  complexidade: '',
  material_principal: '',
  observacoes: '',
}

export default function ProjetosModule({ token }) {
  const [projects, setProjects] = useState([])
  const [clients, setClients] = useState([])
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
      const [projectRows, clientRows] = await Promise.all([
        listProjects(token),
        listClientes(token),
      ])
      setProjects(projectRows)
      setClients(clientRows)
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

  function openEdit(project) {
    setEditingId(project.id_projeto)
    setForm({
      referencia: project.referencia ?? '',
      designacao: project.designacao ?? '',
      id_cliente: project.id_cliente ? String(project.id_cliente) : '',
      tipologia: project.tipologia ?? '',
      estado: project.estado ?? 'em_analise',
      data_inicio: project.data_inicio ?? '',
      data_entrega_prevista: project.data_entrega_prevista ?? '',
      complexidade: project.complexidade ?? '',
      material_principal: project.material_principal ?? '',
      observacoes: project.observacoes ?? '',
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
      referencia: form.referencia,
      designacao: form.designacao,
      id_cliente: form.id_cliente ? Number(form.id_cliente) : null,
      tipologia: form.tipologia || null,
      estado: form.estado,
      data_inicio: form.data_inicio || null,
      data_entrega_prevista: form.data_entrega_prevista || null,
      complexidade: form.complexidade || null,
      material_principal: form.material_principal || null,
      observacoes: form.observacoes || null,
    }

    try {
      if (editingId) {
        await updateProject(token, editingId, payload)
        setSuccess('Projeto atualizado.')
      } else {
        await createProject(token, payload)
        setSuccess('Projeto criado.')
      }
      cancelForm()
      await load()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(project) {
    if (!window.confirm(`Eliminar projeto #${project.id_projeto} "${project.designacao}"?`)) return
    setError('')
    setSuccess('')
    try {
      await deleteProject(token, project.id_projeto)
      setSuccess('Projeto eliminado.')
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  const clientById = useMemo(
    () => new Map(clients.map((client) => [client.id_cliente, client])),
    [clients],
  )

  const normalizedSearch = search.toLowerCase()
  const filtered = projects.filter((p) => {
    const clientName = clientById.get(p.id_cliente)?.nome || ''

    return (
      !normalizedSearch ||
      p.referencia?.toLowerCase().includes(normalizedSearch) ||
      p.designacao?.toLowerCase().includes(normalizedSearch) ||
      clientName.toLowerCase().includes(normalizedSearch)
    )
  })

  return (
    <div className="module-layout">
      <div className="panel">
        <div className="panel-head">
          <h3>Projetos</h3>
          <span>{loading ? 'A carregar...' : `${projects.length} registos`}</span>
        </div>

        {error && <p className="message error">{error}</p>}
        {success && <p className="message success">{success}</p>}

        <div className="module-toolbar">
          <input
            placeholder="Pesquisar referencia ou designacao..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="button" onClick={openCreate}>
            + Novo projeto
          </button>
        </div>

        {showForm && (
          <form className="inline-form" onSubmit={handleSubmit}>
            <div className="form-row">
              <label>
                Referencia *
                <input value={form.referencia} onChange={(e) => setField('referencia', e.target.value)} required />
              </label>
              <label>
                Designacao *
                <input value={form.designacao} onChange={(e) => setField('designacao', e.target.value)} required />
              </label>
              <label>
                Cliente
                <select value={form.id_cliente} onChange={(e) => setField('id_cliente', e.target.value)}>
                  <option value="">Sem cliente associado</option>
                  {clients.map((client) => (
                    <option key={client.id_cliente} value={client.id_cliente}>
                      {client.nome}{client.ativo ? '' : ' (inativo)'}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Tipologia
                <input value={form.tipologia} onChange={(e) => setField('tipologia', e.target.value)} />
              </label>
              <label>
                Estado
                <select value={form.estado} onChange={(e) => setField('estado', e.target.value)}>
                  {ESTADOS.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </label>
              <label>
                Data inicio
                <input type="date" value={form.data_inicio} onChange={(e) => setField('data_inicio', e.target.value)} />
              </label>
              <label>
                Data entrega prevista
                <input type="date" value={form.data_entrega_prevista} onChange={(e) => setField('data_entrega_prevista', e.target.value)} />
              </label>
              <label>
                Complexidade
                <input value={form.complexidade} onChange={(e) => setField('complexidade', e.target.value)} />
              </label>
              <label>
                Material principal
                <input value={form.material_principal} onChange={(e) => setField('material_principal', e.target.value)} />
              </label>
            </div>
            <label>
              Observacoes
              <input value={form.observacoes} onChange={(e) => setField('observacoes', e.target.value)} />
            </label>
            <div className="form-actions">
              <button type="submit" disabled={saving}>
                {saving ? 'A gravar...' : editingId ? 'Guardar alteracoes' : 'Criar projeto'}
              </button>
              <button type="button" className="btn-secondary" onClick={cancelForm}>
                Cancelar
              </button>
            </div>
          </form>
        )}

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Referencia</th>
                <th>Designacao</th>
                <th>Cliente</th>
                <th>Tipologia</th>
                <th>Estado</th>
                <th>Data Inicio</th>
                <th>Data Entrega</th>
                <th>Criado</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id_projeto}>
                  <td>{p.id_projeto}</td>
                  <td>{p.referencia}</td>
                  <td>{p.designacao}</td>
                  <td>{clientById.get(p.id_cliente)?.nome || '-'}</td>
                  <td>{p.tipologia || '-'}</td>
                  <td><span className={`badge badge-${p.estado}`}>{p.estado}</span></td>
                  <td>{formatDate(p.data_inicio)}</td>
                  <td>{formatDate(p.data_entrega_prevista)}</td>
                  <td>{formatDate(p.criado_em)}</td>
                  <td>
                    <div className="row-actions">
                      <button type="button" className="btn-xs" onClick={() => openEdit(p)}>Editar</button>
                      <button type="button" className="btn-xs btn-danger" onClick={() => handleDelete(p)}>Eliminar</button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={10}>Sem projetos.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
