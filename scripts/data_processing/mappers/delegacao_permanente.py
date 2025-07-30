"""
Parliamentary Permanent Delegations Mapper
==========================================

Schema mapper for parliamentary permanent delegation files (DelegacaoPermanente*.xml).
Handles permanent parliamentary delegations to international organizations 
and their membership compositions.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging

from .base_mapper import SchemaMapper, SchemaError

logger = logging.getLogger(__name__)


class DelegacaoPermanenteMapper(SchemaMapper):
    """Schema mapper for parliamentary permanent delegation files"""
    
    def get_expected_fields(self) -> Set[str]:
        return {
            'ArrayOfDelegacaoPermanenteOut', 'DelegacaoPermanenteOut', 'Id', 'Nome', 
            'Legislatura', 'Sessao', 'DataEleicao', 'Composicao', 'Comissoes', 'Reunioes',
            # Members
            'DelegacaoPermanenteMembroOut', 'Gp', 'Cargo', 'DataInicio', 'DataFim'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map parliamentary permanent delegations to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        # Validate schema coverage according to strict mode
        self.validate_schema_coverage(xml_root, file_info, strict_mode)
        
        # Extract legislatura from filename or XML
        legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
        legislatura_id = self._get_or_create_legislatura(legislatura_sigla)
        
        # Process permanent delegations
        for delegation in xml_root.findall('.//DelegacaoPermanenteOut'):
            try:
                success = self._process_delegation(delegation, legislatura_id)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Permanent delegation processing error: {str(e)}"
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
    
    def _process_delegation(self, delegation: ET.Element, legislatura_id: int) -> bool:
        """Process individual permanent delegation"""
        try:
            # Extract basic fields
            id_externo = self._get_int_value(delegation, 'Id')
            nome = self._get_text_value(delegation, 'Nome')
            sessao = self._get_text_value(delegation, 'Sessao')
            data_eleicao_str = self._get_text_value(delegation, 'DataEleicao')
            
            if not nome:
                logger.warning("Missing required field: Nome")
                return False
            
            # Parse election date
            data_atividade = self._parse_date(data_eleicao_str)
            if not data_atividade:
                logger.warning(f"Invalid election date: {data_eleicao_str}")
                return False
            
            # Check if delegation record already exists
            if id_externo:
                self.cursor.execute("""
                    SELECT id FROM atividades_parlamentares_detalhadas
                    WHERE id_externo = ? AND tipo = 'DELEGACAO_PERMANENTE'
                """, (id_externo,))
                
                if self.cursor.fetchone():
                    # Update existing record
                    self.cursor.execute("""
                        UPDATE atividades_parlamentares_detalhadas SET
                            titulo = ?, data_atividade = ?, legislatura_id = ?
                        WHERE id_externo = ? AND tipo = 'DELEGACAO_PERMANENTE'
                    """, (nome, data_atividade, legislatura_id, id_externo))
                else:
                    # Insert new delegation record
                    self.cursor.execute("""
                        INSERT INTO atividades_parlamentares_detalhadas (
                            id_externo, tipo, titulo, data_atividade, legislatura_id
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (id_externo, 'DELEGACAO_PERMANENTE', nome, data_atividade, legislatura_id))
            else:
                # Insert without external ID
                self.cursor.execute("""
                    INSERT INTO atividades_parlamentares_detalhadas (
                        tipo, titulo, data_atividade, legislatura_id
                    ) VALUES (?, ?, ?, ?)
                """, ('DELEGACAO_PERMANENTE', nome, data_atividade, legislatura_id))
            
            # Process members
            composicao = delegation.find('Composicao')
            if composicao is not None:
                for member in composicao.findall('DelegacaoPermanenteMembroOut'):
                    self._process_delegation_member(member, id_externo, legislatura_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing permanent delegation: {e}")
            return False
    
    def _process_delegation_member(self, member: ET.Element, delegation_id: int, legislatura_id: int) -> bool:
        """Process delegation member"""
        try:
            # Extract member fields
            member_id = self._get_int_value(member, 'Id')
            nome = self._get_text_value(member, 'Nome')
            gp = self._get_text_value(member, 'Gp')
            cargo = self._get_text_value(member, 'Cargo')
            data_inicio_str = self._get_text_value(member, 'DataInicio')
            data_fim_str = self._get_text_value(member, 'DataFim')
            
            if not nome:
                return False
            
            # Parse dates
            data_inicio = self._parse_date(data_inicio_str)
            data_fim = self._parse_date(data_fim_str) if data_fim_str else None
            
            # Create member activity record
            titulo = f"{nome} - {cargo}" if cargo else nome
            if gp:
                titulo += f" ({gp})"
            
            # Check if member record already exists
            if member_id:
                self.cursor.execute("""
                    SELECT id FROM atividades_parlamentares_detalhadas
                    WHERE id_externo = ? AND tipo = 'DELEGACAO_PERMANENTE_MEMBRO'
                """, (member_id,))
                
                if self.cursor.fetchone():
                    return True  # Already exists
            
            # Insert member record
            self.cursor.execute("""
                INSERT INTO atividades_parlamentares_detalhadas (
                    id_externo, tipo, titulo, data_atividade, legislatura_id
                ) VALUES (?, ?, ?, ?, ?)
            """, (member_id, 'DELEGACAO_PERMANENTE_MEMBRO', titulo, data_inicio, legislatura_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing delegation member: {e}")
            return False
    
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