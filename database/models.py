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
    
    # Relationships
    atividades = relationship("AtividadeDeputado", back_populates="deputado", cascade="all, delete-orphan")


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
    permanent_committees = relationship("PermanentCommittee", back_populates="organization", cascade="all, delete-orphan")
    sub_committees = relationship("SubCommittee", back_populates="organization", cascade="all, delete-orphan")
    
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
    meetings = relationship("OrganMeeting", back_populates="commission", cascade="all, delete-orphan")


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
    meetings = relationship("OrganMeeting", back_populates="work_group", cascade="all, delete-orphan")


class PermanentCommittee(Base):
    __tablename__ = 'permanent_committees'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('parliamentary_organizations.id'), nullable=False)
    id_orgao = Column(Integer)
    sigla_orgao = Column(String(20))
    nome_sigla = Column(String(200))
    numero_orgao = Column(Integer)
    sigla_legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    organization = relationship("ParliamentaryOrganization", back_populates="permanent_committees")
    historical_compositions = relationship("PermanentCommitteeHistoricalComposition", back_populates="permanent_committee", cascade="all, delete-orphan")
    meetings = relationship("OrganMeeting", back_populates="permanent_committee", cascade="all, delete-orphan")


class SubCommittee(Base):
    __tablename__ = 'sub_committees'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('parliamentary_organizations.id'), nullable=False)
    id_orgao = Column(Integer)
    sigla_orgao = Column(String(20))
    nome_sigla = Column(String(200))
    numero_orgao = Column(Integer)
    sigla_legislatura = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    
    organization = relationship("ParliamentaryOrganization", back_populates="sub_committees")
    historical_compositions = relationship("SubCommitteeHistoricalComposition", back_populates="sub_committee", cascade="all, delete-orphan")
    meetings = relationship("OrganMeeting", back_populates="sub_committee", cascade="all, delete-orphan")


# Meeting Model (shared by all organ types)
class OrganMeeting(Base):
    __tablename__ = 'organ_meetings'
    
    id = Column(Integer, primary_key=True)
    
    # Foreign keys to different organ types
    commission_id = Column(Integer, ForeignKey('commissions.id'))
    work_group_id = Column(Integer, ForeignKey('work_groups.id'))
    permanent_committee_id = Column(Integer, ForeignKey('permanent_committees.id'))
    sub_committee_id = Column(Integer, ForeignKey('sub_committees.id'))
    
    # Meeting data
    reu_tar_sigla = Column(String(20))
    reu_local = Column(String(200))
    reu_data = Column(Date)
    reu_hora = Column(String(10))
    reu_tipo = Column(String(100))
    reu_estado = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    commission = relationship("Commission", back_populates="meetings")
    work_group = relationship("WorkGroup", back_populates="meetings")
    permanent_committee = relationship("PermanentCommittee", back_populates="meetings")
    sub_committee = relationship("SubCommittee", back_populates="meetings")


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
    dep_nome_completo = Column(String(300))
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


class PermanentCommitteeHistoricalComposition(Base):
    __tablename__ = 'permanent_committee_historical_compositions'
    
    id = Column(Integer, primary_key=True)
    permanent_committee_id = Column(Integer, ForeignKey('permanent_committees.id'), nullable=False)
    leg_des = Column(String(20))
    dep_id = Column(Integer)
    dep_cad_id = Column(Integer)
    dep_nome_parlamentar = Column(String(200))
    org_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    permanent_committee = relationship("PermanentCommittee", back_populates="historical_compositions")
    gp_situations = relationship("OrganCompositionGPSituation", back_populates="permanent_committee_composition", cascade="all, delete-orphan")
    deputy_positions = relationship("OrganCompositionDeputyPosition", back_populates="permanent_committee_composition", cascade="all, delete-orphan")
    deputy_situations = relationship("OrganCompositionDeputySituation", back_populates="permanent_committee_composition", cascade="all, delete-orphan")


class SubCommitteeHistoricalComposition(Base):
    __tablename__ = 'sub_committee_historical_compositions'
    
    id = Column(Integer, primary_key=True)
    sub_committee_id = Column(Integer, ForeignKey('sub_committees.id'), nullable=False)
    leg_des = Column(String(20))
    dep_id = Column(Integer)
    dep_cad_id = Column(Integer)
    dep_nome_parlamentar = Column(String(200))
    org_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    sub_committee = relationship("SubCommittee", back_populates="historical_compositions")
    gp_situations = relationship("OrganCompositionGPSituation", back_populates="sub_committee_composition", cascade="all, delete-orphan")
    deputy_positions = relationship("OrganCompositionDeputyPosition", back_populates="sub_committee_composition", cascade="all, delete-orphan")
    deputy_situations = relationship("OrganCompositionDeputySituation", back_populates="sub_committee_composition", cascade="all, delete-orphan")


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
    permanent_committee_composition_id = Column(Integer, ForeignKey('permanent_committee_historical_compositions.id'))
    sub_committee_composition_id = Column(Integer, ForeignKey('sub_committee_historical_compositions.id'))
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
    permanent_committee_composition = relationship("PermanentCommitteeHistoricalComposition", back_populates="gp_situations")
    sub_committee_composition = relationship("SubCommitteeHistoricalComposition", back_populates="gp_situations")


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
    permanent_committee_composition_id = Column(Integer, ForeignKey('permanent_committee_historical_compositions.id'))
    sub_committee_composition_id = Column(Integer, ForeignKey('sub_committee_historical_compositions.id'))
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
    permanent_committee_composition = relationship("PermanentCommitteeHistoricalComposition", back_populates="deputy_positions")
    sub_committee_composition = relationship("SubCommitteeHistoricalComposition", back_populates="deputy_positions")


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
    permanent_committee_composition_id = Column(Integer, ForeignKey('permanent_committee_historical_compositions.id'))
    sub_committee_composition_id = Column(Integer, ForeignKey('sub_committee_historical_compositions.id'))
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
    permanent_committee_composition = relationship("PermanentCommitteeHistoricalComposition", back_populates="deputy_situations")
    sub_committee_composition = relationship("SubCommitteeHistoricalComposition", back_populates="deputy_situations")


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


