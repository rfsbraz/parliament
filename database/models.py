"""
SQLAlchemy Models for Portuguese Parliament Database
===================================================

Comprehensive models for all parliamentary data with zero data loss.
Supports both SQLite (development) and Aurora MySQL/PostgreSQL (production).

Author: Claude
Version: 2.0 - Full Mapping Implementation
"""

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, Index, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


# =====================================================
# MAIN ENTITIES
# =====================================================

class Legislatura(Base):
    __tablename__ = 'legislaturas'
    
    id = Column(Integer, primary_key=True)
    numero = Column(String(20), unique=True, nullable=False)
    designacao = Column(String(100), nullable=False)
    data_inicio = Column(Date)
    data_fim = Column(Date)
    ativa = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Partido(Base):
    __tablename__ = 'partidos'
    
    id = Column(Integer, primary_key=True)
    sigla = Column(String(10), unique=True, nullable=False)
    nome = Column(String(200), nullable=False)
    designacao_completa = Column(Text)
    cor_hex = Column(String(7))
    ativo = Column(Boolean, default=True)
    data_fundacao = Column(Date)
    ideologia = Column(String(100))
    lider_parlamentar = Column(String(200))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CirculoEleitoral(Base):
    __tablename__ = 'circulos_eleitorais'
    
    id = Column(Integer, primary_key=True)
    designacao = Column(String(100), unique=True, nullable=False)
    codigo = Column(String(10))
    regiao = Column(String(50))
    distrito = Column(String(50))
    num_deputados = Column(Integer, default=0)
    populacao = Column(Integer)
    area_km2 = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Deputado(Base):
    __tablename__ = 'deputados'
    
    id = Column(Integer, primary_key=True)
    id_cadastro = Column(Integer, unique=True, nullable=False)
    nome = Column(String(200), nullable=False)
    nome_completo = Column(String(300))
    profissao = Column(String(200))
    data_nascimento = Column(Date)
    naturalidade = Column(String(100))
    habilitacoes_academicas = Column(Text)
    biografia = Column(Text)
    foto_url = Column(String(500))
    email = Column(String(100))
    telefone = Column(String(20))
    gabinete = Column(String(50))
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# =====================================================
# COMPREHENSIVE DEPUTY ACTIVITIES - ZERO DATA LOSS
# =====================================================

class DeputyActivity(Base):
    __tablename__ = 'deputy_activities'
    
    id = Column(Integer, primary_key=True)
    id_cadastro = Column(Integer, nullable=False)
    legislatura_sigla = Column(String(20), nullable=False)
    nome_deputado = Column(String(200))
    partido_gp = Column(String(10))
    xml_file_path = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    initiatives = relationship("DeputyInitiative", back_populates="deputy_activity", cascade="all, delete-orphan")
    interventions = relationship("DeputyIntervention", back_populates="deputy_activity", cascade="all, delete-orphan")
    reports = relationship("DeputyReport", back_populates="deputy_activity", cascade="all, delete-orphan")
    parliamentary_activities = relationship("DeputyParliamentaryActivity", back_populates="deputy_activity", cascade="all, delete-orphan")
    legislative_data = relationship("DeputyLegislativeData", back_populates="deputy_activity", cascade="all, delete-orphan")
    gp_situations = relationship("DeputyGPSituation", back_populates="deputy_activity", cascade="all, delete-orphan")
    situations = relationship("DeputySituation", back_populates="deputy_activity", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_deputy_activities_cadastro_leg', 'id_cadastro', 'legislatura_sigla'),
    )


# =====================================================
# INITIATIVES
# =====================================================

class DeputyInitiative(Base):
    __tablename__ = 'deputy_initiatives'
    
    id = Column(Integer, primary_key=True)
    deputy_activity_id = Column(Integer, ForeignKey('deputy_activities.id'), nullable=False)
    id_iniciativa = Column(Integer)
    numero = Column(String(50))
    tipo = Column(String(50))
    desc_tipo = Column(String(200))
    assunto = Column(Text)
    legislatura = Column(String(20))
    sessao = Column(String(20))
    data_entrada = Column(Date)
    data_agendamento_debate = Column(Date)
    orgao_exterior = Column(String(200))
    observacoes = Column(Text)
    tipo_autor = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputy_activity = relationship("DeputyActivity", back_populates="initiatives")
    votes = relationship("DeputyInitiativeVote", back_populates="initiative", cascade="all, delete-orphan")
    author_groups = relationship("DeputyInitiativeAuthorGroup", back_populates="initiative", cascade="all, delete-orphan")
    author_elected = relationship("DeputyInitiativeAuthorElected", back_populates="initiative", cascade="all, delete-orphan")
    guests = relationship("DeputyInitiativeGuest", back_populates="initiative", cascade="all, delete-orphan")
    publications = relationship("DeputyInitiativePublication", back_populates="initiative", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_deputy_initiatives_activity', 'deputy_activity_id'),
        Index('idx_deputy_initiatives_data_entrada', 'data_entrada'),
    )


