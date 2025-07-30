"""
Parliamentary Activities Mapper
===============================

Schema mapper for parliamentary activities files (Atividades*.xml).
Handles various types of parliamentary activities including debates, 
interpellations, elections, ceremonies, and reports.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .base_mapper import SchemaMapper, SchemaError

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    AtividadeParlamentar, AtividadeParlamentarPublicacao, AtividadeParlamentarVotacao,
    AtividadeParlamentarEleito, AtividadeParlamentarConvidado, DebateParlamentar,
    RelatorioParlamentar, Legislatura, OrcamentoContasGerencia
)

logger = logging.getLogger(__name__)


class AtividadesMapper(SchemaMapper):
    """Schema mapper for parliamentary activities files"""
    
    def __init__(self, db_connection):
        super().__init__(db_connection)
        # Create SQLAlchemy session from raw connection
        # Get the database file path from the connection
        db_path = db_connection.execute('PRAGMA database_list').fetchone()[2]
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # Root structure
            'Atividades', 'Atividades.AtividadesGerais', 
            
            # Activities section
            'Atividades.AtividadesGerais.Atividades', 'Atividades.AtividadesGerais.Atividades.Atividade',
            'Atividades.AtividadesGerais.Atividades.Atividade.Tipo',
            'Atividades.AtividadesGerais.Atividades.Atividade.DescTipo',
            'Atividades.AtividadesGerais.Atividades.Atividade.Assunto',
            'Atividades.AtividadesGerais.Atividades.Atividade.Legislatura',
            'Atividades.AtividadesGerais.Atividades.Atividade.Sessao',
            'Atividades.AtividadesGerais.Atividades.Atividade.DataEntrada',
            'Atividades.AtividadesGerais.Atividades.Atividade.DataAgendamentoDebate',
            'Atividades.AtividadesGerais.Atividades.Atividade.Numero',
            'Atividades.AtividadesGerais.Atividades.Atividade.TipoAutor',
            'Atividades.AtividadesGerais.Atividades.Atividade.AutoresGP',
            'Atividades.AtividadesGerais.Atividades.Atividade.AutoresGP.string',
            'Atividades.AtividadesGerais.Atividades.Atividade.TextosAprovados',
            'Atividades.AtividadesGerais.Atividades.Atividade.TextosAprovados.string',
            'Atividades.AtividadesGerais.Atividades.Atividade.ResultadoVotacaoPontos',
            'Atividades.AtividadesGerais.Atividades.Atividade.OrgaoExterior',
            'Atividades.AtividadesGerais.Atividades.Atividade.Observacoes',
            
            # Activity Publications
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.idPag',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.idDeb',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.supl',
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.obs',
            
            # Activity Debate Publications
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pag',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.idPag',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.idDeb',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.obs',
            
            # Activity Voting
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.id',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.resultado',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.unanime',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.descricao',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.ausencias',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.ausencias.string',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.reuniao',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.data',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pag',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.idPag',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.idDeb',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.obs',
            
            # Reports section
            'Atividades.AtividadesGerais.Relatorios', 'Atividades.AtividadesGerais.Relatorios.Relatorio',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Tipo',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.DescTipo',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Assunto',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Legislatura',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Sessao',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.DataEntrada',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.DataAgendamentoDebate',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Comissao',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.EntidadesExternas',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.EntidadesExternas.string',
            
            # Report Publications
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.idPag',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.idDeb',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.supl',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.obs',
            
            # Report Debate Publications
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pag',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.idPag',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.idDeb',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.obs',
            
            # Debates section
            'Atividades.Debates', 'Atividades.Debates.DadosPesquisaDebatesOut',
            'Atividades.Debates.DadosPesquisaDebatesOut.DebateId',
            'Atividades.Debates.DadosPesquisaDebatesOut.TipoDebateDesig',
            'Atividades.Debates.DadosPesquisaDebatesOut.TipoDebate',
            'Atividades.Debates.DadosPesquisaDebatesOut.DataDebate',
            'Atividades.Debates.DadosPesquisaDebatesOut.Sessao',
            'Atividades.Debates.DadosPesquisaDebatesOut.Legislatura',
            'Atividades.Debates.DadosPesquisaDebatesOut.Assunto',
            'Atividades.Debates.DadosPesquisaDebatesOut.TipoAutor',
            'Atividades.Debates.DadosPesquisaDebatesOut.AutoresDeputados',
            'Atividades.Debates.DadosPesquisaDebatesOut.AutoresGP',
            'Atividades.Debates.DadosPesquisaDebatesOut.DataEntrada',
            'Atividades.Debates.DadosPesquisaDebatesOut.Intervencoes',
            'Atividades.Debates.DadosPesquisaDebatesOut.Intervencoes.string',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.idPag',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.idDeb',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.obs',
            'Atividades.Debates.DadosPesquisaDebatesOut.Observacoes',
            
            # Deslocacoes section
            'Atividades.Deslocacoes',
            
            # Audicoes section
            'Atividades.Audicoes',
            
            # Audiencias section  
            'Atividades.Audiencias',
            
            # Eventos section
            'Atividades.Eventos',
            
            # Eleitos nested structures
            'Atividades.AtividadesGerais.Atividades.Atividade.Eleitos',
            'Atividades.AtividadesGerais.Atividades.Atividade.Eleitos.pt_gov_ar_objectos_EleitosOut',
            'Atividades.AtividadesGerais.Atividades.Atividade.Eleitos.pt_gov_ar_objectos_EleitosOut.nome',
            'Atividades.AtividadesGerais.Atividades.Atividade.Eleitos.pt_gov_ar_objectos_EleitosOut.cargo',
            
            # Convidados nested structures
            'Atividades.AtividadesGerais.Atividades.Atividade.Convidados',
            'Atividades.AtividadesGerais.Atividades.Atividade.Convidados.pt_gov_ar_objectos_ConvidadosOut',
            'Atividades.AtividadesGerais.Atividades.Atividade.Convidados.pt_gov_ar_objectos_ConvidadosOut.nome',
            'Atividades.AtividadesGerais.Atividades.Atividade.Convidados.pt_gov_ar_objectos_ConvidadosOut.cargo',
            'Atividades.AtividadesGerais.Atividades.Atividade.Convidados.pt_gov_ar_objectos_ConvidadosOut.pais',
            'Atividades.AtividadesGerais.Atividades.Atividade.Convidados.pt_gov_ar_objectos_ConvidadosOut.honra',
            
            # Nested pag.string structures for all publication types
            'Atividades.AtividadesGerais.Atividades.Atividade.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            'Atividades.AtividadesGerais.Atividades.Atividade.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            'Atividades.Debates.DadosPesquisaDebatesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            
            # Missing voting detail field
            'Atividades.AtividadesGerais.Atividades.Atividade.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.detalhe',
            
            # Additional sections that might be present but not mapped yet
            'Atividades.AtividadesGerais.Debates', 'Atividades.AtividadesGerais.Audicoes', 
            'Atividades.AtividadesGerais.Audiencias', 'Atividades.AtividadesGerais.Deslocacoes',
            'Atividades.AtividadesGerais.Eventos',
            
            # IX Legislature specific fields - Report Voting and Publications
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.resultado',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.descricao',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.reuniao',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.data',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut.pag',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut.idPag',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut.idDeb',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut.obs',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.publicacao.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            
            # Report voting debate section
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.id',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.resultado',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.reuniao',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.data',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pag',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.idPag',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.idDeb',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.obs',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.publicacao.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.detalhe',
            
            # Report authors/rapporteurs section
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Relatores',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Relatores.pt_gov_ar_objectos_RelatoresOut',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Relatores.pt_gov_ar_objectos_RelatoresOut.id',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Relatores.pt_gov_ar_objectos_RelatoresOut.nome',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Relatores.pt_gov_ar_objectos_RelatoresOut.gp',
            
            # Report observations and texts approved
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Observacoes',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.TextosAprovados',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.TextosAprovados.string',
            
            # Report voting ID field
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.id',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoRelatorio.unanime',
            
            # Audicoes (Parliamentary Hearings) section
            'Atividades.Audicoes.DadosAudicoesComissaoOut',
            'Atividades.Audicoes.DadosAudicoesComissaoOut.IDAudicao',
            'Atividades.Audicoes.DadosAudicoesComissaoOut.NumeroAudicao',
            'Atividades.Audicoes.DadosAudicoesComissaoOut.SessaoLegislativa',
            'Atividades.Audicoes.DadosAudicoesComissaoOut.Legislatura',
            'Atividades.Audicoes.DadosAudicoesComissaoOut.Assunto',
            'Atividades.Audicoes.DadosAudicoesComissaoOut.DataAudicao',
            'Atividades.Audicoes.DadosAudicoesComissaoOut.Data',
            'Atividades.Audicoes.DadosAudicoesComissaoOut.Comissao',
            'Atividades.Audicoes.DadosAudicoesComissaoOut.TipoAudicao',
            'Atividades.Audicoes.DadosAudicoesComissaoOut.Entidades',
            'Atividades.Audicoes.DadosAudicoesComissaoOut.Observacoes',
            
            # Audiencias (Parliamentary Audiences) section  
            'Atividades.Audiencias.DadosAudienciasComissaoOut',
            'Atividades.Audiencias.DadosAudienciasComissaoOut.IDAudiencia',
            'Atividades.Audiencias.DadosAudienciasComissaoOut.NumeroAudiencia',
            'Atividades.Audiencias.DadosAudienciasComissaoOut.SessaoLegislativa',
            'Atividades.Audiencias.DadosAudienciasComissaoOut.Legislatura',
            'Atividades.Audiencias.DadosAudienciasComissaoOut.Assunto',
            'Atividades.Audiencias.DadosAudienciasComissaoOut.DataAudiencia',
            'Atividades.Audiencias.DadosAudienciasComissaoOut.Data',
            'Atividades.Audiencias.DadosAudienciasComissaoOut.Comissao',
            'Atividades.Audiencias.DadosAudienciasComissaoOut.Concedida',
            'Atividades.Audiencias.DadosAudienciasComissaoOut.TipoAudiencia',
            'Atividades.Audiencias.DadosAudienciasComissaoOut.Entidades',
            'Atividades.Audiencias.DadosAudienciasComissaoOut.Observacoes',
            
            # Orçamento e Contas de Gerência section
            'Atividades.OrcamentoContasGerencia',
            'Atividades.OrcamentoContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut', 
            'Atividades.OrcamentoContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.id',
            'Atividades.OrcamentoContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.tipo',
            'Atividades.OrcamentoContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.tp',
            'Atividades.OrcamentoContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.titulo',
            'Atividades.OrcamentoContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.ano',
            'Atividades.OrcamentoContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.leg',
            'Atividades.OrcamentoContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.SL',
            'Atividades.OrcamentoContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.dtAprovacaoCA',
            'Atividades.OrcamentoContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.dtAgendamento',
            
            # Additional fields found in XIII Legislature
            # Report Documents  
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Documentos',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Documentos.DocsOut',
            
            # Report Voting with unanime field
            'Atividades.AtividadesGerais.Relatorios.Relatorio.VotacaoDebate.pt_gov_ar_objectos_VotacaoOut.unanime',
            
            # Events section
            'Atividades.Eventos',
            'Atividades.Eventos.DadosEventosComissaoOut',
            'Atividades.Eventos.DadosEventosComissaoOut.IDEvento',
            'Atividades.Eventos.DadosEventosComissaoOut.Data',
            'Atividades.Eventos.DadosEventosComissaoOut.Legislatura',
            'Atividades.Eventos.DadosEventosComissaoOut.LocalEvento',
            
            # Report Commission Opinion
            'Atividades.AtividadesGerais.Relatorios.Relatorio.ParecerComissao',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.ParecerComissao.AtividadeComissoesOut',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.ParecerComissao.AtividadeComissoesOut.Documentos',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.ParecerComissao.AtividadeComissoesOut.Documentos.pt_gov_ar_objectos_DocsOut',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.ParecerComissao.AtividadeComissoesOut.Documentos.pt_gov_ar_objectos_DocsOut.dataDocumento',
            
            # UTAO Opinion Date
            'Atividades.AtividadesGerais.Relatorios.Relatorio.DataParecerUTAO',
            
            # Additional XIII Legislature fields discovered in second pass
            # Deslocacoes (Displacements) section
            'Atividades.Deslocacoes',
            'Atividades.Deslocacoes.DadosDeslocacoesComissaoOut',
            'Atividades.Deslocacoes.DadosDeslocacoesComissaoOut.SessaoLegislativa',
            'Atividades.Deslocacoes.DadosDeslocacoesComissaoOut.Legislatura',
            'Atividades.Deslocacoes.DadosDeslocacoesComissaoOut.LocalEvento',
            
            # Report Commission Opinion - Extended fields
            'Atividades.AtividadesGerais.Relatorios.Relatorio.ParecerComissao.AtividadeComissoesOut.Relatores',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.ParecerComissao.AtividadeComissoesOut.Relatores.pt_gov_ar_objectos_RelatoresOut',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.ParecerComissao.AtividadeComissoesOut.Relatores.pt_gov_ar_objectos_RelatoresOut.gp',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.ParecerComissao.AtividadeComissoesOut.Documentos.pt_gov_ar_objectos_DocsOut.publicarInternet',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.ParecerComissao.AtividadeComissoesOut.Documentos.pt_gov_ar_objectos_DocsOut.tipoDocumento',
            
            # Report Links and Audicoes
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Links',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Links.DocsOut',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Links.DocsOut.TituloDocumento',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Audicoes',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Audicoes.string',
            
            # Third pass - additional XIII Legislature fields
            # Report Commission Opinion - More fields
            'Atividades.AtividadesGerais.Relatorios.Relatorio.ParecerComissao.AtividadeComissoesOut.Sigla',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.ParecerComissao.AtividadeComissoesOut.Nome',
            
            # Report Documents - Extended fields
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Documentos.DocsOut.DataDocumento',
            'Atividades.AtividadesGerais.Relatorios.Relatorio.Documentos.DocsOut.TituloDocumento',
            
            # Deslocacoes - Additional fields
            'Atividades.Deslocacoes.DadosDeslocacoesComissaoOut.DataIni',
            'Atividades.Deslocacoes.DadosDeslocacoesComissaoOut.Tipo',
            'Atividades.Deslocacoes.DadosDeslocacoesComissaoOut.IDDeslocacao',
            
            # Activity - Additional fields
            'Atividades.AtividadesGerais.Atividades.Atividade.OutrosSubscritores',
            
            # Report - Government Members
            'Atividades.AtividadesGerais.Relatorios.Relatorio.MembrosGoverno'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map parliamentary activities to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        try:
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Extract legislatura from filename or XML
            legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
            
            # Process general activities
            atividades_gerais = xml_root.find('.//AtividadesGerais')
            if atividades_gerais is not None:
                for atividade in atividades_gerais.findall('.//Atividade'):
                    try:
                        success = self._process_atividade(atividade, legislatura)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                        else:
                            error_msg = f"Failed to process activity record"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                            if strict_mode:
                                logger.error(f"STRICT MODE: Exiting due to data validation failure in activity processing")
                                raise ValueError(f"STRICT MODE: Activity processing failed - {error_msg}")
                    except Exception as e:
                        error_msg = f"Activity processing error: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
                        self.session.rollback()
                        if strict_mode:
                            logger.error(f"STRICT MODE: Exiting due to activity processing exception")
                            raise
            
            # Process debates
            debates = xml_root.find('.//Debates')
            if debates is not None:
                for debate in debates.findall('.//DadosPesquisaDebatesOut'):
                    try:
                        success = self._process_debate(debate, legislatura)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                        else:
                            error_msg = f"Failed to process debate record"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                            if strict_mode:
                                logger.error(f"STRICT MODE: Exiting due to data validation failure in debate processing")
                                raise ValueError(f"STRICT MODE: Debate processing failed - {error_msg}")
                    except Exception as e:
                        error_msg = f"Debate processing error: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
                        self.session.rollback()
                        if strict_mode:
                            logger.error(f"STRICT MODE: Exiting due to debate processing exception")
                            raise
            
            # Process reports
            relatorios = xml_root.find('.//Relatorios')
            if relatorios is not None:
                for relatorio in relatorios.findall('.//Relatorio'):
                    try:
                        success = self._process_relatorio(relatorio, legislatura)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                        else:
                            error_msg = f"Failed to process report record"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                            if strict_mode:
                                logger.error(f"STRICT MODE: Exiting due to data validation failure in report processing")
                                raise ValueError(f"STRICT MODE: Report processing failed - {error_msg}")
                    except Exception as e:
                        error_msg = f"Report processing error: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
                        self.session.rollback()
                        if strict_mode:
                            logger.error(f"STRICT MODE: Exiting due to report processing exception")
                            raise
            
            # Process OrcamentoContasGerencia section
            orcamento_gerencia = xml_root.find('.//OrcamentoContasGerencia')
            if orcamento_gerencia is not None:
                for entry in orcamento_gerencia.findall('.//pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut'):
                    try:
                        success = self._process_orcamento_gerencia(entry, legislatura)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                        else:
                            error_msg = f"Failed to process budget/account record"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                            if strict_mode:
                                logger.error(f"STRICT MODE: Exiting due to data validation failure in budget/account processing")
                                raise ValueError(f"STRICT MODE: Budget/account processing failed - {error_msg}")
                    except Exception as e:
                        error_msg = f"Budget/account processing error: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
                        self.session.rollback()
                        if strict_mode:
                            logger.error(f"STRICT MODE: Exiting due to budget/account processing exception")
                            raise
            
            # Commit all changes
            self.session.commit()
            return results
            
        except Exception as e:
            error_msg = f"Critical error processing activities: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            self.session.rollback()
            
            # In strict mode, re-raise the exception to trigger immediate exit
            if strict_mode:
                logger.error(f"STRICT MODE: Re-raising exception to trigger immediate exit")
                raise
            
            return results
    
    def _extract_legislatura(self, file_path: str, xml_root: ET.Element) -> str:
        """Extract legislatura from filename or XML content"""
        # Try filename first
        filename = os.path.basename(file_path)
        leg_match = re.search(r'(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)', filename)
        if leg_match:
            return leg_match.group(1)
        
        # Try XML content - look for first Legislatura element
        leg_element = xml_root.find('.//Legislatura')
        if leg_element is not None and leg_element.text:
            leg_text = leg_element.text.strip()
            # Convert number to roman if needed
            if leg_text.isdigit():
                num_to_roman = {
                    '0': 'CONSTITUINTE', '1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V', 
                    '6': 'VI', '7': 'VII', '8': 'VIII', '9': 'IX', '10': 'X', '11': 'XI', 
                    '12': 'XII', '13': 'XIII', '14': 'XIV', '15': 'XV', '16': 'XVI', '17': 'XVII'
                }
                return num_to_roman.get(leg_text, leg_text)
            return leg_text
        
        # Default to XVII
        return 'XVII'
    
    def _process_atividade(self, atividade: ET.Element, legislatura: Legislatura) -> bool:
        """Process individual parliamentary activity"""
        try:
            # First check if this is an empty/placeholder record
            has_content = any(
                child.text and child.text.strip() 
                for child in atividade.iter() 
                if child != atividade  # Don't count the parent element itself
            )
            
            if not has_content:
                logger.debug("Skipping empty activity record (no content found)")
                return True  # Successfully skip empty records
            
            # Extract basic fields
            tipo = self._get_text_value(atividade, 'Tipo')
            desc_tipo = self._get_text_value(atividade, 'DescTipo')
            assunto = self._get_text_value(atividade, 'Assunto')
            numero = self._get_text_value(atividade, 'Numero')
            tipo_autor = self._get_text_value(atividade, 'TipoAutor')
            autores_gp = self._get_text_value(atividade, 'AutoresGP')
            observacoes = self._get_text_value(atividade, 'Observacoes')
            
            # Extract dates with comprehensive fallback strategy
            data_entrada_str = self._get_text_value(atividade, 'DataEntrada')
            data_agendamento_str = self._get_text_value(atividade, 'DataAgendamentoDebate')
            
            data_entrada = self._parse_date(data_entrada_str)
            data_agendamento_debate = self._parse_date(data_agendamento_str)
            data_atividade = data_entrada or data_agendamento_debate
            
            # Strict validation - only accept records with primary dates
            if not data_atividade:
                logger.warning(f"DATA VALIDATION FAILURE: No valid date found for activity: {assunto[:50] if assunto else 'Unknown'}")
                logger.warning(f"Primary date fields - DataEntrada: {data_entrada_str}, DataAgendamentoDebate: {data_agendamento_str}")
                return False
            
            if not assunto:
                logger.warning("DATA VALIDATION FAILURE: Missing required field: Assunto")
                return False
            
            # Create external ID from numero
            id_externo = None
            if numero:
                try:
                    id_externo = int(numero)
                except ValueError:
                    pass
            
            # Check if activity already exists
            existing = None
            if id_externo:
                existing = self.session.query(AtividadeParlamentar).filter_by(
                    atividade_id=id_externo
                ).first()
            
            if existing:
                # Update existing record
                existing.tipo = tipo
                existing.desc_tipo = desc_tipo
                existing.assunto = assunto
                existing.numero = numero
                existing.data_atividade = data_atividade
                existing.data_entrada = data_entrada
                existing.data_agendamento_debate = data_agendamento_debate
                existing.tipo_autor = tipo_autor
                existing.autores_gp = autores_gp
                existing.observacoes = observacoes
                existing.legislatura_id = legislatura.id
            else:
                # Create new activity record
                atividade_obj = AtividadeParlamentar(
                    atividade_id=id_externo,
                    tipo=tipo,
                    desc_tipo=desc_tipo,
                    assunto=assunto,
                    numero=numero,
                    data_atividade=data_atividade,
                    data_entrada=data_entrada,
                    data_agendamento_debate=data_agendamento_debate,
                    tipo_autor=tipo_autor,
                    autores_gp=autores_gp,
                    observacoes=observacoes,
                    legislatura_id=legislatura.id
                )
                self.session.add(atividade_obj)
                self.session.flush()  # Get the ID
                existing = atividade_obj
            
            # Process related data
            self._process_activity_publications(atividade, existing)
            self._process_activity_votacoes(atividade, existing)
            self._process_activity_eleitos(atividade, existing)
            self._process_activity_convidados(atividade, existing)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing activity: {e}")
            self.session.rollback()
            return False
    
    def _process_debate(self, debate: ET.Element, legislatura: Legislatura) -> bool:
        """Process debate data"""
        try:
            # First check if this is an empty/placeholder record
            has_content = any(
                child.text and child.text.strip() 
                for child in debate.iter() 
                if child != debate  # Don't count the parent element itself
            )
            
            if not has_content:
                logger.debug("Skipping empty debate record (no content found)")
                return True  # Successfully skip empty records
            
            debate_id = self._get_text_value(debate, 'DebateId')
            tipo_debate_desig = self._get_text_value(debate, 'TipoDebateDesig')
            data_debate_str = self._get_text_value(debate, 'DataDebate')
            tipo_debate = self._get_text_value(debate, 'TipoDebate')
            assunto = self._get_text_value(debate, 'Assunto')
            intervencoes = self._get_text_value(debate, 'Intervencoes')
            
            # Strict validation - require both debate_id and assunto
            if not debate_id:
                logger.warning(f"DATA VALIDATION FAILURE: Missing required DebateId")
                return False
                
            if not assunto:
                logger.warning(f"DATA VALIDATION FAILURE: Missing required Assunto")
                return False
            
            data_debate = self._parse_date(data_debate_str)
            
            # Strict validation - only accept records with primary dates
            if not data_debate:
                logger.warning(f"DATA VALIDATION FAILURE: No valid date found for debate: {assunto[:50] if assunto else 'Unknown'}")
                logger.warning(f"Primary date field - DataDebate: {data_debate_str}")
                return False
            
            debate_id_int = int(debate_id)
            
            # Check if debate already exists
            existing = self.session.query(DebateParlamentar).filter_by(
                debate_id=debate_id_int
            ).first()
            
            if existing:
                # Update existing debate
                existing.tipo_debate_desig = tipo_debate_desig
                existing.data_debate = data_debate
                existing.tipo_debate = tipo_debate
                existing.assunto = assunto
                existing.intervencoes = intervencoes
                # Ensure legislatura has an ID
                if hasattr(legislatura, 'id') and legislatura.id:
                    existing.legislatura_id = legislatura.id
                else:
                    logger.error(f"Legislatura object missing ID: {type(legislatura)} = {legislatura}")
                    return False
            else:
                # Create new debate record  
                # Ensure legislatura has an ID
                if not hasattr(legislatura, 'id') or not legislatura.id:
                    logger.error(f"Legislatura object missing ID: {type(legislatura)} = {legislatura}")
                    return False
                    
                debate_obj = DebateParlamentar(
                    debate_id=debate_id_int,
                    tipo_debate_desig=tipo_debate_desig,
                    data_debate=data_debate,
                    tipo_debate=tipo_debate,
                    assunto=assunto,
                    intervencoes=intervencoes,
                    legislatura_id=legislatura.id
                )
                self.session.add(debate_obj)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing debate: {e}")
            self.session.rollback()
            return False
    
    def _process_relatorio(self, relatorio: ET.Element, legislatura: Legislatura) -> bool:
        """Process report data"""
        try:
            # First check if this is an empty/placeholder record
            has_content = any(
                child.text and child.text.strip() 
                for child in relatorio.iter() 
                if child != relatorio  # Don't count the parent element itself
            )
            
            if not has_content:
                logger.debug("Skipping empty report record (no content found)")
                return True  # Successfully skip empty records
            
            tipo = self._get_text_value(relatorio, 'Tipo')
            assunto = self._get_text_value(relatorio, 'Assunto')
            data_entrada_str = self._get_text_value(relatorio, 'DataEntrada')
            comissao = self._get_text_value(relatorio, 'Comissao')
            entidades_externas = self._get_text_value(relatorio, 'EntidadesExternas')
            
            if not assunto:
                logger.warning(f"DATA VALIDATION FAILURE: Missing required report field - Assunto")
                return False
            
            data_entrada = self._parse_date(data_entrada_str)
            if not data_entrada:
                logger.warning(f"DATA VALIDATION FAILURE: No valid date found for report: {assunto[:50] if assunto else 'Unknown'}")
                logger.warning(f"Date field checked - DataEntrada: {data_entrada_str}")
                return False
            
            # Create new report record (no external ID available, so always create new)
            relatorio_obj = RelatorioParlamentar(
                tipo=tipo or 'RELATORIO',
                assunto=assunto,
                data_entrada=data_entrada,
                comissao=comissao,
                entidades_externas=entidades_externas,
                legislatura_id=legislatura.id
            )
            self.session.add(relatorio_obj)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing report: {e}")
            self.session.rollback()
            return False
    
    def _map_activity_type(self, tipo: str) -> Optional[str]:
        """Map XML activity type to database enum"""
        if not tipo:
            return None
        
        # Map common activity types
        type_mapping = {
            'ITG': 'interpelacao',
            'OEX': 'votacao', 
            'SES': 'debate',
            'PRC': 'audiencia',
            'DEBATE': 'debate',
            'RELATORIO': 'audiencia'
        }
        
        return type_mapping.get(tipo.upper(), 'debate')  # Default to debate
    
    def _get_text_value(self, parent: ET.Element, tag_name: str) -> Optional[str]:
        """Get text value from XML element"""
        element = parent.find(tag_name)
        if element is not None and element.text:
            return element.text.strip()
        return None
    
    def _parse_date(self, date_str: str) -> Optional[object]:
        """Parse date string to Python date object"""
        if not date_str:
            return None
        
        try:
            from datetime import datetime
            
            # Try ISO format first
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Try DD/MM/YYYY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    return datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", '%Y-%m-%d').date()
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not parse date: {date_str} - {e}")
        
        return None
    
    def _get_or_create_legislatura(self, legislatura_sigla: str) -> Legislatura:
        """Get or create legislatura record"""
        legislatura = self.session.query(Legislatura).filter_by(numero=legislatura_sigla).first()
        
        if legislatura:
            return legislatura
        
        # Create new legislatura if it doesn't exist
        numero_int = self._convert_roman_to_int(legislatura_sigla)
        
        legislatura = Legislatura(
            numero=legislatura_sigla,
            designacao=f"{numero_int}.ª Legislatura",
            ativa=False
        )
        
        self.session.add(legislatura)
        self.session.flush()  # Get the ID
        return legislatura
    
    def _convert_roman_to_int(self, roman: str) -> int:
        """Convert Roman numeral to integer"""
        roman_numerals = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
            'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'CONSTITUINTE': 0
        }
        return roman_numerals.get(roman, 17)
    
    def _process_activity_publications(self, atividade: ET.Element, atividade_obj: AtividadeParlamentar):
        """Process publications for activity"""
        publicacao = atividade.find('Publicacao')
        if publicacao is not None:
            for pub in publicacao.findall('pt_gov_ar_objectos_PublicacoesOut'):
                pub_nr = self._get_int_value(pub, 'pubNr')
                pub_tipo = self._get_text_value(pub, 'pubTipo')
                pub_tp = self._get_text_value(pub, 'pubTp')
                pub_leg = self._get_text_value(pub, 'pubLeg')
                pub_sl = self._get_int_value(pub, 'pubSL')
                pub_dt = self._parse_date(self._get_text_value(pub, 'pubdt'))
                url_diario = self._get_text_value(pub, 'URLDiario')
                id_pag = self._get_int_value(pub, 'idPag')
                id_deb = self._get_int_value(pub, 'idDeb')
                
                # Handle page numbers
                pag_text = None
                pag_elem = pub.find('pag')
                if pag_elem is not None:
                    string_elems = pag_elem.findall('string')
                    if string_elems:
                        pag_text = ', '.join([s.text for s in string_elems if s.text])
                
                publicacao_record = AtividadeParlamentarPublicacao(
                    atividade_id=atividade_obj.id,
                    pub_nr=pub_nr,
                    pub_tipo=pub_tipo,
                    pub_tp=pub_tp,
                    pub_leg=pub_leg,
                    pub_sl=pub_sl,
                    pub_dt=pub_dt,
                    pag=pag_text,
                    url_diario=url_diario,
                    id_pag=id_pag,
                    id_deb=id_deb
                )
                self.session.add(publicacao_record)
    
    def _process_activity_votacoes(self, atividade: ET.Element, atividade_obj: AtividadeParlamentar):
        """Process voting records for activity"""
        votacao_debate = atividade.find('VotacaoDebate')
        if votacao_debate is not None:
            for votacao in votacao_debate.findall('pt_gov_ar_objectos_VotacaoOut'):
                votacao_id = self._get_int_value(votacao, 'id')
                resultado = self._get_text_value(votacao, 'resultado')
                reuniao = self._get_text_value(votacao, 'reuniao')
                publicacao = self._get_text_value(votacao, 'publicacao')
                data = self._parse_date(self._get_text_value(votacao, 'data'))
                
                votacao_record = AtividadeParlamentarVotacao(
                    atividade_id=atividade_obj.id,
                    votacao_id=votacao_id,
                    resultado=resultado,
                    reuniao=reuniao,
                    publicacao=publicacao,
                    data=data
                )
                self.session.add(votacao_record)
    
    def _process_activity_eleitos(self, atividade: ET.Element, atividade_obj: AtividadeParlamentar):
        """Process elected members for activity"""
        eleitos = atividade.find('Eleitos')
        if eleitos is not None:
            for eleito in eleitos.findall('pt_gov_ar_objectos_EleitosOut'):
                nome = self._get_text_value(eleito, 'nome')
                cargo = self._get_text_value(eleito, 'cargo')
                
                if nome:
                    eleito_record = AtividadeParlamentarEleito(
                        atividade_id=atividade_obj.id,
                        nome=nome,
                        cargo=cargo
                    )
                    self.session.add(eleito_record)
    
    def _process_activity_convidados(self, atividade: ET.Element, atividade_obj: AtividadeParlamentar):
        """Process guests/invitees for activity"""
        convidados = atividade.find('Convidados')
        if convidados is not None:
            for convidado in convidados.findall('pt_gov_ar_objectos_ConvidadosOut'):
                nome = self._get_text_value(convidado, 'nome')
                pais = self._get_text_value(convidado, 'pais')
                honra = self._get_text_value(convidado, 'honra')
                
                if nome:
                    convidado_record = AtividadeParlamentarConvidado(
                        atividade_id=atividade_obj.id,
                        nome=nome,
                        pais=pais,
                        honra=honra
                    )
                    self.session.add(convidado_record)
    
    def _process_orcamento_gerencia(self, entry: ET.Element, legislatura: Legislatura) -> bool:
        """Process budget and account management entry"""
        try:
            # First check if this is an empty/placeholder record
            has_content = any(
                child.text and child.text.strip() 
                for child in entry.iter() 
                if child != entry  # Don't count the parent element itself
            )
            
            if not has_content:
                logger.debug("Skipping empty budget/account record (no content found)")
                return True  # Successfully skip empty records
            
            # Extract required fields
            entry_id = self._get_int_value(entry, 'id')
            tipo = self._get_text_value(entry, 'tipo')
            tp = self._get_text_value(entry, 'tp')
            titulo = self._get_text_value(entry, 'titulo')
            ano = self._get_int_value(entry, 'ano')
            leg = self._get_text_value(entry, 'leg')
            sl = self._get_int_value(entry, 'SL')
            
            # Validate required fields
            if not entry_id:
                logger.warning(f"DATA VALIDATION FAILURE: Missing required budget/account field - id")
                return False
            
            if not titulo:
                logger.warning(f"DATA VALIDATION FAILURE: Missing required budget/account field - titulo")
                return False
            
            if not ano:
                logger.warning(f"DATA VALIDATION FAILURE: Missing required budget/account field - ano")
                return False
            
            # Extract optional date fields
            dt_aprovacao_str = self._get_text_value(entry, 'dtAprovacaoCA')
            dt_agendamento_str = self._get_text_value(entry, 'dtAgendamento')
            
            dt_aprovacao = self._parse_date(dt_aprovacao_str) if dt_aprovacao_str else None
            dt_agendamento = self._parse_date(dt_agendamento_str) if dt_agendamento_str else None
            
            # Check if record already exists
            existing = self.session.query(OrcamentoContasGerencia).filter_by(
                entry_id=entry_id,
                legislatura_id=legislatura.id
            ).first()
            
            if existing:
                logger.debug(f"Budget/account entry {entry_id} already exists, skipping")
                return True
            
            # Create new budget/account record
            orcamento_obj = OrcamentoContasGerencia(
                entry_id=entry_id,
                tipo=tipo or 'Unknown',
                tp=tp or 'UNK',
                titulo=titulo,
                ano=ano,
                leg=leg or legislatura.numero,
                sl=sl or 1,
                dt_aprovacao_ca=dt_aprovacao,
                dt_agendamento=dt_agendamento,
                legislatura_id=legislatura.id
            )
            self.session.add(orcamento_obj)
            
            logger.debug(f"Processed budget/account entry: {entry_id} - {titulo[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error processing budget/account entry: {e}")
            self.session.rollback()
            return False
    
    def _get_int_value(self, parent: ET.Element, tag_name: str) -> Optional[int]:
        """Get integer value from XML element"""
        text_value = self._get_text_value(parent, tag_name)
        if text_value:
            try:
                return int(text_value)
            except ValueError:
                return None
        return None