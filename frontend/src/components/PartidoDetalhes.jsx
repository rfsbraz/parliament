import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Users, MapPin, User, BarChart3, TrendingUp, UserCheck, Handshake } from 'lucide-react';
import PartyVotingAnalytics from './PartyVotingAnalytics';
import PartyDemographics from './PartyDemographics';
import { apiFetch } from '../config/api';
import { tokens } from '../styles/tokens';
import { LoadingSpinner } from './common';

const PartidoDetalhes = () => {
  const { partidoId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [dados, setDados] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get active tab from URL hash, default to 'deputados'
  const getActiveTabFromUrl = () => {
    const hash = location.hash.replace('#', '');
    const validTabs = ['deputados', 'analytics', 'demografia'];
    return validTabs.includes(hash) ? hash : 'deputados';
  };

  const [activeTab, setActiveTab] = useState(getActiveTabFromUrl());

  // Sync activeTab with URL hash changes
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

  // Handle tab change with URL update
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    navigate(`#${tabId}`, { replace: true });
  };

  // Set default tab in URL if no hash is present
  useEffect(() => {
    if (!location.hash) {
      navigate('#deputados', { replace: true });
    }
  }, [navigate, location.hash]);

  useEffect(() => {
    const fetchDados = async () => {
      try {
        setLoading(true);
        // Fetch all party deputies from all periods (no legislatura filter)
        const response = await apiFetch(`partidos/${encodeURIComponent(partidoId)}/deputados`);
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

    if (partidoId) {
      fetchDados();
    }
  }, [partidoId]);

  if (loading) {
    return <LoadingSpinner message="A carregar dados do partido" />;
  }

  if (error) {
    return (
      <div
        style={{
          minHeight: '100vh',
          backgroundColor: tokens.colors.bgPrimary,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <p
            style={{
              fontFamily: tokens.fonts.body,
              color: tokens.colors.accent,
              marginBottom: '1rem',
            }}
          >
            Erro: {error}
          </p>
          <Link
            to="/partidos"
            style={{
              fontFamily: tokens.fonts.body,
              color: tokens.colors.primary,
              textDecoration: 'underline',
            }}
          >
            Voltar aos partidos
          </Link>
        </div>
      </div>
    );
  }

  if (!dados) {
    return (
      <div
        style={{
          minHeight: '100vh',
          backgroundColor: tokens.colors.bgPrimary,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <p style={{ fontFamily: tokens.fonts.body, color: tokens.colors.textSecondary }}>
          Partido não encontrado
        </p>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: tokens.colors.bgPrimary }}>
      {/* Header */}
      <div
        style={{
          backgroundColor: tokens.colors.bgSecondary,
          borderBottom: `1px solid ${tokens.colors.border}`,
        }}
      >
        <div
          style={{
            maxWidth: '1280px',
            margin: '0 auto',
            padding: '1rem 1.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Link
                to="/partidos"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  fontFamily: tokens.fonts.body,
                  color: tokens.colors.textSecondary,
                  textDecoration: 'none',
                  transition: 'color 150ms ease',
                }}
                onMouseEnter={(e) => e.target.style.color = tokens.colors.textPrimary}
                onMouseLeave={(e) => e.target.style.color = tokens.colors.textSecondary}
              >
                <ArrowLeft style={{ width: '20px', height: '20px', marginRight: '0.5rem' }} />
                Voltar aos Partidos
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '2rem 1.5rem' }}>
        {/* Informação do Partido */}
        <div
          style={{
            backgroundColor: tokens.colors.bgSecondary,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '4px',
            marginBottom: '2rem',
          }}
        >
          <div style={{ padding: '1.5rem 2rem' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
              <div>
                <h1
                  style={{
                    fontFamily: tokens.fonts.headline,
                    fontSize: '2rem',
                    fontWeight: 700,
                    color: tokens.colors.textPrimary,
                    marginBottom: '0.5rem',
                  }}
                >
                  {dados.partido.sigla}
                </h1>
                <p
                  style={{
                    fontFamily: tokens.fonts.body,
                    fontSize: '1.125rem',
                    color: tokens.colors.textSecondary,
                  }}
                >
                  {dados.partido.nome}
                </p>
                {dados.coligacao && (
                  <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center' }}>
                    <Handshake style={{ width: '16px', height: '16px', marginRight: '0.5rem', color: tokens.colors.purple }} />
                    <span style={{ fontFamily: tokens.fonts.body, fontSize: '0.875rem', color: tokens.colors.textSecondary }}>
                      Parte da coligação{' '}
                      <Link
                        to={`/coligacoes/${encodeURIComponent(dados.coligacao.sigla)}`}
                        style={{
                          color: tokens.colors.purple,
                          fontWeight: 600,
                          textDecoration: 'underline',
                        }}
                      >
                        {dados.coligacao.sigla}
                      </Link>
                      {dados.coligacao.nome && dados.coligacao.nome !== dados.coligacao.sigla && (
                        <span style={{ color: tokens.colors.textMuted }}> ({dados.coligacao.nome})</span>
                      )}
                    </span>
                  </div>
                )}
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ display: 'flex', alignItems: 'center', color: tokens.colors.textSecondary, marginBottom: '0.5rem' }}>
                  <Users style={{ width: '20px', height: '20px', marginRight: '0.5rem' }} />
                  <span
                    style={{
                      fontFamily: tokens.fonts.mono,
                      fontSize: '1.5rem',
                      fontWeight: 700,
                      color: tokens.colors.primary,
                    }}
                  >
                    {dados.total}
                  </span>
                  <span style={{ fontFamily: tokens.fonts.body, marginLeft: '0.25rem' }}>deputados</span>
                </div>
                <div style={{ fontFamily: tokens.fonts.body, fontSize: '0.875rem', color: tokens.colors.textMuted }}>
                  {dados.mandatos_ativos} mandatos ativos
                </div>
              </div>
            </div>

            {/* Estatísticas Rápidas */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1.5rem' }}>
              <div
                style={{
                  backgroundColor: '#E8F5E9',
                  borderRadius: '4px',
                  padding: '1rem',
                  border: `1px solid ${tokens.colors.border}`,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <Users style={{ width: '32px', height: '32px', color: tokens.colors.primary }} />
                  <div style={{ marginLeft: '0.75rem' }}>
                    <p style={{ fontFamily: tokens.fonts.body, fontSize: '0.75rem', fontWeight: 600, color: tokens.colors.primary, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Total Histórico
                    </p>
                    <p style={{ fontFamily: tokens.fonts.mono, fontSize: '1.5rem', fontWeight: 700, color: tokens.colors.textPrimary }}>
                      {dados.total}
                    </p>
                    <p style={{ fontFamily: tokens.fonts.body, fontSize: '0.75rem', color: tokens.colors.primary }}>
                      todas as legislaturas
                    </p>
                  </div>
                </div>
              </div>

              <div
                style={{
                  backgroundColor: '#E3F2FD',
                  borderRadius: '4px',
                  padding: '1rem',
                  border: `1px solid ${tokens.colors.border}`,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <MapPin style={{ width: '32px', height: '32px', color: tokens.colors.blue }} />
                  <div style={{ marginLeft: '0.75rem' }}>
                    <p style={{ fontFamily: tokens.fonts.body, fontSize: '0.75rem', fontWeight: 600, color: tokens.colors.blue, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Círculos Históricos
                    </p>
                    <p style={{ fontFamily: tokens.fonts.mono, fontSize: '1.5rem', fontWeight: 700, color: tokens.colors.textPrimary }}>
                      {dados.historico?.total_circulos || new Set(dados.deputados.map(d => d.circulo)).size}
                    </p>
                    <p style={{ fontFamily: tokens.fonts.body, fontSize: '0.75rem', color: tokens.colors.blue }}>
                      distritos eleitorais
                    </p>
                  </div>
                </div>
              </div>

              <div
                style={{
                  backgroundColor: '#F3E8FF',
                  borderRadius: '4px',
                  padding: '1rem',
                  border: `1px solid ${tokens.colors.border}`,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <User style={{ width: '32px', height: '32px', color: tokens.colors.purple }} />
                  <div style={{ marginLeft: '0.75rem' }}>
                    <p style={{ fontFamily: tokens.fonts.body, fontSize: '0.75rem', fontWeight: 600, color: tokens.colors.purple, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Mandatos Ativos
                    </p>
                    <p style={{ fontFamily: tokens.fonts.mono, fontSize: '1.5rem', fontWeight: 700, color: tokens.colors.textPrimary }}>
                      {dados.mandatos_ativos}
                    </p>
                    <p style={{ fontFamily: tokens.fonts.body, fontSize: '0.75rem', color: tokens.colors.purple }}>
                      legislatura atual
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs de Atividade */}
        <div
          style={{
            backgroundColor: tokens.colors.bgSecondary,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '4px',
          }}
        >
          {/* Tab Headers */}
          <div style={{ borderBottom: `1px solid ${tokens.colors.border}` }}>
            <nav style={{ display: 'flex', gap: '2rem', padding: '0 1.5rem' }}>
              {[
                { id: 'deputados', label: 'Deputados', icon: Users },
                { id: 'demografia', label: 'Demografia', icon: UserCheck },
                { id: 'analytics', label: 'Análise Política', icon: BarChart3 }
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => handleTabChange(tab.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '1rem 0',
                      fontFamily: tokens.fonts.body,
                      fontSize: '0.875rem',
                      fontWeight: isActive ? 600 : 500,
                      color: isActive ? tokens.colors.primary : tokens.colors.textMuted,
                      background: 'none',
                      border: 'none',
                      borderBottom: isActive ? `2px solid ${tokens.colors.primary}` : '2px solid transparent',
                      cursor: 'pointer',
                      transition: 'all 150ms ease',
                    }}
                  >
                    <Icon style={{ width: '16px', height: '16px', marginRight: '0.5rem' }} />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div style={{ padding: '1.5rem' }}>
            {activeTab === 'deputados' && (
              <div>
                <div style={{ marginBottom: '1.5rem' }}>
                  <h2
                    style={{
                      fontFamily: tokens.fonts.body,
                      fontSize: '1.25rem',
                      fontWeight: 600,
                      color: tokens.colors.textPrimary,
                    }}
                  >
                    Deputados do {dados.partido.sigla}
                  </h2>
                  <p
                    style={{
                      fontFamily: tokens.fonts.body,
                      fontSize: '0.875rem',
                      color: tokens.colors.textSecondary,
                      marginTop: '0.25rem',
                    }}
                  >
                    Histórico completo de {dados.total} deputados que representaram o {dados.partido.sigla} ao longo de todas as legislaturas.
                    {dados.mandatos_ativos} deputados têm mandatos ativos na legislatura atual.
                  </p>
                  {dados.historico && (
                    <div
                      style={{
                        marginTop: '0.75rem',
                        padding: '0.75rem',
                        backgroundColor: '#E8F5E9',
                        border: `1px solid ${tokens.colors.border}`,
                        borderRadius: '4px',
                      }}
                    >
                      <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.75rem', fontFamily: tokens.fonts.body, color: tokens.colors.primary }}>
                        <span>
                          <span style={{ fontWeight: 600 }}>Período:</span> {dados.historico.periodo_atividade || 'N/A'}
                        </span>
                        <span>
                          <span style={{ fontWeight: 600 }}>Legislaturas:</span> {dados.historico.total_legislaturas || 0}
                        </span>
                        <span>
                          <span style={{ fontWeight: 600 }}>Círculos:</span> {dados.historico.total_circulos || 0}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  {dados.deputados.map((deputado) => (
                    <div
                      key={deputado.id}
                      style={{
                        padding: '1rem 0',
                        borderBottom: `1px solid ${tokens.colors.border}`,
                        transition: 'background-color 150ms ease',
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = tokens.colors.bgPrimary}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <div style={{ flexShrink: 0, position: 'relative' }}>
                              {deputado.picture_url ? (
                                <div style={{ width: '48px', height: '48px', position: 'relative' }}>
                                  <img
                                    src={deputado.picture_url}
                                    alt={deputado.nome}
                                    style={{
                                      width: '48px',
                                      height: '48px',
                                      borderRadius: '50%',
                                      objectFit: 'cover',
                                      backgroundColor: tokens.colors.border,
                                      border: `2px solid ${tokens.colors.bgSecondary}`,
                                    }}
                                    onError={(e) => {
                                      e.target.style.display = 'none';
                                      e.target.nextSibling.style.display = 'flex';
                                    }}
                                  />
                                  <div
                                    style={{
                                      width: '48px',
                                      height: '48px',
                                      borderRadius: '50%',
                                      backgroundColor: '#E8F5E9',
                                      display: 'none',
                                      alignItems: 'center',
                                      justifyContent: 'center',
                                      border: `2px solid ${tokens.colors.bgSecondary}`,
                                    }}
                                  >
                                    <User style={{ width: '24px', height: '24px', color: tokens.colors.primary }} />
                                  </div>
                                </div>
                              ) : (
                                <div
                                  style={{
                                    width: '48px',
                                    height: '48px',
                                    borderRadius: '50%',
                                    backgroundColor: '#E8F5E9',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    border: `2px solid ${tokens.colors.bgSecondary}`,
                                  }}
                                >
                                  <User style={{ width: '24px', height: '24px', color: tokens.colors.primary }} />
                                </div>
                              )}
                            </div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <Link
                                to={`/deputados/${deputado.id_cadastro || deputado.id}`}
                                style={{
                                  fontFamily: tokens.fonts.body,
                                  fontSize: '1rem',
                                  fontWeight: 600,
                                  color: tokens.colors.textPrimary,
                                  textDecoration: 'none',
                                  transition: 'color 150ms ease',
                                }}
                                onMouseEnter={(e) => e.target.style.color = tokens.colors.primary}
                                onMouseLeave={(e) => e.target.style.color = tokens.colors.textPrimary}
                              >
                                {deputado.nome}
                              </Link>
                              {deputado.profissao && (
                                <p
                                  style={{
                                    fontFamily: tokens.fonts.body,
                                    fontSize: '0.875rem',
                                    color: tokens.colors.textSecondary,
                                    marginTop: '0.25rem',
                                  }}
                                >
                                  {deputado.profissao}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.875rem', color: tokens.colors.textMuted }}>
                          <div style={{ display: 'flex', alignItems: 'center' }}>
                            <MapPin style={{ width: '16px', height: '16px', marginRight: '0.25rem' }} />
                            <span style={{ fontFamily: tokens.fonts.body }}>{deputado.circulo}</span>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center' }}>
                            <span style={{ fontFamily: tokens.fonts.body, fontSize: '0.75rem', color: tokens.colors.textMuted }}>
                              {deputado.mandato_ativo ?
                                `Leg. ${deputado.ultima_legislatura} (atual)` :
                                `Última: Leg. ${deputado.ultima_legislatura}`
                              }
                            </span>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center' }}>
                            {deputado.mandato_ativo ? (
                              <span
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  padding: '0.25rem 0.625rem',
                                  borderRadius: '2px',
                                  fontSize: '0.75rem',
                                  fontFamily: tokens.fonts.body,
                                  fontWeight: 600,
                                  backgroundColor: '#E8F5E9',
                                  color: tokens.colors.primary,
                                }}
                              >
                                Ativo
                              </span>
                            ) : (
                              <span
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  padding: '0.25rem 0.625rem',
                                  borderRadius: '2px',
                                  fontSize: '0.75rem',
                                  fontFamily: tokens.fonts.body,
                                  fontWeight: 600,
                                  backgroundColor: '#F5F5F5',
                                  color: tokens.colors.textMuted,
                                }}
                              >
                                Inativo
                              </span>
                            )}
                          </div>

                          <Link
                            to={`/deputados/${deputado.id_cadastro || deputado.id}`}
                            style={{
                              fontFamily: tokens.fonts.body,
                              fontSize: '0.875rem',
                              fontWeight: 600,
                              color: tokens.colors.primary,
                              textDecoration: 'none',
                              transition: 'opacity 150ms ease',
                            }}
                            onMouseEnter={(e) => e.target.style.opacity = '0.8'}
                            onMouseLeave={(e) => e.target.style.opacity = '1'}
                          >
                            Ver Detalhes →
                          </Link>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Resumo por Círculo */}
                <div
                  style={{
                    marginTop: '2rem',
                    backgroundColor: tokens.colors.bgPrimary,
                    borderRadius: '4px',
                    padding: '1.5rem',
                    border: `1px solid ${tokens.colors.border}`,
                  }}
                >
                  <h3
                    style={{
                      fontFamily: tokens.fonts.body,
                      fontSize: '1.125rem',
                      fontWeight: 600,
                      color: tokens.colors.textPrimary,
                      marginBottom: '1rem',
                    }}
                  >
                    Distribuição por Círculo Eleitoral
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                    {Object.entries(
                      dados.deputados.reduce((acc, deputado) => {
                        acc[deputado.circulo] = (acc[deputado.circulo] || 0) + 1;
                        return acc;
                      }, {})
                    )
                      .sort(([,a], [,b]) => b - a)
                      .map(([circulo, count]) => (
                        <div
                          key={circulo}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '0.75rem',
                            backgroundColor: tokens.colors.bgSecondary,
                            borderRadius: '4px',
                            border: `1px solid ${tokens.colors.border}`,
                          }}
                        >
                          <span style={{ fontFamily: tokens.fonts.body, fontSize: '0.875rem', fontWeight: 500, color: tokens.colors.textPrimary }}>{circulo}</span>
                          <span style={{ fontFamily: tokens.fonts.mono, fontSize: '0.875rem', fontWeight: 700, color: tokens.colors.primary }}>{count}</span>
                        </div>
                      ))
                    }
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'demografia' && (
              <PartyDemographics
                partidoId={partidoId}
                dadosDemograficos={dados.demografia}
                partidoInfo={dados.partido}
              />
            )}

            {activeTab === 'analytics' && (
              <PartyVotingAnalytics
                partidoId={partidoId}
                legislatura="17"
              />
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default PartidoDetalhes;
