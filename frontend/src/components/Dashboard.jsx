import { motion } from 'framer-motion'
import { Users, Building, MapPin, TrendingUp } from 'lucide-react'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
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
      {/* Header */}
      <motion.div variants={itemVariants} className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Parlamento Português
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Explore os dados abertos da XVII Legislatura de forma interativa e visual
        </p>
      </motion.div>

      {/* Stats Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium opacity-90">
              Total de Deputados
            </CardTitle>
            <Users className="h-4 w-4 opacity-90" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totais.deputados || 0}</div>
            <p className="text-xs opacity-90">
              Ativos na XVII Legislatura
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white border-0">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium opacity-90">
              Partidos Representados
            </CardTitle>
            <Building className="h-4 w-4 opacity-90" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totais.partidos || 0}</div>
            <p className="text-xs opacity-90">
              Grupos parlamentares
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium opacity-90">
              Círculos Eleitorais
            </CardTitle>
            <MapPin className="h-4 w-4 opacity-90" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totais.circulos || 0}</div>
            <p className="text-xs opacity-90">
              Distritos e regiões
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Distribuição por Partido */}
        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5" />
                <span>Distribuição por Partido</span>
              </CardTitle>
              <CardDescription>
                Número de deputados por grupo parlamentar
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={partidosData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ sigla, deputados }) => `${sigla}: ${deputados}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="deputados"
                  >
                    {partidosData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.cor} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        {/* Top Círculos Eleitorais */}
        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <MapPin className="w-5 h-5" />
                <span>Principais Círculos Eleitorais</span>
              </CardTitle>
              <CardDescription>
                Círculos com maior representação parlamentar
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={circulosData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="circulo" 
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    fontSize={12}
                  />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="deputados" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Partido Details */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>Detalhes dos Partidos</CardTitle>
            <CardDescription>
              Lista completa com número de deputados por partido
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {partidosData.map((partido, index) => (
                <motion.div
                  key={partido.sigla}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center space-x-3 p-4 rounded-lg border hover:shadow-md transition-shadow"
                >
                  <div 
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: partido.cor }}
                  />
                  <div className="flex-1">
                    <div className="font-semibold text-sm">{partido.sigla}</div>
                    <div className="text-xs text-gray-500 truncate">
                      {partido.nome}
                    </div>
                  </div>
                  <div className="text-lg font-bold text-gray-900">
                    {partido.deputados}
                  </div>
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

