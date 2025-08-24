import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ExternalLink, AlertTriangle, X } from 'lucide-react'
import Dashboard from './components/Dashboard'
import DeputadosPage from './components/DeputadosPage'
import DeputadoDetalhes from './components/DeputadoDetalhes'
import PartidosPage from './components/PartidosPage'
import PartidoDetalhes from './components/PartidoDetalhes'
import ColigacaoDetalhes from './components/ColigacaoDetalhes'
import AgendaPage from './components/AgendaPage'
import TransparenciaPage from './components/TransparenciaPage'
import Navigation from './components/Navigation'
import { apiFetch } from './config/api'
import './App.css'

const AppContent = () => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showBanner, setShowBanner] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      // Get overall statistics instead of per-legislatura
      const response = await apiFetch('estatisticas')
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
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Navigation />
        
        {/* Construction Banner */}
        {showBanner && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-amber-500 border-b-2 border-amber-600 shadow-lg"
          >
            <div className="container mx-auto px-4 py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="h-5 w-5 text-amber-900 flex-shrink-0" />
                  <div className="text-amber-900">
                    <p className="font-semibold text-sm sm:text-base">
                      🚧 Website em Desenvolvimento
                    </p>
                    <p className="text-xs sm:text-sm opacity-90">
                      Este portal encontra-se em fase de desenvolvimento. Os dados apresentados são meramente demonstrativos e não devem ser considerados oficiais ou definitivos.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowBanner(false)}
                  className="ml-4 p-1 rounded-md text-amber-900 hover:bg-amber-400 transition-colors flex-shrink-0"
                  aria-label="Fechar aviso"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
        
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard stats={stats} />} />
            <Route path="/deputados" element={<DeputadosPage />} />
            <Route path="/deputados/:cadId" element={<DeputadoDetalhes />} />
            <Route path="/partidos" element={<PartidosPage />} />
            <Route path="/partidos/:partidoId" element={<PartidoDetalhes />} />
            <Route path="/coligacoes/:coligacaoId" element={<ColigacaoDetalhes />} />
            <Route path="/agenda" element={<AgendaPage />} />
            <Route path="/transparencia" element={<TransparenciaPage />} />
          </Routes>
        </main>

          {/* Footer */}
          <footer className="bg-white border-t border-gray-200 mt-auto">
            <div className="container mx-auto px-4 py-6">
              <div className="text-center text-sm text-gray-600">
                <p className="mb-2">
                  Dados do Parlamento por
                </p>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4 text-blue-600">
                  <a 
                    href="https://www.parlamento.pt/Cidadania/paginas/dadosabertos.aspx" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center hover:text-blue-800 transition-colors"
                  >
                    <ExternalLink className="h-4 w-4 mr-1" />
                    Dados Abertos do Parlamento
                  </a>
                  <span className="hidden sm:inline text-gray-400">•</span>
                  <a 
                    href="https://av.parlamento.pt/" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center hover:text-blue-800 transition-colors"
                  >
                    <ExternalLink className="h-4 w-4 mr-1" />
                    Canal Parlamento
                  </a>
                </div>
              </div>
            </div>
          </footer>
        </div>
      </Router>
  )
}

function App() {
  return <AppContent />
}

export default App

