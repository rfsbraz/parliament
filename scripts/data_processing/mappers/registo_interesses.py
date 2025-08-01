"""
Conflicts of Interest Registry Mapper
=====================================

Schema mapper for conflicts of interest files (RegistoInteresses*.xml).
Handles conflict of interest declarations including marital status, exclusivity, and spouse information.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Optional, Set
import logging
import re
import os

from .base_mapper import SchemaMapper, SchemaError

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import RegistoInteresses, Deputado, Legislatura

logger = logging.getLogger(__name__)


class RegistoInteressesMapper(SchemaMapper):
    """Schema mapper for conflicts of interest registry files"""
    
    def __init__(self, session):
        # Accept SQLAlchemy session directly (passed by unified importer)
        super().__init__(session)
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # Root elements
            'ArrayOfRegistoInteresses',
            'ArrayOfRegistoInteresses.RegistoInteresses',
            
            # V3 Schema (newer format)
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.RecordId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.FullName',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.MaritalStatus',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.SpouseName',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.MatrimonialRegime',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.Exclusivity',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV3.DGFNumber',
            
            # V2 Schema (XII, XIII)
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadNomeCompleto',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadActividadeProfissional',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadEstadoCivilCod',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadEstadoCivilDes',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadFamId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadNomeConjuge',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV2.cadRgi',
            
            # V1 Schema (XI)
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadNomeCompleto',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadActividadeProfissional',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadEstadoCivilCod',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadEstadoCivilDes',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadFamId',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadNomeConjuge',
            'ArrayOfRegistoInteresses.RegistoInteresses.RegistoInteressesV1.cadRgi',
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Validate and map conflicts of interest XML to database"""
        results = {
            'records_processed': 0,
            'records_imported': 0,
            'errors': []
        }
        
        try:
            # Extract legislatura from file path
            legislatura_sigla = self._extract_legislatura(file_info['file_path'])
            if not legislatura_sigla:
                error_msg = f"Could not extract legislatura from file path: {file_info['file_path']}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            # Get or create legislatura
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
            
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Process each RegistoInteresses record
            for registo in xml_root.findall('.//RegistoInteresses'):
                # Try different schema versions
                registo_v3 = registo.find('RegistoInteressesV3')
                registo_v2 = registo.find('RegistoInteressesV2')
                registo_v1 = registo.find('RegistoInteressesV1')
                
                if registo_v3 is not None:
                    # Handle V3 schema (newer format)
                    try:
                        record_id = self._get_text(registo_v3, 'RecordId')
                        full_name = self._get_text(registo_v3, 'FullName')
                        marital_status = self._get_text(registo_v3, 'MaritalStatus')
                        spouse_name = self._get_text(registo_v3, 'SpouseName')
                        matrimonial_regime = self._get_text(registo_v3, 'MatrimonialRegime')
                        exclusivity = self._get_text(registo_v3, 'Exclusivity')
                        dgf_number = self._get_text(registo_v3, 'DGFNumber')
                        
                        success = self._process_v3_record(
                            record_id, full_name, marital_status, spouse_name, 
                            matrimonial_regime, exclusivity, dgf_number, legislatura
                        )
                        if success:
                            results['records_imported'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing V3 conflicts record: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        logger.error("Data integrity issue detected - exiting immediately")
                        import sys
                        sys.exit(1)
                        
                elif registo_v2 is not None:
                    # Handle V2 schema (XII, XIII)
                    try:
                        record_id = self._get_text(registo_v2, 'cadId')
                        full_name = self._get_text(registo_v2, 'cadNomeCompleto')
                        marital_status_desc = self._get_text(registo_v2, 'cadEstadoCivilDes')
                        spouse_name = self._get_text(registo_v2, 'cadNomeConjuge')
                        
                        # V2 doesn't have direct exclusivity/dgf fields, but we can extract from nested rgi data
                        matrimonial_regime = None
                        exclusivity = None
                        dgf_number = None
                        
                        # Try to extract from nested rgi data if available
                        rgi = registo_v2.find('cadRgi/pt_ar_wsgode_objectos_DadosRegistoInteressesWebV2')
                        if rgi is not None:
                            matrimonial_regime = self._get_text(rgi, 'rgiRegimeBensDes')
                        
                        success = self._process_v2_record(
                            record_id, full_name, marital_status_desc, spouse_name,
                            matrimonial_regime, exclusivity, dgf_number, legislatura
                        )
                        if success:
                            results['records_imported'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing V2 conflicts record: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        logger.error("Data integrity issue detected - exiting immediately")
                        import sys
                        sys.exit(1)
                        
                elif registo_v1 is not None:
                    # Handle V1 schema (XI)
                    try:
                        record_id = self._get_text(registo_v1, 'cadId')
                        full_name = self._get_text(registo_v1, 'cadNomeCompleto')
                        marital_status_desc = self._get_text(registo_v1, 'cadEstadoCivilDes')
                        spouse_name = self._get_text(registo_v1, 'cadNomeConjuge')
                        
                        # V1 doesn't have direct exclusivity/dgf fields
                        matrimonial_regime = None
                        exclusivity = None
                        dgf_number = None
                        
                        success = self._process_v1_record(
                            record_id, full_name, marital_status_desc, spouse_name,
                            matrimonial_regime, exclusivity, dgf_number, legislatura
                        )
                        if success:
                            results['records_imported'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing V1 conflicts record: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        logger.error("Data integrity issue detected - exiting immediately")
                        import sys
                        sys.exit(1)
            
            # Commit all changes
            self.session.commit()
            logger.info(f"Imported {results['records_imported']} conflicts of interest records from {file_info['file_path']}")
            
        except Exception as e:
            error_msg = f"Critical error processing conflicts file {file_info['file_path']}: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            logger.error("Data integrity issue detected - exiting immediately")
            import sys
            sys.exit(1)
            return results
        
        return results
    
    def _get_text(self, parent: ET.Element, tag: str) -> Optional[str]:
        """Get text content from child element, return None if not found"""
        element = parent.find(tag)
        if element is not None and element.text:
            return element.text.strip()
        return None
    
    def _extract_legislatura(self, file_path: str) -> Optional[str]:
        """Extract legislatura from file path"""
        # Try different patterns
        patterns = [
            r'Legislatura_([A-Z]+|\d+)',
            r'[/\\]([XVII]+)[/\\]',
            r'([XVII]+)\.xml',
            r'(\d+)\.xml'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, file_path, re.IGNORECASE)
            if match:
                leg = match.group(1).upper()
                # Convert roman numerals to numbers if needed
                roman_map = {
                    'XVII': '17', 'XVI': '16', 'XV': '15', 'XIV': '14', 'XIII': '13',
                    'XII': '12', 'XI': '11', 'X': '10', 'IX': '9', 'VIII': '8',
                    'VII': '7', 'VI': '6', 'V': '5', 'IV': '4', 'III': '3',
                    'II': '2', 'I': '1', 'CONSTITUINTE': '0'
                }
                return roman_map.get(leg, leg)
        
        return None
    
    def _get_or_create_legislatura(self, legislatura_sigla: str) -> Legislatura:
        """Get or create legislatura record"""
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
        """Convert Roman numeral to integer"""
        roman_numerals = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
            'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'CONSTITUINTE': 0
        }
        return roman_numerals.get(roman, 17)
    
    def _get_or_create_deputado(self, record_id: int, full_name: str) -> Deputado:
        """Get or create deputy record"""
        deputado = self.session.query(Deputado).filter_by(id_cadastro=record_id).first()
        
        if deputado:
            return deputado
        
        # Create basic deputy record
        deputado = Deputado(
            id_cadastro=record_id,
            nome=full_name,
            nome_completo=full_name,
            ativo=True
        )
        
        self.session.add(deputado)
        self.session.flush()  # Get the ID
        return deputado
    
    def _process_v3_record(self, record_id: str, full_name: str, marital_status: str, 
                          spouse_name: str, matrimonial_regime: str, exclusivity: str, 
                          dgf_number: str, legislatura: Legislatura) -> bool:
        """Process V3 schema record"""
        try:
            if not record_id or not full_name:
                return False
            
            # Try to find deputy by record_id (assuming it's a cad_id)
            try:
                cad_id = int(record_id)
                deputado = self._get_or_create_deputado(cad_id, full_name)
            except ValueError:
                # If record_id is not numeric, create a dummy deputy
                deputado = self._get_or_create_deputado(0, full_name)
            
            # Check if record already exists
            existing = self.session.query(RegistoInteresses).filter_by(
                deputado_id=deputado.id,
                legislatura_id=legislatura.id,
                record_id=record_id
            ).first()
            
            if existing:
                # Update existing record
                existing.full_name = full_name
                existing.marital_status = marital_status
                existing.spouse_name = spouse_name
                existing.matrimonial_regime = matrimonial_regime
                existing.exclusivity = exclusivity
                existing.dgf_number = dgf_number
                existing.schema_version = "V3"
            else:
                # Create new record
                registo = RegistoInteresses(
                    deputado_id=deputado.id,
                    legislatura_id=legislatura.id,
                    record_id=record_id,
                    full_name=full_name,
                    marital_status=marital_status,
                    spouse_name=spouse_name,
                    matrimonial_regime=matrimonial_regime,
                    exclusivity=exclusivity,
                    dgf_number=dgf_number,
                    schema_version="V3"
                )
                self.session.add(registo)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing V3 record: {e}")
            return False
    
    def _process_v2_record(self, record_id: str, full_name: str, marital_status_desc: str,
                          spouse_name: str, matrimonial_regime: str, exclusivity: str,
                          dgf_number: str, legislatura: Legislatura) -> bool:
        """Process V2 schema record"""
        try:
            if not record_id or not full_name:
                return False
            
            cad_id = int(record_id) if record_id.isdigit() else 0
            deputado = self._get_or_create_deputado(cad_id, full_name)
            
            # Check if record already exists
            existing = self.session.query(RegistoInteresses).filter_by(
                deputado_id=deputado.id,
                legislatura_id=legislatura.id,
                cad_id=cad_id
            ).first()
            
            if existing:
                # Update existing record
                existing.cad_nome_completo = full_name
                existing.cad_estado_civil_des = marital_status_desc
                existing.cad_nome_conjuge = spouse_name
                existing.cad_rgi = matrimonial_regime
                existing.schema_version = "V2"
            else:
                # Create new record
                registo = RegistoInteresses(
                    deputado_id=deputado.id,
                    legislatura_id=legislatura.id,
                    cad_id=cad_id,
                    cad_nome_completo=full_name,
                    cad_estado_civil_des=marital_status_desc,
                    cad_nome_conjuge=spouse_name,
                    cad_rgi=matrimonial_regime,
                    schema_version="V2"
                )
                self.session.add(registo)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing V2 record: {e}")
            return False
    
    def _process_v1_record(self, record_id: str, full_name: str, marital_status_desc: str,
                          spouse_name: str, matrimonial_regime: str, exclusivity: str,
                          dgf_number: str, legislatura: Legislatura) -> bool:
        """Process V1 schema record"""
        try:
            if not record_id or not full_name:
                return False
            
            cad_id = int(record_id) if record_id.isdigit() else 0
            deputado = self._get_or_create_deputado(cad_id, full_name)
            
            # Check if record already exists
            existing = self.session.query(RegistoInteresses).filter_by(
                deputado_id=deputado.id,
                legislatura_id=legislatura.id,
                cad_id=cad_id
            ).first()
            
            if existing:
                # Update existing record
                existing.cad_nome_completo = full_name
                existing.cad_estado_civil_des = marital_status_desc
                existing.cad_nome_conjuge = spouse_name
                existing.schema_version = "V1"
            else:
                # Create new record
                registo = RegistoInteresses(
                    deputado_id=deputado.id,
                    legislatura_id=legislatura.id,
                    cad_id=cad_id,
                    cad_nome_completo=full_name,
                    cad_estado_civil_des=marital_status_desc,
                    cad_nome_conjuge=spouse_name,
                    schema_version="V1"
                )
                self.session.add(registo)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing V1 record: {e}")
            return False