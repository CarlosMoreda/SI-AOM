export const API_BASE_URL =
  import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

function toApiUrl(path) {
  const base = API_BASE_URL.endsWith('/')
    ? API_BASE_URL.slice(0, -1)
    : API_BASE_URL
  const suffix = path.startsWith('/') ? path : `/${path}`
  return `${base}${suffix}`
}

export async function apiRequest(path, { method = 'GET', token, body } = {}) {
  const response = await fetch(toApiUrl(path), {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  const responseType = response.headers.get('content-type') || ''
  const isJson = responseType.includes('application/json')
  const payload = isJson ? await response.json() : null

  if (!response.ok) {
    let message = `Erro HTTP ${response.status}`
    if (payload?.detail) {
      if (typeof payload.detail === 'string') {
        message = payload.detail
      } else if (Array.isArray(payload.detail)) {
        // FastAPI validation errors: [{loc, msg, type}, ...]
        message = payload.detail.map((e) => e.msg || JSON.stringify(e)).join('; ')
      } else {
        message = JSON.stringify(payload.detail)
      }
    }
    throw new Error(message)
  }

  return payload
}
