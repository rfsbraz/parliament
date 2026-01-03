import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { ArrowLeft, User, MapPin, Calendar, Briefcase, Activity, FileText, Vote, MessageSquare, Play, Clock, ExternalLink, Mail, Shield, AlertTriangle, Heart, Users, TrendingUp, TrendingDown, Minus, Info, ChevronRight, Target, Award, Globe, CheckCircle2, BarChart3 } from 'lucide-react';
import VotingAnalytics from './VotingAnalytics';
import LegislatureDropdown from './LegislatureDropdown';
import { apiFetch } from '../config/api';
import { tokens } from '../styles/tokens';
import { LoadingSpinner } from './common';

// TODO: Deputy mandate linking limitation
// Current system uses name-based linking to connect same person across legislaturas
// This is a temporary solution because deputado_id changes every legislative period
// Future enhancement: Implement proper unique person identifiers or create person-linking table

// Enhanced Statistics Components

/**
 * Calculate trend indicator based on current vs career average
 */
const getTrendIndicator = (current, total, legislaturesServed = 1) => {
  if (total === 0 || legislaturesServed === 0) return 'stable';
  const careerAverage = total / Math.max(legislaturesServed, 1);
  const threshold = 0.1; // 10% threshold for trend changes
  
  if (current > careerAverage * (1 + threshold)) return 'up';
  if (current < careerAverage * (1 - threshold)) return 'down';
  return 'stable';
};

/**
 * Color scheme mapping for Data Observatory theme
 */
const colorSchemes = {
  blue: {
    bg: '#EFF6FF',
    bgSecondary: '#DBEAFE',
    primary: '#2563EB',
    primaryDark: '#1D4ED8',
    text: '#1E40AF',
    textLight: '#3B82F6',
    border: '#BFDBFE',
  },
  green: {
    bg: '#F0FDF4',
    bgSecondary: '#DCFCE7',
    primary: '#16A34A',
    primaryDark: '#15803D',
    text: '#166534',
    textLight: '#22C55E',
    border: '#BBF7D0',
  },
  purple: {
    bg: '#FAF5FF',
    bgSecondary: '#F3E8FF',
    primary: '#9333EA',
    primaryDark: '#7E22CE',
    text: '#6B21A8',
    textLight: '#A855F7',
    border: '#E9D5FF',
  },
  orange: {
    bg: '#FFF7ED',
    bgSecondary: '#FFEDD5',
    primary: '#EA580C',
    primaryDark: '#C2410C',
    text: '#9A3412',
    textLight: '#F97316',
    border: '#FED7AA',
  },
};

/**
 * Get progress bar color based on percentage (for attendance)
 */
const getAttendanceColors = (percentage) => {
  if (percentage >= 75) {
    return {
      bar: tokens.colors.success,
      bg: '#DCFCE7',
      text: tokens.colors.success,
      label: 'Excelente',
    };
  } else if (percentage >= 50) {
    return {
      bar: tokens.colors.orange,
      bg: '#FFEDD5',
      text: tokens.colors.warning,
      label: 'Boa',
    };
  } else {
    return {
      bar: tokens.colors.danger,
      bg: '#FEE2E2',
      text: tokens.colors.danger,
      label: 'Baixa',
    };
  }
};

/**
 * Enhanced Statistic Card Component with Data Observatory theme
 */
const StatisticCard = ({
  title,
  icon: Icon,
  current,
  total,
  colorScheme,
  description,
  tabId,
  onCardClick
}) => {
  const percentage = total > 0 ? Math.min((current / total) * 100, 100) : 0;
  const trend = getTrendIndicator(current, total, 3);
  const scheme = colorSchemes[colorScheme] || colorSchemes.blue;

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? tokens.colors.success : trend === 'down' ? tokens.colors.danger : tokens.colors.textMuted;

  const handleClick = () => {
    if (onCardClick) {
      onCardClick(tabId);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <article
      style={{
        position: 'relative',
        background: `linear-gradient(135deg, ${scheme.bg} 0%, ${scheme.bgSecondary} 100%)`,
        borderRadius: '4px',
        border: `1px solid ${scheme.border}`,
        padding: '16px',
        cursor: 'pointer',
        transition: 'border-color 0.15s ease',
        fontFamily: tokens.fonts.body,
      }}
      role="listitem"
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      aria-labelledby={`${tabId}-title`}
      aria-describedby={`${tabId}-description ${tabId}-stats`}
      onMouseEnter={(e) => e.currentTarget.style.borderColor = scheme.primary}
      onMouseLeave={(e) => e.currentTarget.style.borderColor = scheme.border}
    >
      {/* Header with Icon and Trend */}
      <header style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{
          padding: '10px',
          backgroundColor: scheme.primary,
          borderRadius: '4px',
          flexShrink: 0,
        }}>
          <Icon style={{ width: '20px', height: '20px', color: '#FFFFFF' }} aria-hidden="true" />
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '4px 8px',
          backgroundColor: 'rgba(255, 255, 255, 0.7)',
          borderRadius: '9999px',
        }}>
          <TrendIcon style={{ width: '12px', height: '12px', color: trendColor }} aria-hidden="true" />
          <span className="sr-only">
            Tendência: {trend === 'up' ? 'acima da média' : trend === 'down' ? 'abaixo da média' : 'estável'}
          </span>
        </div>
      </header>

      {/* Content */}
      <div>
        <h4
          id={`${tabId}-title`}
          style={{
            fontSize: '0.75rem',
            fontWeight: 600,
            color: scheme.text,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '12px',
          }}
        >
          {title}
        </h4>

        {/* Statistics */}
        <div id={`${tabId}-stats`}>
          {/* Current Value */}
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.875rem', fontWeight: 500, color: scheme.textLight }}>Atual</span>
            <span style={{ fontSize: '1.5rem', fontWeight: 700, color: scheme.text, fontFamily: tokens.fonts.mono }}>
              {current.toLocaleString('pt-PT')}
            </span>
          </div>

          {/* Progress Bar */}
          <div style={{ marginBottom: '12px' }}>
            <div style={{
              width: '100%',
              backgroundColor: 'rgba(255, 255, 255, 0.6)',
              borderRadius: '9999px',
              height: '6px',
              overflow: 'hidden',
            }}>
              <div
                style={{
                  height: '100%',
                  backgroundColor: scheme.primary,
                  borderRadius: '9999px',
                  width: `${Math.min(percentage, 100)}%`,
                  transition: 'width 0.5s ease',
                }}
                role="progressbar"
                aria-valuenow={percentage}
                aria-valuemin="0"
                aria-valuemax="100"
                aria-label={`${current} de ${total} (${percentage.toFixed(1)}%)`}
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: scheme.textLight }}>
                {percentage.toFixed(1)}% do total
              </span>
              <span style={{ fontSize: '0.75rem', color: scheme.text }}>
                {total.toLocaleString('pt-PT')} total
              </span>
            </div>
          </div>

          {/* Total Career */}
          <div style={{
            display: 'flex',
            alignItems: 'baseline',
            justifyContent: 'space-between',
            borderTop: `1px solid ${scheme.border}`,
            paddingTop: '8px',
          }}>
            <span style={{ fontSize: '0.75rem', color: scheme.textLight }}>Total carreira</span>
            <span style={{ fontSize: '1.125rem', fontWeight: 600, color: scheme.text, fontFamily: tokens.fonts.mono }}>
              {total.toLocaleString('pt-PT')}
            </span>
          </div>
        </div>
      </div>

      {/* Screen reader description */}
      <p id={`${tabId}-description`} className="sr-only">
        {description}. Clique para ver detalhes.
      </p>
    </article>
  );
};

/**
 * Skeleton Loading Card for Statistics - Data Observatory theme
 */
const StatisticCardSkeleton = ({ colorScheme = 'gray' }) => {
  const scheme = colorSchemes[colorScheme] || { bg: '#F9FAFB', bgSecondary: '#F3F4F6', border: '#E5E7EB', primary: '#D1D5DB' };
  return (
    <article
      style={{
        background: `linear-gradient(135deg, ${scheme.bg} 0%, ${scheme.bgSecondary} 100%)`,
        borderRadius: '4px',
        border: `1px solid ${scheme.border}`,
        padding: '16px',
        fontFamily: tokens.fonts.body,
      }}
      role="listitem"
      aria-label="Carregando estatística..."
    >
      <header style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ padding: '10px', backgroundColor: scheme.primary || '#D1D5DB', borderRadius: '4px', opacity: 0.5 }}>
          <div style={{ width: '20px', height: '20px', backgroundColor: '#FFFFFF', borderRadius: '2px' }} />
        </div>
        <div style={{ padding: '4px 8px', backgroundColor: 'rgba(255,255,255,0.6)', borderRadius: '9999px' }}>
          <div style={{ width: '48px', height: '12px', backgroundColor: '#D1D5DB', borderRadius: '2px' }} />
        </div>
      </header>
      <div>
        <div style={{ width: '80px', height: '16px', backgroundColor: '#D1D5DB', borderRadius: '2px', marginBottom: '12px' }} />
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div style={{ width: '48px', height: '16px', backgroundColor: '#D1D5DB', borderRadius: '2px' }} />
          <div style={{ width: '64px', height: '32px', backgroundColor: '#D1D5DB', borderRadius: '2px' }} />
        </div>
        <div style={{ width: '100%', height: '6px', backgroundColor: '#E5E7EB', borderRadius: '9999px', marginBottom: '8px' }}>
          <div style={{ width: '60%', height: '100%', backgroundColor: '#D1D5DB', borderRadius: '9999px' }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: `1px solid ${tokens.colors.border}`, paddingTop: '8px' }}>
          <div style={{ width: '80px', height: '12px', backgroundColor: '#D1D5DB', borderRadius: '2px' }} />
          <div style={{ width: '56px', height: '20px', backgroundColor: '#D1D5DB', borderRadius: '2px' }} />
        </div>
      </div>
    </article>
  );
};

/**
 * Statistics Loading Skeleton Component - Data Observatory theme
 */
const StatisticsLoadingSkeleton = () => (
  <section
    style={{
      backgroundColor: tokens.colors.bgSecondary,
      borderRadius: '4px',
      border: `1px solid ${tokens.colors.border}`,
      marginBottom: '32px',
      fontFamily: tokens.fonts.body,
    }}
    aria-label="Carregando estatísticas..."
  >
    <header style={{ padding: '16px 24px', borderBottom: `1px solid ${tokens.colors.border}` }}>
      <div style={{ width: '256px', height: '24px', backgroundColor: '#D1D5DB', borderRadius: '2px', marginBottom: '8px' }} />
      <div style={{ width: '384px', height: '16px', backgroundColor: '#E5E7EB', borderRadius: '2px' }} />
    </header>
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }} role="list">
        <StatisticCardSkeleton colorScheme="blue" />
        <StatisticCardSkeleton colorScheme="green" />
        <StatisticCardSkeleton colorScheme="purple" />
        <StatisticCardSkeleton colorScheme="orange" />
      </div>
    </div>
  </section>
);

/**
 * Statistics Error Component - Data Observatory theme
 */
const StatisticsError = ({ error, onRetry }) => (
  <section
    style={{
      backgroundColor: tokens.colors.bgSecondary,
      borderRadius: '4px',
      border: `1px solid ${tokens.colors.border}`,
      marginBottom: '32px',
      fontFamily: tokens.fonts.body,
    }}
    role="alert"
    aria-labelledby="error-heading"
  >
    <header style={{ padding: '16px 24px', borderBottom: `1px solid ${tokens.colors.border}` }}>
      <h3
        id="error-heading"
        style={{ fontSize: '1.125rem', fontWeight: 600, color: tokens.colors.textPrimary, fontFamily: tokens.fonts.headline }}
      >
        Resumo de Atividade Parlamentar
      </h3>
    </header>
    <div style={{ padding: '24px', textAlign: 'center' }}>
      <AlertTriangle style={{ margin: '0 auto 16px', width: '48px', height: '48px', color: tokens.colors.danger }} aria-hidden="true" />
      <h4 style={{ fontSize: '1.125rem', fontWeight: 500, color: tokens.colors.textPrimary, marginBottom: '8px' }}>
        Erro ao carregar estatísticas
      </h4>
      <p style={{ fontSize: '0.875rem', color: tokens.colors.textSecondary, marginBottom: '16px' }}>
        Não foi possível carregar as estatísticas de atividade. Por favor, tente novamente.
      </p>
      {error && (
        <details style={{ fontSize: '0.75rem', color: tokens.colors.textMuted, marginBottom: '16px' }}>
          <summary style={{ cursor: 'pointer' }}>Detalhes técnicos</summary>
          <p style={{ marginTop: '8px', textAlign: 'left', backgroundColor: tokens.colors.bgPrimary, padding: '8px', borderRadius: '4px' }}>{error}</p>
        </details>
      )}
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            padding: '8px 16px',
            border: 'none',
            fontSize: '0.875rem',
            fontWeight: 500,
            borderRadius: '4px',
            color: '#FFFFFF',
            backgroundColor: tokens.colors.primary,
            cursor: 'pointer',
            transition: 'background-color 0.15s ease',
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = tokens.colors.primaryLight}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = tokens.colors.primary}
        >
          Tentar novamente
        </button>
      )}
    </div>
  </section>
);

