"""
SQLAlchemy Models for Portuguese Parliament Database
===================================================

Comprehensive models for all parliamentary data with zero data loss.
Uses MySQL database with proper foreign key constraints and relationships.

Author: Claude
Version: 3.0 - MySQL Implementation
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
    sexo = Column(String(1))  # M/F - cadSexo field
    profissao = Column(String(200))
    data_nascimento = Column(Date)
    naturalidade = Column(String(100))
    estado_civil_cod = Column(String(10))  # cadEstadoCivilCod
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
    cargos = relationship("DepCargo", back_populates="deputado", cascade="all, delete-orphan")
    habilitacoes = relationship("DeputadoHabilitacao", back_populates="deputado", cascade="all, delete-orphan")
    cargos_funcoes = relationship("DeputadoCargoFuncao", back_populates="deputado", cascade="all, delete-orphan")
    titulos = relationship("DeputadoTitulo", back_populates="deputado", cascade="all, delete-orphan")
    condecoracoes = relationship("DeputadoCondecoracao", back_populates="deputado", cascade="all, delete-orphan")
    obras_publicadas = relationship("DeputadoObraPublicada", back_populates="deputado", cascade="all, delete-orphan")
    atividades_orgaos = relationship("DeputadoAtividadeOrgao", back_populates="deputado", cascade="all, delete-orphan")
    mandatos_legislativos = relationship("DeputadoMandatoLegislativo", back_populates="deputado", cascade="all, delete-orphan")
    registo_interesses_v2 = relationship("RegistoInteressesV2", back_populates="deputado", cascade="all, delete-orphan")
    gp_situations = relationship("DeputyGPSituation", back_populates="deputado", cascade="all, delete-orphan")
    situations = relationship("DeputySituation", back_populates="deputado", cascade="all, delete-orphan")


class DepCargo(Base):
    __tablename__ = 'dep_cargos'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputado = relationship("Deputado", back_populates="cargos")
    dados_cargo_deputado = relationship("DadosCargoDeputado", back_populates="dep_cargo", cascade="all, delete-orphan")


class DadosCargoDeputado(Base):
    __tablename__ = 'dados_cargo_deputados'
    
    id = Column(Integer, primary_key=True)
    dep_cargo_id = Column(Integer, ForeignKey('dep_cargos.id'), nullable=False)
    car_des = Column(String(200))  # carDes - Position description
    car_id = Column(Integer)  # carId - Position ID
    car_dt_inicio = Column(Date)  # carDtInicio - Position start date
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    dep_cargo = relationship("DepCargo", back_populates="dados_cargo_deputado")


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
    """Deputy Parliamentary Group Situation - unified model for all contexts"""
    __tablename__ = 'deputy_gp_situations'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    gp_id = Column(Integer)  # Parliamentary Group ID
    gp_sigla = Column(String(20))  # Parliamentary Group acronym/sigla
    gp_dt_inicio = Column(Date)  # Start date of GP membership
    gp_dt_fim = Column(Date)  # End date of GP membership
    composition_context = Column(String(50))  # Context where this GP situation was recorded (ar_board, commission, etc.)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputado = relationship("Deputado", back_populates="gp_situations")
    legislatura = relationship("Legislatura")


class DeputySituation(Base):
    """Deputy Situation - unified model for all contexts (organ composition, activities, etc.)"""
    __tablename__ = 'deputy_situations'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    sio_des = Column(String(200))  # Situation description (e.g., "Renunciou", "Efetivo", etc.)
    sio_tip_mem = Column(String(100))  # Type of membership
    sio_dt_inicio = Column(Date)  # Start date of situation
    sio_dt_fim = Column(Date)  # End date of situation
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputado = relationship("Deputado", back_populates="situations")
    legislatura = relationship("Legislatura")


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
    hora_inicio = Column(Text)  # TIME field stored as TEXT
    hora_fim = Column(Text)     # TIME field stored as TEXT
    evento_dia_inteiro = Column(Boolean, default=False)
    titulo = Column(Text, nullable=False)
    subtitulo = Column(Text)
    descricao = Column(Text)
    local_evento = Column(Text)
    link_externo = Column(Text)
    pos_plenario = Column(Boolean, default=False)
    estado = Column(Text, default='agendado')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    secao_parlamentar_id = Column(Integer, ForeignKey('secoes_parlamentares.id'))
    tema_parlamentar_id = Column(Integer, ForeignKey('temas_parlamentares.id'))
    
    __table_args__ = (
        Index('idx_agenda_data', 'data_evento'),
        Index('idx_agenda_legislatura_data', 'legislatura_id', 'data_evento'),
        # Index('idx_agenda_grupo', 'grupo_parlamentar'),  # Removed - TEXT column cannot be indexed without key length
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
    sigla_orgao = Column(String(50))
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
    sigla_orgao = Column(String(50))
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
    sigla_orgao = Column(String(50))
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
    sigla_orgao = Column(String(50))
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
    sigla_orgao = Column(String(50))
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
    sigla_orgao = Column(String(50))
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
    sigla_orgao = Column(String(50))
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
    sigla_orgao = Column(String(50))
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
    sigla_orgao = Column(String(50))
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
    
    # Extended meeting fields (III Legislature)
    reu_id = Column(Integer)  # Meeting ID from XML
    reu_numero = Column(Integer)  # Meeting number
    reu_data_hora = Column(String(50))  # Combined date/time string
    reu_final_plenario = Column(Boolean)  # Final plenary indicator
    reu_tir_des = Column(String(200))  # Meeting type description
    leg_des = Column(String(50))  # Legislature description
    sel_numero = Column(String(50))  # Session number
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    commission = relationship("Commission", back_populates="meetings")
    work_group = relationship("WorkGroup", back_populates="meetings")
    permanent_committee = relationship("PermanentCommittee", back_populates="meetings")
    sub_committee = relationship("SubCommittee", back_populates="meetings")
    attendances = relationship("MeetingAttendance", back_populates="meeting", cascade="all, delete-orphan")


class MeetingAttendance(Base):
    """Meeting attendance data (Presencas) - tracks deputy attendance at meetings"""
    __tablename__ = 'meeting_attendances'
    
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey('organ_meetings.id'), nullable=False)
    
    # Deputy information
    dep_id = Column(Integer)
    dep_cad_id = Column(Integer)
    dep_nome_parlamentar = Column(String(200))
    
    # Attendance details
    pres_tipo = Column(String(50))  # Presence type (present, absent, etc.)
    pres_justificacao = Column(Text)  # Justification for absence
    dt_reuniao = Column(Date)  # Meeting date for this attendance record
    tipo_reuniao = Column(String(100))  # Type of meeting
    # Structured attendance quality fields
    sigla_qualidade_presenca = Column(String(100))  # Presence quality designation
    sigla_grupo = Column(String(50))  # Group designation if applicable  
    sigla_falta = Column(String(50))  # Absence designation if applicable
    motivo_falta = Column(Text)  # Reason for absence - XIII Legislature
    observacoes = Column(Text)  # Additional free-text observations
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    meeting = relationship("OrganMeeting", back_populates="attendances")


class DeputyVideo(Base):
    """Deputy video data - stores video links associated with deputies"""
    __tablename__ = 'deputy_videos'
    
    id = Column(Integer, primary_key=True)
    
    # Deputy information
    dep_id = Column(Integer)
    dep_cad_id = Column(Integer)
    dep_nome_parlamentar = Column(String(200))
    
    # Video details
    url = Column(Text)  # Video URL
    tipo = Column(String(100))  # Video type/category
    
    # Context - which organ/composition this video is associated with
    organ_type = Column(String(50))  # Type of organ (Plenario, Commission, etc.)
    organ_id = Column(Integer)  # ID of the specific organ
    legislatura_numero = Column(String(20))  # Legislature designation
    
    created_at = Column(DateTime, default=func.now())


# Historical Composition Models
class AdministrativeCouncilHistoricalComposition(Base):
    __tablename__ = 'administrative_council_historical_compositions'
    
    id = Column(Integer, primary_key=True)
    council_id = Column(Integer, ForeignKey('administrative_councils.id'), nullable=False)
    leg_des = Column(String(20))
    dep_id = Column(Integer)
    dep_cad_id = Column(Integer)
    dep_nome_parlamentar = Column(String(200))
    dep_nome_completo = Column(String(200))
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
    dep_nome_completo = Column(String(200))
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
    dep_nome_completo = Column(String(200))  # IX Legislature field
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
    dep_nome_completo = Column(String(200))  # IX Legislature field
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
    dep_nome_completo = Column(String(200))  # VIII Legislature field
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
    dep_nome_completo = Column(String(200))  # VI Legislature field
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
    dep_nome_completo = Column(String(200))  # IX Legislature field
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
    file_url = Column(String(1000), nullable=False)
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
        # Index('idx_import_status_url', 'file_url'),  # Removed - VARCHAR(1000) too long for MySQL index
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
    intervencoes = relationship("ActividadeIntervencao", back_populates="actividade_out", cascade="all, delete-orphan")
    
    # IX Legislature relationships
    atividades_parlamentares = relationship("ActividadesParlamentares", back_populates="actividade_out", cascade="all, delete-orphan")
    grupos_parlamentares_amizade = relationship("GruposParlamentaresAmizade", back_populates="actividade_out", cascade="all, delete-orphan")
    delegacoes_permanentes = relationship("DelegacoesPermanentes", back_populates="actividade_out", cascade="all, delete-orphan")
    delegacoes_eventuais = relationship("DelegacoesEventuais", back_populates="actividade_out", cascade="all, delete-orphan")
    requerimentos_ativ_dep = relationship("RequerimentosAtivDep", back_populates="actividade_out", cascade="all, delete-orphan")
    subcomissoes_grupos_trabalho = relationship("SubComissoesGruposTrabalho", back_populates="actividade_out", cascade="all, delete-orphan")
    relatores_peticoes = relationship("RelatoresPeticoes", back_populates="actividade_out", cascade="all, delete-orphan")
    relatores_iniciativas = relationship("RelatoresIniciativas", back_populates="actividade_out", cascade="all, delete-orphan")
    comissoes = relationship("Comissoes", back_populates="actividade_out", cascade="all, delete-orphan")
    
    # I Legislature relationships
    autores_pareceres_inc_imu = relationship("AutoresPareceresIncImu", back_populates="actividade_out", cascade="all, delete-orphan")
    relatores_ini_europeias = relationship("RelatoresIniEuropeias", back_populates="actividade_out", cascade="all, delete-orphan")
    parlamento_jovens = relationship("ParlamentoJovens", back_populates="actividade_out", cascade="all, delete-orphan")
    eventos = relationship("Eventos", back_populates="actividade_out", cascade="all, delete-orphan")


class DadosLegisDeputado(Base):
    __tablename__ = 'dados_legis_deputados'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    nome = Column(String(200))  # Nome field
    dpl_grpar = Column(String(100))  # Dpl_grpar field
    dpl_lg = Column(String(100))  # Dpl_lg field - NEW FIELD
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
    evento_id = Column(Integer, ForeignKey('eventos.id'), nullable=True)  # I Legislature Events
    deslocacao_id = Column(Integer, ForeignKey('deslocacoes.id'), nullable=True)  # I Legislature Displacements
    
    # IX Legislature additional fields
    act_id = Column(Integer)  # ActId
    act_as = Column(Text)  # ActAs - subject/title
    act_dtent = Column(String(50))  # ActDtent - entry date
    acc_dtaud = Column(String(50))  # AccDtaud - hearing date
    act_tp = Column(String(10))  # ActTp - activity type
    act_tpdesc = Column(String(200))  # ActTpdesc - type description
    act_nr = Column(String(50))  # ActNr - activity number
    act_lg = Column(String(20))  # ActLg - legislature
    act_loc = Column(String(500))  # ActLoc - activity location (I Legislature Events/Deslocacoes)
    act_dtdes1 = Column(String(50))  # ActDtdes1 - first displacement date
    act_dtdes2 = Column(String(50))  # ActDtdes2 - second displacement date
    act_dtent = Column(String(50))  # ActDtent - entry date (for Events section)
    act_tpdesc = Column(String(200))  # ActTpdesc - activity type description (for Events)
    act_sl = Column(String(20))  # ActSl - session legislature
    tev_tp = Column(String(100))  # TevTp - event type
    nome_entidade_externa = Column(Text)  # NomeEntidadeExterna
    cms_no = Column(String(500))  # CmsNo - committee name
    cms_ab = Column(String(20))  # CmsAb - committee abbreviation
    
    created_at = Column(DateTime, default=func.now())
    
    audiencia = relationship("ActividadeAudiencia", back_populates="actividades_comissao")
    audicao = relationship("ActividadeAudicao", back_populates="actividades_comissao")
    evento = relationship("Eventos", back_populates="actividades_comissao")
    deslocacao = relationship("Deslocacoes", back_populates="actividades_comissao")


class ActividadeIntervencao(Base):
    __tablename__ = 'actividade_intervencoes'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    actividade_out = relationship("ActividadeOut", back_populates="intervencoes")
    intervencoes_out = relationship("ActividadeIntervencaoOut", back_populates="actividade_intervencao", cascade="all, delete-orphan")


class ActividadeIntervencaoOut(Base):
    __tablename__ = 'actividade_intervencoes_out'
    
    id = Column(Integer, primary_key=True)
    actividade_intervencao_id = Column(Integer, ForeignKey('actividade_intervencoes.id'), nullable=False)
    
    # IntervencoesOut fields from XML
    int_id = Column(Integer)  # IntId
    int_su = Column(Text)  # IntSu - Summary
    int_te = Column(Text)  # IntTe - Intervention Text
    pub_dar = Column(String(200))  # PubDar - Publication Diary
    pub_dtreu = Column(Date)  # PubDtreu - Publication Date
    pub_lg = Column(String(50))  # PubLg - Publication Legislature
    pub_nr = Column(Integer)  # PubNr - Publication Number
    pub_tp = Column(String(100))  # PubTp - Publication Type
    pub_sl = Column(String(200))  # PubSl - Publication Series/Supplement
    tin_ds = Column(String(200))  # TinDs - Intervention Type Description
    
    created_at = Column(DateTime, default=func.now())
    
    actividade_intervencao = relationship("ActividadeIntervencao", back_populates="intervencoes_out")


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
    outros_subscritores = Column(Text)  # OutrosSubscritores field
    textos_aprovados = Column(Text)  # Missing approved texts field
    resultado_votacao_pontos = Column(Text)  # Missing ResultadoVotacaoPontos field
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
    supl = Column(String(100))  # Missing supplement field
    obs = Column(Text)  # Missing observations field
    
    created_at = Column(DateTime, default=func.now())
    
    atividade = relationship("AtividadeParlamentar", back_populates="publicacoes")


class AtividadeParlamentarVotacao(Base):
    __tablename__ = 'atividade_parlamentar_votacoes'
    
    id = Column(Integer, primary_key=True)
    atividade_id = Column(Integer, ForeignKey('atividade_parlamentar.id'), nullable=False)
    
    votacao_id = Column(Integer)
    resultado = Column(String(100))
    unanime = Column(Boolean)  # Missing unanimous field
    reuniao = Column(String(100))
    publicacao = Column(String(200))
    data = Column(Date)
    detalhe = Column(Text)  # Missing voting detail field
    descricao = Column(Text)  # Missing voting description field
    ausencias = Column(Text)  # Missing voting absences field
    
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
    sessao = Column(Integer)  # Missing session field
    assunto = Column(Text)
    tipo_autor = Column(String(100))  # Missing TipoAutor field
    autores_deputados = Column(Text)  # Missing authors field
    autores_gp = Column(Text)  # Missing AutoresGP field
    data_entrada = Column(Date)  # Missing DataEntrada field
    intervencoes = Column(Text)
    observacoes = Column(Text)  # Missing Observacoes field for debates
    artigo = Column(Text)  # Artigo field for debates
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="debates_parlamentares")
    publicacoes = relationship("DebateParlamentarPublicacao", back_populates="debate", cascade="all, delete-orphan")


class DebateParlamentarPublicacao(Base):
    __tablename__ = 'debate_parlamentar_publicacoes'
    
    id = Column(Integer, primary_key=True)
    debate_id = Column(Integer, ForeignKey('debate_parlamentar.id'), nullable=False)
    
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
    supl = Column(String(100))  # Missing supplement field
    obs = Column(Text)  # Observations field
    
    created_at = Column(DateTime, default=func.now())
    
    debate = relationship("DebateParlamentar", back_populates="publicacoes")


class RelatorioParlamentar(Base):
    __tablename__ = 'relatorio_parlamentar'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Core fields
    relatorio_id = Column(Integer, unique=True)  # External ID if available
    tipo = Column(String(100))
    desc_tipo = Column(String(200))  # Missing DescTipo field
    assunto = Column(Text)
    sessao = Column(Integer)  # Missing session field
    data_entrada = Column(Date)
    data_agendamento_debate = Column(Date)  # Missing DataAgendamentoDebate field
    comissao = Column(String(200))
    entidades_externas = Column(Text)
    textos_aprovados = Column(Text)  # Missing TextosAprovados field for reports
    observacoes = Column(Text)  # Missing Observacoes field
    
    # Additional XIII Legislature fields
    data_parecer_utao = Column(Date)  # DataParecerUTAO field
    data_pedido_parecer = Column(Date)  # DataPedidoParecer field
    membros_governo = Column(Text)  # MembrosGoverno field
    audicoes = Column(Text)  # Audicoes field
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="relatorios_parlamentares")
    publicacoes = relationship("RelatorioParlamentarPublicacao", back_populates="relatorio", cascade="all, delete-orphan")
    votacoes = relationship("RelatorioParlamentarVotacao", back_populates="relatorio", cascade="all, delete-orphan")
    relatores = relationship("RelatorioParlamentarRelator", back_populates="relatorio", cascade="all, delete-orphan")
    documentos = relationship("RelatorioParlamentarDocumento", back_populates="relatorio", cascade="all, delete-orphan")
    links = relationship("RelatorioParlamentarLink", back_populates="relatorio", cascade="all, delete-orphan")
    comissoes_opinioes = relationship("RelatorioParlamentarComissaoOpiniao", back_populates="relatorio", cascade="all, delete-orphan")


class RelatorioParlamentarPublicacao(Base):
    __tablename__ = 'relatorio_parlamentar_publicacoes'
    
    id = Column(Integer, primary_key=True)
    relatorio_id = Column(Integer, ForeignKey('relatorio_parlamentar.id'), nullable=False)
    
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
    supl = Column(String(100))  # Missing supplement field
    obs = Column(Text)  # Observations field
    
    created_at = Column(DateTime, default=func.now())
    
    relatorio = relationship("RelatorioParlamentar", back_populates="publicacoes")


class RelatorioParlamentarVotacao(Base):
    __tablename__ = 'relatorio_parlamentar_votacoes'
    
    id = Column(Integer, primary_key=True)
    relatorio_id = Column(Integer, ForeignKey('relatorio_parlamentar.id'), nullable=False)
    
    votacao_id = Column(Integer)
    id_votacao = Column(Integer)  # VotacaoRelatorio.id field
    resultado = Column(String(100))
    unanime = Column(Boolean)  # VotacaoRelatorio.unanime field
    descricao = Column(Text)  # VotacaoRelatorio.descricao
    reuniao = Column(String(100))
    data = Column(Date)
    
    created_at = Column(DateTime, default=func.now())
    
    relatorio = relationship("RelatorioParlamentar", back_populates="votacoes")
    publicacao = relationship("RelatorioParlamentarVotacaoPublicacao", back_populates="votacao", cascade="all, delete-orphan")


class RelatorioParlamentarVotacaoPublicacao(Base):
    __tablename__ = 'relatorio_parlamentar_votacao_publicacoes'
    
    id = Column(Integer, primary_key=True)
    votacao_id = Column(Integer, ForeignKey('relatorio_parlamentar_votacoes.id'), nullable=False)
    
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
    obs = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    votacao = relationship("RelatorioParlamentarVotacao", back_populates="publicacao")


class RelatorioParlamentarRelator(Base):
    __tablename__ = 'relatorio_parlamentar_relatores'
    
    id = Column(Integer, primary_key=True)
    relatorio_id = Column(Integer, ForeignKey('relatorio_parlamentar.id'), nullable=False)
    
    relator_id = Column(Integer)  # Relatores.pt_gov_ar_objectos_RelatoresOut.id
    nome = Column(String(200))  # Relatores.pt_gov_ar_objectos_RelatoresOut.nome
    gp = Column(String(100))    # Relatores.pt_gov_ar_objectos_RelatoresOut.gp
    
    created_at = Column(DateTime, default=func.now())
    
    relatorio = relationship("RelatorioParlamentar", back_populates="relatores")


class RelatorioParlamentarDocumento(Base):
    __tablename__ = 'relatorio_parlamentar_documentos'
    
    id = Column(Integer, primary_key=True)
    relatorio_id = Column(Integer, ForeignKey('relatorio_parlamentar.id'), nullable=False)
    
    # Document fields from Documentos.DocsOut
    data_documento = Column(Date)
    tipo_documento = Column(String(200))
    titulo_documento = Column(Text)
    url = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    relatorio = relationship("RelatorioParlamentar", back_populates="documentos")


class RelatorioParlamentarLink(Base):
    __tablename__ = 'relatorio_parlamentar_links'
    
    id = Column(Integer, primary_key=True)
    relatorio_id = Column(Integer, ForeignKey('relatorio_parlamentar.id'), nullable=False)
    
    # Link fields from Links.DocsOut
    data_documento = Column(Date)
    tipo_documento = Column(String(200))
    titulo_documento = Column(Text)
    url = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    relatorio = relationship("RelatorioParlamentar", back_populates="links")


class EventoParlamentar(Base):
    __tablename__ = 'eventos_parlamentares'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Event fields from Eventos.DadosEventosComissaoOut
    id_evento = Column(Integer, nullable=False)
    data = Column(Date)
    designacao = Column(Text)
    local_evento = Column(String(500))
    sessao_legislativa = Column(Integer)
    tipo_evento = Column(String(200))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    legislatura = relationship("Legislatura")
    
    # Indexes
    __table_args__ = (
        Index('idx_evento_parlamentar_id_evento', 'id_evento'),
        Index('idx_evento_parlamentar_legislatura', 'legislatura_id'),
        Index('idx_evento_parlamentar_data', 'data'),
        UniqueConstraint('id_evento', 'legislatura_id', name='uq_evento_parlamentar_id_leg'),
    )


class DeslocacaoParlamentar(Base):
    __tablename__ = 'deslocacoes_parlamentares'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Displacement fields from Deslocacoes.DadosDeslocacoesComissaoOut
    id_deslocacao = Column(Integer, nullable=False)
    data_ini = Column(Date)
    data_fim = Column(Date)
    designacao = Column(Text)
    local_evento = Column(String(500))
    sessao_legislativa = Column(Integer)
    tipo = Column(String(200))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    legislatura = relationship("Legislatura")
    
    # Indexes
    __table_args__ = (
        Index('idx_deslocacao_parlamentar_id_deslocacao', 'id_deslocacao'),
        Index('idx_deslocacao_parlamentar_legislatura', 'legislatura_id'),
        Index('idx_deslocacao_parlamentar_data_ini', 'data_ini'),
        UniqueConstraint('id_deslocacao', 'legislatura_id', name='uq_deslocacao_parlamentar_id_leg'),
    )


class RelatorioParlamentarComissaoOpiniao(Base):
    __tablename__ = 'relatorio_parlamentar_comissoes_opinioes'
    
    id = Column(Integer, primary_key=True)
    relatorio_parlamentar_id = Column(Integer, ForeignKey('relatorio_parlamentar.id'), nullable=False)
    
    # Commission Opinion fields from ParecerComissao.AtividadeComissoesOut
    comissao_id = Column(Integer)  # AtividadeComissoesOut.Id
    nome = Column(String(500))     # AtividadeComissoesOut.Nome
    numero = Column(Integer)       # AtividadeComissoesOut.Numero
    sigla = Column(String(50))     # AtividadeComissoesOut.Sigla
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    relatorio = relationship("RelatorioParlamentar", back_populates="comissoes_opinioes")
    documentos = relationship("RelatorioParlamentarComissaoDocumento", back_populates="comissao_opiniao")
    relatores = relationship("RelatorioParlamentarComissaoRelator", back_populates="comissao_opiniao")


class RelatorioParlamentarComissaoDocumento(Base):
    __tablename__ = 'relatorio_parlamentar_comissao_documentos'
    
    id = Column(Integer, primary_key=True)
    comissao_opiniao_id = Column(Integer, ForeignKey('relatorio_parlamentar_comissoes_opinioes.id'), nullable=False)
    
    # Document fields from ParecerComissao.AtividadeComissoesOut.Documentos.pt_gov_ar_objectos_DocsOut
    url = Column(Text)
    data_documento = Column(Date)
    publicar_internet = Column(Boolean)
    tipo_documento = Column(String(200))
    titulo_documento = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    comissao_opiniao = relationship("RelatorioParlamentarComissaoOpiniao", back_populates="documentos")


class RelatorioParlamentarComissaoRelator(Base):
    __tablename__ = 'relatorio_parlamentar_comissao_relatores'
    
    id = Column(Integer, primary_key=True)
    comissao_opiniao_id = Column(Integer, ForeignKey('relatorio_parlamentar_comissoes_opinioes.id'), nullable=False)
    
    # Relator fields from ParecerComissao.AtividadeComissoesOut.Relatores.pt_gov_ar_objectos_RelatoresOut
    relator_id = Column(Integer)
    nome = Column(String(200))
    gp = Column(String(100))
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    comissao_opiniao = relationship("RelatorioParlamentarComissaoOpiniao", back_populates="relatores")


class RelatorioParlamentarIniciativaConjunta(Base):
    __tablename__ = 'relatorio_parlamentar_iniciativas_conjuntas'
    
    id = Column(Integer, primary_key=True)
    relatorio_id = Column(Integer, ForeignKey('relatorio_parlamentar.id'), nullable=False)
    
    # Joint Initiative fields from IniciativasConjuntas.pt_gov_ar_objectos_iniciativas_DiscussaoConjuntaOut
    iniciativa_id = Column(Integer)  # id field
    tipo = Column(String(200))       # tipo field
    desc_tipo = Column(String(500))  # descTipo field
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    relatorio = relationship("RelatorioParlamentar", backref="iniciativas_conjuntas")


class AudicoesParlamentares(Base):
    __tablename__ = 'audicoes_parlamentares'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'))
    
    id_audicao = Column(Integer)  # IDAudicao
    numero_audicao = Column(String(100))  # NumeroAudicao field
    sessao_legislativa = Column(String(100))  # SessaoLegislativa field
    assunto = Column(Text)
    data_audicao = Column(Date)
    data = Column(Date)  # Data field (alternative date format)
    comissao = Column(String(200))
    tipo_audicao = Column(String(100))
    entidades = Column(Text)  # Entidades field
    observacoes = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="audicoes_parlamentares")


class AudienciasParlamentares(Base):
    __tablename__ = 'audiencias_parlamentares'
    
    id = Column(Integer, primary_key=True)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'))
    
    id_audiencia = Column(Integer)  # IDAudiencia field
    numero_audiencia = Column(Integer)  # NumeroAudiencia
    sessao_legislativa = Column(String(100))  # SessaoLegislativa field
    assunto = Column(Text)
    data_audiencia = Column(Date)
    data = Column(Date)  # Data field (alternative date format)
    comissao = Column(String(200))
    concedida = Column(Boolean)  # Concedida
    tipo_audiencia = Column(String(100))
    entidades = Column(Text)  # Entidades field
    observacoes = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    legislatura = relationship("Legislatura", backref="audiencias_parlamentares")


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


# Petition models
class PeticaoParlamentar(Base):
    __tablename__ = 'peticoes_detalhadas'
    
    id = Column(Integer, primary_key=True)
    pet_id = Column(Integer, unique=True, nullable=False)  # External ID
    pet_nr = Column(Integer)
    pet_leg = Column(Text)
    pet_sel = Column(Integer)
    pet_assunto = Column(Text)
    pet_situacao = Column(Text)
    pet_nr_assinaturas = Column(Integer)
    pet_data_entrada = Column(Date)
    pet_atividade_id = Column(Integer)
    pet_autor = Column(Text)
    data_debate = Column(Date)
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    updated_at = Column(DateTime, default=func.now, onupdate=func.now)
    
    # Relationships
    legislatura = relationship("Legislatura", backref="peticoes")
    publicacoes = relationship("PeticaoPublicacao", back_populates="peticao", cascade="all, delete-orphan")
    comissoes = relationship("PeticaoComissao", back_populates="peticao", cascade="all, delete-orphan")
    documentos = relationship("PeticaoDocumento", back_populates="peticao", cascade="all, delete-orphan")
    intervencoes = relationship("PeticaoIntervencao", back_populates="peticao", cascade="all, delete-orphan")

class PeticaoPublicacao(Base):
    __tablename__ = 'peticoes_publicacoes'
    
    id = Column(Integer, primary_key=True)
    peticao_id = Column(Integer, ForeignKey('peticoes_detalhadas.id'), nullable=False)
    tipo = Column(Text)  # PublicacaoPeticao or PublicacaoDebate
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
    peticao = relationship("PeticaoParlamentar", back_populates="publicacoes")

class PeticaoComissao(Base):
    __tablename__ = 'peticoes_comissoes'
    
    id = Column(Integer, primary_key=True)
    peticao_id = Column(Integer, ForeignKey('peticoes_detalhadas.id'), nullable=False)
    legislatura = Column(Text)
    numero = Column(Integer)
    id_comissao = Column(Integer)
    nome = Column(Text)
    admissibilidade = Column(Text)
    data_admissibilidade = Column(Date)
    data_envio_par = Column(Date)
    data_arquivo = Column(Date)
    situacao = Column(Text)
    data_reaberta = Column(Date)
    data_baixa_comissao = Column(Date)
    transitada = Column(Text)
    
    # Relationships
    peticao = relationship("PeticaoParlamentar", back_populates="comissoes")
    relatores = relationship("PeticaoRelator", back_populates="comissao", cascade="all, delete-orphan")
    relatorios_finais = relationship("PeticaoRelatorioFinal", back_populates="comissao", cascade="all, delete-orphan")
    documentos = relationship("PeticaoDocumento", back_populates="comissao_peticao", cascade="all, delete-orphan")

class PeticaoRelator(Base):
    __tablename__ = 'peticoes_relatores'
    
    id = Column(Integer, primary_key=True)
    comissao_peticao_id = Column(Integer, ForeignKey('peticoes_comissoes.id'), nullable=False)
    relator_id = Column(Integer)
    nome = Column(Text)
    gp = Column(Text)
    data_nomeacao = Column(Date)
    data_cessacao = Column(Date)
    
    # Relationships
    comissao = relationship("PeticaoComissao", back_populates="relatores")

class PeticaoRelatorioFinal(Base):
    __tablename__ = 'peticoes_relatorios_finais'
    
    id = Column(Integer, primary_key=True)
    comissao_peticao_id = Column(Integer, ForeignKey('peticoes_comissoes.id'), nullable=False)
    data_relatorio = Column(Date)
    votacao = Column(Text)
    relatorio_final_id = Column(Text)
    
    # Relationships
    comissao = relationship("PeticaoComissao", back_populates="relatorios_finais")

class PeticaoDocumento(Base):
    __tablename__ = 'peticoes_documentos'
    
    id = Column(Integer, primary_key=True)
    peticao_id = Column(Integer, ForeignKey('peticoes_detalhadas.id'), nullable=True)
    comissao_peticao_id = Column(Integer, ForeignKey('peticoes_comissoes.id'), nullable=True)
    tipo_documento_categoria = Column(Text)
    titulo_documento = Column(Text)
    data_documento = Column(Date)
    tipo_documento = Column(Text)
    url = Column(Text)
    
    # Relationships
    peticao = relationship("PeticaoParlamentar", back_populates="documentos")
    comissao_peticao = relationship("PeticaoComissao", back_populates="documentos")

class PeticaoIntervencao(Base):
    __tablename__ = 'peticoes_intervencoes'
    
    id = Column(Integer, primary_key=True)
    peticao_id = Column(Integer, ForeignKey('peticoes_detalhadas.id'), nullable=False)
    data_reuniao_plenaria = Column(Date)
    
    # Relationships
    peticao = relationship("PeticaoParlamentar", back_populates="intervencoes")
    oradores = relationship("PeticaoOrador", back_populates="intervencao", cascade="all, delete-orphan")

class PeticaoOrador(Base):
    __tablename__ = 'peticoes_oradores'
    
    id = Column(Integer, primary_key=True)
    intervencao_id = Column(Integer, ForeignKey('peticoes_intervencoes.id'), nullable=False)
    fase_sessao = Column(Text)
    sumario = Column(Text)
    convidados = Column(Text)
    membros_governo = Column(Text)
    
    # Relationships
    intervencao = relationship("PeticaoIntervencao", back_populates="oradores")
    publicacoes = relationship("PeticaoOradorPublicacao", back_populates="orador", cascade="all, delete-orphan")

class PeticaoOradorPublicacao(Base):
    __tablename__ = 'peticoes_oradores_publicacoes'
    
    id = Column(Integer, primary_key=True)
    orador_id = Column(Integer, ForeignKey('peticoes_oradores.id'), nullable=False)
    pub_nr = Column(Integer)
    pub_tipo = Column(Text)
    pub_tp = Column(Text)
    pub_leg = Column(Text)
    pub_sl = Column(Integer)
    pub_dt = Column(Date)
    pag = Column(Text)
    id_int = Column(Integer)
    url_diario = Column(Text)
    
    # Relationships
    orador = relationship("PeticaoOrador", back_populates="publicacoes")


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


# =====================================================
# ORÇAMENTO E CONTAS DE GERÊNCIA
# =====================================================

class OrcamentoContasGerencia(Base):
    __tablename__ = 'orcamento_contas_gerencia'
    
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, nullable=False)  # id field from XML
    legislatura_id = Column(Integer, ForeignKey('legislaturas.id'), nullable=False)
    
    # Core fields
    tipo = Column(String(100), nullable=False)  # "Orçamento da A.R." or "Conta Gerência"
    tp = Column(String(10), nullable=False)  # "OAR" or "CGE" 
    titulo = Column(Text, nullable=False)  # Full title/description
    ano = Column(Integer, nullable=False)  # Year
    leg = Column(String(20), nullable=False)  # Legislature code (V, XI, etc.)
    sl = Column(Integer, nullable=False)  # Session number
    
    # Optional date fields
    dt_aprovacao_ca = Column(Date)  # dtAprovacaoCA - approval date
    dt_agendamento = Column(Date)  # dtAgendamento - scheduling date
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    legislatura = relationship("Legislatura")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_orcamento_gerencia_entry_id', 'entry_id'),
        Index('idx_orcamento_gerencia_legislatura', 'legislatura_id'),
        Index('idx_orcamento_gerencia_tipo', 'tipo'),
        Index('idx_orcamento_gerencia_ano', 'ano'),
        UniqueConstraint('entry_id', 'legislatura_id', name='uq_orcamento_gerencia_entry_leg'),
    )


# =====================================================
# IX LEGISLATURE COMPREHENSIVE MODELS
# =====================================================

class ActividadesParlamentares(Base):
    """Parliamentary Activities - ActP section"""
    __tablename__ = 'atividades_parlamentares'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    atividades = relationship("ActividadesParlamentaresOut", back_populates="atividades_parlamentares", cascade="all, delete-orphan")


class ActividadesParlamentaresOut(Base):
    """Individual Parliamentary Activities"""
    __tablename__ = 'atividades_parlamentares_out'
    
    id = Column(Integer, primary_key=True)
    atividades_parlamentares_id = Column(Integer, ForeignKey('atividades_parlamentares.id'), nullable=False)
    
    # Core fields from XML
    act_id = Column(Integer)  # ActId
    act_nr = Column(String(50))  # ActNr
    act_tp = Column(String(10))  # ActTp
    act_tpdesc = Column(String(200))  # ActTpdesc
    act_sel_lg = Column(String(20))  # ActSelLg
    act_sel_nr = Column(String(20))  # ActSelNr
    act_dtent = Column(String(50))  # ActDtent - entry date as string
    act_dtdeb = Column(DateTime)  # ActDtdeb - debate date
    act_as = Column(Text)  # ActAs - subject/title
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    atividades_parlamentares = relationship("ActividadesParlamentares", back_populates="atividades")


class GruposParlamentaresAmizade(Base):
    """Parliamentary Friendship Groups - Gpa section"""
    __tablename__ = 'grupos_parlamentares_amizade'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    grupos = relationship("GruposParlamentaresAmizadeOut", back_populates="grupos_parlamentares_amizade", cascade="all, delete-orphan")


class GruposParlamentaresAmizadeOut(Base):
    """Individual Friendship Groups"""
    __tablename__ = 'grupos_parlamentares_amizade_out'
    
    id = Column(Integer, primary_key=True)
    grupos_parlamentares_amizade_id = Column(Integer, ForeignKey('grupos_parlamentares_amizade.id'), nullable=False)
    
    # Core fields from XML
    gpl_id = Column(Integer)  # GplId - group ID
    gpl_no = Column(String(500))  # GplNo - group name
    gpl_sel_lg = Column(String(20))  # GplSelLg - group session legislature
    cga_crg = Column(String(200))  # CgaCrg - group charge/responsibility
    cga_dtini = Column(String(50))  # CgaDtini - group start date
    cga_dtfim = Column(String(50))  # CgaDtfim - group end date
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    grupos_parlamentares_amizade = relationship("GruposParlamentaresAmizade", back_populates="grupos")


class DelegacoesPermanentes(Base):
    """Permanent Delegations - DlP section"""
    __tablename__ = 'delegacoes_permanentes'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    delegacoes = relationship("DelegacoesPermanentesOut", back_populates="delegacoes_permanentes", cascade="all, delete-orphan")


class DelegacoesPermanentesOut(Base):
    """Individual Permanent Delegations"""
    __tablename__ = 'delegacoes_permanentes_out'
    
    id = Column(Integer, primary_key=True)
    delegacoes_permanentes_id = Column(Integer, ForeignKey('delegacoes_permanentes.id'), nullable=False)
    
    # Core fields from XML
    dep_id = Column(Integer)  # DepId
    dep_no = Column(String(500))  # DepNo - delegation name
    dep_sel_lg = Column(String(20))  # DepSelLg - delegation session legislature
    dep_sel_nr = Column(String(20))  # DepSelNr - delegation session number
    cde_crg = Column(String(200))  # CdeCrg - charge/responsibility
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    delegacoes_permanentes = relationship("DelegacoesPermanentes", back_populates="delegacoes")
    reunioes = relationship("ReunioesDelegacoesPermanentes", back_populates="delegacoes_permanentes_out", cascade="all, delete-orphan")


class DelegacoesEventuais(Base):
    """Occasional Delegations - DlE section"""
    __tablename__ = 'delegacoes_eventuais'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    delegacoes = relationship("DelegacoesEventuaisOut", back_populates="delegacoes_eventuais", cascade="all, delete-orphan")


class DelegacoesEventuaisOut(Base):
    """Individual Occasional Delegations"""
    __tablename__ = 'delegacoes_eventuais_out'
    
    id = Column(Integer, primary_key=True)
    delegacoes_eventuais_id = Column(Integer, ForeignKey('delegacoes_eventuais.id'), nullable=False)
    
    # Core fields from XML
    dev_id = Column(Integer)  # DevId - delegation ID
    dev_no = Column(String(500))  # DevNo - delegation name
    dev_tp = Column(String(100))  # DevTp - delegation type (I Legislature)
    dev_dtini = Column(String(50))  # DevDtIni - start date
    dev_dtfim = Column(String(50))  # DevDtfim - end date
    dev_sel_nr = Column(String(20))  # DevSelNr - session number
    dev_sel_lg = Column(String(20))  # DevSelLg - session legislature
    dev_loc = Column(String(500))  # DevLoc - location
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    delegacoes_eventuais = relationship("DelegacoesEventuais", back_populates="delegacoes")


class RequerimentosAtivDep(Base):
    """Deputy Activity Requirements - Req section"""
    __tablename__ = 'requerimentos_ativ_dep'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    requerimentos = relationship("RequerimentosAtivDepOut", back_populates="requerimentos_ativ_dep", cascade="all, delete-orphan")


class RequerimentosAtivDepOut(Base):
    """Individual Requirements"""
    __tablename__ = 'requerimentos_ativ_dep_out'
    
    id = Column(Integer, primary_key=True)
    requerimentos_ativ_dep_id = Column(Integer, ForeignKey('requerimentos_ativ_dep.id'), nullable=False)
    
    # Core fields from XML
    req_id = Column(Integer)  # ReqId
    req_nr = Column(String(50))  # ReqNr
    req_tp = Column(String(10))  # ReqTp
    req_lg = Column(String(20))  # ReqLg
    req_sl = Column(String(20))  # ReqSl
    req_as = Column(Text)  # ReqAs - subject
    req_dt = Column(DateTime)  # ReqDt - date
    req_per_tp = Column(String(20))  # ReqPerTp
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    requerimentos_ativ_dep = relationship("RequerimentosAtivDep", back_populates="requerimentos")


class SubComissoesGruposTrabalho(Base):
    """Sub-committees and Working Groups - Scgt section"""
    __tablename__ = 'subcomissoes_grupos_trabalho'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    subcomissoes = relationship("SubComissoesGruposTrabalhoOut", back_populates="subcomissoes_grupos_trabalho", cascade="all, delete-orphan")


class SubComissoesGruposTrabalhoOut(Base):
    """Individual Sub-committees/Working Groups"""
    __tablename__ = 'subcomissoes_grupos_trabalho_out'
    
    id = Column(Integer, primary_key=True)
    subcomissoes_grupos_trabalho_id = Column(Integer, ForeignKey('subcomissoes_grupos_trabalho.id'), nullable=False)
    
    # Core fields from XML
    scm_cd = Column(String(20))  # ScmCd - sub-committee code
    scm_com_cd = Column(String(20))  # ScmComCd - committee code
    ccm_dscom = Column(Text)  # CcmDscom - committee description
    cms_situacao = Column(String(200))  # CmsSituacao - committee situation (I Legislature)
    cms_cargo = Column(String(200))  # CmsCargo - committee position
    scm_com_lg = Column(String(20))  # ScmComLg - committee legislature
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    subcomissoes_grupos_trabalho = relationship("SubComissoesGruposTrabalho", back_populates="subcomissoes")


class RelatoresPeticoes(Base):
    """Petition Rapporteurs - Rel.RelatoresPeticoes section"""
    __tablename__ = 'relatores_peticoes'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    relatores = relationship("RelatoresPeticoesOut", back_populates="relatores_peticoes", cascade="all, delete-orphan")


class RelatoresPeticoesOut(Base):
    """Individual Petition Rapporteurs"""
    __tablename__ = 'relatores_peticoes_out'
    
    id = Column(Integer, primary_key=True)
    relatores_peticoes_id = Column(Integer, ForeignKey('relatores_peticoes.id'), nullable=False)
    
    # Core fields from XML
    pec_dtrelf = Column(String(50))  # PecDtrelf - petition report date
    pet_id = Column(Integer)  # PetId - petition ID
    pet_nr = Column(String(50))  # PetNr - petition number
    pet_aspet = Column(Text)  # PetAspet - petition subject
    pet_sel_lg_pk = Column(String(20))  # PetSelLgPk - petition legislature primary key
    pet_sel_nr_pk = Column(String(20))  # PetSelNrPk - petition session number primary key
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    relatores_peticoes = relationship("RelatoresPeticoes", back_populates="relatores")


class Comissoes(Base):
    """Committees - Cms section"""
    __tablename__ = 'comissoes'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    comissoes_out = relationship("ComissoesOut", back_populates="comissoes", cascade="all, delete-orphan")


class ComissoesOut(Base):
    """Individual Committee entries"""
    __tablename__ = 'comissoes_out'
    
    id = Column(Integer, primary_key=True)
    comissoes_id = Column(Integer, ForeignKey('comissoes.id'), nullable=False)
    
    # Core fields from XML
    cms_no = Column(String(500))  # CmsNo - committee name
    cms_cd = Column(String(20))  # CmsCd - committee code
    cms_lg = Column(String(20))  # CmsLg - committee legislature
    cms_cargo = Column(String(200))  # CmsCargo - committee position
    cms_sub_cargo = Column(String(200))  # CmsSubCargo - committee sub-position
    cms_situacao = Column(String(200))  # CmsSituacao - committee situation
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    comissoes = relationship("Comissoes", back_populates="comissoes_out")


class RelatoresIniciativas(Base):
    """Initiative Rapporteurs - Rel.RelatoresIniciativas section"""
    __tablename__ = 'relatores_iniciativas'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    relatores = relationship("RelatoresIniciativasOut", back_populates="relatores_iniciativas", cascade="all, delete-orphan")


class RelatoresIniciativasOut(Base):
    """Individual Initiative Rapporteurs"""
    __tablename__ = 'relatores_iniciativas_out'
    
    id = Column(Integer, primary_key=True)
    relatores_iniciativas_id = Column(Integer, ForeignKey('relatores_iniciativas.id'), nullable=False)
    
    # Core fields from XML
    ini_id = Column(Integer)  # IniId - initiative ID
    ini_nr = Column(String(50))  # IniNr - initiative number
    ini_tp = Column(String(100))  # IniTp - initiative type
    ini_sel_lg = Column(String(20))  # IniSelLg - initiative session legislature
    acc_dtrel = Column(String(50))  # AccDtrel - rapporteur assignment date
    rel_fase = Column(String(200))  # RelFase - rapporteur phase
    ini_ti = Column(Text)  # IniTi - initiative title
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    relatores_iniciativas = relationship("RelatoresIniciativas", back_populates="relatores")


class ReunioesDelegacoesPermanentes(Base):
    """Permanent Delegation Meetings - DlP.DelegacoesPermanentesOut.DepReunioes section"""
    __tablename__ = 'reunioes_delegacoes_permanentes'
    
    id = Column(Integer, primary_key=True)
    delegacoes_permanentes_out_id = Column(Integer, ForeignKey('delegacoes_permanentes_out.id'), nullable=False)
    
    # Core fields from XML
    ren_dt_ini = Column(String(50))  # RenDtIni - meeting start date
    ren_loc = Column(String(500))  # RenLoc - meeting location
    ren_dt_fim = Column(String(50))  # RenDtFim - meeting end date
    ren_ti = Column(Text)  # RenTi - meeting title
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    delegacoes_permanentes_out = relationship("DelegacoesPermanentesOut", back_populates="reunioes")


# =====================================================
# I LEGISLATURE SPECIFIC MODELS
# =====================================================

class AutoresPareceresIncImu(Base):
    """Authors of Incompatibility/Immunity Opinions - I Legislature Rel.AutoresPareceresIncImu section"""
    __tablename__ = 'autores_pareceres_inc_imu'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    autores = relationship("AutoresPareceresIncImuOut", back_populates="autores_pareceres_inc_imu", cascade="all, delete-orphan")


class AutoresPareceresIncImuOut(Base):
    """Individual Authors of Incompatibility/Immunity Opinions"""
    __tablename__ = 'autores_pareceres_inc_imu_out'
    
    id = Column(Integer, primary_key=True)
    autores_pareceres_inc_imu_id = Column(Integer, ForeignKey('autores_pareceres_inc_imu.id'), nullable=False)
    
    # Core fields from XML
    act_id = Column(Integer)  # ActId - activity ID
    act_as = Column(Text)  # ActAs - activity subject
    act_sel_lg = Column(String(20))  # ActSelLg - activity session legislature
    act_tp_desc = Column(String(200))  # ActTpDesc - activity type description
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    autores_pareceres_inc_imu = relationship("AutoresPareceresIncImu", back_populates="autores")


class RelatoresIniEuropeias(Base):
    """European Initiative Rapporteurs - I Legislature Rel.RelatoresIniEuropeias section"""
    __tablename__ = 'relatores_ini_europeias'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    relatores = relationship("RelatoresIniEuropeiasOut", back_populates="relatores_ini_europeias", cascade="all, delete-orphan")


class RelatoresIniEuropeiasOut(Base):
    """Individual European Initiative Rapporteurs"""
    __tablename__ = 'relatores_ini_europeias_out'
    
    id = Column(Integer, primary_key=True)
    relatores_ini_europeias_id = Column(Integer, ForeignKey('relatores_ini_europeias.id'), nullable=False)
    
    # Core fields from XML
    ine_id = Column(Integer)  # IneId - European initiative ID
    ine_data_relatorio = Column(String(50))  # IneDataRelatorio - report date
    ine_referencia = Column(String(200))  # IneReferencia - reference
    ine_titulo = Column(Text)  # IneTitulo - title
    leg = Column(String(20))  # Leg - legislature
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    relatores_ini_europeias = relationship("RelatoresIniEuropeias", back_populates="relatores")


class ParlamentoJovens(Base):
    """Youth Parliament - I Legislature ParlamentoJovens section"""
    __tablename__ = 'parlamento_jovens'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    dados_deputado = relationship("DadosDeputadoParlamentoJovens", back_populates="parlamento_jovens", cascade="all, delete-orphan")


class DadosDeputadoParlamentoJovens(Base):
    """Youth Parliament Deputy Data"""
    __tablename__ = 'dados_deputado_parlamento_jovens'
    
    id = Column(Integer, primary_key=True)
    parlamento_jovens_id = Column(Integer, ForeignKey('parlamento_jovens.id'), nullable=False)
    
    # Core fields from XML
    tipo_reuniao = Column(String(200))  # TipoReuniao - meeting type
    circulo_eleitoral = Column(String(200))  # CirculoEleitoral - electoral district
    legislatura = Column(String(20))  # Legislatura - legislature
    data = Column(String(50))  # Data - date
    sessao = Column(String(100))  # Sessao - session
    estabelecimento = Column(String(500))  # Estabelecimento - establishment
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    parlamento_jovens = relationship("ParlamentoJovens", back_populates="dados_deputado")


class Eventos(Base):
    """Events - I Legislature Eventos section"""
    __tablename__ = 'eventos'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    actividades_comissao = relationship("ActividadesComissaoOut", back_populates="evento", cascade="all, delete-orphan")


class Deslocacoes(Base):
    """Displacements - I Legislature Deslocacoes section"""
    __tablename__ = 'deslocacoes'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    actividades_comissao = relationship("ActividadesComissaoOut", back_populates="deslocacao", cascade="all, delete-orphan")


class RelatoresContasPublicas(Base):
    """Public Accounts Rapporteurs - I Legislature Rel.RelatoresContasPublicas section"""
    __tablename__ = 'relatores_contas_publicas'
    
    id = Column(Integer, primary_key=True)
    actividade_out_id = Column(Integer, ForeignKey('actividade_outs.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    actividade_out = relationship("ActividadeOut")
    relatores = relationship("RelatoresContasPublicasOut", back_populates="relatores_contas_publicas", cascade="all, delete-orphan")


class RelatoresContasPublicasOut(Base):
    """Individual Public Accounts Rapporteurs"""
    __tablename__ = 'relatores_contas_publicas_out'
    
    id = Column(Integer, primary_key=True)
    relatores_contas_publicas_id = Column(Integer, ForeignKey('relatores_contas_publicas.id'), nullable=False)
    
    # Core fields from XML - based on similar structure to other rapporteur models
    act_id = Column(Integer)  # ActId - activity ID
    act_as = Column(Text)  # ActAs - activity subject
    act_tp = Column(String(10))  # ActTp - activity type
    cta_id = Column(Integer)  # CtaId - account ID
    cta_no = Column(String(500))  # CtaNo - account name
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    relatores_contas_publicas = relationship("RelatoresContasPublicas", back_populates="relatores")# I Legislature Biographical Models - to be appended to models.py

# =====================================================
# I LEGISLATURE BIOGRAPHICAL DATA MODELS - COMPREHENSIVE
# =====================================================

class DeputadoHabilitacao(Base):
    """Deputy Academic Qualifications (cadHabilitacoes)"""
    __tablename__ = 'deputado_habilitacoes'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    hab_id = Column(Integer)  # habId - qualification ID
    hab_des = Column(String(500))  # habDes - qualification description
    hab_tipo_id = Column(Integer)  # habTipoId - qualification type ID
    hab_estado = Column(String(50))  # habEstado - qualification state/status
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputado = relationship("Deputado", back_populates="habilitacoes")


class DeputadoCargoFuncao(Base):
    """Deputy Positions/Functions (cadCargosFuncoes)"""
    __tablename__ = 'deputado_cargos_funcoes'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    fun_id = Column(Integer)  # funId - function ID
    fun_des = Column(Text)  # funDes - function description
    fun_ordem = Column(Integer)  # funOrdem - function order
    fun_antiga = Column(String(1))  # funAntiga - S/N whether it's an old function
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputado = relationship("Deputado", back_populates="cargos_funcoes")


class DeputadoTitulo(Base):
    """Deputy Titles/Awards (cadTitulos)"""
    __tablename__ = 'deputado_titulos'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    tit_id = Column(Integer)  # titId - title ID
    tit_des = Column(Text)  # titDes - title description
    tit_ordem = Column(Integer)  # titOrdem - title order
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputado = relationship("Deputado", back_populates="titulos")


class DeputadoCondecoracao(Base):
    """Deputy Decorations/Honors (cadCondecoracoes)"""
    __tablename__ = 'deputado_condecoracoes'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    cod_id = Column(Integer)  # codId - decoration ID
    cod_des = Column(Text)  # codDes - decoration description
    cod_ordem = Column(Integer)  # codOrdem - decoration order
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputado = relationship("Deputado", back_populates="condecoracoes")


class DeputadoObraPublicada(Base):
    """Deputy Published Works (cadObrasPublicadas)"""
    __tablename__ = 'deputado_obras_publicadas'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    pub_id = Column(Integer)  # pubId - publication ID
    pub_des = Column(Text)  # pubDes - publication description
    pub_ordem = Column(Integer)  # pubOrdem - publication order
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputado = relationship("Deputado", back_populates="obras_publicadas")


class DeputadoAtividadeOrgao(Base):
    """Deputy Activity in Parliamentary Organs (cadActividadeOrgaos)"""
    __tablename__ = 'deputado_atividades_orgaos'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    
    # Activity type - 'committee' or 'working_group'
    tipo_atividade = Column(String(50), nullable=False)  # 'actividadeCom' or 'actividadeGT'
    
    # Organ details (pt_ar_wsgode_objectos_DadosOrgaos)
    org_id = Column(Integer)        # orgId - organ ID
    org_sigla = Column(String(50))  # orgSigla - organ acronym
    org_des = Column(String(200))   # orgDes - organ description
    cargo_des = Column(String(200)) # cargoDes - position description
    tim_des = Column(String(50))    # timDes - mandate period description
    leg_des = Column(String(50))    # legDes - legislature description
    
    # Position details (pt_ar_wsgode_objectos_DadosCargosOrgao)
    tia_des = Column(String(200))   # tiaDes - position type description
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputado = relationship("Deputado", back_populates="atividades_orgaos")


class DeputadoMandatoLegislativo(Base):
    """Deputy Legislative Mandates (cadDeputadoLegis) - Enhanced with all fields"""
    __tablename__ = 'deputado_mandatos_legislativos'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    
    # Core mandate data
    dep_nome_parlamentar = Column(String(200))  # depNomeParlamentar
    leg_des = Column(String(50))  # legDes - legislature designation (IA, IB, II, etc.)
    ce_des = Column(String(100))  # ceDes - electoral circle description
    par_sigla = Column(String(20))  # parSigla - party acronym
    par_des = Column(String(200))  # parDes - party description
    gp_sigla = Column(String(20))  # gpSigla - parliamentary group acronym
    gp_des = Column(String(200))  # gpDes - parliamentary group description
    ind_des = Column(String(200))  # indDes - indication description
    url_video_biografia = Column(String(500))  # urlVideoBiografia - biography video URL
    ind_data = Column(Date)  # indData - indication date
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputado = relationship("Deputado", back_populates="mandatos_legislativos")


class RegistoInteressesV2(Base):
    """Interest Registry V2 (RegistoInteressesV2List)"""
    __tablename__ = 'registo_interesses_v2'
    
    id = Column(Integer, primary_key=True)
    deputado_id = Column(Integer, ForeignKey('deputados.id'), nullable=False)
    
    # All V2 fields based on the unmapped field structure
    cad_id = Column(Integer)  # cadId - deputy cadastral ID
    cad_estado_civil_cod = Column(String(10))  # cadEstadoCivilCod - marital status code
    cad_nome_completo = Column(String(200))  # cadNomeCompleto - full name
    cad_actividade_profissional = Column(Text)  # cadActividadeProfissional - professional activity
    cad_estado_civil_des = Column(String(50))  # cadEstadoCivilDes - marital status description
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deputado = relationship("Deputado", back_populates="registo_interesses_v2")