# AtividadeDeputado Models for Deputy Activity Data

class AtividadeDeputado(Base):
    __tablename__ = 'atividade_deputados'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    dep_cad_id = Column(Integer)  # DepCadId field
    leg_des = Column(String(20))  # LegDes field
    created_at = Column(DateTime, default=func.now())
    
    deputado = relationship("Deputado", back_populates="atividades")
    atividade_list = relationship("AtividadeDeputadoList", back_populates="atividade_deputado", cascade="all, delete-orphan")
    deputado_situacoes = relationship("DeputadoSituacao", back_populates="atividade_deputado", cascade="all, delete-orphan")


class AtividadeDeputadoList(Base):
    __tablename__ = 'atividade_deputado_lists'
    
    id = Column(Integer, primary_key=True)
    atividade_deputado_id = Column(Integer, ForeignKey('atividade_deputados.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    atividade_deputado = relationship("AtividadeDeputado", back_populates="atividade_list")
    actividade_outs = relationship("ActividadeOut", back_populates="atividade_list", cascade="all, delete-orphan")


class ActividadeOut(Base):
    __tablename__ = 'actividade_outs'
    
    id = Column(Integer, primary_key=True)
    atividade_list_id = Column(Integer, ForeignKey('atividade_deputado_lists.id'), nullable=False)
    rel = Column(Text)  # Rel field - appears to be empty in the XML
    created_at = Column(DateTime, default=func.now())
    
    atividade_list = relationship("AtividadeDeputadoList", back_populates="actividade_outs")
    dados_legis_deputados = relationship("DadosLegisDeputado", back_populates="actividade_out", cascade="all, delete-orphan")
    audiencias = relationship("ActividadeAudiencia", back_populates="actividade_out", cascade="all, delete-orphan")
    audicoes = relationship("ActividadeAudicao", back_populates="actividade_out", cascade="all, delete-orphan")


class DadosLegisDeputado(Base):
    __tablename__ = 'dados_legis_deputados'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    nome = Column(String(200))  # Nome field
    dpl_grpar = Column(String(100))  # Dpl_grpar field
    created_at = Column(DateTime, default=func.now())
    
    actividade_out = relationship("ActividadeOut", back_populates="dados_legis_deputados")


class ActividadeAudiencia(Base):
    __tablename__ = 'actividade_audiencias'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    actividade_out = relationship("ActividadeOut", back_populates="audiencias")
    actividades_comissao = relationship("ActividadesComissaoOut", back_populates="audiencia", cascade="all, delete-orphan")


class ActividadeAudicao(Base):
    __tablename__ = 'actividade_audicoes'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    actividade_out = relationship("ActividadeOut", back_populates="audicoes")
    actividades_comissao = relationship("ActividadesComissaoOut", back_populates="audicao", cascade="all, delete-orphan")


class ActividadesComissaoOut(Base):
    __tablename__ = 'actividades_comissao_outs'
    
    id = Column(Integer, primary_key=True)
    audiencia_id = Column(Integer, ForeignKey('actividade_audiencias.id'), nullable=True)
    audicao_id = Column(Integer, ForeignKey('actividade_audicoes.id'), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    audiencia = relationship("ActividadeAudiencia", back_populates="actividades_comissao")
    audicao = relationship("ActividadeAudicao", back_populates="actividades_comissao")


class DeputadoSituacao(Base):
    __tablename__ = 'deputado_situacoes'
    
    id = Column(Integer, primary_key=True)
    atividade_deputado_id = Column(Integer, ForeignKey('atividade_deputados.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    atividade_deputado = relationship("AtividadeDeputado", back_populates="deputado_situacoes")
    dados_situacao = relationship("DadosSituacaoDeputado", back_populates="deputado_situacao", cascade="all, delete-orphan")


class DadosSituacaoDeputado(Base):
    __tablename__ = 'dados_situacao_deputados'
    
    id = Column(Integer, primary_key=True)
    deputado_situacao_id = Column(Integer, ForeignKey('deputado_situacoes.id'), nullable=False)
    sio_des = Column(String(100))  # SioDes - situation description
    sio_dt_inicio = Column(Date)   # SioDtInicio - start date
    sio_dt_fim = Column(Date)      # SioDtFim - end date
    created_at = Column(DateTime, default=func.now())
    
    deputado_situacao = relationship("DeputadoSituacao", back_populates="dados_situacao")


class RegistoInteresses(Base):
    __tablename__ = 'registo_interesses'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # V3 Schema fields (newer format)
    record_id = Column(String(50))
    full_name = Column(String(200))
    marital_status = Column(String(50))
    spouse_name = Column(String(200))
    matrimonial_regime = Column(String(100))
    exclusivity = Column(String(10))  # "Yes"/"No"
    dgf_number = Column(String(50))
    
    # V2/V1 Schema fields (older formats)
    cad_id = Column(Integer)
    cad_nome_completo = Column(String(200))
    cad_actividade_profissional = Column(Text)
    cad_estado_civil_cod = Column(String(10))
    cad_estado_civil_des = Column(String(50))
    cad_fam_id = Column(Integer)
    cad_nome_conjuge = Column(String(200))
    cad_rgi = Column(String(100))
    
    schema_version = Column(String(10))  # "V1", "V2", or "V3"
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    deputado = relationship("Deputado", backref="registos_interesses")
    legislatura = relationship("Legislatura", backref="registos_interesses")


class DiplomaAprovado(Base):
    __tablename__ = 'diplomas_aprovados'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Core diploma fields
    diploma_id = Column(Integer, unique=True)  # External ID
    numero = Column(Integer)
    titulo = Column(Text)
    tipo = Column(String(100))
    sessao = Column(Integer)
    ano_civil = Column(Integer)
    link_texto = Column(Text)
    observacoes = Column(Text)
    tp = Column(String(50))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="diplomas_aprovados")
    publicacoes = relationship("DiplomaPublicacao", back_populates="diploma", cascade="all, delete-orphan")
    iniciativas = relationship("DiplomaIniciativa", back_populates="diploma", cascade="all, delete-orphan")


class DiplomaPublicacao(Base):
    __tablename__ = 'diploma_publicacoes'
    
    id = Column(Integer, primary_key=True)
    diploma_id = Column(Integer, ForeignKey('diplomas_aprovados.id'), nullable=False)
    
    pub_nr = Column(Integer)
    pub_tipo = Column(String(50))
    pub_tp = Column(String(10))
    pub_leg = Column(String(20))
    pub_sl = Column(Integer)
    pub_dt = Column(Date)
    pag = Column(Text)  # Can contain multiple page numbers
    id_pag = Column(Integer)
    url_diario = Column(Text)
    supl = Column(String(10))
    obs = Column(Text)
    pag_final_diario_supl = Column(String(50))
    
    created_at = Column(DateTime, default=func.now())
    
    diploma = relationship("DiplomaAprovado", back_populates="publicacoes")


class DiplomaIniciativa(Base):
    __tablename__ = 'diploma_iniciativas'
    
    id = Column(Integer, primary_key=True)
    diploma_id = Column(Integer, ForeignKey('diplomas_aprovados.id'), nullable=False)
    
    ini_nr = Column(Integer)
    ini_tipo = Column(String(100))
    ini_link_texto = Column(Text)
    ini_id = Column(Integer)
    
    created_at = Column(DateTime, default=func.now())
    
    diploma = relationship("DiplomaAprovado", back_populates="iniciativas")


class PerguntaRequerimento(Base):
    __tablename__ = 'perguntas_requerimentos'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Core fields
    requerimento_id = Column(Integer, unique=True)  # External ID
    tipo = Column(String(100))
    nr = Column(Integer)
    req_tipo = Column(String(100))
    sessao = Column(Integer)
    assunto = Column(Text)
    dt_entrada = Column(Date)
    data_envio = Column(Date)
    observacoes = Column(Text)
    ficheiro = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="perguntas_requerimentos")
    publicacoes = relationship("PerguntaRequerimentoPublicacao", back_populates="pergunta_requerimento", cascade="all, delete-orphan")
    destinatarios = relationship("PerguntaRequerimentoDestinatario", back_populates="pergunta_requerimento", cascade="all, delete-orphan")
    autores = relationship("PerguntaRequerimentoAutor", back_populates="pergunta_requerimento", cascade="all, delete-orphan")


class PerguntaRequerimentoPublicacao(Base):
    __tablename__ = 'pergunta_requerimento_publicacoes'
    
    id = Column(Integer, primary_key=True)
    pergunta_requerimento_id = Column(Integer, ForeignKey('perguntas_requerimentos.id'), nullable=False)
    
    pub_nr = Column(Integer)
    pub_tipo = Column(String(50))
    pub_tp = Column(String(10))
    pub_leg = Column(String(20))
    pub_sl = Column(Integer)
    pub_dt = Column(Date)
    id_pag = Column(Integer)
    url_diario = Column(Text)
    pag = Column(Text)
    supl = Column(String(10))
    obs = Column(Text)
    pag_final_diario_supl = Column(String(50))
    
    created_at = Column(DateTime, default=func.now())
    
    pergunta_requerimento = relationship("PerguntaRequerimento", back_populates="publicacoes")


class PerguntaRequerimentoDestinatario(Base):
    __tablename__ = 'pergunta_requerimento_destinatarios'
    
    id = Column(Integer, primary_key=True)
    pergunta_requerimento_id = Column(Integer, ForeignKey('perguntas_requerimentos.id'), nullable=False)
    
    nome_entidade = Column(String(200))
    data_envio = Column(Date)
    
    created_at = Column(DateTime, default=func.now())
    
    pergunta_requerimento = relationship("PerguntaRequerimento", back_populates="destinatarios")
    respostas = relationship("PerguntaRequerimentoResposta", back_populates="destinatario", cascade="all, delete-orphan")


class PerguntaRequerimentoResposta(Base):
    __tablename__ = 'pergunta_requerimento_respostas'
    
    id = Column(Integer, primary_key=True)
    destinatario_id = Column(Integer, ForeignKey('pergunta_requerimento_destinatarios.id'), nullable=False)
    
    entidade = Column(String(200))
    data_resposta = Column(Date)
    ficheiro = Column(Text)
    doc_remetida = Column(String(200))
    
    created_at = Column(DateTime, default=func.now())
    
    destinatario = relationship("PerguntaRequerimentoDestinatario", back_populates="respostas")


class PerguntaRequerimentoAutor(Base):
    __tablename__ = 'pergunta_requerimento_autores'
    
    id = Column(Integer, primary_key=True)
    pergunta_requerimento_id = Column(Integer, ForeignKey('perguntas_requerimentos.id'), nullable=False)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=True)
    
    id_cadastro = Column(Integer)
    nome = Column(String(200))
    gp = Column(String(50))  # Grupo Parlamentar
    
    created_at = Column(DateTime, default=func.now())
    
    pergunta_requerimento = relationship("PerguntaRequerimento", back_populates="autores")
    deputado = relationship("Deputado", backref="perguntas_requerimentos_autoria")


class CooperacaoParlamentar(Base):
    __tablename__ = 'cooperacao_parlamentar'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Core fields
    cooperacao_id = Column(Integer, unique=True)  # External ID
    tipo = Column(String(100))
    nome = Column(Text)
    sessao = Column(Integer)
    data = Column(Date)
    local = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="cooperacao_parlamentar")
    programas = relationship("CooperacaoPrograma", back_populates="cooperacao", cascade="all, delete-orphan")
    atividades = relationship("CooperacaoAtividade", back_populates="cooperacao", cascade="all, delete-orphan")


class CooperacaoPrograma(Base):
    __tablename__ = 'cooperacao_programas'
    
    id = Column(Integer, primary_key=True)
    cooperacao_id = Column(Integer, ForeignKey('cooperacao_parlamentar.id'), nullable=False)
    
    nome = Column(Text)
    descricao = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    cooperacao = relationship("CooperacaoParlamentar", back_populates="programas")


class CooperacaoAtividade(Base):
    __tablename__ = 'cooperacao_atividades'
    
    id = Column(Integer, primary_key=True)
    cooperacao_id = Column(Integer, ForeignKey('cooperacao_parlamentar.id'), nullable=False)
    
    tipo_atividade = Column(String(100))
    data_inicio = Column(Date)
    data_fim = Column(Date)
    descricao = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    cooperacao = relationship("CooperacaoParlamentar", back_populates="atividades")
    participantes = relationship("CooperacaoParticipante", back_populates="atividade", cascade="all, delete-orphan")


class CooperacaoParticipante(Base):
    __tablename__ = 'cooperacao_participantes'
    
    id = Column(Integer, primary_key=True)
    atividade_id = Column(Integer, ForeignKey('cooperacao_atividades.id'), nullable=False)
    
    nome = Column(String(200))
    cargo = Column(String(100))
    entidade = Column(String(200))
    tipo_participante = Column(String(50))  # 'interno', 'externo', etc.
    
    created_at = Column(DateTime, default=func.now())
    
    atividade = relationship("CooperacaoAtividade", back_populates="participantes")


class DelegacaoEventual(Base):
    __tablename__ = 'delegacao_eventual'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Core fields
    delegacao_id = Column(Integer, unique=True)  # External ID
    nome = Column(Text)
    local = Column(Text)
    sessao = Column(Integer)
    data_inicio = Column(Date)
    data_fim = Column(Date)
    tipo = Column(String(100))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="delegacoes_eventuais")
    participantes = relationship("DelegacaoEventualParticipante", back_populates="delegacao", cascade="all, delete-orphan")


