"""
Orçamento do Estado (State Budget) Mapper
=========================================

Schema mapper for State Budget files covering both formats:
1. OEPropostasAlteracao<numOE>*.xml (Amendment Proposals - Legislaturas X-XV)
2. OE<numOE>*.xml (Budget Items - Legislatura XVI+)

Based on official Parliament documentation (multiple versions):
- "Significado das Tags dos Ficheiros OEPropostasAlteracao<numOE>Or.xml / OEPropostasAlteracao<numOE>Al.xml"
- "Significado das Tags dos Ficheiros OE<numOE>Or.xml / OE<numOE>Al.xml"

XML Structures:
- Legacy: Complex amendment proposal workflow with nested proponents, voting, regional opinions
- Current: Simplified budget item structure with type-based categorization

Key Features:
- Dual format support with automatic structure detection
- Complex nested data processing (proponents, votes, diplomas, initiatives, maps)
- Regional autonomous regions opinion tracking
"""

import logging
import os
import re

# Import our models
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from .common_utilities import DataValidationUtils
from .enhanced_base_mapper import SchemaError, SchemaMapper

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.models import (
    Legislatura,
    OrcamentoEstado,
    OrcamentoEstadoArtigo,
    OrcamentoEstadoArtigoAlinea,
    OrcamentoEstadoArtigoNumero,
    OrcamentoEstadoDiploma,
    OrcamentoEstadoDiplomaAlinea,
    OrcamentoEstadoDiplomaArtigo,
    OrcamentoEstadoDiplomaMedida,
    OrcamentoEstadoDiplomaMedidaNumero,
    OrcamentoEstadoDiplomaNumero,
    OrcamentoEstadoDiplomaTerceiro,
    OrcamentoEstadoGrupoParlamentarVoto,
    OrcamentoEstadoIniciativa,
    OrcamentoEstadoItem,
    OrcamentoEstadoProponente,
    OrcamentoEstadoPropostaAlteracao,
    OrcamentoEstadoRequerimentoAvocacao,
    OrcamentoEstadoVotacao,
)

logger = logging.getLogger(__name__)


