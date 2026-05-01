export default function AuthPage({
  email,
  password,
  onEmailChange,
  onPasswordChange,
  onSubmit,
  authLoading,
  authError,
}) {
  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="eyebrow">SI-AOM</p>
        <h1>Painel de Orcamentacao e Producao</h1>
        <p className="subtitle">Entra com a tua conta para gerir projetos e orcamentos.</p>

        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => onEmailChange(event.target.value)}
              required
              autoComplete="username"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => onPasswordChange(event.target.value)}
              required
              autoComplete="current-password"
            />
          </label>

          <button type="submit" disabled={authLoading}>
            {authLoading ? 'A autenticar...' : 'Entrar'}
          </button>
        </form>

        {authError && <p className="message error">{authError}</p>}
      </section>
    </main>
  )
}