/**
 * Enhanced Attendance Card with Data Observatory theme
 */
const AttendanceCard = ({ currentRate, totalRate, totalSessions, onCardClick }) => {
  const currentPercentage = (currentRate * 100);
  const totalPercentage = (totalRate * 100);
  const colors = getAttendanceColors(currentPercentage);
  const scheme = colorSchemes.orange;

  const handleClick = () => {
    if (onCardClick) {
      onCardClick('attendance');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <article
      style={{
        position: 'relative',
        background: `linear-gradient(135deg, ${scheme.bg} 0%, #FEE2E2 100%)`,
        borderRadius: '4px',
        border: `1px solid ${scheme.border}`,
        padding: '16px',
        cursor: 'pointer',
        transition: 'border-color 0.15s ease',
        fontFamily: tokens.fonts.body,
      }}
      role="listitem"
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      aria-labelledby="attendance-title"
      aria-describedby="attendance-description attendance-stats"
      onMouseEnter={(e) => e.currentTarget.style.borderColor = scheme.primary}
      onMouseLeave={(e) => e.currentTarget.style.borderColor = scheme.border}
    >
      {/* Header */}
      <header style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{
          padding: '10px',
          backgroundColor: scheme.primary,
          borderRadius: '4px',
          flexShrink: 0,
        }}>
          <Activity style={{ width: '20px', height: '20px', color: '#FFFFFF' }} aria-hidden="true" />
        </div>
        <div style={{
          padding: '4px 8px',
          backgroundColor: 'rgba(255, 255, 255, 0.7)',
          borderRadius: '9999px',
          fontSize: '0.75rem',
          fontWeight: 500,
          color: colors.text,
        }}>
          {colors.label}
        </div>
      </header>

      {/* Content */}
      <div>
        <h4
          id="attendance-title"
          style={{
            fontSize: '0.75rem',
            fontWeight: 600,
            color: scheme.text,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '12px',
          }}
        >
          Taxa de Presença
        </h4>

        {/* Statistics */}
        <div id="attendance-stats">
          {/* Current Rate */}
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.875rem', fontWeight: 500, color: scheme.textLight }}>Atual</span>
            <span style={{ fontSize: '1.5rem', fontWeight: 700, color: scheme.text, fontFamily: tokens.fonts.mono }}>
              {currentPercentage.toFixed(1)}%
            </span>
          </div>

          {/* Visual Progress */}
          <div style={{ marginBottom: '12px' }}>
            <div style={{
              width: '100%',
              backgroundColor: colors.bg,
              borderRadius: '9999px',
              height: '6px',
              overflow: 'hidden',
            }}>
              <div
                style={{
                  height: '100%',
                  backgroundColor: colors.bar,
                  borderRadius: '9999px',
                  width: `${currentPercentage}%`,
                  transition: 'width 0.5s ease',
                }}
                role="progressbar"
                aria-valuenow={currentPercentage}
                aria-valuemin="0"
                aria-valuemax="100"
                aria-label={`Taxa de presença: ${currentPercentage.toFixed(1)}%`}
              />
            </div>
          </div>

          {/* Career Total */}
          <div style={{
            display: 'flex',
            alignItems: 'baseline',
            justifyContent: 'space-between',
            borderTop: `1px solid ${scheme.border}`,
            paddingTop: '8px',
            marginBottom: '12px',
          }}>
            <span style={{ fontSize: '0.75rem', color: scheme.textLight }}>Total carreira</span>
            <span style={{ fontSize: '1.125rem', fontWeight: 600, color: scheme.text, fontFamily: tokens.fonts.mono }}>
              {totalPercentage.toFixed(1)}%
            </span>
          </div>

          {/* Sessions Info */}
          <div style={{ fontSize: '0.75rem', color: scheme.textLight, textAlign: 'center' }}>
            {totalSessions} sessões na legislatura atual
          </div>
        </div>
      </div>

      {/* Screen reader description */}
      <p id="attendance-description" className="sr-only">
        Taxa de presença às sessões parlamentares. Clique para ver detalhes.
      </p>
    </article>
  );
};

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
  const [selectedLegislature, setSelectedLegislature] = useState(null);
  
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
        const deputadoResponse = await apiFetch(`deputados/${cadId}/detalhes`);
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
        if (selectedLegislature) {
          apiParams.set('legislatura', selectedLegislature);
        }
        apiParams.set('page', currentPage.toString());
        apiParams.set('per_page', '50');
        
        const atividadesUrl = `deputados/${cadId}/atividades?${apiParams.toString()}`;
        const atividadesResponse = await apiFetch(atividadesUrl);
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
          const conflitosResponse = await apiFetch(`deputados/${cadId}/conflitos-interesse`);
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
          const attendanceResponse = await apiFetch(`deputados/${cadId}/attendance`);
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
  }, [cadId, interventionTypeFilter, interventionSort, currentPage, selectedLegislature]);

  if (loading) {
    return <LoadingSpinner message="A carregar dados do deputado" />;
  }

  if (error) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: tokens.colors.bgPrimary,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: tokens.fonts.body,
      }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{
            color: tokens.colors.accent,
            marginBottom: '16px',
            fontSize: '0.938rem',
          }}>Erro: {error}</p>
          <Link
            to="/deputados"
            style={{
              color: tokens.colors.primary,
              textDecoration: 'none',
            }}
            onMouseEnter={(e) => e.target.style.textDecoration = 'underline'}
            onMouseLeave={(e) => e.target.style.textDecoration = 'none'}
          >
            Voltar aos deputados
          </Link>
        </div>
      </div>
    );
  }

  if (!deputado) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: tokens.colors.bgPrimary,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: tokens.fonts.body,
      }}>
        <p style={{ color: tokens.colors.textSecondary }}>Deputado não encontrado</p>
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
    <div style={{
      minHeight: '100vh',
      backgroundColor: tokens.colors.bgPrimary,
      fontFamily: tokens.fonts.body,
    }}>
      {/* Header */}
      <div style={{
        backgroundColor: tokens.colors.bgSecondary,
        borderBottom: `1px solid ${tokens.colors.border}`,
      }}>
        <div style={{
          maxWidth: '1280px',
          margin: '0 auto',
          padding: '16px 24px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <Link
                to="/deputados"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  color: tokens.colors.textSecondary,
                  textDecoration: 'none',
                  fontSize: '0.875rem',
                  transition: 'color 0.15s ease',
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = tokens.colors.primary}
                onMouseLeave={(e) => e.currentTarget.style.color = tokens.colors.textSecondary}
              >
                <ArrowLeft style={{ width: '18px', height: '18px', marginRight: '8px' }} />
                Voltar aos Deputados
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div style={{
        maxWidth: '1280px',
        margin: '0 auto',
        padding: '32px 24px',
      }}>
        {/* Perfil do Deputado */}
        <div style={{
          backgroundColor: tokens.colors.bgSecondary,
          border: `1px solid ${tokens.colors.border}`,
          borderRadius: '4px',
          marginBottom: '32px',
        }}>
          <div style={{ padding: '32px 24px' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '24px', flexWrap: 'wrap' }}>
              {/* Avatar */}
              <div style={{ flexShrink: 0 }}>
                {deputado.picture_url ? (
                  <img
                    src={deputado.picture_url}
                    alt={deputado.nome}
                    style={{
                      width: '96px',
                      height: '96px',
                      borderRadius: '50%',
                      objectFit: 'cover',
                      backgroundColor: tokens.colors.border,
                      border: `2px solid ${tokens.colors.border}`,
                    }}
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                ) : null}
                <div style={{
                  width: '96px',
                  height: '96px',
                  borderRadius: '50%',
                  backgroundColor: '#E8F5E9',
                  display: deputado.picture_url ? 'none' : 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <User style={{ width: '48px', height: '48px', color: tokens.colors.primary }} />
                </div>
              </div>

              {/* Informações Básicas */}
              <div style={{ flex: 1, minWidth: '300px' }}>
                <h1 style={{
                  fontFamily: tokens.fonts.headline,
                  fontSize: '1.875rem',
                  fontWeight: 700,
                  color: tokens.colors.textPrimary,
                  marginBottom: '8px',
                  lineHeight: 1.2,
                }}>
                  {deputado.nome}
                </h1>

                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  alignItems: 'center',
                  gap: '16px',
                  color: tokens.colors.textSecondary,
                  marginBottom: '16px',
                  fontSize: '0.875rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <Briefcase style={{ width: '16px', height: '16px', marginRight: '8px' }} />
                    <span>{deputado.profissao || 'Profissão não informada'}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <MapPin style={{ width: '16px', height: '16px', marginRight: '8px' }} />
                    <span>{deputado.circulo}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <Calendar style={{ width: '16px', height: '16px', marginRight: '8px' }} />
                    <span>Mandato desde {new Date(deputado.mandato.inicio).toLocaleDateString('pt-PT')}</span>
                  </div>
                </div>

                {/* Partido */}
                {deputado.partido && (
                  <Link
                    to={`/partidos/${encodeURIComponent(deputado.partido.id)}`}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      padding: '6px 12px',
                      borderRadius: '4px',
                      fontSize: '0.813rem',
                      fontWeight: 500,
                      backgroundColor: '#E8F5E9',
                      color: tokens.colors.primary,
                      textDecoration: 'none',
                      border: `1px solid ${tokens.colors.primary}20`,
                      transition: 'background-color 0.15s ease',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#C8E6C9'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#E8F5E9'}
                  >
                    {deputado.partido.sigla} - {deputado.partido.nome}
                  </Link>
                )}
              </div>

              {/* Status and Actions */}
              <div style={{ flexShrink: 0 }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '12px' }}>
                  {/* Status Badge */}
                  {deputado.career_info?.is_currently_active ? (
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      padding: '6px 12px',
                      borderRadius: '4px',
                      fontSize: '0.813rem',
                      fontWeight: 500,
                      backgroundColor: tokens.colors.successBg,
                      color: tokens.colors.success,
                      border: `1px solid ${tokens.colors.success}30`,
                    }}>
                      <div style={{
                        width: '8px',
                        height: '8px',
                        backgroundColor: tokens.colors.success,
                        borderRadius: '50%',
                        marginRight: '8px',
                      }} />
                      Ativo
                    </span>
                  ) : deputado.career_info?.latest_completed_mandate ? (
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      padding: '6px 12px',
                      borderRadius: '4px',
                      fontSize: '0.813rem',
                      fontWeight: 500,
                      backgroundColor: tokens.colors.bgPrimary,
                      color: tokens.colors.textSecondary,
                      border: `1px solid ${tokens.colors.border}`,
                    }}>
                      <div style={{
                        width: '8px',
                        height: '8px',
                        backgroundColor: tokens.colors.textMuted,
                        borderRadius: '50%',
                        marginRight: '8px',
                      }} />
                      Último mandato: {deputado.career_info.latest_completed_mandate.legislatura} ({deputado.career_info.latest_completed_mandate.periodo})
                    </span>
                  ) : (
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      padding: '6px 12px',
                      borderRadius: '4px',
                      fontSize: '0.813rem',
                      fontWeight: 500,
                      backgroundColor: tokens.colors.bgPrimary,
                      color: tokens.colors.textSecondary,
                      border: `1px solid ${tokens.colors.border}`,
                    }}>
                      <div style={{
                        width: '8px',
                        height: '8px',
                        backgroundColor: tokens.colors.textMuted,
                        borderRadius: '50%',
                        marginRight: '8px',
                      }} />
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
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        padding: '8px 16px',
                        border: `1px solid ${tokens.colors.primary}`,
                        fontSize: '0.813rem',
                        fontWeight: 500,
                        borderRadius: '4px',
                        color: tokens.colors.primary,
                        backgroundColor: tokens.colors.bgSecondary,
                        cursor: 'pointer',
                        transition: 'background-color 0.15s ease',
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#E8F5E9'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = tokens.colors.bgSecondary}
                      title="Enviar email através do site oficial do Parlamento"
                    >
                      <Mail style={{ width: '16px', height: '16px', marginRight: '8px' }} />
                      Enviar e-mail
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Political Performance Metrics - Meaningful Statistics */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
            <BarChart3 style={{ width: '24px', height: '24px', color: tokens.colors.primary, marginRight: '8px' }} />
            <h3 style={{
              fontFamily: tokens.fonts.headline,
              fontSize: '1.125rem',
              fontWeight: 600,
              color: tokens.colors.textPrimary,
            }}>Performance Parlamentar</h3>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '16px',
          }}>
            {/* Legislative Effectiveness */}
            <div style={{
              backgroundColor: tokens.colors.bgSecondary,
              border: `1px solid ${tokens.colors.border}`,
              borderRadius: '4px',
              padding: '20px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                <Target style={{ width: '32px', height: '32px', color: tokens.colors.primary }} />
                <div style={{ marginLeft: '12px' }}>
                  <p style={{ fontSize: '0.813rem', fontWeight: 500, color: tokens.colors.textSecondary }}>Eficácia Legislativa</p>
                  <p style={{
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    color: tokens.colors.textPrimary,
                    fontFamily: tokens.fonts.mono,
                  }}>
                    {deputado.estatisticas.iniciativas_propostas}
                  </p>
                </div>
              </div>
              <div style={{ fontSize: '0.75rem', color: tokens.colors.textMuted }}>
                <span style={{ fontWeight: 600 }}>Taxa Atividade:</span> {deputado.estatisticas.taxa_atividade_anual}/ano
              </div>
              <div style={{ fontSize: '0.75rem', color: tokens.colors.textMuted, marginTop: '4px' }}>
                Iniciativas + Intervenções por ano de serviço
              </div>
            </div>

            {/* Political Experience */}
            <div style={{
              backgroundColor: tokens.colors.bgSecondary,
              border: `1px solid ${tokens.colors.border}`,
              borderRadius: '4px',
              padding: '20px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                <Award style={{ width: '32px', height: '32px', color: tokens.colors.purple }} />
                <div style={{ marginLeft: '12px' }}>
                  <p style={{ fontSize: '0.813rem', fontWeight: 500, color: tokens.colors.textSecondary }}>Experiência</p>
                  <p style={{
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    color: tokens.colors.textPrimary,
                    fontFamily: tokens.fonts.mono,
                  }}>
                    {deputado.estatisticas.nivel_experiencia}
                  </p>
                </div>
              </div>
              <div style={{ fontSize: '0.75rem', color: tokens.colors.textMuted }}>
                <span style={{ fontWeight: 600 }}>{deputado.estatisticas.total_mandatos}</span> mandatos • <span style={{ fontWeight: 600 }}>{deputado.estatisticas.tempo_servico_anos}</span> anos
              </div>
              <div style={{ fontSize: '0.75rem', color: tokens.colors.textMuted, marginTop: '4px' }}>
                Legislaturas: {deputado.estatisticas.legislaturas_servidas}
              </div>
            </div>

            {/* Parliamentary Engagement */}
            <div style={{
              backgroundColor: tokens.colors.bgSecondary,
              border: `1px solid ${tokens.colors.border}`,
              borderRadius: '4px',
              padding: '20px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                <Activity style={{
                  width: '32px',
                  height: '32px',
                  color: deputado.estatisticas.taxa_assiduidade >= 0.9 ? tokens.colors.success :
                         deputado.estatisticas.taxa_assiduidade >= 0.8 ? tokens.colors.primary :
                         deputado.estatisticas.taxa_assiduidade >= 0.7 ? tokens.colors.warning :
                         tokens.colors.orange,
                }} />
                <div style={{ marginLeft: '12px' }}>
                  <p style={{ fontSize: '0.813rem', fontWeight: 500, color: tokens.colors.textSecondary }}>Participação</p>
                  <p style={{
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    fontFamily: tokens.fonts.mono,
                    color: deputado.estatisticas.taxa_assiduidade >= 0.9 ? tokens.colors.success :
                           deputado.estatisticas.taxa_assiduidade >= 0.8 ? tokens.colors.primary :
                           deputado.estatisticas.taxa_assiduidade >= 0.7 ? tokens.colors.warning :
                           tokens.colors.orange,
                  }}>
                    {(deputado.estatisticas.taxa_assiduidade * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
              <div style={{ fontSize: '0.75rem', color: tokens.colors.textMuted }}>
                <span style={{ fontWeight: 600 }}>{deputado.estatisticas.intervencoes_parlamentares}</span> intervenções
              </div>
              <div style={{ fontSize: '0.75rem', color: tokens.colors.textMuted, marginTop: '4px' }}>
                Taxa de assiduidade às sessões plenárias
              </div>
            </div>

            {/* National Performance Context */}
            <div style={{
              backgroundColor: tokens.colors.bgSecondary,
              border: `1px solid ${tokens.colors.border}`,
              borderRadius: '4px',
              padding: '20px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                <Globe style={{
                  width: '32px',
                  height: '32px',
                  color: deputado.estatisticas.percentil_nacional >= 75 ? tokens.colors.success :
                         deputado.estatisticas.percentil_nacional >= 50 ? tokens.colors.primary :
                         deputado.estatisticas.percentil_nacional >= 25 ? tokens.colors.warning :
                         tokens.colors.orange,
                }} />
                <div style={{ marginLeft: '12px' }}>
                  <p style={{ fontSize: '0.813rem', fontWeight: 500, color: tokens.colors.textSecondary }}>Ranking Nacional</p>
                  <p style={{
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    fontFamily: tokens.fonts.mono,
                    color: deputado.estatisticas.percentil_nacional >= 75 ? tokens.colors.success :
                           deputado.estatisticas.percentil_nacional >= 50 ? tokens.colors.primary :
                           deputado.estatisticas.percentil_nacional >= 25 ? tokens.colors.warning :
                           tokens.colors.orange,
                  }}>
                    {deputado.estatisticas.percentil_nacional}º
                  </p>
                </div>
              </div>
              <div style={{ fontSize: '0.75rem', color: tokens.colors.textMuted }}>
                {deputado.estatisticas.consistencia_eleitoral && (
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <CheckCircle2 style={{ width: '12px', height: '12px', color: tokens.colors.success, marginRight: '4px' }} />
                    <span>Círculo consistente: {deputado.estatisticas.circulo_principal}</span>
                  </div>
                )}
              </div>
              <div style={{ fontSize: '0.75rem', color: tokens.colors.textMuted, marginTop: '4px' }}>
                Percentil com base na atividade legislativa
              </div>
            </div>
          </div>

          {/* Comparative Context Footer */}
          <div style={{
            marginTop: '16px',
            padding: '16px',
            backgroundColor: tokens.colors.bgPrimary,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '4px',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
              fontSize: '0.813rem',
              color: tokens.colors.textSecondary,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <Info style={{ width: '16px', height: '16px', marginRight: '4px' }} />
                  <span>Contexto Comparativo:</span>
                </div>
                {deputado.estatisticas.partido_atual && (
                  <span>
                    Média do <strong>{deputado.estatisticas.partido_atual}</strong>: {deputado.estatisticas.media_partido_iniciativas} iniciativas
                  </span>
                )}
              </div>
              <div style={{ fontSize: '0.75rem', color: tokens.colors.textMuted }}>
                Dados baseados em atividade parlamentar verificável
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Overview Estatísticas de Atividade */}
        {loading ? (
          <StatisticsLoadingSkeleton />
        ) : error && !atividades ? (
          <StatisticsError 
            error={error} 
            onRetry={() => window.location.reload()} 
          />
        ) : atividades?.statistics ? (
          <section className="bg-white rounded-lg shadow-sm border mb-8" aria-labelledby="activity-overview-heading">
            <header className="px-6 py-4 border-b border-gray-200">
              <h3 id="activity-overview-heading" className="text-lg font-semibold text-gray-900">Resumo de Atividade Parlamentar</h3>
              <p className="text-sm text-gray-500 mt-1">Atividade na legislatura atual vs. total da carreira</p>
            </header>
            <div className="p-4 sm:p-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 animate-fade-in" role="list" style={{ animationDelay: '0.1s' }}>
                {/* Intervenções Card */}
                <StatisticCard
                  title="Intervenções"
                  icon={MessageSquare}
                  current={atividades.statistics.current_legislature.intervencoes_count}
                  total={atividades.statistics.total_career.intervencoes_count}
                  colorScheme="blue"
                  description="Participações em debates parlamentares"
                  tabId="intervencoes"
                  onCardClick={handleTabChange}
                />

                {/* Iniciativas Card */}
                <StatisticCard
                  title="Iniciativas"
                  icon={FileText}
                  current={atividades.statistics.current_legislature.iniciativas_count}
                  total={atividades.statistics.total_career.iniciativas_count}
                  colorScheme="green"
                  description="Propostas de lei e outras iniciativas apresentadas"
                  tabId="iniciativas"
                  onCardClick={handleTabChange}
                />

                {/* Votações Card */}
                <StatisticCard
                  title="Votações"
                  icon={Vote}
                  current={atividades.statistics.current_legislature.votacoes_count}
                  total={atividades.statistics.total_career.votacoes_count}
                  colorScheme="purple"
                  description="Participações em votações parlamentares"
                  tabId="votacoes"
                  onCardClick={handleTabChange}
                />

                {/* Taxa de Presença Card */}
                {atividades.statistics.current_legislature.attendance_rate !== undefined && (
                  <AttendanceCard
                    currentRate={atividades.statistics.current_legislature.attendance_rate}
                    totalRate={atividades.statistics.total_career.attendance_rate}
                    totalSessions={atividades.statistics.current_legislature.total_sessions}
                    onCardClick={handleTabChange}
                  />
                )}
              </div>
              
              {/* Enhanced insight footer */}
              <footer className="mt-6 pt-4 border-t border-gray-100">
                <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
                  <Info className="h-4 w-4" aria-hidden="true" />
                  <p className="text-center">
                    Os números da "legislatura atual" referem-se ao mandato em curso. 
                    O "total carreira" inclui todos os mandatos anteriores deste deputado.
                  </p>
                </div>
              </footer>
            </div>
          </section>
        ) : null}

        {/* Tabs de Atividade */}
        <div style={{
          backgroundColor: tokens.colors.bgSecondary,
          border: `1px solid ${tokens.colors.border}`,
          borderRadius: '4px',
        }}>
          {/* Tab Headers */}
          <div style={{ borderBottom: `1px solid ${tokens.colors.border}` }}>
            <nav style={{
              display: 'flex',
              gap: '8px',
              padding: '0 24px',
              overflowX: 'auto',
            }}>
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => handleTabChange(tab.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '16px 8px',
                      borderBottom: isActive ? `2px solid ${tokens.colors.primary}` : '2px solid transparent',
                      fontWeight: isActive ? 600 : 400,
                      fontSize: '0.813rem',
                      color: isActive ? tokens.colors.primary : tokens.colors.textSecondary,
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                      transition: 'color 0.15s ease, border-color 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.color = tokens.colors.textPrimary;
                        e.currentTarget.style.borderBottomColor = tokens.colors.border;
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.color = tokens.colors.textSecondary;
                        e.currentTarget.style.borderBottomColor = 'transparent';
                      }
                    }}
                  >
                    <Icon style={{ width: '16px', height: '16px', marginRight: '8px' }} />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div style={{ padding: '24px' }}>
            {activeTab === 'biografia' && (
              <div>
                <div style={{ maxWidth: 'none' }}>
                  {(deputado.nome_completo || deputado.data_nascimento || deputado.naturalidade || deputado.profissao || deputado.habilitacoes_academicas || (deputado.atividades_orgaos && deputado.atividades_orgaos.length > 0)) ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                      {/* Personal Information Section */}
                      {deputado.nome_completo && (
                        <div style={{
                          backgroundColor: '#E8F5E9',
                          border: `1px solid ${tokens.colors.primary}30`,
                          borderRadius: '4px',
                          padding: '24px',
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                            <div style={{
                              width: '32px',
                              height: '32px',
                              backgroundColor: tokens.colors.primary,
                              borderRadius: '4px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              marginRight: '12px',
                            }}>
                              <User style={{ width: '20px', height: '20px', color: '#FFFFFF' }} />
                            </div>
                            <h4 style={{
                              fontFamily: tokens.fonts.headline,
                              fontSize: '1.125rem',
                              fontWeight: 600,
                              color: tokens.colors.textPrimary,
                            }}>Informações Pessoais</h4>
                          </div>
                          <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                            gap: '16px',
                          }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                              <div>
                                <span style={{
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  color: tokens.colors.primary,
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.05em',
                                }}>Nome Completo</span>
                                <p style={{ color: tokens.colors.textPrimary, fontWeight: 500 }}>{deputado.nome_completo}</p>
                              </div>
                              {deputado.naturalidade && (
                                <div>
                                  <span style={{
                                    fontSize: '0.75rem',
                                    fontWeight: 600,
                                    color: tokens.colors.primary,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.05em',
                                  }}>Naturalidade</span>
                                  <p style={{ color: tokens.colors.textPrimary }}>{deputado.naturalidade}</p>
                                </div>
                              )}
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                              {deputado.data_nascimento && (
                                <div>
                                  <span style={{
                                    fontSize: '0.75rem',
                                    fontWeight: 600,
                                    color: tokens.colors.primary,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.05em',
                                  }}>Data de Nascimento</span>
                                  <p style={{ color: tokens.colors.textPrimary }}>
                                    {new Date(deputado.data_nascimento).toLocaleDateString('pt-PT')}
                                    {' '}
                                    {(() => {
                                      const birthDate = new Date(deputado.data_nascimento);
                                      const today = new Date();
                                      const age = today.getFullYear() - birthDate.getFullYear() -
                                        (today.getMonth() < birthDate.getMonth() ||
                                         (today.getMonth() === birthDate.getMonth() && today.getDate() < birthDate.getDate()) ? 1 : 0);
                                      return age > 0 ? <span style={{ fontSize: '0.875rem', color: tokens.colors.textSecondary }}>({age} anos)</span> : null;
                                    })()}
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Biografia Header */}
                      {(deputado.profissao || deputado.habilitacoes_academicas || deputado.biografia || (deputado.atividades_orgaos && deputado.atividades_orgaos.length > 0)) && (
                        <h3 style={{
                          fontFamily: tokens.fonts.headline,
                          fontSize: '1.125rem',
                          fontWeight: 600,
                          color: tokens.colors.textPrimary,
                          marginBottom: '16px',
                          marginTop: '32px',
                        }}>
                          Biografia
                        </h3>
                      )}

                      {deputado.profissao && (
                        <div style={{ position: 'relative' }}>
                          <div style={{ display: 'flex' }}>
                            <div style={{
                              width: '4px',
                              backgroundColor: tokens.colors.primary,
                              borderRadius: '2px',
                              marginRight: '16px',
                              flexShrink: 0,
                            }} />
                            <div style={{ flex: 1 }}>
                              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                                <Briefcase style={{ width: '20px', height: '20px', color: tokens.colors.primary, marginRight: '8px' }} />
                                <h4 style={{ fontWeight: 600, color: tokens.colors.textPrimary }}>Profissão</h4>
                              </div>
                              <p style={{
                                color: tokens.colors.textSecondary,
                                fontSize: '0.938rem',
                                lineHeight: 1.6,
                                paddingLeft: '28px',
                              }}>
                                {deputado.profissao}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      {deputado.habilitacoes_academicas && (
                        <div style={{ position: 'relative' }}>
                          <div style={{ display: 'flex' }}>
                            <div style={{
                              width: '4px',
                              backgroundColor: tokens.colors.success,
                              borderRadius: '2px',
                              marginRight: '16px',
                              flexShrink: 0,
                            }} />
                            <div style={{ flex: 1 }}>
                              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                                <svg style={{ width: '20px', height: '20px', color: tokens.colors.success, marginRight: '8px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                                </svg>
                                <h4 style={{ fontWeight: 600, color: tokens.colors.textPrimary }}>Habilitações Académicas</h4>
                              </div>
                              <div style={{ paddingLeft: '28px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {deputado.habilitacoes_academicas.split(';').map((hab, index) => (
                                  <div key={index} style={{ display: 'flex', alignItems: 'flex-start' }}>
                                    <div style={{
                                      width: '8px',
                                      height: '8px',
                                      backgroundColor: tokens.colors.success,
                                      borderRadius: '50%',
                                      marginTop: '8px',
                                      marginRight: '12px',
                                      flexShrink: 0,
                                    }} />
                                    <span style={{ fontSize: '0.938rem', lineHeight: 1.6, color: tokens.colors.textSecondary }}>{hab.trim()}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {deputado.biografia && (
                        <div style={{ position: 'relative' }}>
                          <div style={{ display: 'flex' }}>
                            <div style={{
                              width: '4px',
                              backgroundColor: tokens.colors.purple,
                              borderRadius: '2px',
                              marginRight: '16px',
                              flexShrink: 0,
                            }} />
                            <div style={{ flex: 1 }}>
                              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                                <User style={{ width: '20px', height: '20px', color: tokens.colors.purple, marginRight: '8px' }} />
                                <h4 style={{ fontWeight: 600, color: tokens.colors.textPrimary }}>Biografia</h4>
                              </div>
                              <div style={{
                                color: tokens.colors.textSecondary,
                                fontSize: '0.938rem',
                                lineHeight: 1.6,
                                whiteSpace: 'pre-line',
                                paddingLeft: '28px',
                              }}>
                                {deputado.biografia}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {deputado.atividades_orgaos && deputado.atividades_orgaos.length > 0 && (
                        <div style={{ position: 'relative' }}>
                          <div style={{ display: 'flex' }}>
                            <div style={{
                              width: '4px',
                              backgroundColor: tokens.colors.orange,
                              borderRadius: '2px',
                              marginRight: '16px',
                              flexShrink: 0,
                            }} />
                            <div style={{ flex: 1 }}>
                              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
                                <svg style={{ width: '20px', height: '20px', color: tokens.colors.orange, marginRight: '8px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                                </svg>
                                <h4 style={{ fontWeight: 600, color: tokens.colors.textPrimary }}>Atividade em Órgãos Parlamentares</h4>
                              </div>
                              <div style={{ paddingLeft: '28px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                {deputado.atividades_orgaos.map((orgao, index) => (
                                  <div key={index} style={{
                                    backgroundColor: '#FFF7ED',
                                    border: `1px solid ${tokens.colors.orange}30`,
                                    borderRadius: '4px',
                                    padding: '16px',
                                  }}>
                                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                                      <div style={{ flex: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                                          <h5 style={{ fontWeight: 500, color: tokens.colors.textPrimary }}>
                                            {orgao.nome}
                                            {orgao.sigla && (
                                              <span style={{ marginLeft: '8px', fontSize: '0.875rem', color: tokens.colors.orange, fontWeight: 400 }}>({orgao.sigla})</span>
                                            )}
                                          </h5>
                                        </div>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '8px', fontSize: '0.813rem' }}>
                                          <span style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            padding: '4px 8px',
                                            borderRadius: '4px',
                                            fontSize: '0.75rem',
                                            fontWeight: 500,
                                            backgroundColor: orgao.titular ? tokens.colors.successBg : tokens.colors.warningBg,
                                            color: orgao.titular ? tokens.colors.success : tokens.colors.warning,
                                          }}>
                                            {orgao.tipo_membro}
                                          </span>
                                          {orgao.cargo !== 'membro' && (
                                            <span style={{
                                              display: 'inline-flex',
                                              alignItems: 'center',
                                              padding: '4px 8px',
                                              borderRadius: '4px',
                                              fontSize: '0.75rem',
                                              fontWeight: 500,
                                              backgroundColor: '#E8F5E9',
                                              color: tokens.colors.primary,
                                            }}>
                                              {orgao.cargo === 'presidente' ? 'Presidente' :
                                               orgao.cargo === 'vice_presidente' ? 'Vice-Presidente' :
                                               orgao.cargo === 'secretario' ? 'Secretário' :
                                               orgao.cargo}
                                            </span>
                                          )}
                                          {orgao.observacoes && (
                                            <span style={{ color: tokens.colors.textMuted }}>
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
                    <div style={{ textAlign: 'center', padding: '48px 0' }}>
                      <div style={{
                        margin: '0 auto',
                        width: '64px',
                        height: '64px',
                        backgroundColor: tokens.colors.bgPrimary,
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginBottom: '16px',
                      }}>
                        <User style={{ width: '32px', height: '32px', color: tokens.colors.textMuted }} />
                      </div>
                      <p style={{ color: tokens.colors.textMuted, fontSize: '1.125rem', fontWeight: 500, marginBottom: '8px' }}>Informações biográficas não disponíveis</p>
                      <p style={{ fontSize: '0.875rem', color: tokens.colors.textMuted }}>
                        Dados biográficos não foram fornecidos para este deputado
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'intervencoes' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                  <div>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: tokens.colors.textPrimary, fontFamily: tokens.fonts.headline }}>
                      Intervenções Parlamentares
                    </h3>
                    {totalInterventions > 0 && (
                      <p style={{ fontSize: '0.875rem', color: tokens.colors.textMuted, marginTop: '4px' }}>
                        {interventionTypeFilter
                          ? `${atividades?.intervencoes?.length || 0} de ${totalInterventions} intervenções (filtrado por "${interventionTypeFilter}")`
                          : `${totalInterventions} intervenções`
                        }
                      </p>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    {atividades && atividades.intervencoes.length > 0 && (
                      <div style={{ display: 'flex', gap: '8px' }}>
                      <select
                        value={interventionTypeFilter}
                        onChange={(e) => {
                          const newType = e.target.value;
                          setInterventionTypeFilter(newType);
                          setCurrentPage(1);
                          updateInterventionParams({ tipo_intervencao: newType, page: 1 });
                        }}
                        style={{
                          border: `1px solid ${tokens.colors.border}`,
                          borderRadius: '4px',
                          padding: '6px 12px',
                          fontSize: '0.875rem',
                          backgroundColor: tokens.colors.bgSecondary,
                          color: tokens.colors.textPrimary,
                          fontFamily: tokens.fonts.body,
                        }}
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
                        style={{
                          border: `1px solid ${tokens.colors.border}`,
                          borderRadius: '4px',
                          padding: '6px 12px',
                          fontSize: '0.875rem',
                          backgroundColor: tokens.colors.bgSecondary,
                          color: tokens.colors.textPrimary,
                          fontFamily: tokens.fonts.body,
                        }}
                      >
                        <option value="newest">Mais recentes</option>
                        <option value="oldest">Mais antigas</option>
                        <option value="type">Por tipo</option>
                      </select>
                      </div>
                    )}
                    <LegislatureDropdown
                      selectedLegislature={selectedLegislature}
                      onLegislatureChange={setSelectedLegislature}
                      deputyCadId={cadId}
                      size="sm"
                    />
                  </div>
                </div>

                {atividades && atividades.intervencoes.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    {(() => {
                      const interventions = atividades.intervencoes || [];

                      // Helper functions for inline styles
                      const getTipoStyle = (tipo) => {
                        if (tipo?.includes('Interpelação')) return { backgroundColor: colorSchemes.blue.bg, color: colorSchemes.blue.text, borderColor: colorSchemes.blue.border };
                        if (tipo?.includes('Declaração')) return { backgroundColor: colorSchemes.green.bg, color: colorSchemes.green.text, borderColor: colorSchemes.green.border };
                        if (tipo?.includes('Pedido')) return { backgroundColor: colorSchemes.orange.bg, color: colorSchemes.orange.text, borderColor: colorSchemes.orange.border };
                        if (tipo?.includes('Pergunta')) return { backgroundColor: colorSchemes.purple.bg, color: colorSchemes.purple.text, borderColor: colorSchemes.purple.border };
                        return { backgroundColor: tokens.colors.bgPrimary, color: tokens.colors.textSecondary, borderColor: tokens.colors.border };
                      };

                      const getQualidadeStyle = (qualidade) => {
                        if (qualidade === 'Deputado') return { backgroundColor: colorSchemes.blue.bg, color: colorSchemes.blue.text, borderColor: colorSchemes.blue.border };
                        if (qualidade === 'P.A.R.') return { backgroundColor: colorSchemes.purple.bg, color: colorSchemes.purple.text, borderColor: colorSchemes.purple.border };
                        return { backgroundColor: tokens.colors.bgPrimary, color: tokens.colors.textSecondary, borderColor: tokens.colors.border };
                      };

                      return interventions.map((intervencao, index) => (
                        <div key={index} style={{
                          border: `1px solid ${tokens.colors.border}`,
                          borderRadius: '4px',
                          padding: '24px',
                          backgroundColor: tokens.colors.bgSecondary,
                          transition: 'border-color 0.15s ease',
                        }}>
                          {/* Context badges */}
                          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
                            <span style={{
                              ...getTipoStyle(intervencao.tipo),
                              padding: '4px 12px',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              fontWeight: 500,
                              border: `1px solid ${getTipoStyle(intervencao.tipo).borderColor}`,
                            }}>
                              {intervencao.tipo}
                            </span>
                            {intervencao.qualidade && (
                              <span style={{
                                ...getQualidadeStyle(intervencao.qualidade),
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '0.75rem',
                                fontWeight: 500,
                                border: `1px solid ${getQualidadeStyle(intervencao.qualidade).borderColor}`,
                              }}>
                                {intervencao.qualidade}
                              </span>
                            )}
                            {intervencao.sessao_numero && (
                              <span style={{
                                padding: '4px 8px',
                                backgroundColor: tokens.colors.bgPrimary,
                                color: tokens.colors.textSecondary,
                                fontSize: '0.75rem',
                                fontWeight: 500,
                                borderRadius: '4px',
                                border: `1px solid ${tokens.colors.border}`,
                              }}>
                                Sessão {intervencao.sessao_numero}
                              </span>
                            )}
                          </div>

                          <div style={{ display: 'flex', gap: '16px' }}>
                            {/* Video Thumbnail */}
                            {intervencao.url_video && intervencao.thumbnail_url ? (
                              <div style={{ position: 'relative', flexShrink: 0 }}>
                                <div
                                  style={{
                                    width: '144px',
                                    height: '88px',
                                    borderRadius: '4px',
                                    overflow: 'hidden',
                                    backgroundColor: tokens.colors.bgPrimary,
                                    position: 'relative',
                                    cursor: 'pointer',
                                  }}
                                  onClick={() => window.open(intervencao.url_video, '_blank')}
                                >
                                  <img
                                    src={intervencao.thumbnail_url}
                                    alt="Video thumbnail"
                                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                    onError={(e) => {
                                      e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTQ0IiBoZWlnaHQ9IjkwIiB2aWV3Qm94PSIwIDAgMTQ0IDkwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8cmVjdCB3aWR0aD0iMTQ0IiBoZWlnaHQ9IjkwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik02MCA0NUw4NCA1N0w2MCA2OVY0NVoiIGZpbGw9IiM5Q0EzQUYiLz4KPC9zdmc+';
                                    }}
                                  />
                                  {intervencao.duracao_video && (
                                    <div style={{
                                      position: 'absolute',
                                      bottom: '4px',
                                      right: '4px',
                                      backgroundColor: 'rgba(0,0,0,0.8)',
                                      color: '#FFFFFF',
                                      fontSize: '0.75rem',
                                      padding: '2px 6px',
                                      borderRadius: '2px',
                                      display: 'flex',
                                      alignItems: 'center',
                                    }}>
                                      <Clock style={{ width: '12px', height: '12px', marginRight: '4px' }} />
                                      {intervencao.duracao_video}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ) : intervencao.url_video ? (
                              <div style={{ position: 'relative', flexShrink: 0 }}>
                                <div
                                  style={{
                                    width: '144px',
                                    height: '88px',
                                    borderRadius: '4px',
                                    overflow: 'hidden',
                                    backgroundColor: colorSchemes.blue.bg,
                                    border: `1px solid ${colorSchemes.blue.border}`,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    cursor: 'pointer',
                                  }}
                                  onClick={() => window.open(intervencao.url_video, '_blank')}
                                >
                                  <Play style={{ width: '32px', height: '32px', color: colorSchemes.blue.primary }} />
                                </div>
                              </div>
                            ) : null}

                            {/* Content */}
                            <div style={{ flex: 1, minWidth: 0 }}>
                              {/* Header with date and action buttons */}
                              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '12px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.875rem', color: tokens.colors.textMuted }}>
                                  <div style={{ display: 'flex', alignItems: 'center' }}>
                                    <Calendar style={{ width: '16px', height: '16px', marginRight: '4px' }} />
                                    {new Date(intervencao.data).toLocaleDateString('pt-PT')}
                                  </div>
                                </div>

                                {/* Action Buttons */}
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '16px', flexShrink: 0 }}>
                                  {intervencao.url_video && (
                                    <button
                                      onClick={() => window.open(intervencao.url_video, '_blank')}
                                      style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        padding: '6px 12px',
                                        border: `1px solid ${colorSchemes.blue.border}`,
                                        fontSize: '0.875rem',
                                        fontWeight: 500,
                                        borderRadius: '4px',
                                        color: colorSchemes.blue.text,
                                        backgroundColor: colorSchemes.blue.bg,
                                        cursor: 'pointer',
                                        whiteSpace: 'nowrap',
                                      }}
                                    >
                                      <Play className="h-4 w-4 mr-1" />
                                      Ver Vídeo
                                    </button>
                                  )}
                                  {intervencao.publicacao?.url_diario && (
                                    <button
                                      onClick={() => window.open(intervencao.publicacao.url_diario, '_blank')}
                                      style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        padding: '6px 12px',
                                        border: `1px solid ${colorSchemes.orange.border}`,
                                        fontSize: '0.875rem',
                                        fontWeight: 500,
                                        borderRadius: '4px',
                                        color: colorSchemes.orange.text,
                                        backgroundColor: colorSchemes.orange.bg,
                                        cursor: 'pointer',
                                        whiteSpace: 'nowrap',
                                      }}
                                    >
                                      <ExternalLink style={{ width: '16px', height: '16px', marginRight: '4px' }} />
                                      {intervencao.publicacao.pub_numero ? `DR ${intervencao.publicacao.pub_numero}` : 'Diário'}
                                    </button>
                                  )}
                                </div>
                              </div>

                              {/* Subject/Title */}
                              {intervencao.assunto && (
                                <div style={{ marginBottom: '12px' }}>
                                  <h4 style={{ color: tokens.colors.textPrimary, fontWeight: 500, fontSize: '0.875rem', lineHeight: 1.4 }}>
                                    {intervencao.assunto}
                                  </h4>
                                </div>
                              )}

                              {/* Summary */}
                              {intervencao.resumo && (
                                <p style={{ color: tokens.colors.textSecondary, fontSize: '0.875rem', lineHeight: 1.6, marginBottom: '12px' }}>
                                  {intervencao.resumo}
                                </p>
                              )}

                              {/* Additional Info */}
                              {(intervencao.sumario || intervencao.fase_sessao) && (
                                <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: `1px solid ${tokens.colors.border}` }}>
                                  {intervencao.sumario && (
                                    <p style={{ fontSize: '0.875rem', color: tokens.colors.textSecondary, marginBottom: '8px' }}>
                                      <span style={{ fontWeight: 500, color: tokens.colors.textPrimary }}>Sumário:</span> {intervencao.sumario}
                                    </p>
                                  )}
                                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                    {intervencao.fase_sessao && (
                                      <span style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        padding: '4px 8px',
                                        borderRadius: '4px',
                                        fontSize: '0.75rem',
                                        fontWeight: 500,
                                        backgroundColor: tokens.colors.bgPrimary,
                                        color: tokens.colors.textSecondary,
                                        border: `1px solid ${tokens.colors.border}`,
                                      }}>
                                        {intervencao.fase_sessao}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              )}

                              {/* Publication metadata */}
                              {intervencao.publicacao && (
                                <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: `1px solid ${tokens.colors.border}` }}>
                                  <div style={{ display: 'flex', gap: '16px', fontSize: '0.75rem', color: tokens.colors.textMuted }}>
                                    {intervencao.publicacao.pub_tipo && (
                                      <span style={{ display: 'flex', alignItems: 'center' }}>
                                        📰 {intervencao.publicacao.pub_tipo}
                                      </span>
                                    )}
                                    {intervencao.publicacao.pub_data && (
                                      <span style={{ display: 'flex', alignItems: 'center' }}>
                                        📅 Pub: {new Date(intervencao.publicacao.pub_data).toLocaleDateString('pt-PT')}
                                      </span>
                                    )}
                                    {intervencao.publicacao.paginas && (
                                      <span style={{ display: 'flex', alignItems: 'center' }}>
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
                      <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        gap: '8px',
                        marginTop: '32px',
                        paddingTop: '24px',
                        borderTop: `1px solid ${tokens.colors.border}`,
                      }}>
                        <button
                          onClick={() => {
                            if (currentPage > 1) {
                              const newPage = currentPage - 1;
                              setCurrentPage(newPage);
                              updateInterventionParams({ page: newPage });
                            }
                          }}
                          disabled={currentPage <= 1}
                          style={{
                            padding: '8px 12px',
                            fontSize: '0.875rem',
                            backgroundColor: tokens.colors.bgSecondary,
                            border: `1px solid ${tokens.colors.border}`,
                            borderRadius: '4px',
                            cursor: currentPage <= 1 ? 'not-allowed' : 'pointer',
                            opacity: currentPage <= 1 ? 0.5 : 1,
                            color: tokens.colors.textPrimary,
                          }}
                        >
                          Anterior
                        </button>

                        <span style={{ padding: '8px 16px', fontSize: '0.875rem', color: tokens.colors.textSecondary, fontFamily: tokens.fonts.mono }}>
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
                          style={{
                            padding: '8px 12px',
                            fontSize: '0.875rem',
                            backgroundColor: tokens.colors.bgSecondary,
                            border: `1px solid ${tokens.colors.border}`,
                            borderRadius: '4px',
                            cursor: currentPage >= totalPages ? 'not-allowed' : 'pointer',
                            opacity: currentPage >= totalPages ? 0.5 : 1,
                            color: tokens.colors.textPrimary,
                          }}
                        >
                          Próxima
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '48px 0' }}>
                    <div style={{
                      margin: '0 auto',
                      width: '64px',
                      height: '64px',
                      backgroundColor: tokens.colors.bgPrimary,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginBottom: '16px',
                    }}>
                      <MessageSquare style={{ width: '32px', height: '32px', color: tokens.colors.textMuted }} />
                    </div>
                    <p style={{ color: tokens.colors.textMuted, fontSize: '1.125rem', fontWeight: 500, marginBottom: '8px' }}>Nenhuma intervenção registada</p>
                    <p style={{ fontSize: '0.875rem', color: tokens.colors.textMuted }}>
                      Os dados de intervenções serão carregados em futuras atualizações
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'iniciativas' && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                  <div>
                    <h3 style={{
                      fontFamily: tokens.fonts.headline,
                      fontSize: '1.25rem',
                      fontWeight: '600',
                      color: tokens.colors.textPrimary,
                      margin: 0
                    }}>
                      Iniciativas Legislativas
                    </h3>
                    <p style={{
                      fontFamily: tokens.fonts.body,
                      fontSize: '0.875rem',
                      color: tokens.colors.textMuted,
                      marginTop: '0.25rem',
                      margin: '0.25rem 0 0 0'
                    }}>
                      Projetos de lei e resoluções apresentados pelo deputado
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    {atividades && atividades.iniciativas && atividades.iniciativas.length > 0 && (
                      <div style={{
                        fontFamily: tokens.fonts.mono,
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        color: tokens.colors.primary,
                        backgroundColor: '#E8F5E9',
                        padding: '0.375rem 0.75rem',
                        borderRadius: '2px',
                        border: `1px solid ${tokens.colors.primary}20`
                      }}>
                        {atividades.iniciativas.length} iniciativas
                      </div>
                    )}
                    <LegislatureDropdown
                      selectedLegislature={selectedLegislature}
                      onLegislatureChange={setSelectedLegislature}
                      deputyCadId={cadId}
                      size="sm"
                    />
                  </div>
                </div>
                
                {atividades && atividades.iniciativas && atividades.iniciativas.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {atividades.iniciativas.map((iniciativa, index) => {
                      // Helper function to get type styling - returns style object
                      const getTypeStyle = (tipo) => {
                        switch (tipo) {
                          case 'J':
                            return { backgroundColor: colorSchemes.blue.bg, color: colorSchemes.blue.text, borderColor: colorSchemes.blue.border };
                          case 'R':
                            return { backgroundColor: colorSchemes.green.bg, color: colorSchemes.green.text, borderColor: colorSchemes.green.border };
                          case 'P':
                            return { backgroundColor: colorSchemes.purple.bg, color: colorSchemes.purple.text, borderColor: colorSchemes.purple.border };
                          case 'D':
                            return { backgroundColor: colorSchemes.orange.bg, color: colorSchemes.orange.text, borderColor: colorSchemes.orange.border };
                          default:
                            return { backgroundColor: '#F3F4F6', color: tokens.colors.textSecondary, borderColor: tokens.colors.border };
                        }
                      };

                      // Helper function to get status styling - returns style object
                      const getStatusStyle = (estado) => {
                        if (!estado) return null;
                        switch (estado?.toLowerCase()) {
                          case 'aprovado':
                            return { backgroundColor: tokens.colors.successBg, color: tokens.colors.success, borderColor: '#BBF7D0' };
                          case 'rejeitado':
                            return { backgroundColor: tokens.colors.dangerBg, color: tokens.colors.danger, borderColor: '#FECACA' };
                          case 'em votação':
                            return { backgroundColor: tokens.colors.warningBg, color: tokens.colors.warning, borderColor: '#FDE68A' };
                          case 'retirado':
                            return { backgroundColor: '#F9FAFB', color: tokens.colors.textSecondary, borderColor: tokens.colors.border };
                          default:
                            return { backgroundColor: tokens.colors.infoBg, color: tokens.colors.info, borderColor: '#BFDBFE' };
                        }
                      };

                      // Helper function to get progress bar color
                      const getProgressColor = (estado) => {
                        if (!estado) return tokens.colors.blue;
                        switch (estado?.toLowerCase()) {
                          case 'aprovado': return tokens.colors.success;
                          case 'rejeitado': return tokens.colors.danger;
                          case 'em votação': return '#F59E0B';
                          default: return tokens.colors.blue;
                        }
                      };

                      // Helper function to get progress bar width
                      const getProgressWidth = (estado) => {
                        if (!estado) return '50%';
                        switch (estado?.toLowerCase()) {
                          case 'aprovado': return '100%';
                          case 'rejeitado': return '100%';
                          case 'em votação': return '75%';
                          default: return '50%';
                        }
                      };

                      const typeStyles = getTypeStyle(iniciativa.tipo);
                      const statusStyles = getStatusStyle(iniciativa.estado);

                      return (
                        <div key={index} style={{
                          backgroundColor: tokens.colors.bgSecondary,
                          border: `1px solid ${tokens.colors.border}`,
                          borderRadius: '4px',
                          padding: '1.5rem',
                          transition: 'border-color 0.2s ease'
                        }}>
                          {/* Header with type and date */}
                          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                              <span style={{
                                ...typeStyles,
                                fontFamily: tokens.fonts.body,
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                padding: '0.375rem 0.75rem',
                                borderRadius: '2px',
                                border: `1px solid ${typeStyles.borderColor}`,
                                textTransform: 'uppercase',
                                letterSpacing: '0.025em'
                              }}>
                                {iniciativa.tipo_descricao || iniciativa.tipo}
                              </span>
                              {iniciativa.estado && statusStyles && (
                                <span style={{
                                  ...statusStyles,
                                  fontFamily: tokens.fonts.body,
                                  fontSize: '0.75rem',
                                  fontWeight: '500',
                                  padding: '0.25rem 0.5rem',
                                  borderRadius: '2px',
                                  border: `1px solid ${statusStyles.borderColor}`
                                }}>
                                  {iniciativa.estado}
                                </span>
                              )}
                            </div>
                            <div style={{
                              fontFamily: tokens.fonts.mono,
                              fontSize: '0.75rem',
                              color: tokens.colors.textMuted,
                              display: 'flex',
                              alignItems: 'center',
                              flexShrink: 0,
                              marginLeft: '1rem'
                            }}>
                              <Calendar style={{ height: '14px', width: '14px', marginRight: '0.25rem' }} />
                              {new Date(iniciativa.data_apresentacao || iniciativa.data).toLocaleDateString('pt-PT')}
                            </div>
                          </div>

                          {/* Title */}
                          <h4 style={{
                            fontFamily: tokens.fonts.headline,
                            fontWeight: '600',
                            color: tokens.colors.textPrimary,
                            marginBottom: '0.75rem',
                            fontSize: '1.125rem',
                            lineHeight: '1.4'
                          }}>
                            {iniciativa.titulo}
                          </h4>

                          {/* Details */}
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                              <div style={{
                                fontFamily: tokens.fonts.body,
                                fontSize: '0.875rem',
                                color: tokens.colors.textSecondary,
                                display: 'flex',
                                alignItems: 'center'
                              }}>
                                <FileText style={{ height: '16px', width: '16px', marginRight: '0.25rem' }} />
                                <span>Tipo: {iniciativa.tipo}</span>
                              </div>
                              {iniciativa.resultado && (
                                <div style={{
                                  fontFamily: tokens.fonts.body,
                                  fontSize: '0.875rem',
                                  color: tokens.colors.textSecondary,
                                  display: 'flex',
                                  alignItems: 'center'
                                }}>
                                  <Activity style={{ height: '16px', width: '16px', marginRight: '0.25rem' }} />
                                  <span>Resultado: {iniciativa.resultado}</span>
                                </div>
                              )}
                            </div>

                            {/* Action button */}
                            <button
                              onClick={() => toggleInitiativeDetails(index)}
                              style={{
                                fontFamily: tokens.fonts.body,
                                fontSize: '0.875rem',
                                fontWeight: '600',
                                color: tokens.colors.primary,
                                backgroundColor: 'transparent',
                                border: 'none',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                padding: '0.25rem 0.5rem',
                                borderRadius: '2px',
                                transition: 'background-color 0.2s ease'
                              }}
                            >
                              {expandedInitiatives.has(index) ? 'Ocultar detalhes' : 'Ver detalhes'}
                              <svg
                                style={{
                                  height: '16px',
                                  width: '16px',
                                  marginLeft: '0.25rem',
                                  transform: expandedInitiatives.has(index) ? 'rotate(90deg)' : 'none',
                                  transition: 'transform 0.2s ease'
                                }}
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
                            <div style={{
                              marginTop: '1rem',
                              paddingTop: '1rem',
                              borderTop: `1px solid ${tokens.colors.border}`
                            }}>
                              <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                fontFamily: tokens.fonts.mono,
                                fontSize: '0.75rem',
                                color: tokens.colors.textMuted
                              }}>
                                <div style={{
                                  flex: 1,
                                  backgroundColor: '#E5E7EB',
                                  borderRadius: '2px',
                                  height: '4px',
                                  marginRight: '0.75rem',
                                  overflow: 'hidden'
                                }}>
                                  <div style={{
                                    height: '100%',
                                    borderRadius: '2px',
                                    backgroundColor: getProgressColor(iniciativa.estado),
                                    width: getProgressWidth(iniciativa.estado),
                                    transition: 'width 0.3s ease'
                                  }} />
                                </div>
                                <span style={{
                                  fontSize: '0.75rem',
                                  fontWeight: '500',
                                  color: tokens.colors.textSecondary
                                }}>
                                  {iniciativa.estado || 'Em análise'}
                                </span>
                              </div>
                            </div>
                          )}

                          {/* Expandable Details Section */}
                          {expandedInitiatives.has(index) && (
                            <div style={{
                              marginTop: '1rem',
                              paddingTop: '1rem',
                              borderTop: `1px solid ${tokens.colors.border}`
                            }}>
                              <h5 style={{
                                fontFamily: tokens.fonts.headline,
                                fontWeight: '600',
                                color: tokens.colors.textPrimary,
                                marginBottom: '0.75rem',
                                fontSize: '0.9375rem'
                              }}>Detalhes da Iniciativa</h5>

                              <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                                gap: '1rem',
                                fontSize: '0.875rem'
                              }}>
                                {/* Left Column */}
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                  <div>
                                    <span style={{
                                      fontFamily: tokens.fonts.body,
                                      fontWeight: '600',
                                      color: tokens.colors.textSecondary,
                                      fontSize: '0.75rem',
                                      textTransform: 'uppercase',
                                      letterSpacing: '0.05em'
                                    }}>Tipo:</span>
                                    <p style={{
                                      fontFamily: tokens.fonts.body,
                                      color: tokens.colors.textPrimary,
                                      marginTop: '0.25rem'
                                    }}>
                                      {iniciativa.tipo_descricao} ({iniciativa.tipo})
                                    </p>
                                  </div>

                                  <div>
                                    <span style={{
                                      fontFamily: tokens.fonts.body,
                                      fontWeight: '600',
                                      color: tokens.colors.textSecondary,
                                      fontSize: '0.75rem',
                                      textTransform: 'uppercase',
                                      letterSpacing: '0.05em'
                                    }}>Data de Apresentação:</span>
                                    <p style={{
                                      fontFamily: tokens.fonts.body,
                                      color: tokens.colors.textPrimary,
                                      marginTop: '0.25rem'
                                    }}>
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
                                      <span style={{
                                        fontFamily: tokens.fonts.body,
                                        fontWeight: '600',
                                        color: tokens.colors.textSecondary,
                                        fontSize: '0.75rem',
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.05em'
                                      }}>Estado Atual:</span>
                                      <p style={{
                                        fontFamily: tokens.fonts.body,
                                        color: tokens.colors.textPrimary,
                                        marginTop: '0.25rem'
                                      }}>{iniciativa.estado}</p>
                                    </div>
                                  )}
                                </div>

                                {/* Right Column */}
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                  {iniciativa.resultado && (
                                    <div>
                                      <span style={{
                                        fontFamily: tokens.fonts.body,
                                        fontWeight: '600',
                                        color: tokens.colors.textSecondary,
                                        fontSize: '0.75rem',
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.05em'
                                      }}>Resultado:</span>
                                      <p style={{
                                        fontFamily: tokens.fonts.body,
                                        color: tokens.colors.textPrimary,
                                        marginTop: '0.25rem'
                                      }}>{iniciativa.resultado}</p>
                                    </div>
                                  )}

                                  <div>
                                    <span style={{
                                      fontFamily: tokens.fonts.body,
                                      fontWeight: '600',
                                      color: tokens.colors.textSecondary,
                                      fontSize: '0.75rem',
                                      textTransform: 'uppercase',
                                      letterSpacing: '0.05em'
                                    }}>Categoria:</span>
                                    <p style={{
                                      fontFamily: tokens.fonts.body,
                                      color: tokens.colors.textPrimary,
                                      marginTop: '0.25rem'
                                    }}>
                                      {iniciativa.tipo === 'J' ? 'Projeto de Lei' :
                                       iniciativa.tipo === 'R' ? 'Projeto de Resolução' :
                                       iniciativa.tipo === 'P' ? 'Proposta' :
                                       iniciativa.tipo === 'D' ? 'Decreto' :
                                       'Iniciativa Legislativa'}
                                    </p>
                                  </div>

                                  <div>
                                    <span style={{
                                      fontFamily: tokens.fonts.body,
                                      fontWeight: '600',
                                      color: tokens.colors.textSecondary,
                                      fontSize: '0.75rem',
                                      textTransform: 'uppercase',
                                      letterSpacing: '0.05em'
                                    }}>Status:</span>
                                    <p style={{
                                      fontFamily: tokens.fonts.body,
                                      color: tokens.colors.textPrimary,
                                      marginTop: '0.25rem'
                                    }}>
                                      {iniciativa.estado ?
                                        `Em fase: ${iniciativa.estado}` :
                                        'Em análise nas comissões competentes'
                                      }
                                    </p>
                                  </div>
                                </div>
                              </div>

                              {/* Full Title Section */}
                              <div style={{
                                marginTop: '1rem',
                                paddingTop: '1rem',
                                borderTop: `1px solid ${tokens.colors.border}`
                              }}>
                                <span style={{
                                  fontFamily: tokens.fonts.body,
                                  fontWeight: '600',
                                  color: tokens.colors.textSecondary,
                                  fontSize: '0.75rem',
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.05em'
                                }}>Título Completo:</span>
                                <p style={{
                                  fontFamily: tokens.fonts.body,
                                  color: tokens.colors.textSecondary,
                                  marginTop: '0.5rem',
                                  lineHeight: '1.6'
                                }}>
                                  {iniciativa.titulo}
                                </p>
                              </div>

                              {/* Additional Actions */}
                              <div style={{
                                marginTop: '1rem',
                                paddingTop: '1rem',
                                borderTop: `1px solid ${tokens.colors.border}`
                              }}>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                  <button
                                    onClick={() => {
                                      const url = iniciativa.urls?.documento ||
                                        `https://www.parlamento.pt/site/search/Pages/pesquisa.aspx?sq=${encodeURIComponent(iniciativa.titulo)}`;
                                      window.open(url, '_blank');
                                    }}
                                    style={{
                                      fontFamily: tokens.fonts.body,
                                      fontSize: '0.75rem',
                                      fontWeight: '500',
                                      backgroundColor: colorSchemes.blue.bg,
                                      color: colorSchemes.blue.text,
                                      padding: '0.375rem 0.75rem',
                                      borderRadius: '2px',
                                      border: `1px solid ${colorSchemes.blue.border}`,
                                      cursor: 'pointer',
                                      transition: 'background-color 0.2s ease'
                                    }}
                                  >
                                    Ver Documento
                                  </button>
                                  <button
                                    onClick={() => {
                                      const url = iniciativa.urls?.debates ||
                                        `https://www.parlamento.pt/ActividadeParlamentar/Paginas/DetalhePerguntaRequerimento.aspx?txt=${encodeURIComponent(iniciativa.titulo)}`;
                                      window.open(url, '_blank');
                                    }}
                                    style={{
                                      fontFamily: tokens.fonts.body,
                                      fontSize: '0.75rem',
                                      fontWeight: '500',
                                      backgroundColor: tokens.colors.bgPrimary,
                                      color: tokens.colors.textSecondary,
                                      padding: '0.375rem 0.75rem',
                                      borderRadius: '2px',
                                      border: `1px solid ${tokens.colors.border}`,
                                      cursor: 'pointer',
                                      transition: 'background-color 0.2s ease'
                                    }}
                                  >
                                    Histórico de Votações
                                  </button>
                                  <button
                                    onClick={() => {
                                      const url = iniciativa.urls?.oficial ||
                                        `https://www.parlamento.pt/ActividadeParlamentar/Paginas/Iniciativas.aspx?txt=${encodeURIComponent(iniciativa.titulo)}`;
                                      window.open(url, '_blank');
                                    }}
                                    style={{
                                      fontFamily: tokens.fonts.body,
                                      fontSize: '0.75rem',
                                      fontWeight: '500',
                                      backgroundColor: colorSchemes.green.bg,
                                      color: colorSchemes.green.text,
                                      padding: '0.375rem 0.75rem',
                                      borderRadius: '2px',
                                      border: `1px solid ${colorSchemes.green.border}`,
                                      cursor: 'pointer',
                                      transition: 'background-color 0.2s ease'
                                    }}
                                  >
                                    Link Oficial
                                  </button>
                                </div>
                                <p style={{
                                  fontFamily: tokens.fonts.body,
                                  fontSize: '0.75rem',
                                  color: tokens.colors.textMuted,
                                  marginTop: '0.5rem'
                                }}>
                                  {iniciativa.urls?.documento || iniciativa.urls?.debates || iniciativa.urls?.oficial ?
                                    'Links diretos para documentos oficiais do Parlamento' :
                                    'Links direcionam para pesquisa no site oficial do Parlamento'
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
                  <div style={{
                    textAlign: 'center',
                    padding: '3rem 1rem',
                    backgroundColor: tokens.colors.bgSecondary,
                    border: `1px solid ${tokens.colors.border}`,
                    borderRadius: '4px'
                  }}>
                    <div style={{
                      margin: '0 auto 1rem',
                      width: '4rem',
                      height: '4rem',
                      backgroundColor: tokens.colors.bgPrimary,
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: `1px solid ${tokens.colors.border}`
                    }}>
                      <FileText style={{ height: '2rem', width: '2rem', color: tokens.colors.textMuted }} />
                    </div>
                    <p style={{
                      fontFamily: tokens.fonts.headline,
                      color: tokens.colors.textSecondary,
                      fontSize: '1.125rem',
                      fontWeight: '500',
                      marginBottom: '0.5rem'
                    }}>
                      Nenhuma iniciativa registada
                    </p>
                    <p style={{
                      fontFamily: tokens.fonts.body,
                      fontSize: '0.875rem',
                      color: tokens.colors.textMuted
                    }}>
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
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                  <div>
                    <h3 style={{
                      fontFamily: tokens.fonts.headline,
                      fontSize: '1.25rem',
                      fontWeight: '600',
                      color: tokens.colors.textPrimary,
                      margin: 0
                    }}>
                      Conflitos de Interesse
                    </h3>
                    <p style={{
                      fontFamily: tokens.fonts.body,
                      fontSize: '0.875rem',
                      color: tokens.colors.textMuted,
                      marginTop: '0.25rem',
                      margin: '0.25rem 0 0 0'
                    }}>
                      Declaração de conflitos de interesse conforme exigido por lei
                    </p>
                  </div>
                </div>

                {conflitosInteresse ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    {/* Status Card */}
                    <div style={{
                      borderRadius: '4px',
                      border: `2px solid ${conflitosInteresse.has_conflict_potential ? '#FDE68A' : '#BBF7D0'}`,
                      padding: '1.5rem',
                      backgroundColor: conflitosInteresse.has_conflict_potential ? tokens.colors.warningBg : tokens.colors.successBg
                    }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                        <div style={{
                          flexShrink: 0,
                          width: '2.5rem',
                          height: '2.5rem',
                          borderRadius: '4px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          backgroundColor: conflitosInteresse.has_conflict_potential ? '#FEF3C7' : '#DCFCE7',
                          border: `1px solid ${conflitosInteresse.has_conflict_potential ? '#FDE68A' : '#BBF7D0'}`
                        }}>
                          {conflitosInteresse.has_conflict_potential ? (
                            <AlertTriangle style={{ height: '20px', width: '20px', color: tokens.colors.warning }} />
                          ) : (
                            <Shield style={{ height: '20px', width: '20px', color: tokens.colors.success }} />
                          )}
                        </div>
                        <div style={{ marginLeft: '1rem', flex: 1 }}>
                          <h4 style={{
                            fontFamily: tokens.fonts.headline,
                            fontSize: '1.125rem',
                            fontWeight: '600',
                            color: conflitosInteresse.has_conflict_potential ? '#92400E' : '#14532D',
                            margin: 0
                          }}>
                            {conflitosInteresse.exclusivity_description}
                          </h4>
                          <p style={{
                            fontFamily: tokens.fonts.body,
                            fontSize: '0.875rem',
                            marginTop: '0.25rem',
                            color: conflitosInteresse.has_conflict_potential ? '#B45309' : '#166534'
                          }}>
                            {conflitosInteresse.has_conflict_potential
                              ? 'Deputado exerce atividades não exclusivas que podem gerar conflitos de interesse'
                              : 'Deputado exerce mandato em regime de exclusividade'
                            }
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Personal Information */}
                    <div style={{
                      backgroundColor: tokens.colors.bgSecondary,
                      borderRadius: '4px',
                      border: `1px solid ${tokens.colors.border}`
                    }}>
                      <div style={{
                        padding: '1rem 1.5rem',
                        borderBottom: `1px solid ${tokens.colors.border}`
                      }}>
                        <h4 style={{
                          fontFamily: tokens.fonts.headline,
                          fontSize: '1rem',
                          fontWeight: '600',
                          color: tokens.colors.textPrimary,
                          display: 'flex',
                          alignItems: 'center',
                          margin: 0
                        }}>
                          <User style={{ height: '20px', width: '20px', color: tokens.colors.primary, marginRight: '0.5rem' }} />
                          Informações Pessoais
                        </h4>
                      </div>
                      <div style={{ padding: '1rem 1.5rem' }}>
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                          gap: '1.5rem'
                        }}>
                          <div>
                            <label style={{
                              fontFamily: tokens.fonts.body,
                              fontSize: '0.75rem',
                              fontWeight: '600',
                              color: tokens.colors.textSecondary,
                              textTransform: 'uppercase',
                              letterSpacing: '0.05em'
                            }}>
                              Nome Completo
                            </label>
                            <p style={{
                              fontFamily: tokens.fonts.body,
                              color: tokens.colors.textPrimary,
                              fontWeight: '500',
                              marginTop: '0.25rem'
                            }}>
                              {conflitosInteresse.full_name}
                            </p>
                          </div>

                          {conflitosInteresse.dgf_number && (
                            <div>
                              <label style={{
                                fontFamily: tokens.fonts.body,
                                fontSize: '0.75rem',
                                fontWeight: '600',
                                color: tokens.colors.textSecondary,
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em'
                              }}>
                                Número DGF
                              </label>
                              <p style={{
                                fontFamily: tokens.fonts.mono,
                                color: tokens.colors.textPrimary,
                                marginTop: '0.25rem'
                              }}>
                                {conflitosInteresse.dgf_number}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Marital Status and Regime */}
                    {(conflitosInteresse.marital_status || conflitosInteresse.matrimonial_regime || conflitosInteresse.spouse_name) && (
                      <div style={{
                        backgroundColor: tokens.colors.bgSecondary,
                        borderRadius: '4px',
                        border: `1px solid ${tokens.colors.border}`
                      }}>
                        <div style={{
                          padding: '1rem 1.5rem',
                          borderBottom: `1px solid ${tokens.colors.border}`
                        }}>
                          <h4 style={{
                            fontFamily: tokens.fonts.headline,
                            fontSize: '1rem',
                            fontWeight: '600',
                            color: tokens.colors.textPrimary,
                            display: 'flex',
                            alignItems: 'center',
                            margin: 0
                          }}>
                            <Heart style={{ height: '20px', width: '20px', color: tokens.colors.accent, marginRight: '0.5rem' }} />
                            Estado Civil e Regime Matrimonial
                          </h4>
                        </div>
                        <div style={{ padding: '1rem 1.5rem' }}>
                          <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                            gap: '1.5rem'
                          }}>
                            {conflitosInteresse.marital_status && (
                              <div>
                                <label style={{
                                  fontFamily: tokens.fonts.body,
                                  fontSize: '0.75rem',
                                  fontWeight: '600',
                                  color: tokens.colors.textSecondary,
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.05em'
                                }}>
                                  Estado Civil
                                </label>
                                <p style={{
                                  fontFamily: tokens.fonts.body,
                                  color: tokens.colors.textPrimary,
                                  marginTop: '0.25rem'
                                }}>
                                  {conflitosInteresse.marital_status}
                                </p>
                              </div>
                            )}

                            {conflitosInteresse.matrimonial_regime && (
                              <div>
                                <label style={{
                                  fontFamily: tokens.fonts.body,
                                  fontSize: '0.75rem',
                                  fontWeight: '600',
                                  color: tokens.colors.textSecondary,
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.05em'
                                }}>
                                  Regime Matrimonial
                                </label>
                                <p style={{
                                  fontFamily: tokens.fonts.body,
                                  color: tokens.colors.textPrimary,
                                  marginTop: '0.25rem'
                                }}>
                                  {conflitosInteresse.matrimonial_regime}
                                </p>
                              </div>
                            )}

                            {conflitosInteresse.spouse_name && (
                              <div>
                                <label style={{
                                  fontFamily: tokens.fonts.body,
                                  fontSize: '0.75rem',
                                  fontWeight: '600',
                                  color: tokens.colors.textSecondary,
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.05em'
                                }}>
                                  Nome do Cônjuge
                                </label>
                                <div style={{ marginTop: '0.25rem' }}>
                                  {conflitosInteresse.spouse_deputy ? (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                      <Link
                                        to={getDeputadoUrl(conflitosInteresse.spouse_deputy.cad_id || conflitosInteresse.spouse_deputy.id)}
                                        style={{
                                          fontFamily: tokens.fonts.body,
                                          color: tokens.colors.primary,
                                          fontWeight: '500',
                                          textDecoration: 'none'
                                        }}
                                      >
                                        {conflitosInteresse.spouse_name}
                                      </Link>
                                      <span style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        padding: '0.25rem 0.5rem',
                                        borderRadius: '2px',
                                        fontSize: '0.75rem',
                                        fontWeight: '500',
                                        backgroundColor: colorSchemes.blue.bg,
                                        color: colorSchemes.blue.text,
                                        border: `1px solid ${colorSchemes.blue.border}`,
                                        width: 'fit-content'
                                      }}>
                                        <Users style={{ height: '12px', width: '12px', marginRight: '0.25rem' }} />
                                        Também Deputado/a ({conflitosInteresse.spouse_deputy.partido_sigla})
                                      </span>
                                    </div>
                                  ) : (
                                    <p style={{
                                      fontFamily: tokens.fonts.body,
                                      color: tokens.colors.textPrimary,
                                      fontWeight: '500'
                                    }}>
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
                    <div style={{
                      backgroundColor: tokens.colors.infoBg,
                      border: `1px solid #BFDBFE`,
                      borderRadius: '4px',
                      padding: '1rem'
                    }}>
                      <div style={{ display: 'flex' }}>
                        <Shield style={{ height: '20px', width: '20px', color: tokens.colors.info, marginTop: '2px', flexShrink: 0 }} />
                        <div style={{ marginLeft: '0.75rem' }}>
                          <h5 style={{
                            fontFamily: tokens.fonts.headline,
                            fontSize: '0.875rem',
                            fontWeight: '600',
                            color: '#1E3A8A',
                            margin: 0
                          }}>
                            Transparência e Integridade
                          </h5>
                          <p style={{
                            fontFamily: tokens.fonts.body,
                            fontSize: '0.875rem',
                            color: tokens.colors.info,
                            marginTop: '0.25rem'
                          }}>
                            Esta informação é disponibilizada em cumprimento das obrigações de transparência
                            dos deputados, conforme estabelecido na legislação parlamentar portuguesa.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{
                    textAlign: 'center',
                    padding: '3rem 1rem',
                    backgroundColor: tokens.colors.bgSecondary,
                    border: `1px solid ${tokens.colors.border}`,
                    borderRadius: '4px'
                  }}>
                    <div style={{
                      margin: '0 auto 1rem',
                      width: '4rem',
                      height: '4rem',
                      backgroundColor: tokens.colors.bgPrimary,
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: `1px solid ${tokens.colors.border}`
                    }}>
                      <Shield style={{ height: '2rem', width: '2rem', color: tokens.colors.textMuted }} />
                    </div>
                    <p style={{
                      fontFamily: tokens.fonts.headline,
                      color: tokens.colors.textSecondary,
                      fontSize: '1.125rem',
                      fontWeight: '500',
                      marginBottom: '0.5rem'
                    }}>
                      Dados de conflitos de interesse não disponíveis
                    </p>
                    <p style={{
                      fontFamily: tokens.fonts.body,
                      fontSize: '0.875rem',
                      color: tokens.colors.textMuted
                    }}>
                      As informações sobre conflitos de interesse não foram encontradas para este deputado
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'attendance' && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                  <h3 style={{
                    fontFamily: tokens.fonts.headline,
                    fontSize: '1.25rem',
                    fontWeight: '600',
                    color: tokens.colors.textPrimary,
                    margin: 0
                  }}>
                    Registo de Presenças
                  </h3>
                </div>

                {attendanceData ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    {/* Summary Cards */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                      gap: '1rem',
                      marginBottom: '1.5rem'
                    }}>
                      <div style={{
                        backgroundColor: tokens.colors.bgSecondary,
                        borderRadius: '4px',
                        border: `1px solid ${tokens.colors.border}`,
                        padding: '1rem'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          <div style={{
                            padding: '0.5rem',
                            backgroundColor: colorSchemes.blue.bg,
                            borderRadius: '4px',
                            border: `1px solid ${colorSchemes.blue.border}`
                          }}>
                            <Activity style={{ height: '20px', width: '20px', color: colorSchemes.blue.primary }} />
                          </div>
                          <div style={{ marginLeft: '0.75rem' }}>
                            <p style={{
                              fontFamily: tokens.fonts.body,
                              fontSize: '0.875rem',
                              fontWeight: '500',
                              color: tokens.colors.textSecondary,
                              margin: 0
                            }}>Total Sessões</p>
                            <p style={{
                              fontFamily: tokens.fonts.mono,
                              fontSize: '1.5rem',
                              fontWeight: '700',
                              color: tokens.colors.textPrimary,
                              margin: 0
                            }}>{attendanceData.summary.total_sessions}</p>
                          </div>
                        </div>
                      </div>

                      <div style={{
                        backgroundColor: tokens.colors.bgSecondary,
                        borderRadius: '4px',
                        border: `1px solid ${tokens.colors.border}`,
                        padding: '1rem'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          <div style={{
                            padding: '0.5rem',
                            backgroundColor: colorSchemes.green.bg,
                            borderRadius: '4px',
                            border: `1px solid ${colorSchemes.green.border}`
                          }}>
                            <Activity style={{ height: '20px', width: '20px', color: colorSchemes.green.primary }} />
                          </div>
                          <div style={{ marginLeft: '0.75rem' }}>
                            <p style={{
                              fontFamily: tokens.fonts.body,
                              fontSize: '0.875rem',
                              fontWeight: '500',
                              color: tokens.colors.textSecondary,
                              margin: 0
                            }}>Presente</p>
                            <p style={{
                              fontFamily: tokens.fonts.mono,
                              fontSize: '1.5rem',
                              fontWeight: '700',
                              color: tokens.colors.success,
                              margin: 0
                            }}>{attendanceData.summary.present}</p>
                          </div>
                        </div>
                      </div>

                      <div style={{
                        backgroundColor: tokens.colors.bgSecondary,
                        borderRadius: '4px',
                        border: `1px solid ${tokens.colors.border}`,
                        padding: '1rem'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          <div style={{
                            padding: '0.5rem',
                            backgroundColor: colorSchemes.orange.bg,
                            borderRadius: '4px',
                            border: `1px solid ${colorSchemes.orange.border}`
                          }}>
                            <Activity style={{ height: '20px', width: '20px', color: colorSchemes.orange.primary }} />
                          </div>
                          <div style={{ marginLeft: '0.75rem' }}>
                            <p style={{
                              fontFamily: tokens.fonts.body,
                              fontSize: '0.875rem',
                              fontWeight: '500',
                              color: tokens.colors.textSecondary,
                              margin: 0
                            }}>Falta Justificada</p>
                            <p style={{
                              fontFamily: tokens.fonts.mono,
                              fontSize: '1.5rem',
                              fontWeight: '700',
                              color: tokens.colors.warning,
                              margin: 0
                            }}>{attendanceData.summary.justified_absence}</p>
                          </div>
                        </div>
                      </div>

                      <div style={{
                        backgroundColor: tokens.colors.bgSecondary,
                        borderRadius: '4px',
                        border: `1px solid ${tokens.colors.border}`,
                        padding: '1rem'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          <div style={{
                            padding: '0.5rem',
                            backgroundColor: tokens.colors.dangerBg,
                            borderRadius: '4px',
                            border: `1px solid #FECACA`
                          }}>
                            <Activity style={{ height: '20px', width: '20px', color: tokens.colors.danger }} />
                          </div>
                          <div style={{ marginLeft: '0.75rem' }}>
                            <p style={{
                              fontFamily: tokens.fonts.body,
                              fontSize: '0.875rem',
                              fontWeight: '500',
                              color: tokens.colors.textSecondary,
                              margin: 0
                            }}>Falta Injustificada</p>
                            <p style={{
                              fontFamily: tokens.fonts.mono,
                              fontSize: '1.5rem',
                              fontWeight: '700',
                              color: tokens.colors.danger,
                              margin: 0
                            }}>{attendanceData.summary.unjustified_absence}</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Timeline */}
                    <div style={{
                      backgroundColor: tokens.colors.bgSecondary,
                      borderRadius: '4px',
                      border: `1px solid ${tokens.colors.border}`
                    }}>
                      <div style={{
                        padding: '1rem 1.5rem',
                        borderBottom: `1px solid ${tokens.colors.border}`
                      }}>
                        <h4 style={{
                          fontFamily: tokens.fonts.headline,
                          fontSize: '1rem',
                          fontWeight: '600',
                          color: tokens.colors.textPrimary,
                          margin: 0
                        }}>Timeline de Presenças</h4>
                      </div>
                      <div style={{ padding: '1.5rem' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                          {attendanceData.timeline.map((entry, index) => {
                            const getStatusColor = (status) => {
                              switch (status) {
                                case 'success': return tokens.colors.success;
                                case 'warning': return '#F59E0B';
                                case 'danger': return tokens.colors.danger;
                                case 'info': return tokens.colors.blue;
                                default: return tokens.colors.textMuted;
                              }
                            };

                            const getStatusBg = (status) => {
                              switch (status) {
                                case 'success': return { bg: colorSchemes.green.bg, text: colorSchemes.green.text, border: colorSchemes.green.border };
                                case 'warning': return { bg: colorSchemes.orange.bg, text: colorSchemes.orange.text, border: colorSchemes.orange.border };
                                case 'danger': return { bg: tokens.colors.dangerBg, text: tokens.colors.danger, border: '#FECACA' };
                                case 'info': return { bg: colorSchemes.blue.bg, text: colorSchemes.blue.text, border: colorSchemes.blue.border };
                                default: return { bg: '#F3F4F6', text: tokens.colors.textSecondary, border: tokens.colors.border };
                              }
                            };

                            const statusStyles = getStatusBg(entry.status);

                            return (
                              <div
                                key={index}
                                style={{
                                  display: 'flex',
                                  alignItems: 'flex-start',
                                  gap: '1rem',
                                  padding: '1rem',
                                  borderRadius: '4px',
                                  border: `1px solid ${tokens.colors.border}`,
                                  backgroundColor: tokens.colors.bgPrimary
                                }}
                              >
                                <div style={{
                                  flexShrink: 0,
                                  width: '12px',
                                  height: '12px',
                                  borderRadius: '2px',
                                  marginTop: '6px',
                                  backgroundColor: getStatusColor(entry.status)
                                }}></div>

                                <div style={{ flex: 1 }}>
                                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                      <span style={{
                                        fontFamily: tokens.fonts.mono,
                                        fontSize: '0.875rem',
                                        fontWeight: '500',
                                        color: tokens.colors.textPrimary
                                      }}>
                                        {new Date(entry.date).toLocaleDateString('pt-PT')}
                                      </span>
                                      <span style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        padding: '0.25rem 0.5rem',
                                        borderRadius: '2px',
                                        fontSize: '0.75rem',
                                        fontWeight: '500',
                                        backgroundColor: statusStyles.bg,
                                        color: statusStyles.text,
                                        border: `1px solid ${statusStyles.border}`
                                      }}>
                                        {entry.attendance_description}
                                      </span>
                                    </div>
                                    <span style={{
                                      fontFamily: tokens.fonts.body,
                                      fontSize: '0.75rem',
                                      color: tokens.colors.textMuted
                                    }}>
                                      {entry.session_type}
                                    </span>
                                  </div>

                                  {entry.reason && (
                                    <p style={{
                                      fontFamily: tokens.fonts.body,
                                      fontSize: '0.875rem',
                                      color: tokens.colors.textSecondary,
                                      marginTop: '0.5rem'
                                    }}>
                                      <span style={{ fontWeight: '600' }}>Motivo:</span> {entry.reason}
                                    </p>
                                  )}

                                  {entry.justification && (
                                    <p style={{
                                      fontFamily: tokens.fonts.body,
                                      fontSize: '0.875rem',
                                      color: tokens.colors.textSecondary,
                                      marginTop: '0.25rem'
                                    }}>
                                      <span style={{ fontWeight: '600' }}>Justificação:</span> {entry.justification}
                                    </p>
                                  )}

                                  {entry.observations && (
                                    <p style={{
                                      fontFamily: tokens.fonts.body,
                                      fontSize: '0.875rem',
                                      color: tokens.colors.textSecondary,
                                      marginTop: '0.25rem'
                                    }}>
                                      <span style={{ fontWeight: '600' }}>Observações:</span> {entry.observations}
                                    </p>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>

                        {attendanceData.timeline.length === 0 && (
                          <div style={{ textAlign: 'center', padding: '2rem' }}>
                            <Activity style={{ height: '3rem', width: '3rem', color: tokens.colors.textMuted, margin: '0 auto 0.75rem' }} />
                            <p style={{
                              fontFamily: tokens.fonts.body,
                              color: tokens.colors.textMuted
                            }}>Nenhum registo de presença encontrado</p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Legend */}
                    <div style={{
                      backgroundColor: tokens.colors.bgSecondary,
                      borderRadius: '4px',
                      border: `1px solid ${tokens.colors.border}`,
                      padding: '1.5rem'
                    }}>
                      <h4 style={{
                        fontFamily: tokens.fonts.headline,
                        fontSize: '1rem',
                        fontWeight: '600',
                        color: tokens.colors.textPrimary,
                        marginBottom: '1rem'
                      }}>Legenda dos Códigos</h4>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                        gap: '0.75rem'
                      }}>
                        {Object.entries(attendanceData.codes_legend).map(([code, info]) => {
                          const getCodeStyles = (status) => {
                            switch (status) {
                              case 'success': return { bg: colorSchemes.green.bg, text: colorSchemes.green.text, border: colorSchemes.green.border };
                              case 'warning': return { bg: colorSchemes.orange.bg, text: colorSchemes.orange.text, border: colorSchemes.orange.border };
                              case 'danger': return { bg: tokens.colors.dangerBg, text: tokens.colors.danger, border: '#FECACA' };
                              case 'info': return { bg: colorSchemes.blue.bg, text: colorSchemes.blue.text, border: colorSchemes.blue.border };
                              default: return { bg: '#F3F4F6', text: tokens.colors.textSecondary, border: tokens.colors.border };
                            }
                          };
                          const codeStyles = getCodeStyles(info.status);

                          return (
                            <div key={code} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                padding: '0.25rem 0.5rem',
                                borderRadius: '2px',
                                fontSize: '0.75rem',
                                fontFamily: tokens.fonts.mono,
                                fontWeight: '600',
                                backgroundColor: codeStyles.bg,
                                color: codeStyles.text,
                                border: `1px solid ${codeStyles.border}`
                              }}>
                                {code}
                              </span>
                              <span style={{
                                fontFamily: tokens.fonts.body,
                                fontSize: '0.875rem',
                                color: tokens.colors.textSecondary
                              }}>{info.description}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{
                    textAlign: 'center',
                    padding: '3rem 1rem',
                    backgroundColor: tokens.colors.bgSecondary,
                    border: `1px solid ${tokens.colors.border}`,
                    borderRadius: '4px'
                  }}>
                    <Activity style={{ height: '3rem', width: '3rem', color: tokens.colors.textMuted, margin: '0 auto 0.75rem' }} />
                    <p style={{
                      fontFamily: tokens.fonts.body,
                      color: tokens.colors.textMuted
                    }}>Dados de presença não disponíveis</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'mandatos-anteriores' && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                  <h3 style={{
                    fontFamily: tokens.fonts.headline,
                    fontSize: '1.25rem',
                    fontWeight: '600',
                    color: tokens.colors.textPrimary,
                    margin: 0
                  }}>
                    Mandatos Anteriores
                  </h3>
                </div>

                {deputado.mandatos_historico && deputado.mandatos_historico.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {deputado.mandatos_historico.map((mandato, index) => (
                      <div
                        key={index}
                        style={{
                          backgroundColor: mandato.is_current ? '#E8F5E9' : tokens.colors.bgSecondary,
                          borderRadius: '4px',
                          border: mandato.is_current ? `2px solid ${tokens.colors.primary}` : `1px solid ${tokens.colors.border}`,
                          padding: '1.5rem',
                          transition: 'border-color 0.2s ease'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                              <h4 style={{
                                fontFamily: tokens.fonts.headline,
                                fontSize: '1.125rem',
                                fontWeight: '600',
                                color: tokens.colors.textPrimary,
                                margin: 0
                              }}>
                                {mandato.legislatura_nome}
                              </h4>
                              {mandato.is_current && (
                                <span style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  padding: '0.25rem 0.5rem',
                                  borderRadius: '2px',
                                  fontSize: '0.75rem',
                                  fontWeight: '600',
                                  backgroundColor: tokens.colors.primary,
                                  color: '#FFFFFF',
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.025em'
                                }}>
                                  Atual
                                </span>
                              )}
                            </div>

                            <div style={{
                              display: 'grid',
                              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                              gap: '1rem',
                              marginBottom: '1rem'
                            }}>
                              <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                fontFamily: tokens.fonts.mono,
                                fontSize: '0.875rem',
                                color: tokens.colors.textSecondary
                              }}>
                                <Calendar style={{ height: '16px', width: '16px', marginRight: '0.5rem' }} />
                                <span>
                                  {new Date(mandato.mandato_inicio).toLocaleDateString('pt-PT')} - {' '}
                                  {mandato.mandato_fim
                                    ? new Date(mandato.mandato_fim).toLocaleDateString('pt-PT')
                                    : 'Presente'
                                  }
                                </span>
                              </div>

                              <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                fontFamily: tokens.fonts.body,
                                fontSize: '0.875rem',
                                color: tokens.colors.textSecondary
                              }}>
                                <MapPin style={{ height: '16px', width: '16px', marginRight: '0.5rem' }} />
                                <span>{mandato.circulo}</span>
                              </div>

                              <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                fontFamily: tokens.fonts.body,
                                fontSize: '0.875rem',
                                color: tokens.colors.textSecondary
                              }}>
                                <Briefcase style={{ height: '16px', width: '16px', marginRight: '0.5rem' }} />
                                <span>{mandato.partido_sigla}</span>
                              </div>
                            </div>
                          </div>

                          {mandato.is_current && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                              <span style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                padding: '0.5rem 0.75rem',
                                borderRadius: '4px',
                                fontSize: '0.875rem',
                                fontWeight: '500',
                                backgroundColor: colorSchemes.green.bg,
                                color: colorSchemes.green.text,
                                border: `1px solid ${colorSchemes.green.border}`
                              }}>
                                <Calendar style={{ height: '16px', width: '16px', marginRight: '0.5rem' }} />
                                Legislatura Atual
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{
                    textAlign: 'center',
                    padding: '3rem 1rem',
                    backgroundColor: tokens.colors.bgSecondary,
                    border: `1px solid ${tokens.colors.border}`,
                    borderRadius: '4px'
                  }}>
                    <div style={{
                      margin: '0 auto 1rem',
                      width: '4rem',
                      height: '4rem',
                      backgroundColor: tokens.colors.bgPrimary,
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: `1px solid ${tokens.colors.border}`
                    }}>
                      <Calendar style={{ height: '2rem', width: '2rem', color: tokens.colors.textMuted }} />
                    </div>
                    <p style={{
                      fontFamily: tokens.fonts.headline,
                      color: tokens.colors.textSecondary,
                      fontSize: '1.125rem',
                      fontWeight: '500',
                      marginBottom: '0.5rem'
                    }}>
                      Apenas um mandato registrado
                    </p>
                    <p style={{
                      fontFamily: tokens.fonts.body,
                      fontSize: '0.875rem',
                      color: tokens.colors.textMuted
                    }}>
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

