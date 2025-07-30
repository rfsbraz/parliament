import React, { useState, useEffect } from 'react';
import { Calendar, TrendingUp, Users, Target, BarChart3, PieChart, Activity, Shield } from 'lucide-react';

const VotingAnalytics = ({ deputadoId, legislatura }) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeChart, setActiveChart] = useState('overview');

  useEffect(() => {
    const fetchVotingAnalytics = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/deputados/${deputadoId}/voting-analytics?legislatura=${legislatura}`);
        if (!response.ok) {
          throw new Error('Erro ao carregar análises de votação');
        }
        const data = await response.json();
        setAnalytics(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (deputadoId) {
      fetchVotingAnalytics();
    }
  }, [deputadoId, legislatura]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Carregando análises de votação...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">Erro: {error}</div>
        <p className="text-gray-500">Não foi possível carregar as análises de votação</p>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Dados de votação não disponíveis</p>
      </div>
    );
  }

  const charts = [
    { id: 'overview', label: 'Visão Geral', icon: Activity },
    { id: 'collaboration', label: 'Colaboração Cross-Party', icon: Users },
    { id: 'themes', label: 'Temas Legislativos', icon: BarChart3 },
    { id: 'critical', label: 'Votações Críticas', icon: Target }
  ];

  // Party Discipline Heatmap Component
  const PartyDisciplineChart = () => {
    const { party_discipline } = analytics;
    const alignment = (party_discipline.overall_alignment * 100).toFixed(1);
    
    // Group timeline data by month for better visualization
    const monthlyData = party_discipline.timeline.reduce((acc, item) => {
      const month = item.date.substring(0, 7); // YYYY-MM
      if (!acc[month]) {
        acc[month] = { aligned: 0, total: 0, month };
      }
      acc[month].total++;
      if (item.aligned) acc[month].aligned++;
      return acc;
    }, {});

    const monthlyDataArray = Object.values(monthlyData).map(month => ({
      ...month,
      alignment_rate: month.total > 0 ? (month.aligned / month.total * 100) : 0
    }));

    return (
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-semibold text-gray-900 flex items-center">
              <Shield className="h-5 w-5 text-blue-600 mr-2" />
              Disciplina Partidária
            </h4>
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">{alignment}%</div>
              <div className="text-sm text-gray-600">Alinhamento Geral</div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
            {monthlyDataArray.map((month, index) => (
              <div key={month.month} className="relative">
                <div className="text-xs text-gray-600 mb-1">{month.month}</div>
                <div 
                  className={`h-8 rounded flex items-center justify-center text-white text-xs font-medium ${
                    month.alignment_rate >= 90 ? 'bg-green-600' :
                    month.alignment_rate >= 70 ? 'bg-yellow-500' :
                    month.alignment_rate >= 50 ? 'bg-orange-500' :
                    'bg-red-500'
                  }`}
                  title={`${month.month}: ${month.aligned}/${month.total} votações alinhadas (${month.alignment_rate.toFixed(1)}%)`}
                >
                  {month.alignment_rate.toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-4 flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-600 rounded mr-2"></div>
                <span>≥90% Alinhado</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-yellow-500 rounded mr-2"></div>
                <span>70-89%</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-orange-500 rounded mr-2"></div>
                <span>50-69%</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-500 rounded mr-2"></div>
                <span>&lt;50%</span>
              </div>
            </div>
            <div className="text-gray-600">
              {party_discipline.timeline.length} votações analisadas
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Voting Pattern Distribution Chart
  const VoteDistributionChart = () => {
    const { vote_distribution } = analytics;
    const total = Object.values(vote_distribution).reduce((sum, count) => sum + count, 0);
    
    const voteTypes = [
      { key: 'favor', label: 'A Favor', color: 'bg-green-500', textColor: 'text-green-800' },
      { key: 'contra', label: 'Contra', color: 'bg-red-500', textColor: 'text-red-800' },
      { key: 'abstencao', label: 'Abstenção', color: 'bg-yellow-500', textColor: 'text-yellow-800' },
      { key: 'ausente', label: 'Ausente', color: 'bg-gray-400', textColor: 'text-gray-800' }
    ];

    return (
      <div className="space-y-6">
        
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {voteTypes.map(type => {
            const count = vote_distribution[type.key] || 0;
            const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;
            
            return (
              <div key={type.key} className="bg-white border rounded-lg p-4 text-center">
                <div className={`w-12 h-12 ${type.color} rounded-full mx-auto mb-3 flex items-center justify-center`}>
                  <span className="text-white font-bold text-lg">{percentage}%</span>
                </div>
                <div className="text-sm font-medium text-gray-900">{type.label}</div>
                <div className="text-2xl font-bold text-gray-700">{count}</div>
                <div className="text-xs text-gray-500">votações</div>
              </div>
            );
          })}
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-700 mb-2">Total: {total} votações</div>
          <div className="flex rounded-lg overflow-hidden h-4">
            {voteTypes.map(type => {
              const count = vote_distribution[type.key] || 0;
              const width = total > 0 ? (count / total * 100) : 0;
              return (
                <div
                  key={type.key}
                  className={type.color}
                  style={{ width: `${width}%` }}
                  title={`${type.label}: ${count} (${width.toFixed(1)}%)`}
                />
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  // Participation Timeline Chart
  const ParticipationTimelineChart = () => {
    const { participation_timeline } = analytics;
    
    return (
      <div className="space-y-6">
        
        <div className="space-y-3">
          {participation_timeline.slice(-10).map((day, index) => (
            <div key={day.date} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-medium text-gray-900">
                  {new Date(day.date).toLocaleDateString('pt-PT', { 
                    weekday: 'short', 
                    year: 'numeric', 
                    month: 'short', 
                    day: 'numeric' 
                  })}
                </div>
                <div className="text-sm text-gray-600">
                  {day.participated}/{day.total_votes} votações ({(day.participation_rate * 100).toFixed(0)}%)
                </div>
              </div>
              
              <div className="flex items-center space-x-4 text-xs">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded mr-1"></div>
                  <span>A Favor: {day.favor_votes}</span>
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-red-500 rounded mr-1"></div>
                  <span>Contra: {day.contra_votes}</span>
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-yellow-500 rounded mr-1"></div>
                  <span>Abstenção: {day.abstention_votes}</span>
                </div>
              </div>
              
              <div className="mt-2 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${day.participation_rate * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Cross-Party Collaboration Chart
  const CollaborationChart = () => {
    const { cross_party_collaboration } = analytics;
    
    if (!cross_party_collaboration.length) {
      return (
        <div className="text-center py-8">
          <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Dados de colaboração cross-party não disponíveis</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        <h4 className="text-lg font-semibold text-gray-900 flex items-center">
          <Users className="h-5 w-5 text-indigo-600 mr-2" />
          Colaboração Cross-Party
        </h4>
        
        <div className="space-y-3">
          {cross_party_collaboration.map((party, index) => (
            <div key={party.party} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-medium text-gray-900">{party.party}</div>
                <div className="text-sm text-gray-600">
                  {(party.alignment_rate * 100).toFixed(1)}% alinhamento
                </div>
              </div>
              
              <div className="flex items-center justify-between mb-2">
                <div className="text-xs text-gray-500">
                  {party.aligned_votes}/{party.total_votes} votações alinhadas
                </div>
              </div>
              
              <div className="bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    party.alignment_rate >= 0.7 ? 'bg-green-500' :
                    party.alignment_rate >= 0.5 ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`}
                  style={{ width: `${party.alignment_rate * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Legislative Theme Radar Chart
  const ThemeAnalysisChart = () => {
    const { theme_analysis } = analytics;
    
    return (
      <div className="space-y-6">
        <h4 className="text-lg font-semibold text-gray-900 flex items-center">
          <BarChart3 className="h-5 w-5 text-orange-600 mr-2" />
          Análise por Temas Legislativos
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {theme_analysis.map((theme, index) => (
            <div key={theme.tema} className="bg-white border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="text-sm font-medium text-gray-900">{theme.tema}</div>
                <div className="text-xs text-gray-500">{theme.total_votes} votações</div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded mr-1"></div>
                    A Favor
                  </span>
                  <span>{theme.favor_votes} ({(theme.favor_rate * 100).toFixed(0)}%)</span>
                </div>
                
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center">
                    <div className="w-2 h-2 bg-red-500 rounded mr-1"></div>
                    Contra
                  </span>
                  <span>{theme.contra_votes}</span>
                </div>
                
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center">
                    <div className="w-2 h-2 bg-yellow-500 rounded mr-1"></div>
                    Abstenção
                  </span>
                  <span>{theme.abstention_votes}</span>
                </div>
                
                {theme.absent_votes > 0 && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="flex items-center">
                      <div className="w-2 h-2 bg-gray-400 rounded mr-1"></div>
                      Ausente
                    </span>
                    <span>{theme.absent_votes}</span>
                  </div>
                )}
              </div>
              
              <div className="mt-3 flex rounded overflow-hidden h-2">
                <div 
                  className="bg-green-500" 
                  style={{ width: `${(theme.favor_votes / theme.total_votes) * 100}%` }}
                />
                <div 
                  className="bg-red-500" 
                  style={{ width: `${(theme.contra_votes / theme.total_votes) * 100}%` }}
                />
                <div 
                  className="bg-yellow-500" 
                  style={{ width: `${(theme.abstention_votes / theme.total_votes) * 100}%` }}
                />
                <div 
                  className="bg-gray-400" 
                  style={{ width: `${(theme.absent_votes / theme.total_votes) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Critical Votes Analysis
  const CriticalVotesChart = () => {
    const { critical_votes } = analytics;
    
    const voteTypeColors = {
      budget: 'bg-purple-100 text-purple-800 border-purple-200',
      government: 'bg-blue-100 text-blue-800 border-blue-200',
      confidence: 'bg-red-100 text-red-800 border-red-200',
      regular: 'bg-gray-100 text-gray-800 border-gray-200'
    };
    
    const voteColors = {
      favor: 'text-green-600',
      contra: 'text-red-600',
      abstencao: 'text-yellow-600',
      ausente: 'text-gray-500'
    };
    
    return (
      <div className="space-y-6">
        <h4 className="text-lg font-semibold text-gray-900 flex items-center">
          <Target className="h-5 w-5 text-red-600 mr-2" />
          Análise de Votações Críticas
        </h4>
        
        <div className="space-y-3">
          {critical_votes.slice(0, 15).map((vote, index) => (
            <div key={index} className="bg-white border rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900 mb-2 line-clamp-2">
                    {vote.objeto}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${voteTypeColors[vote.type] || voteTypeColors.regular}`}>
                      {vote.type === 'budget' ? 'Orçamento' :
                       vote.type === 'government' ? 'Governo' :
                       vote.type === 'confidence' ? 'Confiança' :
                       'Regular'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(vote.data).toLocaleDateString('pt-PT')}
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className={`text-sm font-medium ${voteColors[vote.voto] || 'text-gray-600'}`}>
                    {vote.voto === 'favor' ? 'A Favor' :
                     vote.voto === 'contra' ? 'Contra' :
                     vote.voto === 'abstencao' ? 'Abstenção' :
                     'Ausente'}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    vote.resultado === 'aprovada' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {vote.resultado === 'aprovada' ? 'Aprovada' : 'Rejeitada'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Combined Overview Component
  const OverviewChart = () => {
    return (
      <div className="space-y-8">
        {/* Party Discipline Section */}
        <div>
          <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Shield className="h-5 w-5 text-blue-600 mr-2" />
            Disciplina Partidária
          </h4>
          <PartyDisciplineChart />
        </div>

        {/* Vote Distribution Section */}
        <div>
          <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <PieChart className="h-5 w-5 text-purple-600 mr-2" />
            Padrão de Votação
          </h4>
          <VoteDistributionChart />
        </div>

        {/* Participation Timeline Section */}
        <div>
          <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Activity className="h-5 w-5 text-green-600 mr-2" />
            Participação
          </h4>
          <ParticipationTimelineChart />
        </div>
      </div>
    );
  };

  const renderChart = () => {
    switch (activeChart) {
      case 'overview':
        return <OverviewChart />;
      case 'collaboration':
        return <CollaborationChart />;
      case 'themes':
        return <ThemeAnalysisChart />;
      case 'critical':
        return <CriticalVotesChart />;
      default:
        return <OverviewChart />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Chart Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 overflow-x-auto">
          {charts.map((chart) => {
            const Icon = chart.icon;
            return (
              <button
                key={chart.id}
                onClick={() => setActiveChart(chart.id)}
                className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
                  activeChart === chart.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4 mr-2" />
                {chart.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Chart Content */}
      <div className="min-h-96">
        {renderChart()}
      </div>

      {/* Summary Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <TrendingUp className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
          <div>
            <h5 className="text-sm font-medium text-blue-900">
              Análise Baseada em Dados Reais
            </h5>
            <p className="text-sm text-blue-700 mt-1">
              Estas visualizações são baseadas no historial completo de votações do deputado 
              {analytics.deputy_info?.party && ` (${analytics.deputy_info.party.sigla})`} 
              na {legislatura}ª Legislatura, incluindo análises de disciplina partidária, 
              colaboração cross-party e padrões temáticos de votação.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VotingAnalytics;