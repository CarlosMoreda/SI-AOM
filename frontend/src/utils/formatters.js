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
