import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Users, TrendingUp, BarChart3, ArrowRight, Building, Handshake, Filter } from 'lucide-react';

const PartidosPage = () => {
  const [partidos, setPartidos] = useState([]);
  const [coligacoes, setColigacoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState('all'); // 'all', 'partidos', 'coligacoes'
  const [showInactiveCoalitions, setShowInactiveCoalitions] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchData();
  }, [showInactiveCoalitions]);

  const fetchData = async () => {
    try {
      // Fetch parties
      const partidosResponse = await fetch('/api/partidos');
      const partidosData = await partidosResponse.json();
      setPartidos(partidosData.partidos || []);

      // Fetch coalitions
      const coligacoesResponse = await fetch(`/api/coligacoes?include_inactive=${showInactiveCoalitions}`);
      const coligacoesData = await coligacoesResponse.json();
      setColigacoes(coligacoesData.coligacoes || []);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  };

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
  };

  const coligacaoCores = {
    'AD': '#3B82F6',
    'CDU': '#DC2626',
    'PAF': '#3B82F6',
    'APU': '#EF4444',
    'MDP/CDE': '#F59E0B'
  };

  const spectrumColors = {
    'esquerda': '#DC2626',
    'centro-esquerda': '#F59E0B',
    'centro': '#6B7280',
    'centro-direita': '#3B82F6',
    'direita': '#1E40AF'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  const totalDeputados = partidos.reduce((sum, partido) => sum + partido.num_deputados, 0);
  const activeColigacoes = coligacoes.filter(c => c.ativa);

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Partidos e Coligações
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Explore o panorama completo dos partidos políticos e coligações no Parlamento Português
        </p>
      </motion.div>

      {/* Statistics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-6"
      >
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center">
            <Building className="h-8 w-8 text-blue-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Partidos</p>
              <p className="text-2xl font-bold text-gray-900">{partidos.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center">
            <Handshake className="h-8 w-8 text-purple-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Coligações</p>
              <p className="text-2xl font-bold text-gray-900">{coligacoes.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center">
            <Users className="h-8 w-8 text-green-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Total Deputados</p>
              <p className="text-2xl font-bold text-gray-900">{totalDeputados}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-orange-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Coligações Ativas</p>
              <p className="text-2xl font-bold text-gray-900">{activeColigacoes.length}</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Filter Tabs */}
      <div className="flex flex-col items-center space-y-4">
        <div className="flex justify-center space-x-4">
          <button
            onClick={() => setActiveView('all')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeView === 'all'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4" />
              <span>Todos</span>
            </div>
          </button>
          <button
            onClick={() => setActiveView('partidos')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeView === 'partidos'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Building className="h-4 w-4" />
              <span>Partidos ({partidos.length})</span>
            </div>
          </button>
          <button
            onClick={() => setActiveView('coligacoes')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeView === 'coligacoes'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Handshake className="h-4 w-4" />
              <span>Coligações ({coligacoes.length})</span>
            </div>
          </button>
        </div>
        
        {/* Show Inactive Coalitions Toggle */}
        {(activeView === 'all' || activeView === 'coligacoes') && (
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="showInactive"
              checked={showInactiveCoalitions}
              onChange={(e) => setShowInactiveCoalitions(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="showInactive" className="text-sm text-gray-600">
              Mostrar coligações inativas
            </label>
          </div>
        )}
      </div>

      {/* Parties Section */}
      {(activeView === 'all' || activeView === 'partidos') && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <Building className="h-6 w-6 mr-2 text-blue-600" />
            Partidos Individuais
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {(partidos || []).map((partido, index) => (
              <motion.div
                key={partido.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * index }}
                className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 overflow-hidden group"
              >
                {/* Party color bar */}
                <div 
                  className="h-2 w-full"
                  style={{ backgroundColor: partidoCores[partido.sigla] || '#6B7280' }}
                ></div>
                
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-2xl font-bold text-gray-900 mb-1">
                        {partido.sigla}
                      </h3>
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {partido.nome}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold" style={{ color: partidoCores[partido.sigla] || '#6B7280' }}>
                        {partido.num_deputados}
                      </div>
                      <div className="text-xs text-gray-500">deputados</div>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="mb-4">
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>Representação</span>
                      <span>{((partido.num_deputados / 230) * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full transition-all duration-500"
                        style={{ 
                          backgroundColor: partidoCores[partido.sigla] || '#6B7280',
                          width: `${(partido.num_deputados / 230) * 100}%`
                        }}
                      ></div>
                    </div>
                  </div>

                  <Link
                    to={`/partidos/${partido.sigla}`}
                    className="inline-flex items-center text-blue-600 hover:text-blue-700 text-sm font-medium group-hover:translate-x-1 transition-transform"
                  >
                    Ver detalhes
                    <ArrowRight className="ml-1 h-4 w-4" />
                  </Link>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Coalitions Section - Moved to bottom */}
      {(activeView === 'all' || activeView === 'coligacoes') && coligacoes.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: activeView === 'all' ? 0.3 : 0.2 }}
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <Handshake className="h-6 w-6 mr-2 text-purple-600" />
            Coligações
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {coligacoes.map((coligacao, index) => (
              <motion.div
                key={coligacao.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * index }}
                className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 overflow-hidden group"
              >
                {/* Coalition color bar */}
                <div 
                  className="h-3 w-full bg-gradient-to-r"
                  style={{ 
                    background: `linear-gradient(to right, ${
                      spectrumColors[coligacao.espectro_politico] || '#6B7280'
                    }, ${
                      coligacaoCores[coligacao.sigla] || '#9333EA'
                    })` 
                  }}
                ></div>
                
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="text-2xl font-bold text-gray-900">
                          {coligacao.sigla}
                        </h3>
                        <Handshake className="h-5 w-5 text-purple-600" />
                        {coligacao.ativa && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-semibold">
                            Ativa
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {coligacao.nome}
                      </p>
                      {coligacao.espectro_politico && (
                        <span className="inline-block mt-2 px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                          {coligacao.espectro_politico}
                        </span>
                      )}
                    </div>
                    <div className="text-right ml-4">
                      <div className="text-3xl font-bold text-purple-600">
                        {coligacao.deputy_count || 0}
                      </div>
                      <div className="text-xs text-gray-500">deputados</div>
                    </div>
                  </div>

                  {/* Component parties preview */}
                  {coligacao.component_parties && coligacao.component_parties.length > 0 && (
                    <div className="mb-4">
                      <p className="text-xs text-gray-500 mb-2">Partidos componentes:</p>
                      <div className="flex flex-wrap gap-1">
                        {coligacao.component_parties.slice(0, 3).map(party => (
                          <span 
                            key={party.sigla}
                            className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded"
                          >
                            {party.sigla}
                          </span>
                        ))}
                        {coligacao.component_parties.length > 3 && (
                          <span className="px-2 py-1 bg-gray-50 text-gray-600 text-xs rounded">
                            +{coligacao.component_parties.length - 3}
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Dates */}
                  {(coligacao.data_formacao || coligacao.data_dissolucao) && (
                    <div className="text-xs text-gray-500 mb-4">
                      {coligacao.data_formacao && (
                        <p>Formada: {new Date(coligacao.data_formacao).getFullYear()}</p>
                      )}
                      {coligacao.data_dissolucao && (
                        <p>Dissolvida: {new Date(coligacao.data_dissolucao).getFullYear()}</p>
                      )}
                    </div>
                  )}

                  <Link
                    to={`/coligacoes/${encodeURIComponent(coligacao.sigla)}`}
                    className="inline-flex items-center text-purple-600 hover:text-purple-700 text-sm font-medium group-hover:translate-x-1 transition-transform"
                  >
                    Ver detalhes
                    <ArrowRight className="ml-1 h-4 w-4" />
                  </Link>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default PartidosPage;