class DeputyInitiativeVote(Base):
    __tablename__ = 'deputy_initiative_votes'
    
    id = Column(Integer, primary_key=True)
    initiative_id = Column(Integer, ForeignKey('deputy_initiatives.id'), nullable=False)
    id_votacao = Column(String(50))
    resultado = Column(String(50))
    reuniao = Column(String(100))
    unanime = Column(String(10))
    data_votacao = Column(Date)
    descricao = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    initiative = relationship("DeputyInitiative", back_populates="votes")


class DeputyInitiativeAuthorGroup(Base):
    __tablename__ = 'deputy_initiative_author_groups'
    
    id = Column(Integer, primary_key=True)
    initiative_id = Column(Integer, ForeignKey('deputy_initiatives.id'), nullable=False)
    nome = Column(String(200))
    cargo = Column(String(100))
    pais = Column(String(50))
    honra = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    initiative = relationship("DeputyInitiative", back_populates="author_groups")


class DeputyInitiativeAuthorElected(Base):
    __tablename__ = 'deputy_initiative_author_elected'
    
    id = Column(Integer, primary_key=True)
    initiative_id = Column(Integer, ForeignKey('deputy_initiatives.id'), nullable=False)
    nome = Column(String(200))
    cargo = Column(String(100))
    pais = Column(String(50))
    honra = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    initiative = relationship("DeputyInitiative", back_populates="author_elected")


class DeputyInitiativeGuest(Base):
    __tablename__ = 'deputy_initiative_guests'
    
    id = Column(Integer, primary_key=True)
    initiative_id = Column(Integer, ForeignKey('deputy_initiatives.id'), nullable=False)
    nome = Column(String(200))
    cargo = Column(String(100))
    pais = Column(String(50))
    honra = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    initiative = relationship("DeputyInitiative", back_populates="guests")


class DeputyInitiativePublication(Base):
    __tablename__ = 'deputy_initiative_publications'
    
    id = Column(Integer, primary_key=True)
    initiative_id = Column(Integer, ForeignKey('deputy_initiatives.id'), nullable=False)
    pub_nr = Column(String(50))
    pub_tipo = Column(String(50))
    pub_data = Column(Date)
    url_diario = Column(String(500))
    legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    initiative = relationship("DeputyInitiative", back_populates="publications")


# =====================================================
# INTERVENTIONS
# =====================================================

class DeputyIntervention(Base):
    __tablename__ = 'deputy_interventions'
    
    id = Column(Integer, primary_key=True)
    deputy_activity_id = Column(Integer, ForeignKey('deputy_activities.id'), nullable=False)
    id_intervencao = Column(Integer)
    tipo = Column(String(50))
    data_intervencao = Column(Date)
    qualidade = Column(String(100))
    sumario = Column(Text)
    resumo = Column(Text)
    fase_sessao = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputy_activity = relationship("DeputyActivity", back_populates="interventions")
    
    __table_args__ = (
        Index('idx_deputy_interventions_activity', 'deputy_activity_id'),
        Index('idx_deputy_interventions_data', 'data_intervencao'),
    )


# =====================================================
# REPORTS (same structure as initiatives)
# =====================================================

class DeputyReport(Base):
    __tablename__ = 'deputy_reports'
    
    id = Column(Integer, primary_key=True)
    deputy_activity_id = Column(Integer, ForeignKey('deputy_activities.id'), nullable=False)
    id_relatorio = Column(Integer)
    numero = Column(String(50))
    tipo = Column(String(50))
    desc_tipo = Column(String(200))
    assunto = Column(Text)
    legislatura = Column(String(20))
    sessao = Column(String(20))
    data_entrada = Column(Date)
    data_agendamento_debate = Column(Date)
    orgao_exterior = Column(String(200))
    observacoes = Column(Text)
    tipo_autor = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputy_activity = relationship("DeputyActivity", back_populates="reports")
    votes = relationship("DeputyReportVote", back_populates="report", cascade="all, delete-orphan")
    author_groups = relationship("DeputyReportAuthorGroup", back_populates="report", cascade="all, delete-orphan")
    author_elected = relationship("DeputyReportAuthorElected", back_populates="report", cascade="all, delete-orphan")
    guests = relationship("DeputyReportGuest", back_populates="report", cascade="all, delete-orphan")
    publications = relationship("DeputyReportPublication", back_populates="report", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_deputy_reports_activity', 'deputy_activity_id'),
        Index('idx_deputy_reports_data_entrada', 'data_entrada'),
    )


# Report supporting tables (same pattern as initiatives)
class DeputyReportVote(Base):
    __tablename__ = 'deputy_report_votes'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('deputy_reports.id'), nullable=False)
    id_votacao = Column(String(50))
    resultado = Column(String(50))
    reuniao = Column(String(100))
    unanime = Column(String(10))
    data_votacao = Column(Date)
    descricao = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    report = relationship("DeputyReport", back_populates="votes")


class DeputyReportAuthorGroup(Base):
    __tablename__ = 'deputy_report_author_groups'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('deputy_reports.id'), nullable=False)
    nome = Column(String(200))
    cargo = Column(String(100))
    pais = Column(String(50))
    honra = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    report = relationship("DeputyReport", back_populates="author_groups")


