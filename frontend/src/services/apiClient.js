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
  if (status === 401) return 'Sessao expirada. Volta a iniciar sessao.'
  if (status === 403) return 'Sem permissao para executar esta operacao.'
  if (status === 404) return 'Recurso nao encontrado.'
  if (status === 409) return 'Operacao em conflito com o estado actual dos dados.'
  if (status === 422) return 'Dados invalidos. Verifica os campos preenchidos.'
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
    // fetch lanca TypeError quando nao consegue contactar o servidor
    // (offline, CORS, backend em baixo, DNS, etc.).
    throw new ApiError(
      'Nao foi possivel contactar o servidor. Verifica a tua ligacao ou se o backend esta a correr.',
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

    // Sessao expirada/invalida: notifica os consumidores (ex: useAuth) para
    // que possam invalidar o token e empurrar o utilizador para o login.
    if (response.status === 401 && typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('siaom:unauthorized'))
    }

    throw new ApiError(message, { status: response.status, code: 'http' })
  }

  return payload
}
