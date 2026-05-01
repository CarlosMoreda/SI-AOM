import { useState } from 'react'

import AuthPage from './components/AuthPage'
import DashboardPage from './components/DashboardPage'
import { useAuth } from './hooks/useAuth'
import { useDashboard } from './hooks/useDashboard'
import './style/auth-page.css'
import './style/dashboard-page.css'

function App() {
  const auth = useAuth()
  const dashboard = useDashboard(auth.token, auth.user?.perfil)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  async function handleLogin(event) {
    event.preventDefault()
    const success = await auth.loginWithPassword(email, password)
    if (success) {
      setPassword('')
    }
  }

  if (!auth.token) {
    return (
      <AuthPage
        email={email}
        password={password}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onSubmit={handleLogin}
        authLoading={auth.authLoading}
        authError={auth.authError}
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
