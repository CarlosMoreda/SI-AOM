import { useCallback, useEffect, useState } from 'react'

import { clearToken, readToken, writeToken } from '../services/tokenStorage'
import { getCurrentUser, login } from '../services/authService'

export function useAuth() {
  const [token, setToken] = useState(() => readToken())
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState('')

  const logout = useCallback(() => {
    clearToken()
    setToken('')
    setUser(null)
  }, [])

  const loginWithPassword = useCallback(async (email, password) => {
    setAuthLoading(true)
    setAuthError('')
    try {
      const payload = await login(email, password)
      writeToken(payload.access_token)
      setToken(payload.access_token)
      return true
    } catch (err) {
      setAuthError(err.message || 'Credenciais inválidas')
      return false
    } finally {
      setAuthLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!token) return

    let ignore = false

    const syncSession = async () => {
      setAuthLoading(true)
      setAuthError('')
      try {
        const me = await getCurrentUser(token)
        if (!ignore) setUser(me)
      } catch (err) {
        if (ignore) return
        clearToken()
        setToken('')
        setUser(null)
        setAuthError(err.message || 'Sessão inválida')
      } finally {
        if (!ignore) setAuthLoading(false)
      }
    }

    syncSession()

    return () => {
      ignore = true
    }
  }, [token])

  // Se qualquer chamada da API devolver 401, o apiClient emite este evento
  // e a sessão é terminada automaticamente.
  useEffect(() => {
    const handler = () => {
      clearToken()
      setToken('')
      setUser(null)
      setAuthError('Sessão expirada. Volta a iniciar sessão.')
    }
    window.addEventListener('siaom:unauthorized', handler)
    return () => window.removeEventListener('siaom:unauthorized', handler)
  }, [])

  return {
    token,
    user,
    authLoading,
    authError,
    loginWithPassword,
    logout,
  }
}
