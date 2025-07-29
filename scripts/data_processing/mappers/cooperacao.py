"""
Parliamentary Cooperation Mapper
===============================

Schema mapper for parliamentary cooperation files (Cooperacao*.xml).
Handles international parliamentary cooperation agreements, programs, 
and activities between Portuguese Parliament and other institutions.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging

from .base_mapper import SchemaMapper, SchemaError

logger = logging.getLogger(__name__)


class CooperacaoMapper(SchemaMapper):
    """Schema mapper for parliamentary cooperation files"""
    
    def get_expected_fields(self) -> Set[str]:
        return {
            'ArrayOfCooperacaoOut', 'CooperacaoOut', 'Id', 'Tipo', 'Nome', 
            'Legislatura', 'Sessao', 'Data', 'Local', 'Programas', 'Atividades',
            # Cooperation activities
            'CooperacaoAtividade', 'TipoAtividade', 'DataInicio', 'DataFim', 
            'Participantes', 'RelacoesExternasParticipantes'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict) -> Dict:
        """Map parliamentary cooperation to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        unmapped_fields = self.check_schema_coverage(xml_root)
        if unmapped_fields:
            logger.warning(f"Some unmapped fields found: {', '.join(list(unmapped_fields)[:10])}")
        
        # Extract legislatura from filename or XML
        legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
        legislatura_id = self._get_or_create_legislatura(legislatura_sigla)
        
        # Process cooperation items
        for cooperacao_item in xml_root.findall('.//CooperacaoOut'):
            try:
                success = self._process_cooperacao_item(cooperacao_item, legislatura_id)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Cooperation item processing error: {str(e)}"
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
    
    def _process_cooperacao_item(self, cooperacao_item: ET.Element, legislatura_id: int) -> bool:
        """Process individual cooperation item"""
        try:
            # Extract basic fields
            id_externo = self._get_int_value(cooperacao_item, 'Id')
            tipo = self._get_text_value(cooperacao_item, 'Tipo')
            nome = self._get_text_value(cooperacao_item, 'Nome')
            sessao = self._get_text_value(cooperacao_item, 'Sessao')
            data_str = self._get_text_value(cooperacao_item, 'Data')
            local = self._get_text_value(cooperacao_item, 'Local')
            
            if not nome:
                logger.warning("Missing required field: Nome")
                return False
            
            # Parse date
            data_atividade = self._parse_date(data_str)
            
            # Map cooperation type to activity type
            tipo_atividade = self._map_cooperation_type(tipo)
            
            # Check if record already exists
            if id_externo:
                self.cursor.execute("""
                    SELECT id FROM atividades_parlamentares_detalhadas
                    WHERE id_externo = ?
                """, (id_externo,))
                
                if self.cursor.fetchone():
                    # Update existing record
                    self.cursor.execute("""
                        UPDATE atividades_parlamentares_detalhadas SET
                            tipo = ?, titulo = ?, data_atividade = ?, legislatura_id = ?
                        WHERE id_externo = ?
                    """, (tipo or 'COOPERACAO', nome, data_atividade, legislatura_id, id_externo))
                    return True
            
            # Insert new record
            self.cursor.execute("""
                INSERT INTO atividades_parlamentares_detalhadas (
                    id_externo, tipo, titulo, data_atividade, legislatura_id
                ) VALUES (?, ?, ?, ?, ?)
            """, (id_externo, tipo or 'COOPERACAO', nome, data_atividade, legislatura_id))
            
            # Process nested programs
            programas = cooperacao_item.find('Programas')
            if programas is not None:
                for programa in programas.findall('CooperacaoOut'):
                    self._process_cooperacao_item(programa, legislatura_id)
            
            # Process nested activities  
            atividades = cooperacao_item.find('Atividades')
            if atividades is not None:
                for atividade in atividades.findall('CooperacaoAtividade'):
                    self._process_cooperacao_atividade(atividade, legislatura_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing cooperation item: {e}")
            return False
    
    def _process_cooperacao_atividade(self, atividade: ET.Element, legislatura_id: int) -> bool:
        """Process cooperation activity"""
        try:
            # Extract activity fields
            id_externo = self._get_int_value(atividade, 'Id')
            tipo_atividade = self._get_text_value(atividade, 'TipoAtividade')
            tipo = self._get_text_value(atividade, 'Tipo')
            nome = self._get_text_value(atividade, 'Nome')
            data_inicio_str = self._get_text_value(atividade, 'DataInicio')
            data_fim_str = self._get_text_value(atividade, 'DataFim')
            local = self._get_text_value(atividade, 'Local')
            
            if not nome:
                return False
            
            # Parse dates
            data_atividade = self._parse_date(data_inicio_str)
            
            # Check if already exists
            if id_externo:
                self.cursor.execute("""
                    SELECT id FROM atividades_parlamentares_detalhadas
                    WHERE id_externo = ?
                """, (id_externo,))
                
                if self.cursor.fetchone():
                    return True  # Already exists
            
            # Insert activity
            self.cursor.execute("""
                INSERT INTO atividades_parlamentares_detalhadas (
                    id_externo, tipo, titulo, data_atividade, legislatura_id
                ) VALUES (?, ?, ?, ?, ?)
            """, (id_externo, tipo_atividade or 'COOPERACAO_ATIVIDADE', nome, data_atividade, legislatura_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing cooperation activity: {e}")
            return False
    
    def _map_cooperation_type(self, tipo: str) -> Optional[str]:
        """Map cooperation type to standard values"""
        if not tipo:
            return 'audiencia'  # Default to audiencia for cooperation
        
        # Map common cooperation types
        type_mapping = {
            'ACR': 'audiencia',  # Acordo/Agreement
            'PRG': 'audiencia',  # Programa/Program
            'DSL': 'debate',     # Deslocacao/Mission
            'FRM': 'audiencia',  # Formacao/Training
            'ACO': 'audiencia'   # Acordo/Agreement
        }
        
        return type_mapping.get(tipo.upper(), 'audiencia')
    
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
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
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
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # Try ISO format
            if re.match(r'\d{4}-\d{2}-\d{2}', date_part):
                return date_part
            
        except (ValueError, IndexError):
            logger.warning(f"Could not parse date: {date_str}")
        
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