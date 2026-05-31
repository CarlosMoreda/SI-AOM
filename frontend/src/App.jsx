import { useEffect, useState } from 'react'

import AuthPage from './components/AuthPage'
import DashboardPage from './components/DashboardPage'
import ForgotPasswordPage from './components/ForgotPasswordPage'
import ResetPasswordPage from './components/ResetPasswordPage'
import { useAuth } from './hooks/useAuth'
import { useDashboard } from './hooks/useDashboard'
import './style/auth-page.css'
import './style/dashboard-page.css'

function readResetTokenFromUrl() {
  if (typeof window === 'undefined') return ''
  const params = new URLSearchParams(window.location.search)
  return params.get('reset_token') || ''
}

function clearResetTokenFromUrl() {
  if (typeof window === 'undefined') return
  const url = new URL(window.location.href)
  url.searchParams.delete('reset_token')
  window.history.replaceState({}, '', url.toString())
}

function App() {
  const auth = useAuth()
  const dashboard = useDashboard(auth.token, auth.user?.perfil)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [authView, setAuthView] = useState('login') // 'login' | 'forgot' | 'reset'
  const [resetToken, setResetToken] = useState('')

  useEffect(() => {
    const token = readResetTokenFromUrl()
    if (token) {
      setResetToken(token)
      setAuthView('reset')
    }
  }, [])

  async function handleLogin(event) {
    event.preventDefault()
    const success = await auth.loginWithPassword(email, password)
    if (success) {
      setPassword('')
    }
  }

  function backToLogin() {
    clearResetTokenFromUrl()
    setResetToken('')
    setAuthView('login')
  }

  if (!auth.token) {
    if (authView === 'forgot') {
      return <ForgotPasswordPage onBack={backToLogin} />
    }
    if (authView === 'reset' && resetToken) {
      return <ResetPasswordPage token={resetToken} onDone={backToLogin} />
    }
    return (
      <AuthPage
        email={email}
        password={password}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onSubmit={handleLogin}
        authLoading={auth.authLoading}
        authError={auth.authError}
        onForgotPassword={() => setAuthView('forgot')}
      />
    )
  }

  return (
    <DashboardPage
      user={auth.user}
      token={auth.token}
      authError={auth.authError}
      onLogout={auth.logout}
      projects={dashboard.projects}
      budgets={dashboard.budgets}
      totalOrcado={dashboard.totalOrcado}
      loadingData={dashboard.loadingData}
      dataError={dashboard.dataError}
      selectedProjectId={dashboard.selectedProjectId}
      setSelectedProjectId={dashboard.setSelectedProjectId}
      projectBudgets={dashboard.projectBudgets}
      projectAnalysis={dashboard.projectAnalysis}
      projectAnalysisLoading={dashboard.projectAnalysisLoading}
      projectAnalysisError={dashboard.projectAnalysisError}
      budgetRealTotals={dashboard.budgetRealTotals}
      budgetRealLoading={dashboard.budgetRealLoading}
      budgetRealError={dashboard.budgetRealError}
    />
  )
}

export default App
