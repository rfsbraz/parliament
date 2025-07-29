import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Users, Building, MapPin, TrendingUp, Crown, Award, Sparkles, BarChart3 } from 'lucide-react'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const Dashboard = ({ stats }) => {
  if (!stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">Carregando Dashboard...</h2>
          <p className="text-gray-600">Por favor, aguarde enquanto carregamos os dados.</p>
        </div>
      </div>
    )
  }

  const { totais = {}, distribuicao_partidos = [], distribuicao_circulos = [] } = stats

  // Cores para os partidos
  const partidoCores = {
    'PSD': '#FF6B35',
    'CH': '#1E3A8A',
    'PS': '#EF4444',
    'IL': '#06B6D4',
    'L': '#10B981',
    'PCP': '#DC2626',
    'CDS-PP': '#F59E0B',
    'BE': '#8B5CF6',
    'PAN': '#22C55E',
    'JPP': '#6366F1'
  }

  const partidosData = (distribuicao_partidos || []).map(partido => ({
    ...partido,
    cor: partidoCores[partido.sigla] || '#6B7280'
  }))

  const circulosData = (distribuicao_circulos || []).slice(0, 8) // Top 8 círculos

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5
      }
    }
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Enhanced Header */}
      <motion.div variants={itemVariants} className="relative">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mb-6 shadow-lg">
            <Building className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-4 tracking-tight">
            Parlamento Português
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Análise de dados parlamentares em tempo real com insights profundos sobre a atividade legislativa
          </p>
          <div className="flex items-center justify-center mt-6 space-x-2">
            <Sparkles className="w-5 h-5 text-blue-500" />
            <span className="text-sm font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
              Dados Oficiais do Parlamento
            </span>
          </div>
        </div>
      </motion.div>

      {/* Enhanced Stats Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-medium opacity-90">
              Total de Deputados
            </CardTitle>
            <div className="p-2 bg-white/20 rounded-lg">
              <Users className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-1">{totais.deputados || 0}</div>
            <p className="text-xs opacity-90">
              Representantes ativos
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-500 to-green-600 text-white border-0 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-medium opacity-90">
              Partidos Representados
            </CardTitle>
            <div className="p-2 bg-white/20 rounded-lg">
              <Building className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-1">{totais.partidos || 0}</div>
            <p className="text-xs opacity-90">
              Grupos parlamentares
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-medium opacity-90">
              Círculos Eleitorais
            </CardTitle>
            <div className="p-2 bg-white/20 rounded-lg">
              <MapPin className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-1">{totais.circulos || 0}</div>
            <p className="text-xs opacity-90">
              Distritos e regiões
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-500 to-red-500 text-white border-0 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-medium opacity-90">
              Total de Mandatos
            </CardTitle>
            <div className="p-2 bg-white/20 rounded-lg">
              <Award className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-1">{totais.mandatos || 0}</div>
            <p className="text-xs opacity-90">
              Posições ocupadas
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Quick Stats Highlights */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-blue-500 rounded-full">
                <Crown className="h-6 w-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Maior Partido</h3>
                <p className="text-2xl font-bold text-blue-600">
                  {stats.maior_partido?.sigla || 'N/A'}
                </p>
                <p className="text-sm text-gray-600">
                  {stats.maior_partido?.deputados || 0} deputados
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-green-500 rounded-full">
                <MapPin className="h-6 w-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Maior Círculo</h3>
                <p className="text-2xl font-bold text-green-600">
                  {stats.maior_circulo?.designacao || 'N/A'}
                </p>
                <p className="text-sm text-gray-600">
                  {stats.maior_circulo?.deputados || 0} deputados
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Enhanced Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Distribuição por Partido */}
        <motion.div variants={itemVariants}>
          <Card className="shadow-lg border-0 bg-white hover:shadow-xl transition-shadow duration-300">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-t-lg">
              <CardTitle className="flex items-center space-x-3">
                <div className="p-2 bg-blue-500 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <div>
                  <span className="text-lg font-semibold text-gray-900">Distribuição por Partido</span>
                  <CardDescription className="mt-1">
                    Representação parlamentar por grupo político
                  </CardDescription>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <ResponsiveContainer width="100%" height={350}>
                <PieChart>
                  <Pie
                    data={partidosData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ sigla, deputados, percent }) => 
                      `${sigla}: ${deputados} (${(percent * 100).toFixed(1)}%)`
                    }
                    outerRadius={90}
                    fill="#8884d8"
                    dataKey="deputados"
                    stroke="#ffffff"
                    strokeWidth={2}
                  >
                    {partidosData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.cor} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value, name) => [`${value} deputados`, 'Total']}
                    labelFormatter={(label) => `Partido: ${label}`}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        {/* Top Círculos Eleitorais */}
        <motion.div variants={itemVariants}>
          <Card className="shadow-lg border-0 bg-white hover:shadow-xl transition-shadow duration-300">
            <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-t-lg">
              <CardTitle className="flex items-center space-x-3">
                <div className="p-2 bg-green-500 rounded-lg">
                  <BarChart3 className="w-5 h-5 text-white" />
                </div>
                <div>
                  <span className="text-lg font-semibold text-gray-900">Círculos Eleitorais</span>
                  <CardDescription className="mt-1">
                    Representação por distrito e região
                  </CardDescription>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={circulosData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis 
                    dataKey="circulo" 
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    fontSize={11}
                    stroke="#6B7280"
                  />
                  <YAxis stroke="#6B7280" fontSize={11} />
                  <Tooltip 
                    formatter={(value) => [`${value} deputados`, 'Total']}
                    labelStyle={{ color: '#374151' }}
                    contentStyle={{ 
                      backgroundColor: '#f9fafb', 
                      border: '1px solid #d1d5db',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar 
                    dataKey="deputados" 
                    fill="url(#barGradient)" 
                    radius={[6, 6, 0, 0]}
                    stroke="#10B981"
                    strokeWidth={1}
                  />
                  <defs>
                    <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10B981" />
                      <stop offset="100%" stopColor="#059669" />
                    </linearGradient>
                  </defs>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Enhanced Party Details */}
      <motion.div variants={itemVariants}>
        <Card className="shadow-lg border-0 bg-white">
          <CardHeader className="bg-gradient-to-r from-gray-50 to-slate-50 rounded-t-lg">
            <CardTitle className="flex items-center space-x-3">
              <div className="p-2 bg-gray-700 rounded-lg">
                <Building className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-xl font-semibold text-gray-900">Composição Parlamentar</span>
                <CardDescription className="mt-1">
                  Distribuição detalhada por partido político
                </CardDescription>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {partidosData
                .sort((a, b) => b.deputados - a.deputados)
                .map((partido, index) => (
                <motion.div
                  key={partido.sigla}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Link 
                    to={`/partidos/${partido.id}`}
                    className="group relative overflow-hidden bg-white border border-gray-200 rounded-xl p-5 hover:shadow-lg hover:border-gray-300 transition-all duration-300 hover:-translate-y-1 block cursor-pointer"
                  >
                    {/* Background gradient effect */}
                    <div 
                      className="absolute inset-0 opacity-5 group-hover:opacity-10 transition-opacity duration-300"
                      style={{ backgroundColor: partido.cor }}
                    />
                    
                    <div className="relative flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div 
                          className="w-5 h-5 rounded-full shadow-sm ring-2 ring-white group-hover:ring-4 transition-all duration-300"
                          style={{ backgroundColor: partido.cor }}
                        />
                        <div className="flex-1">
                          <div className="font-bold text-lg text-gray-900 group-hover:text-blue-600 transition-colors duration-300">
                            {partido.sigla}
                          </div>
                          <div className="text-sm text-gray-600 line-clamp-1 group-hover:text-gray-700 transition-colors duration-300">
                            {partido.nome}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {((partido.deputados / (totais.deputados || 1)) * 100).toFixed(1)}% do parlamento
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors duration-300">
                          {partido.deputados}
                        </div>
                        <div className="text-xs text-gray-500 uppercase tracking-wide font-medium">
                          deputados
                        </div>
                      </div>
                    </div>
                    
                    {/* Progress bar */}
                    <div className="mt-4 bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div 
                        className="h-full rounded-full transition-all duration-500 ease-out group-hover:opacity-90"
                        style={{ 
                          backgroundColor: partido.cor,
                          width: `${(partido.deputados / Math.max(...partidosData.map(p => p.deputados))) * 100}%`
                        }}
                      />
                    </div>
                    
                    {/* Click indicator */}
                    <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}

export default Dashboard