class DeputyReportAuthorElected(Base):
    __tablename__ = 'deputy_report_author_elected'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('deputy_reports.id'), nullable=False)
    nome = Column(String(200))
    cargo = Column(String(100))
    pais = Column(String(50))
    honra = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    report = relationship("DeputyReport", back_populates="author_elected")


class DeputyReportGuest(Base):
    __tablename__ = 'deputy_report_guests'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('deputy_reports.id'), nullable=False)
    nome = Column(String(200))
    cargo = Column(String(100))
    pais = Column(String(50))
    honra = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    report = relationship("DeputyReport", back_populates="guests")


class DeputyReportPublication(Base):
    __tablename__ = 'deputy_report_publications'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('deputy_reports.id'), nullable=False)
    pub_nr = Column(String(50))
    pub_tipo = Column(String(50))
    pub_data = Column(Date)
    url_diario = Column(String(500))
    legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    report = relationship("DeputyReport", back_populates="publications")


# =====================================================
# PARLIAMENTARY ACTIVITIES (same structure as initiatives)
# =====================================================

class DeputyParliamentaryActivity(Base):
    __tablename__ = 'deputy_parliamentary_activities'
    
    id = Column(Integer, primary_key=True)
    deputy_activity_id = Column(Integer, ForeignKey('deputy_activities.id'), nullable=False)
    id_atividade = Column(Integer)
    numero = Column(String(50))
    tipo = Column(String(50))
    desc_tipo = Column(String(200))
    assunto = Column(Text)
    legislatura = Column(String(20))
    sessao = Column(String(20))
    data_entrada = Column(Date)
    data_agendamento_debate = Column(Date)
    orgao_exterior = Column(String(200))
    observacoes = Column(Text)
    tipo_autor = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputy_activity = relationship("DeputyActivity", back_populates="parliamentary_activities")
    votes = relationship("DeputyParliamentaryActivityVote", back_populates="activity", cascade="all, delete-orphan")
    author_groups = relationship("DeputyParliamentaryActivityAuthorGroup", back_populates="activity", cascade="all, delete-orphan")
    author_elected = relationship("DeputyParliamentaryActivityAuthorElected", back_populates="activity", cascade="all, delete-orphan")
    guests = relationship("DeputyParliamentaryActivityGuest", back_populates="activity", cascade="all, delete-orphan")
    publications = relationship("DeputyParliamentaryActivityPublication", back_populates="activity", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_deputy_parliamentary_activities_activity', 'deputy_activity_id'),
        Index('idx_deputy_parliamentary_activities_data_entrada', 'data_entrada'),
    )


# Parliamentary Activity supporting tables (same pattern)
class DeputyParliamentaryActivityVote(Base):
    __tablename__ = 'deputy_parliamentary_activity_votes'
    
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey('deputy_parliamentary_activities.id'), nullable=False)
    id_votacao = Column(String(50))
    resultado = Column(String(50))
    reuniao = Column(String(100))
    unanime = Column(String(10))
    data_votacao = Column(Date)
    descricao = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    activity = relationship("DeputyParliamentaryActivity", back_populates="votes")


class DeputyParliamentaryActivityAuthorGroup(Base):
    __tablename__ = 'deputy_parliamentary_activity_author_groups'
    
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey('deputy_parliamentary_activities.id'), nullable=False)
    nome = Column(String(200))
    cargo = Column(String(100))
    pais = Column(String(50))
    honra = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    activity = relationship("DeputyParliamentaryActivity", back_populates="author_groups")


class DeputyParliamentaryActivityAuthorElected(Base):
    __tablename__ = 'deputy_parliamentary_activity_author_elected'
    
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey('deputy_parliamentary_activities.id'), nullable=False)
    nome = Column(String(200))
    cargo = Column(String(100))
    pais = Column(String(50))
    honra = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    activity = relationship("DeputyParliamentaryActivity", back_populates="author_elected")


class DeputyParliamentaryActivityGuest(Base):
    __tablename__ = 'deputy_parliamentary_activity_guests'
    
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey('deputy_parliamentary_activities.id'), nullable=False)
    nome = Column(String(200))
    cargo = Column(String(100))
    pais = Column(String(50))
    honra = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    activity = relationship("DeputyParliamentaryActivity", back_populates="guests")


class DeputyParliamentaryActivityPublication(Base):
    __tablename__ = 'deputy_parliamentary_activity_publications'
    
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey('deputy_parliamentary_activities.id'), nullable=False)
    pub_nr = Column(String(50))
    pub_tipo = Column(String(50))
    pub_data = Column(Date)
    url_diario = Column(String(500))
    legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    activity = relationship("DeputyParliamentaryActivity", back_populates="publications")


# =====================================================
# LEGISLATIVE DATA (same structure as initiatives)
# =====================================================

