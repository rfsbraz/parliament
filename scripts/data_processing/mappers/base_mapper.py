"""
Base Schema Mapper
==================

Base classes and utilities for all schema mappers in the unified importer system.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Set, Optional
from datetime import datetime, date
import logging
import re
import os

logger = logging.getLogger(__name__)

# XML Namespace Registry
NAMESPACES = {
    'ap': 'http://parlamento.pt/AP/svc/',
    'ar': 'http://ar.parlamento.pt',
    'wsgode': 'http://ar.parlamento.pt/wsgode',
    'tempuri': 'http://tempuri.org/'
}


class SchemaError(Exception):
    """Raised when schema validation fails - unmapped fields detected"""
    pass


class SchemaMapper:
    """Base class for file type schema mappers"""
    
    def __init__(self, session):
        self.session = session
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
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
    
    def validate_schema_coverage(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False):
        """Validate schema coverage and handle unmapped fields according to strict mode"""
        unmapped_fields = self.check_schema_coverage(xml_root)
        if unmapped_fields:
            unmapped_summary = ', '.join(list(unmapped_fields)[:10])
            if strict_mode:
                # In strict mode, raise SchemaError
                logger.error(f"STRICT MODE: Unmapped fields detected in {file_info.get('file_path', 'unknown file')}")
                logger.error(f"Unmapped fields: {unmapped_summary}")
                if len(unmapped_fields) > 10:
                    logger.error(f"... and {len(unmapped_fields) - 10} more unmapped fields")
                logger.error("STRICT MODE: Exiting due to schema coverage violation")
                raise SchemaError(f"Unmapped fields detected: {unmapped_summary}")
            else:
                # Normal mode, just log warning
                logger.warning(f"Some unmapped fields found: {unmapped_summary}")
        return unmapped_fields
    
    def _collect_field_names(self, element: ET.Element, field_set: Set[str], prefix: str = ""):
        """Recursively collect all field names from XML"""
        current_name = f"{prefix}.{element.tag}" if prefix else element.tag
        field_set.add(current_name)
        
        for child in element:
            self._collect_field_names(child, field_set, current_name)
    
    # Common Utility Methods
    def _get_text_value(self, parent: ET.Element, tag_name: str) -> Optional[str]:
        """Get text value from XML element"""
        element = parent.find(tag_name)
        if element is not None and element.text:
            return element.text.strip()
        return None
    
    def _get_int_value(self, parent: ET.Element, tag_name: str) -> Optional[int]:
        """Get integer value from XML element"""
        text_value = self._get_text_value(parent, tag_name)
        if text_value:
            try:
                return int(text_value)
            except ValueError:
                logger.warning(f"Could not convert '{text_value}' to integer for tag '{tag_name}'")
                return None
        return None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object (standardized implementation)"""
        if not date_str:
            return None
        
        try:
            # Handle datetime format: DD/MM/YYYY HH:MM:SS
            if ' ' in date_str:
                date_part = date_str.split(' ')[0]
            else:
                date_part = date_str
            
            # Try DD/MM/YYYY format
            if '/' in date_part:
                parts = date_part.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    return datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", '%Y-%m-%d').date()
            
            # Try ISO format (YYYY-MM-DD)
            if re.match(r'\d{4}-\d{2}-\d{2}', date_part):
                return datetime.strptime(date_part[:10], '%Y-%m-%d').date()
            
            # Try YYYY-MM-DDTHH:MM:SS format
            if 'T' in date_str:
                return datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').date()
                
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
        
        return None
    
    def _get_or_create_legislatura(self, legislatura_sigla: str):
        """Get or create legislatura record (common implementation)"""
        # Import here to avoid circular imports
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        from database.models import Legislatura
        
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
        """Convert Roman numeral to integer (common implementation)"""
        roman_numerals = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
            'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'CONSTITUINTE': 0
        }
        return roman_numerals.get(roman, 17)
    
    def _extract_legislatura(self, file_path: str, xml_root: ET.Element = None) -> str:
        """Extract legislatura from filename or XML content (common implementation)"""
        # Try filename first
        filename = os.path.basename(file_path)
        leg_match = re.search(r'(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)', filename)
        if leg_match:
            return leg_match.group(1)
        
        # Try XML content if provided - look for first Legislatura element
        if xml_root is not None:
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
    
    def _get_namespaced_element(self, parent: ET.Element, namespace_key: str, tag_name: str) -> Optional[ET.Element]:
        """Get element with namespace prefix from registry"""
        if namespace_key in NAMESPACES:
            full_tag = f"{{{NAMESPACES[namespace_key]}}}{tag_name}"
            return parent.find(f".//{full_tag}")
        return parent.find(f".//{tag_name}")
    
    def _get_namespaced_text(self, parent: ET.Element, namespace_key: str, tag_name: str) -> Optional[str]:
        """Get text from namespaced element"""
        element = self._get_namespaced_element(parent, namespace_key, tag_name)
        if element is not None and element.text:
            return element.text.strip()
        return None
    
    def _handle_processing_error(self, error: Exception, error_context: str, strict_mode: bool = False):
        """Standardized error handling for processing errors"""
        error_msg = f"{error_context}: {str(error)}"
        logger.error(error_msg)
        self.session.rollback()
        
        if strict_mode:
            logger.error(f"STRICT MODE: Exiting due to {error_context.lower()}")
            raise SchemaError(f"{error_context} failed in strict mode: {error}")
        
        return error_msg