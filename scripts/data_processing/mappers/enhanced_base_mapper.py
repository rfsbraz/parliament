"""
Enhanced Base Schema Mapper
==========================

Consolidated base classes to eliminate code duplication across all schema mappers.
Provides common functionality for SQLAlchemy session management, legislature handling,
XML processing, and error handling.
"""

import xml.etree.ElementTree as ET
import os
import re
from typing import Dict, List, Set, Optional, Any
import logging
from datetime import datetime
# SQLAlchemy session handling (sessions passed from unified importer)
from abc import ABC, abstractmethod

# Import models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import Legislatura

logger = logging.getLogger(__name__)


class SchemaError(Exception):
    """Raised when schema validation fails - unmapped fields detected"""
    pass


class DatabaseSessionMixin:
    """Mixin providing SQLAlchemy session management"""
    
    def __init__(self, session):
        """Initialize with SQLAlchemy session"""
        # Only accept SQLAlchemy sessions - unified importer passes these
        self.session = session
        self.engine = self.session.bind
        self._owns_session = False
    
    def close_session(self):
        """Close session if we own it"""
        if self._owns_session and self.session:
            self.session.close()
    
    def commit_transaction(self):
        """Commit current transaction"""
        try:
            self.session.commit()
        except Exception as e:
            logger.error(f"Transaction commit failed: {str(e)}")
            import sys
            sys.exit(1)
    
    def rollback_transaction(self):
        """Exit immediately instead of rolling back"""
        logger.error("Data integrity issue detected - exiting immediately")
        import sys
        sys.exit(1)


class LegislatureHandlerMixin:
    """Mixin providing legislature extraction and management"""
    
    # Roman numeral mapping
    ROMAN_TO_NUMBER = {
        'CONSTITUINTE': 0, 'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
        'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11,
        'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17
    }
    
    NUMBER_TO_ROMAN = {v: k for k, v in ROMAN_TO_NUMBER.items()}
    
    def _extract_legislatura(self, file_path: str, xml_root: ET.Element) -> str:
        """Extract legislatura from filename or XML content with comprehensive fallback"""
        # Try filename first - most reliable
        filename = os.path.basename(file_path)
        leg_match = re.search(r'(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)', filename)
        if leg_match:
            return leg_match.group(1)
        
        # Try XML content - multiple possible locations
        xml_patterns = [
            './/Legislatura',
            './/LegDes', 
            './/IniLeg',
            './/leg',
            './/Leg'
        ]
        
        for pattern in xml_patterns:
            leg_element = xml_root.find(pattern)
            if leg_element is not None and leg_element.text:
                leg_text = leg_element.text.strip()
                
                # Handle numeric format
                if leg_text.isdigit():
                    leg_num = int(leg_text)
                    if leg_num in self.NUMBER_TO_ROMAN:
                        return self.NUMBER_TO_ROMAN[leg_num]
                
                # Handle roman numeral format
                if leg_text.upper() in self.ROMAN_TO_NUMBER:
                    return leg_text.upper()
        
        # Final fallback - extract from directory structure
        path_match = re.search(r'/(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)/', file_path)
        if path_match:
            return path_match.group(1)
        
        logger.warning(f"Could not extract legislatura from {file_path}, defaulting to XVII")
        return "XVII"  # Current legislature as fallback
    
    def _get_or_create_legislatura(self, legislatura_sigla: str) -> Legislatura:
        """Get existing or create new legislatura record"""
        if not hasattr(self, 'session'):
            raise AttributeError("Session not available - ensure DatabaseSessionMixin is used")
        
        legislatura = self.session.query(Legislatura).filter_by(numero=legislatura_sigla).first()
        if legislatura:
            return legislatura
        
        # Create new legislatura
        leg_number = self.ROMAN_TO_NUMBER.get(legislatura_sigla, 17)  # Default to XVII
        legislatura = Legislatura(
            numero=legislatura_sigla,
            designacao=f"{leg_number}.ª Legislatura",
            data_inicio=datetime.now().date(),  # Should be updated with real dates
            data_fim=None,
            ativa=False
        )
        
        self.session.add(legislatura)
        logger.info(f"Created new legislatura: {legislatura_sigla}")
        return legislatura


