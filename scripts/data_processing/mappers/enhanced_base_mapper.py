"""
Enhanced Base Schema Mapper
==========================

Consolidated base classes to eliminate code duplication across all schema mappers.
Provides common functionality for SQLAlchemy session management, legislature handling,
XML processing, and error handling.
"""

import logging
import os
import re

# Import models
import sys
import xml.etree.ElementTree as ET

# SQLAlchemy session handling (sessions passed from unified importer)
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.models import Legislatura, Deputado

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
        "CONSTITUINTE": 0,
        "I": 1,
        "II": 2,
        "III": 3,
        "IV": 4,
        "V": 5,
        "VI": 6,
        "VII": 7,
        "VIII": 8,
        "IX": 9,
        "X": 10,
        "XI": 11,
        "XII": 12,
        "XIII": 13,
        "XIV": 14,
        "XV": 15,
        "XVI": 16,
        "XVII": 17,
    }

    NUMBER_TO_ROMAN = {v: k for k, v in ROMAN_TO_NUMBER.items()}

    def _extract_legislatura(self, file_path: str, xml_root: ET.Element) -> str:
        """Extract legislatura from filename or XML content with comprehensive fallback"""

        # Try filename first - most reliable (case-insensitive)
        filename = os.path.basename(file_path)
        # Use specific, ordered patterns to avoid false matches
        # Order by length (longest first) to ensure correct matching
        sorted_legislatures = [
            "CONSTITUINTE",
            "XVII",
            "XVI",
            "XV",
            "XIV",
            "XIII",
            "XII",
            "XI",
            "VIII",
            "VII",
            "VI",
            "IV",
            "III",
            "II",
            "IX",
            "X",
            "V",
            "I",
        ]

        # Check each legislature individually with specific context patterns
        for legislature in sorted_legislatures:
            patterns = [
                # Pattern 1: After known prefixes (RegistoBiografico, Atividade, etc.)
                rf"(Biografico|Atividade.*|Iniciativas|Intervencoes|File|Data){legislature}\.xml$",
                # Pattern 2: After underscore/dash
                rf"[_-]{legislature}\.xml$",
                # Pattern 3: Before underscore/dash
                rf"^{legislature}[_-]",
                # Pattern 4: Standalone at start or end
                rf"^{legislature}([^A-Za-z]|$)",
                rf"[^A-Za-z]{legislature}\.xml$",
            ]

            for i, pattern in enumerate(patterns):
                leg_match = re.search(pattern, filename, re.IGNORECASE)
                if leg_match:
                    return legislature

        # Try XML content - multiple possible locations (only if xml_root is provided)
        if xml_root is not None:
            xml_patterns = [
                ".//Legislatura",
                ".//LegDes",
                ".//IniLeg",
                ".//leg",
                ".//Leg",
            ]

            for pattern in xml_patterns:
                leg_element = xml_root.find(pattern)
                if leg_element is not None and leg_element.text:
                    leg_text = leg_element.text.strip()

                    # Handle numeric format
                    if leg_text.isdigit():
                        leg_num = int(leg_text)
                        if leg_num in self.NUMBER_TO_ROMAN:
                            result = self.NUMBER_TO_ROMAN[leg_num]
                            return result

                    # Handle roman numeral format
                    if leg_text.upper() in self.ROMAN_TO_NUMBER:
                        result = leg_text.upper()
                        return result

                    # Handle partial matches for CONSTITUINTE
                    if leg_text.upper().startswith("CONS"):
                        return "CONSTITUINTE"

        # Final fallback - extract from directory structure (case-insensitive)
        path_match = re.search(
            r"[/\\\\](CONSTITUINTE|XVII|XVI|XV|XIV|XIII|XII|XI|VIII|VII|VI|IV|III|IX|II|X|V|I)_?[Ll]egislatura",
            file_path,
            re.IGNORECASE,
        )
        if path_match:
            result = path_match.group(1).upper()
            return result

        raise SchemaError(f"Could not extract legislatura from file path: {file_path}")

    def _get_or_create_legislatura(self, legislatura_sigla: str) -> Legislatura:
        """Get existing or create new legislatura record"""
        logger.debug(f"_get_or_create_legislatura called with sigla: '{legislatura_sigla}'")
        
        if not hasattr(self, "session"):
            raise AttributeError(
                "Session not available - ensure DatabaseSessionMixin is used"
            )

        # Query for existing legislatura
        logger.debug(f"Querying database for existing legislatura: {legislatura_sigla}")
        legislatura = (
            self.session.query(Legislatura).filter_by(numero=legislatura_sigla).first()
        )
        
        if legislatura:
            logger.debug(f"Found existing legislatura: {legislatura_sigla} (ID: {legislatura.id})")
            return legislatura

        logger.debug(f"Legislatura {legislatura_sigla} not found, creating new one")
        
        # Create new legislatura
        leg_number = self.ROMAN_TO_NUMBER.get(legislatura_sigla, 17)  # Default to XVII
        logger.debug(
            f"Creating new legislatura: sigla='{legislatura_sigla}', number={leg_number}"
        )
        legislatura = Legislatura(
            numero=legislatura_sigla,
            designacao=f"{leg_number}.ª Legislatura",
            data_inicio=datetime.now().date(),  # Should be updated with real dates
            data_fim=None,
            ativa=False,
        )

        logger.debug(f"Adding legislatura {legislatura_sigla} to session")
        self.session.add(legislatura)
        
        logger.debug(f"Flushing session to get ID for legislatura {legislatura_sigla}")
        self.session.flush()  # Flush to get the auto-generated ID
        
        logger.info(f"Created new legislatura: {legislatura_sigla} (ID: {legislatura.id})")
        logger.debug(f"Session state after legislatura creation: {self.session.new}, {self.session.dirty}")
        
        return legislatura

    def _get_legislatura_id(self, file_info: Dict) -> int:
        """
        Extract legislature ID from file info for deputy records.

        Args:
            file_info: Dictionary containing file_path and other metadata

        Returns:
            Legislature ID for use in deputado records
        """
        logger.debug(f"_get_legislatura_id called with file_info: {file_info}")
        
        if not hasattr(self, "session"):
            raise AttributeError(
                "Session not available - ensure DatabaseSessionMixin is used"
            )

        # Extract legislatura sigla from file path
        file_path = file_info.get("file_path", "")
        logger.debug(f"Extracting legislatura from file path: {file_path}")
        legislatura_sigla = self._extract_legislatura(file_path, None)
        logger.debug(f"Extracted legislatura sigla: {legislatura_sigla}")

        # Get or create the legislatura record
        logger.debug(f"Getting or creating legislatura for sigla: {legislatura_sigla}")
        legislatura = self._get_or_create_legislatura(legislatura_sigla)
        logger.debug(f"Got legislatura ID: {legislatura.id}")

        return legislatura.id

    def _get_or_create_deputado(self, record_id: int, id_cadastro: int, nome: str, nome_completo: str = None, legislatura_id: int = None) -> Deputado:
        """
        Get or create deputy record with CORRECT primary key handling
        
        CRITICAL FIX: The issue was that foreign key references in XML data point to deputado.id,
        not id_cadastro. This method uses record_id as the deputado.id (primary key) that other
        records will reference, while id_cadastro tracks the same person across legislatures.
        
        Args:
            record_id: The ID from XML data that becomes deputado.id (primary key for foreign key references)
            id_cadastro: The cadastral ID for linking the same person across legislatures
            nome: Deputy's parliamentary name
            nome_completo: Deputy's full name (optional)
            legislatura_id: Legislature ID (optional, can be derived from context)
            
        Returns:
            Deputado record that can be referenced by its .id field (which equals record_id)
        """
        if not hasattr(self, "session"):
            raise AttributeError("Session not available - ensure DatabaseSessionMixin is used")
        
        # First, check if this specific record_id already exists as primary key
        deputado = self.session.query(Deputado).filter_by(id=record_id).first()
        if deputado:
            # Update with any new information we have
            if nome_completo and not deputado.nome_completo:
                deputado.nome_completo = nome_completo
            if nome and deputado.nome != nome:
                deputado.nome = nome
            return deputado
        
        # Check if this person (by id_cadastro) exists with a different record_id
        existing_person = self.session.query(Deputado).filter_by(id_cadastro=id_cadastro).first()
        if existing_person:
            logger.info(f"Deputy {nome} (cadastro {id_cadastro}) already exists with different record ID {existing_person.id}, creating new record with ID {record_id}")
        
        # Get legislature ID if not provided
        if legislatura_id is None:
            if hasattr(self, 'file_info'):
                legislatura_id = self._get_legislatura_id(self.file_info)
            else:
                # Fallback - get current legislature from context
                raise ValueError("Cannot determine legislature_id - please provide explicitly")
        
        # Create new deputy record with specific record_id as primary key
        deputado = Deputado(
            id=record_id,  # CRITICAL: Use record_id as primary key for foreign key references
            id_cadastro=id_cadastro,  # This tracks the same person across legislatures
            nome=nome,
            nome_completo=nome_completo,
            legislatura_id=legislatura_id,
            ativo=True
        )
        
        self.session.add(deputado)
        self.session.flush()  # Ensure the record gets the correct ID
        
        logger.debug(f"Created deputy record: ID={deputado.id}, cadastro={id_cadastro}, name={nome}")
        return deputado


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
    def safe_date_extract(
        element: Optional[ET.Element], format_str: str = "%Y-%m-%d"
    ) -> Optional[datetime]:
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

    def _collect_field_names(
        self, element: ET.Element, field_set: Set[str], prefix: str = ""
    ):
        """Recursively collect all field names from XML"""
        current_name = f"{prefix}.{element.tag}" if prefix else element.tag
        field_set.add(current_name)

        for child in element:
            self._collect_field_names(child, field_set, current_name)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string with multiple format support"""
        if not date_str or date_str.strip() == "":
            return None

        date_str = date_str.strip()

        # Common date formats in Portuguese parliamentary data
        formats = [
            "%Y-%m-%d",  # 2025-01-15
            "%d-%m-%Y",  # 15-01-2025
            "%Y/%m/%d",  # 2025/01/15
            "%d/%m/%Y",  # 15/01/2025
            "%Y-%m-%dT%H:%M:%S",  # ISO format with time
            "%Y-%m-%d %H:%M:%S",  # Standard datetime
        ]

        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return (
                    parsed_date.date() if hasattr(parsed_date, "date") else parsed_date
                )
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _get_text(self, parent: ET.Element, tag: str) -> Optional[str]:
        """Get text from XML element"""
        if parent is None:
            return None
        element = parent.find(tag)
        if element is not None and element.text:
            return element.text.strip()
        return None

    def _get_namespaced_text(
        self, parent: ET.Element, namespace: str, tag: str
    ) -> Optional[str]:
        """Get text from namespaced XML element"""
        if namespace == "tempuri":
            full_tag = f"{{http://tempuri.org/}}{tag}"
        else:
            full_tag = f"{{{namespace}}}{tag}"

        element = parent.find(full_tag)
        if element is not None and element.text:
            return element.text.strip()
        return None

    def _get_namespaced_element(
        self, parent: ET.Element, namespace: str, tag: str
    ) -> Optional[ET.Element]:
        """Get namespaced XML element"""
        if namespace == "tempuri":
            full_tag = f"{{http://tempuri.org/}}{tag}"
        else:
            full_tag = f"{{{namespace}}}{tag}"

        return parent.find(full_tag)

    def _get_int_text(self, parent: ET.Element, tag: str) -> Optional[int]:
        """Get integer value from XML element text"""
        text = self._get_text(parent, tag)
        if text and text.isdigit():
            return int(text)
        return None

    def _get_text_value(self, parent: ET.Element, tag_name: str) -> Optional[str]:
        """Get text value from XML element - standardized method used across all mappers"""
        if parent is None:
            return None
        try:
            element = parent.find(tag_name)
            if element is not None and element.text:
                return element.text.strip()
            return None
        except AttributeError:
            logger.warning(f"Error accessing element with tag '{tag_name}' from parent")
            return None

    def _get_int_value(self, parent: ET.Element, tag_name: str) -> Optional[int]:
        """Get integer value from XML element - standardized method used across all mappers"""
        text_value = self._get_text_value(parent, tag_name)
        if text_value:
            try:
                # Handle both integer and float strings
                return int(text_value)
            except (ValueError, TypeError):
                return None
        return None

    def _get_boolean_value(self, parent: ET.Element, tag_name: str) -> Optional[bool]:
        """
        Get boolean value from XML element - standardized method used across all mappers
        
        Handles common boolean representations:
        - True: 'true', '1', 'yes', 'sim', 'True', 'TRUE'
        - False: 'false', '0', 'no', 'não', 'False', 'FALSE'
        - None: empty, None, or unrecognized values
        
        Args:
            parent: XML element to search within
            tag_name: Name of the tag to extract boolean from
            
        Returns:
            Optional[bool]: True/False if recognized, None otherwise
        """
        text_value = self._get_text_value(parent, tag_name)
        if text_value is None:
            return None
        
        value_lower = text_value.lower().strip()
        
        # True values (English and Portuguese)
        if value_lower in ('true', '1', 'yes', 'sim'):
            return True
        # False values (English and Portuguese) 
        elif value_lower in ('false', '0', 'no', 'não', 'nao'):
            return False
        
        # Log warning for unrecognized values
        logger.warning(f"Unrecognized boolean value '{text_value}' for tag '{tag_name}', returning None")
        return None

    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int - handles strings, floats, None"""
        if not value:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None


