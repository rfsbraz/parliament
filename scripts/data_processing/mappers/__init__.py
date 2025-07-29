"""
Schema Mappers Package
=====================

This package contains all schema mappers for the unified parliament data importer.
Each mapper handles a specific file type and provides XML-to-database mapping functionality.
"""

from .base_mapper import SchemaMapper, SchemaError
from .registo_biografico import RegistoBiograficoMapper
from .iniciativas import InitiativasMapper
from .intervencoes import IntervencoesMapper
from .registo_interesses import RegistoInteressesMapper
from .atividade_deputados import AtividadeDeputadosMapper

__all__ = [
    'SchemaMapper',
    'SchemaError', 
    'RegistoBiograficoMapper',
    'InitiativasMapper',
    'IntervencoesMapper',
    'RegistoInteressesMapper',
    'AtividadeDeputadosMapper'
]