class DelegacaoEventualParticipante(Base):
    __tablename__ = 'delegacao_eventual_participantes'
    
    id = Column(Integer, primary_key=True)
    delegacao_id = Column(Integer, ForeignKey('delegacao_eventual.id'), nullable=False)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=True)
    
    nome = Column(String(200))
    cargo = Column(String(100))
    gp = Column(String(50))  # Grupo Parlamentar
    tipo_participante = Column(String(50))  # 'deputado', 'funcionario', 'externo'
    
    created_at = Column(DateTime, default=func.now())
    
    delegacao = relationship("DelegacaoEventual", back_populates="participantes")
    deputado = relationship("Deputado", backref="delegacoes_eventuais_participacao")


class DelegacaoPermanente(Base):
    __tablename__ = 'delegacao_permanente'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Core fields
    delegacao_id = Column(Integer, unique=True)  # External ID
    nome = Column(Text)
    sessao = Column(String(50))
    data_eleicao = Column(Date)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="delegacoes_permanentes")
    membros = relationship("DelegacaoPermanenteMembro", back_populates="delegacao", cascade="all, delete-orphan")


class DelegacaoPermanenteMembro(Base):
    __tablename__ = 'delegacao_permanente_membros'
    
    id = Column(Integer, primary_key=True)
    delegacao_id = Column(Integer, ForeignKey('delegacao_permanente.id'), nullable=False)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=True)
    
    membro_id = Column(Integer)  # External member ID
    nome = Column(String(200))
    cargo = Column(String(100))
    gp = Column(String(50))  # Grupo Parlamentar
    data_inicio = Column(Date)
    data_fim = Column(Date)
    
    created_at = Column(DateTime, default=func.now())
    
    delegacao = relationship("DelegacaoPermanente", back_populates="membros")
    deputado = relationship("Deputado", backref="delegacoes_permanentes_participacao")


