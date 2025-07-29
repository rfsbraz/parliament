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

logger = logging.getLogger(__name__)


class RegistoInteressesMapper(SchemaMapper):
    """Schema mapper for conflicts of interest registry files"""
    
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
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict) -> Dict:
        """Validate and map conflicts of interest XML to database"""
        results = {
            'records_imported': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Extract legislatura from file path
            legislatura = self._extract_legislatura(file_info['file_path'])
            if not legislatura:
                error_msg = f"Could not extract legislatura from file path: {file_info['file_path']}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            # Check schema coverage
            unmapped_fields = self.check_schema_coverage(xml_root)
            if unmapped_fields:
                logger.warning(f"Unmapped fields in {file_info['file_path']}: {unmapped_fields}")
                results['warnings'].extend([f"Unmapped field: {field}" for field in unmapped_fields])
            
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
                        
                        if not record_id or not full_name:
                            results['errors'].append(f"Missing required fields in V3 record")
                            continue
                        
                        self.cursor.execute('''
                            INSERT OR REPLACE INTO conflicts_of_interest 
                            (record_id, legislatura, full_name, marital_status, spouse_name, matrimonial_regime, exclusivity, dgf_number)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (record_id, legislatura, full_name, marital_status, spouse_name, matrimonial_regime, exclusivity, dgf_number))
                        
                        results['records_imported'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing V3 conflicts record: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        
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
                        
                        if not record_id or not full_name:
                            results['errors'].append(f"Missing required fields in V2 record")
                            continue
                        
                        self.cursor.execute('''
                            INSERT OR REPLACE INTO conflicts_of_interest 
                            (record_id, legislatura, full_name, marital_status, spouse_name, matrimonial_regime, exclusivity, dgf_number)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (record_id, legislatura, full_name, marital_status_desc, spouse_name, matrimonial_regime, exclusivity, dgf_number))
                        
                        results['records_imported'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing V2 conflicts record: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        
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
                        
                        if not record_id or not full_name:
                            results['errors'].append(f"Missing required fields in V1 record")
                            continue
                        
                        self.cursor.execute('''
                            INSERT OR REPLACE INTO conflicts_of_interest 
                            (record_id, legislatura, full_name, marital_status, spouse_name, matrimonial_regime, exclusivity, dgf_number)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (record_id, legislatura, full_name, marital_status_desc, spouse_name, matrimonial_regime, exclusivity, dgf_number))
                        
                        results['records_imported'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing V1 conflicts record: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
            
            logger.info(f"Imported {results['records_imported']} conflicts of interest records from {file_info['file_path']}")
            
        except Exception as e:
            error_msg = f"Critical error processing conflicts file {file_info['file_path']}: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            raise SchemaError(error_msg) from e
        
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