"""
Parliamentary Occasional Delegations Mapper
===========================================

Schema mapper for parliamentary occasional delegation files (DelegacaoEventual*.xml).
Handles parliamentary delegation meetings, missions, and international events.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging

from .base_mapper import SchemaMapper, SchemaError

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    DelegacaoEventual, DelegacaoEventualParticipante, Deputado, Legislatura
)

logger = logging.getLogger(__name__)


class DelegacaoEventualMapper(SchemaMapper):
    """Schema mapper for parliamentary occasional delegation files"""
    
    def __init__(self, session):
        # Accept SQLAlchemy session directly (passed by unified importer)
        super().__init__(session)
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # Root elements
            'ArrayOfDelegacaoEventualReuniao',
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao',
            
            # Main delegation fields
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Id',
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Nome',
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Local',
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Legislatura',
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Sessao',
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.DataInicio',
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.DataFim',
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Tipo',
            
            # Participants
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Participantes',
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Participantes.RelacoesExternasParticipantes',
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Participantes.RelacoesExternasParticipantes.Gp',
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Participantes.RelacoesExternasParticipantes.Leg',
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Participantes.RelacoesExternasParticipantes.Id',  # IX Legislature
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Participantes.RelacoesExternasParticipantes.Nome',  # IX Legislature
            'ArrayOfDelegacaoEventualReuniao.DelegacaoEventualReuniao.Participantes.RelacoesExternasParticipantes.Tipo'  # IX Legislature
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map parliamentary delegation events to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        try:
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Extract legislatura from filename or XML
            legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
            
            # Process delegation events
            for delegation_event in xml_root.findall('.//DelegacaoEventualReuniao'):
                try:
                    success = self._process_delegation_event(delegation_event, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Delegation event processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
                    self.session.rollback()
                    if strict_mode:
                        logger.error("STRICT MODE: Exiting due to delegation event processing error")
                        raise SchemaError(f"Delegation event processing failed in strict mode: {e}")
                    continue
            
            # Commit all changes
            self.session.commit()
            return results
            
        except Exception as e:
            error_msg = f"Critical error processing delegation events: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            self.session.rollback()
            raise SchemaError(f"Critical delegation processing error: {e}")
    
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
    
    def _process_delegation_event(self, delegation_event: ET.Element, legislatura: Legislatura) -> bool:
        """Process individual delegation event"""
        try:
            # Extract basic fields
            id_externo = self._get_int_value(delegation_event, 'Id')
            nome = self._get_text_value(delegation_event, 'Nome')
            local = self._get_text_value(delegation_event, 'Local')
            sessao = self._get_text_value(delegation_event, 'Sessao')
            data_inicio_str = self._get_text_value(delegation_event, 'DataInicio')
            data_fim_str = self._get_text_value(delegation_event, 'DataFim')
            
            if not nome:
                logger.warning("Missing required field: Nome")
                return False
            
            # Parse dates
            data_inicio = self._parse_date(data_inicio_str)
            data_fim = self._parse_date(data_fim_str)
            
            # Check if delegation already exists
            existing = None
            if id_externo:
                existing = self.session.query(DelegacaoEventual).filter_by(
                    delegacao_id=id_externo
                ).first()
            
            if existing:
                # Update existing record
                existing.nome = nome
                existing.local = local
                existing.sessao = sessao
                existing.data_inicio = data_inicio
                existing.data_fim = data_fim
                existing.legislatura_id = legislatura.id
            else:
                # Create new delegation record
                delegacao = DelegacaoEventual(
                    delegacao_id=id_externo,
                    nome=nome,
                    local=local,
                    sessao=sessao,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    legislatura_id=legislatura.id
                )
                self.session.add(delegacao)
                self.session.flush()  # Get the ID
                existing = delegacao
            
            # Process participants
            self._process_delegation_participants(delegation_event, existing)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing delegation event: {e}")
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
    
    def _process_delegation_participants(self, delegation_event: ET.Element, delegacao: DelegacaoEventual):
        """Process delegation participants"""
        # Process internal participants
        participantes = delegation_event.find('Participantes')
        if participantes is not None:
            for participante in participantes:
                nome = participante.text if participante.text else participante.tag
                tipo = self._get_text_value(participante, 'Tipo')
                gp = self._get_text_value(participante, 'Gp')
                leg = self._get_text_value(participante, 'Leg')
                
                if nome:
                    participante_record = DelegacaoEventualParticipante(
                        delegacao_id=delegacao.id,
                        nome=nome,
                        gp=gp,
                        tipo_participante='interno'
                    )
                    self.session.add(participante_record)
        
        # Process external participants (enhanced for IX Legislature)
        participantes_elem = delegation_event.find('Participantes')
        if participantes_elem is not None:
            relacoes_externas = participantes_elem.find('RelacoesExternasParticipantes')
            if relacoes_externas is not None:
                # IX Legislature structure with Id, Nome, Tipo fields
                participante_id = self._get_int_value(relacoes_externas, 'Id')
                nome = self._get_text_value(relacoes_externas, 'Nome')
                tipo = self._get_text_value(relacoes_externas, 'Tipo')
                gp = self._get_text_value(relacoes_externas, 'Gp')
                
                if nome or participante_id:
                    participante_record = DelegacaoEventualParticipante(
                        delegacao_id=delegacao.id,
                        participante_id=participante_id,
                        nome=nome,
                        gp=gp,
                        tipo_participante=tipo or 'externo'
                    )
                    self.session.add(participante_record)