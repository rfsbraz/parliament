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
from .common_utilities import DataValidationUtils
from typing import Any, Dict, List, Optional, Set

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.models import Legislatura, Deputado, DeputyIdentityMapping, Coligacao, ColigacaoPartido
from .coalition_detector import CoalitionDetector

logger = logging.getLogger(__name__)


class CoalitionDetectionMixin:
    """Mixin providing coalition detection capabilities to mappers"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.coalition_detector = CoalitionDetector()
        self._coalition_cache = {}  # Cache detection results
    
    def detect_and_process_coalition(self, par_sigla: str, par_des: str = None) -> Dict:
        """
        Detect if par_sigla is a coalition and process accordingly
        
        Returns:
            Dict with coalition information and processing instructions
        """
        if not par_sigla:
            return {"is_coalition": False, "entity_type": "unknown"}
        
        # Check cache first
        if par_sigla in self._coalition_cache:
            return self._coalition_cache[par_sigla]
        
        # Detect coalition
        detection = self.coalition_detector.detect(par_sigla)
        
        result = {
            "is_coalition": detection.is_coalition,
            "entity_type": "coligacao" if detection.is_coalition else "partido", 
            "confidence": detection.confidence,
            "coalition_sigla": par_sigla,  # Use the input sigla as coalition sigla
            "coalition_name": detection.coalition_name,
            "component_parties": detection.component_parties,
            "detection_method": detection.detection_method,
            "political_spectrum": detection.political_spectrum,
            "formation_date": detection.formation_date
        }
        
        # Cache result
        self._coalition_cache[par_sigla] = result
        return result
    
    def get_or_create_coalition(self, coalition_info: Dict) -> Optional[Coligacao]:
        """Create or retrieve coalition record"""
        if not coalition_info["is_coalition"]:
            return None
        
        sigla = coalition_info.get("coalition_sigla", "")
        if not sigla:
            return None
        
        # Try to find existing coalition
        coalition = self.session.query(Coligacao).filter_by(sigla=sigla).first()
        
        if not coalition:
            # Create new coalition
            coalition = Coligacao(
                sigla=sigla,
                nome=coalition_info.get("coalition_name", f"Coligação {sigla}"),
                nome_eleitoral=coalition_info.get("coalition_name"),
                data_formacao=coalition_info.get("formation_date"),
                tipo_coligacao="eleitoral",  # Default type
                espectro_politico=coalition_info.get("political_spectrum"),
                confianca_detecao=coalition_info.get("confidence", 0.0)
                # Note: ativo is now a calculated property based on current legislature XVII deputies
            )
            
            try:
                self.session.add(coalition)
                self.session.flush()  # Get ID without committing
                
                # Create component party relationships
                for component in coalition_info.get("component_parties", []):
                    relationship = ColigacaoPartido(
                        coligacao_id=coalition.id,
                        partido_sigla=component["sigla"],
                        partido_nome=component["nome"],
                        ativo=True,
                        papel_coligacao="componente",
                        confianca_detecao=coalition_info.get("confidence", 0.0)
                    )
                    self.session.add(relationship)
                
                logger.info(f"Created coalition: {sigla} with {len(coalition_info.get('component_parties', []))} components")
                
            except Exception as e:
                logger.error(f"Error creating coalition {sigla}: {e}")
                self.session.rollback()
                return None
        
        return coalition
    
    def update_mandate_coalition_context(self, mandate, par_sigla: str):
        """Update mandate record with coalition context"""
        coalition_info = self.detect_and_process_coalition(par_sigla)
        
        # Update mandate fields
        mandate.tipo_entidade_politica = coalition_info["entity_type"]
        mandate.eh_coligacao = coalition_info["is_coalition"]
        mandate.confianca_detecao_coligacao = coalition_info["confidence"]
        
        # Link to coalition if detected
        if coalition_info["is_coalition"]:
            coalition = self.get_or_create_coalition(coalition_info)
            if coalition:
                mandate.coligacao_id = coalition.id
        
        return mandate


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
        "IA": 1,
        "IB": 1,
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

    # Create NUMBER_TO_ROMAN mapping, preferring main periods over sub-periods
    NUMBER_TO_ROMAN = {
        0: 'CONSTITUINTE', 1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V',
        6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI',
        12: 'XII', 13: 'XIII', 14: 'XIV', 15: 'XV', 16: 'XVI', 17: 'XVII'
    }

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
            "IB",
            "IA",
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
        # Pattern 1: Full legislature directory names (with or without "_Legislatura" suffix)
        path_match = re.search(
            r"[/\\\\](CONSTITUINTE|XVII|XVI|XV|XIV|XIII|XII|XI|VIII|VII|VI|IV|III|IB|IA|IX|II|X|V|I)(_?[Ll]egislatura)?[/\\\\]",
            file_path,
            re.IGNORECASE,
        )
        if path_match:
            result = path_match.group(1).upper()
            return result
            
        # Pattern 2: Legislature names in filename (with word boundaries to avoid false matches)
        filename_match = re.search(
            r"\b(CONSTITUINTE|XVII|XVI|XV|XIV|XIII|XII|XI|VIII|VII|VI|IV|III|IB|IA|IX|II|X|V|I)\b",
            filename,
            re.IGNORECASE,
        )
        if filename_match:
            result = filename_match.group(1).upper()
            return result

        raise SchemaError(f"Could not extract legislatura from file path: {file_path}")

    def _extract_legislatura_from_xml_content(self, leg_des: str) -> str:
        """
        Extract and normalize legislature identifier from XML LegDes content.
        
        This method handles the specific format of legislature identifiers found in
        XML LegDes fields and converts them to our standardized legislature format.
        
        Args:
            leg_des: Legislature identifier from XML (e.g. 'XVII', '17', 'CONSTITUINTE')
            
        Returns:
            Standardized legislature identifier
            
        Examples:
            'XVII' -> 'XVII'
            '17' -> 'XVII' 
            'CONSTITUINTE' -> 'CONSTITUINTE'
        """
        if not leg_des:
            return None
            
        leg_des = leg_des.strip().upper()
        
        # Direct match for known legislature formats
        if leg_des in ['CONSTITUINTE', 'XVII', 'XVI', 'XV', 'XIV', 'XIII', 'XII', 
                       'XI', 'X', 'IX', 'VIII', 'VII', 'VI', 'V', 'IV', 'III', 
                       'II', 'I', 'IA', 'IB']:
            return leg_des
            
        # Convert numeric to roman
        if leg_des.isdigit():
            leg_num = int(leg_des)
            if leg_num in self.NUMBER_TO_ROMAN:
                return self.NUMBER_TO_ROMAN[leg_num]
                
        # Handle special variations
        if leg_des in ['CONS', 'CON', 'CONSTITUENT']:
            return 'CONSTITUINTE'
            
        # Return as-is if we can't normalize it
        logger.warning(f"Unknown legislature format in XML LegDes: '{leg_des}', returning as-is")
        return leg_des

    def _get_or_create_legislatura(self, legislatura_sigla: str) -> Legislatura:
        """Get existing or create new legislatura record by Roman numeral"""
        logger.debug(f"_get_or_create_legislatura called with sigla: '{legislatura_sigla}'")
        
        if not hasattr(self, "session"):
            raise AttributeError(
                "Session not available - ensure DatabaseSessionMixin is used"
            )
        
        # Normalize input
        normalized_sigla = legislatura_sigla.upper().strip()
        
        # Map variations to standard forms
        legislature_mappings = {
            # CONSTITUINTE variations
            "CONSTITUINTE": "CONSTITUINTE",
            "CONSTITUENTE": "CONSTITUINTE", 
            "CONS": "CONSTITUINTE",
            "CONST": "CONSTITUINTE",
            # First legislature variations
            "I": "I",
            "IA": "I", 
            "IB": "I",
            # All other Roman numerals (no variations)
            "II": "II", "III": "III", "IV": "IV", "V": "V", "VI": "VI", 
            "VII": "VII", "VIII": "VIII", "IX": "IX", "X": "X", "XI": "XI", 
            "XII": "XII", "XIII": "XIII", "XIV": "XIV", "XV": "XV", 
            "XVI": "XVI", "XVII": "XVII", "XVIII": "XVIII"
        }
        
        # Get the canonical form
        target_legislature = legislature_mappings.get(normalized_sigla, normalized_sigla)
        logger.debug(f"Mapped '{legislatura_sigla}' to '{target_legislature}'")
        
        # Try to find existing legislatura by numero
        legislatura = self.session.query(Legislatura).filter_by(numero=target_legislature).first()
        
        if legislatura:
            logger.debug(f"Found existing legislatura '{target_legislature}' (ID: {legislatura.id})")
            return legislatura
        
        # Create new legislatura
        logger.debug(f"Creating new legislatura: '{target_legislature}'")
        
        if target_legislature == "CONSTITUINTE":
            designacao = "Assembleia Constituinte"
        else:
            # Get numeric value for designacao
            leg_number = self.ROMAN_TO_NUMBER.get(target_legislature, 0)
            designacao = f"{leg_number}.ª Legislatura" if leg_number > 0 else target_legislature
            
        legislatura = Legislatura(
            numero=target_legislature,
            designacao=designacao,
            data_inicio=None,  # Will be set from XML data
            data_fim=None,
            ativa=False,
        )

        self.session.add(legislatura)
        self.session.flush()  # Get the ID
        
        logger.info(f"Created new legislatura: {target_legislature} (ID: {legislatura.id})")
        return legislatura

    def _get_legislatura_id(self, file_info: Dict) -> int:
        """
        Extract legislature ID from file info for deputy records.

        Args:
            file_info: Dictionary containing file_path and other metadata

        Returns:
            Legislature ID for use in deputado records
        """
        logger.info(f"[LEGISLATURE_ID] Getting legislature ID from file_info: {file_info}")
        
        if not hasattr(self, "session"):
            raise AttributeError(
                "Session not available - ensure DatabaseSessionMixin is used"
            )

        # Extract legislatura sigla from file path
        file_path = file_info.get("file_path", "")
        logger.info(f"[LEGISLATURE_ID] Extracting from file path: {file_path}")
        legislatura_sigla = self._extract_legislatura(file_path, None)
        logger.info(f"[LEGISLATURE_ID] Extracted legislature sigla: '{legislatura_sigla}'")

        # Get or create the legislatura record
        logger.info(f"[LEGISLATURE_ID] Getting or creating legislature record for sigla: '{legislatura_sigla}'")
        legislatura = self._get_or_create_legislatura(legislatura_sigla)
        logger.info(f"[LEGISLATURE_ID] Got legislature with ID={legislatura.id}, numero='{legislatura.numero}'")

        return legislatura.id

    def _get_or_create_deputado(self, record_id: int, id_cadastro: int, nome: str, nome_completo: str = None, legislatura_id: int = None, xml_context: ET.Element = None) -> Deputado:
        """
        Get or create deputy record with CORRECT primary key handling
        
        CRITICAL FIX: The issue was that foreign key references in XML data point to deputado.id,
        not id_cadastro. This method uses record_id as the deputado.id (primary key) that other
        records will reference, while id_cadastro tracks the same person across legislatures.
        
        IMPORTANT: LegDes from XML takes precedence over filename-based legislature extraction
        to handle cases where files contain data for multiple legislatures.
        
        Args:
            record_id: The ID from XML data that becomes deputado.id (primary key for foreign key references)
            id_cadastro: The cadastral ID for linking the same person across legislatures
            nome: Deputy's parliamentary name
            nome_completo: Deputy's full name (optional)
            legislatura_id: Legislature ID (optional, can be derived from context)
            xml_context: XML element context to extract LegDes (takes precedence over filename)
            
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
        
        # Get legislature ID if not provided - prioritize XML LegDes over filename
        if legislatura_id is None:
            # CRITICAL FIX: First try to extract from XML context (LegDes takes precedence)
            if xml_context is not None:
                leg_des = self._get_text_value(xml_context, "LegDes")
                if leg_des:
                    logger.debug(f"Found LegDes '{leg_des}' in XML context for deputy {nome}")
                    # Extract legislature from XML content first
                    try:
                        legislatura_sigla = self._extract_legislatura_from_xml_content(leg_des)
                        if legislatura_sigla:
                            legislatura = self._get_or_create_legislatura(legislatura_sigla)
                            legislatura_id = legislatura.id
                            logger.info(f"Using legislature from XML LegDes '{leg_des}' -> '{legislatura_sigla}' (ID: {legislatura_id}) for deputy {nome}")
                    except Exception as e:
                        logger.warning(f"Failed to extract legislature from XML LegDes '{leg_des}' for deputy {nome}: {e}")
            
            # Fallback to filename-based extraction if XML didn't provide legislature
            if legislatura_id is None:
                if hasattr(self, 'file_info'):
                    legislatura_id = self._get_legislatura_id(self.file_info)
                    logger.debug(f"Using legislature from filename for deputy {nome}: {legislatura_id}")
                else:
                    # Last resort fallback
                    raise ValueError(f"Cannot determine legislature_id for deputy {nome} - no XML LegDes or file context available")
        
        # Create new deputy record with specific record_id as primary key
        deputado = Deputado(
            id=record_id,  # CRITICAL: Use record_id as primary key for foreign key references
            id_cadastro=id_cadastro,  # This tracks the same person across legislatures
            nome=nome,
            nome_completo=nome_completo,
            legislatura_id=legislatura_id
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
        """Parse date string using common flexible date parser"""
        from .common_utilities import DataValidationUtils
        
        parsed = DataValidationUtils.parse_date_flexible(date_str)
        if parsed:
            # Return date object if it's a datetime, otherwise return as-is
            return parsed.date() if hasattr(parsed, 'date') else parsed
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
        # Use _safe_int to properly handle float strings like '8526.0'
        return self._safe_int(text)

    def _get_text_value(self, parent: ET.Element, tag_name: str) -> Optional[str]:
        """Get text value from XML element - standardized method used across all mappers"""
        if parent is None:
            return None
        try:
            element = parent.find(tag_name)
            if element is not None and element.text:
                text = element.text.strip()
                # Fix common Portuguese character encoding issues
                return self._fix_portuguese_characters(text)
            return None
        except AttributeError:
            logger.warning(f"Error accessing element with tag '{tag_name}' from parent")
            return None

    def _fix_portuguese_characters(self, text: str) -> str:
        """Fix common Portuguese character encoding issues"""
        if not text:
            return text
        
        # Specific name corrections for known cases from the error logs
        known_name_fixes = {
            'V?nia Andrea de Castro Jesus': 'Vânia Andrea de Castro Jesus',
            'S?nia Margarida da Silva Fernandes': 'Sónia Margarida da Silva Fernandes', 
            'Sofia Alexandra Correia Pereira': 'Sofia Alexandra Correia Pereira',  # This one seems correct
            'Rui Jorge Cordeiro Gon?alves dos Santos': 'Rui Jorge Cordeiro Gonçalves dos Santos'
        }
        
        # Check for exact match fixes first
        if text in known_name_fixes:
            corrected = known_name_fixes[text]
            logger.info(f"Applied known name correction: '{text}' -> '{corrected}'")
            return corrected
        
        # Log encoding issues for further investigation
        if '?' in text:
            logger.warning(f"Potential Portuguese character encoding issue detected: {text}")
        
        return text

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
        """Safely convert value to int - handles strings, floats, None, and float strings like '7890.0'"""
        if value is None or value == '':
            return None
        try:
            # First try direct int conversion for normal cases
            if isinstance(value, int):
                return value
            elif isinstance(value, float):
                return int(value)
            elif isinstance(value, str):
                # Handle whitespace-only strings
                if not value.strip():
                    return None
                
                stripped_value = value.strip()
                
                # Reject scientific notation (e.g., "1e5", "1.23e4")
                if 'e' in stripped_value.lower():
                    return None
                
                # Handle float format strings like '7890.0' by converting to float first
                float_value = DataValidationUtils.safe_float_convert(stripped_value)
                if float_value is not None:
                    return int(float_value)
            return None
        except (ValueError, TypeError):
            return None


class EnhancedSchemaMapper(
    DatabaseSessionMixin, LegislatureHandlerMixin, XMLProcessingMixin, CoalitionDetectionMixin, ABC
):
    """Enhanced base class for all schema mappers with consolidated functionality"""

    def __init__(self, session):
        DatabaseSessionMixin.__init__(self, session)
        CoalitionDetectionMixin.__init__(self)

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

    def _find_deputy_robust(
        self, cad_id: int, nome_completo: str = None, nome_parlamentar: str = None, legislatura_id: int = None
    ) -> Deputado:
        """
        Robust deputy matching with cadastral ID change tracking.

        This method handles cases where deputy cadastral IDs change over time by implementing
        a multi-level matching strategy and tracking identity mappings.

        Args:
            cad_id: Current cadastral ID to look up
            nome_completo: Full deputy name for fallback matching
            nome_parlamentar: Parliamentary name for fallback matching
            legislatura_id: Legislature ID to scope the search (CRITICAL FIX)

        Returns:
            Deputado: The matched deputy record

        Raises:
            ValueError: If no deputy can be matched using any strategy
        """
        # Step 1: Try direct cadastral ID lookup within the current legislature
        query = self.session.query(Deputado).filter(Deputado.id_cadastro == cad_id)
        
        # CRITICAL FIX: Scope to specific legislature if provided
        if legislatura_id is not None:
            query = query.filter(Deputado.legislatura_id == legislatura_id)
        
        deputy = query.first()
        if deputy:
            return deputy

        # Step 2: Check if this cadastral ID is mapped to another ID
        identity_mapping = (
            self.session.query(DeputyIdentityMapping)
            .filter(DeputyIdentityMapping.old_cad_id == cad_id)
            .first()
        )

        if identity_mapping:
            # Try to find deputy with the new cadastral ID within the current legislature
            query = self.session.query(Deputado).filter(Deputado.id_cadastro == identity_mapping.new_cad_id)
            
            if legislatura_id is not None:
                query = query.filter(Deputado.legislatura_id == legislatura_id)
                
            deputy = query.first()
            if deputy:
                logger.info(
                    f"Found deputy via identity mapping: old_cad_id={cad_id} -> new_cad_id={identity_mapping.new_cad_id}"
                )
                return deputy

        # Step 3: Fallback to name-based matching if names are provided
        if nome_completo or nome_parlamentar:
            query = self.session.query(Deputado)
            
            # Scope to current legislature if provided
            if legislatura_id is not None:
                query = query.filter(Deputado.legislatura_id == legislatura_id)

            # Try full name match first
            if nome_completo:
                deputy = query.filter(
                    Deputado.nome_completo.ilike(f"%{nome_completo}%")
                ).first()
                if deputy:
                    # Record the identity mapping for future lookups
                    # deputy.id_cadastro is the OLD ID (existing in DB), cad_id is the NEW ID (we're trying to find)
                    self._record_identity_mapping(
                        deputy.id_cadastro, cad_id, nome_completo or nome_parlamentar, deputy
                    )
                    logger.info(
                        f"Deputy found by full name match - recording identity mapping: old_cad_id={deputy.id_cadastro} -> new_cad_id={cad_id} ({nome_completo})"
                    )
                    return deputy

            # Try parliamentary name match
            if nome_parlamentar:
                deputy = query.filter(
                    Deputado.nome.ilike(f"%{nome_parlamentar}%")
                ).first()
                if deputy:
                    # Record the identity mapping for future lookups
                    # deputy.id_cadastro is the OLD ID (existing in DB), cad_id is the NEW ID (we're trying to find)
                    self._record_identity_mapping(
                        deputy.id_cadastro, cad_id, nome_parlamentar, deputy
                    )
                    logger.info(
                        f"Deputy found by parliamentary name match - recording identity mapping: old_cad_id={deputy.id_cadastro} -> new_cad_id={cad_id} ({nome_parlamentar})"
                    )
                    return deputy

        # Step 4: No match found using any strategy
        names = []
        if nome_completo:
            names.append(f"nome_completo='{nome_completo}'")
        if nome_parlamentar:
            names.append(f"nome_parlamentar='{nome_parlamentar}'")
        name_info = " (" + ", ".join(names) + ")" if names else ""
        
        legislature_info = f" in legislature {legislatura_id}" if legislatura_id else ""

        raise ValueError(
            f"Deputy with cadId {cad_id} not found in database using any matching strategy{name_info}{legislature_info}"
        )

    def _record_identity_mapping(
        self, old_cad_id: int, new_cad_id: int, deputy_name: str, deputy: Deputado
    ):
        """Record an identity mapping between old and new cadastral IDs and update the deputy record."""
        # Flush session to ensure any pending objects are written to DB for query
        self.session.flush()
        
        # Check if mapping already exists (including any just flushed)
        existing_mapping = (
            self.session.query(DeputyIdentityMapping)
            .filter(
                DeputyIdentityMapping.old_cad_id == old_cad_id,
                DeputyIdentityMapping.new_cad_id == new_cad_id,
            )
            .first()
        )

        if existing_mapping:
            logger.debug(f"Identity mapping {old_cad_id} -> {new_cad_id} already exists, skipping")
            return

        # Record the identity mapping
        mapping = DeputyIdentityMapping(
            old_cad_id=old_cad_id,
            new_cad_id=new_cad_id,
            deputy_name=deputy_name,
            confidence_score=90,  # Discovered via name matching
            verified=False,
        )
        self.session.add(mapping)

        # Update deputy's current cadastral ID to the new value
        deputy.id_cadastro = new_cad_id
        logger.info(f"Updated deputy cadastral ID: {old_cad_id} -> {new_cad_id} for {deputy_name}")


# Backward compatibility alias
SchemaMapper = EnhancedSchemaMapper
