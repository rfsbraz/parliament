"""
Orçamento do Estado (State Budget) Translators
=============================================

Translators for State Budget-related coded fields from both formats:
1. OEPropostasAlteracao (Amendment Proposals) - Legislaturas X-XV
2. OE (Budget Items) - Legislatura XVI+

Based on official Parliament documentation covering both structural formats.

XML Structures:
- Legacy: OEPropostasAlteracao<numOE>Or.xml / OEPropostasAlteracao<numOE>Al.xml
- Current: OE<numOE>Or.xml / OE<numOE>Al.xml
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TipoPropostaAlteracao(Enum):
    """
    Amendment proposal types (Legacy format - OEPropostasAlteracao)
    
    Used in models:
    - OEPropostaAlteracao (tipo field)
    - State Budget amendment proposals
    
    Documentation Reference:
    - tipo: "Tipo de proposta de alteração"
    """
    
    ELIMINACAO = "Eliminação"
    SUBSTITUICAO = "Substituição"
    EMENDA = "Emenda"
    ADITAMENTO = "Aditamento"


class TipoItemOrcamento(Enum):
    """
    Budget item types (Current format - OE)
    
    Used in models:
    - OEItem (tipo field)
    - State Budget item classification
    
    Documentation Reference:
    - tipo: "Tipo de item do orçamento"
    Values:
    - 1: Diplomas a modificar
    - 2: Iniciativas/Artigos
    - 3: Iniciativas/Mapas
    """
    
    DIPLOMAS_MODIFICAR = "1"
    INICIATIVAS_ARTIGOS = "2" 
    INICIATIVAS_MAPAS = "3"


class EstadoPropostaLegacy(Enum):
    """
    Proposal states (Legacy format - OEPropostasAlteracao)
    
    Used in models:
    - OEPropostaAlteracao (estado field)
    - Amendment proposal workflow states
    
    Documentation Reference:
    - estado: "Estado da proposta de alteração"
    """
    
    NAO_ADMITIDA = "Não Admitida"
    ADMITIDA = "Admitida"
    AGUARDA_VOTO_COMISSAO = "Aguarda Voto em Comissão"
    REJEITADO_COMISSAO = "Rejeitado(a) em Comissão"
    APROVADO_COMISSAO = "Aprovado(a) em Comissão"
    AGUARDA_VOTO_PLENARIO = "Aguarda Voto em Plenário"
    REMETIDO_PLENARIO = "Remetido na Plenário"
    REJEITADO_PLENARIO = "Rejeitado(a) em Plenário"
    APROVADO_PLENARIO = "Aprovado(a) em Plenário"
    SUBSTITUIDO = "Substituído(a)"
    PREJUDICADO = "Prejudicado(a)"
    RETIRADO = "Retirado(a)"
    ELIMINADO = "Eliminado(a)"
    AVOCADO = "Avocado(a)"


class EstadoPropostaCurrent(Enum):
    """
    Proposal states (Current format - OE)
    
    Used in models:
    - OEItem (estado field)
    - Budget item proposal states
    
    Documentation Reference:
    - estado: "Estado da proposta"
    """
    
    ADMITIDA = "Admitida"
    AGUARDA_VOTO_COMISSAO = "Aguarda Voto Em Comissão"
    AGUARDA_VOTO_PLENARIO = "Aguarda Voto em Plenário"
    APROVADO_COMISSAO = "Aprovado(a) em Comissão"
    APROVADO_PLENARIO = "Aprovado(a) em Plenário"
    APROVADO_UNANIMIDADE_COMISSAO = "Aprovado(a) por Unanimidade em Comissão"
    AVOCADO = "Avocado(a)"
    ENTRADA = "Entrada"
    NAO_ADMITIDA = "Não Admitida"
    PREJUDICADO = "Prejudicado(a)"
    REJEITADO_COMISSAO = "Rejeitado(a) em Comissão"
    REJEITADO_PLENARIO = "Rejeitado(a) em Plenário"
    REMETIDO_PLENARIO = "Remetido(a) a Plenário"
    RETIRADO = "Retirado(a)"
    SUBSTITUIDO = "Substituído(a)"


class IncidePropostaAlteracao(Enum):
    """
    Amendment proposal scope (Legacy format - OEPropostasAlteracao)
    
    Used in models:
    - OEPropostaAlteracao (incide field)
    - What the amendment proposal affects
    
    Documentation Reference:
    - incide: "A proposta de alteração pode incidir em..."
    """
    
    MAPAS = "Mapas"
    MAPA_PIDAC = "Mapa PIDAC"
    ARTICULADO = "Articulado"


@dataclass
class OrcamentoEstadoTranslation:
    """Container for State Budget field translation results"""
    
    code: str
    description: str
    category: str = "orcamento_estado"
    is_valid: bool = True
    format_type: str = "current"  # "legacy" or "current"
    
    def __str__(self) -> str:
        return self.description


class OrcamentoEstadoTranslator:
    """
    Translator for State Budget-related coded fields
    
    Handles both legacy (OEPropostasAlteracao) and current (OE) formats
    for comprehensive State Budget data processing.
    
    Usage:
        translator = OrcamentoEstadoTranslator()
        
        # Legacy format (OEPropostasAlteracao)
        tipo_desc = translator.tipo_proposta_alteracao_legacy("Eliminação")
        estado_desc = translator.estado_proposta_legacy("Aprovado(a) em Comissão")
        incide_desc = translator.incide_proposta_alteracao("Mapas")
        
        # Current format (OE)
        tipo_desc = translator.tipo_item_orcamento("1")  # "Diplomas a modificar"
        estado_desc = translator.estado_proposta_current("Admitida")
        
        # With metadata
        translation = translator.get_tipo_item_orcamento("2")
        print(f"Code: {translation.code}, Valid: {translation.is_valid}")
    """
    
    def __init__(self):
        pass
    
    # Legacy format methods (OEPropostasAlteracao)
    def tipo_proposta_alteracao_legacy(self, tipo: str) -> Optional[str]:
        """Get description for amendment proposal type (legacy format)"""
        translation = self.get_tipo_proposta_alteracao_legacy(tipo)
        return translation.description if translation else None
    
    def get_tipo_proposta_alteracao_legacy(self, tipo: str) -> Optional[OrcamentoEstadoTranslation]:
        """
        Get full translation metadata for amendment proposal type (legacy format)
        
        Documentation Reference:
        - Maps tipo field to amendment proposal types
        - Used in OEPropostasAlteracao structure
        """
        if not tipo:
            return None
        
        try:
            # Direct string matching for legacy format
            for enum_item in TipoPropostaAlteracao:
                if enum_item.value == tipo:
                    return OrcamentoEstadoTranslation(
                        code=tipo,
                        description=enum_item.value,
                        category="tipo_proposta_alteracao",
                        is_valid=True,
                        format_type="legacy"
                    )
            
            return OrcamentoEstadoTranslation(
                code=tipo,
                description=f"Unknown amendment type: {tipo}",
                category="tipo_proposta_alteracao", 
                is_valid=False,
                format_type="legacy"
            )
        except Exception:
            return OrcamentoEstadoTranslation(
                code=tipo,
                description=f"Unknown amendment type: {tipo}",
                category="tipo_proposta_alteracao",
                is_valid=False,
                format_type="legacy"
            )
    
    def estado_proposta_legacy(self, estado: str) -> Optional[str]:
        """Get description for proposal state (legacy format)"""
        translation = self.get_estado_proposta_legacy(estado)
        return translation.description if translation else None
    
    def get_estado_proposta_legacy(self, estado: str) -> Optional[OrcamentoEstadoTranslation]:
        """
        Get full translation metadata for proposal state (legacy format)
        
        Documentation Reference:
        - Maps estado field to proposal workflow states
        - Used in OEPropostasAlteracao structure
        """
        if not estado:
            return None
        
        try:
            # Direct string matching for legacy format
            for enum_item in EstadoPropostaLegacy:
                if enum_item.value == estado:
                    return OrcamentoEstadoTranslation(
                        code=estado,
                        description=enum_item.value,
                        category="estado_proposta",
                        is_valid=True,
                        format_type="legacy"
                    )
            
            return OrcamentoEstadoTranslation(
                code=estado,
                description=f"Unknown proposal state: {estado}",
                category="estado_proposta",
                is_valid=False,
                format_type="legacy"
            )
        except Exception:
            return OrcamentoEstadoTranslation(
                code=estado,
                description=f"Unknown proposal state: {estado}",
                category="estado_proposta",
                is_valid=False,
                format_type="legacy"
            )
    
    def incide_proposta_alteracao(self, incide: str) -> Optional[str]:
        """Get description for amendment proposal scope"""
        translation = self.get_incide_proposta_alteracao(incide)
        return translation.description if translation else None
    
    def get_incide_proposta_alteracao(self, incide: str) -> Optional[OrcamentoEstadoTranslation]:
        """
        Get full translation metadata for amendment proposal scope
        
        Documentation Reference:
        - Maps incide field to what amendment affects
        - Used in OEPropostasAlteracao structure
        """
        if not incide:
            return None
        
        try:
            # Direct string matching for legacy format
            for enum_item in IncidePropostaAlteracao:
                if enum_item.value == incide:
                    return OrcamentoEstadoTranslation(
                        code=incide,
                        description=enum_item.value,
                        category="incide_proposta_alteracao",
                        is_valid=True,
                        format_type="legacy"
                    )
            
            return OrcamentoEstadoTranslation(
                code=incide,
                description=f"Unknown scope: {incide}",
                category="incide_proposta_alteracao",
                is_valid=False,
                format_type="legacy"
            )
        except Exception:
            return OrcamentoEstadoTranslation(
                code=incide,
                description=f"Unknown scope: {incide}",
                category="incide_proposta_alteracao",
                is_valid=False,
                format_type="legacy"
            )
    
    # Current format methods (OE)
    def tipo_item_orcamento(self, tipo: str) -> Optional[str]:
        """Get description for budget item type (current format)"""
        translation = self.get_tipo_item_orcamento(tipo)
        return translation.description if translation else None
    
    def get_tipo_item_orcamento(self, tipo: str) -> Optional[OrcamentoEstadoTranslation]:
        """
        Get full translation metadata for budget item type (current format)
        
        Documentation Reference:
        - Maps tipo field to budget item types
        - Used in OE structure
        """
        if not tipo:
            return None
        
        tipo_descriptions = {
            "1": "Diplomas a modificar",
            "2": "Iniciativas/Artigos", 
            "3": "Iniciativas/Mapas"
        }
        
        description = tipo_descriptions.get(tipo)
        is_valid = tipo in tipo_descriptions
        
        return OrcamentoEstadoTranslation(
            code=tipo,
            description=description or f"Unknown item type: {tipo}",
            category="tipo_item_orcamento",
            is_valid=is_valid,
            format_type="current"
        )
    
    def estado_proposta_current(self, estado: str) -> Optional[str]:
        """Get description for proposal state (current format)"""
        translation = self.get_estado_proposta_current(estado)
        return translation.description if translation else None
    
    def get_estado_proposta_current(self, estado: str) -> Optional[OrcamentoEstadoTranslation]:
        """
        Get full translation metadata for proposal state (current format)
        
        Documentation Reference:
        - Maps estado field to proposal states
        - Used in OE structure
        """
        if not estado:
            return None
        
        try:
            # Direct string matching for current format
            for enum_item in EstadoPropostaCurrent:
                if enum_item.value == estado:
                    return OrcamentoEstadoTranslation(
                        code=estado,
                        description=enum_item.value,
                        category="estado_proposta",
                        is_valid=True,
                        format_type="current"
                    )
            
            return OrcamentoEstadoTranslation(
                code=estado,
                description=f"Unknown proposal state: {estado}",
                category="estado_proposta",
                is_valid=False,
                format_type="current"
            )
        except Exception:
            return OrcamentoEstadoTranslation(
                code=estado,
                description=f"Unknown proposal state: {estado}",
                category="estado_proposta",
                is_valid=False,
                format_type="current"
            )


# Global instance for convenience
orcamento_estado_translator = OrcamentoEstadoTranslator()


# Legacy format convenience functions
def translate_tipo_proposta_alteracao_legacy(tipo: str) -> Optional[str]:
    """Quick translation of amendment proposal type (legacy format)"""
    return orcamento_estado_translator.tipo_proposta_alteracao_legacy(tipo)


def translate_estado_proposta_legacy(estado: str) -> Optional[str]:
    """Quick translation of proposal state (legacy format)"""
    return orcamento_estado_translator.estado_proposta_legacy(estado)


def translate_incide_proposta_alteracao(incide: str) -> Optional[str]:
    """Quick translation of amendment proposal scope"""
    return orcamento_estado_translator.incide_proposta_alteracao(incide)


# Current format convenience functions
def translate_tipo_item_orcamento(tipo: str) -> Optional[str]:
    """Quick translation of budget item type (current format)"""
    return orcamento_estado_translator.tipo_item_orcamento(tipo)


def translate_estado_proposta_current(estado: str) -> Optional[str]:
    """Quick translation of proposal state (current format)"""
    return orcamento_estado_translator.estado_proposta_current(estado)