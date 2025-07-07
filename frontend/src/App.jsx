import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import { Layout } from './components/Layout'
import IntegratedDashboard from './pages/IntegratedDashboard'
import { StatementDetail } from './pages/StatementDetail'
import { Upload } from './pages/Upload'
import { ThemeProvider } from './contexts/ThemeContext'

function App() {
  return (
    <ThemeProvider>
      <div className="min-h-screen bg-background text-foreground transition-colors duration-200">
        <ErrorBoundary fallbackMessage="La aplicación ha encontrado un problema. Por favor, recarga la página.">
          <Router>
            <Layout>
              <Routes>
                <Route path="/" element={<IntegratedDashboard />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="/statements" element={<Navigate to="/" replace />} />
                <Route path="/statements/:id" element={<StatementDetail />} />
              </Routes>
            </Layout>
          </Router>
        </ErrorBoundary>
      </div>
    </ThemeProvider>
  )
}

export default App