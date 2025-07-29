import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Users, MapPin, User } from 'lucide-react';
import { useLegislatura } from '../contexts/LegislaturaContext';

const PartidoDetalhes = () => {
  const { partidoId } = useParams();
  const { selectedLegislatura } = useLegislatura();
  const [dados, setDados] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDados = async () => {
      if (!selectedLegislatura) return;
      
      try {
        setLoading(true);
        const response = await fetch(`/api/partidos/${partidoId}/deputados?legislatura=${selectedLegislatura.numero}`);
        if (!response.ok) {
          throw new Error('Erro ao carregar dados do partido');
        }
        const data = await response.json();
        setDados(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (partidoId && selectedLegislatura) {
      fetchDados();
    }
  }, [partidoId, selectedLegislatura]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando dados do partido...</p>
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
        <p className="text-gray-600">Partido não encontrado</p>
      </div>
    );
  }

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
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Informação do Partido */}
        <div className="bg-white rounded-lg shadow-sm border mb-8">
          <div className="px-6 py-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  {dados.partido.sigla}
                </h1>
                <p className="text-xl text-gray-600">{dados.partido.nome}</p>
              </div>
              <div className="text-right">
                <div className="flex items-center text-gray-600 mb-2">
                  <Users className="h-5 w-5 mr-2" />
                  <span className="text-2xl font-bold text-blue-600">
                    {dados.total}
                  </span>
                  <span className="ml-1">deputados</span>
                </div>
              </div>
            </div>

            {/* Estatísticas Rápidas */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center">
                  <Users className="h-8 w-8 text-blue-600" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-blue-600">Total Deputados</p>
                    <p className="text-2xl font-bold text-blue-900">{dados.total}</p>
                  </div>
                </div>
              </div>
              
              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center">
                  <MapPin className="h-8 w-8 text-green-600" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-green-600">Círculos Representados</p>
                    <p className="text-2xl font-bold text-green-900">
                      {new Set(dados.deputados.map(d => d.circulo)).size}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center">
                  <User className="h-8 w-8 text-purple-600" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-purple-600">Mandatos Ativos</p>
                    <p className="text-2xl font-bold text-purple-900">
                      {dados.deputados.filter(d => d.mandato_ativo).length}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Lista de Deputados */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              Deputados do {dados.partido.sigla}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Lista completa dos {dados.total} deputados eleitos por este partido
            </p>
          </div>

          <div className="divide-y divide-gray-200">
            {dados.deputados.map((deputado) => (
              <div key={deputado.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                          <User className="h-5 w-5 text-blue-600" />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <Link 
                          to={`/deputados/${deputado.id}/${selectedLegislatura?.numero || '17'}`}
                          className="text-lg font-medium text-gray-900 hover:text-blue-600 transition-colors"
                        >
                          {deputado.nome}
                        </Link>
                        {deputado.profissao && (
                          <p className="text-sm text-gray-600 mt-1">
                            {deputado.profissao}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <div className="flex items-center">
                      <MapPin className="h-4 w-4 mr-1" />
                      <span>{deputado.circulo}</span>
                    </div>
                    
                    <div className="flex items-center">
                      {deputado.mandato_ativo ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Ativo
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          Inativo
                        </span>
                      )}
                    </div>
                    
                    <Link 
                      to={`/deputados/${deputado.id}/${selectedLegislatura?.numero || '17'}`}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Ver Detalhes →
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Resumo por Círculo */}
        <div className="mt-8 bg-white rounded-lg shadow-sm border">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Distribuição por Círculo Eleitoral
            </h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(
                dados.deputados.reduce((acc, deputado) => {
                  acc[deputado.circulo] = (acc[deputado.circulo] || 0) + 1;
                  return acc;
                }, {})
              )
                .sort(([,a], [,b]) => b - a)
                .map(([circulo, count]) => (
                  <div key={circulo} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm font-medium text-gray-900">{circulo}</span>
                    <span className="text-sm font-bold text-blue-600">{count}</span>
                  </div>
                ))
              }
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PartidoDetalhes;