class OrcamentoEstadoMapper(SchemaMapper):
    """
    Schema mapper for State Budget files

    Processes both legacy OEPropostasAlteracao and current OE XML structures
    with comprehensive field mapping based on official specifications.

    Handles:
    - Legacy Format (X-XV Legislaturas): Amendment proposal workflow
    - Current Format (XVI+ Legislaturas): Budget item structure
    - Dual structure support with automatic detection
    - Complex nested data (proponents, voting, regional opinions)
    """

    def __init__(self, session):
        super().__init__(session)
        self.processed_proposals = 0
        self.processed_items = 0
        self.processed_proponents = 0
        self.processed_votes = 0
        self.processed_articles = 0
        self.processed_diplomas = 0
        self.processed_initiatives = 0

    def get_expected_fields(self) -> Set[str]:
        """
        Define expected XML fields based on both O_E specifications.
        Covers legacy OEPropostasAlteracao and current OE structures.
        """
        return {
            # Legacy structure (OEPropostasAlteracao) - Complex amendment proposal workflow
            "PropostasDeAlteracao",
            "PropostasDeAlteracao.PropostaDeAlteracao",
            "PropostasDeAlteracao.PropostaDeAlteracao.ID",
            "PropostasDeAlteracao.PropostaDeAlteracao.Numero",
            "PropostasDeAlteracao.PropostaDeAlteracao.Data",
            "PropostasDeAlteracao.PropostaDeAlteracao.Titulo",
            "PropostasDeAlteracao.PropostaDeAlteracao.Tema",
            "PropostasDeAlteracao.PropostaDeAlteracao.Apresentada",
            "PropostasDeAlteracao.PropostaDeAlteracao.Incide",
            "PropostasDeAlteracao.PropostaDeAlteracao.Tipo",
            "PropostasDeAlteracao.PropostaDeAlteracao.Estado",
            "PropostasDeAlteracao.PropostaDeAlteracao.NumeroArtigoNovo",
            "PropostasDeAlteracao.PropostaDeAlteracao.Conteudo",
            "PropostasDeAlteracao.PropostaDeAlteracao.Ficheiro",
            "PropostasDeAlteracao.PropostaDeAlteracao.GrupoParlamentar_Partido",
            # Legacy nested structures
            "PropostasDeAlteracao.PropostaDeAlteracao.Proponentes",
            "PropostasDeAlteracao.PropostaDeAlteracao.Proponentes.Proponente",
            "PropostasDeAlteracao.PropostaDeAlteracao.Proponentes.Proponente.GP_Partido",
            "PropostasDeAlteracao.PropostaDeAlteracao.Proponentes.Proponente.Deputado",
            "PropostasDeAlteracao.PropostaDeAlteracao.PedidoParecerRAA",
            "PropostasDeAlteracao.PropostaDeAlteracao.PedidoParecerRAM",
            "PropostasDeAlteracao.PropostaDeAlteracao.SugeridoParecerRAA",
            "PropostasDeAlteracao.PropostaDeAlteracao.SugeridoParecerRAM",
            "PropostasDeAlteracao.PropostaDeAlteracao.ParecerDasRegioesAutonomas",
            "PropostasDeAlteracao.PropostaDeAlteracao.ParecerDasRegioesAutonomas.Parecer",
            "PropostasDeAlteracao.PropostaDeAlteracao.ParecerDasRegioesAutonomas.Parecer.TipoAssociacao",
            "PropostasDeAlteracao.PropostaDeAlteracao.ParecerDasRegioesAutonomas.Parecer.Titulo",
            "PropostasDeAlteracao.PropostaDeAlteracao.ParecerDasRegioesAutonomas.Parecer.Ficheiro",
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos",
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos.Iniciativa_Artigo",
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos.Iniciativa_Artigo.Artigo",
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos.Iniciativa_Artigo.Titulo",
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos.Iniciativa_Artigo.Texto",
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos.Iniciativa_Artigo.Estado",
            # Nested Numeros and Alineas structures within articles
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos.Iniciativa_Artigo.Numeros",
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos.Iniciativa_Artigo.Numeros.Numero",
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos.Iniciativa_Artigo.Numeros.Titulo",
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos.Iniciativa_Artigo.Numeros.Estado",
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos.Iniciativa_Artigo.Numeros.Alineas",
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos.Iniciativa_Artigo.Numeros.Alineas.Alinea",
            "PropostasDeAlteracao.PropostaDeAlteracao.Iniciativas_Artigos.Iniciativa_Artigo.Numeros.Alineas.Titulo",
            "PropostasDeAlteracao.PropostaDeAlteracao.ProgramasMedidas",
            "PropostasDeAlteracao.PropostaDeAlteracao.ProgramasMedidas.Nome",
            "PropostasDeAlteracao.PropostaDeAlteracao.ProgramasMedidas.Descricao",
            "PropostasDeAlteracao.PropostaDeAlteracao.DiplomasMedidas",
            "PropostasDeAlteracao.PropostaDeAlteracao.DiplomasMedidas.DiplomaMedida",
            "PropostasDeAlteracao.PropostaDeAlteracao.DiplomasMedidas.DiplomaMedida.Titulo",
            "PropostasDeAlteracao.PropostaDeAlteracao.DiplomasMedidas.DiplomaMedida.NumerosMedidas",
            "PropostasDeAlteracao.PropostaDeAlteracao.DiplomasMedidas.DiplomaMedida.NumerosMedidas.NumeroMedida",
            "PropostasDeAlteracao.PropostaDeAlteracao.DiplomasMedidas.DiplomaMedida.NumerosMedidas.NumeroMedida.Designacao",
            "PropostasDeAlteracao.PropostaDeAlteracao.DiplomasMedidas.DiplomaMedida.Texto",
            "PropostasDeAlteracao.PropostaDeAlteracao.Requerimentos",
            "PropostasDeAlteracao.PropostaDeAlteracao.Requerimentos.Requerimento",
            "PropostasDeAlteracao.PropostaDeAlteracao.Requerimentos.Requerimento.Data",
            "PropostasDeAlteracao.PropostaDeAlteracao.Requerimentos.Requerimento.Titulo",
            "PropostasDeAlteracao.PropostaDeAlteracao.Requerimentos.Requerimento.Observacoes",
            "PropostasDeAlteracao.PropostaDeAlteracao.Requerimentos.Requerimento.Aprovado",
            "PropostasDeAlteracao.PropostaDeAlteracao.Requerimentos.Requerimento.Ficheiro",
            "PropostasDeAlteracao.PropostaDeAlteracao.Ministerio",
            "PropostasDeAlteracao.PropostaDeAlteracao.Medidas_Programas",
            "PropostasDeAlteracao.PropostaDeAlteracao.Medidas_Programas.Descricao",
            "PropostasDeAlteracao.PropostaDeAlteracao.Medidas_Programas.SubDescricao",
            "PropostasDeAlteracao.PropostaDeAlteracao.NUTS",
            "PropostasDeAlteracao.PropostaDeAlteracao.NUTS.Descricao",
            "PropostasDeAlteracao.PropostaDeAlteracao.Votacoes",
            "PropostasDeAlteracao.PropostaDeAlteracao.Votacoes.Votacao",
            "PropostasDeAlteracao.PropostaDeAlteracao.Votacoes.Votacao.Descricoes",
            "PropostasDeAlteracao.PropostaDeAlteracao.Votacoes.Votacao.DiplomasTerceirosouPropostasDeLeiMapas",
            "PropostasDeAlteracao.PropostaDeAlteracao.Votacoes.Votacao.DiplomasTerceirosouPropostasDeLeiMapas.Diploma",
            "PropostasDeAlteracao.PropostaDeAlteracao.Votacoes.Votacao.SubDescricao",
            "PropostasDeAlteracao.PropostaDeAlteracao.Votacoes.Votacao.Data",
            "PropostasDeAlteracao.PropostaDeAlteracao.Votacoes.Votacao.ResultadoCompleto",
            "PropostasDeAlteracao.PropostaDeAlteracao.Votacoes.Votacao.Resultado",
            "PropostasDeAlteracao.PropostaDeAlteracao.Votacoes.Votacao.GruposParlamentares",
            "PropostasDeAlteracao.PropostaDeAlteracao.Votacoes.Votacao.GruposParlamentares.GrupoParlamentar",
            "PropostasDeAlteracao.PropostaDeAlteracao.Votacoes.Votacao.GruposParlamentares.Voto",
            # Root wrapper structure
            "Itens",
            "Itens.Item",
            "Itens.Item.ID",
            "Itens.Item.ID_Pai",
            "Itens.Item.Tipo",
            "Itens.Item.Numero",
            "Itens.Item.Titulo",
            "Itens.Item.Texto",
            "Itens.Item.Estado",
            # Itens wrapper nested structures
            "Itens.Item.Artigos",
            "Itens.Item.Artigos.Artigo",
            "Itens.Item.Artigos.Artigo.ID_Art",
            "Itens.Item.Artigos.Artigo.ID_Pai",
            "Itens.Item.Artigos.Artigo.Tipo",
            "Itens.Item.Artigos.Artigo.Numero",
            "Itens.Item.Artigos.Artigo.Titulo",
            "Itens.Item.Artigos.Artigo.Texto",
            "Itens.Item.Artigos.Artigo.Estado",
            "Itens.Item.PropostasDeAlteracao",
            "Itens.Item.PropostasDeAlteracao.Proposta",
            "Itens.Item.PropostasDeAlteracao.Proposta.ID_Pai",
            "Itens.Item.PropostasDeAlteracao.Proposta.ID_PA",
            "Itens.Item.PropostasDeAlteracao.Proposta.Objeto",
            "Itens.Item.PropostasDeAlteracao.Proposta.Data",
            "Itens.Item.PropostasDeAlteracao.Proposta.Apresentado",
            "Itens.Item.PropostasDeAlteracao.Proposta.Incide",
            "Itens.Item.PropostasDeAlteracao.Proposta.Tipo",
            "Itens.Item.PropostasDeAlteracao.Proposta.Estado",
            "Itens.Item.PropostasDeAlteracao.Proposta.Ficheiro",
            "Itens.Item.DiplomasaModificar",
            "Itens.Item.DiplomasaModificar.DiplomaModificar",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.TextoOuEstado",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.ID_Dip",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomaTitulo",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomaSubTitulo",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.ID_Art",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.Numero",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.Titulo",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.Texto",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.Estado",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaArtigoEstado",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaArtigoID",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaArtigoTituto",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaArtigoSubTitulo",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaArtigoTexto",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaNumeroTitulo",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaNumeroEstado",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaNumeroID",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas.DiplomaAlinea",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas.DiplomaAlinea.DiplomaAlineaTitulo",
            "Itens.Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas.DiplomaAlinea.DiplomaAlineaEstado",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.ID_Dip",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomaTitulo",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomaSubTitulo",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.ID_Art",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.Numero",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.Titulo",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.Texto",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.Estado",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaNumeroTitulo",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaNumeroEstado",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas.DiplomaAlinea",
            "Itens.Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas.DiplomaAlinea.DiplomaAlineaTitulo",
            "Itens.Item.IniciativasMapas",
            "Itens.Item.IniciativasMapas.IniciativaMapa",
            "Itens.Item.IniciativasMapas.IniciativaMapa.MapasNumero",
            "Itens.Item.IniciativasMapas.IniciativaMapa.MapasTitulo",
            "Itens.Item.IniciativasMapas.IniciativaMapa.MapasEstado",
            "Itens.Item.IniciativasMapas.IniciativaMapa.MapasLink",
            "Itens.Item.Votacoes",
            "Itens.Item.Votacoes.Votacao",
            "Itens.Item.Votacoes.Votacao.Descricoes",
            "Itens.Item.Votacoes.Votacao.Descricoes.Descricao",
            "Itens.Item.Votacoes.Votacao.DiplomasTerceiros",
            "Itens.Item.Votacoes.Votacao.DiplomasTerceirosouPropostasDeLeiMapas",
            "Itens.Item.Votacoes.Votacao.DiplomasTerceirosouPropostasDeLeiMapas.Diploma",
            "Itens.Item.Votacoes.Votacao.Data",
            "Itens.Item.Votacoes.Votacao.Resultado",
            "Itens.Item.Votacoes.Votacao.ResultadoCompleto",
            "Itens.Item.Votacoes.Votacao.SubDescricao",
            "Itens.Item.Votacoes.Votacao.GruposParlamentares",
            "Itens.Item.Votacoes.Votacao.GruposParlamentares.GrupoParlamentar",
            "Itens.Item.Votacoes.Votacao.GruposParlamentares.Voto",
            "Itens.Item.RequerimentosDeAvocacao",
            "Itens.Item.RequerimentosDeAvocacao.RequerimentoDeAvocacao",
            "Itens.Item.RequerimentosDeAvocacao.RequerimentoDeAvocacao.AvocacaoDescricao",
            "Itens.Item.RequerimentosDeAvocacao.RequerimentoDeAvocacao.AvocacaoData",
            "Itens.Item.RequerimentosDeAvocacao.RequerimentoDeAvocacao.AvocacaoTitulo",
            "Itens.Item.RequerimentosDeAvocacao.RequerimentoDeAvocacao.AvocacaoEstado",
            "Itens.Item.RequerimentosDeAvocacao.RequerimentoDeAvocacao.AvocacaoFicheiro",
            # Current structure (OE) - Simplified budget item structure
            "Item",
            "Item.ID",
            "Item.ID_Pai",
            "Item.Tipo",
            "Item.Numero",
            "Item.Titulo",
            "Item.Texto",
            "Item.Estado",
            "Item.Artigos",
            "Item.Artigos.Artigo",
            "Item.Artigos.Artigo.ID_Art",
            "Item.Artigos.Artigo.ID_Pai",
            "Item.Artigos.Artigo.Tipo",
            "Item.Artigos.Artigo.Numero",
            "Item.Artigos.Artigo.Titulo",
            "Item.Artigos.Artigo.Texto",
            "Item.Artigos.Artigo.Estado",
            "Item.PropostasDeAlteracao",
            "Item.PropostasDeAlteracao.Proposta",
            "Item.PropostasDeAlteracao.Proposta.ID_Pai",
            "Item.PropostasDeAlteracao.Proposta.ID_PA",
            "Item.PropostasDeAlteracao.Proposta.Objeto",
            "Item.PropostasDeAlteracao.Proposta.Data",
            "Item.PropostasDeAlteracao.Proposta.Apresentado",
            "Item.PropostasDeAlteracao.Proposta.Incide",
            "Item.PropostasDeAlteracao.Proposta.Tipo",
            "Item.PropostasDeAlteracao.Proposta.Estado",
            "Item.PropostasDeAlteracao.Proposta.Ficheiro",
            "Item.DiplomasaModificar",
            "Item.DiplomasaModificar.DiplomaModificar",
            "Item.DiplomasaModificar.DiplomaaModificar",
            "Item.DiplomasaModificar.DiplomaaModificar.TextoOuEstado",
            "Item.DiplomasaModificar.DiplomaaModificar.ID_Dip",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomaTitulo",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomaSubTitulo",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.ID_Art",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.Numero",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.Titulo",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.Texto",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.Estado",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaNumeroTitulo",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaNumeroEstado",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas.DiplomaAlinea",
            "Item.DiplomasaModificar.DiplomaaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas.DiplomaAlinea.DiplomaAlineaTitulo",
            "Item.DiplomasaModificar.DiplomaModificar.ID_Dip",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomaTitulo",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomaSubTitulo",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.ID_Art",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.Numero",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.Titulo",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.Texto",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.Estado",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaNumeroTitulo",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaNumeroEstado",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas.DiplomaAlinea",
            "Item.DiplomasaModificar.DiplomaModificar.DiplomasArtigos.DiplomaArtigo.DiplomaNumeros.DiplomaNumero.DiplomaAlineas.DiplomaAlinea.DiplomaAlineaTitulo",
            "Item.IniciativasMapas",
            "Item.IniciativasMapas.IniciativaMapa",
            "Item.IniciativasMapas.IniciativaMapa.MapasNumero",
            "Item.IniciativasMapas.IniciativaMapa.MapasTitulo",
            "Item.IniciativasMapas.IniciativaMapa.MapasEstado",
            "Item.IniciativasMapas.IniciativaMapa.MapasLink",
            "Item.Votacoes",
            "Item.Votacoes.Votacao",
            "Item.Votacoes.Votacao.Descricoes",
            "Item.Votacoes.Votacao.Descricoes.Descricao",
            "Item.Votacoes.Votacao.DiplomasTerceiros",
            "Item.Votacoes.Votacao.DiplomasTerceirosouPropostasDeLeiMapas",
            "Item.Votacoes.Votacao.Data",
            "Item.Votacoes.Votacao.Resultado",
            "Item.RequerimentosDeAvocacao",
            "Item.RequerimentosDeAvocacao.RequerimentoDeAvocacao",
            "Item.RequerimentosDeAvocacao.RequerimentoDeAvocacao.AvocacaoDescricao",
            "Item.RequerimentosDeAvocacao.RequerimentoDeAvocacao.AvocacaoData",
            "Item.RequerimentosDeAvocacao.RequerimentoDeAvocacao.AvocacaoTitulo",
            "Item.RequerimentosDeAvocacao.RequerimentoDeAvocacao.AvocacaoEstado",
            "Item.RequerimentosDeAvocacao.RequerimentoDeAvocacao.AvocacaoFicheiro",
        }

    def validate_and_map(
        self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False
    ) -> Dict:
        """
        Map State Budget data to database with comprehensive field processing

        Supports both legacy OEPropostasAlteracao and current OE structures
        with automatic format detection and appropriate processing.

        Args:
            xml_root: Root XML element
            file_info: Dictionary containing file metadata
            strict_mode: Whether to exit on unmapped fields

        Returns:
            Dictionary with processing results
        """
        # Store for use in nested methods
        self.file_info = file_info

        results = {"records_processed": 0, "records_imported": 0, "errors": []}
        file_path = file_info["file_path"]
        filename = os.path.basename(file_path)

        try:
            logger.info(f"Processing Orçamento do Estado file: {file_path}")

            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)

            # Extract legislatura from filename or path
            legislatura = self._extract_legislatura_from_path(file_path)

            # Determine format type based on root element and filename
            format_type = self._detect_format_type(xml_root, filename)
            logger.info(f"Detected format type: {format_type} for file {filename}")

            if format_type == "legacy":
                # Process legacy OEPropostasAlteracao format
                proposal_elements = xml_root.findall(".//PropostaDeAlteracao")
                logger.info(
                    f"Found {len(proposal_elements)} amendment proposals in legacy format"
                )

                for proposta in proposal_elements:
                    try:
                        success = self._process_legacy_proposal(
                            proposta, legislatura, filename
                        )
                        results["records_processed"] += 1
                        if success:
                            results["records_imported"] += 1
                            self.processed_proposals += 1
                    except Exception as e:
                        error_msg = (
                            f"Legacy proposal processing error in {filename}: {str(e)}"
                        )
                        logger.error(error_msg)
                        results["errors"].append(error_msg)
                        if strict_mode:
                            raise

            elif format_type == "current":
                # Process current OE format
                item_elements = xml_root.findall(".//Item")
                logger.info(
                    f"Found {len(item_elements)} budget items in current format"
                )

                for item in item_elements:
                    try:
                        success = self._process_current_item(
                            item, legislatura, filename
                        )
                        results["records_processed"] += 1
                        if success:
                            results["records_imported"] += 1
                            self.processed_items += 1
                    except Exception as e:
                        error_msg = (
                            f"Current item processing error in {filename}: {str(e)}"
                        )
                        logger.error(error_msg)
                        results["errors"].append(error_msg)
                        if strict_mode:
                            raise
            else:
                error_msg = f"Unknown format type detected for {filename}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                return results

            # Commit all changes
            self.session.commit()

            logger.info(f"Successfully processed Orçamento do Estado file: {file_path}")
            logger.info(
                f"Statistics: {self.processed_proposals} proposals (legacy), "
                f"{self.processed_items} items (current), {self.processed_proponents} proponents, "
                f"{self.processed_votes} votes, {self.processed_articles} articles, "
                f"{self.processed_diplomas} diplomas, {self.processed_initiatives} initiatives"
            )

            return results

        except Exception as e:
            error_msg = f"Critical error processing Orçamento do Estado: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            if strict_mode:
                raise
            return results

    def _detect_format_type(self, xml_root: ET.Element, filename: str) -> str:
        """
        Detect whether this is legacy or current format

        Args:
            xml_root: Root XML element
            filename: Filename for additional context

        Returns:
            'legacy' for OEPropostasAlteracao format, 'current' for OE format
        """
        # Check filename patterns first
        if "OEPropostasAlteracao" in filename:
            return "legacy"
        elif re.match(r"OE\d+.*\.xml", filename):
            return "current"

        # Check root element structure
        if xml_root.find(".//PropostaDeAlteracao") is not None:
            return "legacy"
        elif xml_root.find(".//Item") is not None:
            return "current"

        # Default to current if uncertain
        logger.warning(
            f"Could not definitively determine format type for {filename}, defaulting to current"
        )
        return "current"

    def _extract_legislatura_from_path(self, file_path: str) -> Optional[Legislatura]:
        """
        Extract and get/create legislatura from file path

        Args:
            file_path: Full file path

        Returns:
            Legislatura instance or None
        """
        # Extract legislatura from path patterns
        patterns = [
            r"[/\\]([XVII]+)_Legislatura[/\\]",
            r"[/\\](\d+)_Legislatura[/\\]",
            r"OE(\d+)",
            r"OEPropostasAlteracao(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, file_path)
            if match:
                leg_str = match.group(1)
                # Convert roman to numeric if needed
                roman_map = {
                    "XVII": "17",
                    "XVI": "16",
                    "XV": "15",
                    "XIV": "14",
                    "XIII": "13",
                    "XII": "12",
                    "XI": "11",
                    "X": "10",
                    "IX": "9",
                    "VIII": "8",
                    "VII": "7",
                    "VI": "6",
                    "V": "5",
                    "IV": "4",
                    "III": "3",
                    "II": "2",
                    "I": "1",
                }
                legislatura_num = roman_map.get(leg_str, leg_str)
                break
        else:
            logger.warning(f"Could not extract legislatura from path: {file_path}")
            legislatura_num = "17"  # Default

        # Get or create legislatura
        legislatura = (
            self.session.query(Legislatura).filter_by(numero=legislatura_num).first()
        )
        if not legislatura:
            legislatura = Legislatura(
                numero=legislatura_num,
                designacao=f"Legislatura {legislatura_num}",
                ativa=False,
            )
            self.session.add(legislatura)
            self.session.flush()

        return legislatura

    def _process_legacy_proposal(
        self, proposta: ET.Element, legislatura: Legislatura, filename: str
    ) -> bool:
        """
        Process individual amendment proposal (legacy format)

        Args:
            proposta: PropostaDeAlteracao XML element
            legislatura: Legislatura instance
            filename: Source filename

        Returns:
            Success boolean
        """
        try:
            # Extract basic proposal fields
            proposal_id = DataValidationUtils.safe_float_convert(
                self._get_text_value(proposta, "ID")
            )
            numero = self._get_text_value(proposta, "Numero")
            data_str = self._get_text_value(proposta, "Data")
            titulo = self._get_text_value(proposta, "Titulo")
            tema = self._get_text_value(proposta, "Tema")
            apresentada = self._get_text_value(proposta, "Apresentada")
            incide = self._get_text_value(proposta, "Incide")
            tipo = self._get_text_value(proposta, "Tipo")
            estado = self._get_text_value(proposta, "Estado")
            numero_artigo_novo = self._get_text_value(proposta, "NumeroArtigoNovo")
            conteudo = self._get_text_value(proposta, "Conteudo")
            ficheiro = self._get_text_value(proposta, "Ficheiro")
            grupo_parlamentar = self._get_text_value(
                proposta, "GrupoParlamentar_Partido"
            )

            # Parse date
            data_proposta = None
            if data_str:
                data_proposta = DataValidationUtils.parse_date_flexible(data_str)

            if not proposal_id:
                logger.warning("Legacy proposal missing ID, skipping")
                return False

            # Check if proposal already exists
            existing = (
                self.session.query(OrcamentoEstadoPropostaAlteracao)
                .filter_by(proposta_id=int(proposal_id))
                .first()
            )

            if existing:
                # Update existing
                existing.numero = numero
                existing.data_proposta = data_proposta
                existing.titulo = titulo
                existing.tema = tema
                existing.apresentada = apresentada
                existing.incide = incide
                existing.tipo = tipo
                existing.estado = estado
                existing.numero_artigo_novo = numero_artigo_novo
                existing.conteudo = conteudo
                existing.ficheiro_url = ficheiro
                existing.grupo_parlamentar = grupo_parlamentar
                existing.legislatura_id = legislatura.id
                proposal_obj = existing
            else:
                # Create new
                proposal_obj = OrcamentoEstadoPropostaAlteracao(
                    proposta_id=int(proposal_id),
                    numero=numero,
                    data_proposta=data_proposta,
                    titulo=titulo,
                    tema=tema,
                    apresentada=apresentada,
                    incide=incide,
                    tipo=tipo,
                    estado=estado,
                    numero_artigo_novo=numero_artigo_novo,
                    conteudo=conteudo,
                    ficheiro_url=ficheiro,
                    grupo_parlamentar=grupo_parlamentar,
                    legislatura_id=legislatura.id,
                    format_type="legacy",
                )
                self.session.add(proposal_obj)
                self.session.flush()

            # Process nested data
            self._process_legacy_nested_data(proposta, proposal_obj)

            return True

        except Exception as e:
            logger.error(f"Error processing legacy proposal: {e}")
            return False

    def _process_current_item(
        self, item: ET.Element, legislatura: Legislatura, filename: str
    ) -> bool:
        """
        Process individual budget item (current format)

        Args:
            item: Item XML element
            legislatura: Legislatura instance
            filename: Source filename

        Returns:
            Success boolean
        """
        try:
            # Extract basic item fields
            item_id = DataValidationUtils.safe_float_convert(
                self._get_text_value(item, "ID")
            )
            id_pai = DataValidationUtils.safe_float_convert(
                self._get_text_value(item, "ID_Pai")
            )
            tipo = self._get_text_value(item, "Tipo")
            numero = self._get_text_value(item, "Numero")
            titulo = self._get_text_value(item, "Titulo")
            texto = self._get_text_value(item, "Texto")
            estado = self._get_text_value(item, "Estado")

            if not item_id:
                logger.warning("Current item missing ID, skipping")
                return False

            # Check if item already exists
            existing = (
                self.session.query(OrcamentoEstadoItem)
                .filter_by(item_id=int(item_id))
                .first()
            )

            if existing:
                # Update existing
                existing.id_pai = int(id_pai) if id_pai else None
                existing.tipo = tipo
                existing.numero = numero
                existing.titulo = titulo
                existing.texto = texto
                existing.estado = estado
                existing.legislatura_id = legislatura.id
                item_obj = existing
            else:
                # Create new
                item_obj = OrcamentoEstadoItem(
                    item_id=int(item_id),
                    id_pai=int(id_pai) if id_pai else None,
                    tipo=tipo,
                    numero=numero,
                    titulo=titulo,
                    texto=texto,
                    estado=estado,
                    legislatura_id=legislatura.id,
                    format_type="current",
                )
                self.session.add(item_obj)
                self.session.flush()

            # Process nested data
            self._process_current_nested_data(item, item_obj)

            return True

        except Exception as e:
            logger.error(f"Error processing current item: {e}")
            return False

    def _process_legacy_nested_data(
        self, proposta: ET.Element, proposal_obj: OrcamentoEstadoPropostaAlteracao
    ):
        """Process nested data for legacy format (proponents, votes, etc.)"""
        try:
            # Process Proponentes (Proponents)
            proponentes_elem = proposta.find("Proponentes")
            if proponentes_elem is not None:
                for proponente_elem in proponentes_elem.findall("Proponente"):
                    gp_partido = self._get_text_value(proponente_elem, "GP_Partido")
                    deputado = self._get_text_value(proponente_elem, "Deputado")

                    if gp_partido or deputado:
                        proponente_obj = OrcamentoEstadoProponente(
                            proposta_id=proposal_obj.id,
                            grupo_parlamentar=gp_partido,
                            deputado_nome=deputado,
                            tipo_proponente="deputado" if deputado else "grupo",
                        )
                        self.session.add(proponente_obj)
                        self.processed_proponents += 1

            # Process Votacoes (Voting Records)
            votacoes_elem = proposta.find("Votacoes")
            if votacoes_elem is not None:
                for votacao_elem in votacoes_elem.findall("Votacao"):
                    data_str = self._get_text_value(votacao_elem, "Data")
                    descricoes = self._get_text_value(votacao_elem, "Descricoes")
                    sub_descricao = self._get_text_value(votacao_elem, "SubDescricao")
                    resultado = self._get_text_value(votacao_elem, "ResultadoCompleto")
                    if not resultado:
                        resultado = self._get_text_value(votacao_elem, "Resultado")
                    diplomas_terceiros = self._get_text_value(
                        votacao_elem, "DiplomasTerceiros"
                    )
                    grupos_parlamentares = self._get_text_value(
                        votacao_elem, "GruposParlamentares"
                    )

                    data_votacao = None
                    if data_str:
                        data_votacao = DataValidationUtils.parse_date_flexible(data_str)

                    votacao_obj = OrcamentoEstadoVotacao(
                        proposta_id=proposal_obj.id,
                        data_votacao=data_votacao,
                        descricao=descricoes,
                        sub_descricao=sub_descricao,
                        resultado=resultado,
                        diplomas_terceiros=diplomas_terceiros,
                        grupos_parlamentares=grupos_parlamentares,
                    )
                    self.session.add(votacao_obj)
                    self.processed_votes += 1

            # Process Iniciativas_Artigos (Articles)
            artigos_elem = proposta.find("Iniciativas_Artigos")
            if artigos_elem is not None:
                for artigo_elem in artigos_elem.findall("Iniciativa_Artigo"):
                    numero = self._get_text_value(artigo_elem, "Artigo")
                    titulo = self._get_text_value(artigo_elem, "Titulo")
                    texto = self._get_text_value(artigo_elem, "Texto")
                    estado = self._get_text_value(artigo_elem, "Estado")

                    artigo_obj = OrcamentoEstadoArtigo(
                        proposta_id=proposal_obj.id,
                        numero=numero,
                        titulo=titulo,
                        texto=texto,
                        estado=estado,
                    )
                    self.session.add(artigo_obj)
                    self.processed_articles += 1

            logger.debug(
                f"Processed legacy nested data for proposal {proposal_obj.proposta_id}"
            )

        except Exception as e:
            logger.error(f"Error processing legacy nested data: {e}")
            raise

    def _process_current_nested_data(
        self, item: ET.Element, item_obj: OrcamentoEstadoItem
    ):
        """Process nested data for current format (articles, proposals, etc.)"""
        try:
            # Process Artigos (Articles)
            artigos_elem = item.find("Artigos")
            if artigos_elem is not None:
                for artigo_elem in artigos_elem.findall("Artigo"):
                    artigo_id = DataValidationUtils.safe_float_convert(
                        self._get_text_value(artigo_elem, "ID_Art")
                    )
                    id_pai = DataValidationUtils.safe_float_convert(
                        self._get_text_value(artigo_elem, "ID_Pai")
                    )
                    tipo = self._get_text_value(artigo_elem, "Tipo")
                    numero = self._get_text_value(artigo_elem, "Numero")
                    titulo = self._get_text_value(artigo_elem, "Titulo")
                    texto = self._get_text_value(artigo_elem, "Texto")
                    estado = self._get_text_value(artigo_elem, "Estado")

                    artigo_obj = OrcamentoEstadoArtigo(
                        item_id=item_obj.id,
                        artigo_id=int(artigo_id) if artigo_id else None,
                        id_pai=int(id_pai) if id_pai else None,
                        tipo=tipo,
                        numero=numero,
                        titulo=titulo,
                        texto=texto,
                        estado=estado,
                    )
                    self.session.add(artigo_obj)
                    self.processed_articles += 1

            # Process PropostasDeAlteracao (Amendment Proposals within items)
            propostas_elem = item.find("PropostasDeAlteracao")
            if propostas_elem is not None:
                for proposta_elem in propostas_elem.findall("Proposta"):
                    proposta_id = DataValidationUtils.safe_float_convert(
                        self._get_text_value(proposta_elem, "ID_PA")
                    )
                    id_pai = DataValidationUtils.safe_float_convert(
                        self._get_text_value(proposta_elem, "ID_Pai")
                    )
                    objeto = self._get_text_value(proposta_elem, "Objeto")
                    data_str = self._get_text_value(proposta_elem, "Data")
                    apresentado = self._get_text_value(proposta_elem, "Apresentado")
                    incide = self._get_text_value(proposta_elem, "Incide")
                    tipo = self._get_text_value(proposta_elem, "Tipo")
                    estado = self._get_text_value(proposta_elem, "Estado")
                    ficheiro = self._get_text_value(proposta_elem, "Ficheiro")

                    if proposta_id:
                        data_proposta = None
                        if data_str:
                            data_proposta = DataValidationUtils.parse_date_flexible(
                                data_str
                            )

                        proposta_obj = OrcamentoEstadoPropostaAlteracao(
                            proposta_id=int(proposta_id),
                            id_pai=int(id_pai) if id_pai else None,
                            titulo=objeto,
                            data_proposta=data_proposta,
                            apresentado=apresentado,
                            incide=incide,
                            tipo=tipo,
                            estado=estado,
                            ficheiro_url=ficheiro,
                            legislatura_id=item_obj.legislatura_id,
                            format_type="current",
                        )
                        self.session.add(proposta_obj)
                        self.processed_proposals += 1

            # Process DiplomasaModificar (Diplomas to Modify)
            diplomas_elem = item.find("DiplomasaModificar")
            if diplomas_elem is not None:
                # Check both variants: DiplomaModificar and DiplomaaModificar
                diploma_elements = diplomas_elem.findall(
                    "DiplomaModificar"
                ) + diplomas_elem.findall("DiplomaaModificar")
                for diploma_elem in diploma_elements:
                    diploma_id = DataValidationUtils.safe_float_convert(
                        self._get_text_value(diploma_elem, "ID_Dip")
                    )
                    titulo = self._get_text_value(diploma_elem, "DiplomaTitulo")
                    sub_titulo = self._get_text_value(diploma_elem, "DiplomaSubTitulo")
                    artigos_texto = self._get_text_value(
                        diploma_elem, "DiplomasArtigos"
                    )

                    diploma_obj = OrcamentoEstadoDiploma(
                        item_id=item_obj.id,
                        diploma_id=int(diploma_id) if diploma_id else None,
                        titulo=titulo,
                        sub_titulo=sub_titulo,
                        artigos_texto=artigos_texto,
                    )
                    self.session.add(diploma_obj)
                    self.session.flush()  # Get the ID
                    self.processed_diplomas += 1

                    # Process TextoOuEstado field for DiplomaaModificar variants
                    texto_ou_estado = self._get_text_value(
                        diploma_elem, "TextoOuEstado"
                    )
                    if texto_ou_estado:
                        # Store in appropriate field - could be additional text or state info
                        if not diploma_obj.artigos_texto:
                            diploma_obj.artigos_texto = texto_ou_estado
                        else:
                            diploma_obj.artigos_texto += f" | {texto_ou_estado}"

                    # Process detailed diploma articles (DiplomasArtigos.DiplomaArtigo)
                    diplomas_artigos = diploma_elem.find("DiplomasArtigos")
                    if diplomas_artigos is not None:
                        for diploma_artigo_elem in diplomas_artigos.findall(
                            "DiplomaArtigo"
                        ):
                            artigo_id = self._get_int_value(
                                diploma_artigo_elem, "ID_Art"
                            )
                            diploma_artigo_id_alt = self._get_int_value(
                                diploma_artigo_elem, "DiplomaArtigoID"
                            )
                            artigo_numero = self._get_text_value(
                                diploma_artigo_elem, "Numero"
                            )
                            artigo_titulo = self._get_text_value(
                                diploma_artigo_elem, "Titulo"
                            )
                            diploma_artigo_titulo_alt = self._get_text_value(
                                diploma_artigo_elem, "DiplomaArtigoTituto"
                            )
                            diploma_artigo_subtitulo = self._get_text_value(
                                diploma_artigo_elem, "DiplomaArtigoSubTitulo"
                            )
                            artigo_texto = self._get_text_value(
                                diploma_artigo_elem, "Texto"
                            )
                            diploma_artigo_texto = self._get_text_value(
                                diploma_artigo_elem, "DiplomaArtigoTexto"
                            )
                            artigo_estado = self._get_text_value(
                                diploma_artigo_elem, "Estado"
                            )
                            diploma_artigo_estado = self._get_text_value(
                                diploma_artigo_elem, "DiplomaArtigoEstado"
                            )

                            diploma_artigo_obj = OrcamentoEstadoDiplomaArtigo(
                                diploma_id=diploma_obj.id,
                                artigo_id=artigo_id,
                                diploma_artigo_id_alt=diploma_artigo_id_alt,
                                numero=artigo_numero,
                                titulo=artigo_titulo,
                                diploma_artigo_titulo_alt=diploma_artigo_titulo_alt,
                                diploma_artigo_subtitulo=diploma_artigo_subtitulo,
                                texto=artigo_texto,
                                diploma_artigo_texto=diploma_artigo_texto,
                                estado=artigo_estado,
                                diploma_artigo_estado=diploma_artigo_estado,
                            )
                            self.session.add(diploma_artigo_obj)
                            self.session.flush()  # Get the ID

                            # Process diploma numbers (DiplomaNumeros.DiplomaNumero)
                            diploma_numeros = diploma_artigo_elem.find("DiplomaNumeros")
                            if diploma_numeros is not None:
                                for diploma_numero_elem in diploma_numeros.findall(
                                    "DiplomaNumero"
                                ):
                                    diploma_numero_id = self._get_int_value(
                                        diploma_numero_elem, "DiplomaNumeroID"
                                    )
                                    numero_titulo = self._get_text_value(
                                        diploma_numero_elem, "DiplomaNumeroTitulo"
                                    )
                                    numero_estado = self._get_text_value(
                                        diploma_numero_elem, "DiplomaNumeroEstado"
                                    )

                                    diploma_numero_obj = OrcamentoEstadoDiplomaNumero(
                                        diploma_artigo_id=diploma_artigo_obj.id,
                                        diploma_numero_id=diploma_numero_id,
                                        titulo=numero_titulo,
                                        estado=numero_estado,
                                    )
                                    self.session.add(diploma_numero_obj)
                                    self.session.flush()  # Get the ID

                                    # Process diploma alineas (DiplomaAlineas.DiplomaAlinea)
                                    diploma_alineas = diploma_numero_elem.find(
                                        "DiplomaAlineas"
                                    )
                                    if diploma_alineas is not None:
                                        for (
                                            diploma_alinea_elem
                                        ) in diploma_alineas.findall("DiplomaAlinea"):
                                            alinea_titulo = self._get_text_value(
                                                diploma_alinea_elem,
                                                "DiplomaAlineaTitulo",
                                            )
                                            alinea_estado = self._get_text_value(
                                                diploma_alinea_elem,
                                                "DiplomaAlineaEstado",
                                            )

                                            diploma_alinea_obj = OrcamentoEstadoDiplomaAlinea(
                                                diploma_numero_id=diploma_numero_obj.id,
                                                titulo=alinea_titulo,
                                                estado=alinea_estado,
                                            )
                                            self.session.add(diploma_alinea_obj)

            # Process IniciativasMapas (Initiative Maps)
            iniciativas_elem = item.find("IniciativasMapas")
            if iniciativas_elem is not None:
                for iniciativa_elem in iniciativas_elem.findall("IniciativaMapa"):
                    numero = self._get_text_value(iniciativa_elem, "MapasNumero")
                    titulo = self._get_text_value(iniciativa_elem, "MapasTitulo")
                    estado = self._get_text_value(iniciativa_elem, "MapasEstado")
                    link_url = self._get_text_value(iniciativa_elem, "MapasLink")

                    iniciativa_obj = OrcamentoEstadoIniciativa(
                        item_id=item_obj.id,
                        numero=numero,
                        titulo=titulo,
                        estado=estado,
                        link_url=link_url,
                    )
                    self.session.add(iniciativa_obj)
                    self.processed_initiatives += 1

            # Process Votacoes (Voting Records)
            votacoes_elem = item.find("Votacoes")
            if votacoes_elem is not None:
                for votacao_elem in votacoes_elem.findall("Votacao"):
                    data_str = self._get_text_value(votacao_elem, "Data")
                    descricoes = self._get_text_value(votacao_elem, "Descricoes")

                    # Handle nested Descricoes.Descricao structure
                    if not descricoes:
                        descricoes_elem = votacao_elem.find("Descricoes")
                        if descricoes_elem is not None:
                            descricao_elem = descricoes_elem.find("Descricao")
                            if descricao_elem is not None and descricao_elem.text:
                                descricoes = descricao_elem.text.strip()

                    diplomas_terceiros = self._get_text_value(
                        votacao_elem, "DiplomasTerceiros"
                    )

                    # Handle DiplomasTerceirosouPropostasDeLeiMapas
                    diplomas_terceiros_alt = self._get_text_value(
                        votacao_elem, "DiplomasTerceirosouPropostasDeLeiMapas"
                    )
                    if not diplomas_terceiros and diplomas_terceiros_alt:
                        diplomas_terceiros = diplomas_terceiros_alt
                    elif diplomas_terceiros_alt:
                        # Handle nested Diploma structure
                        diplomas_elem = votacao_elem.find(
                            "DiplomasTerceirosouPropostasDeLeiMapas"
                        )
                        if diplomas_elem is not None:
                            diploma_elems = diplomas_elem.findall("Diploma")
                            if diploma_elems:
                                diploma_texts = [
                                    d.text.strip() for d in diploma_elems if d.text
                                ]
                                if diploma_texts:
                                    diplomas_terceiros += "; " + "; ".join(
                                        diploma_texts
                                    )

                    resultado = self._get_text_value(votacao_elem, "Resultado")
                    resultado_completo = self._get_text_value(
                        votacao_elem, "ResultadoCompleto"
                    )
                    if not resultado and resultado_completo:
                        resultado = resultado_completo

                    sub_descricao = self._get_text_value(votacao_elem, "SubDescricao")

                    # Handle GruposParlamentares structure
                    grupos_parlamentares = self._get_text_value(
                        votacao_elem, "GruposParlamentares"
                    )
                    grupos_elem = votacao_elem.find("GruposParlamentares")
                    if grupos_elem is not None and not grupos_parlamentares:
                        # Process nested GrupoParlamentar and Voto elements
                        grupo_texts = []
                        for grupo_elem in grupos_elem.findall("GrupoParlamentar"):
                            if grupo_elem.text:
                                grupo_texts.append(grupo_elem.text.strip())
                        for voto_elem in grupos_elem.findall("Voto"):
                            if voto_elem.text:
                                grupo_texts.append(f"Voto: {voto_elem.text.strip()}")
                        if grupo_texts:
                            grupos_parlamentares = "; ".join(grupo_texts)

                    data_votacao = None
                    if data_str:
                        data_votacao = DataValidationUtils.parse_date_flexible(data_str)

                    votacao_obj = OrcamentoEstadoVotacao(
                        item_id=item_obj.id,
                        data_votacao=data_votacao,
                        descricao=descricoes,
                        sub_descricao=sub_descricao,
                        resultado=resultado,
                        diplomas_terceiros=diplomas_terceiros,
                        grupos_parlamentares=grupos_parlamentares,
                    )
                    self.session.add(votacao_obj)
                    self.processed_votes += 1

            # Process RequerimentosDeAvocacao (Avocation Requests)
            requerimentos_elem = item.find("RequerimentosDeAvocacao")
            if requerimentos_elem is not None:
                for requerimento_elem in requerimentos_elem.findall(
                    "RequerimentoDeAvocacao"
                ):
                    descricao = self._get_text_value(
                        requerimento_elem, "AvocacaoDescricao"
                    )
                    data_str = self._get_text_value(requerimento_elem, "AvocacaoData")
                    titulo = self._get_text_value(requerimento_elem, "AvocacaoTitulo")
                    estado = self._get_text_value(requerimento_elem, "AvocacaoEstado")
                    ficheiro = self._get_text_value(
                        requerimento_elem, "AvocacaoFicheiro"
                    )

                    data_requerimento = None
                    if data_str:
                        data_requerimento = DataValidationUtils.parse_date_flexible(
                            data_str
                        )

                    requerimento_obj = OrcamentoEstadoRequerimentoAvocacao(
                        item_id=item_obj.id,
                        descricao=descricao,
                        data_requerimento=data_requerimento,
                        titulo=titulo,
                        estado=estado,
                        ficheiro_url=ficheiro,
                    )
                    self.session.add(requerimento_obj)

            logger.debug(f"Processed current nested data for item {item_obj.item_id}")

        except Exception as e:
            logger.error(f"Error processing current nested data: {e}")
            raise

    def _get_text_value(self, element: ET.Element, tag: str) -> Optional[str]:
        """Safely extract text value from XML element"""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None

    def _get_int_value(self, element: ET.Element, tag: str) -> Optional[int]:
        """Safely extract integer value from XML element"""
        text_val = self._get_text_value(element, tag)
        if text_val:
            try:
                return int(text_val)
            except ValueError:
                logger.warning(
                    f"Could not convert '{text_val}' to integer for tag '{tag}'"
                )
                return None
        return None

    def get_processing_stats(self) -> Dict[str, int]:
        """Return processing statistics"""
        return {
            "processed_proposals": self.processed_proposals,
            "processed_items": self.processed_items,
            "processed_proponents": self.processed_proponents,
            "processed_votes": self.processed_votes,
            "processed_articles": self.processed_articles,
            "processed_diplomas": self.processed_diplomas,
            "processed_initiatives": self.processed_initiatives,
        }
