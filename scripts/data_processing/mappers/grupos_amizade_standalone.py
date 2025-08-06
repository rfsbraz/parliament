"""
Parliamentary Friendship Groups Standalone Mapper
================================================

Schema mapper for standalone parliamentary friendship groups files (GrupoDeAmizadeXX.xml).
These files contain comprehensive friendship group data including detailed member information,
meetings, visits, and participant records.

Based on analysis of actual XML structure from GrupoDeAmizadeXV.xml and other legislature files.

XML Structure:
- Root: ArrayOfGrupoDeAmizadeOut
- Main Group: GrupoDeAmizadeOut  
- Members: Composicao/DelegacaoPermanenteMembroOut
- Meetings/Visits: Visitas/GrupoDeAmizadeReuniao
- Participants: Participantes/RelacoesExternasParticipantes

Key differences from deputy activity GPA data:
- Standalone files with complete group information
- Detailed member composition with roles and service periods  
- Meeting and visit records with participant lists
- Not tied to specific deputy activities
"""

import xml.etree.ElementTree as ET
import os
import logging
from datetime import datetime
from typing import Dict, Optional, Set, List, Tuple

from .enhanced_base_mapper import SchemaMapper, SchemaError
from .common_utilities import DataValidationUtils

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    GrupoAmizadeStandalone, GrupoAmizadeMembro, GrupoAmizadeReuniao, 
    GrupoAmizadeParticipante, Legislatura
)

# GPA data is already in meaningful form, no field translation needed

logger = logging.getLogger(__name__)


