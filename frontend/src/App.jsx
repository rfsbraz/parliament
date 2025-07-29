import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { motion } from 'framer-motion'
import Dashboard from './components/Dashboard'
import DeputadosPage from './components/DeputadosPage'
import DeputadoDetalhes from './components/DeputadoDetalhes'
import PartidosPage from './components/PartidosPage'
import PartidoDetalhes from './components/PartidoDetalhes'
import AgendaPage from './components/AgendaPage'
import AnalysisPageSimple from './components/AnalysisPageSimple'
import Navigation from './components/Navigation'
import { LegislaturaProvider } from './contexts/LegislaturaContext'
import './App.css'

function App() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/estatisticas')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full"
        />
      </div>
    )
  }

  return (
    <LegislaturaProvider>
      <Router>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
          <Navigation />
          
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<Dashboard stats={stats} />} />
              <Route path="/deputados" element={<DeputadosPage />} />
              <Route path="/deputados/:deputadoId" element={<DeputadoDetalhes />} />
              <Route path="/partidos" element={<PartidosPage />} />
              <Route path="/partidos/:partidoId" element={<PartidoDetalhes />} />
              <Route path="/agenda" element={<AgendaPage />} />
              <Route path="/analises" element={<AnalysisPageSimple />} />
            </Routes>
          </main>
        </div>
      </Router>
    </LegislaturaProvider>
  )
}

export default App

