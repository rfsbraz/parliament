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

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    CooperacaoParlamentar, CooperacaoPrograma, CooperacaoAtividade, 
    CooperacaoParticipante, Legislatura
)

logger = logging.getLogger(__name__)


class CooperacaoMapper(SchemaMapper):
    """Schema mapper for parliamentary cooperation files"""
    
    def __init__(self, session):
        # Accept SQLAlchemy session directly (passed by unified importer)
        super().__init__(session)
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # Root elements
            'ArrayOfCooperacaoOut',
            'ArrayOfCooperacaoOut.CooperacaoOut',
            
            # Main cooperation fields
            'ArrayOfCooperacaoOut.CooperacaoOut.Id',
            'ArrayOfCooperacaoOut.CooperacaoOut.Tipo',
            'ArrayOfCooperacaoOut.CooperacaoOut.Nome',
            'ArrayOfCooperacaoOut.CooperacaoOut.Legislatura',
            'ArrayOfCooperacaoOut.CooperacaoOut.Sessao',
            'ArrayOfCooperacaoOut.CooperacaoOut.Data',
            'ArrayOfCooperacaoOut.CooperacaoOut.Local',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades',
            
            # Cooperation activities
            'ArrayOfCooperacaoOut.CooperacaoOut.CooperacaoAtividade',
            'ArrayOfCooperacaoOut.CooperacaoOut.CooperacaoAtividade.TipoAtividade',
            'ArrayOfCooperacaoOut.CooperacaoOut.CooperacaoAtividade.DataInicio',
            'ArrayOfCooperacaoOut.CooperacaoOut.CooperacaoAtividade.DataFim',
            'ArrayOfCooperacaoOut.CooperacaoOut.CooperacaoAtividade.Participantes',
            'ArrayOfCooperacaoOut.CooperacaoOut.CooperacaoAtividade.RelacoesExternasParticipantes'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map parliamentary cooperation to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        # Validate schema coverage according to strict mode
        self.validate_schema_coverage(xml_root, file_info, strict_mode)
        
        # Extract legislatura from filename or XML
        legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
        legislatura = self._get_or_create_legislatura(legislatura_sigla)
        
        # Process cooperation items
        for cooperacao_item in xml_root.findall('.//CooperacaoOut'):
            try:
                success = self._process_cooperacao_item(cooperacao_item, legislatura)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Cooperation item processing error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['records_processed'] += 1
                self.session.rollback()
        
        # Commit all changes
        self.session.commit()
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
    
    def _process_cooperacao_item(self, cooperacao_item: ET.Element, legislatura: Legislatura) -> bool:
        """Process individual cooperation item"""
        try:
            # Extract basic fields
            id_externo = self._get_int_value(cooperacao_item, 'Id')
            tipo = self._get_text_value(cooperacao_item, 'Tipo')
            nome = self._get_text_value(cooperacao_item, 'Nome')
            sessao = self._get_int_value(cooperacao_item, 'Sessao')
            data_str = self._get_text_value(cooperacao_item, 'Data')
            local = self._get_text_value(cooperacao_item, 'Local')
            
            if not nome:
                logger.warning("Missing required field: Nome")
                return False
            
            # Parse date
            data = self._parse_date(data_str)
            
            # Check if record already exists
            existing = None
            if id_externo:
                existing = self.session.query(CooperacaoParlamentar).filter_by(
                    cooperacao_id=id_externo
                ).first()
            
            if existing:
                # Update existing record
                existing.tipo = tipo
                existing.nome = nome
                existing.sessao = sessao
                existing.data = data
                existing.local = local
                existing.legislatura_id = legislatura.id
            else:
                # Create new record
                cooperacao = CooperacaoParlamentar(
                    cooperacao_id=id_externo,
                    tipo=tipo,
                    nome=nome,
                    sessao=sessao,
                    data=data,
                    local=local,
                    legislatura_id=legislatura.id
                )
                self.session.add(cooperacao)
                self.session.flush()  # Get the ID
                existing = cooperacao
            
            # Process programs and activities
            self._process_cooperation_programs(cooperacao_item, existing)
            self._process_cooperation_activities(cooperacao_item, existing)
            
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
    
    def _process_cooperation_programs(self, cooperacao_item: ET.Element, cooperacao: CooperacaoParlamentar):
        """Process cooperation programs"""
        programas = cooperacao_item.find('Programas')
        if programas is not None:
            for programa in programas:
                nome = programa.tag if programa.tag else None
                descricao = programa.text if programa.text else None
                
                if nome:
                    programa_record = CooperacaoPrograma(
                        cooperacao_id=cooperacao.id,
                        nome=nome,
                        descricao=descricao
                    )
                    self.session.add(programa_record)
    
    def _process_cooperation_activities(self, cooperacao_item: ET.Element, cooperacao: CooperacaoParlamentar):
        """Process cooperation activities"""
        atividades = cooperacao_item.find('Atividades')
        if atividades is not None:
            for atividade in atividades.findall('CooperacaoAtividade'):
                tipo_atividade = self._get_text_value(atividade, 'TipoAtividade')
                data_inicio = self._parse_date(self._get_text_value(atividade, 'DataInicio'))
                data_fim = self._parse_date(self._get_text_value(atividade, 'DataFim'))
                descricao = self._get_text_value(atividade, 'Descricao')
                
                atividade_record = CooperacaoAtividade(
                    cooperacao_id=cooperacao.id,
                    tipo_atividade=tipo_atividade,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    descricao=descricao
                )
                self.session.add(atividade_record)
                self.session.flush()  # Get the ID
                
                # Process participants
                self._process_cooperation_participants(atividade, atividade_record)
    
    def _process_cooperation_participants(self, atividade: ET.Element, atividade_record: CooperacaoAtividade):
        """Process cooperation participants"""
        # Process internal participants
        participantes = atividade.find('Participantes')
        if participantes is not None:
            for participante in participantes:
                nome = participante.text if participante.text else participante.tag
                if nome:
                    participante_record = CooperacaoParticipante(
                        atividade_id=atividade_record.id,
                        nome=nome,
                        tipo_participante='interno'
                    )
                    self.session.add(participante_record)
        
        # Process external participants
        externos = atividade.find('RelacoesExternasParticipantes')
        if externos is not None:
            for externo in externos:
                nome = externo.text if externo.text else externo.tag
                if nome:
                    participante_record = CooperacaoParticipante(
                        atividade_id=atividade_record.id,
                        nome=nome,
                        tipo_participante='externo'
                    )
                    self.session.add(participante_record)