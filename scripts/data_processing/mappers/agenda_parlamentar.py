"""
Parliamentary Agenda Mapper
===========================

Schema mapper for parliamentary agenda files (AgendaParlamentar*.xml).
Handles parliamentary session agendas, meetings, and event scheduling.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set
import logging

from .base_mapper import SchemaMapper, SchemaError

logger = logging.getLogger(__name__)


class AgendaParlamentarMapper(SchemaMapper):
    """Schema mapper for parliamentary agenda files"""
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # Root elements
            'ArrayOfAgendaParlamentar',
            
            # AgendaParlamentar nested elements
            'ArrayOfAgendaParlamentar.AgendaParlamentar',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.Id',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.SectionId',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.Section',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.ThemeId',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.Theme',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.OrderValue',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.ParlamentGroup',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.AllDayEvent',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.EventStartDate',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.EventStartTime',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.EventEndDate',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.EventEndTime',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.Title',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.Subtitle',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.InternetText',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.Local',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.Link',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.LegDes',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.OrgDes',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.ReuNumero',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.SelNumero',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.PostPlenary',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.AnexosComissaoPermanente',
            'ArrayOfAgendaParlamentar.AgendaParlamentar.AnexosPlenario'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map parliamentary agenda to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        # Validate schema coverage according to strict mode
        self.validate_schema_coverage(xml_root, file_info, strict_mode)
        
        # Extract legislatura from filename or XML
        legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
        legislatura_id = self._get_or_create_legislatura(legislatura_sigla)
        
        # Process each agenda item
        for agenda_item in xml_root.findall('.//AgendaParlamentar'):
            try:
                success = self._process_agenda_item(agenda_item, legislatura_id)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Agenda item processing error: {str(e)}"
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
        
        # Try XML content
        leg_des = xml_root.find('.//LegDes')
        if leg_des is not None and leg_des.text:
            return leg_des.text.strip()
        
        # Default to XVII
        return 'XVII'
    
    def _process_agenda_item(self, agenda_item: ET.Element, legislatura_id: int) -> bool:
        """Process individual agenda item"""
        try:
            # Extract basic fields
            id_externo = self._get_int_value(agenda_item, 'Id')
            secao_id = self._get_int_value(agenda_item, 'SectionId')
            secao_nome = self._get_text_value(agenda_item, 'Section')
            tema_id = self._get_int_value(agenda_item, 'ThemeId')
            tema_nome = self._get_text_value(agenda_item, 'Theme')
            grupo_parlamentar = self._get_text_value(agenda_item, 'ParlamentGroup')
            
            # Extract dates and times
            event_start_date = self._get_text_value(agenda_item, 'EventStartDate')
            event_start_time = self._get_text_value(agenda_item, 'EventStartTime')
            event_end_date = self._get_text_value(agenda_item, 'EventEndDate')
            event_end_time = self._get_text_value(agenda_item, 'EventEndTime')
            
            # Parse date
            data_evento = self._parse_date(event_start_date)
            if not data_evento:
                logger.warning(f"Invalid event date: {event_start_date}")
                return False
            
            # Parse times
            hora_inicio = self._parse_time(event_start_time)
            hora_fim = self._parse_time(event_end_time)
            
            # Extract other fields
            all_day_event = self._get_boolean_value(agenda_item, 'AllDayEvent')
            titulo = self._get_text_value(agenda_item, 'Title')
            subtitulo = self._get_text_value(agenda_item, 'Subtitle')
            descricao = self._get_text_value(agenda_item, 'InternetText')
            local_evento = self._get_text_value(agenda_item, 'Local')
            link_externo = self._get_text_value(agenda_item, 'Link')
            pos_plenario = self._get_boolean_value(agenda_item, 'PostPlenary')
            
            if not titulo:
                logger.warning("Missing required field: Title")
                return False
            
            # Check if record already exists
            self.cursor.execute("""
                SELECT id FROM agenda_parlamentar 
                WHERE id_externo = ? AND legislatura_id = ?
            """, (id_externo, legislatura_id))
            
            if self.cursor.fetchone():
                # Update existing record
                self.cursor.execute("""
                    UPDATE agenda_parlamentar SET
                        secao_id = ?, secao_nome = ?, tema_id = ?, tema_nome = ?,
                        grupo_parlamentar = ?, data_evento = ?, hora_inicio = ?, hora_fim = ?,
                        evento_dia_inteiro = ?, titulo = ?, subtitulo = ?, descricao = ?,
                        local_evento = ?, link_externo = ?, pos_plenario = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id_externo = ? AND legislatura_id = ?
                """, (
                    secao_id, secao_nome, tema_id, tema_nome, grupo_parlamentar,
                    data_evento, hora_inicio, hora_fim, all_day_event, titulo,
                    subtitulo, descricao, local_evento, link_externo, pos_plenario,
                    id_externo, legislatura_id
                ))
            else:
                # Insert new record
                self.cursor.execute("""
                    INSERT INTO agenda_parlamentar (
                        id_externo, legislatura_id, secao_id, secao_nome, tema_id, tema_nome,
                        grupo_parlamentar, data_evento, hora_inicio, hora_fim, evento_dia_inteiro,
                        titulo, subtitulo, descricao, local_evento, link_externo, pos_plenario
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    id_externo, legislatura_id, secao_id, secao_nome, tema_id, tema_nome,
                    grupo_parlamentar, data_evento, hora_inicio, hora_fim, all_day_event,
                    titulo, subtitulo, descricao, local_evento, link_externo, pos_plenario
                ))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing agenda item: {e}")
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
    
    def _get_boolean_value(self, parent: ET.Element, tag_name: str) -> bool:
        """Get boolean value from XML element"""
        text_value = self._get_text_value(parent, tag_name)
        if text_value:
            return text_value.lower() in ('true', '1', 'yes')
        return False
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
        if not date_str:
            return None
        
        try:
            # Try common Portuguese date format: DD/MM/YYYY
            if '/' in date_str:
                day, month, year = date_str.split('/')
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # Try ISO format
            if '-' in date_str:
                return date_str
            
        except (ValueError, IndexError):
            logger.warning(f"Could not parse date: {date_str}")
        
        return None
    
    def _parse_time(self, time_str: str) -> Optional[str]:
        """Parse time string to HH:MM:SS format"""
        if not time_str:
            return None
        
        try:
            # Handle HH:MM:SS format
            if time_str.count(':') == 2:
                return time_str
            
            # Handle HH:MM format
            if time_str.count(':') == 1:
                return f"{time_str}:00"
            
        except Exception:
            logger.warning(f"Could not parse time: {time_str}")
        
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