class DeputyLegislativeData(Base):
    __tablename__ = 'deputy_legislative_data'
    
    id = Column(Integer, primary_key=True)
    deputy_activity_id = Column(Integer, ForeignKey('deputy_activities.id'), nullable=False)
    id_dados = Column(Integer)
    numero = Column(String(50))
    tipo = Column(String(50))
    desc_tipo = Column(String(200))
    assunto = Column(Text)
    legislatura = Column(String(20))
    sessao = Column(String(20))
    data_entrada = Column(Date)
    data_agendamento_debate = Column(Date)
    orgao_exterior = Column(String(200))
    observacoes = Column(Text)
    tipo_autor = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputy_activity = relationship("DeputyActivity", back_populates="legislative_data")
    votes = relationship("DeputyLegislativeDataVote", back_populates="legislative_data", cascade="all, delete-orphan")
    author_groups = relationship("DeputyLegislativeDataAuthorGroup", back_populates="legislative_data", cascade="all, delete-orphan")
    author_elected = relationship("DeputyLegislativeDataAuthorElected", back_populates="legislative_data", cascade="all, delete-orphan")
    guests = relationship("DeputyLegislativeDataGuest", back_populates="legislative_data", cascade="all, delete-orphan")
    publications = relationship("DeputyLegislativeDataPublication", back_populates="legislative_data", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_deputy_legislative_data_activity', 'deputy_activity_id'),
        Index('idx_deputy_legislative_data_data_entrada', 'data_entrada'),
    )


# Legislative Data supporting tables (same pattern)
class DeputyLegislativeDataVote(Base):
    __tablename__ = 'deputy_legislative_data_votes'
    
    id = Column(Integer, primary_key=True)
    legislative_data_id = Column(Integer, ForeignKey('deputy_legislative_data.id'), nullable=False)
    id_votacao = Column(String(50))
    resultado = Column(String(50))
    reuniao = Column(String(100))
    unanime = Column(String(10))
    data_votacao = Column(Date)
    descricao = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    legislative_data = relationship("DeputyLegislativeData", back_populates="votes")


class DeputyLegislativeDataAuthorGroup(Base):
    __tablename__ = 'deputy_legislative_data_author_groups'
    
    id = Column(Integer, primary_key=True)
    legislative_data_id = Column(Integer, ForeignKey('deputy_legislative_data.id'), nullable=False)
    nome = Column(String(200))
    cargo = Column(String(100))
    pais = Column(String(50))
    honra = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    legislative_data = relationship("DeputyLegislativeData", back_populates="author_groups")


class DeputyLegislativeDataAuthorElected(Base):
    __tablename__ = 'deputy_legislative_data_author_elected'
    
    id = Column(Integer, primary_key=True)
    legislative_data_id = Column(Integer, ForeignKey('deputy_legislative_data.id'), nullable=False)
    nome = Column(String(200))
    cargo = Column(String(100))
    pais = Column(String(50))
    honra = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    legislative_data = relationship("DeputyLegislativeData", back_populates="author_elected")


class DeputyLegislativeDataGuest(Base):
    __tablename__ = 'deputy_legislative_data_guests'
    
    id = Column(Integer, primary_key=True)
    legislative_data_id = Column(Integer, ForeignKey('deputy_legislative_data.id'), nullable=False)
    nome = Column(String(200))
    cargo = Column(String(100))
    pais = Column(String(50))
    honra = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    legislative_data = relationship("DeputyLegislativeData", back_populates="guests")


class DeputyLegislativeDataPublication(Base):
    __tablename__ = 'deputy_legislative_data_publications'
    
    id = Column(Integer, primary_key=True)
    legislative_data_id = Column(Integer, ForeignKey('deputy_legislative_data.id'), nullable=False)
    pub_nr = Column(String(50))
    pub_tipo = Column(String(50))
    pub_data = Column(Date)
    url_diario = Column(String(500))
    legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    legislative_data = relationship("DeputyLegislativeData", back_populates="publications")


# =====================================================
# COMPLEX NESTED STRUCTURES
# =====================================================

class DeputyGPSituation(Base):
    __tablename__ = 'deputy_gp_situations'
    
    id = Column(Integer, primary_key=True)
    deputy_activity_id = Column(Integer, ForeignKey('deputy_activities.id'), nullable=False)
    gp_id = Column(Integer)
    gp_sigla = Column(String(10))
    gp_dt_inicio = Column(Date)
    gp_dt_fim = Column(Date)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputy_activity = relationship("DeputyActivity", back_populates="gp_situations")


class DeputySituation(Base):
    __tablename__ = 'deputy_situations'
    
    id = Column(Integer, primary_key=True)
    deputy_activity_id = Column(Integer, ForeignKey('deputy_activities.id'), nullable=False)
    sio_des = Column(String(200))
    sio_dt_inicio = Column(Date)
    sio_dt_fim = Column(Date)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputy_activity = relationship("DeputyActivity", back_populates="situations")


# =====================================================
# LEGACY TABLES (for existing data compatibility)
# =====================================================

class TemasParliamentares(Base):
    __tablename__ = 'temas_parlamentares'
    
    id = Column(Integer, primary_key=True)
    id_externo = Column(Integer)
    nome = Column(String(200), nullable=False)
    descricao = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_temas_parlamentares_id_externo', 'id_externo'),
    )


class SecoesParliamentares(Base):
    __tablename__ = 'secoes_parlamentares'
    
    id = Column(Integer, primary_key=True)
    id_externo = Column(Integer)
    nome = Column(String(200), nullable=False)
    descricao = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_secoes_parlamentares_id_externo', 'id_externo'),
    )


