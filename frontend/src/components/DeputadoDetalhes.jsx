import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, User, MapPin, Calendar, Briefcase, Activity, FileText, Vote, MessageSquare } from 'lucide-react';

const DeputadoDetalhes = () => {
  const { deputadoId } = useParams();
  const [deputado, setDeputado] = useState(null);
  const [atividades, setAtividades] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('resumo');

  useEffect(() => {
    const fetchDados = async () => {
      try {
        setLoading(true);
        
        // Buscar detalhes do deputado
        const deputadoResponse = await fetch(`/api/deputados/${deputadoId}/detalhes`);
        if (!deputadoResponse.ok) {
          throw new Error('Erro ao carregar dados do deputado');
        }
        const deputadoData = await deputadoResponse.json();
        setDeputado(deputadoData);

        // Buscar atividades do deputado
        const atividadesResponse = await fetch(`/api/deputados/${deputadoId}/atividades`);
        if (!atividadesResponse.ok) {
          throw new Error('Erro ao carregar atividades do deputado');
        }
        const atividadesData = await atividadesResponse.json();
        setAtividades(atividadesData);
        
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (deputadoId) {
      fetchDados();
    }
  }, [deputadoId]);

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
    { id: 'resumo', label: 'Biografia', icon: User },
    { id: 'intervencoes', label: 'Intervenções', icon: MessageSquare },
    { id: 'iniciativas', label: 'Iniciativas', icon: FileText },
    { id: 'votacoes', label: 'Votações', icon: Vote }
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
                <Link 
                  to={`/partidos/${deputado.partido.sigla}`}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
                >
                  {deputado.partido.sigla} - {deputado.partido.nome}
                </Link>
              </div>

              {/* Status */}
              <div className="flex-shrink-0">
                {deputado.mandato.ativo ? (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                    Mandato Ativo
                  </span>
                ) : (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                    <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                    Mandato Inativo
                  </span>
                )}
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
              <Activity className="h-8 w-8 text-purple-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Taxa Assiduidade</p>
                <p className="text-2xl font-bold text-gray-900">
                  {(deputado.estatisticas.taxa_assiduidade * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <Calendar className="h-8 w-8 text-orange-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Mandatos</p>
                <p className="text-2xl font-bold text-gray-900">
                  {deputado.estatisticas.total_mandatos}
                </p>
              </div>
            </div>
          </div>
        </div>

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
                    onClick={() => setActiveTab(tab.id)}
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
            {activeTab === 'resumo' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Biografia
                </h3>
                <div className="prose max-w-none">
                  {(deputado.profissao || deputado.habilitacoes_academicas) ? (
                    <div className="space-y-4">
                      {deputado.profissao && (
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2">Profissão</h4>
                          <p className="text-gray-700">{deputado.profissao}</p>
                        </div>
                      )}
                      
                      {deputado.habilitacoes_academicas && (
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2">Habilitações Académicas</h4>
                          <div className="text-gray-700">
                            {deputado.habilitacoes_academicas.split(';').map((hab, index) => (
                              <div key={index} className="mb-1">
                                • {hab.trim()}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {deputado.biografia && (
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2">Biografia</h4>
                          <div className="text-gray-700 leading-relaxed whitespace-pre-line">
                            {deputado.biografia}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-500">Informações biográficas não disponíveis</p>
                      <p className="text-sm text-gray-400 mt-2">
                        Dados biográficos não foram fornecidos para este deputado
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'intervencoes' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Intervenções Parlamentares
                </h3>
                {atividades && atividades.intervencoes.length > 0 ? (
                  <div className="space-y-4">
                    {(atividades.intervencoes || []).map((intervencao, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{intervencao.tipo}</h4>
                          <span className="text-sm text-gray-500">{intervencao.data}</span>
                        </div>
                        <p className="text-gray-600 text-sm">{intervencao.resumo}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">Nenhuma intervenção registada</p>
                    <p className="text-sm text-gray-400 mt-2">
                      Os dados de intervenções serão carregados em futuras atualizações
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'iniciativas' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Iniciativas Legislativas
                </h3>
                {atividades && atividades.iniciativas.length > 0 ? (
                  <div className="space-y-4">
                    {(atividades.iniciativas || []).map((iniciativa, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{iniciativa.titulo}</h4>
                          <span className="text-sm text-gray-500">{iniciativa.data}</span>
                        </div>
                        <p className="text-gray-600 text-sm">{iniciativa.tipo}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">Nenhuma iniciativa registada</p>
                    <p className="text-sm text-gray-400 mt-2">
                      Os dados de iniciativas serão carregados em futuras atualizações
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'votacoes' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Histórico de Votações
                </h3>
                <div className="text-center py-8">
                  <Vote className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">Dados de votações não disponíveis</p>
                  <p className="text-sm text-gray-400 mt-2">
                    Esta funcionalidade será implementada em futuras versões
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeputadoDetalhes;