class AtividadeParlamentar(Base):
    __tablename__ = 'atividade_parlamentar'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Core fields
    atividade_id = Column(Integer, unique=True)  # External ID
    tipo = Column(String(100))
    desc_tipo = Column(String(200))
    assunto = Column(Text)
    numero = Column(String(50))
    data_atividade = Column(Date)
    data_entrada = Column(Date)
    data_agendamento_debate = Column(Date)
    tipo_autor = Column(String(100))
    autores_gp = Column(Text)
    observacoes = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="atividades_parlamentares")
    publicacoes = relationship("AtividadeParlamentarPublicacao", back_populates="atividade", cascade="all, delete-orphan")
    votacoes = relationship("AtividadeParlamentarVotacao", back_populates="atividade", cascade="all, delete-orphan")
    eleitos = relationship("AtividadeParlamentarEleito", back_populates="atividade", cascade="all, delete-orphan")
    convidados = relationship("AtividadeParlamentarConvidado", back_populates="atividade", cascade="all, delete-orphan")


class AtividadeParlamentarPublicacao(Base):
    __tablename__ = 'atividade_parlamentar_publicacoes'
    
    id = Column(Integer, primary_key=True)
    atividade_id = Column(Integer, ForeignKey('atividade_parlamentar.id'), nullable=False)
    
    pub_nr = Column(Integer)
    pub_tipo = Column(String(100))
    pub_tp = Column(String(50))
    pub_leg = Column(String(50))
    pub_sl = Column(Integer)
    pub_dt = Column(Date)
    pag = Column(Text)
    url_diario = Column(Text)
    id_pag = Column(Integer)
    id_deb = Column(Integer)
    
    created_at = Column(DateTime, default=func.now())
    
    atividade = relationship("AtividadeParlamentar", back_populates="publicacoes")