class AgendaParlamentar(Base):
    __tablename__ = 'agenda_parlamentar'
    
    id = Column(Integer, primary_key=True)
    id_externo = Column(Integer)
    legislatura_id = Column(Integer, nullable=False)
    secao_id = Column(Integer)
    secao_nome = Column(Text)
    tema_id = Column(Integer)
    tema_nome = Column(Text)
    grupo_parlamentar = Column(Text)
    data_evento = Column(Date, nullable=False)
    hora_inicio = Column(Text)  # TIME in SQLite shows as TEXT
    hora_fim = Column(Text)     # TIME in SQLite shows as TEXT
    evento_dia_inteiro = Column(Boolean, default=False)
    titulo = Column(Text, nullable=False)
    subtitulo = Column(Text)
    descricao = Column(Text)
    local_evento = Column(Text)
    link_externo = Column(Text)
    pos_plenario = Column(Boolean, default=False)
    estado = Column(Text, default='agendado')
    created_at = Column(Text, default='CURRENT_TIMESTAMP')  # TIMESTAMP in SQLite
    updated_at = Column(Text, default='CURRENT_TIMESTAMP')  # TIMESTAMP in SQLite
    secao_parlamentar_id = Column(Integer, ForeignKey('secoes_parlamentares.id'))
    tema_parlamentar_id = Column(Integer, ForeignKey('temas_parlamentares.id'))
    
    __table_args__ = (
        Index('idx_agenda_data', 'data_evento'),
        Index('idx_agenda_legislatura_data', 'legislatura_id', 'data_evento'),
        Index('idx_agenda_grupo', 'grupo_parlamentar'),
        UniqueConstraint('id_externo', 'legislatura_id'),
        ForeignKeyConstraint(['legislatura_id'], ['legislaturas.id']),
    )




# =====================================================
# PARLIAMENTARY ORGANIZATION STRUCTURE (OrganizacaoAR)
# =====================================================

class ParliamentaryOrganization(Base):
    __tablename__ = 'parliamentary_organizations'
    
    id = Column(Integer, primary_key=True)
    legislatura_sigla = Column(String(20), nullable=False)
    xml_file_path = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    administrative_councils = relationship("AdministrativeCouncil", back_populates="organization", cascade="all, delete-orphan")
    leader_conferences = relationship("LeaderConference", back_populates="organization", cascade="all, delete-orphan")
    commission_president_conferences = relationship("CommissionPresidentConference", back_populates="organization", cascade="all, delete-orphan")
    plenaries = relationship("Plenary", back_populates="organization", cascade="all, delete-orphan")
    ar_boards = relationship("ARBoard", back_populates="organization", cascade="all, delete-orphan")
    commissions = relationship("Commission", back_populates="organization", cascade="all, delete-orphan")
    work_groups = relationship("WorkGroup", back_populates="organization", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_parliamentary_organizations_legislatura', 'legislatura_sigla'),
    )


class AdministrativeCouncil(Base):
    __tablename__ = 'administrative_councils'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('parliamentary_organizations.id'), nullable=False)
    id_orgao = Column(Integer)
    sigla_orgao = Column(String(20))
    nome_sigla = Column(String(200))
    numero_orgao = Column(Integer)
    sigla_legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    organization = relationship("ParliamentaryOrganization", back_populates="administrative_councils")
    historical_compositions = relationship("AdministrativeCouncilHistoricalComposition", back_populates="council", cascade="all, delete-orphan")


class LeaderConference(Base):
    __tablename__ = 'leader_conferences'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('parliamentary_organizations.id'), nullable=False)
    id_orgao = Column(Integer)
    sigla_orgao = Column(String(20))
    nome_sigla = Column(String(200))
    numero_orgao = Column(Integer)
    sigla_legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    organization = relationship("ParliamentaryOrganization", back_populates="leader_conferences")
    historical_compositions = relationship("LeaderConferenceHistoricalComposition", back_populates="conference", cascade="all, delete-orphan")


class CommissionPresidentConference(Base):
    __tablename__ = 'commission_president_conferences'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('parliamentary_organizations.id'), nullable=False)
    id_orgao = Column(Integer)
    sigla_orgao = Column(String(20))
    nome_sigla = Column(String(200))
    numero_orgao = Column(Integer)
    sigla_legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    organization = relationship("ParliamentaryOrganization", back_populates="commission_president_conferences")
    historical_compositions = relationship("CommissionPresidentConferenceHistoricalComposition", back_populates="conference", cascade="all, delete-orphan")


class Plenary(Base):
    __tablename__ = 'plenaries'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('parliamentary_organizations.id'), nullable=False)
    id_orgao = Column(Integer)
    sigla_orgao = Column(String(20))
    nome_sigla = Column(String(200))
    numero_orgao = Column(Integer)
    sigla_legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    organization = relationship("ParliamentaryOrganization", back_populates="plenaries")
    compositions = relationship("PlenaryComposition", back_populates="plenary", cascade="all, delete-orphan")


