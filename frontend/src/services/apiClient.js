export const API_BASE_URL =
  import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

function toApiUrl(path) {
  const base = API_BASE_URL.endsWith('/')
    ? API_BASE_URL.slice(0, -1)
    : API_BASE_URL
  const suffix = path.startsWith('/') ? path : `/${path}`
  return `${base}${suffix}`
}

function friendlyHttpMessage(status) {
  if (status === 401) return 'Sessão expirada. Volta a iniciar sessão.'
  if (status === 403) return 'Sem permissão para executar esta operação.'
  if (status === 404) return 'Recurso não encontrado.'
  if (status === 409) return 'Operação em conflito com o estado atual dos dados.'
  if (status === 422) return 'Dados inválidos. Verifica os campos preenchidos.'
  if (status >= 500) return 'Erro no servidor. Tenta novamente em alguns segundos.'
  return `Erro HTTP ${status}`
}

export class ApiError extends Error {
  constructor(message, { status = 0, code = 'unknown' } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

function buildQuery(params = {}) {
  const usp = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      usp.append(key, value)
    }
  }
  const qs = usp.toString()
  return qs ? `?${qs}` : ''
}

/**
 * GET paginado: devolve { items, total }. O total vem do cabeçalho
 * X-Total-Count (exposto pelo backend), permitindo calcular o nº de páginas.
 */
export async function apiRequestPaged(path, { token, params = {} } = {}) {
  let response
  try {
    response = await fetch(toApiUrl(`${path}${buildQuery(params)}`), {
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    })
  } catch {
    throw new ApiError(
      'Não foi possível contactar o servidor. Verifica a tua ligação ou se o backend está a correr.',
      { status: 0, code: 'network' },
    )
  }

  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    let message = friendlyHttpMessage(response.status)
    if (payload?.detail && typeof payload.detail === 'string') message = payload.detail
    if (response.status === 401 && typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('siaom:unauthorized'))
    }
    throw new ApiError(message, { status: response.status, code: 'http' })
  }

  const totalHeader = response.headers.get('X-Total-Count')
  const items = Array.isArray(payload) ? payload : []
  const total = totalHeader != null ? Number(totalHeader) : items.length
  return { items, total }
}

export async function apiRequest(path, { method = 'GET', token, body } = {}) {
  let response
  try {
    response = await fetch(toApiUrl(path), {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    // fetch lança TypeError quando não consegue contactar o servidor
    // (offline, CORS, backend em baixo, DNS, etc.).
    throw new ApiError(
      'Não foi possível contactar o servidor. Verifica a tua ligação ou se o backend está a correr.',
      { status: 0, code: 'network' },
    )
  }

  const responseType = response.headers.get('content-type') || ''
  const isJson = responseType.includes('application/json')
  const payload = isJson ? await response.json().catch(() => null) : null

  if (!response.ok) {
    let message = friendlyHttpMessage(response.status)
    if (payload?.detail) {
      if (typeof payload.detail === 'string') {
        message = payload.detail
      } else if (Array.isArray(payload.detail)) {
        // FastAPI validation errors: [{loc, msg, type}, ...]
        const msgs = payload.detail
          .map((e) => e.msg || JSON.stringify(e))
          .filter(Boolean)
        if (msgs.length) message = msgs.join('; ')
      }
    }

    // Sessão expirada/inválida: notifica os consumidores (ex: useAuth) para
    // que possam invalidar o token e empurrar o utilizador para o login.
    if (response.status === 401 && typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('siaom:unauthorized'))
    }

    throw new ApiError(message, { status: response.status, code: 'http' })
  }

  return payload
}
