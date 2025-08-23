import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Clock, MapPin, Users, FileText, Vote, Activity, ChevronRight, AlertCircle } from 'lucide-react';
import { apiFetch } from '../config/api';

const AgendaPage = () => {
  const [agendaHoje, setAgendaHoje] = useState(null);
  const [agendaSemana, setAgendaSemana] = useState(null);
  const [votacoesRecentes, setVotacoesRecentes] = useState(null);
  const [estatisticas, setEstatisticas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('hoje');

  useEffect(() => {
    fetchDados();
  }, []);

  const fetchDados = async () => {
    try {
      setLoading(true);
      
      // Buscar dados em paralelo
      const [agendaHojeRes, agendaSemanaRes, votacoesRes, estatisticasRes] = await Promise.all([
        apiFetch('agenda/hoje'),
        apiFetch('agenda/semana'),
        apiFetch('votacoes/recentes?limite=5'),
        apiFetch('estatisticas/atividade')
      ]);

      if (agendaHojeRes.ok) {
        const agendaHojeData = await agendaHojeRes.json();
        setAgendaHoje(agendaHojeData);
      }

      if (agendaSemanaRes.ok) {
        const agendaSemanaData = await agendaSemanaRes.json();
        setAgendaSemana(agendaSemanaData);
      }

      if (votacoesRes.ok) {
        const votacoesData = await votacoesRes.json();
        setVotacoesRecentes(votacoesData);
      }

      if (estatisticasRes.ok) {
        const estatisticasData = await estatisticasRes.json();
        setEstatisticas(estatisticasData);
      }

    } catch (error) {
      console.error('Erro ao carregar dados da agenda:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatarHora = (hora) => {
    return hora || '--:--';
  };

  const getEstadoColor = (estado) => {
    switch (estado) {
      case 'em_curso': return 'bg-green-100 text-green-800';
      case 'concluido': return 'bg-gray-100 text-gray-800';
      case 'cancelado': return 'bg-red-100 text-red-800';
      default: return 'bg-blue-100 text-blue-800';
    }
  };

  const getTipoIcon = (tipo) => {
    switch (tipo) {
      case 'plenario': return Users;
      case 'comissao': return FileText;
      case 'votacao': return Vote;
      default: return Activity;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando agenda parlamentar...</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'hoje', label: 'Hoje', icon: Calendar },
    { id: 'semana', label: 'Esta Semana', icon: Activity },
    { id: 'votacoes', label: 'Votações', icon: Vote }
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Agenda Parlamentar
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Acompanhe as atividades diárias do Parlamento Português
        </p>
      </motion.div>

      {/* Estatísticas Rápidas */}
      {estatisticas && estatisticas.estatisticas && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-6"
        >
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Sessões Plenárias</p>
                <p className="text-2xl font-bold text-gray-900">
                  {estatisticas.estatisticas.sessoes_plenarias?.total_ano || 0}
                </p>
                <p className="text-xs text-gray-500">este ano</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-center">
              <Vote className="h-8 w-8 text-green-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Votações</p>
                <p className="text-2xl font-bold text-gray-900">
                  {estatisticas.estatisticas.votacoes?.total_ano || 0}
                </p>
                <p className="text-xs text-gray-500">
                  {estatisticas.estatisticas.votacoes?.taxa_aprovacao || 0}% aprovadas
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-center">
              <FileText className="h-8 w-8 text-purple-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Iniciativas</p>
                <p className="text-2xl font-bold text-gray-900">
                  {estatisticas.estatisticas.iniciativas?.apresentadas || 0}
                </p>
                <p className="text-xs text-gray-500">apresentadas</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-orange-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Assiduidade</p>
                <p className="text-2xl font-bold text-gray-900">
                  {estatisticas.estatisticas.assiduidade?.media_presencas || 0}%
                </p>
                <p className="text-xs text-gray-500">média</p>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-xl shadow-lg border border-gray-100"
      >
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
          {activeTab === 'hoje' && agendaHoje && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-gray-900">
                  Agenda de Hoje
                </h3>
                <span className="text-sm text-gray-500">
                  {new Date(agendaHoje.data).toLocaleDateString('pt-PT', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </span>
              </div>

              {agendaHoje.eventos.length > 0 ? (
                <div className="space-y-4">
                  {(agendaHoje.eventos || []).map((evento) => {
                    const Icon = getTipoIcon(evento.tipo);
                    return (
                      <div key={evento.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3">
                            <div className="flex-shrink-0">
                              <Icon className="h-6 w-6 text-blue-600 mt-1" />
                            </div>
                            <div className="flex-1">
                              <h4 className="text-lg font-medium text-gray-900 mb-2">
                                {evento.titulo}
                              </h4>
                              <p className="text-gray-600 mb-3">
                                {evento.descricao}
                              </p>
                              <div className="flex items-center space-x-4 text-sm text-gray-500">
                                <div className="flex items-center">
                                  <Clock className="h-4 w-4 mr-1" />
                                  <span>
                                    {formatarHora(evento.hora_inicio)}
                                    {evento.hora_fim && ` - ${formatarHora(evento.hora_fim)}`}
                                  </span>
                                </div>
                                {evento.local && (
                                  <div className="flex items-center">
                                    <MapPin className="h-4 w-4 mr-1" />
                                    <span>{evento.local}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEstadoColor(evento.estado)}`}>
                            {evento.estado === 'em_curso' && '🔴 '}
                            {evento.estado.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">Nenhuma atividade agendada para hoje</p>
                </div>
              )}

              {/* Resumo do dia */}
              {agendaHoje.resumo && (
                <div className="mt-8 bg-blue-50 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-2">Resumo do Dia</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-blue-600 font-medium">
                        {agendaHoje.resumo.sessoes_plenarias}
                      </span>
                      <span className="text-blue-800 ml-1">sessões plenárias</span>
                    </div>
                    <div>
                      <span className="text-blue-600 font-medium">
                        {agendaHoje.resumo.reunioes_comissao}
                      </span>
                      <span className="text-blue-800 ml-1">reuniões de comissão</span>
                    </div>
                    <div>
                      <span className="text-blue-600 font-medium">
                        {agendaHoje.resumo.outros_eventos}
                      </span>
                      <span className="text-blue-800 ml-1">outros eventos</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'semana' && agendaSemana && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-gray-900">
                  Agenda da Semana
                </h3>
                <span className="text-sm text-gray-500">
                  {new Date(agendaSemana.periodo.inicio).toLocaleDateString('pt-PT')} - {new Date(agendaSemana.periodo.fim).toLocaleDateString('pt-PT')}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(agendaSemana.agenda || []).map((dia) => (
                  <div key={dia.data} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900">
                        {new Date(dia.data).toLocaleDateString('pt-PT', { weekday: 'long' })}
                      </h4>
                      <span className="text-sm text-gray-500">
                        {new Date(dia.data).toLocaleDateString('pt-PT', { day: 'numeric', month: 'short' })}
                      </span>
                    </div>
                    
                    {dia.eventos.length > 0 ? (
                      <div className="space-y-2">
                        {(dia.eventos || []).map((evento) => (
                          <div key={evento.id} className="flex items-center justify-between text-sm">
                            <span className="text-gray-700">{evento.titulo}</span>
                            <span className={`px-2 py-1 rounded text-xs ${getEstadoColor(evento.estado)}`}>
                              {evento.hora_inicio}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 italic">Sem atividades</p>
                    )}
                  </div>
                ))}
              </div>

              {/* Resumo da semana */}
              {agendaSemana.resumo && (
                <div className="mt-6 bg-green-50 rounded-lg p-4">
                  <h4 className="font-medium text-green-900 mb-2">Resumo da Semana</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-green-600 font-medium">
                        {agendaSemana.resumo.total_eventos}
                      </span>
                      <span className="text-green-800 ml-1">eventos totais</span>
                    </div>
                    <div>
                      <span className="text-green-600 font-medium">
                        {agendaSemana.resumo.dias_com_atividade}
                      </span>
                      <span className="text-green-800 ml-1">dias com atividade</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'votacoes' && votacoesRecentes && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-gray-900">
                  Votações Recentes
                </h3>
                <span className="text-sm text-gray-500">
                  {votacoesRecentes.resumo.periodo}
                </span>
              </div>

              <div className="space-y-4">
                {(votacoesRecentes.votacoes || []).map((votacao) => (
                  <div key={votacao.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h4 className="text-lg font-medium text-gray-900 mb-1">
                          {votacao.titulo}
                        </h4>
                        <p className="text-gray-600 text-sm mb-2">
                          {votacao.descricao}
                        </p>
                        <span className="text-xs text-gray-500">
                          {new Date(votacao.data).toLocaleDateString('pt-PT')}
                        </span>
                      </div>
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        votacao.resultado === 'aprovado' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {votacao.resultado}
                      </span>
                    </div>

                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <div className="text-center">
                        <div className="text-green-600 font-bold text-lg">
                          {votacao.votos_favor}
                        </div>
                        <div className="text-gray-500 text-xs">A favor</div>
                      </div>
                      <div className="text-center">
                        <div className="text-red-600 font-bold text-lg">
                          {votacao.votos_contra}
                        </div>
                        <div className="text-gray-500 text-xs">Contra</div>
                      </div>
                      <div className="text-center">
                        <div className="text-yellow-600 font-bold text-lg">
                          {votacao.abstencoes}
                        </div>
                        <div className="text-gray-500 text-xs">Abstenções</div>
                      </div>
                      <div className="text-center">
                        <div className="text-gray-600 font-bold text-lg">
                          {votacao.ausencias}
                        </div>
                        <div className="text-gray-500 text-xs">Ausências</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Resumo das votações */}
              {votacoesRecentes.resumo && (
                <div className="mt-6 bg-purple-50 rounded-lg p-4">
                  <h4 className="font-medium text-purple-900 mb-2">Resumo das Votações</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-purple-600 font-medium">
                        {votacoesRecentes.resumo.aprovadas}
                      </span>
                      <span className="text-purple-800 ml-1">aprovadas</span>
                    </div>
                    <div>
                      <span className="text-purple-600 font-medium">
                        {votacoesRecentes.resumo.rejeitadas}
                      </span>
                      <span className="text-purple-800 ml-1">rejeitadas</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </motion.div>

      {/* Aviso sobre dados simulados */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-yellow-50 border border-yellow-200 rounded-lg p-4"
      >
        <div className="flex items-center">
          <AlertCircle className="h-5 w-5 text-yellow-600 mr-3" />
          <div>
            <h4 className="text-sm font-medium text-yellow-800">
              Dados Demonstrativos
            </h4>
            <p className="text-sm text-yellow-700 mt-1">
              Os dados apresentados são simulados para demonstração. 
              A integração com dados reais será implementada em futuras versões.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default AgendaPage;

