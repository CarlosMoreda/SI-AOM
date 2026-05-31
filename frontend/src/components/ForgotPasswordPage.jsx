import { useState } from 'react'

import { requestPasswordReset } from '../services/passwordResetService'

export default function ForgotPasswordPage({ onBack }) {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [info, setInfo] = useState('')
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setInfo('')
    setError('')
    try {
      const res = await requestPasswordReset(email.trim())
      setInfo(res.mensagem || 'Pedido enviado.')
    } catch (e) {
      setError(e.message || 'Nao foi possivel pedir a recuperacao.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="eyebrow">SI-AOM</p>
        <h1>Recuperar Password</h1>
        <p className="subtitle">
          Indica o teu email. Se existir uma conta associada, vais receber um link para
          definir uma nova password.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoComplete="username"
            />
          </label>

          <button type="submit" disabled={loading}>
            {loading ? 'A enviar...' : 'Enviar link de recuperacao'}
          </button>
        </form>

        {info && <p className="message success">{info}</p>}
        {error && <p className="message error">{error}</p>}

        <p className="auth-secondary">
          <button type="button" className="link-button" onClick={onBack}>
            Voltar ao login
          </button>
        </p>
      </section>
    </main>
  )
}
