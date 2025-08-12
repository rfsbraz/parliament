import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Users, Building, Calendar, TrendingUp, Handshake, History, MapPin, Award, Target, Activity } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const ColigacaoDetalhes = () => {
  const { coligacaoId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [dados, setDados] = useState(null);
  const [deputados, setDeputados] = useState([]);
  const [partidos, setPartidos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get active tab from URL hash
  const getActiveTabFromUrl = () => {
    const hash = location.hash.replace('#', '');
    const validTabs = ['overview', 'deputados', 'partidos', 'timeline', 'performance'];
    return validTabs.includes(hash) ? hash : 'overview';
  };

  const [activeTab, setActiveTab] = useState(getActiveTabFromUrl());

  // Coalition colors based on political spectrum
  const spectrumColors = {
    'esquerda': '#DC2626',
    'centro-esquerda': '#F59E0B',
    'centro': '#6B7280',
    'centro-direita': '#3B82F6',
    'direita': '#1E40AF'
  };

  useEffect(() => {
    const handleHashChange = () => {
      setActiveTab(getActiveTabFromUrl());
    };

    window.addEventListener('hashchange', handleHashChange);
    setActiveTab(getActiveTabFromUrl());

    return () => {
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, [location.hash]);

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    navigate(`#${tabId}`, { replace: true });
  };

  useEffect(() => {
    if (!location.hash) {
      navigate('#overview', { replace: true });
    }
  }, [navigate, location.hash]);

  useEffect(() => {
    const fetchDados = async () => {
      try {
        setLoading(true);
        
        // Fetch coalition details
        const coligacaoResponse = await fetch(`/api/coligacoes/${encodeURIComponent(coligacaoId)}`);
        if (!coligacaoResponse.ok) {
          throw new Error('Erro ao carregar dados da coligação');
        }
        const coligacaoData = await coligacaoResponse.json();
        setDados(coligacaoData);

        // Fetch coalition deputies
        const deputadosResponse = await fetch(`/api/coligacoes/${encodeURIComponent(coligacaoId)}/deputados`);
        if (deputadosResponse.ok) {
          const deputadosData = await deputadosResponse.json();
          setDeputados(deputadosData.deputados || []);
        }

        // Fetch component parties
        const partidosResponse = await fetch(`/api/coligacoes/${encodeURIComponent(coligacaoId)}/partidos`);
        if (partidosResponse.ok) {
          const partidosData = await partidosResponse.json();
          setPartidos(partidosData.partidos || []);
        }

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (coligacaoId) {
      fetchDados();
    }
  }, [coligacaoId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando dados da coligação...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Erro: {error}</p>
          <Link to="/partidos" className="text-blue-600 hover:underline">
            Voltar aos partidos
          </Link>
        </div>
      </div>
    );
  }

  if (!dados) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Coligação não encontrada</p>
      </div>
    );
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-PT', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  // Coalition timeline data
  const timelineEvents = [
    dados.data_formacao && {
      date: dados.data_formacao,
      title: 'Formação da Coligação',
      description: `Criação da ${dados.nome}`,
      type: 'formation'
    },
    dados.data_dissolucao && {
      date: dados.data_dissolucao,
      title: 'Dissolução',
      description: 'Fim da coligação',
      type: 'dissolution'
    }
  ].filter(Boolean);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link 
                to="/partidos" 
                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                Voltar aos Partidos
              </Link>
            </div>
            <div className="flex items-center space-x-2">
              <Handshake className="h-5 w-5 text-blue-600" />
              <span className="text-sm font-medium text-gray-600">Coligação</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Coalition Header */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-sm border mb-8"
        >
          <div className="px-6 py-8">
            <div className="flex items-start justify-between mb-6">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h1 className="text-3xl font-bold text-gray-900">
                    {dados.sigla}
                  </h1>
                  <span 
                    className="px-3 py-1 rounded-full text-xs font-semibold text-white"
                    style={{ 
                      backgroundColor: spectrumColors[dados.espectro_politico] || '#6B7280' 
                    }}
                  >
                    {dados.espectro_politico || 'N/A'}
                  </span>
                  {dados.ativa && (
                    <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
                      Ativa
                    </span>
                  )}
                </div>
                <p className="text-xl text-gray-600 mb-4">{dados.nome}</p>
                
                {/* Key Information */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                  <div className="flex items-center text-gray-600">
                    <Calendar className="h-5 w-5 mr-2 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500">Formação</p>
                      <p className="font-medium">{formatDate(dados.data_formacao)}</p>
                    </div>
                  </div>
                  
                  {dados.data_dissolucao && (
                    <div className="flex items-center text-gray-600">
                      <Calendar className="h-5 w-5 mr-2 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-500">Dissolução</p>
                        <p className="font-medium">{formatDate(dados.data_dissolucao)}</p>
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center text-gray-600">
                    <Building className="h-5 w-5 mr-2 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500">Tipo</p>
                      <p className="font-medium capitalize">{dados.tipo_coligacao || 'Eleitoral'}</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="text-right ml-6">
                <div className="flex items-center text-gray-600 mb-2">
                  <Users className="h-5 w-5 mr-2" />
                  <span className="text-2xl font-bold text-blue-600">
                    {dados.deputy_count || deputados.length}
                  </span>
                  <span className="ml-1">deputados</span>
                </div>
                <div className="text-sm text-gray-500">
                  {partidos.length} partidos componentes
                </div>
              </div>
            </div>

            {/* Observations */}
            {dados.observacoes && (
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">{dados.observacoes}</p>
              </div>
            )}
          </div>
        </motion.div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm border mb-8">
          <div className="border-b">
            <nav className="flex -mb-px">
              <button
                onClick={() => handleTabChange('overview')}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'overview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center">
                  <Target className="h-4 w-4 mr-2" />
                  Visão Geral
                </div>
              </button>
              
              <button
                onClick={() => handleTabChange('partidos')}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'partidos'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center">
                  <Building className="h-4 w-4 mr-2" />
                  Partidos Componentes
                </div>
              </button>
              
              <button
                onClick={() => handleTabChange('deputados')}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'deputados'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center">
                  <Users className="h-4 w-4 mr-2" />
                  Deputados ({deputados.length})
                </div>
              </button>
              
              <button
                onClick={() => handleTabChange('timeline')}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'timeline'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center">
                  <History className="h-4 w-4 mr-2" />
                  Linha do Tempo
                </div>
              </button>
              
              <button
                onClick={() => handleTabChange('performance')}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'performance'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center">
                  <Activity className="h-4 w-4 mr-2" />
                  Desempenho Eleitoral
                </div>
              </button>
            </nav>
          </div>

          <div className="p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Contexto Histórico</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose max-w-none text-gray-600">
                      {dados.sigla === 'AD' && (
                        <>
                          <p>A Aliança Democrática foi uma coligação política de centro-direita formada em 1979, 
                          unindo o PSD (então PPD/PSD), o CDS e o PPM. Foi a primeira coligação governamental estável 
                          após o 25 de Abril, marcando a consolidação democrática portuguesa.</p>
                          <p className="mt-3">Sob a liderança de Francisco Sá Carneiro, a AD venceu as eleições de 1979 e 1980, 
                          estabelecendo um modelo de governação de centro-direita que seria referência para futuras coligações.</p>
                        </>
                      )}
                      {dados.sigla === 'CDU' && (
                        <>
                          <p>A Coligação Democrática Unitária representa a mais duradoura aliança política 
                          na democracia portuguesa, unindo desde 1987 o Partido Comunista Português e o 
                          Partido Ecologista "Os Verdes".</p>
                          <p className="mt-3">Com forte implantação no Alentejo e cintura industrial de Lisboa, 
                          a CDU mantém uma linha política consistente de esquerda, defendendo os direitos 
                          dos trabalhadores e uma visão crítica da integração europeia.</p>
                        </>
                      )}
                      {dados.sigla === 'PAF' && (
                        <>
                          <p>Portugal à Frente foi a designação adotada pela coligação PSD/CDS-PP para 
                          as eleições legislativas de 2015, representando uma renovação da tradicional 
                          aliança de centro-direita.</p>
                          <p className="mt-3">Apesar de ter obtido a maioria relativa, a PàF não conseguiu 
                          formar governo, marcando uma mudança significativa no panorama político português 
                          com a formação da "geringonça" à esquerda.</p>
                        </>
                      )}
                      {!['AD', 'CDU', 'PAF'].includes(dados.sigla) && (
                        <p>Coligação política portuguesa formada para maximizar a representação eleitoral 
                        dos partidos componentes através de uma estratégia unificada.</p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Key Achievements */}
                <Card>
                  <CardHeader>
                    <CardTitle>Momentos Chave</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {dados.sigla === 'AD' && (
                        <>
                          <div className="flex items-start space-x-3">
                            <Award className="h-5 w-5 text-blue-600 mt-0.5" />
                            <div>
                              <p className="font-medium">Vitória Eleitoral 1979</p>
                              <p className="text-sm text-gray-600">42.5% dos votos, primeiro governo de coligação estável</p>
                            </div>
                          </div>
                          <div className="flex items-start space-x-3">
                            <Award className="h-5 w-5 text-blue-600 mt-0.5" />
                            <div>
                              <p className="font-medium">Maioria Absoluta 1980</p>
                              <p className="text-sm text-gray-600">44.9% dos votos, consolidação do projeto político</p>
                            </div>
                          </div>
                        </>
                      )}
                      {dados.sigla === 'CDU' && (
                        <>
                          <div className="flex items-start space-x-3">
                            <Award className="h-5 w-5 text-blue-600 mt-0.5" />
                            <div>
                              <p className="font-medium">Consistência Eleitoral</p>
                              <p className="text-sm text-gray-600">Presença parlamentar ininterrupta desde 1987</p>
                            </div>
                          </div>
                          <div className="flex items-start space-x-3">
                            <Award className="h-5 w-5 text-blue-600 mt-0.5" />
                            <div>
                              <p className="font-medium">Força Regional</p>
                              <p className="text-sm text-gray-600">Liderança consistente no Alentejo</p>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Component Parties Tab */}
            {activeTab === 'partidos' && (
              <div className="space-y-4">
                {partidos.map((partido, index) => (
                  <motion.div
                    key={partido.sigla}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
                  >
                    <Link 
                      to={`/partidos/${partido.sigla}`}
                      className="flex items-center justify-between"
                    >
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {partido.sigla}
                        </h3>
                        <p className="text-sm text-gray-600">{partido.nome}</p>
                        {partido.papel_coligacao && (
                          <span className="inline-block mt-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            {partido.papel_coligacao}
                          </span>
                        )}
                      </div>
                      <div className="text-right">
                        {partido.data_adesao && (
                          <p className="text-sm text-gray-500">
                            Desde {new Date(partido.data_adesao).getFullYear()}
                          </p>
                        )}
                      </div>
                    </Link>
                  </motion.div>
                ))}
              </div>
            )}

            {/* Deputies Tab */}
            {activeTab === 'deputados' && (
              <div className="space-y-4">
                {deputados.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">
                    Nenhum deputado encontrado para esta coligação
                  </p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {deputados.map((deputado, index) => (
                      <motion.div
                        key={deputado.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.05 }}
                        className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <Link to={`/deputados/${deputado.id_cadastro || deputado.id}`}>
                          <h4 className="font-semibold text-gray-900 hover:text-blue-600">
                            {deputado.nome}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">
                            {deputado.partido_sigla}
                          </p>
                          <p className="text-xs text-gray-500 mt-2">
                            {deputado.circulo}
                          </p>
                        </Link>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Timeline Tab */}
            {activeTab === 'timeline' && (
              <div className="space-y-6">
                <div className="relative">
                  <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-300"></div>
                  {timelineEvents.map((event, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.2 }}
                      className="relative flex items-start mb-8"
                    >
                      <div className={`
                        z-10 flex items-center justify-center w-16 h-16 rounded-full 
                        ${event.type === 'formation' ? 'bg-green-100' : 'bg-red-100'}
                      `}>
                        <Calendar className={`h-6 w-6 ${
                          event.type === 'formation' ? 'text-green-600' : 'text-red-600'
                        }`} />
                      </div>
                      <div className="ml-6">
                        <p className="text-sm text-gray-500">
                          {formatDate(event.date)}
                        </p>
                        <h3 className="text-lg font-semibold text-gray-900 mt-1">
                          {event.title}
                        </h3>
                        <p className="text-gray-600 mt-1">
                          {event.description}
                        </p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Performance Tab */}
            {activeTab === 'performance' && (
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Desempenho Eleitoral</CardTitle>
                    <CardDescription>
                      Evolução dos resultados eleitorais da coligação
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-500 text-center py-8">
                      Dados de desempenho eleitoral em desenvolvimento
                    </p>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ColigacaoDetalhes;