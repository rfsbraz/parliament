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

__all__ = [
    'DeputyActivityTranslator',
    'InterventionTranslator', 
    'InitiativeTranslator',
    'PublicationTranslator',
    'GeneralActivityTranslator'
]