class AtividadeParlamentarVotacao(Base):
    __tablename__ = 'atividade_parlamentar_votacoes'
    
    id = Column(Integer, primary_key=True)
    atividade_id = Column(Integer, ForeignKey('atividade_parlamentar.id'), nullable=False)
    
    votacao_id = Column(Integer)
    resultado = Column(String(100))
    reuniao = Column(String(100))
    publicacao = Column(String(200))
    data = Column(Date)
    
    created_at = Column(DateTime, default=func.now())
    
    atividade = relationship("AtividadeParlamentar", back_populates="votacoes")


class AtividadeParlamentarEleito(Base):
    __tablename__ = 'atividade_parlamentar_eleitos'
    
    id = Column(Integer, primary_key=True)
    atividade_id = Column(Integer, ForeignKey('atividade_parlamentar.id'), nullable=False)
    
    nome = Column(String(200))
    cargo = Column(String(100))
    
    created_at = Column(DateTime, default=func.now())
    
    atividade = relationship("AtividadeParlamentar", back_populates="eleitos")


class AtividadeParlamentarConvidado(Base):
    __tablename__ = 'atividade_parlamentar_convidados'
    
    id = Column(Integer, primary_key=True)
    atividade_id = Column(Integer, ForeignKey('atividade_parlamentar.id'), nullable=False)
    
    nome = Column(String(200))
    pais = Column(String(100))
    honra = Column(String(100))
    
    created_at = Column(DateTime, default=func.now())
    
    atividade = relationship("AtividadeParlamentar", back_populates="convidados")


class DebateParlamentar(Base):
    __tablename__ = 'debate_parlamentar'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Core fields
    debate_id = Column(Integer, unique=True)  # External ID
    tipo_debate_desig = Column(String(200))
    data_debate = Column(Date)
    tipo_debate = Column(String(100))
    assunto = Column(Text)
    intervencoes = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="debates_parlamentares")


class RelatorioParlamentar(Base):
    __tablename__ = 'relatorio_parlamentar'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Core fields
    relatorio_id = Column(Integer, unique=True)  # External ID if available
    tipo = Column(String(100))
    assunto = Column(Text)
    data_entrada = Column(Date)
    comissao = Column(String(200))
    entidades_externas = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="relatorios_parlamentares")


