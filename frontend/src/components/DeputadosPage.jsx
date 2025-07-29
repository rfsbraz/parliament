import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { User, Search, Filter, MapPin, Briefcase, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useLegislatura } from '../contexts/LegislaturaContext';

const DeputadosPage = () => {
  const [deputados, setDeputados] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState(null)
  const { selectedLegislatura } = useLegislatura()

  useEffect(() => {
    if (selectedLegislatura) {
      fetchDeputados()
    }
  }, [page, search, selectedLegislatura])

  const fetchDeputados = async () => {
    if (!selectedLegislatura) return
    
    try {
      setLoading(true)
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '20',
        legislatura: selectedLegislatura.numero.toString()
      })
      
      if (search) {
        params.append('search', search)
      }

      const response = await fetch(`/api/deputados?${params}`)
      const data = await response.json()
      setDeputados(data.deputados || [])
      setPagination(data.pagination)
    } catch (error) {
      console.error('Erro ao carregar deputados:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    fetchDeputados()
  }

  if (loading && (deputados || []).length === 0) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"
        />
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Deputados
        </h1>
        <p className="text-gray-600">
          {pagination ? `${pagination.total} deputados` : 'Carregando...'}
        </p>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="flex space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Pesquisar por nome..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <Button type="submit" disabled={loading}>
              {loading ? 'Pesquisando...' : 'Pesquisar'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Deputados Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {(deputados || []).map((deputado, index) => (
          <motion.div
            key={deputado.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center space-x-4">
                  {deputado.picture_url && (
                    <img
                      src={deputado.picture_url}
                      alt={deputado.nome}
                      className="w-16 h-16 rounded-full object-cover bg-gray-200"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  )}
                  <div className="flex-1">
                    <CardTitle className="text-lg">
                      {deputado.nome || deputado.nome_completo}
                    </CardTitle>
                    <CardDescription>
                      {deputado.partido?.sigla} • {deputado.circulo}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm text-gray-600 mb-4">
                  {deputado.profissao && (
                    <div>
                      <strong>Profissão:</strong> {deputado.profissao}
                    </div>
                  )}
                  {deputado.partido && (
                    <div>
                      <strong>Partido:</strong> {deputado.partido.nome}
                    </div>
                  )}
                </div>
                <Link
                  to={`/deputados/${deputado.id}`}
                  className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium text-sm transition-colors"
                >
                  Ver Detalhes
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Pagination */}
      {pagination && pagination.pages > 1 && (
        <div className="flex justify-center space-x-2">
          <Button
            variant="outline"
            disabled={!pagination.has_prev}
            onClick={() => setPage(page - 1)}
          >
            Anterior
          </Button>
          <span className="flex items-center px-4 py-2 text-sm text-gray-600">
            Página {pagination.page} de {pagination.pages}
          </span>
          <Button
            variant="outline"
            disabled={!pagination.has_next}
            onClick={() => setPage(page + 1)}
          >
            Próxima
          </Button>
        </div>
      )}
    </motion.div>
  )
}

export default DeputadosPage

