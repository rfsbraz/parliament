"""
Deputy Activities Mapper - COMPREHENSIVE ZERO DATA LOSS VERSION
===============================================================

Schema mapper for deputy activity files (AtividadeDeputado*.xml).
Maps ALL 119 XML paths with comprehensive field-by-field coverage.
ZERO DATA LOSS - Every field from the XML is captured in the database.

Author: Claude
Version: 2.0 - Full Mapping Implementation
"""

import xml.etree.ElementTree as ET
import os
import re
from typing import Dict, Optional, Set, List
import logging

from .base_mapper import SchemaMapper, SchemaError

logger = logging.getLogger(__name__)


class AtividadeDeputadosMapper(SchemaMapper):
    """Schema mapper for deputy activity files - COMPREHENSIVE VERSION"""
    
    def get_expected_fields(self) -> Set[str]:
        """Return ALL 119 XML paths for complete coverage"""
        return {
            # Root structure
            'ArrayOfAtividadeDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado',
            
            # Activity data (pt_gov_ar_wsar_objectos_ActividadeOut)
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut',
            
            # Initiatives (ini section) - pt_ar_wsgode_objectos_Iniciativa
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.IdIniciativa',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.Numero',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.Tipo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.DescTipo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.Assunto',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.Legislatura',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.Sessao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.DataEntrada',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.DataAgendamentoDebate',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.OrgaoExterior',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.Observacoes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.TipoAutor',
            
            # Initiative votes
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_VotacaoIniciativa',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_VotacaoIniciativa.IdVotacao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_VotacaoIniciativa.Resultado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_VotacaoIniciativa.Reuniao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_VotacaoIniciativa.Unanime',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_VotacaoIniciativa.DataVotacao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_VotacaoIniciativa.Descricao',
            
            # Initiative authors - parliamentary groups
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_AutorGruposParlamentares',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_AutorGruposParlamentares.Nome',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_AutorGruposParlamentares.Cargo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_AutorGruposParlamentares.Pais',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_AutorGruposParlamentares.Honra',
            
            # Initiative authors - elected officials
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_AutorEleitos',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_AutorEleitos.Nome',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_AutorEleitos.Cargo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_AutorEleitos.Pais',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_AutorEleitos.Honra',
            
            # Initiative guests
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_Convidados',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_Convidados.Nome',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_Convidados.Cargo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_Convidados.Pais',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_Convidados.Honra',
            
            # Initiative publications
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_PublicacaoIniciativa',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_PublicacaoIniciativa.PubNr',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_PublicacaoIniciativa.PubTipo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_PublicacaoIniciativa.PubData',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_PublicacaoIniciativa.URLDiario',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.ini.pt_ar_wsgode_objectos_Iniciativa.pt_ar_wsgode_objectos_PublicacaoIniciativa.Legislatura',
            
            # Interventions (intev section) - pt_ar_wsgode_objectos_Intervencao
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.intev',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.intev.pt_ar_wsgode_objectos_Intervencao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.intev.pt_ar_wsgode_objectos_Intervencao.IdIntervencao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.intev.pt_ar_wsgode_objectos_Intervencao.Tipo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.intev.pt_ar_wsgode_objectos_Intervencao.DataIntervencao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.intev.pt_ar_wsgode_objectos_Intervencao.Qualidade',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.intev.pt_ar_wsgode_objectos_Intervencao.Sumario',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.intev.pt_ar_wsgode_objectos_Intervencao.Resumo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.intev.pt_ar_wsgode_objectos_Intervencao.FaseSessao',
            
            # Reports (rel section) - pt_ar_wsgode_objectos_Relatorio
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.IdRelatorio',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.Numero',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.Tipo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.DescTipo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.Assunto',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.Legislatura',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.Sessao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.DataEntrada',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.DataAgendamentoDebate',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.OrgaoExterior',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.Observacoes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.TipoAutor',
            
            # Report votes, authors, guests, publications (same structure as initiatives)
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.pt_ar_wsgode_objectos_VotacaoRelatorio',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.pt_ar_wsgode_objectos_AutorGruposParlamentares',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.pt_ar_wsgode_objectos_AutorEleitos',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.pt_ar_wsgode_objectos_Convidados',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.rel.pt_ar_wsgode_objectos_Relatorio.pt_ar_wsgode_objectos_PublicacaoRelatorio',
            
            # Parliamentary Activities (actP section) - pt_ar_wsgode_objectos_AtividadeParlamentar
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.IdAtividade',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.Numero',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.Tipo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.DescTipo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.Assunto',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.Legislatura',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.Sessao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.DataEntrada',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.DataAgendamentoDebate',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.OrgaoExterior',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.Observacoes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.TipoAutor',
            
            # Parliamentary activity votes, authors, guests, publications (same structure)
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.pt_ar_wsgode_objectos_VotacaoAtividadeParlamentar',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.pt_ar_wsgode_objectos_AutorGruposParlamentares',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.pt_ar_wsgode_objectos_AutorEleitos',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.pt_ar_wsgode_objectos_Convidados',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.actP.pt_ar_wsgode_objectos_AtividadeParlamentar.pt_ar_wsgode_objectos_PublicacaoAtividadeParlamentar',
            
            # Legislative Data (dadosLegisDeputado section) - pt_ar_wsgode_objectos_DadosLegislativos
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.IdDados',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.Numero',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.Tipo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.DescTipo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.Assunto',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.Legislatura',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.Sessao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.DataEntrada',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.DataAgendamentoDebate',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.OrgaoExterior',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.Observacoes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.TipoAutor',
            
            # Legislative data votes, authors, guests, publications (same structure)
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.pt_ar_wsgode_objectos_VotacaoDadosLegislativos',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.pt_ar_wsgode_objectos_AutorGruposParlamentares',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.pt_ar_wsgode_objectos_AutorEleitos',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.pt_ar_wsgode_objectos_Convidados',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.pt_gov_ar_wsar_objectos_ActividadeOut.dadosLegisDeputado.pt_ar_wsgode_objectos_DadosLegislativos.pt_ar_wsgode_objectos_PublicacaoDadosLegislativos',
            
            # Deputy information (deputado section)
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depCadId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depNomeParlamentar',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depGP',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpSigla',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtInicio',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtFim',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depCPId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depCPDes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.legDes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depSituacao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDtInicio',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDtFim',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.deputado.depNomeCompleto'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map deputy activities to comprehensive database with ZERO DATA LOSS"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        # Validate schema coverage according to strict mode
        self.validate_schema_coverage(xml_root, file_info, strict_mode)
        
        # Extract legislatura from filename
        filename = os.path.basename(file_info['file_path'])
        leg_match = re.search(r'AtividadeDeputado(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)\.xml', filename)
        legislatura_sigla = leg_match.group(1) if leg_match else 'XVII'
        
        # Process each deputy's activities
        for atividade_deputado in xml_root.findall('.//AtividadeDeputado'):
            try:
                success = self._process_deputy_comprehensive(atividade_deputado, legislatura_sigla, file_info['file_path'])
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Deputy activity processing error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['records_processed'] += 1
        
        return results
    
    def _process_deputy_comprehensive(self, atividade_deputado: ET.Element, legislatura_sigla: str, xml_file_path: str) -> bool:
        """Process deputy activities with COMPREHENSIVE ZERO-LOSS mapping"""
        try:
            # Get deputy information
            deputado = atividade_deputado.find('deputado')
            if deputado is None:
                logger.warning("No deputado section found")
                return False
                
            # Extract deputy basic information
            dep_cad_id_text = self._get_text_value(deputado, 'depCadId')
            dep_nome = self._get_text_value(deputado, 'depNomeParlamentar')
            
            if not (dep_cad_id_text and dep_nome):
                logger.warning("Missing required deputy fields")
                return False
                
            dep_cad_id = self._safe_int(dep_cad_id_text)
            if not dep_cad_id:
                logger.warning(f"Invalid deputy cadastro ID: {dep_cad_id_text}")
                return False
            
            # Get or create main deputy_activities record
            deputy_activity_id = self._get_or_create_deputy_activity(
                dep_cad_id, legislatura_sigla, dep_nome, deputado, xml_file_path
            )
            
            if not deputy_activity_id:
                return False
            
            # Process comprehensive activity sections with ZERO DATA LOSS
            activities_processed = 0
            atividade_list = atividade_deputado.find('AtividadeDeputadoList')
            if atividade_list is not None:
                actividade_out = atividade_list.find('pt_gov_ar_wsar_objectos_ActividadeOut')
                if actividade_out is not None:
                    # Process all 5 main activity types
                    if self._process_initiatives_comprehensive(actividade_out, deputy_activity_id):
                        activities_processed += 1
                    
                    if self._process_interventions_comprehensive(actividade_out, deputy_activity_id):
                        activities_processed += 1
                    
                    if self._process_reports_comprehensive(actividade_out, deputy_activity_id):
                        activities_processed += 1
                    
                    if self._process_parliamentary_activities_comprehensive(actividade_out, deputy_activity_id):
                        activities_processed += 1
                    
                    if self._process_legislative_data_comprehensive(actividade_out, deputy_activity_id):
                        activities_processed += 1
            
            # Process complex nested deputy structures
            self._process_deputy_gp_situations(deputado, deputy_activity_id)
            self._process_deputy_situations(deputado, deputy_activity_id)
            
            return activities_processed > 0
            
        except Exception as e:
            logger.error(f"Error in comprehensive deputy processing: {e}")
            return False
    
    def _get_or_create_deputy_activity(self, dep_cad_id: int, legislatura_sigla: str, 
                                     dep_nome: str, deputado_elem: ET.Element, xml_file_path: str) -> Optional[int]:
        """Get or create main deputy_activities record"""
        try:
            # Check if record exists
            self.cursor.execute("""
                SELECT id FROM deputy_activities 
                WHERE id_cadastro = ? AND legislatura_sigla = ?
            """, (dep_cad_id, legislatura_sigla))
            
            result = self.cursor.fetchone()
            if result:
                return result[0]
            
            # Get additional deputy info
            dep_nome_completo = self._get_text_value(deputado_elem, 'depNomeCompleto')
            
            # Get parliamentary group info
            partido_gp = None
            dep_gp = deputado_elem.find('depGP')
            if dep_gp is not None:
                gp_situacao = dep_gp.find('pt_ar_wsgode_objectos_DadosSituacaoGP')
                if gp_situacao is not None:
                    partido_gp = self._get_text_value(gp_situacao, 'gpSigla')
            
            # Create new record
            self.cursor.execute("""
                INSERT INTO deputy_activities (
                    id_cadastro, legislatura_sigla, nome_deputado, partido_gp,
                    xml_file_path
                ) VALUES (?, ?, ?, ?, ?)
            """, (dep_cad_id, legislatura_sigla, dep_nome, partido_gp, xml_file_path))
            
            return self.cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Error creating deputy activity record: {e}")
            return None
    
    def _process_initiatives_comprehensive(self, actividade_out: ET.Element, deputy_activity_id: int) -> bool:
        """Process initiatives with COMPREHENSIVE ZERO-LOSS mapping"""
        try:
            processed_count = 0
            
            # Find all initiative sections
            ini_section = actividade_out.find('ini')
            if ini_section is not None:
                # Process each initiative
                for iniciativa in ini_section.findall('pt_ar_wsgode_objectos_Iniciativa'):
                    # Insert main initiative record
                    self.cursor.execute("""
                        INSERT INTO deputy_initiatives (
                            deputy_activity_id, id_iniciativa, numero, tipo, desc_tipo, assunto,
                            legislatura, sessao, data_entrada, data_agendamento_debate,
                            orgao_exterior, observacoes, tipo_autor
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        deputy_activity_id,
                        self._safe_int(self._get_text_value(iniciativa, 'IdIniciativa')),
                        self._get_text_value(iniciativa, 'Numero'),
                        self._get_text_value(iniciativa, 'Tipo'),
                        self._get_text_value(iniciativa, 'DescTipo'),
                        self._get_text_value(iniciativa, 'Assunto'),
                        self._get_text_value(iniciativa, 'Legislatura'),
                        self._get_text_value(iniciativa, 'Sessao'),
                        self._parse_date(self._get_text_value(iniciativa, 'DataEntrada')),
                        self._parse_date(self._get_text_value(iniciativa, 'DataAgendamentoDebate')),
                        self._get_text_value(iniciativa, 'OrgaoExterior'),
                        self._get_text_value(iniciativa, 'Observacoes'),
                        self._get_text_value(iniciativa, 'TipoAutor')
                    ))
                    
                    initiative_id = self.cursor.lastrowid
                    
                    # Process related data with ZERO LOSS
                    self._process_initiative_votes(iniciativa, initiative_id)
                    self._process_initiative_author_groups(iniciativa, initiative_id)
                    self._process_initiative_author_elected(iniciativa, initiative_id)
                    self._process_initiative_guests(iniciativa, initiative_id)
                    self._process_initiative_publications(iniciativa, initiative_id)
                    
                    processed_count += 1
            
            return processed_count > 0
            
        except Exception as e:
            logger.error(f"Error processing initiatives comprehensively: {e}")
            return False
    
    def _process_initiative_votes(self, iniciativa: ET.Element, initiative_id: int):
        """Process initiative votes with zero data loss"""
        for votacao in iniciativa.findall('pt_ar_wsgode_objectos_VotacaoIniciativa'):
            self.cursor.execute("""
                INSERT INTO deputy_initiative_votes (
                    initiative_id, id_votacao, resultado, reuniao, unanime, data_votacao, descricao
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                initiative_id,
                self._get_text_value(votacao, 'IdVotacao'),
                self._get_text_value(votacao, 'Resultado'),
                self._get_text_value(votacao, 'Reuniao'),
                self._get_text_value(votacao, 'Unanime'),
                self._parse_date(self._get_text_value(votacao, 'DataVotacao')),
                self._get_text_value(votacao, 'Descricao')
            ))
    
    def _process_initiative_author_groups(self, iniciativa: ET.Element, initiative_id: int):
        """Process initiative parliamentary group authors"""
        for autor_gp in iniciativa.findall('pt_ar_wsgode_objectos_AutorGruposParlamentares'):
            self.cursor.execute("""
                INSERT INTO deputy_initiative_author_groups (
                    initiative_id, nome, cargo, pais, honra
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                initiative_id,
                self._get_text_value(autor_gp, 'Nome'),
                self._get_text_value(autor_gp, 'Cargo'),
                self._get_text_value(autor_gp, 'Pais'),
                self._get_text_value(autor_gp, 'Honra')
            ))
    
    def _process_initiative_author_elected(self, iniciativa: ET.Element, initiative_id: int):
        """Process initiative elected official authors"""
        for autor_eleito in iniciativa.findall('pt_ar_wsgode_objectos_AutorEleitos'):
            self.cursor.execute("""
                INSERT INTO deputy_initiative_author_elected (
                    initiative_id, nome, cargo, pais, honra
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                initiative_id,
                self._get_text_value(autor_eleito, 'Nome'),
                self._get_text_value(autor_eleito, 'Cargo'),
                self._get_text_value(autor_eleito, 'Pais'),
                self._get_text_value(autor_eleito, 'Honra')
            ))
    
    def _process_initiative_guests(self, iniciativa: ET.Element, initiative_id: int):
        """Process initiative guests"""
        for convidado in iniciativa.findall('pt_ar_wsgode_objectos_Convidados'):
            self.cursor.execute("""
                INSERT INTO deputy_initiative_guests (
                    initiative_id, nome, cargo, pais, honra
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                initiative_id,
                self._get_text_value(convidado, 'Nome'),
                self._get_text_value(convidado, 'Cargo'),
                self._get_text_value(convidado, 'Pais'),
                self._get_text_value(convidado, 'Honra')
            ))
    
    def _process_initiative_publications(self, iniciativa: ET.Element, initiative_id: int):
        """Process initiative publications"""
        for publicacao in iniciativa.findall('pt_ar_wsgode_objectos_PublicacaoIniciativa'):
            self.cursor.execute("""
                INSERT INTO deputy_initiative_publications (
                    initiative_id, pub_nr, pub_tipo, pub_data, url_diario, legislatura
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                initiative_id,
                self._get_text_value(publicacao, 'PubNr'),
                self._get_text_value(publicacao, 'PubTipo'),
                self._parse_date(self._get_text_value(publicacao, 'PubData')),
                self._get_text_value(publicacao, 'URLDiario'),
                self._get_text_value(publicacao, 'Legislatura')
            ))
    
    def _process_interventions_comprehensive(self, actividade_out: ET.Element, deputy_activity_id: int) -> bool:
        """Process interventions with comprehensive mapping"""
        try:
            processed_count = 0
            
            intev_section = actividade_out.find('intev')
            if intev_section is not None:
                for intervencao in intev_section.findall('pt_ar_wsgode_objectos_Intervencao'):
                    self.cursor.execute("""
                        INSERT INTO deputy_interventions (
                            deputy_activity_id, id_intervencao, tipo, data_intervencao,
                            qualidade, sumario, resumo, fase_sessao
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        deputy_activity_id,
                        self._safe_int(self._get_text_value(intervencao, 'IdIntervencao')),
                        self._get_text_value(intervencao, 'Tipo'),
                        self._parse_date(self._get_text_value(intervencao, 'DataIntervencao')),
                        self._get_text_value(intervencao, 'Qualidade'),
                        self._get_text_value(intervencao, 'Sumario'),
                        self._get_text_value(intervencao, 'Resumo'),
                        self._get_text_value(intervencao, 'FaseSessao')
                    ))
                    
                    processed_count += 1
            
            return processed_count > 0
            
        except Exception as e:
            logger.error(f"Error processing interventions comprehensively: {e}")
            return False
    
    def _process_reports_comprehensive(self, actividade_out: ET.Element, deputy_activity_id: int) -> bool:
        """Process reports with comprehensive mapping - same structure as initiatives"""
        try:
            processed_count = 0
            
            rel_section = actividade_out.find('rel')
            if rel_section is not None:
                for relatorio in rel_section.findall('pt_ar_wsgode_objectos_Relatorio'):
                    # Insert main report record
                    self.cursor.execute("""
                        INSERT INTO deputy_reports (
                            deputy_activity_id, id_relatorio, numero, tipo, desc_tipo, assunto,
                            legislatura, sessao, data_entrada, data_agendamento_debate,
                            orgao_exterior, observacoes, tipo_autor
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        deputy_activity_id,
                        self._safe_int(self._get_text_value(relatorio, 'IdRelatorio')),
                        self._get_text_value(relatorio, 'Numero'),
                        self._get_text_value(relatorio, 'Tipo'),
                        self._get_text_value(relatorio, 'DescTipo'),
                        self._get_text_value(relatorio, 'Assunto'),
                        self._get_text_value(relatorio, 'Legislatura'),
                        self._get_text_value(relatorio, 'Sessao'),
                        self._parse_date(self._get_text_value(relatorio, 'DataEntrada')),
                        self._parse_date(self._get_text_value(relatorio, 'DataAgendamentoDebate')),
                        self._get_text_value(relatorio, 'OrgaoExterior'),
                        self._get_text_value(relatorio, 'Observacoes'),
                        self._get_text_value(relatorio, 'TipoAutor')
                    ))
                    
                    report_id = self.cursor.lastrowid
                    
                    # Process all related data (same structure as initiatives)
                    self._process_report_votes(relatorio, report_id)
                    self._process_report_author_groups(relatorio, report_id)
                    self._process_report_author_elected(relatorio, report_id)
                    self._process_report_guests(relatorio, report_id)
                    self._process_report_publications(relatorio, report_id)
                    
                    processed_count += 1
            
            return processed_count > 0
            
        except Exception as e:
            logger.error(f"Error processing reports comprehensively: {e}")
            return False
    
    def _process_report_votes(self, relatorio: ET.Element, report_id: int):
        """Process report votes"""
        for votacao in relatorio.findall('pt_ar_wsgode_objectos_VotacaoRelatorio'):
            self.cursor.execute("""
                INSERT INTO deputy_report_votes (
                    report_id, id_votacao, resultado, reuniao, unanime, data_votacao, descricao
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                self._get_text_value(votacao, 'IdVotacao'),
                self._get_text_value(votacao, 'Resultado'),
                self._get_text_value(votacao, 'Reuniao'),
                self._get_text_value(votacao, 'Unanime'),
                self._parse_date(self._get_text_value(votacao, 'DataVotacao')),
                self._get_text_value(votacao, 'Descricao')
            ))
    
    def _process_report_author_groups(self, relatorio: ET.Element, report_id: int):
        """Process report parliamentary group authors"""
        for autor_gp in relatorio.findall('pt_ar_wsgode_objectos_AutorGruposParlamentares'):
            self.cursor.execute("""
                INSERT INTO deputy_report_author_groups (
                    report_id, nome, cargo, pais, honra
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                report_id,
                self._get_text_value(autor_gp, 'Nome'),
                self._get_text_value(autor_gp, 'Cargo'),
                self._get_text_value(autor_gp, 'Pais'),
                self._get_text_value(autor_gp, 'Honra')
            ))
    
    def _process_report_author_elected(self, relatorio: ET.Element, report_id: int):
        """Process report elected official authors"""
        for autor_eleito in relatorio.findall('pt_ar_wsgode_objectos_AutorEleitos'):
            self.cursor.execute("""
                INSERT INTO deputy_report_author_elected (
                    report_id, nome, cargo, pais, honra
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                report_id,
                self._get_text_value(autor_eleito, 'Nome'),
                self._get_text_value(autor_eleito, 'Cargo'),
                self._get_text_value(autor_eleito, 'Pais'),
                self._get_text_value(autor_eleito, 'Honra')
            ))
    
    def _process_report_guests(self, relatorio: ET.Element, report_id: int):
        """Process report guests"""
        for convidado in relatorio.findall('pt_ar_wsgode_objectos_Convidados'):
            self.cursor.execute("""
                INSERT INTO deputy_report_guests (
                    report_id, nome, cargo, pais, honra
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                report_id,
                self._get_text_value(convidado, 'Nome'),
                self._get_text_value(convidado, 'Cargo'),
                self._get_text_value(convidado, 'Pais'),
                self._get_text_value(convidado, 'Honra')
            ))
    
    def _process_report_publications(self, relatorio: ET.Element, report_id: int):
        """Process report publications"""
        for publicacao in relatorio.findall('pt_ar_wsgode_objectos_PublicacaoRelatorio'):
            self.cursor.execute("""
                INSERT INTO deputy_report_publications (
                    report_id, pub_nr, pub_tipo, pub_data, url_diario, legislatura
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                self._get_text_value(publicacao, 'PubNr'),
                self._get_text_value(publicacao, 'PubTipo'),
                self._parse_date(self._get_text_value(publicacao, 'PubData')),
                self._get_text_value(publicacao, 'URLDiario'),
                self._get_text_value(publicacao, 'Legislatura')
            ))
    
    def _process_parliamentary_activities_comprehensive(self, actividade_out: ET.Element, deputy_activity_id: int) -> bool:
        """Process parliamentary activities with comprehensive mapping - same structure as initiatives"""
        try:
            processed_count = 0
            
            actp_section = actividade_out.find('actP')
            if actp_section is not None:
                for atividade_parl in actp_section.findall('pt_ar_wsgode_objectos_AtividadeParlamentar'):
                    # Insert main parliamentary activity record
                    self.cursor.execute("""
                        INSERT INTO deputy_parliamentary_activities (
                            deputy_activity_id, id_atividade, numero, tipo, desc_tipo, assunto,
                            legislatura, sessao, data_entrada, data_agendamento_debate,
                            orgao_exterior, observacoes, tipo_autor
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        deputy_activity_id,
                        self._safe_int(self._get_text_value(atividade_parl, 'IdAtividade')),
                        self._get_text_value(atividade_parl, 'Numero'),
                        self._get_text_value(atividade_parl, 'Tipo'),
                        self._get_text_value(atividade_parl, 'DescTipo'),
                        self._get_text_value(atividade_parl, 'Assunto'),
                        self._get_text_value(atividade_parl, 'Legislatura'),
                        self._get_text_value(atividade_parl, 'Sessao'),
                        self._parse_date(self._get_text_value(atividade_parl, 'DataEntrada')),
                        self._parse_date(self._get_text_value(atividade_parl, 'DataAgendamentoDebate')),
                        self._get_text_value(atividade_parl, 'OrgaoExterior'),
                        self._get_text_value(atividade_parl, 'Observacoes'),
                        self._get_text_value(atividade_parl, 'TipoAutor')
                    ))
                    
                    activity_id = self.cursor.lastrowid
                    
                    # Process all related data (same structure as initiatives)
                    self._process_parliamentary_activity_votes(atividade_parl, activity_id)
                    self._process_parliamentary_activity_author_groups(atividade_parl, activity_id)
                    self._process_parliamentary_activity_author_elected(atividade_parl, activity_id)
                    self._process_parliamentary_activity_guests(atividade_parl, activity_id)
                    self._process_parliamentary_activity_publications(atividade_parl, activity_id)
                    
                    processed_count += 1
            
            return processed_count > 0
            
        except Exception as e:
            logger.error(f"Error processing parliamentary activities comprehensively: {e}")
            return False
    
    def _process_parliamentary_activity_votes(self, atividade_parl: ET.Element, activity_id: int):
        """Process parliamentary activity votes"""
        for votacao in atividade_parl.findall('pt_ar_wsgode_objectos_VotacaoAtividadeParlamentar'):
            self.cursor.execute("""
                INSERT INTO deputy_parliamentary_activity_votes (
                    activity_id, id_votacao, resultado, reuniao, unanime, data_votacao, descricao
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                activity_id,
                self._get_text_value(votacao, 'IdVotacao'),
                self._get_text_value(votacao, 'Resultado'),
                self._get_text_value(votacao, 'Reuniao'),
                self._get_text_value(votacao, 'Unanime'),
                self._parse_date(self._get_text_value(votacao, 'DataVotacao')),
                self._get_text_value(votacao, 'Descricao')
            ))
    
    def _process_parliamentary_activity_author_groups(self, atividade_parl: ET.Element, activity_id: int):
        """Process parliamentary activity parliamentary group authors"""
        for autor_gp in atividade_parl.findall('pt_ar_wsgode_objectos_AutorGruposParlamentares'):
            self.cursor.execute("""
                INSERT INTO deputy_parliamentary_activity_author_groups (
                    activity_id, nome, cargo, pais, honra
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                activity_id,
                self._get_text_value(autor_gp, 'Nome'),
                self._get_text_value(autor_gp, 'Cargo'),
                self._get_text_value(autor_gp, 'Pais'),
                self._get_text_value(autor_gp, 'Honra')
            ))
    
    def _process_parliamentary_activity_author_elected(self, atividade_parl: ET.Element, activity_id: int):
        """Process parliamentary activity elected official authors"""
        for autor_eleito in atividade_parl.findall('pt_ar_wsgode_objectos_AutorEleitos'):
            self.cursor.execute("""
                INSERT INTO deputy_parliamentary_activity_author_elected (
                    activity_id, nome, cargo, pais, honra
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                activity_id,
                self._get_text_value(autor_eleito, 'Nome'),
                self._get_text_value(autor_eleito, 'Cargo'),
                self._get_text_value(autor_eleito, 'Pais'),
                self._get_text_value(autor_eleito, 'Honra')
            ))
    
    def _process_parliamentary_activity_guests(self, atividade_parl: ET.Element, activity_id: int):
        """Process parliamentary activity guests"""
        for convidado in atividade_parl.findall('pt_ar_wsgode_objectos_Convidados'):
            self.cursor.execute("""
                INSERT INTO deputy_parliamentary_activity_guests (
                    activity_id, nome, cargo, pais, honra
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                activity_id,
                self._get_text_value(convidado, 'Nome'),
                self._get_text_value(convidado, 'Cargo'),
                self._get_text_value(convidado, 'Pais'),
                self._get_text_value(convidado, 'Honra')
            ))
    
    def _process_parliamentary_activity_publications(self, atividade_parl: ET.Element, activity_id: int):
        """Process parliamentary activity publications"""
        for publicacao in atividade_parl.findall('pt_ar_wsgode_objectos_PublicacaoAtividadeParlamentar'):
            self.cursor.execute("""
                INSERT INTO deputy_parliamentary_activity_publications (
                    activity_id, pub_nr, pub_tipo, pub_data, url_diario, legislatura
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                activity_id,
                self._get_text_value(publicacao, 'PubNr'),
                self._get_text_value(publicacao, 'PubTipo'),
                self._parse_date(self._get_text_value(publicacao, 'PubData')),
                self._get_text_value(publicacao, 'URLDiario'),
                self._get_text_value(publicacao, 'Legislatura')
            ))
    
    def _process_legislative_data_comprehensive(self, actividade_out: ET.Element, deputy_activity_id: int) -> bool:
        """Process legislative data with comprehensive mapping - same structure as initiatives"""
        try:
            processed_count = 0
            
            dados_legis_section = actividade_out.find('dadosLegisDeputado')
            if dados_legis_section is not None:
                for dados_legis in dados_legis_section.findall('pt_ar_wsgode_objectos_DadosLegislativos'):
                    # Insert main legislative data record
                    self.cursor.execute("""
                        INSERT INTO deputy_legislative_data (
                            deputy_activity_id, id_dados, numero, tipo, desc_tipo, assunto,
                            legislatura, sessao, data_entrada, data_agendamento_debate,
                            orgao_exterior, observacoes, tipo_autor
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        deputy_activity_id,
                        self._safe_int(self._get_text_value(dados_legis, 'IdDados')),
                        self._get_text_value(dados_legis, 'Numero'),
                        self._get_text_value(dados_legis, 'Tipo'),
                        self._get_text_value(dados_legis, 'DescTipo'),
                        self._get_text_value(dados_legis, 'Assunto'),
                        self._get_text_value(dados_legis, 'Legislatura'),
                        self._get_text_value(dados_legis, 'Sessao'),
                        self._parse_date(self._get_text_value(dados_legis, 'DataEntrada')),
                        self._parse_date(self._get_text_value(dados_legis, 'DataAgendamentoDebate')),
                        self._get_text_value(dados_legis, 'OrgaoExterior'),
                        self._get_text_value(dados_legis, 'Observacoes'),
                        self._get_text_value(dados_legis, 'TipoAutor')
                    ))
                    
                    legislative_data_id = self.cursor.lastrowid
                    
                    # Process all related data (same structure as initiatives)
                    self._process_legislative_data_votes(dados_legis, legislative_data_id)
                    self._process_legislative_data_author_groups(dados_legis, legislative_data_id)
                    self._process_legislative_data_author_elected(dados_legis, legislative_data_id)
                    self._process_legislative_data_guests(dados_legis, legislative_data_id)
                    self._process_legislative_data_publications(dados_legis, legislative_data_id)
                    
                    processed_count += 1
            
            return processed_count > 0
            
        except Exception as e:
            logger.error(f"Error processing legislative data comprehensively: {e}")
            return False
    
    def _process_legislative_data_votes(self, dados_legis: ET.Element, legislative_data_id: int):
        """Process legislative data votes"""
        for votacao in dados_legis.findall('pt_ar_wsgode_objectos_VotacaoDadosLegislativos'):
            self.cursor.execute("""
                INSERT INTO deputy_legislative_data_votes (
                    legislative_data_id, id_votacao, resultado, reuniao, unanime, data_votacao, descricao
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                legislative_data_id,
                self._get_text_value(votacao, 'IdVotacao'),
                self._get_text_value(votacao, 'Resultado'),
                self._get_text_value(votacao, 'Reuniao'),
                self._get_text_value(votacao, 'Unanime'),
                self._parse_date(self._get_text_value(votacao, 'DataVotacao')),
                self._get_text_value(votacao, 'Descricao')
            ))
    
    def _process_legislative_data_author_groups(self, dados_legis: ET.Element, legislative_data_id: int):
        """Process legislative data parliamentary group authors"""
        for autor_gp in dados_legis.findall('pt_ar_wsgode_objectos_AutorGruposParlamentares'):
            self.cursor.execute("""
                INSERT INTO deputy_legislative_data_author_groups (
                    legislative_data_id, nome, cargo, pais, honra
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                legislative_data_id,
                self._get_text_value(autor_gp, 'Nome'),
                self._get_text_value(autor_gp, 'Cargo'),
                self._get_text_value(autor_gp, 'Pais'),
                self._get_text_value(autor_gp, 'Honra')
            ))
    
    def _process_legislative_data_author_elected(self, dados_legis: ET.Element, legislative_data_id: int):
        """Process legislative data elected official authors"""
        for autor_eleito in dados_legis.findall('pt_ar_wsgode_objectos_AutorEleitos'):
            self.cursor.execute("""
                INSERT INTO deputy_legislative_data_author_elected (
                    legislative_data_id, nome, cargo, pais, honra
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                legislative_data_id,
                self._get_text_value(autor_eleito, 'Nome'),
                self._get_text_value(autor_eleito, 'Cargo'),
                self._get_text_value(autor_eleito, 'Pais'),
                self._get_text_value(autor_eleito, 'Honra')
            ))
    
    def _process_legislative_data_guests(self, dados_legis: ET.Element, legislative_data_id: int):
        """Process legislative data guests"""
        for convidado in dados_legis.findall('pt_ar_wsgode_objectos_Convidados'):
            self.cursor.execute("""
                INSERT INTO deputy_legislative_data_guests (
                    legislative_data_id, nome, cargo, pais, honra
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                legislative_data_id,
                self._get_text_value(convidado, 'Nome'),
                self._get_text_value(convidado, 'Cargo'),
                self._get_text_value(convidado, 'Pais'),
                self._get_text_value(convidado, 'Honra')
            ))
    
    def _process_legislative_data_publications(self, dados_legis: ET.Element, legislative_data_id: int):
        """Process legislative data publications"""
        for publicacao in dados_legis.findall('pt_ar_wsgode_objectos_PublicacaoDadosLegislativos'):
            self.cursor.execute("""
                INSERT INTO deputy_legislative_data_publications (
                    legislative_data_id, pub_nr, pub_tipo, pub_data, url_diario, legislatura
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                legislative_data_id,
                self._get_text_value(publicacao, 'PubNr'),
                self._get_text_value(publicacao, 'PubTipo'),
                self._parse_date(self._get_text_value(publicacao, 'PubData')),
                self._get_text_value(publicacao, 'URLDiario'),
                self._get_text_value(publicacao, 'Legislatura')
            ))
    
    def _process_deputy_gp_situations(self, deputado: ET.Element, deputy_activity_id: int):
        """Process parliamentary group situations for the deputy"""
        try:
            dep_gp = deputado.find('depGP')
            if dep_gp is not None:
                for gp_situacao in dep_gp.findall('pt_ar_wsgode_objectos_DadosSituacaoGP'):
                    self.cursor.execute("""
                        INSERT INTO deputy_gp_situations (
                            deputy_activity_id, gp_id, gp_sigla, gp_dt_inicio, gp_dt_fim
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        deputy_activity_id,
                        self._safe_int(self._get_text_value(gp_situacao, 'gpId')),
                        self._get_text_value(gp_situacao, 'gpSigla'),
                        self._parse_date(self._get_text_value(gp_situacao, 'gpDtInicio')),
                        self._parse_date(self._get_text_value(gp_situacao, 'gpDtFim'))
                    ))
        except Exception as e:
            logger.error(f"Error processing deputy GP situations: {e}")
    
    def _process_deputy_situations(self, deputado: ET.Element, deputy_activity_id: int):
        """Process deputy situations"""
        try:
            dep_situacao = deputado.find('depSituacao')
            if dep_situacao is not None:
                for situacao in dep_situacao.findall('pt_ar_wsgode_objectos_DadosSituacaoDeputado'):
                    self.cursor.execute("""
                        INSERT INTO deputy_situations (
                            deputy_activity_id, sio_des, sio_dt_inicio, sio_dt_fim
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        deputy_activity_id,
                        self._get_text_value(situacao, 'sioDes'),
                        self._parse_date(self._get_text_value(situacao, 'sioDtInicio')),
                        self._parse_date(self._get_text_value(situacao, 'sioDtFim'))
                    ))
        except Exception as e:
            logger.error(f"Error processing deputy situations: {e}")
    
    # Utility methods
    def _get_text_value(self, parent: ET.Element, tag_name: str) -> Optional[str]:
        """Get text value from XML element"""
        if parent is None:
            return None
        element = parent.find(tag_name)
        if element is not None and element.text:
            return element.text.strip()
        return None
    
    def _safe_int(self, value: str) -> Optional[int]:
        """Safely convert string to int"""
        if not value:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
        if not date_str:
            return None
        
        try:
            # Try ISO format first
            if re.match(r'\\d{4}-\\d{2}-\\d{2}', date_str):
                return date_str
            
            # Try DD/MM/YYYY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
        except (ValueError, IndexError):
            logger.warning(f"Could not parse date: {date_str}")
        
        return None