class XMLProcessingMixin:
    """Mixin providing common XML processing utilities"""
    
    @staticmethod
    def safe_text_extract(element: Optional[ET.Element], default: str = "") -> str:
        """Safely extract text from XML element"""
        if element is not None and element.text:
            return element.text.strip()
        return default
    
    @staticmethod
    def safe_int_extract(element: Optional[ET.Element], default: int = 0) -> int:
        """Safely extract integer from XML element"""
        if element is not None and element.text:
            try:
                return int(element.text.strip())
            except ValueError:
                pass
        return default
    
    @staticmethod
    def safe_date_extract(element: Optional[ET.Element], format_str: str = "%Y-%m-%d") -> Optional[datetime]:
        """Safely extract date from XML element"""
        if element is not None and element.text:
            try:
                return datetime.strptime(element.text.strip(), format_str)
            except ValueError:
                # Try alternative formats
                alt_formats = ["%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"]
                for alt_format in alt_formats:
                    try:
                        return datetime.strptime(element.text.strip(), alt_format)
                    except ValueError:
                        continue
        return None
    
    def _collect_field_names(self, element: ET.Element, field_set: Set[str], prefix: str = ""):
        """Recursively collect all field names from XML"""
        current_name = f"{prefix}.{element.tag}" if prefix else element.tag
        field_set.add(current_name)
        
        for child in element:
            self._collect_field_names(child, field_set, current_name)


class EnhancedSchemaMapper(DatabaseSessionMixin, LegislatureHandlerMixin, XMLProcessingMixin, ABC):
    """Enhanced base class for all schema mappers with consolidated functionality"""
    
    def __init__(self, session):
        DatabaseSessionMixin.__init__(self, session)
    
    @abstractmethod
    def get_expected_fields(self) -> Set[str]:
        """Return set of expected XML field names for this schema"""
        pass
    
    @abstractmethod
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Validate XML structure and map to database schema"""
        pass
    
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
                # In strict mode, exit immediately on unmapped fields
                import sys
                logger.error(f"STRICT MODE: Unmapped fields detected in {file_info.get('file_path', 'unknown file')}")
                logger.error(f"Unmapped fields: {unmapped_summary}")
                if len(unmapped_fields) > 10:
                    logger.error(f"... and {len(unmapped_fields) - 10} more unmapped fields")
                logger.error("STRICT MODE: Exiting due to schema coverage violation")
                sys.exit(1)
            else:
                # Normal mode, just log warning
                logger.warning(f"Some unmapped fields found: {unmapped_summary}")
        return unmapped_fields
    
    def process_with_error_handling(self, processing_func, item, error_context: str = "item") -> bool:
        """Common error handling pattern for processing items"""
        try:
            processing_func(item)
            return True
        except Exception as e:
            error_msg = f"{error_context} processing error: {str(e)}"
            logger.error(error_msg)
            logger.error("Data integrity issue detected - exiting immediately")
            import sys
            sys.exit(1)
    
    def create_processing_results(self) -> Dict:
        """Create standard results dictionary"""
        return {
            'records_processed': 0,
            'records_imported': 0,
            'errors': []
        }
    
    def finalize_processing(self, results: Dict) -> Dict:
        """Finalize processing with transaction commit"""
        try:
            self.commit_transaction()
            logger.info(f"Processing completed: {results['records_imported']}/{results['records_processed']} imported")
        except Exception as e:
            logger.error(f"Transaction commit failed: {str(e)}")
            results['errors'].append(f"Transaction commit failed: {str(e)}")
        
        return results
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with proper cleanup"""
        if exc_type:
            logger.error("Exception occurred in context manager - exiting immediately")
            import sys
            sys.exit(1)
        self.close_session()


# Backward compatibility alias
SchemaMapper = EnhancedSchemaMapper