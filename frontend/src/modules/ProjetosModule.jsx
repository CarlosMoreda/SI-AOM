import { useCallback, useEffect, useMemo, useState } from 'react'

import { formatDate, formatStatusLabel } from '../utils/formatters'
import Pagination from '../components/Pagination'
import { listClientes } from '../services/clienteService'
import {
  createProject,
  deleteProject,
  listProjectsPaged,
  updateProject,
} from '../services/projectService'

const PAGE_SIZE = 30

const ESTADOS = [
  'em_analise',
  'planeado',
  'aprovado',
  'em_execucao',
  'concluido',
  'cancelado',
]

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
  tratamento_superficie: '',
  numero_pecas: '',
  lead_time: '',
  observacoes: '',
}

export default function ProjetosModule({ token }) {
  const [projects, setProjects] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')

  // Projetos: paginados (server-side). Clientes: lista completa para o
  // dropdown do formulario e para resolver o nome na tabela.
  const loadProjects = useCallback(async (p, q) => {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      const res = await listProjectsPaged(token, {
        q,
        limit: PAGE_SIZE,
        offset: (p - 1) * PAGE_SIZE,
      })
      setProjects(res.items)
      setTotal(res.total)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    if (!token) return
    listClientes(token).then(setClients).catch(() => {})
  }, [token])

  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    loadProjects(page, debouncedSearch)
  }, [page, debouncedSearch, loadProjects])

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
      tratamento_superficie: project.tratamento_superficie ?? '',
      numero_pecas: project.numero_pecas != null ? String(project.numero_pecas) : '',
      lead_time: project.lead_time != null ? String(project.lead_time) : '',
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
      tratamento_superficie: form.tratamento_superficie || null,
      numero_pecas: form.numero_pecas !== '' ? Number(form.numero_pecas) : null,
      lead_time: form.lead_time !== '' ? Number(form.lead_time) : null,
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
      await loadProjects(page, debouncedSearch)
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
      await loadProjects(page, debouncedSearch)
    } catch (e) {
      setError(e.message)
    }
  }

  const clientById = useMemo(
    () => new Map(clients.map((client) => [client.id_cliente, client])),
    [clients],
  )

  return (
    <div className="module-layout">
      <div className="panel">
        <div className="panel-head">
          <h3>Projetos</h3>
          <span>{loading ? 'A carregar...' : `${total} registos`}</span>
        </div>

        {error && <p className="message error">{error}</p>}
        {success && <p className="message success">{success}</p>}

        <div className="module-toolbar">
          <input
            placeholder="Pesquisar referência ou designação..."
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
                Referência *
                <input value={form.referencia} onChange={(e) => setField('referencia', e.target.value)} required />
              </label>
              <label>
                Designação *
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
                    <option key={s} value={s}>{formatStatusLabel(s)}</option>
                  ))}
                </select>
              </label>
              <label>
                Data início
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
              <label>
                Tratamento superfície
                <input value={form.tratamento_superficie} onChange={(e) => setField('tratamento_superficie', e.target.value)} />
              </label>
              <label>
                Número de peças
                <input type="number" min="0" step="1" value={form.numero_pecas} onChange={(e) => setField('numero_pecas', e.target.value)} />
              </label>
              <label>
                Lead time (dias)
                <input type="number" min="0" step="1" value={form.lead_time} onChange={(e) => setField('lead_time', e.target.value)} />
              </label>
            </div>
            <label>
              Observações
              <input value={form.observacoes} onChange={(e) => setField('observacoes', e.target.value)} />
            </label>
            <div className="form-actions">
              <button type="submit" disabled={saving}>
                {saving ? 'A gravar...' : editingId ? 'Guardar alterações' : 'Criar projeto'}
              </button>
              <button type="button" className="btn-secondary" onClick={cancelForm}>
                Cancelar
              </button>
            </div>
          </form>
        )}

        <div className="table-scroll fit-table-wrap">
          <table className="fit-table projetos-fit">
            <thead>
              <tr>
                <th>ID</th>
                <th>Referência</th>
                <th>Designação</th>
                <th>Cliente</th>
                <th>Tipologia</th>
                <th>Estado</th>
                <th>Data Início</th>
                <th>Data de Entrega</th>
                <th>Criado</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr key={p.id_projeto}>
                  <td>{p.id_projeto}</td>
                  <td>{p.referencia}</td>
                  <td>{p.designacao}</td>
                  <td>{clientById.get(p.id_cliente)?.nome || '-'}</td>
                  <td>{p.tipologia || '-'}</td>
                  <td><span className={`badge badge-${p.estado}`}>{formatStatusLabel(p.estado)}</span></td>
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
              {projects.length === 0 && (
                <tr>
                  <td colSpan={10}>{loading ? 'A carregar...' : 'Sem projetos.'}</td>
                </tr>
              )}
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