class EnhancedSchemaMapper(
    DatabaseSessionMixin, LegislatureHandlerMixin, XMLProcessingMixin, ABC
):
    """Enhanced base class for all schema mappers with consolidated functionality"""

    def __init__(self, session):
        DatabaseSessionMixin.__init__(self, session)

    @abstractmethod
    def get_expected_fields(self) -> Set[str]:
        """Return set of expected XML field names for this schema"""
        pass

    @abstractmethod
    def validate_and_map(
        self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False
    ) -> Dict:
        """Validate XML structure and map to database schema"""
        pass

    def check_schema_coverage(self, xml_root: ET.Element) -> List[str]:
        """Check for unmapped fields in XML"""
        found_fields = set()
        self._collect_field_names(xml_root, found_fields)

        expected_fields = self.get_expected_fields()
        unmapped_fields = found_fields - expected_fields

        return list(unmapped_fields)

    def validate_schema_coverage(
        self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False
    ):
        """Validate schema coverage and handle unmapped fields according to strict mode"""
        unmapped_fields = self.check_schema_coverage(xml_root)
        if unmapped_fields:
            unmapped_summary = ", ".join(list(unmapped_fields)[:10])
            if strict_mode:
                # In strict mode, exit immediately on unmapped fields
                import sys

                logger.error(
                    f"STRICT MODE: Unmapped fields detected in {file_info.get('file_path', 'unknown file')}"
                )
                logger.error(f"Unmapped fields: {unmapped_summary}")
                if len(unmapped_fields) > 10:
                    logger.error(
                        f"... and {len(unmapped_fields) - 10} more unmapped fields"
                    )
                logger.error("STRICT MODE: Exiting due to schema coverage violation")
                sys.exit(1)
            else:
                # Normal mode, just log warning
                logger.warning(f"Some unmapped fields found: {unmapped_summary}")
        return unmapped_fields

    def process_with_error_handling(
        self, processing_func, item, error_context: str = "item"
    ) -> bool:
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
        return {"records_processed": 0, "records_imported": 0, "errors": []}

    def finalize_processing(self, results: Dict) -> Dict:
        """Finalize processing with transaction commit"""
        try:
            self.commit_transaction()
            logger.info(
                f"Processing completed: {results['records_imported']}/{results['records_processed']} imported"
            )
        except Exception as e:
            logger.error(f"Transaction commit failed: {str(e)}")
            results["errors"].append(f"Transaction commit failed: {str(e)}")

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