class ARBoard(Base):
    __tablename__ = 'ar_boards'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('parliamentary_organizations.id'), nullable=False)
    id_orgao = Column(Integer)
    sigla_orgao = Column(String(20))
    nome_sigla = Column(String(200))
    numero_orgao = Column(Integer)
    sigla_legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    organization = relationship("ParliamentaryOrganization", back_populates="ar_boards")
    historical_compositions = relationship("ARBoardHistoricalComposition", back_populates="board", cascade="all, delete-orphan")


class Commission(Base):
    __tablename__ = 'commissions'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('parliamentary_organizations.id'), nullable=False)
    id_orgao = Column(Integer)
    sigla_orgao = Column(String(20))
    nome_sigla = Column(String(200))
    numero_orgao = Column(Integer)
    sigla_legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    organization = relationship("ParliamentaryOrganization", back_populates="commissions")
    historical_compositions = relationship("CommissionHistoricalComposition", back_populates="commission", cascade="all, delete-orphan")


class WorkGroup(Base):
    __tablename__ = 'work_groups'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('parliamentary_organizations.id'), nullable=False)
    id_orgao = Column(Integer)
    sigla_orgao = Column(String(20))
    nome_sigla = Column(String(200))
    numero_orgao = Column(Integer)
    sigla_legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    organization = relationship("ParliamentaryOrganization", back_populates="work_groups")
    historical_compositions = relationship("WorkGroupHistoricalComposition", back_populates="work_group", cascade="all, delete-orphan")


# Historical Composition Models
class AdministrativeCouncilHistoricalComposition(Base):
    __tablename__ = 'administrative_council_historical_compositions'
    
    id = Column(Integer, primary_key=True)
    council_id = Column(Integer, ForeignKey('administrative_councils.id'), nullable=False)
    leg_des = Column(String(20))
    dep_id = Column(Integer)
    dep_cad_id = Column(Integer)
    dep_nome_parlamentar = Column(String(200))
    org_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    council = relationship("AdministrativeCouncil", back_populates="historical_compositions")
    gp_situations = relationship("OrganCompositionGPSituation", back_populates="admin_council_composition", cascade="all, delete-orphan")
    deputy_positions = relationship("OrganCompositionDeputyPosition", back_populates="admin_council_composition", cascade="all, delete-orphan")
    deputy_situations = relationship("OrganCompositionDeputySituation", back_populates="admin_council_composition", cascade="all, delete-orphan")


class LeaderConferenceHistoricalComposition(Base):
    __tablename__ = 'leader_conference_historical_compositions'
    
    id = Column(Integer, primary_key=True)
    conference_id = Column(Integer, ForeignKey('leader_conferences.id'), nullable=False)
    leg_des = Column(String(20))
    dep_id = Column(Integer)
    dep_cad_id = Column(Integer)
    dep_nome_parlamentar = Column(String(200))
    org_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    conference = relationship("LeaderConference", back_populates="historical_compositions")
    gp_situations = relationship("OrganCompositionGPSituation", back_populates="leader_conference_composition", cascade="all, delete-orphan")
    deputy_positions = relationship("OrganCompositionDeputyPosition", back_populates="leader_conference_composition", cascade="all, delete-orphan")
    deputy_situations = relationship("OrganCompositionDeputySituation", back_populates="leader_conference_composition", cascade="all, delete-orphan")


class CommissionPresidentConferenceHistoricalComposition(Base):
    __tablename__ = 'commission_president_conference_historical_compositions'
    
    id = Column(Integer, primary_key=True)
    conference_id = Column(Integer, ForeignKey('commission_president_conferences.id'), nullable=False)
    leg_des = Column(String(20))
    dep_id = Column(Integer)
    dep_cad_id = Column(Integer)
    dep_nome_parlamentar = Column(String(200))
    org_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    conference = relationship("CommissionPresidentConference", back_populates="historical_compositions")
    gp_situations = relationship("OrganCompositionGPSituation", back_populates="cpc_composition", cascade="all, delete-orphan")
    deputy_positions = relationship("OrganCompositionDeputyPosition", back_populates="cpc_composition", cascade="all, delete-orphan")
    deputy_situations = relationship("OrganCompositionDeputySituation", back_populates="cpc_composition", cascade="all, delete-orphan")
    presidency_organs = relationship("PresidencyOrgan", back_populates="cpc_composition", cascade="all, delete-orphan")


class PlenaryComposition(Base):
    __tablename__ = 'plenary_compositions'
    
    id = Column(Integer, primary_key=True)
    plenary_id = Column(Integer, ForeignKey('plenaries.id'), nullable=False)
    leg_des = Column(String(20))
    dep_id = Column(Integer)
    dep_cad_id = Column(Integer)
    dep_nome_parlamentar = Column(String(200))
    org_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    plenary = relationship("Plenary", back_populates="compositions")
    gp_situations = relationship("OrganCompositionGPSituation", back_populates="plenary_composition", cascade="all, delete-orphan")
    deputy_positions = relationship("OrganCompositionDeputyPosition", back_populates="plenary_composition", cascade="all, delete-orphan")
    deputy_situations = relationship("OrganCompositionDeputySituation", back_populates="plenary_composition", cascade="all, delete-orphan")


