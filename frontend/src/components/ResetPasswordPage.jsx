import { useState } from 'react'

import { confirmPasswordReset } from '../services/passwordResetService'

export default function ResetPasswordPage({ token, onDone }) {
  const [novaPassword, setNovaPassword] = useState('')
  const [confirmar, setConfirmar] = useState('')
  const [loading, setLoading] = useState(false)
  const [info, setInfo] = useState('')
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setInfo('')

    if (novaPassword.length < 8) {
      setError('A password deve ter pelo menos 8 caracteres.')
      return
    }
    if (novaPassword !== confirmar) {
      setError('As passwords nao coincidem.')
      return
    }

    setLoading(true)
    try {
      const res = await confirmPasswordReset(token, novaPassword)
      setInfo(res.mensagem || 'Password atualizada.')
      setTimeout(() => onDone(), 1500)
    } catch (e) {
      setError(e.message || 'Nao foi possivel redefinir a password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="eyebrow">SI-AOM</p>
        <h1>Definir Nova Password</h1>
        <p className="subtitle">
          Introduz a nova password para a tua conta. O link de recuperacao so pode ser
          utilizado uma vez.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Nova password
            <input
              type="password"
              value={novaPassword}
              onChange={(event) => setNovaPassword(event.target.value)}
              required
              minLength={8}
              maxLength={72}
              autoComplete="new-password"
            />
          </label>
          <label>
            Confirmar password
            <input
              type="password"
              value={confirmar}
              onChange={(event) => setConfirmar(event.target.value)}
              required
              minLength={8}
              maxLength={72}
              autoComplete="new-password"
            />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? 'A guardar...' : 'Atualizar password'}
          </button>
        </form>

        {info && <p className="message success">{info}</p>}
        {error && <p className="message error">{error}</p>}

        <p className="auth-secondary">
          <button type="button" className="link-button" onClick={onDone}>
            Voltar ao login
          </button>
        </p>
      </section>
    </main>
  )
}
