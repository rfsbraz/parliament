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
import uuid
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging

from .enhanced_base_mapper import SchemaMapper, SchemaError

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
            
            # Nested programs within Programas
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Id',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Tipo',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Nome',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Legislatura',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Sessao',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Data',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Local',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades',
            
            # Activities within nested programs
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade.Id',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade.Nome',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade.DataInicio',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade.DataFim',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade.Tipo',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade.TipoAtividade',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade.Local',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade.Participantes',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade.RelacoesExternasParticipantes',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade.Participantes.RelacoesExternasParticipantes',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade.Participantes.RelacoesExternasParticipantes.Id',
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Atividades.CooperacaoAtividade.Participantes.RelacoesExternasParticipantes.Nome',
            
            # Nested programs within nested programs
            'ArrayOfCooperacaoOut.CooperacaoOut.Programas.CooperacaoOut.Programas',
            
            # Direct activities under main cooperation
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade.Id',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade.Nome',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade.DataInicio',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade.DataFim',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade.Tipo',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade.TipoAtividade',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade.Local',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade.Participantes',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade.RelacoesExternasParticipantes',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade.Participantes.RelacoesExternasParticipantes',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade.Participantes.RelacoesExternasParticipantes.Id',
            'ArrayOfCooperacaoOut.CooperacaoOut.Atividades.CooperacaoAtividade.Participantes.RelacoesExternasParticipantes.Nome'
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
                logger.error("Data integrity issue detected during cooperation item processing")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                results['errors'].append(error_msg)
                results['records_processed'] += 1
                raise RuntimeError(f"Data integrity issue: {error_msg}")
        
        # Commit all changes
        return results
    
    
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
                logger.debug("Missing Nome field - importing with placeholder")
                nome = "COOPERACAO_SEM_NOME"
            
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
                    id=uuid.uuid4(),
                    cooperacao_id=id_externo,
                    tipo=tipo,
                    nome=nome,
                    sessao=sessao,
                    data=data,
                    local=local,
                    legislatura_id=legislatura.id
                )
                self.session.add(cooperacao)
                existing = cooperacao
            
            # Process programs and activities
            self._process_cooperation_programs(cooperacao_item, existing)
            self._process_cooperation_activities(cooperacao_item, existing)
            
            # Process nested programs
            programas = cooperacao_item.find('Programas')
            if programas is not None:
                for programa in programas.findall('CooperacaoOut'):
                    self._process_cooperacao_item(programa, legislatura)
            
            # Process nested activities  
            atividades = cooperacao_item.find('Atividades')
            if atividades is not None:
                for atividade in atividades.findall('CooperacaoAtividade'):
                    self._process_cooperacao_atividade(atividade, existing)
            
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
    
    # NOTE: _get_or_create_legislatura is inherited from EnhancedSchemaMapper (with caching)
    # NOTE: Roman numeral conversion uses ROMAN_TO_NUMBER from LegislatureHandlerMixin

    def _process_cooperation_programs(self, cooperacao_item: ET.Element, cooperacao: CooperacaoParlamentar):
        """Process cooperation programs"""
        programas = cooperacao_item.find('Programas')
        if programas is not None:
            for programa in programas:
                nome = programa.tag if programa.tag else None
                descricao = programa.text if programa.text else None
                
                if nome:
                    programa_record = CooperacaoPrograma(
                        id=uuid.uuid4(),
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
                atividade_id = self._get_int_value(atividade, 'Id')
                nome = self._get_text_value(atividade, 'Nome')
                tipo_atividade = self._get_text_value(atividade, 'TipoAtividade')
                tipo = self._get_text_value(atividade, 'Tipo')
                local = self._get_text_value(atividade, 'Local')
                data_inicio = self._parse_date(self._get_text_value(atividade, 'DataInicio'))
                data_fim = self._parse_date(self._get_text_value(atividade, 'DataFim'))
                descricao = self._get_text_value(atividade, 'Descricao')
                
                # Use TipoAtividade if available, otherwise use Tipo
                tipo_final = tipo_atividade if tipo_atividade else tipo
                
                atividade_record = CooperacaoAtividade(
                    id=uuid.uuid4(),
                    cooperacao_id=cooperacao.id,
                    atividade_id=atividade_id,
                    nome=nome,
                    tipo_atividade=tipo_final,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    local=local,
                    descricao=descricao
                )
                self.session.add(atividade_record)
                
                # Process participants
                self._process_cooperation_participants(atividade, atividade_record)
    
    def _process_cooperation_participants(self, atividade: ET.Element, atividade_record: CooperacaoAtividade):
        """Process cooperation participants"""
        # Process internal participants
        participantes = atividade.find('Participantes')
        if participantes is not None:
            # Check for structured participant data
            externos_nested = participantes.find('RelacoesExternasParticipantes')
            if externos_nested is not None:
                for externo in externos_nested:
                    participante_id = self._get_int_value(externo, 'Id')
                    nome = self._get_text_value(externo, 'Nome')
                    if nome:
                        participante_record = CooperacaoParticipante(
                            id=uuid.uuid4(),
                            atividade_id=atividade_record.id,
                            participante_id=participante_id,
                            nome=nome,
                            tipo_participante='externo'
                        )
                        self.session.add(participante_record)
            else:
                # Process simple participant data
                for participante in participantes:
                    nome = participante.text if participante.text else participante.tag
                    if nome:
                        participante_record = CooperacaoParticipante(
                            id=uuid.uuid4(),
                            atividade_id=atividade_record.id,
                            nome=nome,
                            tipo_participante='interno'
                        )
                        self.session.add(participante_record)
        
        # Process direct external participants
        externos = atividade.find('RelacoesExternasParticipantes')
        if externos is not None:
            for externo in externos:
                participante_id = self._get_int_value(externo, 'Id')
                nome = self._get_text_value(externo, 'Nome')
                if nome:
                    participante_record = CooperacaoParticipante(
                        id=uuid.uuid4(),
                        atividade_id=atividade_record.id,
                        participante_id=participante_id,
                        nome=nome,
                        tipo_participante='externo'
                    )
                    self.session.add(participante_record)

    def _process_cooperacao_atividade(self, atividade: ET.Element, cooperacao: CooperacaoParlamentar):
        """Process individual cooperation activity directly nested under main cooperation item"""
        atividade_id = self._get_int_value(atividade, 'Id')
        nome = self._get_text_value(atividade, 'Nome')
        tipo_atividade = self._get_text_value(atividade, 'TipoAtividade')
        tipo = self._get_text_value(atividade, 'Tipo')
        local = self._get_text_value(atividade, 'Local')
        data_inicio = self._parse_date(self._get_text_value(atividade, 'DataInicio'))
        data_fim = self._parse_date(self._get_text_value(atividade, 'DataFim'))
        
        # Use TipoAtividade if available, otherwise use Tipo
        tipo_final = tipo_atividade if tipo_atividade else tipo
        
        if tipo_final or nome:
            atividade_record = CooperacaoAtividade(
                id=uuid.uuid4(),
                cooperacao_id=cooperacao.id,
                atividade_id=atividade_id,
                nome=nome,
                tipo_atividade=tipo_final,
                data_inicio=data_inicio,
                data_fim=data_fim,
                local=local
            )
            self.session.add(atividade_record)
            
            # Process participants
            self._process_cooperation_participants(atividade, atividade_record)