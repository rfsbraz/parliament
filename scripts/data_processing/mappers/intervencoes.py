"""
Parliamentary Interventions Mapper
==================================

Schema mapper for parliamentary interventions files (Intervencoes<Legislatura>.xml).
Based on official Parliament documentation (December 2017):
"Significado das Tags do Ficheiro Intervenções<Legislatura>.xml"

XML Structure:
- Root: Intervencoes_DadosPesquisaIntervencoesOut
- Multiple nested structures for activities, guests, audiovisual data, related initiatives, etc.
- Important coded values requiring translation:
  - TipodeDebate (1-37): Debate type codes with specific descriptions
  - TipodeIntervencao (2-2396): Intervention type codes
  - TipodePublicacao (A-V): Publication type codes
  - TipodeAtividade (AGP-VOT): Activity type codes
  - TipodeIniciativa (A-U): Initiative type codes (matches existing enum)

Handles deputy interventions in parliament sessions and maps them to the database
with comprehensive field mapping and coded value translations.
"""

import xml.etree.ElementTree as ET
import os
import re
import requests
import sys
import time
from typing import Dict, Optional, Set
import logging
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

from .enhanced_base_mapper import SchemaMapper, SchemaError
from .common_utilities import DataValidationUtils

# Import translators for coded values
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.translators import IntervencoesTranslator

# Import our models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    IntervencaoParlamentar, IntervencaoPublicacao, IntervencaoDeputado,
    IntervencaoMembroGoverno, IntervencaoConvidado, IntervencaoAtividadeRelacionada,
    IntervencaoIniciativa, IntervencaoAudiovisual, Deputado, Legislatura
)

logger = logging.getLogger(__name__)


