"""
Portuguese Parliament Field Translators
======================================

Thematic field translation modules for Portuguese Parliament data.
Each module contains translators for specific functional areas.
"""

from .deputy_activities import DeputyActivityTranslator
from .parliamentary_interventions import InterventionTranslator  
from .initiatives import InitiativeTranslator
from .publications import PublicationTranslator
from .general_activities import GeneralActivityTranslator
from .agenda_parlamentar import AgendaTranslator
from .delegacao_eventual import DelegacaoEventualTranslator
from .delegacoes_permanentes import DelegacoesPermanentesTranslator
from .diplomas_aprovados import (DIPLOMA_FIELDS, PUBLICACAO_FIELDS, INICIATIVA_FIELDS, 
                                ORCAMENTO_FIELDS, DOCUMENT_FIELDS, ALL_FIELDS,
                                get_field_translation, get_field_description, 
                                get_field_xml_path, get_field_enum)
from .common_enums import TipoParticipante

__all__ = [
    'DeputyActivityTranslator',
    'InterventionTranslator', 
    'InitiativeTranslator',
    'PublicationTranslator',
    'GeneralActivityTranslator',
    'AgendaTranslator',
    'DelegacaoEventualTranslator',
    'DelegacoesPermanentesTranslator',
    'TipoParticipante',
    # Diplomas Aprovados translations
    'DIPLOMA_FIELDS',
    'PUBLICACAO_FIELDS', 
    'INICIATIVA_FIELDS',
    'ORCAMENTO_FIELDS',
    'DOCUMENT_FIELDS',
    'ALL_FIELDS',
    'get_field_translation',
    'get_field_description',
    'get_field_xml_path',
    'get_field_enum'
]