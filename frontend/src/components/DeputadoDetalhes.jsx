import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { ArrowLeft, User, MapPin, Calendar, Briefcase, Activity, FileText, Vote, MessageSquare, Play, Clock, ExternalLink, Mail, Shield, AlertTriangle, Heart, Users } from 'lucide-react';
import VotingAnalytics from './VotingAnalytics';

// TODO: Deputy mandate linking limitation
// Current system uses name-based linking to connect same person across legislaturas
// This is a temporary solution because deputado_id changes every legislative period
// Future enhancement: Implement proper unique person identifiers or create person-linking table

const DeputadoDetalhes = () => {
  const { cadId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [deputado, setDeputado] = useState(null);
  const [atividades, setAtividades] = useState(null);
  const [conflitosInteresse, setConflitosInteresse] = useState(null);
  const [attendanceData, setAttendanceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [interventionTypeFilter, setInterventionTypeFilter] = useState(searchParams.get('tipo_intervencao') || '');
  const [interventionSort, setInterventionSort] = useState(searchParams.get('ordenacao_intervencoes') || 'newest');
  const [currentPage, setCurrentPage] = useState(parseInt(searchParams.get('page')) || 1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalInterventions, setTotalInterventions] = useState(0);
  const [expandedInitiatives, setExpandedInitiatives] = useState(new Set());
  
  // Helper function to generate deputy URLs
  const getDeputadoUrl = (cadId) => {
    return `/deputados/${cadId}`;
  };

  // Toggle initiative details expansion
  const toggleInitiativeDetails = (index) => {
    const newExpanded = new Set(expandedInitiatives);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedInitiatives(newExpanded);
  };

  // Get active tab from URL hash, default to 'biografia'
  const getActiveTabFromUrl = () => {
    const hash = location.hash.replace('#', '');
    const validTabs = ['biografia', 'intervencoes', 'iniciativas', 'votacoes', 'attendance', 'mandatos-anteriores', 'conflitos-interesse'];
    return validTabs.includes(hash) ? hash : 'biografia';
  };

  const [activeTab, setActiveTab] = useState(getActiveTabFromUrl());

  // Sync activeTab with URL hash changes
  useEffect(() => {
    const handleHashChange = () => {
      setActiveTab(getActiveTabFromUrl());
    };

    // Listen for hash changes (browser back/forward)
    window.addEventListener('hashchange', handleHashChange);
    
    // Update tab when location changes
    setActiveTab(getActiveTabFromUrl());

    return () => {
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, [location.hash]);

  // Handle tab change with URL update
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    navigate(`#${tabId}`, { replace: true });
  };

  // Set default tab in URL if no hash is present
  useEffect(() => {
    if (!location.hash) {
      navigate('#biografia', { replace: true });
    }
  }, [navigate, location.hash]);

  // Function to update URL parameters
  const updateInterventionParams = (newParams) => {
    const updatedParams = new URLSearchParams(searchParams);
    Object.entries(newParams).forEach(([key, value]) => {
      if (value && value !== '') {
        updatedParams.set(key, value);
      } else {
        updatedParams.delete(key);
      }
    });
    setSearchParams(updatedParams);
  };

  useEffect(() => {
    const fetchDados = async () => {
      try {
        setLoading(true);
        
        // Buscar detalhes do deputado
        const deputadoResponse = await fetch(`/api/deputados/${cadId}/detalhes`);
        if (!deputadoResponse.ok) {
          throw new Error('Erro ao carregar dados do deputado');
        }
        const deputadoData = await deputadoResponse.json();
        setDeputado(deputadoData);

        // Buscar atividades do deputado with API parameters
        const apiParams = new URLSearchParams();
        if (interventionTypeFilter) {
          apiParams.set('tipo_intervencao', interventionTypeFilter);
        }
        if (interventionSort) {
          apiParams.set('ordenacao_intervencoes', interventionSort);
        }
        apiParams.set('page', currentPage.toString());
        apiParams.set('per_page', '50');
        
        const atividadesUrl = `/api/deputados/${cadId}/atividades?${apiParams.toString()}`;
        const atividadesResponse = await fetch(atividadesUrl);
        if (!atividadesResponse.ok) {
          throw new Error('Erro ao carregar atividades do deputado');
        }
        const atividadesData = await atividadesResponse.json();
        setAtividades(atividadesData);
        
        // Update pagination state if intervention metadata is available
        if (atividadesData.intervention_metadata) {
          setTotalPages(atividadesData.intervention_metadata.pages);
          setTotalInterventions(atividadesData.intervention_metadata.total);
        }

        // Buscar conflitos de interesse do deputado
        try {
          const conflitosResponse = await fetch(`/api/deputados/${cadId}/conflitos-interesse`);
          if (conflitosResponse.ok) {
            const conflitosData = await conflitosResponse.json();
            setConflitosInteresse(conflitosData);
          }
        } catch (conflitosErr) {
          // Conflitos de interesse são opcionais, não interromper o carregamento
          console.warn('Dados de conflitos de interesse não disponíveis:', conflitosErr);
        }

        // Buscar dados de presenças do deputado
        try {
          const attendanceResponse = await fetch(`/api/deputados/${cadId}/attendance`);
          if (attendanceResponse.ok) {
            const attendanceDataResult = await attendanceResponse.json();
            setAttendanceData(attendanceDataResult);
          }
        } catch (attendanceErr) {
          // Dados de presença são opcionais, não interromper o carregamento
          console.warn('Dados de presença não disponíveis:', attendanceErr);
        }
        
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (cadId) {
      fetchDados();
    }
  }, [cadId, interventionTypeFilter, interventionSort, currentPage]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando dados do deputado...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Erro: {error}</p>
          <Link to="/deputados" className="text-blue-600 hover:underline">
            Voltar aos deputados
          </Link>
        </div>
      </div>
    );
  }

  if (!deputado) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Deputado não encontrado</p>
      </div>
    );
  }

  const tabs = [
    { id: 'biografia', label: 'Biografia', icon: User },
    { id: 'intervencoes', label: 'Intervenções', icon: MessageSquare },
    { id: 'iniciativas', label: 'Iniciativas', icon: FileText },
    { id: 'votacoes', label: 'Votações', icon: Vote },
    { id: 'attendance', label: 'Presenças', icon: Activity },
    { id: 'mandatos-anteriores', label: 'Mandatos Anteriores', icon: Calendar },
    { id: 'conflitos-interesse', label: 'Conflitos de Interesse', icon: Shield }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link 
                to="/deputados" 
                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                Voltar aos Deputados
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Perfil do Deputado */}
        <div className="bg-white rounded-lg shadow-sm border mb-8">
          <div className="px-6 py-8">
            <div className="flex items-start space-x-6">
              {/* Avatar */}
              <div className="flex-shrink-0">
                {deputado.picture_url ? (
                  <img
                    src={deputado.picture_url}
                    alt={deputado.nome}
                    className="h-24 w-24 rounded-full object-cover bg-gray-200 border-2 border-gray-200"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                ) : null}
                <div className="h-24 w-24 rounded-full bg-blue-100 flex items-center justify-center" style={{ display: deputado.picture_url ? 'none' : 'flex' }}>
                  <User className="h-12 w-12 text-blue-600" />
                </div>
              </div>
              
              {/* Informações Básicas */}
              <div className="flex-1">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  {deputado.nome}
                </h1>
                
                <div className="flex flex-wrap items-center gap-4 text-gray-600 mb-4">
                  <div className="flex items-center">
                    <Briefcase className="h-4 w-4 mr-2" />
                    <span>{deputado.profissao || 'Profissão não informada'}</span>
                  </div>
                  
                  <div className="flex items-center">
                    <MapPin className="h-4 w-4 mr-2" />
                    <span>{deputado.circulo}</span>
                  </div>
                  
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 mr-2" />
                    <span>Mandato desde {new Date(deputado.mandato.inicio).toLocaleDateString('pt-PT')}</span>
                  </div>
                </div>

                {/* Partido */}
                {deputado.partido && (
                  <Link 
                    to={`/partidos/${encodeURIComponent(deputado.partido.id)}`}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
                  >
                    {deputado.partido.sigla} - {deputado.partido.nome}
                  </Link>
                )}
              </div>

              {/* Status and Actions */}
              <div className="flex-shrink-0">
                <div className="flex flex-col items-end space-y-3">
                  {/* Status Badge */}
                  {deputado.career_info?.is_currently_active ? (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                      <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                      Ativo
                    </span>
                  ) : deputado.career_info?.latest_completed_mandate ? (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                      <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                      Último mandato: {deputado.career_info.latest_completed_mandate.legislatura} ({deputado.career_info.latest_completed_mandate.periodo})
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                      <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                      Status Indisponível
                    </span>
                  )}
                  
                  {/* Email Button - Only show for active deputies */}
                  {deputado.career_info?.is_currently_active && (
                    <button
                      onClick={() => {
                        const emailUrl = `https://www.parlamento.pt/DeputadoGP/Paginas/EmailDeputado.aspx?BID=${deputado.id_cadastro}`;
                        window.open(emailUrl, '_blank', 'width=800,height=600,scrollbars=yes,resizable=yes');
                      }}
                      className="inline-flex items-center px-4 py-2 border border-blue-300 text-sm font-medium rounded-md text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors shadow-sm"
                      title="Enviar email através do site oficial do Parlamento"
                    >
                      <Mail className="h-4 w-4 mr-2" />
                      Enviar e-mail
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Estatísticas Rápidas */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <MessageSquare className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Intervenções</p>
                <p className="text-2xl font-bold text-gray-900">
                  {deputado.estatisticas.total_intervencoes}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <FileText className="h-8 w-8 text-green-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Iniciativas</p>
                <p className="text-2xl font-bold text-gray-900">
                  {deputado.estatisticas.total_iniciativas}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <Activity className={`h-8 w-8 ${
                deputado.estatisticas.taxa_assiduidade >= 0.9 ? 'text-green-600' :
                deputado.estatisticas.taxa_assiduidade >= 0.8 ? 'text-blue-600' :
                deputado.estatisticas.taxa_assiduidade >= 0.7 ? 'text-yellow-600' :
                deputado.estatisticas.taxa_assiduidade >= 0.5 ? 'text-orange-600' :
                'text-red-600'
              }`} />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Taxa Assiduidade</p>
                <p className={`text-2xl font-bold ${
                  deputado.estatisticas.taxa_assiduidade >= 0.9 ? 'text-green-700' :
                  deputado.estatisticas.taxa_assiduidade >= 0.8 ? 'text-blue-700' :
                  deputado.estatisticas.taxa_assiduidade >= 0.7 ? 'text-yellow-700' :
                  deputado.estatisticas.taxa_assiduidade >= 0.5 ? 'text-orange-700' :
                  'text-red-700'
                }`}>
                  {(deputado.estatisticas.taxa_assiduidade * 100).toFixed(1)}%
                </p>
                <div className={`text-xs font-medium mt-1 ${
                  deputado.estatisticas.taxa_assiduidade >= 0.9 ? 'text-green-600' :
                  deputado.estatisticas.taxa_assiduidade >= 0.8 ? 'text-blue-600' :
                  deputado.estatisticas.taxa_assiduidade >= 0.7 ? 'text-yellow-600' :
                  deputado.estatisticas.taxa_assiduidade >= 0.5 ? 'text-orange-600' :
                  'text-red-600'
                }`}>
                  {deputado.estatisticas.taxa_assiduidade >= 0.9 ? 'Excelente' :
                   deputado.estatisticas.taxa_assiduidade >= 0.8 ? 'Muito Boa' :
                   deputado.estatisticas.taxa_assiduidade >= 0.7 ? 'Boa' :
                   deputado.estatisticas.taxa_assiduidade >= 0.5 ? 'Razoável' :
                   'Baixa'}
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <Calendar className="h-8 w-8 text-orange-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Mandatos</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-2xl font-bold text-gray-900">
                    {deputado.estatisticas.total_mandatos}
                  </p>
                  {deputado.estatisticas.legislaturas_servidas && (
                    <span className="text-xs px-2 py-1 bg-orange-50 text-orange-700 rounded-full">
                      {deputado.estatisticas.legislaturas_servidas.includes(',') 
                        ? `Legs. ${deputado.estatisticas.legislaturas_servidas}`
                        : `Leg. ${deputado.estatisticas.legislaturas_servidas}`}
                    </span>
                  )}
                </div>
                {deputado.estatisticas.anos_servico > 0 && (
                  <p className="text-sm text-gray-500 mt-1">
                    {deputado.estatisticas.anos_servico} anos de serviço
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Overview Estatísticas de Atividade */}
        {atividades?.statistics && (
          <div className="bg-white rounded-lg shadow-sm border mb-8">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Resumo de Atividade Parlamentar</h3>
              <p className="text-sm text-gray-500 mt-1">Atividade na legislatura atual vs. total da carreira</p>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Intervenções */}
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-3 bg-blue-500 rounded-lg shadow-sm">
                      <MessageSquare className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-blue-900 uppercase tracking-wide mb-3">
                      Intervenções
                    </h4>
                    <div className="space-y-2">
                      <div className="flex items-baseline justify-between">
                        <span className="text-sm text-blue-700">Atual</span>
                        <span className="text-2xl font-bold text-blue-900">
                          {atividades.statistics.current_legislature.intervencoes_count}
                        </span>
                      </div>
                      <div className="flex items-baseline justify-between border-t border-blue-200 pt-2">
                        <span className="text-xs text-blue-600">Total carreira</span>
                        <span className="text-lg font-semibold text-blue-700">
                          {atividades.statistics.total_career.intervencoes_count}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Iniciativas */}
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-3 bg-green-500 rounded-lg shadow-sm">
                      <FileText className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-green-900 uppercase tracking-wide mb-3">
                      Iniciativas
                    </h4>
                    <div className="space-y-2">
                      <div className="flex items-baseline justify-between">
                        <span className="text-sm text-green-700">Atual</span>
                        <span className="text-2xl font-bold text-green-900">
                          {atividades.statistics.current_legislature.iniciativas_count}
                        </span>
                      </div>
                      <div className="flex items-baseline justify-between border-t border-green-200 pt-2">
                        <span className="text-xs text-green-600">Total carreira</span>
                        <span className="text-lg font-semibold text-green-700">
                          {atividades.statistics.total_career.iniciativas_count}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Votações */}
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-3 bg-purple-500 rounded-lg shadow-sm">
                      <Vote className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-purple-900 uppercase tracking-wide mb-3">
                      Votações
                    </h4>
                    <div className="space-y-2">
                      <div className="flex items-baseline justify-between">
                        <span className="text-sm text-purple-700">Atual</span>
                        <span className="text-2xl font-bold text-purple-900">
                          {atividades.statistics.current_legislature.votacoes_count}
                        </span>
                      </div>
                      <div className="flex items-baseline justify-between border-t border-purple-200 pt-2">
                        <span className="text-xs text-purple-600">Total carreira</span>
                        <span className="text-lg font-semibold text-purple-700">
                          {atividades.statistics.total_career.votacoes_count}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Taxa de Presença */}
                {atividades.statistics.current_legislature.attendance_rate !== undefined && (
                  <div className="bg-gradient-to-br from-orange-50 to-red-100 rounded-lg border border-orange-200 p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="p-3 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg shadow-sm">
                        <Activity className="h-6 w-6 text-white" />
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-orange-900 uppercase tracking-wide mb-3">
                        Taxa de Presença
                      </h4>
                      <div className="space-y-2">
                        <div className="flex items-baseline justify-between">
                          <span className="text-sm text-orange-700">Atual</span>
                          <span className="text-2xl font-bold text-orange-900">
                            {(atividades.statistics.current_legislature.attendance_rate * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex items-baseline justify-between border-t border-orange-200 pt-2">
                          <span className="text-xs text-orange-600">Total carreira</span>
                          <span className="text-lg font-semibold text-orange-700">
                            {(atividades.statistics.total_career.attendance_rate * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <div className="mt-3 text-xs text-orange-600">
                        {atividades.statistics.current_legislature.total_sessions} sessões
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Quick insight footer */}
              <div className="mt-6 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-500 text-center">
                  Os números da "legislatura atual" referem-se ao mandato em curso. 
                  O "total carreira" inclui todos os mandatos anteriores deste deputado.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tabs de Atividade */}
        <div className="bg-white rounded-lg shadow-sm border">
          {/* Tab Headers */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => handleTabChange(tab.id)}
                    className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'biografia' && (
              <div>
                <div className="prose max-w-none">
                  {(deputado.nome_completo || deputado.data_nascimento || deputado.naturalidade || deputado.profissao || deputado.habilitacoes_academicas || (deputado.atividades_orgaos && deputado.atividades_orgaos.length > 0)) ? (
                    <div className="space-y-6">
                      {/* Personal Information Section */}
                      {deputado.nome_completo && (
                        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
                          <div className="flex items-center mb-4">
                            <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center mr-3">
                              <User className="h-5 w-5 text-white" />
                            </div>
                            <h4 className="text-lg font-semibold text-gray-900">Informações Pessoais</h4>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-3">
                              <div>
                                <span className="text-sm font-medium text-indigo-600 uppercase tracking-wide">Nome Completo</span>
                                <p className="text-gray-900 font-medium">{deputado.nome_completo}</p>
                              </div>
                              {deputado.naturalidade && (
                                <div>
                                  <span className="text-sm font-medium text-indigo-600 uppercase tracking-wide">Naturalidade</span>
                                  <p className="text-gray-900">{deputado.naturalidade}</p>
                                </div>
                              )}
                            </div>
                            <div className="space-y-3">
                              {deputado.data_nascimento && (
                                <div>
                                  <span className="text-sm font-medium text-indigo-600 uppercase tracking-wide">Data de Nascimento</span>
                                  <p className="text-gray-900">
                                    {new Date(deputado.data_nascimento).toLocaleDateString('pt-PT')}
                                    {(() => {
                                      const birthDate = new Date(deputado.data_nascimento);
                                      const today = new Date();
                                      const age = today.getFullYear() - birthDate.getFullYear() - 
                                        (today.getMonth() < birthDate.getMonth() || 
                                         (today.getMonth() === birthDate.getMonth() && today.getDate() < birthDate.getDate()) ? 1 : 0);
                                      return age > 0 ? ` ` : '';
                                    })()}
                                    {(() => {
                                      const birthDate = new Date(deputado.data_nascimento);
                                      const today = new Date();
                                      const age = today.getFullYear() - birthDate.getFullYear() - 
                                        (today.getMonth() < birthDate.getMonth() || 
                                         (today.getMonth() === birthDate.getMonth() && today.getDate() < birthDate.getDate()) ? 1 : 0);
                                      return age > 0 ? <span className="text-sm text-gray-600">({age} anos)</span> : null;
                                    })()}
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {/* Biografia Header - only show if there are other sections */}
                      {(deputado.profissao || deputado.habilitacoes_academicas || deputado.biografia || (deputado.atividades_orgaos && deputado.atividades_orgaos.length > 0)) && (
                        <h3 className="text-lg font-semibold text-gray-900 mb-4 mt-8">
                          Biografia
                        </h3>
                      )}
                      
                      {deputado.profissao && (
                        <div className="relative">
                          <div className="flex">
                            <div className="w-1 bg-blue-500 rounded-full mr-4 flex-shrink-0"></div>
                            <div className="flex-1">
                              <div className="flex items-center mb-3">
                                <Briefcase className="h-5 w-5 text-blue-500 mr-2" />
                                <h4 className="font-semibold text-gray-900">Profissão</h4>
                              </div>
                              <p className="text-gray-700 text-base leading-relaxed pl-7">
                                {deputado.profissao}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {deputado.habilitacoes_academicas && (
                        <div className="relative">
                          <div className="flex">
                            <div className="w-1 bg-green-500 rounded-full mr-4 flex-shrink-0"></div>
                            <div className="flex-1">
                              <div className="flex items-center mb-3">
                                <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                                </svg>
                                <h4 className="font-semibold text-gray-900">Habilitações Académicas</h4>
                              </div>
                              <div className="text-gray-700 pl-7 space-y-2">
                                {deputado.habilitacoes_academicas.split(';').map((hab, index) => (
                                  <div key={index} className="flex items-start">
                                    <div className="w-2 h-2 bg-green-400 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                                    <span className="text-base leading-relaxed">{hab.trim()}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {deputado.biografia && (
                        <div className="relative">
                          <div className="flex">
                            <div className="w-1 bg-purple-500 rounded-full mr-4 flex-shrink-0"></div>
                            <div className="flex-1">
                              <div className="flex items-center mb-3">
                                <User className="h-5 w-5 text-purple-500 mr-2" />
                                <h4 className="font-semibold text-gray-900">Biografia</h4>
                              </div>
                              <div className="text-gray-700 text-base leading-relaxed whitespace-pre-line pl-7">
                                {deputado.biografia}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {deputado.atividades_orgaos && deputado.atividades_orgaos.length > 0 && (
                        <div className="relative">
                          <div className="flex">
                            <div className="w-1 bg-orange-500 rounded-full mr-4 flex-shrink-0"></div>
                            <div className="flex-1">
                              <div className="flex items-center mb-3">
                                <svg className="h-5 w-5 text-orange-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                                </svg>
                                <h4 className="font-semibold text-gray-900">Atividade em Órgãos Parlamentares</h4>
                              </div>
                              <div className="space-y-3 pl-7">
                                {deputado.atividades_orgaos.map((orgao, index) => (
                                  <div key={index} className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <div className="flex items-center mb-2">
                                          <h5 className="font-medium text-gray-900">
                                            {orgao.nome}
                                            {orgao.sigla && (
                                              <span className="ml-2 text-sm text-orange-600 font-normal">({orgao.sigla})</span>
                                            )}
                                          </h5>
                                        </div>
                                        <div className="flex flex-wrap items-center gap-3 text-sm">
                                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                            orgao.titular 
                                              ? 'bg-green-100 text-green-800' 
                                              : 'bg-yellow-100 text-yellow-800'
                                          }`}>
                                            {orgao.tipo_membro}
                                          </span>
                                          {orgao.cargo !== 'membro' && (
                                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                              {orgao.cargo === 'presidente' ? 'Presidente' :
                                               orgao.cargo === 'vice_presidente' ? 'Vice-Presidente' :
                                               orgao.cargo === 'secretario' ? 'Secretário' : 
                                               orgao.cargo}
                                            </span>
                                          )}
                                          {orgao.observacoes && (
                                            <span className="text-gray-500">
                                              {orgao.observacoes}
                                            </span>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                        <User className="h-8 w-8 text-gray-400" />
                      </div>
                      <p className="text-gray-500 text-lg font-medium mb-2">Informações biográficas não disponíveis</p>
                      <p className="text-sm text-gray-400">
                        Dados biográficos não foram fornecidos para este deputado
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'intervencoes' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Intervenções Parlamentares
                    </h3>
                    {totalInterventions > 0 && (
                      <p className="text-sm text-gray-500 mt-1">
                        {interventionTypeFilter 
                          ? `${atividades?.intervencoes?.length || 0} de ${totalInterventions} intervenções (filtrado por "${interventionTypeFilter}")`
                          : `${totalInterventions} intervenções`
                        }
                      </p>
                    )}
                  </div>
                  {atividades && atividades.intervencoes.length > 0 && (
                    <div className="flex gap-3">
                      <select 
                        value={interventionTypeFilter}
                        onChange={(e) => {
                          const newType = e.target.value;
                          setInterventionTypeFilter(newType);
                          setCurrentPage(1); // Reset to page 1 when filtering
                          updateInterventionParams({ tipo_intervencao: newType, page: 1 });
                        }}
                        className="border border-gray-300 rounded-md px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">Todos os tipos</option>
                        <option value="Interpelação">Interpelação à mesa</option>
                        <option value="Pedido">Pedido de esclarecimento</option>
                        <option value="Declaração">Declaração política</option>
                        <option value="Pergunta">Pergunta</option>
                      </select>
                      <select 
                        value={interventionSort}
                        onChange={(e) => {
                          const newSort = e.target.value;
                          setInterventionSort(newSort);
                          updateInterventionParams({ ordenacao_intervencoes: newSort });
                        }}
                        className="border border-gray-300 rounded-md px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="newest">Mais recentes</option>
                        <option value="oldest">Mais antigas</option>
                        <option value="type">Por tipo</option>
                      </select>
                    </div>
                  )}
                </div>

                {atividades && atividades.intervencoes.length > 0 ? (
                  <div className="space-y-6">
                    {(() => {
                      // Interventions are already filtered and sorted by the API
                      const interventions = atividades.intervencoes || [];
                      
                      // Helper functions
                      const getTipoColor = (tipo) => {
                        if (tipo?.includes('Interpelação')) return 'bg-blue-100 text-blue-800 border-blue-200';
                        if (tipo?.includes('Declaração')) return 'bg-green-100 text-green-800 border-green-200';
                        if (tipo?.includes('Pedido')) return 'bg-orange-100 text-orange-800 border-orange-200';
                        if (tipo?.includes('Pergunta')) return 'bg-purple-100 text-purple-800 border-purple-200';
                        return 'bg-gray-100 text-gray-800 border-gray-200';
                      };

                      const getQualidadeColor = (qualidade) => {
                        if (qualidade === 'Deputado') return 'bg-blue-50 text-blue-700 border-blue-200';
                        if (qualidade === 'P.A.R.') return 'bg-indigo-50 text-indigo-700 border-indigo-200';
                        return 'bg-gray-50 text-gray-700 border-gray-200';
                      };
                      
                      return interventions.map((intervencao, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow bg-white">
                          {/* Context badges */}
                          <div className="flex gap-2 mb-4">
                            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getTipoColor(intervencao.tipo)}`}>
                              {intervencao.tipo}
                            </span>
                            {intervencao.qualidade && (
                              <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getQualidadeColor(intervencao.qualidade)}`}>
                                {intervencao.qualidade}
                              </span>
                            )}
                            {intervencao.sessao_numero && (
                              <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full border border-gray-200">
                                Sessão {intervencao.sessao_numero}
                              </span>
                            )}
                          </div>

                          <div className="flex gap-4">
                            {/* Video Thumbnail */}
                            {intervencao.url_video && intervencao.thumbnail_url ? (
                              <div className="relative flex-shrink-0">
                                <div className="w-36 h-22 rounded-lg overflow-hidden bg-gray-100 relative group cursor-pointer shadow-sm"
                                     onClick={() => window.open(intervencao.url_video, '_blank')}>
                                  <img 
                                    src={intervencao.thumbnail_url}
                                    alt="Video thumbnail"
                                    className="w-full h-full object-cover"
                                    onError={(e) => {
                                      e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTQ0IiBoZWlnaHQ9IjkwIiB2aWV3Qm94PSIwIDAgMTQ0IDkwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8cmVjdCB3aWR0aD0iMTQ0IiBoZWlnaHQ9IjkwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik02MCA0NUw4NCA1N0w2MCA2OVY0NVoiIGZpbGw9IiM5Q0EzQUYiLz4KPC9zdmc+';
                                    }}
                                  />
                                  {/* Play Button Overlay */}
                                  <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                    <div className="bg-white bg-opacity-95 rounded-full p-2 shadow-lg">
                                      <Play className="h-6 w-6 text-gray-900 ml-1" />
                                    </div>
                                  </div>
                                  {/* Duration Badge */}
                                  {intervencao.duracao_video && (
                                    <div className="absolute bottom-1 right-1 bg-black bg-opacity-80 text-white text-xs px-2 py-1 rounded shadow">
                                      <Clock className="h-3 w-3 inline mr-1" />
                                      {intervencao.duracao_video}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ) : intervencao.url_video ? (
                              // Video without thumbnail
                              <div className="relative flex-shrink-0">
                                <div className="w-36 h-22 rounded-lg overflow-hidden bg-gradient-to-br from-blue-100 to-blue-200 relative group cursor-pointer flex items-center justify-center shadow-sm border border-blue-200"
                                     onClick={() => window.open(intervencao.url_video, '_blank')}>
                                  <Play className="h-8 w-8 text-blue-600" />
                                  <div className="absolute inset-0 bg-blue-600 bg-opacity-10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                                </div>
                              </div>
                            ) : null}
                            
                            {/* Content */}
                            <div className="flex-1 min-w-0">
                              {/* Header with date and action buttons */}
                              <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-3 text-sm text-gray-500">
                                  <div className="flex items-center">
                                    <Calendar className="h-4 w-4 mr-1" />
                                    {new Date(intervencao.data).toLocaleDateString('pt-PT')}
                                  </div>
                                </div>
                                
                                {/* Action Buttons */}
                                <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                                  {intervencao.url_video && (
                                    <button
                                      onClick={() => window.open(intervencao.url_video, '_blank')}
                                      className="inline-flex items-center px-3 py-1.5 border border-blue-300 text-sm font-medium rounded-md text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors shadow-sm whitespace-nowrap"
                                    >
                                      <Play className="h-4 w-4 mr-1" />
                                      Ver Vídeo
                                    </button>
                                  )}
                                  {intervencao.publicacao?.url_diario && (
                                    <button
                                      onClick={() => window.open(intervencao.publicacao.url_diario, '_blank')}
                                      className="inline-flex items-center px-3 py-1.5 border border-amber-300 text-sm font-medium rounded-md text-amber-700 bg-amber-50 hover:bg-amber-100 transition-colors shadow-sm whitespace-nowrap"
                                    >
                                      <ExternalLink className="h-4 w-4 mr-1" />
                                      {intervencao.publicacao.pub_numero ? `DR ${intervencao.publicacao.pub_numero}` : 'Diário'}
                                    </button>
                                  )}
                                </div>
                              </div>

                              {/* Subject/Title - separate line for long titles */}
                              {intervencao.assunto && (
                                <div className="mb-3">
                                  <h4 className="text-gray-800 font-medium text-sm leading-5 line-clamp-2">
                                    {intervencao.assunto}
                                  </h4>
                                </div>
                              )}
                              
                              {/* Summary */}
                              {intervencao.resumo && (
                                <p className="text-gray-700 text-sm leading-relaxed mb-3 line-clamp-3">
                                  {intervencao.resumo}
                                </p>
                              )}
                              
                              {/* Additional Info */}
                              {(intervencao.sumario || intervencao.fase_sessao) && (
                                <div className="mt-3 pt-3 border-t border-gray-100">
                                  {intervencao.sumario && (
                                    <p className="text-sm text-gray-600 mb-2">
                                      <span className="font-medium text-gray-700">Sumário:</span> {intervencao.sumario}
                                    </p>
                                  )}
                                  <div className="flex gap-2 flex-wrap">
                                    {intervencao.fase_sessao && (
                                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
                                        {intervencao.fase_sessao}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              )}

                              {/* Publication metadata */}
                              {intervencao.publicacao && (
                                <div className="mt-3 pt-3 border-t border-gray-100">
                                  <div className="flex gap-4 text-xs text-gray-500">
                                    {intervencao.publicacao.pub_tipo && (
                                      <span className="flex items-center">
                                        📰 {intervencao.publicacao.pub_tipo}
                                      </span>
                                    )}
                                    {intervencao.publicacao.pub_data && (
                                      <span className="flex items-center">
                                        📅 Pub: {new Date(intervencao.publicacao.pub_data).toLocaleDateString('pt-PT')}
                                      </span>
                                    )}
                                    {intervencao.publicacao.paginas && (
                                      <span className="flex items-center">
                                        📄 Pág. {intervencao.publicacao.paginas}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ));
                    })()}
                    
                    {/* Pagination Controls */}
                    {totalPages > 1 && (
                      <div className="flex justify-center items-center gap-2 mt-8 pt-6 border-t border-gray-200">
                        <button
                          onClick={() => {
                            if (currentPage > 1) {
                              const newPage = currentPage - 1;
                              setCurrentPage(newPage);
                              updateInterventionParams({ page: newPage });
                            }
                          }}
                          disabled={currentPage <= 1}
                          className="px-3 py-2 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Anterior
                        </button>
                        
                        <span className="px-4 py-2 text-sm text-gray-700">
                          Página {currentPage} de {totalPages}
                        </span>
                        
                        <button
                          onClick={() => {
                            if (currentPage < totalPages) {
                              const newPage = currentPage + 1;
                              setCurrentPage(newPage);
                              updateInterventionParams({ page: newPage });
                            }
                          }}
                          disabled={currentPage >= totalPages}
                          className="px-3 py-2 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Próxima
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 text-lg font-medium mb-2">Nenhuma intervenção registada</p>
                    <p className="text-sm text-gray-400">
                      Os dados de intervenções serão carregados em futuras atualizações
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'iniciativas' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Iniciativas Legislativas
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      Projetos de lei e resoluções apresentados pelo deputado
                    </p>
                  </div>
                  {atividades && atividades.iniciativas && atividades.iniciativas.length > 0 && (
                    <div className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                      {atividades.iniciativas.length} iniciativas
                    </div>
                  )}
                </div>
                
                {atividades && atividades.iniciativas && atividades.iniciativas.length > 0 ? (
                  <div className="space-y-4">
                    {atividades.iniciativas.map((iniciativa, index) => {
                      // Helper function to get type styling
                      const getTypeStyle = (tipo) => {
                        switch (tipo) {
                          case 'J':
                            return 'bg-blue-100 text-blue-800 border-blue-200';
                          case 'R':
                            return 'bg-green-100 text-green-800 border-green-200';
                          case 'P':
                            return 'bg-purple-100 text-purple-800 border-purple-200';
                          case 'D':
                            return 'bg-orange-100 text-orange-800 border-orange-200';
                          default:
                            return 'bg-gray-100 text-gray-800 border-gray-200';
                        }
                      };

                      // Helper function to get status styling
                      const getStatusStyle = (estado) => {
                        if (!estado) return null;
                        switch (estado?.toLowerCase()) {
                          case 'aprovado':
                            return 'bg-green-50 text-green-700 border-green-200';
                          case 'rejeitado':
                            return 'bg-red-50 text-red-700 border-red-200';
                          case 'em votação':
                            return 'bg-yellow-50 text-yellow-700 border-yellow-200';
                          case 'retirado':
                            return 'bg-gray-50 text-gray-700 border-gray-200';
                          default:
                            return 'bg-blue-50 text-blue-700 border-blue-200';
                        }
                      };

                      return (
                        <div key={index} className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-all duration-200 hover:border-gray-300">
                          {/* Header with type and date */}
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3 flex-wrap">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getTypeStyle(iniciativa.tipo)}`}>
                                {iniciativa.tipo_descricao || iniciativa.tipo}
                              </span>
                              {iniciativa.estado && (
                                <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusStyle(iniciativa.estado)}`}>
                                  {iniciativa.estado}
                                </span>
                              )}
                            </div>
                            <div className="text-sm text-gray-500 flex items-center flex-shrink-0 ml-4">
                              <Calendar className="h-4 w-4 mr-1" />
                              {new Date(iniciativa.data_apresentacao || iniciativa.data).toLocaleDateString('pt-PT')}
                            </div>
                          </div>

                          {/* Title */}
                          <h4 className="font-semibold text-gray-900 mb-3 text-lg leading-tight">
                            {iniciativa.titulo}
                          </h4>

                          {/* Details */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4 text-sm text-gray-600">
                              <div className="flex items-center">
                                <FileText className="h-4 w-4 mr-1" />
                                <span>Tipo: {iniciativa.tipo}</span>
                              </div>
                              {iniciativa.resultado && (
                                <div className="flex items-center">
                                  <Activity className="h-4 w-4 mr-1" />
                                  <span>Resultado: {iniciativa.resultado}</span>
                                </div>
                              )}
                            </div>
                            
                            {/* Action button */}
                            <button 
                              onClick={() => toggleInitiativeDetails(index)}
                              className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center transition-colors"
                            >
                              {expandedInitiatives.has(index) ? 'Ocultar detalhes' : 'Ver detalhes'}
                              <svg 
                                className={`h-4 w-4 ml-1 transition-transform duration-200 ${
                                  expandedInitiatives.has(index) ? 'rotate-90' : ''
                                }`} 
                                fill="none" 
                                stroke="currentColor" 
                                viewBox="0 0 24 24"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                            </button>
                          </div>

                          {/* Progress indicator based on status */}
                          {iniciativa.estado && (
                            <div className="mt-4 pt-4 border-t border-gray-100">
                              <div className="flex items-center text-xs text-gray-500">
                                <div className="flex-1 bg-gray-200 rounded-full h-1 mr-3">
                                  <div 
                                    className={`h-1 rounded-full transition-all duration-300 ${
                                      iniciativa.estado?.toLowerCase() === 'aprovado' ? 'bg-green-500 w-full' :
                                      iniciativa.estado?.toLowerCase() === 'rejeitado' ? 'bg-red-500 w-full' :
                                      iniciativa.estado?.toLowerCase() === 'em votação' ? 'bg-yellow-500 w-3/4' :
                                      'bg-blue-500 w-1/2'
                                    }`}
                                  />
                                </div>
                                <span className="text-xs font-medium">
                                  {iniciativa.estado || 'Em análise'}
                                </span>
                              </div>
                            </div>
                          )}

                          {/* Expandable Details Section */}
                          {expandedInitiatives.has(index) && (
                            <div className="mt-4 pt-4 border-t border-gray-100 animate-fadeIn">
                              <h5 className="font-semibold text-gray-900 mb-3">Detalhes da Iniciativa</h5>
                              
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                {/* Left Column */}
                                <div className="space-y-3">
                                  <div>
                                    <span className="font-medium text-gray-700">Tipo:</span>
                                    <p className="text-gray-600 mt-1">
                                      {iniciativa.tipo_descricao} ({iniciativa.tipo})
                                    </p>
                                  </div>
                                  
                                  <div>
                                    <span className="font-medium text-gray-700">Data de Apresentação:</span>
                                    <p className="text-gray-600 mt-1">
                                      {new Date(iniciativa.data_apresentacao || iniciativa.data).toLocaleDateString('pt-PT', {
                                        weekday: 'long',
                                        year: 'numeric',
                                        month: 'long',
                                        day: 'numeric'
                                      })}
                                    </p>
                                  </div>

                                  {iniciativa.estado && (
                                    <div>
                                      <span className="font-medium text-gray-700">Estado Atual:</span>
                                      <p className="text-gray-600 mt-1">{iniciativa.estado}</p>
                                    </div>
                                  )}
                                </div>

                                {/* Right Column */}
                                <div className="space-y-3">
                                  {iniciativa.resultado && (
                                    <div>
                                      <span className="font-medium text-gray-700">Resultado:</span>
                                      <p className="text-gray-600 mt-1">{iniciativa.resultado}</p>
                                    </div>
                                  )}
                                  
                                  <div>
                                    <span className="font-medium text-gray-700">Categoria:</span>
                                    <p className="text-gray-600 mt-1">
                                      {iniciativa.tipo === 'J' ? 'Projeto de Lei' :
                                       iniciativa.tipo === 'R' ? 'Projeto de Resolução' :
                                       iniciativa.tipo === 'P' ? 'Proposta' :
                                       iniciativa.tipo === 'D' ? 'Decreto' :
                                       'Iniciativa Legislativa'}
                                    </p>
                                  </div>
                                  
                                  <div>
                                    <span className="font-medium text-gray-700">Status:</span>
                                    <p className="text-gray-600 mt-1">
                                      {iniciativa.estado ? 
                                        `Em fase: ${iniciativa.estado}` : 
                                        'Em análise nas comissões competentes'
                                      }
                                    </p>
                                  </div>
                                </div>
                              </div>

                              {/* Full Title Section */}
                              <div className="mt-4 pt-4 border-t border-gray-50">
                                <span className="font-medium text-gray-700">Título Completo:</span>
                                <p className="text-gray-600 mt-2 leading-relaxed">
                                  {iniciativa.titulo}
                                </p>
                              </div>

                              {/* Additional Actions */}
                              <div className="mt-4 pt-4 border-t border-gray-50">
                                <div className="flex gap-2 flex-wrap">
                                  <button 
                                    onClick={() => {
                                      // Use direct Parliament URL if available, fallback to search
                                      const url = iniciativa.urls?.documento || 
                                        `https://www.parlamento.pt/site/search/Pages/pesquisa.aspx?sq=${encodeURIComponent(iniciativa.titulo)}`;
                                      window.open(url, '_blank');
                                    }}
                                    className="text-xs bg-blue-50 text-blue-700 px-3 py-1.5 rounded-full hover:bg-blue-100 transition-colors"
                                  >
                                    📄 Ver Documento
                                  </button>
                                  <button 
                                    onClick={() => {
                                      // Use direct debates URL if available, fallback to search
                                      const url = iniciativa.urls?.debates || 
                                        `https://www.parlamento.pt/ActividadeParlamentar/Paginas/DetalhePerguntaRequerimento.aspx?txt=${encodeURIComponent(iniciativa.titulo)}`;
                                      window.open(url, '_blank');
                                    }}
                                    className="text-xs bg-gray-50 text-gray-700 px-3 py-1.5 rounded-full hover:bg-gray-100 transition-colors"
                                  >
                                    📊 Histórico de Votações
                                  </button>
                                  <button 
                                    onClick={() => {
                                      // Use direct official URL if available, fallback to search
                                      const url = iniciativa.urls?.oficial || 
                                        `https://www.parlamento.pt/ActividadeParlamentar/Paginas/Iniciativas.aspx?txt=${encodeURIComponent(iniciativa.titulo)}`;
                                      window.open(url, '_blank');
                                    }}
                                    className="text-xs bg-green-50 text-green-700 px-3 py-1.5 rounded-full hover:bg-green-100 transition-colors"
                                  >
                                    🔗 Link Oficial
                                  </button>
                                </div>
                                <p className="text-xs text-gray-400 mt-2">
                                  {iniciativa.urls?.documento || iniciativa.urls?.debates || iniciativa.urls?.oficial ? 
                                    '🔗 Links diretos para documentos oficiais do Parlamento' :
                                    'ℹ️ Links direcionam para pesquisa no site oficial do Parlamento'
                                  }
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                      <FileText className="h-8 w-8 text-gray-400" />
                    </div>
                    <p className="text-gray-500 text-lg font-medium mb-2">
                      Nenhuma iniciativa registada
                    </p>
                    <p className="text-sm text-gray-400">
                      Este deputado ainda não apresentou iniciativas legislativas nesta legislatura
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'votacoes' && (
              <VotingAnalytics 
                deputadoId={cadId} 
                legislatura={deputado?.legislatura?.numero || 'XVII'} 
              />
            )}

            {activeTab === 'conflitos-interesse' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Conflitos de Interesse
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      Declaração de conflitos de interesse conforme exigido por lei
                    </p>
                  </div>
                </div>

                {conflitosInteresse ? (
                  <div className="space-y-6">
                    {/* Status Card */}
                    <div className={`rounded-lg border-2 p-6 ${
                      conflitosInteresse.has_conflict_potential 
                        ? 'bg-amber-50 border-amber-200' 
                        : 'bg-green-50 border-green-200'
                    }`}>
                      <div className="flex items-start">
                        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                          conflitosInteresse.has_conflict_potential 
                            ? 'bg-amber-100' 
                            : 'bg-green-100'
                        }`}>
                          {conflitosInteresse.has_conflict_potential ? (
                            <AlertTriangle className="h-5 w-5 text-amber-600" />
                          ) : (
                            <Shield className="h-5 w-5 text-green-600" />
                          )}
                        </div>
                        <div className="ml-4 flex-1">
                          <h4 className={`text-lg font-semibold ${
                            conflitosInteresse.has_conflict_potential 
                              ? 'text-amber-900' 
                              : 'text-green-900'
                          }`}>
                            {conflitosInteresse.exclusivity_description}
                          </h4>
                          <p className={`text-sm mt-1 ${
                            conflitosInteresse.has_conflict_potential 
                              ? 'text-amber-700' 
                              : 'text-green-700'
                          }`}>
                            {conflitosInteresse.has_conflict_potential 
                              ? 'Deputado exerce atividades não exclusivas que podem gerar conflitos de interesse'
                              : 'Deputado exerce mandato em regime de exclusividade'
                            }
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Personal Information */}
                    <div className="bg-white rounded-lg border shadow-sm">
                      <div className="px-6 py-4 border-b border-gray-200">
                        <h4 className="text-lg font-medium text-gray-900 flex items-center">
                          <User className="h-5 w-5 text-blue-600 mr-2" />
                          Informações Pessoais
                        </h4>
                      </div>
                      <div className="px-6 py-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div>
                            <label className="text-sm font-medium text-gray-600 uppercase tracking-wide">
                              Nome Completo
                            </label>
                            <p className="text-gray-900 font-medium mt-1">
                              {conflitosInteresse.full_name}
                            </p>
                          </div>
                          
                          {conflitosInteresse.dgf_number && (
                            <div>
                              <label className="text-sm font-medium text-gray-600 uppercase tracking-wide">
                                Número DGF
                              </label>
                              <p className="text-gray-900 mt-1">
                                {conflitosInteresse.dgf_number}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Marital Status and Regime */}
                    {(conflitosInteresse.marital_status || conflitosInteresse.matrimonial_regime || conflitosInteresse.spouse_name) && (
                      <div className="bg-white rounded-lg border shadow-sm">
                        <div className="px-6 py-4 border-b border-gray-200">
                          <h4 className="text-lg font-medium text-gray-900 flex items-center">
                            <Heart className="h-5 w-5 text-pink-600 mr-2" />
                            Estado Civil e Regime Matrimonial
                          </h4>
                        </div>
                        <div className="px-6 py-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {conflitosInteresse.marital_status && (
                              <div>
                                <label className="text-sm font-medium text-gray-600 uppercase tracking-wide">
                                  Estado Civil
                                </label>
                                <p className="text-gray-900 mt-1">
                                  {conflitosInteresse.marital_status}
                                </p>
                              </div>
                            )}
                            
                            {conflitosInteresse.matrimonial_regime && (
                              <div>
                                <label className="text-sm font-medium text-gray-600 uppercase tracking-wide">
                                  Regime Matrimonial
                                </label>
                                <p className="text-gray-900 mt-1">
                                  {conflitosInteresse.matrimonial_regime}
                                </p>
                              </div>
                            )}
                            
                            {conflitosInteresse.spouse_name && (
                              <div className="md:col-span-2 lg:col-span-1">
                                <label className="text-sm font-medium text-gray-600 uppercase tracking-wide">
                                  Nome do Cônjuge
                                </label>
                                <div className="mt-1">
                                  {conflitosInteresse.spouse_deputy ? (
                                    <div className="space-y-2">
                                      <Link
                                        to={getDeputadoUrl(conflitosInteresse.spouse_deputy.cad_id || conflitosInteresse.spouse_deputy.id)}
                                        className="text-blue-600 hover:text-blue-800 font-medium transition-colors block"
                                      >
                                        {conflitosInteresse.spouse_name}
                                      </Link>
                                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                        <Users className="h-3 w-3 mr-1" />
                                        Também Deputado/a ({conflitosInteresse.spouse_deputy.partido_sigla})
                                      </span>
                                    </div>
                                  ) : (
                                    <p className="text-gray-900 font-medium">
                                      {conflitosInteresse.spouse_name}
                                    </p>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Transparency Note */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex">
                        <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
                        <div className="ml-3">
                          <h5 className="text-sm font-medium text-blue-900">
                            Transparência e Integridade
                          </h5>
                          <p className="text-sm text-blue-700 mt-1">
                            Esta informação é disponibilizada em cumprimento das obrigações de transparência 
                            dos deputados, conforme estabelecido na legislação parlamentar portuguesa.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                      <Shield className="h-8 w-8 text-gray-400" />
                    </div>
                    <p className="text-gray-500 text-lg font-medium mb-2">
                      Dados de conflitos de interesse não disponíveis
                    </p>
                    <p className="text-sm text-gray-400">
                      As informações sobre conflitos de interesse não foram encontradas para este deputado
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'attendance' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Registo de Presenças
                  </h3>
                </div>

                {attendanceData ? (
                  <div className="space-y-6">
                    {/* Summary Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                      <div className="bg-white rounded-lg border p-4">
                        <div className="flex items-center">
                          <div className="p-2 bg-blue-100 rounded-lg">
                            <Activity className="h-5 w-5 text-blue-600" />
                          </div>
                          <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Total Sessões</p>
                            <p className="text-xl font-bold text-gray-900">{attendanceData.summary.total_sessions}</p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="bg-white rounded-lg border p-4">
                        <div className="flex items-center">
                          <div className="p-2 bg-green-100 rounded-lg">
                            <Activity className="h-5 w-5 text-green-600" />
                          </div>
                          <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Presente</p>
                            <p className="text-xl font-bold text-green-700">{attendanceData.summary.present}</p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="bg-white rounded-lg border p-4">
                        <div className="flex items-center">
                          <div className="p-2 bg-yellow-100 rounded-lg">
                            <Activity className="h-5 w-5 text-yellow-600" />
                          </div>
                          <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Falta Justificada</p>
                            <p className="text-xl font-bold text-yellow-700">{attendanceData.summary.justified_absence}</p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="bg-white rounded-lg border p-4">
                        <div className="flex items-center">
                          <div className="p-2 bg-red-100 rounded-lg">
                            <Activity className="h-5 w-5 text-red-600" />
                          </div>
                          <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Falta Injustificada</p>
                            <p className="text-xl font-bold text-red-700">{attendanceData.summary.unjustified_absence}</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Timeline */}
                    <div className="bg-white rounded-lg border">
                      <div className="px-6 py-4 border-b border-gray-200">
                        <h4 className="text-lg font-medium text-gray-900">Timeline de Presenças</h4>
                      </div>
                      <div className="p-6">
                        <div className="space-y-4">
                          {attendanceData.timeline.map((entry, index) => (
                            <div 
                              key={index} 
                              className="flex items-start space-x-4 p-4 rounded-lg border border-gray-100 hover:bg-gray-50"
                            >
                              <div className={`flex-shrink-0 w-3 h-3 rounded-full mt-2 ${
                                entry.status === 'success' ? 'bg-green-500' :
                                entry.status === 'warning' ? 'bg-yellow-500' :
                                entry.status === 'danger' ? 'bg-red-500' :
                                entry.status === 'info' ? 'bg-blue-500' :
                                'bg-gray-400'
                              }`}></div>
                              
                              <div className="flex-1">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center space-x-2">
                                    <span className="text-sm font-medium text-gray-900">
                                      {new Date(entry.date).toLocaleDateString('pt-PT')}
                                    </span>
                                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                      entry.status === 'success' ? 'bg-green-100 text-green-800' :
                                      entry.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                                      entry.status === 'danger' ? 'bg-red-100 text-red-800' :
                                      entry.status === 'info' ? 'bg-blue-100 text-blue-800' :
                                      'bg-gray-100 text-gray-800'
                                    }`}>
                                      {entry.attendance_description}
                                    </span>
                                  </div>
                                  <span className="text-xs text-gray-500">
                                    {entry.session_type}
                                  </span>
                                </div>
                                
                                {entry.reason && (
                                  <p className="text-sm text-gray-600 mt-1">
                                    <span className="font-medium">Motivo:</span> {entry.reason}
                                  </p>
                                )}
                                
                                {entry.justification && (
                                  <p className="text-sm text-gray-600 mt-1">
                                    <span className="font-medium">Justificação:</span> {entry.justification}
                                  </p>
                                )}
                                
                                {entry.observations && (
                                  <p className="text-sm text-gray-600 mt-1">
                                    <span className="font-medium">Observações:</span> {entry.observations}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                        
                        {attendanceData.timeline.length === 0 && (
                          <div className="text-center py-8">
                            <Activity className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                            <p className="text-gray-500">Nenhum registo de presença encontrado</p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Legend */}
                    <div className="bg-white rounded-lg border p-6">
                      <h4 className="text-lg font-medium text-gray-900 mb-4">Legenda dos Códigos</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {Object.entries(attendanceData.codes_legend).map(([code, info]) => (
                          <div key={code} className="flex items-center space-x-2">
                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              info.status === 'success' ? 'bg-green-100 text-green-800' :
                              info.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                              info.status === 'danger' ? 'bg-red-100 text-red-800' :
                              info.status === 'info' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {code}
                            </span>
                            <span className="text-sm text-gray-700">{info.description}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Activity className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-500">Dados de presença não disponíveis</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'mandatos-anteriores' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Mandatos Anteriores
                  </h3>
                </div>

                {deputado.mandatos_historico && deputado.mandatos_historico.length > 0 ? (
                  <div className="space-y-4">
                    {deputado.mandatos_historico.map((mandato, index) => (
                      <div 
                        key={index}
                        className={`bg-white rounded-lg border p-6 hover:shadow-md transition-shadow ${
                          mandato.is_current ? 'ring-2 ring-blue-500 bg-blue-50' : ''
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-3">
                              <h4 className="text-lg font-semibold text-gray-900">
                                {mandato.legislatura_nome}
                              </h4>
                              {mandato.is_current && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                  Atual
                                </span>
                              )}
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600 mb-4">
                              <div className="flex items-center">
                                <Calendar className="h-4 w-4 mr-2" />
                                <span>
                                  {new Date(mandato.mandato_inicio).toLocaleDateString('pt-PT')} - {' '}
                                  {mandato.mandato_fim 
                                    ? new Date(mandato.mandato_fim).toLocaleDateString('pt-PT')
                                    : 'Presente'
                                  }
                                </span>
                              </div>
                              
                              <div className="flex items-center">
                                <MapPin className="h-4 w-4 mr-2" />
                                <span>{mandato.circulo}</span>
                              </div>
                              
                              <div className="flex items-center">
                                <Briefcase className="h-4 w-4 mr-2" />
                                <span>{mandato.partido_sigla}</span>
                              </div>
                            </div>
                          </div>
                          
                          {mandato.is_current && (
                            <div className="flex flex-col gap-2">
                              <span className="inline-flex items-center px-3 py-2 border border-blue-300 shadow-sm text-sm font-medium rounded-md text-blue-700 bg-blue-50">
                                <Calendar className="h-4 w-4 mr-2" />
                                Legislatura Atual
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                      <Calendar className="h-8 w-8 text-gray-400" />
                    </div>
                    <p className="text-gray-500 text-lg font-medium mb-2">
                      Apenas um mandato registrado
                    </p>
                    <p className="text-sm text-gray-400">
                      Este deputado só tem registro de mandato na legislatura atual
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeputadoDetalhes;