class IntervencoesMapper(SchemaMapper):
    """
    Schema mapper for parliamentary interventions files
    
    Processes Intervencoes XML files containing parliamentary interventions data
    with comprehensive field mapping based on December 2017 specification.
    Includes coded value translation for debates, interventions, activities, and publications.
    """
    
    def __init__(self, session):
        # Accept SQLAlchemy session directly (passed by unified importer)
        super().__init__(session)
        # Initialize translator for coded values
        self.translator = IntervencoesTranslator()
        self.processed_interventions = 0
        self.processed_publications = 0
        self.processed_deputies = 0
        self.processed_government_members = 0
        self.processed_guests = 0
        self.processed_activities = 0
        self.processed_initiatives = 0
        self.processed_audiovisual = 0
    
    def get_expected_fields(self) -> Set[str]:
        """
        Define expected XML fields based on official Parliament documentation (December 2017).
        Maps complete Intervencoes_DadosPesquisaIntervencoesOut structure.
        """
        return {
            # Root structure (official spec)
            'Intervencoes_DadosPesquisaIntervencoesOut',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut',
            
            # Legacy structure (for backward compatibility)
            'ArrayOfDadosPesquisaIntervencoesOut',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut',
            
            # Main intervention fields (IntervencoesOut structure)
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.intId',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.intLeg',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.intSL',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.intNr',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.intDt',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.intTp',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.intQual',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.intSumario',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.intResumo',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.intFaseSL',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.ativId',
            
            # Legacy field mappings (for backward compatibility)
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Id',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DataReuniaoPlenaria',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.TipoIntervencao',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Resumo',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Sumario',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Legislatura',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Sessao',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Qualidade',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.FaseSessao',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.IdDebate',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Debate',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.ActividadeId',
            
            # Deputy fields (DeputadosOut structure)
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Deputados',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Deputados.DeputadosOut',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Deputados.DeputadosOut.depCadId',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Deputados.DeputadosOut.depNomeParlamentar',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Deputados.DeputadosOut.depNomeCompleto',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Deputados.DeputadosOut.depGP',
            
            # Legacy deputy fields
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Deputados',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Deputados.idCadastro',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Deputados.nome',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Deputados.GP',
            
            # Government members (MembroGovernoOut structure)
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.MembrosGoverno',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.MembrosGoverno.MembroGovernoOut',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.MembrosGoverno.MembroGovernoOut.memGovNome',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.MembrosGoverno.MembroGovernoOut.memGovCargo',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.MembrosGoverno.MembroGovernoOut.memGovNumero',
            
            # Legacy government members
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.MembrosGoverno',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.MembrosGoverno.nome',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.MembrosGoverno.cargo',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.MembrosGoverno.governo',
            
            # Guests (ConvidadoOut structure)
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Convidados',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Convidados.ConvidadoOut',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Convidados.ConvidadoOut.convNome',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Convidados.ConvidadoOut.convCargo',
            
            # Legacy guests
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Convidados',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Convidados.nome',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Convidados.cargo',
            
            # Publication fields (PublicacaoOut structure)
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Publicacao',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Publicacao.PublicacaoOut',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Publicacao.PublicacaoOut.pubDt',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Publicacao.PublicacaoOut.pubLeg',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Publicacao.PublicacaoOut.pubNr',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Publicacao.PublicacaoOut.pubSL',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Publicacao.PublicacaoOut.pubTp',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Publicacao.PublicacaoOut.pubTipo',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Publicacao.PublicacaoOut.pubIdInt',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Publicacao.PublicacaoOut.pubURL',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.Publicacao.PublicacaoOut.pubPag',
            
            # Legacy publication fields
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.idInt',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            
            # Related activities (AtividadeRelacionadaOut structure)
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.AtividadesRelacionadas',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.AtividadesRelacionadas.AtividadeRelacionadaOut',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.AtividadesRelacionadas.AtividadeRelacionadaOut.ativRelId',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.AtividadesRelacionadas.AtividadeRelacionadaOut.ativRelTp',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.AtividadesRelacionadas.AtividadeRelacionadaOut.ativRelTpDesc',
            
            # Legacy related activities
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.ActividadesRelacionadas',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.ActividadesRelacionadas.id',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.ActividadesRelacionadas.tipo',
            
            # Initiatives (IniciativasRelacionadasOut structure)
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.IniciativasRelacionadas',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.IniciativasRelacionadas.IniciativasRelacionadasOut',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.IniciativasRelacionadas.IniciativasRelacionadasOut.iniId',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.IniciativasRelacionadas.IniciativasRelacionadasOut.iniTp',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.IniciativasRelacionadas.IniciativasRelacionadasOut.iniTpDesc',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.IniciativasRelacionadas.IniciativasRelacionadasOut.iniFase',
            
            # Legacy initiatives
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Iniciativas',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Iniciativas.pt_gov_ar_objectos_intervencoes_IniciativasOut',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Iniciativas.pt_gov_ar_objectos_intervencoes_IniciativasOut.id',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Iniciativas.pt_gov_ar_objectos_intervencoes_IniciativasOut.tipo',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Iniciativas.pt_gov_ar_objectos_intervencoes_IniciativasOut.fase',
            
            # Audiovisual data (DadosAudiovisualOut structure)
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.DadosAudiovisual',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.DadosAudiovisual.DadosAudiovisualOut',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.DadosAudiovisual.DadosAudiovisualOut.audDuracao',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.DadosAudiovisual.DadosAudiovisualOut.audAssunto',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.DadosAudiovisual.DadosAudiovisualOut.audURL',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.DadosAudiovisual.DadosAudiovisualOut.audIntTp',
            'Intervencoes_DadosPesquisaIntervencoesOut.IntervencoesOut.DadosAudiovisual.DadosAudiovisualOut.audIntTpDesc',
            
            # Legacy audiovisual data
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DadosAudiovisual',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DadosAudiovisual.pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DadosAudiovisual.pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut.duracao',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DadosAudiovisual.pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut.assunto',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosAudiovisual.pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut.url',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DadosAudiovisual.pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut.tipoIntervencao',
            
            # Legacy audiovisual structure (for backward compatibility)
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.VideoAudio',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.VideoAudio.VideoUrl'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """
        Map parliamentary interventions to database with comprehensive field processing
        
        Supports both official structure (Intervencoes_DadosPesquisaIntervencoesOut)
        and legacy structure (ArrayOfDadosPesquisaIntervencoesOut) for backward compatibility.
        
        Args:
            xml_root: Root XML element 
            file_info: Dictionary containing file metadata
            strict_mode: Whether to exit on unmapped fields
            
        Returns:
            Dictionary with processing results
        """
        # Store for use in nested methods
        self.file_info = file_info
        
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        file_path = file_info['file_path']
        filename = os.path.basename(file_path)
        skip_video_processing = file_info.get('skip_video_processing', False)
        
        try:
            logger.info(f"Processing Intervencoes file: {file_path}")
            
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Extract legislatura from filename
            leg_match = re.search(r'Intervencoes(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)\.xml', filename)
            legislatura_sigla = leg_match.group(1) if leg_match else 'XVII'
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
            
            logger.info(f"Processing interventions from {filename} (Legislatura {legislatura_sigla})")
            
            # Determine XML structure - check for official vs legacy format
            intervention_elements = []
            
            # Try official structure first
            if xml_root.tag == 'Intervencoes_DadosPesquisaIntervencoesOut':
                intervention_elements = xml_root.findall('IntervencoesOut')
                logger.info(f"Using official XML structure: found {len(intervention_elements)} IntervencoesOut elements")
            
            # Fall back to legacy structure
            if not intervention_elements:
                intervention_elements = xml_root.findall('.//DadosPesquisaIntervencoesOut')
                logger.info(f"Using legacy XML structure: found {len(intervention_elements)} DadosPesquisaIntervencoesOut elements")
            
            # Process each intervention record
            for intervencao in intervention_elements:
                try:
                    success = self._process_intervencao_record(intervencao, legislatura, filename, skip_video_processing)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                        self.processed_interventions += 1
                except Exception as e:
                    error_msg = f"Intervention processing error in {filename}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
                    if strict_mode:
                        logger.error("Data integrity issue detected - exiting immediately")
                        import sys
                        sys.exit(1)
            
            # Commit all changes
            self.session.commit()
            
            logger.info(f"Successfully processed Intervencoes file: {file_path}")
            logger.info(f"Statistics: {self.processed_interventions} interventions, "
                       f"{self.processed_publications} publications, {self.processed_deputies} deputies, "
                       f"{self.processed_government_members} government members, {self.processed_guests} guests, "
                       f"{self.processed_activities} activities, {self.processed_initiatives} initiatives, "
                       f"{self.processed_audiovisual} audiovisual records")
            
            return results
            
        except Exception as e:
            error_msg = f"Critical error processing interventions: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            if strict_mode:
                logger.error("Data integrity issue detected - exiting immediately")
                import sys
                sys.exit(1)
            return results
    
    def _process_intervencao_record(self, intervencao: ET.Element, legislatura: Legislatura, filename: str = None, skip_video_processing: bool = False) -> bool:
        """
        Process individual intervention record with proper normalized storage
        
        Handles both official IntervencoesOut structure and legacy DadosPesquisaIntervencoesOut
        structure for backward compatibility.
        """
        try:
            # Determine structure type based on element tag
            is_official_structure = intervencao.tag == 'IntervencoesOut'
            
            # Extract basic fields - try official structure first, then legacy
            if is_official_structure:
                # Official structure field mapping
                id_elem = intervencao.find('intId')
                legislatura_elem = intervencao.find('intLeg')
                sessao_elem = intervencao.find('intSL')
                numero_elem = intervencao.find('intNr')
                data_elem = intervencao.find('intDt')
                tipo_elem = intervencao.find('intTp')
                tipo_desc_elem = intervencao.find('intTpdesc')
                qualidade_elem = intervencao.find('intQual')
                fase_sessao_elem = intervencao.find('intFaseSL')
                sumario_elem = intervencao.find('intSumario')
                resumo_elem = intervencao.find('intResumo')
                atividade_id_elem = intervencao.find('ativId')
                atividade_tipo_elem = intervencao.find('ativTp')
                atividade_tipo_desc_elem = intervencao.find('ativTpdesc')
                debate_tipo_elem = intervencao.find('debTp')
                debate_tipo_desc_elem = intervencao.find('debTpdesc')
                id_debate_elem = intervencao.find('debId')
                debate_desc_elem = intervencao.find('debDes')
                debate_fase_elem = intervencao.find('debFase')
            else:
                # Legacy structure field mapping
                id_elem = intervencao.find('Id')
                legislatura_elem = intervencao.find('Legislatura')
                sessao_elem = intervencao.find('Sessao')
                numero_elem = None
                data_elem = intervencao.find('DataReuniaoPlenaria')
                tipo_elem = intervencao.find('TipoIntervencao')
                tipo_desc_elem = None
                qualidade_elem = intervencao.find('Qualidade')
                fase_sessao_elem = intervencao.find('FaseSessao')
                sumario_elem = intervencao.find('Sumario')
                resumo_elem = intervencao.find('Resumo')
                atividade_id_elem = intervencao.find('ActividadeId')
                id_debate_elem = intervencao.find('IdDebate')
            
            if id_elem is None:
                logger.warning("Intervention missing required ID field, skipping")
                return False
            
            try:
                intervencao_id = DataValidationUtils.safe_float_convert(id_elem.text)
                if intervencao_id is not None:
                    intervencao_id = int(intervencao_id)
                
                # No translation needed for legacy structure - TipoIntervencao contains the description directly
                
                # Parse date
                data_reuniao = None
                if data_elem is not None and data_elem.text:
                    data_reuniao = DataValidationUtils.parse_date_flexible(data_elem.text)
                
                # Check if intervention already exists
                existing = None
                if intervencao_id:
                    existing = self.session.query(IntervencaoParlamentar).filter_by(
                        intervencao_id=intervencao_id
                    ).first()
                
                if existing:
                    # Update existing intervention
                    existing.legislatura_numero = legislatura_elem.text if legislatura_elem is not None else None
                    existing.sessao_numero = sessao_elem.text if sessao_elem is not None else None
                    # numero field does not exist in legacy XML structure
                    existing.tipo_intervencao = tipo_elem.text if tipo_elem is not None else None
                    existing.data_reuniao_plenaria = data_reuniao
                    existing.qualidade = qualidade_elem.text if qualidade_elem is not None else None
                    existing.fase_sessao = fase_sessao_elem.text if fase_sessao_elem is not None else None
                    existing.sumario = sumario_elem.text if sumario_elem is not None else None
                    existing.resumo = resumo_elem.text if resumo_elem is not None else None
                    existing.atividade_id = DataValidationUtils.safe_float_convert(atividade_id_elem.text) if atividade_id_elem is not None else None
                    existing.id_debate = DataValidationUtils.safe_float_convert(id_debate_elem.text) if id_debate_elem is not None else None
                    existing.legislatura_id = legislatura.id
                else:
                    # Create new intervention record
                    intervention = IntervencaoParlamentar(
                        intervencao_id=intervencao_id,
                        legislatura_numero=legislatura_elem.text if legislatura_elem is not None else None,
                        sessao_numero=sessao_elem.text if sessao_elem is not None else None,
                        # numero field does not exist in legacy XML structure
                        tipo_intervencao=tipo_elem.text if tipo_elem is not None else None,
                        data_reuniao_plenaria=data_reuniao,
                        qualidade=qualidade_elem.text if qualidade_elem is not None else None,
                        fase_sessao=fase_sessao_elem.text if fase_sessao_elem is not None else None,
                        sumario=sumario_elem.text if sumario_elem is not None else None,
                        resumo=resumo_elem.text if resumo_elem is not None else None,
                        atividade_id=DataValidationUtils.safe_float_convert(atividade_id_elem.text) if atividade_id_elem is not None else None,
                        id_debate=DataValidationUtils.safe_float_convert(id_debate_elem.text) if id_debate_elem is not None else None,
                        legislatura_id=legislatura.id
                    )
                    self.session.add(intervention)
                    self.session.flush()  # Get the ID
                    existing = intervention
                
                # Process related data using structure-aware methods
                structure_type = 'official' if is_official_structure else 'legacy'
                self._process_publicacao(intervencao, existing, structure_type)
                self._process_deputados(intervencao, existing, structure_type)
                self._process_membros_governo(intervencao, existing, structure_type)
                self._process_convidados(intervencao, existing, structure_type)
                self._process_atividades_relacionadas(intervencao, existing, structure_type)
                self._process_iniciativas(intervencao, existing, structure_type)
                self._process_audiovisual(intervencao, existing, filename, skip_video_processing, structure_type)
                
                return True
                
            except Exception as db_error:
                logger.error(f"Database error processing intervention {id_elem.text if id_elem is not None else 'unknown'}: {db_error}")
                raise
            
        except Exception as e:
            logger.error(f"Error processing intervention: {e}")
            return False
    
    def _process_publicacao(self, intervencao: ET.Element, intervention: IntervencaoParlamentar, structure_type: str = 'legacy'):
        """
        Process publication data
        
        Args:
            intervencao: XML element containing intervention data
            intervention: IntervencaoParlamentar instance
            structure_type: 'official' or 'legacy' to determine field mapping
        """
        publicacao_elem = intervencao.find('Publicacao')
        if publicacao_elem is not None:
            pub_dados_elem = None
            
            if structure_type == 'official':
                pub_dados_elem = publicacao_elem.find('PublicacaoOut')
            else:
                pub_dados_elem = publicacao_elem.find('pt_gov_ar_objectos_PublicacoesOut')
                
            if pub_dados_elem is not None:
                # Extract publication fields based on structure type
                if structure_type == 'official':
                    pub_numero = pub_dados_elem.find('pubNr')
                    pub_tipo = pub_dados_elem.find('pubTipo')
                    pub_tp = pub_dados_elem.find('pubTp')
                    pub_leg = pub_dados_elem.find('pubLeg')
                    pub_sl = pub_dados_elem.find('pubSL')
                    pub_data = pub_dados_elem.find('pubDt')
                    pag_elem = pub_dados_elem.find('pubPag')
                    id_interno = pub_dados_elem.find('pubIdInt')
                    url_diario = pub_dados_elem.find('pubURL')
                else:
                    pub_numero = pub_dados_elem.find('pubNr')
                    pub_tipo = pub_dados_elem.find('pubTipo')
                    pub_tp = pub_dados_elem.find('pubTp')
                    pub_leg = pub_dados_elem.find('pubLeg')
                    pub_sl = pub_dados_elem.find('pubSL')
                    pub_data = pub_dados_elem.find('pubdt')
                    pag_elem = pub_dados_elem.find('pag')
                    id_interno = pub_dados_elem.find('idInt')
                    url_diario = pub_dados_elem.find('URLDiario')
                
                # Handle page numbers (can be nested in legacy format)
                paginas = None
                if pag_elem is not None:
                    if structure_type == 'legacy':
                        string_elem = pag_elem.find('string')
                        if string_elem is not None:
                            paginas = string_elem.text
                        else:
                            paginas = pag_elem.text
                    else:
                        paginas = pag_elem.text
                
                # Translate publication type code
                pub_tp_code = pub_tp.text if pub_tp is not None else None
                pub_tipo_desc = pub_tipo.text if pub_tipo is not None else None
                if not pub_tipo_desc and pub_tp_code:
                    pub_tipo_desc = self.translator.publication_type(pub_tp_code)
                
                publicacao = IntervencaoPublicacao(
                    intervencao_id=intervention.id,
                    pub_nr=pub_numero.text if pub_numero is not None else None,
                    pub_tipo=pub_tipo_desc,
                    pub_tp=pub_tp_code,
                    pub_leg=pub_leg.text if pub_leg is not None else None,
                    pub_sl=DataValidationUtils.safe_float_convert(pub_sl.text) if pub_sl is not None else None,
                    pub_dt=DataValidationUtils.parse_date_flexible(pub_data.text) if pub_data is not None and pub_data.text else None,
                    pag=paginas,
                    id_int=DataValidationUtils.safe_float_convert(id_interno.text) if id_interno is not None else None,
                    url_diario=url_diario.text if url_diario is not None else None
                )
                self.session.add(publicacao)
                self.processed_publications += 1
    
    def _process_deputados(self, intervencao: ET.Element, intervention: IntervencaoParlamentar, structure_type: str = 'legacy'):
        """
        Process deputy data
        
        Args:
            intervencao: XML element containing intervention data
            intervention: IntervencaoParlamentar instance
            structure_type: 'official' or 'legacy' to determine field mapping
        """
        deputados_elem = intervencao.find('Deputados')
        if deputados_elem is not None:
            # Handle different structures
            deputy_records = []
            
            if structure_type == 'official':
                # Official structure may have multiple DeputadosOut elements
                deputy_records = deputados_elem.findall('DeputadosOut')
            else:
                # Legacy structure - single deputy data directly under Deputados
                deputy_records = [deputados_elem]
            
            for deputy_elem in deputy_records:
                if structure_type == 'official':
                    id_cadastro_elem = deputy_elem.find('depCadId')
                    nome_elem = deputy_elem.find('depNomeParlamentar')
                    nome_completo_elem = deputy_elem.find('depNomeCompleto')
                    gp_elem = deputy_elem.find('depGP')
                else:
                    id_cadastro_elem = deputy_elem.find('idCadastro')
                    nome_elem = deputy_elem.find('nome')
                    nome_completo_elem = None
                    gp_elem = deputy_elem.find('GP')
                
                # Only create record if there's actual deputy data
                if (id_cadastro_elem is not None and id_cadastro_elem.text) or (nome_elem is not None and nome_elem.text):
                    deputado = IntervencaoDeputado(
                        intervencao_id=intervention.id,
                        id_cadastro=DataValidationUtils.safe_float_convert(id_cadastro_elem.text) if id_cadastro_elem is not None else None,
                        nome=nome_elem.text if nome_elem is not None else None,
                        nome_completo=nome_completo_elem.text if nome_completo_elem is not None else None,
                        gp=gp_elem.text if gp_elem is not None else None
                    )
                    self.session.add(deputado)
                    self.processed_deputies += 1
    
    def _process_membros_governo(self, intervencao: ET.Element, intervention: IntervencaoParlamentar, structure_type: str = 'legacy'):
        """
        Process government members data
        
        Args:
            intervencao: XML element containing intervention data
            intervention: IntervencaoParlamentar instance
            structure_type: 'official' or 'legacy' to determine field mapping
        """
        membros_elem = intervencao.find('MembrosGoverno')
        if membros_elem is not None:
            # Handle different structures
            member_records = []
            
            if structure_type == 'official':
                member_records = membros_elem.findall('MembroGovernoOut')
            else:
                member_records = [membros_elem]
            
            for member_elem in member_records:
                if structure_type == 'official':
                    nome_elem = member_elem.find('memGovNome')
                    cargo_elem = member_elem.find('memGovCargo')
                    governo_elem = member_elem.find('memGovNumero')
                else:
                    nome_elem = member_elem.find('nome')
                    cargo_elem = member_elem.find('cargo')
                    governo_elem = member_elem.find('governo')
                
                if (nome_elem is not None and nome_elem.text) or (cargo_elem is not None and cargo_elem.text):
                    membro_governo = IntervencaoMembroGoverno(
                        intervencao_id=intervention.id,
                        nome=nome_elem.text if nome_elem is not None else None,
                        cargo=cargo_elem.text if cargo_elem is not None else None,
                        governo=governo_elem.text if governo_elem is not None else None
                    )
                    self.session.add(membro_governo)
                    self.processed_government_members += 1
    
    def _process_convidados(self, intervencao: ET.Element, intervention: IntervencaoParlamentar):
        """Process invited guests data"""
        convidados_elem = intervencao.find('Convidados')
        if convidados_elem is not None:
            nome_elem = convidados_elem.find('nome')
            cargo_elem = convidados_elem.find('cargo')
            
            if nome_elem is not None or cargo_elem is not None:
                convidado = IntervencaoConvidado(
                    intervencao_id=intervention.id,
                    nome=nome_elem.text if nome_elem is not None else None,
                    cargo=cargo_elem.text if cargo_elem is not None else None
                )
                self.session.add(convidado)
    
    def _process_atividades_relacionadas(self, intervencao: ET.Element, intervention: IntervencaoParlamentar):
        """Process related activities data"""
        atividades_elem = intervencao.find('ActividadesRelacionadas')
        if atividades_elem is not None:
            id_elem = atividades_elem.find('id')
            tipo_elem = atividades_elem.find('tipo')
            
            if id_elem is not None or tipo_elem is not None:
                atividade = IntervencaoAtividadeRelacionada(
                    intervencao_id=intervention.id,
                    atividade_id=self._safe_int(id_elem.text) if id_elem is not None else None,
                    tipo=tipo_elem.text if tipo_elem is not None else None
                )
                self.session.add(atividade)
    
    def _process_iniciativas(self, intervencao: ET.Element, intervention: IntervencaoParlamentar):
        """Process initiatives data"""
        iniciativas_elem = intervencao.find('Iniciativas')
        if iniciativas_elem is not None:
            init_dados_elem = iniciativas_elem.find('pt_gov_ar_objectos_intervencoes_IniciativasOut')
            if init_dados_elem is not None:
                id_elem = init_dados_elem.find('id')
                tipo_elem = init_dados_elem.find('tipo')
                fase_elem = init_dados_elem.find('fase')
                
                if id_elem is not None or tipo_elem is not None:
                    iniciativa = IntervencaoIniciativa(
                        intervencao_id=intervention.id,
                        iniciativa_id=self._safe_int(id_elem.text) if id_elem is not None else None,
                        tipo=tipo_elem.text if tipo_elem is not None else None,
                        fase=fase_elem.text if fase_elem is not None else None
                    )
                    self.session.add(iniciativa)
    
    def _process_audiovisual(self, intervencao: ET.Element, intervention: IntervencaoParlamentar, filename: str = None, skip_video_processing: bool = False):
        """Process audiovisual data with thumbnail extraction"""
        video_url = None
        thumbnail_url = None
        duracao = None
        assunto = None
        tipo_intervencao = None
        
        # Try old VideoAudio structure
        video_elem = intervencao.find('VideoAudio')
        if video_elem is not None:
            video_url_elem = video_elem.find('VideoUrl')
            if video_url_elem is not None:
                video_url = video_url_elem.text
        
        # Try new DadosAudiovisual structure
        if not video_url:
            audiovisual_elem = intervencao.find('DadosAudiovisual')
            if audiovisual_elem is not None:
                dados_elem = audiovisual_elem.find('pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut')
                if dados_elem is not None:
                    url_elem = dados_elem.find('url')
                    duracao_elem = dados_elem.find('duracao')
                    assunto_elem = dados_elem.find('assunto')
                    tipo_elem = dados_elem.find('tipoIntervencao')
                    
                    if url_elem is not None:
                        video_url = url_elem.text
                    if duracao_elem is not None:
                        duracao = duracao_elem.text
                    if assunto_elem is not None:
                        assunto = assunto_elem.text
                    if tipo_elem is not None:
                        tipo_intervencao = tipo_elem.text
        
        # Extract thumbnail if video URL exists and video processing is not skipped
        thumbnail_url = None
        original_video_url = video_url
        if video_url and not skip_video_processing:
            time.sleep(0.5)  # Small delay between requests
            result = self._extract_thumbnail_url_with_fallback(video_url, filename)
            if result:
                thumbnail_url, final_video_url = result
                # If the URL was cleaned during thumbnail extraction, use the cleaned version
                if final_video_url != original_video_url:
                    video_url = final_video_url
                    file_info = f" (from {filename})" if filename else ""
                    logger.info(f"Updated video URL to working version: {video_url}{file_info}")
            else:
                thumbnail_url = None
        elif video_url and skip_video_processing:
            logger.debug(f"Skipping video processing for: {video_url} (skip_video_processing=True)")
        
        # Store audiovisual data
        if video_url or duracao or assunto or tipo_intervencao:
            audiovisual = IntervencaoAudiovisual(
                intervencao_id=intervention.id,
                video_url=video_url,
                duracao=duracao,
                assunto=assunto,
                tipo_intervencao=tipo_intervencao
            )
            self.session.add(audiovisual)
    
    def _get_or_create_legislatura(self, sigla: str) -> Legislatura:
        """Get or create legislatura from sigla"""
        legislatura = self.session.query(Legislatura).filter_by(numero=sigla).first()
        
        if legislatura:
            return legislatura
        
        # Create new legislatura if it doesn't exist
        roman_to_num = {
            'XVII': 17, 'XVI': 16, 'XV': 15, 'XIV': 14, 'XIII': 13,
            'XII': 12, 'XI': 11, 'X': 10, 'IX': 9, 'VIII': 8,
            'VII': 7, 'VI': 6, 'V': 5, 'IV': 4, 'III': 3,
            'II': 2, 'I': 1, 'CONSTITUINTE': 0
        }
        
        numero_int = roman_to_num.get(sigla, 17)
        
        legislatura = Legislatura(
            numero=sigla,
            designacao=f"{numero_int}.ª Legislatura",
            ativa=False
        )
        
        self.session.add(legislatura)
        self.session.flush()  # Get the ID
        return legislatura
    
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to standard format"""
        if not date_str:
            return None
        try:
            from datetime import datetime as dt
            if len(date_str) == 10 and '-' in date_str:
                return date_str
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3 and len(parts[2]) == 4:
                    return f"{parts[2]}-{parts[1]:0>2}-{parts[0]:0>2}"
            return date_str
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return date_str
    
    def _extract_thumbnail_url_with_fallback(self, video_url: str, filename: str = None) -> Optional[tuple]:
        """Extract thumbnail URL from video page HTML with 404 fallback
        Returns: (thumbnail_url, final_video_url) or None if failed"""
        if not video_url:
            return None
        
        file_info = f" (from {filename})" if filename else ""
            
        def try_url(url: str) -> Optional[str]:
            """Try to extract thumbnail from a specific URL"""
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Search for the thumbnail URL pattern in HTML
                html_content = response.text
                
                # Pattern: <img loading="lazy" class="meeting-intervention-image" src="/api/v1/videos/Plenary/X/X/X/thumbnail/X" />
                thumbnail_pattern = r'class="meeting-intervention-image"\s+src="([^"]*thumbnail/\d+)"'
                match = re.search(thumbnail_pattern, html_content)
                
                if match:
                    thumbnail_path = match.group(1)
                    # Convert relative URL to absolute URL using video URL domain
                    parsed_video_url = urlparse(url)
                    base_url = f"{parsed_video_url.scheme}://{parsed_video_url.netloc}"
                    thumbnail_url = urljoin(base_url, thumbnail_path)
                    
                    logger.debug(f"Extracted thumbnail URL: {thumbnail_url}")
                    return thumbnail_url
                else:
                    logger.debug(f"No thumbnail found in video page: {url}")
                    return None
                    
            except requests.HTTPError as e:
                if e.response.status_code == 404:
                    logger.debug(f"404 error for URL: {url}{file_info}")
                    return None
                else:
                    logger.warning(f"HTTP error fetching video page {url}: {e}{file_info}")
                    return None
            except requests.RequestException as e:
                logger.warning(f"Failed to fetch video page {url}: {e}{file_info}")
                return None
            except Exception as e:
                logger.error(f"Error extracting thumbnail from {url}: {e}{file_info}")
                return None
        
        # Try the original URL first
        thumbnail_url = try_url(video_url)
        if thumbnail_url:
            return (thumbnail_url, video_url)
        
        # If original URL failed with 404 and has timestamps, try cleaning them
        if ('tI=' in video_url or 'drc=' in video_url):
            try:
                parsed_url = urlparse(video_url)
                query_params = parse_qs(parsed_url.query)
                
                # Remove time-related parameters
                if 'tI' in query_params:
                    del query_params['tI']
                if 'drc' in query_params:
                    del query_params['drc']
                
                # Reconstruct URL without time parameters
                new_query = urlencode(query_params, doseq=True)
                cleaned_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                if new_query:
                    cleaned_url += f"?{new_query}"
                
                logger.info(f"Retrying thumbnail extraction without timestamps: {cleaned_url}{file_info}")
                cleaned_thumbnail = try_url(cleaned_url)
                if cleaned_thumbnail:
                    return (cleaned_thumbnail, cleaned_url)
                
            except Exception as e:
                logger.warning(f"Could not clean timestamps from video URL {video_url}: {e}{file_info}")
        
        return None
    
    def _construct_direct_video_url(self, legislatura_num: int, sessao_num: int, atividade_id: int, intervencao_id: int) -> str:
        """Construct direct video URL using the pattern: /videos/Plenary/{leg}/{session}/{activity}/{intervention}"""
        return f"https://av.parlamento.pt/videos/Plenary/{legislatura_num}/{sessao_num}/{atividade_id}/{intervencao_id}"
    
    def _roman_to_number(self, roman: str) -> Optional[int]:
        """Convert roman numeral to number"""
        roman_map = {
            'XVII': 17, 'XVI': 16, 'XV': 15, 'XIV': 14, 'XIII': 13,
            'XII': 12, 'XI': 11, 'X': 10, 'IX': 9, 'VIII': 8,
            'VII': 7, 'VI': 6, 'V': 5, 'IV': 4, 'III': 3,
            'II': 2, 'I': 1, 'CONSTITUINTE': 0
        }
        return roman_map.get(roman.upper(), None)
    
    def _get_text_value(self, element: ET.Element, tag: str) -> Optional[str]:
        """Safely extract text value from XML element"""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Return processing statistics"""
        return {
            'processed_interventions': self.processed_interventions,
            'processed_publications': self.processed_publications,
            'processed_deputies': self.processed_deputies,
            'processed_government_members': self.processed_government_members,
            'processed_guests': self.processed_guests,
            'processed_activities': self.processed_activities,
            'processed_initiatives': self.processed_initiatives,
            'processed_audiovisual': self.processed_audiovisual
        }
    
    def close(self):
        """Close the database session"""
        if hasattr(self, 'session') and self.session:
            self.session.close()