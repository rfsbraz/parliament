"""
Initiative Translators
=====================

Translators for parliamentary initiative-related coded fields.
Based on official Parliament documentation (December 2017):
"IniciativasOut" structure from AtividadeDeputado documentation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TipodeIniciativa(Enum):
    """
    Initiative type codes from Portuguese Parliament documentation

    Used in models:
    - IniciativasOut (iniTp field)
    - IniciativaParlamentar (initiative type fields)
    - InitiativeProposal (proposal type fields)

    Documentation Reference:
    - iniTp: "Tipo de iniciativa, campo tipo em TipodeIniciativa"
    - iniTpdesc: "Descrição do tipo de iniciativa, campo descrição em TipodeIniciativa"
    """

    A = "Apreciação Parlamentar"
    C = "Projeto de Revisão Constitucional"
    D = "Projeto de Deliberação"
    F = "Ratificação"
    G = "Projeto de Regimento"
    I = "Inquérito Parlamentar"
    J = "Projeto de Lei"
    P = "Proposta de Lei"
    R = "Projeto de Resolução"
    S = "Proposta de Resolução"
    U = "Iniciativa Popular"


@dataclass
class InitiativeTranslation:
    """Container for initiative field translation results"""

    code: str
    description: str
    category: str = "initiative"
    is_valid: bool = True

    def __str__(self) -> str:
        return self.description


class InitiativeTranslator:
    """
    Translator for initiative-related coded fields

    Usage:
        translator = InitiativeTranslator()

        # Initiative types
        init_desc = translator.initiative_type("J")  # "Projeto de Lei"

        # With metadata
        translation = translator.get_initiative_type("J")
        print(f"Code: {translation.code}, Valid: {translation.is_valid}")
    """

    def initiative_type(self, code: str) -> Optional[str]:
        """Get readable description for initiative type code"""
        translation = self.get_initiative_type(code)
        return translation.description if translation else None

    def get_initiative_type(self, code: str) -> Optional[InitiativeTranslation]:
        """
        Get full translation metadata for initiative type code

        Documentation Reference:
        - Maps iniTp codes to their iniTpdesc descriptions
        - Used across multiple initiative-related models
        """
        if not code:
            return None

        try:
            enum_value = TipodeIniciativa[code.upper()]
            return InitiativeTranslation(
                code=code, description=enum_value.value, is_valid=True
            )
        except KeyError:
            return InitiativeTranslation(
                code=code,
                description=f"Unknown initiative type: {code}",
                is_valid=False,
            )

    def initiative_phase(self, phase_code: str) -> Optional[str]:
        """
        Get readable description for initiative phase

        Documentation Reference:
        - relFase: "Fase da iniciativa em que foi elaborado relatório"
        """
        if not phase_code:
            return None

        # Common phases based on parliamentary procedure
        phase_map = {
            "APRECIACAO": "Apreciação",
            "ESPECIALIDADE": "Especialidade",
            "GENERALIDADE": "Generalidade",
            "VOTACAO_FINAL": "Votação Final",
            "PROMULGACAO": "Promulgação",
            "PUBLICACAO": "Publicação",
        }

        return phase_map.get(phase_code.upper(), f"Phase: {phase_code}")


# Global instance for convenience
initiative_translator = InitiativeTranslator()


def translate_initiative_type(code: str) -> Optional[str]:
    """Quick translation of initiative type code"""
    return initiative_translator.initiative_type(code)
