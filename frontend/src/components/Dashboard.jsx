import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Users, Building, MapPin, TrendingUp, Crown, Award, Sparkles, BarChart3, Target, Activity, Shield, Zap, Layers, ArrowUpDown, Scale, ChevronRight } from 'lucide-react'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line, Area, AreaChart, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'
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

  // Cores para os partidos baseadas nas cores oficiais
  const partidoCores = {
    'PSD': '#FF6B35',    // Laranja/Vermelho PSD
    'PS': '#E91E63',     // Rosa PS
    'CH': '#1565C0',     // Azul Chega
    'IL': '#00BCD4',     // Ciano IL
    'BE': '#9C27B0',     // Roxo BE
    'PCP': '#F44336',    // Vermelho PCP
    'L': '#4CAF50',      // Verde Livre
    'CDS-PP': '#FF9800', // Laranja CDS
    'PAN': '#8BC34A',    // Verde claro PAN
    'JPP': '#673AB7'     // Roxo escuro JPP
  }

  const partidosData = (distribuicao_partidos || []).map(partido => ({
    ...partido,
    cor: partidoCores[partido.sigla] || '#78716C',
    percentagem: ((partido.deputados / (totais.deputados || 1)) * 100).toFixed(1)
  }))

  const circulosData = (distribuicao_circulos || []).slice(0, 10) // Top 10 círculos

  // Cálculo de métricas políticas avançadas
  const calcularFragmentacao = () => {
    const total = totais.deputados || 1
    const enp = 1 / partidosData.reduce((sum, p) => sum + Math.pow(p.deputados / total, 2), 0)
    return enp.toFixed(2)
  }

  const governoData = partidosData.filter(p => ['PSD', 'CDS-PP'].includes(p.sigla))
  const oposicaoData = partidosData.filter(p => !['PSD', 'CDS-PP'].includes(p.sigla))
  
  const governoDeputados = governoData.reduce((sum, p) => sum + p.deputados, 0)
  const oposicaoDeputados = oposicaoData.reduce((sum, p) => sum + p.deputados, 0)
  const maioriaAbsoluta = Math.floor((totais.deputados || 230) / 2) + 1
  
  const estabilidadeGoverno = {
    maioria: governoDeputados >= maioriaAbsoluta,
    margem: governoDeputados - maioriaAbsoluta,
    percentagem: ((governoDeputados / (totais.deputados || 1)) * 100).toFixed(1)
  }

  // Dados para visualização de estabilidade parlamentar
  const estabilidadeData = [
    { name: 'Governo', value: governoDeputados, fill: '#10B981' },
    { name: 'Oposição', value: oposicaoDeputados, fill: '#EF4444' },
    { name: 'Maioria Necessária', value: maioriaAbsoluta, fill: '#6B7280', type: 'line' }
  ]

  // Análise de representatividade regional
  const representatividadeRegional = circulosData.map(circulo => ({
    ...circulo,
    densidade: (circulo.deputados / (totais.deputados || 1) * 100).toFixed(1)
  }))

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
      {/* Enhanced Header with Political Context */}
      <motion.div variants={itemVariants} className="relative">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mb-6 shadow-lg">
            <Building className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-4 tracking-tight">
            Parlamento Português
          </h1>
          <p className="text-xl text-gray-600 max-w-4xl mx-auto leading-relaxed mb-6">
            Análise política em profundidade da XVII Legislatura com métricas de estabilidade democrática e dinâmicas parlamentares
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
                XVII Legislatura (2022-2026)
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <Target className="w-5 h-5 text-green-500" />
              <span className="text-sm font-medium text-green-600 bg-green-50 px-3 py-1 rounded-full">
                Fragmentação: {calcularFragmentacao()} partidos efetivos
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-purple-500" />
              <span className={`text-sm font-medium px-3 py-1 rounded-full ${
                estabilidadeGoverno.maioria 
                  ? 'text-emerald-700 bg-emerald-50' 
                  : 'text-amber-700 bg-amber-50'
              }`}>
                {estabilidadeGoverno.maioria ? 'Maioria Absoluta' : 'Governo Minoritário'}
              </span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Political Analysis Metrics Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-medium opacity-90">
              Composição Parlamentar
            </CardTitle>
            <div className="p-2 bg-white/20 rounded-lg">
              <Users className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-1">{totais.deputados || 230}</div>
            <p className="text-xs opacity-90">
              Deputados · {totais.partidos || 0} partidos
            </p>
          </CardContent>
        </Card>

        <Card className={`border-0 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 text-white ${
          estabilidadeGoverno.maioria 
            ? 'bg-gradient-to-br from-emerald-500 to-green-600' 
            : 'bg-gradient-to-br from-amber-500 to-orange-600'
        }`}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-medium opacity-90">
              Estabilidade Governamental
            </CardTitle>
            <div className="p-2 bg-white/20 rounded-lg">
              <Shield className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-1">{estabilidadeGoverno.percentagem}%</div>
            <p className="text-xs opacity-90">
              {estabilidadeGoverno.maioria ? 'Maioria absoluta' : `Faltam ${Math.abs(estabilidadeGoverno.margem)} deputados`}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-medium opacity-90">
              Fragmentação Política
            </CardTitle>
            <div className="p-2 bg-white/20 rounded-lg">
              <Layers className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-1">{calcularFragmentacao()}</div>
            <p className="text-xs opacity-90">
              Número efetivo de partidos
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white border-0 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-medium opacity-90">
              Representação Territorial
            </CardTitle>
            <div className="p-2 bg-white/20 rounded-lg">
              <MapPin className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-1">{totais.circulos || 22}</div>
            <p className="text-xs opacity-90">
              Círculos eleitorais ativos
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Political Dynamics Overview */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-blue-500 rounded-full">
                <Crown className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">Maior Partido</h3>
                <p className="text-2xl font-bold text-blue-600">
                  {stats.maior_partido?.sigla || 'PSD'}
                </p>
                <p className="text-sm text-gray-600">
                  {stats.maior_partido?.deputados || 0} deputados ({((stats.maior_partido?.deputados || 0) / (totais.deputados || 1) * 100).toFixed(1)}%)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-emerald-50 to-green-50 border-emerald-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-emerald-500 rounded-full">
                <Scale className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">Balanço Governo-Oposição</h3>
                <p className="text-lg font-bold text-emerald-600">
                  {governoDeputados} vs {oposicaoDeputados}
                </p>
                <p className="text-sm text-gray-600">
                  Margem: {estabilidadeGoverno.margem > 0 ? '+' : ''}{estabilidadeGoverno.margem} deputados
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-purple-50 to-violet-50 border-purple-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-purple-500 rounded-full">
                <MapPin className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">Maior Círculo</h3>
                <p className="text-2xl font-bold text-purple-600">
                  {stats.maior_circulo?.designacao || 'Lisboa'}
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
        {/* Hemiciclo Parlamentar Visualization */}
        <motion.div variants={itemVariants}>
          <Card className="shadow-lg border-0 bg-white hover:shadow-xl transition-shadow duration-300">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-t-lg">
              <CardTitle className="flex items-center space-x-3">
                <div className="p-2 bg-blue-500 rounded-lg">
                  <Users className="w-5 h-5 text-white" />
                </div>
                <div>
                  <span className="text-lg font-semibold text-gray-900">Composição Partidária</span>
                  <CardDescription className="mt-1">
                    Distribuição dos 230 deputados por partido político
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
                    label={({ sigla, deputados, percentagem }) => 
                      deputados > 10 ? `${sigla}: ${deputados}` : ''
                    }
                    outerRadius={100}
                    innerRadius={40}
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
                    formatter={(value, name) => [`${value} deputados (${((value / (totais.deputados || 1)) * 100).toFixed(1)}%)`, 'Total']}
                    labelFormatter={(label) => `Partido: ${label}`}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        {/* Government Stability Analysis */}
        <motion.div variants={itemVariants}>
          <Card className="shadow-lg border-0 bg-white hover:shadow-xl transition-shadow duration-300">
            <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-t-lg">
              <CardTitle className="flex items-center space-x-3">
                <div className="p-2 bg-green-500 rounded-lg">
                  <Shield className="w-5 h-5 text-white" />
                </div>
                <div>
                  <span className="text-lg font-semibold text-gray-900">Estabilidade Governamental</span>
                  <CardDescription className="mt-1">
                    Análise da correlação de forças parlamentares
                  </CardDescription>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="h-[350px] flex flex-col justify-center space-y-8">
                {/* Government vs Opposition Bar */}
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">Governo</span>
                    <span className="text-sm font-bold text-green-600">{governoDeputados} deputados</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-4">
                    <div 
                      className="bg-green-500 h-4 rounded-full transition-all duration-500 flex items-center justify-end pr-3"
                      style={{ width: `${(governoDeputados / (totais.deputados || 230)) * 100}%` }}
                    >
                      <span className="text-xs font-semibold text-white">
                        {estabilidadeGoverno.percentagem}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">Oposição</span>
                    <span className="text-sm font-bold text-red-600">{oposicaoDeputados} deputados</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-4">
                    <div 
                      className="bg-red-500 h-4 rounded-full transition-all duration-500 flex items-center justify-end pr-3"
                      style={{ width: `${(oposicaoDeputados / (totais.deputados || 230)) * 100}%` }}
                    >
                      <span className="text-xs font-semibold text-white">
                        {((oposicaoDeputados / (totais.deputados || 230)) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Majority Line */}
                <div className="border-t pt-6">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-medium text-gray-700">Maioria Absoluta</span>
                    <span className="text-sm font-bold text-gray-600">{maioriaAbsoluta} deputados</span>
                  </div>
                  <div className="text-center">
                    <span className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
                      estabilidadeGoverno.maioria 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-amber-100 text-amber-800'
                    }`}>
                      {estabilidadeGoverno.maioria ? 'Governo com maioria absoluta' : 'Governo minoritário'}
                    </span>
                  </div>
                  <div className="mt-3 text-center text-xs text-gray-500">
                    Margem: {estabilidadeGoverno.margem > 0 ? '+' : ''}{estabilidadeGoverno.margem} deputados
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Representação Territorial */}
      <motion.div variants={itemVariants}>
        <Card className="shadow-lg border-0 bg-white hover:shadow-xl transition-shadow duration-300">
          <CardHeader className="bg-gradient-to-r from-purple-50 to-violet-50 rounded-t-lg">
            <CardTitle className="flex items-center space-x-3">
              <div className="p-2 bg-purple-500 rounded-lg">
                <MapPin className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-lg font-semibold text-gray-900">Representação Territorial</span>
                <CardDescription className="mt-1">
                  Distribuição de deputados por círculo eleitoral
                </CardDescription>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={representatividadeRegional} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
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
                  formatter={(value, name) => [
                    `${value} deputados (${((value / (totais.deputados || 1)) * 100).toFixed(1)}%)`, 
                    'Representação'
                  ]}
                  labelStyle={{ color: '#374151' }}
                  contentStyle={{ 
                    backgroundColor: '#f9fafb', 
                    border: '1px solid #d1d5db',
                    borderRadius: '8px'
                  }}
                />
                <Bar 
                  dataKey="deputados" 
                  fill="url(#purpleGradient)" 
                  radius={[6, 6, 0, 0]}
                  stroke="#8B5CF6"
                  strokeWidth={1}
                />
                <defs>
                  <linearGradient id="purpleGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#8B5CF6" />
                    <stop offset="100%" stopColor="#7C3AED" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </motion.div>

      {/* Enhanced Party Details with Political Analysis */}
      <motion.div variants={itemVariants}>
        <Card className="shadow-lg border-0 bg-white">
          <CardHeader className="bg-gradient-to-r from-gray-50 to-slate-50 rounded-t-lg">
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gray-700 rounded-lg">
                  <Building className="w-5 h-5 text-white" />
                </div>
                <div>
                  <span className="text-xl font-semibold text-gray-900">Análise Partidária Detalhada</span>
                  <CardDescription className="mt-1">
                    Força parlamentar e posicionamento político por partido
                  </CardDescription>
                </div>
              </div>
              <div className="text-sm text-gray-500">
                {partidosData.length} partidos representados
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {partidosData
                .sort((a, b) => b.deputados - a.deputados)
                .map((partido, index) => {
                  const isGoverno = ['PSD', 'CDS-PP'].includes(partido.sigla)
                  const isOposicao = !isGoverno
                  
                  return (
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
                        {/* Political positioning indicator */}
                        <div className="absolute top-3 right-3">
                          <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                            isGoverno 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-blue-100 text-blue-700'
                          }`}>
                            {isGoverno ? 'Governo' : 'Oposição'}
                          </span>
                        </div>

                        {/* Background gradient effect */}
                        <div 
                          className="absolute inset-0 opacity-5 group-hover:opacity-10 transition-opacity duration-300"
                          style={{ backgroundColor: partido.cor }}
                        />
                        
                        <div className="relative">
                          <div className="flex items-center space-x-4 mb-4">
                            <div 
                              className="w-6 h-6 rounded-full shadow-sm ring-2 ring-white group-hover:ring-4 transition-all duration-300"
                              style={{ backgroundColor: partido.cor }}
                            />
                            <div className="flex-1">
                              <div className="font-bold text-lg text-gray-900 group-hover:text-blue-600 transition-colors duration-300">
                                {partido.sigla}
                              </div>
                              <div className="text-sm text-gray-600 line-clamp-1 group-hover:text-gray-700 transition-colors duration-300">
                                {partido.nome}
                              </div>
                            </div>
                          </div>

                          <div className="flex justify-between items-end mb-3">
                            <div>
                              <div className="text-2xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors duration-300">
                                {partido.deputados}
                              </div>
                              <div className="text-xs text-gray-500 uppercase tracking-wide font-medium">
                                deputados
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-semibold text-gray-700">
                                {partido.percentagem}%
                              </div>
                              <div className="text-xs text-gray-500">
                                do parlamento
                              </div>
                            </div>
                          </div>
                          
                          {/* Strength indicator bar */}
                          <div className="mb-3 bg-gray-100 rounded-full h-2 overflow-hidden">
                            <div 
                              className="h-full rounded-full transition-all duration-500 ease-out group-hover:opacity-90"
                              style={{ 
                                backgroundColor: partido.cor,
                                width: `${(partido.deputados / Math.max(...partidosData.map(p => p.deputados))) * 100}%`
                              }}
                            />
                          </div>

                          {/* Political influence indicator */}
                          <div className="flex justify-between items-center text-xs text-gray-500">
                            <span>Influência Parlamentar</span>
                            <span className="font-medium">
                              {partido.deputados >= 20 ? 'Alta' : partido.deputados >= 10 ? 'Média' : 'Baixa'}
                            </span>
                          </div>
                        </div>
                        
                        {/* Click indicator */}
                        <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                          <ChevronRight className="w-4 h-4 text-blue-500" />
                        </div>
                      </Link>
                    </motion.div>
                  )
                })}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}

export default Dashboard