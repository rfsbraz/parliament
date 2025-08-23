import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { apiFetch } from '../config/api';

const AnalysisPageSimple = () => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      console.log('Fetching data...')
      const response = await apiFetch('estatisticas')
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('Data received:', data)
      setStats(data)
    } catch (error) {
      console.error('Erro ao carregar dados:', error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p>Carregando análises...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Erro</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Erro ao carregar dados: {error}</p>
            <button 
              onClick={() => {
                setError(null)
                setLoading(true)
                fetchData()
              }}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Tentar novamente
            </button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Sem Dados</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Nenhum dado foi carregado.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Análises Avançadas
        </h1>
        <p className="text-gray-600">
          Insights sobre a composição do parlamento português
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">
                {stats.totais?.deputados || 0}
              </div>
              <div className="text-sm opacity-90">
                Total de Deputados
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">
                {stats.totais?.partidos || 0}
              </div>
              <div className="text-sm opacity-90">
                Partidos Representados
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">
                {stats.totais?.circulos || 0}
              </div>
              <div className="text-sm opacity-90">
                Círculos Eleitorais
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Partidos List */}
      <Card>
        <CardHeader>
          <CardTitle>Distribuição por Partido</CardTitle>
          <CardDescription>
            Número de deputados por grupo parlamentar
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {stats.distribuicao_partidos?.map((partido, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-semibold">{partido.sigla}</div>
                  <div className="text-sm text-gray-600">{partido.nome}</div>
                </div>
                <div className="text-xl font-bold text-blue-600">
                  {partido.deputados}
                </div>
              </div>
            )) || <p>Nenhum partido encontrado</p>}
          </div>
        </CardContent>
      </Card>

      {/* Debug Info */}
      <Card>
        <CardHeader>
          <CardTitle>Debug Info</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="text-xs bg-gray-100 p-4 rounded overflow-auto">
            {JSON.stringify(stats, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  )
}

export default AnalysisPageSimple

