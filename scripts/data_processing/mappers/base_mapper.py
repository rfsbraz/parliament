"""
Base Schema Mapper
==================

Base classes and utilities for all schema mappers in the unified importer system.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)


class SchemaError(Exception):
    """Raised when schema validation fails - unmapped fields detected"""
    pass


class SchemaMapper:
    """Base class for file type schema mappers"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.cursor = db_connection.cursor()
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict) -> Dict:
        """Validate XML structure and map to database schema"""
        raise NotImplementedError("Subclasses must implement validate_and_map")
    
    def get_expected_fields(self) -> Set[str]:
        """Return set of expected XML field names for this schema"""
        raise NotImplementedError("Subclasses must implement get_expected_fields")
    
    def check_schema_coverage(self, xml_root: ET.Element) -> List[str]:
        """Check for unmapped fields in XML"""
        found_fields = set()
        self._collect_field_names(xml_root, found_fields)
        
        expected_fields = self.get_expected_fields()
        unmapped_fields = found_fields - expected_fields
        
        return list(unmapped_fields)
    
    def _collect_field_names(self, element: ET.Element, field_set: Set[str], prefix: str = ""):
        """Recursively collect all field names from XML"""
        current_name = f"{prefix}.{element.tag}" if prefix else element.tag
        field_set.add(current_name)
        
        for child in element:
            self._collect_field_names(child, field_set, current_name)