# Initiative models
class IniciativaParlamentar(Base):
    __tablename__ = 'iniciativas_detalhadas'
    
    id = Column(Integer, primary_key=True)
    ini_id = Column(Integer, unique=True, nullable=False)  # External ID
    ini_nr = Column(Integer)
    ini_tipo = Column(Text)
    ini_desc_tipo = Column(Text)
    ini_leg = Column(Text)
    ini_sel = Column(Integer)
    data_inicio_leg = Column(Date)
    data_fim_leg = Column(Date)
    ini_titulo = Column(Text)
    ini_texto_subst = Column(Text)
    ini_link_texto = Column(Text)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    updated_at = Column(DateTime, default=func.now, onupdate=func.now)
    
    # Relationships
    legislatura = relationship("Legislatura", backref="iniciativas")
    autores_outros = relationship("IniciativaAutorOutro", back_populates="iniciativa", cascade="all, delete-orphan")
    autores_deputados = relationship("IniciativaAutorDeputado", back_populates="iniciativa", cascade="all, delete-orphan")
    autores_grupos = relationship("IniciativaAutorGrupoParlamentar", back_populates="iniciativa", cascade="all, delete-orphan")
    propostas_alteracao = relationship("IniciativaPropostaAlteracao", back_populates="iniciativa", cascade="all, delete-orphan")
    eventos = relationship("IniciativaEvento", back_populates="iniciativa", cascade="all, delete-orphan")

class IniciativaAutorOutro(Base):
    __tablename__ = 'iniciativas_autores_outros'
    
    id = Column(Integer, primary_key=True)
    iniciativa_id = Column(Integer, ForeignKey('iniciativas_detalhadas.id'), nullable=False)
    sigla = Column(Text)
    nome = Column(Text)
    
    # Relationships
    iniciativa = relationship("IniciativaParlamentar", back_populates="autores_outros")

class IniciativaAutorDeputado(Base):
    __tablename__ = 'iniciativas_autores_deputados'
    
    id = Column(Integer, primary_key=True)
    iniciativa_id = Column(Integer, ForeignKey('iniciativas_detalhadas.id'), nullable=False)
    id_cadastro = Column(Integer)
    nome = Column(Text)
    gp = Column(Text)
    
    # Relationships
    iniciativa = relationship("IniciativaParlamentar", back_populates="autores_deputados")

class IniciativaAutorGrupoParlamentar(Base):
    __tablename__ = 'iniciativas_autores_grupos_parlamentares'
    
    id = Column(Integer, primary_key=True)
    iniciativa_id = Column(Integer, ForeignKey('iniciativas_detalhadas.id'), nullable=False)
    gp = Column(Text)
    
    # Relationships
    iniciativa = relationship("IniciativaParlamentar", back_populates="autores_grupos")

class IniciativaPropostaAlteracao(Base):
    __tablename__ = 'iniciativas_propostas_alteracao'
    
    id = Column(Integer, primary_key=True)
    iniciativa_id = Column(Integer, ForeignKey('iniciativas_detalhadas.id'), nullable=False)
    proposta_id = Column(Integer)
    tipo = Column(Text)
    autor = Column(Text)
    
    # Relationships
    iniciativa = relationship("IniciativaParlamentar", back_populates="propostas_alteracao")
    publicacoes = relationship("IniciativaPropostaAlteracaoPublicacao", back_populates="proposta", cascade="all, delete-orphan")

class IniciativaPropostaAlteracaoPublicacao(Base):
    __tablename__ = 'iniciativas_propostas_alteracao_publicacoes'
    
    id = Column(Integer, primary_key=True)
    proposta_id = Column(Integer, ForeignKey('iniciativas_propostas_alteracao.id'), nullable=False)
    pub_nr = Column(Integer)
    pub_tipo = Column(Text)
    pub_tp = Column(Text)
    pub_leg = Column(Text)
    pub_sl = Column(Integer)
    pub_dt = Column(Date)
    pag = Column(Text)
    id_pag = Column(Integer)
    url_diario = Column(Text)
    
    # Relationships
    proposta = relationship("IniciativaPropostaAlteracao", back_populates="publicacoes")

class IniciativaEvento(Base):
    __tablename__ = 'iniciativas_eventos'
    
    id = Column(Integer, primary_key=True)
    iniciativa_id = Column(Integer, ForeignKey('iniciativas_detalhadas.id'), nullable=False)
    oev_id = Column(Integer)
    data_fase = Column(Date)
    fase = Column(Text)
    evt_id = Column(Integer)
    codigo_fase = Column(Integer)
    obs_fase = Column(Text)
    act_id = Column(Integer)
    oev_text_id = Column(Integer)
    textos_aprovados = Column(Text)
    
    # Relationships
    iniciativa = relationship("IniciativaParlamentar", back_populates="eventos")
    publicacoes = relationship("IniciativaEventoPublicacao", back_populates="evento", cascade="all, delete-orphan")
    votacoes = relationship("IniciativaEventoVotacao", back_populates="evento", cascade="all, delete-orphan")
    comissoes = relationship("IniciativaEventoComissao", back_populates="evento", cascade="all, delete-orphan")
    recursos_gp = relationship("IniciativaEventoRecursoGP", back_populates="evento", cascade="all, delete-orphan")
    iniciativas_conjuntas = relationship("IniciativaConjunta", back_populates="evento", cascade="all, delete-orphan")
    intervencoes_debates = relationship("IniciativaIntervencaoDebate", back_populates="evento", cascade="all, delete-orphan")

