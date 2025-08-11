import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Users, TrendingUp, BarChart3, ArrowRight, Building } from 'lucide-react';

const PartidosPage = () => {
  const [partidos, setPartidos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPartidos();
  }, []);

  const fetchPartidos = async () => {
    try {
      // Fetch all parties without legislatura filter
      const response = await fetch('/api/partidos');
      const data = await response.json();
      setPartidos(data.partidos || []);
    } catch (error) {
      console.error('Erro ao carregar partidos:', error);
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

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Partidos Políticos
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Explore o panorama completo dos partidos políticos no Parlamento Português ao longo da história
        </p>
      </motion.div>

      {/* Estatísticas Gerais */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center">
            <Building className="h-8 w-8 text-blue-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Total de Partidos</p>
              <p className="text-2xl font-bold text-gray-900">{partidos.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center">
            <Users className="h-8 w-8 text-green-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Total de Deputados</p>
              <p className="text-2xl font-bold text-gray-900">
                {partidos.reduce((sum, partido) => sum + partido.num_deputados, 0)}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-purple-600" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Maior Partido</p>
              <p className="text-2xl font-bold text-gray-900">
                {partidos.length > 0 ? partidos[0].sigla : '-'}
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Lista de Partidos */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        {(partidos || []).map((partido, index) => (
          <motion.div
            key={partido.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * index }}
            className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 overflow-hidden group"
          >
            {/* Barra colorida do partido */}
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

              {/* Barra de progresso */}
              <div className="mb-4">
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span>Representação</span>
                  <span>{((partido.num_deputados / 249) * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full transition-all duration-500"
                    style={{ 
                      backgroundColor: partidoCores[partido.sigla] || '#6B7280',
                      width: `${(partido.num_deputados / 249) * 100}%`
                    }}
                  ></div>
                </div>
              </div>

              {/* Botão de detalhes */}
              <Link
                to={`/partidos/${encodeURIComponent(partido.id)}`}
                className="w-full bg-gray-50 hover:bg-gray-100 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center group-hover:bg-blue-50 group-hover:text-blue-700"
              >
                Ver Deputados
                <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Gráfico de Distribuição */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white rounded-xl shadow-lg p-6 border border-gray-100"
      >
        <div className="flex items-center mb-6">
          <BarChart3 className="h-6 w-6 text-blue-600 mr-3" />
          <h3 className="text-xl font-semibold text-gray-900">
            Distribuição de Assentos
          </h3>
        </div>
        
        <div className="space-y-3">
          {(partidos || []).map((partido) => (
            <div key={partido.id} className="flex items-center">
              <div className="w-16 text-sm font-medium text-gray-900">
                {partido.sigla}
              </div>
              <div className="flex-1 mx-4">
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className="h-4 rounded-full transition-all duration-500"
                    style={{ 
                      backgroundColor: partidoCores[partido.sigla] || '#6B7280',
                      width: `${(partido.num_deputados / 249) * 100}%`
                    }}
                  ></div>
                </div>
              </div>
              <div className="w-20 text-right">
                <span className="text-sm font-medium text-gray-900">
                  {partido.num_deputados}
                </span>
                <span className="text-xs text-gray-500 ml-1">
                  ({((partido.num_deputados / 249) * 100).toFixed(1)}%)
                </span>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Resumo Estatístico */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Resumo da Composição Parlamentar
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-600 mb-2">
              <strong>Partidos com mais de 50 deputados:</strong> {partidos.filter(p => p.num_deputados > 50).length}
            </p>
            <p className="text-gray-600 mb-2">
              <strong>Partidos com 10-50 deputados:</strong> {partidos.filter(p => p.num_deputados >= 10 && p.num_deputados <= 50).length}
            </p>
            <p className="text-gray-600">
              <strong>Partidos com menos de 10 deputados:</strong> {partidos.filter(p => p.num_deputados < 10).length}
            </p>
          </div>
          <div>
            <p className="text-gray-600 mb-2">
              <strong>Maior partido:</strong> {partidos.length > 0 ? `${partidos[0].sigla} (${partidos[0].num_deputados} deputados)` : '-'}
            </p>
            <p className="text-gray-600 mb-2">
              <strong>Menor partido:</strong> {partidos.length > 0 ? `${partidos[partidos.length - 1].sigla} (${partidos[partidos.length - 1].num_deputados} deputado${partidos[partidos.length - 1].num_deputados > 1 ? 's' : ''})` : '-'}
            </p>
            <p className="text-gray-600">
              <strong>Total de assentos:</strong> {partidos.reduce((sum, partido) => sum + partido.num_deputados, 0)} / 249
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default PartidosPage;

