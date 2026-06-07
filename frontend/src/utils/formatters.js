export function formatMoney(value) {
  const parsed = Number(value ?? 0)
  return new Intl.NumberFormat('pt-PT', {
    style: 'currency',
    currency: 'EUR',
  }).format(Number.isFinite(parsed) ? parsed : 0)
}

export function formatDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('pt-PT').format(date)
}

const STATUS_LABELS = {
  em_analise: 'Em análise',
  planeado: 'Planeado',
  aprovado: 'Aprovado',
  em_execucao: 'Em execução',
  concluido: 'Concluído',
  cancelado: 'Cancelado',
  em_preparacao: 'Em preparação',
  em_revisao: 'Em revisão',
  validado: 'Validado',
  enviado: 'Enviado',
  adjudicado: 'Adjudicado',
  rejeitado: 'Rejeitado',
  arquivado: 'Arquivado',
  sem_estado: 'Sem estado',
}

export function formatStatusLabel(value) {
  if (!value) return '-'

  const raw = String(value).trim()
  const key = raw.toLowerCase()
  if (STATUS_LABELS[key]) return STATUS_LABELS[key]

  const readable = raw.replaceAll('_', ' ').replace(/\s+/g, ' ')
  return readable.charAt(0).toUpperCase() + readable.slice(1)
}

export function formatVersionLabel(value) {
  const raw = String(value ?? '').trim()
  if (!raw) return '-'
  return raw.toLowerCase().startsWith('v') ? raw : `v${raw}`
}