class ARBoardHistoricalComposition(Base):
    __tablename__ = 'ar_board_historical_compositions'
    
    id = Column(Integer, primary_key=True)
    board_id = Column(Integer, ForeignKey('ar_boards.id'), nullable=False)
    leg_des = Column(String(20))
    dep_id = Column(Integer)
    dep_cad_id = Column(Integer)
    dep_nome_parlamentar = Column(String(200))
    org_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    board = relationship("ARBoard", back_populates="historical_compositions")
    gp_situations = relationship("OrganCompositionGPSituation", back_populates="ar_board_composition", cascade="all, delete-orphan")
    deputy_positions = relationship("OrganCompositionDeputyPosition", back_populates="ar_board_composition", cascade="all, delete-orphan")
    deputy_situations = relationship("OrganCompositionDeputySituation", back_populates="ar_board_composition", cascade="all, delete-orphan")


class CommissionHistoricalComposition(Base):
    __tablename__ = 'commission_historical_compositions'
    
    id = Column(Integer, primary_key=True)
    commission_id = Column(Integer, ForeignKey('commissions.id'), nullable=False)
    leg_des = Column(String(20))
    dep_id = Column(Integer)
    dep_cad_id = Column(Integer)
    dep_nome_parlamentar = Column(String(200))
    org_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    commission = relationship("Commission", back_populates="historical_compositions")
    gp_situations = relationship("OrganCompositionGPSituation", back_populates="commission_composition", cascade="all, delete-orphan")
    deputy_positions = relationship("OrganCompositionDeputyPosition", back_populates="commission_composition", cascade="all, delete-orphan")
    deputy_situations = relationship("OrganCompositionDeputySituation", back_populates="commission_composition", cascade="all, delete-orphan")


class WorkGroupHistoricalComposition(Base):
    __tablename__ = 'work_group_historical_compositions'
    
    id = Column(Integer, primary_key=True)
    work_group_id = Column(Integer, ForeignKey('work_groups.id'), nullable=False)
    leg_des = Column(String(20))
    dep_id = Column(Integer)
    dep_cad_id = Column(Integer)
    dep_nome_parlamentar = Column(String(200))
    org_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    work_group = relationship("WorkGroup", back_populates="historical_compositions")
    gp_situations = relationship("OrganCompositionGPSituation", back_populates="work_group_composition", cascade="all, delete-orphan")
    deputy_positions = relationship("OrganCompositionDeputyPosition", back_populates="work_group_composition", cascade="all, delete-orphan")
    deputy_situations = relationship("OrganCompositionDeputySituation", back_populates="work_group_composition", cascade="all, delete-orphan")


# Deputy Position and Situation Models
class OrganCompositionGPSituation(Base):
    __tablename__ = 'organ_composition_gp_situations'
    
    id = Column(Integer, primary_key=True)
    admin_council_composition_id = Column(Integer, ForeignKey('administrative_council_historical_compositions.id'))
    leader_conference_composition_id = Column(Integer, ForeignKey('leader_conference_historical_compositions.id'))
    cpc_composition_id = Column(Integer, ForeignKey('commission_president_conference_historical_compositions.id'))
    plenary_composition_id = Column(Integer, ForeignKey('plenary_compositions.id'))
    ar_board_composition_id = Column(Integer, ForeignKey('ar_board_historical_compositions.id'))
    commission_composition_id = Column(Integer, ForeignKey('commission_historical_compositions.id'))
    work_group_composition_id = Column(Integer, ForeignKey('work_group_historical_compositions.id'))
    gp_id = Column(Integer)
    gp_sigla = Column(String(20))
    gp_dt_inicio = Column(Date)
    gp_dt_fim = Column(Date)
    created_at = Column(DateTime, default=func.now())
    
    admin_council_composition = relationship("AdministrativeCouncilHistoricalComposition", back_populates="gp_situations")
    leader_conference_composition = relationship("LeaderConferenceHistoricalComposition", back_populates="gp_situations")
    cpc_composition = relationship("CommissionPresidentConferenceHistoricalComposition", back_populates="gp_situations")
    plenary_composition = relationship("PlenaryComposition", back_populates="gp_situations")
    ar_board_composition = relationship("ARBoardHistoricalComposition", back_populates="gp_situations")
    commission_composition = relationship("CommissionHistoricalComposition", back_populates="gp_situations")
    work_group_composition = relationship("WorkGroupHistoricalComposition", back_populates="gp_situations")


class OrganCompositionDeputyPosition(Base):
    __tablename__ = 'organ_composition_deputy_positions'
    
    id = Column(Integer, primary_key=True)
    admin_council_composition_id = Column(Integer, ForeignKey('administrative_council_historical_compositions.id'))
    leader_conference_composition_id = Column(Integer, ForeignKey('leader_conference_historical_compositions.id'))
    cpc_composition_id = Column(Integer, ForeignKey('commission_president_conference_historical_compositions.id'))
    plenary_composition_id = Column(Integer, ForeignKey('plenary_compositions.id'))
    ar_board_composition_id = Column(Integer, ForeignKey('ar_board_historical_compositions.id'))
    commission_composition_id = Column(Integer, ForeignKey('commission_historical_compositions.id'))
    work_group_composition_id = Column(Integer, ForeignKey('work_group_historical_compositions.id'))
    car_id = Column(Integer)
    car_des = Column(String(200))
    car_dt_inicio = Column(Date)
    car_dt_fim = Column(Date)
    created_at = Column(DateTime, default=func.now())
    
    admin_council_composition = relationship("AdministrativeCouncilHistoricalComposition", back_populates="deputy_positions")
    leader_conference_composition = relationship("LeaderConferenceHistoricalComposition", back_populates="deputy_positions")
    cpc_composition = relationship("CommissionPresidentConferenceHistoricalComposition", back_populates="deputy_positions")
    plenary_composition = relationship("PlenaryComposition", back_populates="deputy_positions")
    ar_board_composition = relationship("ARBoardHistoricalComposition", back_populates="deputy_positions")
    commission_composition = relationship("CommissionHistoricalComposition", back_populates="deputy_positions")
    work_group_composition = relationship("WorkGroupHistoricalComposition", back_populates="deputy_positions")