class IniciativaEventoPublicacao(Base):
    __tablename__ = 'iniciativas_eventos_publicacoes'
    
    id = Column(Integer, primary_key=True)
    evento_id = Column(Integer, ForeignKey('iniciativas_eventos.id'), nullable=False)
    pub_nr = Column(Integer)
    pub_tipo = Column(Text)
    pub_tp = Column(Text)
    pub_leg = Column(Text)
    pub_sl = Column(Integer)
    pub_dt = Column(Date)
    pag = Column(Text)
    id_pag = Column(Integer)
    url_diario = Column(Text)
    
    # Relationships
    evento = relationship("IniciativaEvento", back_populates="publicacoes")

class IniciativaEventoVotacao(Base):
    __tablename__ = 'iniciativas_eventos_votacoes'
    
    id = Column(Integer, primary_key=True)
    evento_id = Column(Integer, ForeignKey('iniciativas_eventos.id'), nullable=False)
    id_votacao = Column(Integer)
    resultado = Column(Text)
    reuniao = Column(Integer)
    tipo_reuniao = Column(Text)
    detalhe = Column(Text)
    unanime = Column(Text)
    data_votacao = Column(Date)
    
    # Relationships
    evento = relationship("IniciativaEvento", back_populates="votacoes")
    ausencias = relationship("IniciativaVotacaoAusencia", back_populates="votacao", cascade="all, delete-orphan")

class IniciativaVotacaoAusencia(Base):
    __tablename__ = 'iniciativas_votacoes_ausencias'
    
    id = Column(Integer, primary_key=True)
    votacao_id = Column(Integer, ForeignKey('iniciativas_eventos_votacoes.id'), nullable=False)
    grupo_parlamentar = Column(Text)
    
    # Relationships
    votacao = relationship("IniciativaEventoVotacao", back_populates="ausencias")

class IniciativaEventoComissao(Base):
    __tablename__ = 'iniciativas_eventos_comissoes'
    
    id = Column(Integer, primary_key=True)
    evento_id = Column(Integer, ForeignKey('iniciativas_eventos.id'), nullable=False)
    acc_id = Column(Integer)
    numero = Column(Integer)
    id_comissao = Column(Integer)
    nome = Column(Text)
    competente = Column(Text)
    data_distribuicao = Column(Date)
    data_entrada = Column(Date)
    data_agendamento_plenario = Column(Text)
    
    # Relationships
    evento = relationship("IniciativaEvento", back_populates="comissoes")
    publicacoes = relationship("IniciativaComissaoPublicacao", back_populates="comissao", cascade="all, delete-orphan")

class IniciativaComissaoPublicacao(Base):
    __tablename__ = 'iniciativas_comissoes_publicacoes'
    
    id = Column(Integer, primary_key=True)
    comissao_id = Column(Integer, ForeignKey('iniciativas_eventos_comissoes.id'), nullable=False)
    tipo = Column(Text)
    pub_nr = Column(Integer)
    pub_tipo = Column(Text)
    pub_tp = Column(Text)
    pub_leg = Column(Text)
    pub_sl = Column(Integer)
    pub_dt = Column(Date)
    pag = Column(Text)
    id_pag = Column(Integer)
    url_diario = Column(Text)
    
    # Relationships
    comissao = relationship("IniciativaEventoComissao", back_populates="publicacoes")

class IniciativaEventoRecursoGP(Base):
    __tablename__ = 'iniciativas_eventos_recursos_gp'
    
    id = Column(Integer, primary_key=True)
    evento_id = Column(Integer, ForeignKey('iniciativas_eventos.id'), nullable=False)
    grupo_parlamentar = Column(Text)
    
    # Relationships
    evento = relationship("IniciativaEvento", back_populates="recursos_gp")

class IniciativaConjunta(Base):
    __tablename__ = 'iniciativas_conjuntas'
    
    id = Column(Integer, primary_key=True)
    evento_id = Column(Integer, ForeignKey('iniciativas_eventos.id'), nullable=False)
    nr = Column(Integer)
    tipo = Column(Text)
    desc_tipo = Column(Text)
    leg = Column(Text)
    sel = Column(Integer)
    titulo = Column(Text)
    ini_id = Column(Integer)
    
    # Relationships
    evento = relationship("IniciativaEvento", back_populates="iniciativas_conjuntas")

class IniciativaIntervencaoDebate(Base):
    __tablename__ = 'iniciativas_intervencoes_debates'
    
    id = Column(Integer, primary_key=True)
    evento_id = Column(Integer, ForeignKey('iniciativas_eventos.id'), nullable=False)
    data_reuniao_plenaria = Column(Date)
    
    # Relationships
    evento = relationship("IniciativaEvento", back_populates="intervencoes_debates")


