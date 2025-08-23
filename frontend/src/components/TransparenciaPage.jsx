import React, { useState, useEffect } from 'react'
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  BarChart3, 
  Activity, 
  Users, 
  MessageSquare, 
  Scale, 
  RefreshCw,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Eye,
  Target,
  Calendar,
  Vote,
  FileText,
  Award,
  UserCheck,
  Share2
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Area, AreaChart } from 'recharts'
import { apiFetch } from '../config/api';

const TransparenciaPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const location = useLocation()
  
  const [activeTab, setActiveTab] = useState('live')
  const [data, setData] = useState({})
  const [loading, setLoading] = useState({})
  const [lastUpdated, setLastUpdated] = useState(null)

  const tabs = [
    { id: 'live', label: 'Atividade Ao Vivo', icon: Activity, color: 'text-blue-600' },
    { id: 'progress', label: 'Progresso Legislativo', icon: Scale, color: 'text-green-600' },
    { id: 'deputies', label: 'Performance Deputados', icon: Users, color: 'text-purple-600' },
    { id: 'participation', label: 'Participação Cidadã', icon: MessageSquare, color: 'text-orange-600' },
    { id: 'accountability', label: 'Métricas Transparência', icon: BarChart3, color: 'text-red-600' }
  ]

  const API_BASE_URL = 'transparency'

  const fetchData = async (endpoint, key) => {
    setLoading(prev => ({ ...prev, [key]: true }))
    try {
      const response = await fetch(`${API_BASE_URL}/${endpoint}`)
      const result = await response.json()
      if (response.ok) {
        setData(prev => ({ ...prev, [key]: result }))
        if (result.last_updated) {
          setLastUpdated(result.last_updated)
        }
      } else {
        console.error(`Erro ao carregar ${endpoint}:`, result.message)
      }
    } catch (error) {
      console.error(`Erro ao carregar ${endpoint}:`, error)
    }
    setLoading(prev => ({ ...prev, [key]: false }))
  }

  useEffect(() => {
    // Load data based on active tab
    switch (activeTab) {
      case 'live':
        fetchData('live-activity', 'liveActivity')
        break
      case 'progress':
        fetchData('legislative-progress', 'legislativeProgress')
        break
      case 'deputies':
        fetchData('deputy-performance', 'deputyPerformance')
        break
      case 'participation':
        fetchData('citizen-participation', 'citizenParticipation')
        break
      case 'accountability':
        fetchData('accountability-metrics', 'accountabilityMetrics')
        break
    }
  }, [activeTab])

  // Initialize active tab from URL parameter
  useEffect(() => {
    const tab = searchParams.get('tab')
    const validTabs = ['live', 'progress', 'deputies', 'participation', 'accountability']
    if (tab && validTabs.includes(tab)) {
      setActiveTab(tab)
    }
  }, [searchParams])

  // Handle tab change and update URL
  const handleTabChange = (tabId) => {
    setActiveTab(tabId)
    setSearchParams({ tab: tabId })
  }

  // Copy link to clipboard for sharing
  const copyTabLink = (tabId) => {
    const url = `${window.location.origin}/transparencia?tab=${tabId}`
    navigator.clipboard.writeText(url).then(() => {
      // You could add a toast notification here
      console.log('Link copiado:', url)
    })
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('pt-PT')
  }

  const formatPercentage = (value) => {
    return `${value}%`
  }

  const getStatusBadge = (status) => {
    const statusColors = {
      'excellent': 'bg-green-100 text-green-800',
      'good': 'bg-blue-100 text-blue-800',
      'average': 'bg-yellow-100 text-yellow-800',
      'satisfactory': 'bg-yellow-100 text-yellow-800',
      'moderate': 'bg-orange-100 text-orange-800',
      'needs_improvement': 'bg-red-100 text-red-800',
      'concerning': 'bg-red-100 text-red-800',
      'strong': 'bg-green-100 text-green-800'
    }
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    )
  }

  const MetricCard = ({ icon: Icon, title, value, subtitle, trend, color = 'text-blue-600' }) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-white rounded-lg border border-gray-200 p-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg bg-opacity-10 ${color.replace('text-', 'bg-')}`}>
            <Icon className={`h-5 w-5 ${color}`} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
          </div>
        </div>
        {trend && (
          <div className="text-right">
            <span className={`text-sm font-medium ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend > 0 ? '+' : ''}{trend}%
            </span>
          </div>
        )}
      </div>
    </motion.div>
  )

  const ProgressBar = ({ percentage, color = 'bg-blue-500' }) => (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div 
        className={`h-2 rounded-full ${color} transition-all duration-300`}
        style={{ width: `${Math.min(percentage, 100)}%` }}
      />
    </div>
  )

  const renderLiveActivity = () => {
    const liveData = data.liveActivity
    if (!liveData) return <div className="text-center py-8">Carregando dados da atividade parlamentar...</div>

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={Calendar}
            title="Eventos Hoje"
            value={liveData.todays_agenda?.summary?.total_events || 0}
            color="text-blue-600"
          />
          <MetricCard
            icon={Users}
            title="Sessões Plenárias"
            value={liveData.todays_agenda?.summary?.plenary_sessions || 0}
            color="text-green-600"
          />
          <MetricCard
            icon={Vote}
            title="Votações (48h)"
            value={liveData.recent_votes?.summary?.total_votes_48h || 0}
            color="text-purple-600"
          />
          <MetricCard
            icon={TrendingUp}
            title="Taxa Aprovação"
            value={formatPercentage(liveData.recent_votes?.summary?.approval_rate || 0)}
            color="text-orange-600"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5" />
                <span>Agenda de Hoje</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Em Progresso</span>
                  <span className="font-semibold">{liveData.todays_agenda?.summary?.in_progress || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Completados</span>
                  <span className="font-semibold">{liveData.todays_agenda?.summary?.completed || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Reuniões Comissão</span>
                  <span className="font-semibold">{liveData.todays_agenda?.summary?.committee_meetings || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Vote className="h-5 w-5" />
                <span>Atividade Votações</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-600">Taxa de Aprovação</span>
                    <span className="font-semibold">{formatPercentage(liveData.recent_votes?.summary?.approval_rate || 0)}</span>
                  </div>
                  <ProgressBar percentage={liveData.recent_votes?.summary?.approval_rate || 0} color="bg-green-500" />
                </div>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold text-green-600">{liveData.recent_votes?.summary?.approved || 0}</p>
                    <p className="text-sm text-gray-600">Aprovadas</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-red-600">{liveData.recent_votes?.summary?.rejected || 0}</p>
                    <p className="text-sm text-gray-600">Rejeitadas</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  const renderLegislativeProgress = () => {
    const progressData = data.legislativeProgress
    if (!progressData) return <div className="text-center py-8">Carregando progresso legislativo...</div>

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={FileText}
            title="Iniciativas Totais"
            value={progressData.overall_efficiency?.total_initiatives || 0}
            color="text-blue-600"
          />
          <MetricCard
            icon={CheckCircle}
            title="Taxa Aprovação"
            value={formatPercentage(progressData.overall_efficiency?.overall_approval_rate || 0)}
            color="text-green-600"
          />
          <MetricCard
            icon={Users}
            title="Comissões Ativas"
            value={progressData.overall_efficiency?.committees_active || 0}
            color="text-purple-600"
          />
          <MetricCard
            icon={Clock}
            title="Tempo Resp. Médio"
            value={`${progressData.government_responsiveness?.avg_response_days || 0} dias`}
            color="text-orange-600"
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Scale className="h-5 w-5" />
              <span>Responsividade do Governo</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Classificação</span>
                {getStatusBadge(progressData.government_responsiveness?.efficiency_rating)}
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600">Taxa de Resposta</span>
                  <span className="font-semibold">{formatPercentage(progressData.government_responsiveness?.response_rate || 0)}</span>
                </div>
                <ProgressBar percentage={progressData.government_responsiveness?.response_rate || 0} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <p className="text-xl font-bold text-blue-600">{progressData.government_responsiveness?.total_questions || 0}</p>
                  <p className="text-sm text-gray-600">Perguntas</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold text-green-600">{progressData.government_responsiveness?.total_responses || 0}</p>
                  <p className="text-sm text-gray-600">Respostas</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderDeputyPerformance = () => {
    const deputyData = data.deputyPerformance
    if (!deputyData) return <div className="text-center py-8">Carregando dados dos deputados...</div>

    const topDeputies = deputyData.deputy_performance?.slice(0, 5) || []

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={Users}
            title="Deputados Analisados"
            value={deputyData.analysis_period?.total_deputies_analyzed || 0}
            color="text-blue-600"
          />
          <MetricCard
            icon={UserCheck}
            title="Assiduidade Média"
            value={formatPercentage(deputyData.analysis_period?.avg_attendance_rate || 0)}
            color="text-green-600"
          />
          <MetricCard
            icon={Award}
            title="High Performers"
            value={deputyData.summary_statistics?.high_performers || 0}
            color="text-purple-600"
          />
          <MetricCard
            icon={Activity}
            title="Deputados Ativos"
            value={deputyData.summary_statistics?.active_deputies_90d || 0}
            color="text-orange-600"
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Award className="h-5 w-5" />
              <span>Top 5 Deputados</span>
            </CardTitle>
            <CardDescription>Deputados com melhor performance global</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topDeputies.map((deputy, index) => (
                <div key={deputy.deputy_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-bold text-blue-600">{index + 1}</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{deputy.parliamentary_name || deputy.name}</p>
                      <p className="text-sm text-gray-500">{deputy.party || 'N/A'}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900">{deputy.performance?.overall_score}</p>
                    {getStatusBadge(deputy.performance?.rating)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderCitizenParticipation = () => {
    const participationData = data.citizenParticipation
    if (!participationData) return <div className="text-center py-8">Carregando dados de participação...</div>

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={FileText}
            title="Petições Totais"
            value={participationData.petition_data?.total_petitions || 0}
            color="text-blue-600"
          />
          <MetricCard
            icon={CheckCircle}
            title="Taxa Aceitação"
            value={formatPercentage(participationData.petition_data?.processing_status?.acceptance_rate || 0)}
            color="text-green-600"
          />
          <MetricCard
            icon={Users}
            title="Subscritores Médios"
            value={participationData.petition_data?.engagement_metrics?.avg_subscribers || 0}
            color="text-purple-600"
          />
          <MetricCard
            icon={TrendingUp}
            title="Score Engagement"
            value={participationData.petition_data?.engagement_metrics?.citizen_engagement_score || 0}
            color="text-orange-600"
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5" />
              <span>Participação Cidadã</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Classificação Geral</span>
                {getStatusBadge(participationData.participation_summary?.overall_rating)}
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600">Score de Transparência</span>
                  <span className="font-semibold">{participationData.participation_summary?.transparency_score || 0}</span>
                </div>
                <ProgressBar percentage={participationData.participation_summary?.transparency_score || 0} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <p className="text-xl font-bold text-green-600">{participationData.petition_data?.processing_status?.accepted || 0}</p>
                  <p className="text-sm text-gray-600">Aceites</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold text-yellow-600">{participationData.petition_data?.processing_status?.processing || 0}</p>
                  <p className="text-sm text-gray-600">Em Análise</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderAccountabilityMetrics = () => {
    const accountabilityData = data.accountabilityMetrics
    if (!accountabilityData) return <div className="text-center py-8">Carregando métricas de transparência...</div>

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={Target}
            title="Score Geral"
            value={accountabilityData.accountability_summary?.overall_score || 0}
            color="text-blue-600"
          />
          <MetricCard
            icon={TrendingUp}
            title="Responsividade"
            value={formatPercentage(accountabilityData.key_performance_indicators?.government_responsiveness?.score || 0)}
            color="text-green-600"
          />
          <MetricCard
            icon={Scale}
            title="Eficiência"
            value={formatPercentage(accountabilityData.key_performance_indicators?.legislative_efficiency?.score || 0)}
            color="text-purple-600"
          />
          <MetricCard
            icon={Eye}
            title="Transparência"
            value={formatPercentage(accountabilityData.key_performance_indicators?.meeting_transparency?.score || 0)}
            color="text-orange-600"
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Saúde Democrática</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Classificação Geral</span>
                {getStatusBadge(accountabilityData.accountability_summary?.overall_rating)}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Saúde Democrática</span>
                {getStatusBadge(accountabilityData.benchmark_comparison?.overall_democratic_health)}
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600">Score de Accountability</span>
                  <span className="font-semibold">{accountabilityData.accountability_summary?.overall_score || 0}</span>
                </div>
                <ProgressBar percentage={accountabilityData.accountability_summary?.overall_score || 0} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <p className="text-xl font-bold text-green-600">{accountabilityData.benchmark_comparison?.areas_above_benchmark || 0}</p>
                  <p className="text-sm text-gray-600">Acima Benchmark</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold text-red-600">{accountabilityData.benchmark_comparison?.areas_needing_attention || 0}</p>
                  <p className="text-sm text-gray-600">Precisam Atenção</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderContent = () => {
    if (loading[activeTab]) {
      return (
        <div className="flex items-center justify-center py-12">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"
          />
        </div>
      )
    }

    switch (activeTab) {
      case 'live': return renderLiveActivity()
      case 'progress': return renderLegislativeProgress()
      case 'deputies': return renderDeputyPerformance()
      case 'participation': return renderCitizenParticipation()
      case 'accountability': return renderAccountabilityMetrics()
      default: return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Dashboard de Transparência</h1>
        <p className="text-lg text-gray-600 mb-6">
          Monitorização em tempo real da atividade parlamentar portuguesa
        </p>
        {lastUpdated && (
          <p className="text-sm text-gray-500">
            Última atualização: {formatDate(lastUpdated)}
          </p>
        )}
      </motion.div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg border border-gray-200 p-2">
        <div className="flex flex-wrap gap-2">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <div key={tab.id} className="relative group">
                <button
                  onClick={() => handleTabChange(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 border border-blue-200'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
                
                {/* Share button - appears on hover */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    copyTabLink(tab.id)
                  }}
                  className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-white border border-gray-300 rounded-full p-1 hover:bg-gray-50 shadow-sm"
                  title={`Copiar link para ${tab.label}`}
                >
                  <Share2 className="h-3 w-3 text-gray-500" />
                </button>
              </div>
            )
          })}
        </div>
      </div>

      {/* Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
      >
        {renderContent()}
      </motion.div>
    </div>
  )
}

export default TransparenciaPage