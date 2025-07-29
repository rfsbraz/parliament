from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class BiographicalRecord(db.Model):
    __tablename__ = 'biographical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    cadastro_id = db.Column(db.Integer, unique=True, nullable=False)
    nome_completo = db.Column(db.Text)
    data_nascimento = db.Column(db.Text)
    sexo = db.Column(db.Text)
    profissao = db.Column(db.Text)
    import_source = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cadastro_id': self.cadastro_id,
            'nome_completo': self.nome_completo,
            'data_nascimento': self.data_nascimento,
            'sexo': self.sexo,
            'profissao': self.profissao,
            'import_source': self.import_source
        }

class Partido(db.Model):
    __tablename__ = 'partidos'
    
    id = db.Column(db.Integer, primary_key=True)
    sigla = db.Column(db.Text, nullable=False, unique=True)
    nome = db.Column(db.Text, nullable=False)
    designacao_completa = db.Column(db.Text)
    cor_hex = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    data_fundacao = db.Column(db.Date)
    ideologia = db.Column(db.Text)
    lider_parlamentar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sigla': self.sigla,
            'nome': self.nome,
            'designacao_completa': self.designacao_completa,
            'cor_hex': self.cor_hex,
            'ativo': self.ativo,
            'data_fundacao': self.data_fundacao.isoformat() if self.data_fundacao else None,
            'ideologia': self.ideologia,
            'lider_parlamentar': self.lider_parlamentar,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Commission(db.Model):
    __tablename__ = 'commissions_extended'
    
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Text, unique=True, nullable=False)
    nome = db.Column(db.Text)
    legislatura = db.Column(db.Text)
    import_source = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'source_id': self.source_id,
            'nome': self.nome,
            'legislatura': self.legislatura,
            'import_source': self.import_source
        }

class Deputado(db.Model):
    __tablename__ = 'deputados'
    
    id = db.Column(db.Integer, primary_key=True)
    id_cadastro = db.Column(db.Integer, nullable=False, unique=True)
    nome = db.Column(db.Text, nullable=False)
    nome_completo = db.Column(db.Text)
    profissao = db.Column(db.Text)
    data_nascimento = db.Column(db.Date)
    naturalidade = db.Column(db.Text)
    habilitacoes_academicas = db.Column(db.Text)
    biografia = db.Column(db.Text)
    foto_url = db.Column(db.Text)
    email = db.Column(db.Text)
    telefone = db.Column(db.Text)
    gabinete = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'id_cadastro': self.id_cadastro,
            'nome': self.nome,
            'nome_completo': self.nome_completo,
            'profissao': self.profissao,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'naturalidade': self.naturalidade,
            'habilitacoes_academicas': self.habilitacoes_academicas,
            'biografia': self.biografia,
            'foto_url': self.foto_url,
            'email': self.email,
            'telefone': self.telefone,
            'gabinete': self.gabinete,
            'ativo': self.ativo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Legislatura(db.Model):
    __tablename__ = 'legislaturas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, nullable=False, unique=True)
    designacao = db.Column(db.Text, nullable=False)
    data_inicio = db.Column(db.Date)
    data_fim = db.Column(db.Date)
    ativa = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'designacao': self.designacao,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'ativa': self.ativa,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Mandato(db.Model):
    __tablename__ = 'mandatos'
    
    id = db.Column(db.Integer, primary_key=True)
    deputado_id = db.Column(db.Integer, nullable=False)
    partido_id = db.Column(db.Integer, nullable=False)
    circulo_id = db.Column(db.Integer, nullable=False)
    legislatura_id = db.Column(db.Integer, nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date)
    ativo = db.Column(db.Boolean, default=True)
    posicao_lista = db.Column(db.Integer)
    votos_obtidos = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'deputado_id': self.deputado_id,
            'partido_id': self.partido_id,
            'circulo_id': self.circulo_id,
            'legislatura_id': self.legislatura_id,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'ativo': self.ativo,
            'posicao_lista': self.posicao_lista,
            'votos_obtidos': self.votos_obtidos
        }

class CirculoEleitoral(db.Model):
    __tablename__ = 'circulos_eleitorais'
    
    id = db.Column(db.Integer, primary_key=True)
    designacao = db.Column(db.Text, nullable=False, unique=True)
    codigo = db.Column(db.Text)
    regiao = db.Column(db.Text)
    distrito = db.Column(db.Text)
    num_deputados = db.Column(db.Integer, default=0)
    populacao = db.Column(db.Integer)
    area_km2 = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'designacao': self.designacao,
            'codigo': self.codigo,
            'regiao': self.regiao,
            'distrito': self.distrito,
            'num_deputados': self.num_deputados,
            'populacao': self.populacao,
            'area_km2': self.area_km2,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DeputyCommission(db.Model):
    __tablename__ = 'deputy_commissions_extended'
    
    id = db.Column(db.Integer, primary_key=True)
    deputy_id = db.Column(db.Text, nullable=False)
    commission_id = db.Column(db.Text, nullable=False)
    situacao = db.Column(db.Text)
    legislatura = db.Column(db.Text)
    import_source = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'deputy_id': self.deputy_id,
            'commission_id': self.commission_id,
            'situacao': self.situacao,
            'legislatura': self.legislatura,
            'import_source': self.import_source
        }

class Initiative(db.Model):
    __tablename__ = 'initiatives_extended'
    
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Text, unique=True, nullable=False)
    numero = db.Column(db.Text)
    tipo = db.Column(db.Text)
    tipo_descricao = db.Column(db.Text)
    legislatura = db.Column(db.Text)
    sessao = db.Column(db.Text)
    titulo = db.Column(db.Text)
    deputy_id = db.Column(db.Text)
    import_source = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'source_id': self.source_id,
            'numero': self.numero,
            'tipo': self.tipo,
            'tipo_descricao': self.tipo_descricao,
            'legislatura': self.legislatura,
            'sessao': self.sessao,
            'titulo': self.titulo,
            'deputy_id': self.deputy_id,
            'import_source': self.import_source
        }

class Intervention(db.Model):
    __tablename__ = 'interventions_extended'
    
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Text, unique=True, nullable=False)
    titulo = db.Column(db.Text)
    assunto = db.Column(db.Text)
    data_publicacao = db.Column(db.Text)
    tipo_publicacao = db.Column(db.Text)
    legislatura = db.Column(db.Text)
    sessao = db.Column(db.Text)
    numero = db.Column(db.Text)
    tipo_intervencao = db.Column(db.Text)
    paginas_dar = db.Column(db.Text)
    deputy_id = db.Column(db.Text)
    import_source = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'source_id': self.source_id,
            'titulo': self.titulo,
            'assunto': self.assunto,
            'data_publicacao': self.data_publicacao,
            'tipo_publicacao': self.tipo_publicacao,
            'legislatura': self.legislatura,
            'sessao': self.sessao,
            'numero': self.numero,
            'tipo_intervencao': self.tipo_intervencao,
            'paginas_dar': self.paginas_dar,
            'deputy_id': self.deputy_id,
            'import_source': self.import_source
        }

