"""
Approved Diplomas Mapper
========================

Schema mapper for approved diplomas files (Diplomas*.xml).
Handles parliamentary diplomas including laws, decrees, and resolutions.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging

from .base_mapper import SchemaMapper, SchemaError

logger = logging.getLogger(__name__)


class DiplomasAprovadosMapper(SchemaMapper):
    """Schema mapper for approved diplomas files"""
    
    def get_expected_fields(self) -> Set[str]:
        return {
            'ArrayOfDiplomaOut', 'DiplomaOut', 'Id', 'Numero', 'Titulo', 'Tipo', 
            'Legislatura', 'Sessao', 'AnoCivil', 'LinkTexto', 'Numero2', 'Observacoes',
            'Tp', 'Actividades', 'string',
            # Publication data
            'Publicacao', 'pt_gov_ar_objectos_PublicacoesOut', 'pubNr', 'pubTipo', 
            'pubTp', 'pubLeg', 'pubSL', 'pubdt', 'pag', 'idPag', 'URLDiario', 
            'supl', 'obs', 'pagFinalDiarioSupl',
            # Initiative data
            'Iniciativas', 'DiplomaIniciativaOut', 'IniNr', 'IniTipo', 'IniLinkTexto', 'IniId'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict) -> Dict:
        """Map approved diplomas to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        unmapped_fields = self.check_schema_coverage(xml_root)
        if unmapped_fields:
            logger.warning(f"Some unmapped fields found: {', '.join(list(unmapped_fields)[:10])}")
        
        # Extract legislatura from filename or XML
        legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
        legislatura_id = self._get_or_create_legislatura(legislatura_sigla)
        
        # Process diplomas
        for diploma in xml_root.findall('.//DiplomaOut'):
            try:
                success = self._process_diploma(diploma, legislatura_id)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Diploma processing error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['records_processed'] += 1
        
        return results
    
    def _extract_legislatura(self, file_path: str, xml_root: ET.Element) -> str:
        """Extract legislatura from filename or XML content"""
        # Try filename first
        filename = os.path.basename(file_path)
        leg_match = re.search(r'(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)', filename)
        if leg_match:
            return leg_match.group(1)
        
        # Try XML content - look for first Legislatura element
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
    
    def _process_diploma(self, diploma: ET.Element, legislatura_id: int) -> bool:
        """Process individual diploma"""
        try:
            # Extract basic fields
            diploma_id = self._get_int_value(diploma, 'Id')
            numero = self._get_int_value(diploma, 'Numero')
            titulo = self._get_text_value(diploma, 'Titulo')
            tipo = self._get_text_value(diploma, 'Tipo')
            sessao = self._get_int_value(diploma, 'Sessao')
            ano_civil = self._get_int_value(diploma, 'AnoCivil')
            link_texto = self._get_text_value(diploma, 'LinkTexto')
            observacoes = self._get_text_value(diploma, 'Observacoes')
            tp = self._get_text_value(diploma, 'Tp')
            
            if not titulo or not tipo:
                logger.warning("Missing required fields: titulo or tipo")
                return False
            
            # Create activity date from year (use January 1st as default)
            data_atividade = f"{ano_civil}-01-01" if ano_civil else None
            
            # Create diploma title combining type, number and title
            if numero:
                full_title = f"{tipo} n.º {numero}: {titulo}"
            else:
                full_title = f"{tipo}: {titulo}"
            
            # Map diploma type to standard activity type
            activity_type = self._map_diploma_type(tipo, tp)
            
            # Check if diploma already exists
            if diploma_id:
                self.cursor.execute("""
                    SELECT id FROM atividades_parlamentares_detalhadas
                    WHERE id_externo = ? AND tipo = ?
                """, (diploma_id, activity_type))
                
                if self.cursor.fetchone():
                    # Update existing record
                    self.cursor.execute("""
                        UPDATE atividades_parlamentares_detalhadas SET
                            titulo = ?, data_atividade = ?, legislatura_id = ?
                        WHERE id_externo = ? AND tipo = ?
                    """, (full_title, data_atividade, legislatura_id, diploma_id, activity_type))
                    return True
            
            # Insert new diploma record
            self.cursor.execute("""
                INSERT INTO atividades_parlamentares_detalhadas (
                    id_externo, tipo, titulo, data_atividade, legislatura_id
                ) VALUES (?, ?, ?, ?, ?)
            """, (diploma_id, activity_type, full_title, data_atividade, legislatura_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing diploma: {e}")
            return False
    
    def _map_diploma_type(self, tipo: str, tp: str) -> str:
        """Map diploma type to standard activity type"""
        if not tipo:
            return 'DIPLOMA'
        
        tipo_upper = tipo.upper()
        
        if 'LEI' in tipo_upper:
            return 'LEI'
        elif 'DECRETO' in tipo_upper:
            return 'DECRETO'
        elif 'RESOLUÇÃO' in tipo_upper or 'RESOLUCAO' in tipo_upper:
            return 'RESOLUCAO'
        elif 'DELIBERAÇÃO' in tipo_upper or 'DELIBERACAO' in tipo_upper:
            return 'DELIBERACAO'
        else:
            return 'DIPLOMA'
    
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
                return None
        return None
    
    def _get_or_create_legislatura(self, legislatura_sigla: str) -> int:
        """Get or create legislatura record"""
        # Check if legislatura exists
        self.cursor.execute("""
            SELECT id FROM legislaturas WHERE numero = ?
        """, (legislatura_sigla,))
        
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        # Create new legislatura if it doesn't exist
        numero_int = self._convert_roman_to_int(legislatura_sigla)
        
        self.cursor.execute("""
            INSERT INTO legislaturas (numero, designacao, ativa)
            VALUES (?, ?, ?)
        """, (legislatura_sigla, f"{numero_int}.ª Legislatura", False))
        
        return self.cursor.lastrowid
    
    def _convert_roman_to_int(self, roman: str) -> int:
        """Convert Roman numeral to integer"""
        roman_numerals = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
            'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'CONSTITUINTE': 0
        }
        return roman_numerals.get(roman, 17)