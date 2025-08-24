import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { User, Search, Filter, MapPin, Briefcase, ArrowRight, Calendar, Users } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { apiFetch } from '../config/api';

const DeputadosPage = () => {
  const [deputados, setDeputados] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState(null)
  const [filters, setFilters] = useState(null)

  useEffect(() => {
    fetchDeputados()
  }, [page, search])

  const fetchDeputados = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '20',
        active_only: 'false'
      })
      
      if (search) {
        params.append('search', search)
      }

      const response = await apiFetch(`deputados?${params}`)
      const data = await response.json()
      setDeputados(data.deputados || [])
      setPagination(data.pagination)
      setFilters(data.filters)
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
          Deputados Únicos
        </h1>
        <p className="text-gray-600">
          {filters ? (
            <>
              {pagination?.total || 0} pessoas únicas • {filters.total_deputy_records} mandatos totais • {filters.active_deputies_count || 0} deputados ativos
            </>
          ) : 'Carregando...'}
        </p>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <form onSubmit={handleSearch} className="flex space-x-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Pesquisar por nome ou partido..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <Button type="submit" disabled={loading}>
                {loading ? 'Pesquisando...' : 'Pesquisar'}
              </Button>
            </form>
            
            {/* Info Text */}
            <div className="text-xs text-gray-500">
              Mostrando todos os deputados da história parlamentar
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Deputados Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {(deputados || []).map((deputado, index) => (
          <motion.div
            key={`${deputado.deputado_id}-${index}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    {deputado.picture_url ? (
                      <img
                        src={deputado.picture_url}
                        alt={deputado.nome}
                        className="w-16 h-16 rounded-full object-cover bg-gray-200 border-2 border-gray-200"
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.nextSibling.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center" style={{ display: deputado.picture_url ? 'none' : 'flex' }}>
                      <User className="h-8 w-8 text-blue-600" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-lg">
                      {deputado.nome || deputado.nome_completo}
                    </CardTitle>
                    <CardDescription className="flex items-center gap-2 flex-wrap">
                      <span>{deputado.partido_sigla} • {deputado.circulo}</span>
                      {deputado.career_info?.is_currently_active ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Ativo
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          Inativo
                        </span>
                      )}
                      {deputado.career_info?.is_multi_term && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                          <Calendar className="h-3 w-3 mr-1" />
                          {deputado.career_info.total_mandates} mandatos
                        </span>
                      )}
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
                  <div>
                    {deputado.career_info?.is_currently_active ? (
                      <><strong>Mandato Atual:</strong> {deputado.legislatura_nome}</>
                    ) : deputado.career_info?.latest_completed_mandate ? (
                      <><strong>Último mandato:</strong> {deputado.career_info.latest_completed_mandate.legislatura} ({deputado.career_info.latest_completed_mandate.periodo})</>
                    ) : (
                      <><strong>Mandato:</strong> {deputado.legislatura_nome}</>
                    )}
                  </div>
                  {deputado.career_info?.is_multi_term && (
                    <div className="text-xs text-blue-600">
                      <strong>Carreira:</strong> {deputado.career_info.first_mandate}-{deputado.career_info.latest_mandate}
                      {deputado.career_info.parties_served.length > 1 && (
                        <span> • Vários partidos</span>
                      )}
                    </div>
                  )}
                </div>
                <Link
                  to={`/deputados/${deputado.id_cadastro}`}
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