class OrganCompositionDeputySituation(Base):
    __tablename__ = 'organ_composition_deputy_situations'
    
    id = Column(Integer, primary_key=True)
    admin_council_composition_id = Column(Integer, ForeignKey('administrative_council_historical_compositions.id'))
    leader_conference_composition_id = Column(Integer, ForeignKey('leader_conference_historical_compositions.id'))
    cpc_composition_id = Column(Integer, ForeignKey('commission_president_conference_historical_compositions.id'))
    plenary_composition_id = Column(Integer, ForeignKey('plenary_compositions.id'))
    ar_board_composition_id = Column(Integer, ForeignKey('ar_board_historical_compositions.id'))
    commission_composition_id = Column(Integer, ForeignKey('commission_historical_compositions.id'))
    work_group_composition_id = Column(Integer, ForeignKey('work_group_historical_compositions.id'))
    sio_des = Column(String(200))
    sio_tip_mem = Column(String(100))
    sio_dt_inicio = Column(Date)
    sio_dt_fim = Column(Date)
    created_at = Column(DateTime, default=func.now())
    
    admin_council_composition = relationship("AdministrativeCouncilHistoricalComposition", back_populates="deputy_situations")
    leader_conference_composition = relationship("LeaderConferenceHistoricalComposition", back_populates="deputy_situations")
    cpc_composition = relationship("CommissionPresidentConferenceHistoricalComposition", back_populates="deputy_situations")
    plenary_composition = relationship("PlenaryComposition", back_populates="deputy_situations")
    ar_board_composition = relationship("ARBoardHistoricalComposition", back_populates="deputy_situations")
    commission_composition = relationship("CommissionHistoricalComposition", back_populates="deputy_situations")
    work_group_composition = relationship("WorkGroupHistoricalComposition", back_populates="deputy_situations")


# Commission Presidency Models
class PresidencyOrgan(Base):
    __tablename__ = 'presidency_organs'
    
    id = Column(Integer, primary_key=True)
    cpc_composition_id = Column(Integer, ForeignKey('commission_president_conference_historical_compositions.id'), nullable=False)
    org_id = Column(Integer)
    org_numero = Column(Integer)
    org_sigla = Column(String(20))
    org_des = Column(String(200))
    created_at = Column(DateTime, default=func.now())
    
    cpc_composition = relationship("CommissionPresidentConferenceHistoricalComposition", back_populates="presidency_organs")
    commission_presidencies = relationship("CommissionPresidency", back_populates="presidency_organ", cascade="all, delete-orphan")


class CommissionPresidency(Base):
    __tablename__ = 'commission_presidencies'
    
    id = Column(Integer, primary_key=True)
    presidency_organ_id = Column(Integer, ForeignKey('presidency_organs.id'), nullable=False)
    pec_id = Column(Integer)
    pec_tia_des = Column(String(200))
    pec_dt_inicio = Column(Date)
    pec_dt_fim = Column(Date)
    created_at = Column(DateTime, default=func.now())
    
    presidency_organ = relationship("PresidencyOrgan", back_populates="commission_presidencies")


# =====================================================
# IMPORT TRACKING
# =====================================================

class ImportStatus(Base):
    __tablename__ = 'import_status'
    
    id = Column(Integer, primary_key=True)
    file_url = Column(String(1000), nullable=False, unique=True)
    file_path = Column(String(500))
    file_name = Column(String(200), nullable=False)
    file_type = Column(String(20), nullable=False)  # 'JSON', 'XML', 'PDF', 'Archive'
    category = Column(String(100), nullable=False)
    legislatura = Column(String(20))
    sub_series = Column(String(100))  # For DAR files
    session = Column(String(50))    # For DAR files
    number = Column(String(50))     # For DAR files
    file_hash = Column(String(64))  # SHA1 hash of file content
    file_size = Column(Integer)
    status = Column(String(50), nullable=False, default='pending')  # 'pending', 'processing', 'completed', 'failed', 'schema_mismatch'
    schema_issues = Column(Text)  # JSON array of schema validation issues
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    error_message = Column(Text)
    records_imported = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_import_status_url', 'file_url'),
        Index('idx_import_status_hash', 'file_hash'),
        Index('idx_import_status_status', 'status'),
        Index('idx_import_status_category', 'category'),
        Index('idx_import_status_legislatura', 'legislatura'),
    )