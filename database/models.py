"""
SQLAlchemy Models for Portuguese Parliament Database
===================================================

Comprehensive models for all parliamentary data with zero data loss.
Supports both SQLite (development) and Aurora MySQL/PostgreSQL (production).

Author: Claude
Version: 2.0 - Full Mapping Implementation
"""

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, Index
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

class AgendaParlamentar(Base):
    __tablename__ = 'agenda_parlamentar'
    
    id = Column(Integer, primary_key=True)
    id_externo = Column(Integer, unique=True)
    legislatura_id = Column(Integer)
    secao_id = Column(Integer)
    secao_nome = Column(String(200))
    tema_id = Column(Integer)
    tema_nome = Column(String(200))
    grupo_parlamentar = Column(String(100))
    data_evento = Column(Date, nullable=False)
    hora_inicio = Column(String(10))
    hora_fim = Column(String(10))
    evento_dia_inteiro = Column(Boolean, default=False)
    titulo = Column(String(500), nullable=False)
    subtitulo = Column(String(500))
    descricao = Column(Text)
    local_evento = Column(String(200))
    link_externo = Column(String(500))
    pos_plenario = Column(Boolean, default=False)
    estado = Column(String(20), default='agendado')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())