class GruposAmizadeStandaloneMapper(SchemaMapper):
    """
    Schema mapper for standalone parliamentary friendship groups files
    
    Processes GrupoDeAmizadeXX.xml files containing comprehensive parliamentary
    friendship group data including:
    
    - Basic group information (ID, name, legislature, creation date)
    - Complete member composition with roles and service periods
    - Meeting and visit records with locations and dates
    - Detailed participant information for all events
    
    All field mappings based on actual XML structure analysis with proper
    field conversion using the grupos_amizade translator module.
    """
    
    def __init__(self, session):
        super().__init__(session)
        self.processed_groups = 0
        self.processed_members = 0
        self.processed_meetings = 0
        self.processed_participants = 0
        
    def get_expected_fields(self) -> Set[str]:
        """Define expected XML fields for validation"""
        return {
            # Root structure
            'ArrayOfGrupoDeAmizadeOut',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut',
            
            # Main group fields  
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Id',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Nome',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Legislatura',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Sessao',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.DataCriacao',
            
            # Member composition
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Composicao',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Composicao.DelegacaoPermanenteMembroOut',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Composicao.DelegacaoPermanenteMembroOut.Nome',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Composicao.DelegacaoPermanenteMembroOut.Gp',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Composicao.DelegacaoPermanenteMembroOut.Cargo',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Composicao.DelegacaoPermanenteMembroOut.DataInicio',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Composicao.DelegacaoPermanenteMembroOut.DataFim',
            
            # Meetings and visits
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Reunioes',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.Id',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.Nome',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.Tipo',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.Local',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.DataInicio',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.DataFim',
            
            # Meeting participants
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.Participantes',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.Participantes.RelacoesExternasParticipantes',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.Participantes.RelacoesExternasParticipantes.Id',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.Participantes.RelacoesExternasParticipantes.Nome',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.Participantes.RelacoesExternasParticipantes.Tipo',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.Participantes.RelacoesExternasParticipantes.Gp',
            'ArrayOfGrupoDeAmizadeOut.GrupoDeAmizadeOut.Visitas.GrupoDeAmizadeReuniao.Participantes.RelacoesExternasParticipantes.Leg'
        }
    
    def process_file(self, file_path: str) -> bool:
        """
        Process a standalone parliamentary friendship groups XML file
        
        Args:
            file_path: Path to GrupoDeAmizadeXX.xml file
            
        Returns:
            True if processing succeeded, False otherwise
        """
        try:
            logger.info(f"Processing GPA standalone file: {file_path}")
            
            # Parse XML file
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Validate root structure
            if root.tag != 'ArrayOfGrupoDeAmizadeOut':
                raise SchemaError(f"Unexpected root element: {root.tag}, expected: ArrayOfGrupoDeAmizadeOut")
            
            # Process each friendship group
            grupo_elements = root.findall('GrupoDeAmizadeOut')
            if not grupo_elements:
                logger.warning(f"No friendship groups found in file: {file_path}")
                return True
                
            for grupo_element in grupo_elements:
                self._process_grupo_amizade(grupo_element)
                
            logger.info(f"Successfully processed {len(grupo_elements)} friendship groups from {file_path}")
            logger.info(f"Total processed: {self.processed_groups} groups, {self.processed_members} members, "
                       f"{self.processed_meetings} meetings, {self.processed_participants} participants")
            
            return True
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error in file {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return False
    
    def _process_grupo_amizade(self, grupo_element: ET.Element) -> Optional[GrupoAmizadeStandalone]:
        """Process a single friendship group element"""
        try:
            # Extract basic group information
            group_id = self._get_int_value(grupo_element, 'Id')
            nome = self._get_text_value(grupo_element, 'Nome')
            legislatura = self._get_text_value(grupo_element, 'Legislatura')
            sessao = self._get_int_value(grupo_element, 'Sessao')
            data_criacao_str = self._get_text_value(grupo_element, 'DataCriacao')
            
            # Validate required fields
            if not group_id:
                logger.warning("Friendship group missing required Id field, skipping")
                return None
            if not nome:
                logger.warning(f"Friendship group {group_id} missing required Nome field, skipping")
                return None
            if not legislatura:
                logger.warning(f"Friendship group {group_id} missing required Legislatura field, skipping")
                return None
            
            # Parse data criacao using common utilities
            data_criacao = None
            if data_criacao_str:
                data_criacao = DataValidationUtils.parse_date_flexible(data_criacao_str)
            
            # Check if group already exists (avoid duplicates)
            existing_group = self.session.query(GrupoAmizadeStandalone).filter_by(
                group_id=group_id, 
                legislatura=legislatura
            ).first()
            
            if existing_group:
                logger.info(f"Friendship group {group_id} ({nome}) already exists for legislature {legislatura}, updating")
                grupo = existing_group
                grupo.nome = nome
                grupo.sessao = sessao
                grupo.data_criacao = data_criacao
            else:
                # Create new friendship group
                grupo = GrupoAmizadeStandalone(
                    group_id=group_id,
                    nome=nome,
                    legislatura=legislatura,
                    sessao=sessao,
                    data_criacao=data_criacao
                )
                self.session.add(grupo)
            
            self.session.flush()  # Get the ID for relationships
            
            # Process members
            composicao = grupo_element.find('Composicao')
            if composicao is not None:
                # Clear existing members for updates
                if existing_group:
                    self.session.query(GrupoAmizadeMembro).filter_by(grupo_amizade_id=grupo.id).delete()
                
                for membro_element in composicao.findall('DelegacaoPermanenteMembroOut'):
                    self._process_membro(membro_element, grupo.id)
            
            # Process meetings/visits
            visitas = grupo_element.find('Visitas')
            if visitas is not None:
                # Clear existing meetings for updates
                if existing_group:
                    self.session.query(GrupoAmizadeReuniao).filter_by(grupo_amizade_id=grupo.id).delete()
                
                for reuniao_element in visitas.findall('GrupoDeAmizadeReuniao'):
                    self._process_reuniao(reuniao_element, grupo.id)
            
            self.processed_groups += 1
            logger.debug(f"Processed friendship group: {group_id} ({nome}) - Legislature {legislatura}")
            
            return grupo
            
        except Exception as e:
            logger.error(f"Error processing friendship group: {e}")
            return None
    
    def _process_membro(self, membro_element: ET.Element, grupo_id: int) -> Optional[GrupoAmizadeMembro]:
        """Process a single group member element"""
        try:
            # Extract member information
            nome = self._get_text_value(membro_element, 'Nome')
            grupo_parlamentar = self._get_text_value(membro_element, 'Gp')
            cargo = self._get_text_value(membro_element, 'Cargo')
            data_inicio_str = self._get_text_value(membro_element, 'DataInicio')
            data_fim_str = self._get_text_value(membro_element, 'DataFim')
            
            if not nome:
                logger.warning("Group member missing required Nome field, skipping")
                return None
            
            # Parse dates using common utilities  
            data_inicio = None
            data_fim = None
            if data_inicio_str:
                data_inicio = DataValidationUtils.parse_date_flexible(data_inicio_str)
            if data_fim_str:
                data_fim = DataValidationUtils.parse_date_flexible(data_fim_str)
            
            # Create member record
            membro = GrupoAmizadeMembro(
                grupo_amizade_id=grupo_id,
                nome=nome,
                grupo_parlamentar=grupo_parlamentar,
                cargo=cargo,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            
            self.session.add(membro)
            self.processed_members += 1
            
            logger.debug(f"Processed member: {nome} ({cargo}) - GP: {grupo_parlamentar}")
            
            return membro
            
        except Exception as e:
            logger.error(f"Error processing group member: {e}")
            return None
    
    def _process_reuniao(self, reuniao_element: ET.Element, grupo_id: int) -> Optional[GrupoAmizadeReuniao]:
        """Process a single meeting/visit element"""
        try:
            # Extract meeting information
            meeting_id = self._get_int_value(reuniao_element, 'Id')
            nome = self._get_text_value(reuniao_element, 'Nome')
            tipo = self._get_text_value(reuniao_element, 'Tipo')
            local = self._get_text_value(reuniao_element, 'Local')
            data_inicio_str = self._get_text_value(reuniao_element, 'DataInicio')
            data_fim_str = self._get_text_value(reuniao_element, 'DataFim')
            
            # Validate required fields
            if not meeting_id:
                logger.warning("Meeting missing required Id field, skipping")
                return None
            if not nome:
                logger.warning(f"Meeting {meeting_id} missing required Nome field, skipping")
                return None
            if not data_inicio_str:
                logger.warning(f"Meeting {meeting_id} missing required DataInicio field, skipping")
                return None
            
            # Parse dates using common utilities
            data_inicio = DataValidationUtils.parse_date_flexible(data_inicio_str)
            data_fim = None
            if data_fim_str:
                data_fim = DataValidationUtils.parse_date_flexible(data_fim_str)
            
            if not data_inicio:
                logger.warning(f"Meeting {meeting_id} failed to parse DataInicio: {data_inicio_str}")
                return None
            
            # Create meeting record
            reuniao = GrupoAmizadeReuniao(
                grupo_amizade_id=grupo_id,
                meeting_id=meeting_id,
                nome=nome,
                tipo=tipo,
                local=local,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            
            self.session.add(reuniao)
            self.session.flush()  # Get the ID for participants
            
            # Process participants
            participantes = reuniao_element.find('Participantes')
            if participantes is not None:
                for participante_element in participantes.findall('RelacoesExternasParticipantes'):
                    self._process_participante(participante_element, reuniao.id)
            
            self.processed_meetings += 1
            logger.debug(f"Processed meeting: {meeting_id} ({nome[:50]}) - Location: {local}")
            
            return reuniao
            
        except Exception as e:
            logger.error(f"Error processing meeting: {e}")
            return None
    
    def _process_participante(self, participante_element: ET.Element, reuniao_id: int) -> Optional[GrupoAmizadeParticipante]:
        """Process a single meeting participant element"""
        try:
            # Extract participant information
            participant_id = self._get_int_value(participante_element, 'Id')
            nome = self._get_text_value(participante_element, 'Nome')
            tipo = self._get_text_value(participante_element, 'Tipo')
            grupo_parlamentar = self._get_text_value(participante_element, 'Gp')
            legislatura = self._get_text_value(participante_element, 'Leg')
            
            # Validate required fields
            if not participant_id:
                logger.warning("Participant missing required Id field, skipping")
                return None
            if not nome:
                logger.warning(f"Participant {participant_id} missing required Nome field, skipping")
                return None
            if not tipo:
                logger.warning(f"Participant {participant_id} missing required Tipo field, skipping")  
                return None
            
            # Create participant record
            participante = GrupoAmizadeParticipante(
                reuniao_id=reuniao_id,
                participant_id=participant_id,
                nome=nome,
                tipo=tipo,
                grupo_parlamentar=grupo_parlamentar,
                legislatura=legislatura
            )
            
            self.session.add(participante)
            self.processed_participants += 1
            
            logger.debug(f"Processed participant: {participant_id} ({nome}) - Type: {tipo}")
            
            return participante
            
        except Exception as e:
            logger.error(f"Error processing participant: {e}")
            return None
    
    def _get_text_value(self, element: ET.Element, tag: str) -> Optional[str]:
        """Safely extract text value from XML element"""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None
    
    def _get_int_value(self, element: ET.Element, tag: str) -> Optional[int]:
        """Safely extract integer value from XML element"""
        text_value = self._get_text_value(element, tag)
        if text_value:
            return DataValidationUtils.safe_int_convert(text_value)
        return None
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Return processing statistics"""
        return {
            'processed_groups': self.processed_groups,
            'processed_members': self.processed_members,
            'processed_meetings': self.processed_meetings,
            'processed_participants': self.processed_participants
        }