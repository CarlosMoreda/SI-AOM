const TOKEN_STORAGE_KEY = 'si_aom_token'

export function readToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY) || ''
}

export function writeToken(token) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}