class IntervencaoParlamentar(Base):
    __tablename__ = 'intervencao_parlamentar'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Core fields
    intervencao_id = Column(Integer, unique=True)  # External ID
    legislatura_numero = Column(String(50))
    sessao_numero = Column(String(50))
    tipo_intervencao = Column(String(200))
    data_reuniao_plenaria = Column(Date)
    qualidade = Column(String(100))
    fase_sessao = Column(String(100))
    sumario = Column(Text)
    resumo = Column(Text)
    atividade_id = Column(Integer)
    id_debate = Column(Integer)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="intervencoes_parlamentares")
    publicacoes = relationship("IntervencaoPublicacao", back_populates="intervencao", cascade="all, delete-orphan")
    deputados = relationship("IntervencaoDeputado", back_populates="intervencao", cascade="all, delete-orphan")
    membros_governo = relationship("IntervencaoMembroGoverno", back_populates="intervencao", cascade="all, delete-orphan")
    convidados = relationship("IntervencaoConvidado", back_populates="intervencao", cascade="all, delete-orphan")
    atividades_relacionadas = relationship("IntervencaoAtividadeRelacionada", back_populates="intervencao", cascade="all, delete-orphan")
    iniciativas = relationship("IntervencaoIniciativa", back_populates="intervencao", cascade="all, delete-orphan")
    audiovisuais = relationship("IntervencaoAudiovisual", back_populates="intervencao", cascade="all, delete-orphan")


class IntervencaoPublicacao(Base):
    __tablename__ = 'intervencao_publicacoes'
    
    id = Column(Integer, primary_key=True)
    intervencao_id = Column(Integer, ForeignKey('intervencao_parlamentar.id'), nullable=False)
    
    pub_nr = Column(Integer)
    pub_tipo = Column(String(100))
    pub_tp = Column(String(50))
    pub_leg = Column(String(50))
    pub_sl = Column(Integer)
    pub_dt = Column(Date)
    pag = Column(Text)
    id_int = Column(Integer)
    url_diario = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    intervencao = relationship("IntervencaoParlamentar", back_populates="publicacoes")


class IntervencaoDeputado(Base):
    __tablename__ = 'intervencao_deputados'
    
    id = Column(Integer, primary_key=True)
    intervencao_id = Column(Integer, ForeignKey('intervencao_parlamentar.id'), nullable=False)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=True)
    
    id_cadastro = Column(Integer)
    nome = Column(String(200))
    gp = Column(String(50))  # Grupo Parlamentar
    
    created_at = Column(DateTime, default=func.now())
    
    intervencao = relationship("IntervencaoParlamentar", back_populates="deputados")
    deputado = relationship("Deputado", backref="intervencoes_parlamentares")


class IntervencaoMembroGoverno(Base):
    __tablename__ = 'intervencao_membros_governo'
    
    id = Column(Integer, primary_key=True)
    intervencao_id = Column(Integer, ForeignKey('intervencao_parlamentar.id'), nullable=False)
    
    nome = Column(String(200))
    cargo = Column(String(200))
    governo = Column(String(100))
    
    created_at = Column(DateTime, default=func.now())
    
    intervencao = relationship("IntervencaoParlamentar", back_populates="membros_governo")


class IntervencaoConvidado(Base):
    __tablename__ = 'intervencao_convidados'
    
    id = Column(Integer, primary_key=True)
    intervencao_id = Column(Integer, ForeignKey('intervencao_parlamentar.id'), nullable=False)
    
    nome = Column(String(200))
    cargo = Column(String(200))
    
    created_at = Column(DateTime, default=func.now())
    
    intervencao = relationship("IntervencaoParlamentar", back_populates="convidados")


class IntervencaoAtividadeRelacionada(Base):
    __tablename__ = 'intervencao_atividades_relacionadas'
    
    id = Column(Integer, primary_key=True)
    intervencao_id = Column(Integer, ForeignKey('intervencao_parlamentar.id'), nullable=False)
    
    atividade_id = Column(Integer)
    tipo = Column(String(100))
    
    created_at = Column(DateTime, default=func.now())
    
    intervencao = relationship("IntervencaoParlamentar", back_populates="atividades_relacionadas")


class IntervencaoIniciativa(Base):
    __tablename__ = 'intervencao_iniciativas'
    
    id = Column(Integer, primary_key=True)
    intervencao_id = Column(Integer, ForeignKey('intervencao_parlamentar.id'), nullable=False)
    
    iniciativa_id = Column(Integer)
    tipo = Column(String(100))
    numero = Column(String(50))
    fase = Column(String(100))
    
    created_at = Column(DateTime, default=func.now())
    
    intervencao = relationship("IntervencaoParlamentar", back_populates="iniciativas")


class IntervencaoAudiovisual(Base):
    __tablename__ = 'intervencao_audiovisuais'
    
    id = Column(Integer, primary_key=True)
    intervencao_id = Column(Integer, ForeignKey('intervencao_parlamentar.id'), nullable=False)
    
    duracao = Column(String(50))
    assunto = Column(Text)
    url = Column(Text)
    tipo_intervencao = Column(String(200))
    video_url = Column(Text)  # Legacy field
    
    created_at = Column(DateTime, default=func.now())
    
    intervencao = relationship("IntervencaoParlamentar", back_populates="audiovisuais")