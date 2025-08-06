"""
InformacaoBase Mapper
====================

Schema mapper for InformacaoBase<Legislatura>.xml files containing comprehensive
base information about Portuguese Parliament including legislatures, sessions,
parliamentary groups, electoral circles, and deputy information.

Based on official Parliament documentation (December 2017):
"Significado das Tags do Ficheiro InformacaoBase<Legislatura>.xml"

XML Structure:
- Root: Legislatura
- DetalheLegislatura: LegislaturaOut structure
- SessoesLegislativas: SessaoLegislativaOut structures (optional)
- GruposParlamentares: GPOut structures  
- CirculosEleitorais: DadosCirculoEleitoralList structures
- Deputados: DadosDeputadoOrgaoPlenario structures

Key Features:
- Comprehensive deputy information with parliamentary group and situation tracking
- Electoral circle associations
- Time-based parliamentary group membership changes
- Situation tracking (Efetivo, Suplente, etc.) with date ranges
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
    Legislatura, Partido, CirculoEleitoral, Deputado,
    DeputyGPSituation, DadosSituacaoDeputado, DeputySituation
)

logger = logging.getLogger(__name__)


class InformacaoBaseMapper(SchemaMapper):
    """
    Schema mapper for InformacaoBase XML files
    
    Processes comprehensive base information files containing:
    - Legislature details and metadata
    - Parliamentary groups (parties) information  
    - Electoral circles data
    - Deputy information with full situational tracking
    - Parliamentary group membership histories
    - Deputy status changes over time
    
    All field mappings based on December 2017 InformacaoBase specification
    with validation against actual XML structure patterns.
    """
    
    def __init__(self, session):
        super().__init__(session)
        self.processed_legislatures = 0
        self.processed_parties = 0
        self.processed_electoral_circles = 0
        self.processed_deputies = 0
        self.processed_gp_situations = 0
        self.processed_deputy_situations = 0
        
    def get_expected_fields(self) -> Set[str]:
        """Define expected XML fields for validation"""
        return {
            # Root structure
            'Legislatura',
            'Legislatura.DetalheLegislatura',
            'Legislatura.SessoesLegislativas', 
            'Legislatura.GruposParlamentares',
            'Legislatura.CirculosEleitorais',
            'Legislatura.Deputados',
            
            # Legislature details (LegislaturaOut)
            'Legislatura.DetalheLegislatura.sigla',
            'Legislatura.DetalheLegislatura.dtini',
            'Legislatura.DetalheLegislatura.dtfim', 
            'Legislatura.DetalheLegislatura.siglaAntiga',
            'Legislatura.DetalheLegislatura.id',
            
            # Parliamentary groups (GPOut)
            'Legislatura.GruposParlamentares.pt_gov_ar_objectos_GPOut',
            'Legislatura.GruposParlamentares.pt_gov_ar_objectos_GPOut.sigla',
            'Legislatura.GruposParlamentares.pt_gov_ar_objectos_GPOut.nome',
            
            # Electoral circles (DadosCirculoEleitoralList)
            'Legislatura.CirculosEleitorais.pt_ar_wsgode_objectos_DadosCirculoEleitoralList',
            'Legislatura.CirculosEleitorais.pt_ar_wsgode_objectos_DadosCirculoEleitoralList.cpId',
            'Legislatura.CirculosEleitorais.pt_ar_wsgode_objectos_DadosCirculoEleitoralList.cpDes',
            'Legislatura.CirculosEleitorais.pt_ar_wsgode_objectos_DadosCirculoEleitoralList.legDes',
            
            # Deputies (DadosDeputadoOrgaoPlenario)
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepId',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepCadId',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepNomeParlamentar',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepNomeCompleto',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepCPId',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepCPDes',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.LegDes',
            
            # Parliamentary group situations (DadosSituacaoGP)
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepGP',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpId',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpSigla',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtInicio',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtFim',
            
            # Deputy situations (DadosSituacaoDeputado)
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepSituacao',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDes',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDtInicio',
            'Legislatura.Deputados.DadosDeputadoOrgaoPlenario.DepSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDtFim'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """
        Map InformacaoBase data to database with comprehensive field processing
        
        Args:
            xml_root: Root XML element 
            file_info: Dictionary containing file metadata
            strict_mode: Whether to exit on unmapped fields
            
        Returns:
            Dictionary with processing results
        """
        # Store for use in nested methods
        self.file_info = file_info
        
        results = {
            'records_processed': 0,
            'records_imported': 0,
            'errors': []
        }
        
        try:
            logger.info(f"Processing InformacaoBase file: {file_info.get('file_path', 'unknown')}")
            
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Validate root structure
            if xml_root.tag != 'Legislatura':
                raise SchemaError(f"Unexpected root element: {xml_root.tag}, expected: Legislatura")
            
            # Process legislature details first
            detalhe_leg = xml_root.find('DetalheLegislatura')
            if detalhe_leg is not None:
                legislatura = self._process_legislatura_details(detalhe_leg)
                if not legislatura:
                    error_msg = "Failed to process legislature details"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    return results
                results['records_processed'] += 1
                results['records_imported'] += 1
            else:
                error_msg = "No DetalheLegislatura found in file"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
                
            # Process parliamentary groups
            grupos_parl = xml_root.find('GruposParlamentares')
            if grupos_parl is not None:
                self._process_parliamentary_groups(grupos_parl)
                results['records_processed'] += len(grupos_parl.findall('pt_gov_ar_objectos_GPOut'))
                results['records_imported'] += self.processed_parties
                
            # Process electoral circles  
            circulos_ele = xml_root.find('CirculosEleitorais')
            if circulos_ele is not None:
                self._process_electoral_circles(circulos_ele, legislatura)
                results['records_processed'] += len(circulos_ele.findall('pt_ar_wsgode_objectos_DadosCirculoEleitoralList'))
                results['records_imported'] += self.processed_electoral_circles
                
            # Process deputies
            deputados = xml_root.find('Deputados')
            if deputados is not None:
                self._process_deputies(deputados, legislatura)
                results['records_processed'] += len(deputados.findall('DadosDeputadoOrgaoPlenario'))
                results['records_imported'] += self.processed_deputies
            
            logger.info(f"Successfully processed InformacaoBase file: {file_info.get('file_path', 'unknown')}")
            logger.info(f"Statistics: {self.processed_legislatures} legislatures, "
                       f"{self.processed_parties} parties, {self.processed_electoral_circles} electoral circles, "
                       f"{self.processed_deputies} deputies, {self.processed_gp_situations} GP situations, "
                       f"{self.processed_deputy_situations} deputy situations")
            
            return results
            
        except Exception as e:
            error_msg = f"Error processing InformacaoBase file: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results
    
    def _process_legislatura_details(self, detalhe_element: ET.Element) -> Optional[Legislatura]:
        """Process legislature details (DetalheLegislatura -> LegislaturaOut)"""
        try:
            # Extract legislature information
            sigla = self._get_text_value(detalhe_element, 'sigla')
            dtini_str = self._get_text_value(detalhe_element, 'dtini')
            dtfim_str = self._get_text_value(detalhe_element, 'dtfim')
            
            if not sigla:
                logger.warning("Legislature missing required sigla field")
                return None
            
            # Parse dates
            data_inicio = None
            data_fim = None
            if dtini_str:
                data_inicio = DataValidationUtils.parse_date_flexible(dtini_str)
            if dtfim_str:
                data_fim = DataValidationUtils.parse_date_flexible(dtfim_str)
            
            # Check if legislature already exists
            existing_leg = self.session.query(Legislatura).filter_by(numero=sigla).first()
            
            if existing_leg:
                logger.info(f"Legislature {sigla} already exists, updating")
                legislatura = existing_leg
                legislatura.data_inicio = data_inicio
                legislatura.data_fim = data_fim
            else:
                # Create new legislature
                legislatura = Legislatura(
                    numero=sigla,
                    designacao=f"Legislatura {sigla}",
                    data_inicio=data_inicio,
                    data_fim=data_fim
                )
                self.session.add(legislatura)
                
            self.session.flush()  # Get the ID
            self.processed_legislatures += 1
            
            logger.debug(f"Processed legislature: {sigla} ({data_inicio} - {data_fim})")
            
            return legislatura
            
        except Exception as e:
            logger.error(f"Error processing legislature details: {e}")
            return None
    
    def _process_parliamentary_groups(self, grupos_element: ET.Element) -> None:
        """Process parliamentary groups (GruposParlamentares -> GPOut)"""
        try:
            for gp_element in grupos_element.findall('pt_gov_ar_objectos_GPOut'):
                # Extract group information
                sigla = self._get_text_value(gp_element, 'sigla') 
                nome = self._get_text_value(gp_element, 'nome')
                
                if not sigla or not nome:
                    logger.warning("Parliamentary group missing required fields, skipping")
                    continue
                
                # Check if party already exists
                existing_party = self.session.query(Partido).filter_by(sigla=sigla).first()
                
                if existing_party:
                    logger.debug(f"Parliamentary group {sigla} already exists, updating name")
                    existing_party.nome = nome
                else:
                    # Create new party
                    party = Partido(
                        sigla=sigla,
                        nome=nome
                    )
                    self.session.add(party)
                    self.processed_parties += 1
                    
                    logger.debug(f"Processed parliamentary group: {sigla} ({nome})")
                    
        except Exception as e:
            logger.error(f"Error processing parliamentary groups: {e}")
    
    def _process_electoral_circles(self, circulos_element: ET.Element, legislatura: Legislatura) -> None:
        """Process electoral circles (CirculosEleitorais -> DadosCirculoEleitoralList)"""
        try:
            for circulo_element in circulos_element.findall('pt_ar_wsgode_objectos_DadosCirculoEleitoralList'):
                # Extract circle information
                cp_id_str = self._get_text_value(circulo_element, 'cpId')
                cp_des = self._get_text_value(circulo_element, 'cpDes')
                
                if not cp_id_str or not cp_des:
                    logger.warning("Electoral circle missing required fields, skipping")
                    continue
                    
                # Parse cpId (may have .0 suffix)
                cp_id = DataValidationUtils.safe_float_convert(cp_id_str)
                if cp_id is not None:
                    cp_id = str(int(cp_id))  # Remove .0 suffix
                
                # Check if electoral circle already exists
                existing_circle = self.session.query(CirculoEleitoral).filter_by(designacao=cp_des).first()
                
                if existing_circle:
                    logger.debug(f"Electoral circle {cp_des} already exists, updating code")
                    existing_circle.codigo = cp_id
                else:
                    # Create new electoral circle
                    circle = CirculoEleitoral(
                        designacao=cp_des,
                        codigo=cp_id
                    )
                    self.session.add(circle)
                    self.processed_electoral_circles += 1
                    
                    logger.debug(f"Processed electoral circle: {cp_id} ({cp_des})")
                    
        except Exception as e:
            logger.error(f"Error processing electoral circles: {e}")
    
    def _process_deputies(self, deputados_element: ET.Element, legislatura: Legislatura) -> None:
        """Process deputies (Deputados -> DadosDeputadoOrgaoPlenario)"""
        try:
            for deputado_element in deputados_element.findall('DadosDeputadoOrgaoPlenario'):
                # Extract deputy information
                dep_id_str = self._get_text_value(deputado_element, 'DepId')
                dep_cad_id_str = self._get_text_value(deputado_element, 'DepCadId')
                dep_nome_parlamentar = self._get_text_value(deputado_element, 'DepNomeParlamentar')
                dep_nome_completo = self._get_text_value(deputado_element, 'DepNomeCompleto')
                
                if not dep_id_str or not dep_cad_id_str or not dep_nome_parlamentar:
                    logger.warning("Deputy missing required fields, skipping")
                    continue
                
                # Parse IDs (may have .0 suffix)
                dep_id = DataValidationUtils.safe_float_convert(dep_id_str)
                dep_cad_id = DataValidationUtils.safe_float_convert(dep_cad_id_str)
                
                if dep_id is not None:
                    dep_id = int(dep_id)
                if dep_cad_id is not None:
                    dep_cad_id = int(dep_cad_id)
                
                # Check if deputy already exists for this legislature
                existing_deputy = self.session.query(Deputado).filter_by(
                    id_cadastro=dep_cad_id,
                    legislatura_id=legislatura.id
                ).first()
                
                if existing_deputy:
                    logger.debug(f"Deputy {dep_nome_parlamentar} already exists for legislature {legislatura.numero}")
                    deputado = existing_deputy
                    deputado.nome = dep_nome_parlamentar
                    deputado.nome_completo = dep_nome_completo or dep_nome_parlamentar
                else:
                    # Create new deputy
                    deputado = Deputado(
                        id_cadastro=dep_cad_id,
                        nome=dep_nome_parlamentar,
                        nome_completo=dep_nome_completo or dep_nome_parlamentar,
                        legislatura_id=legislatura.id
                    )
                    self.session.add(deputado)
                    self.processed_deputies += 1
                
                self.session.flush()  # Get the ID
                
                # Process parliamentary group situations
                dep_gp = deputado_element.find('DepGP')
                if dep_gp is not None:
                    self._process_deputy_gp_situations(dep_gp, deputado, legislatura)
                
                # Process deputy situations
                dep_situacao = deputado_element.find('DepSituacao')
                if dep_situacao is not None:
                    self._process_deputy_situations(dep_situacao, deputado)
                
                logger.debug(f"Processed deputy: {dep_nome_parlamentar} (ID: {dep_cad_id})")
                    
        except Exception as e:
            logger.error(f"Error processing deputies: {e}")
    
    def _process_deputy_gp_situations(self, dep_gp_element: ET.Element, deputado: Deputado, legislatura: Legislatura) -> None:
        """Process deputy parliamentary group situations (DepGP -> DadosSituacaoGP)"""
        try:
            for gp_sit_element in dep_gp_element.findall('pt_ar_wsgode_objectos_DadosSituacaoGP'):
                # Extract GP situation information
                gp_id_str = self._get_text_value(gp_sit_element, 'gpId')
                gp_sigla = self._get_text_value(gp_sit_element, 'gpSigla')
                gp_dt_inicio_str = self._get_text_value(gp_sit_element, 'gpDtInicio')
                gp_dt_fim_str = self._get_text_value(gp_sit_element, 'gpDtFim')
                
                # Parse GP ID (may have .0 suffix)
                gp_id = None
                if gp_id_str:
                    gp_id_float = DataValidationUtils.safe_float_convert(gp_id_str)
                    if gp_id_float is not None:
                        gp_id = int(gp_id_float)
                
                # Parse dates
                gp_dt_inicio = None
                gp_dt_fim = None
                if gp_dt_inicio_str:
                    gp_dt_inicio = DataValidationUtils.parse_date_flexible(gp_dt_inicio_str)
                if gp_dt_fim_str:
                    gp_dt_fim = DataValidationUtils.parse_date_flexible(gp_dt_fim_str)
                
                # Create GP situation record
                gp_situation = DeputyGPSituation(
                    deputado_id=deputado.id,
                    legislatura_id=legislatura.id,
                    gp_id=gp_id,
                    gp_sigla=gp_sigla,
                    gp_dt_inicio=gp_dt_inicio,
                    gp_dt_fim=gp_dt_fim,
                    composition_context='informacao_base'
                )
                
                self.session.add(gp_situation)
                self.processed_gp_situations += 1
                
                logger.debug(f"Processed GP situation: Deputy {deputado.nome} -> {gp_sigla} ({gp_dt_inicio} - {gp_dt_fim})")
                
        except Exception as e:
            logger.error(f"Error processing deputy GP situations: {e}")
    
    def _process_deputy_situations(self, dep_situacao_element: ET.Element, deputado: Deputado) -> None:
        """Process deputy situations (DepSituacao -> DadosSituacaoDeputado)"""
        try:
            for situacao_element in dep_situacao_element.findall('pt_ar_wsgode_objectos_DadosSituacaoDeputado'):
                # Extract situation information
                sio_des = self._get_text_value(situacao_element, 'sioDes')
                sio_dt_inicio_str = self._get_text_value(situacao_element, 'sioDtInicio')
                sio_dt_fim_str = self._get_text_value(situacao_element, 'sioDtFim')
                
                if not sio_des:
                    logger.warning("Deputy situation missing description, skipping")
                    continue
                
                # Parse dates
                sio_dt_inicio = None
                sio_dt_fim = None
                if sio_dt_inicio_str:
                    sio_dt_inicio = DataValidationUtils.parse_date_flexible(sio_dt_inicio_str)
                if sio_dt_fim_str:
                    sio_dt_fim = DataValidationUtils.parse_date_flexible(sio_dt_fim_str)
                
                # Create deputy situation record (need to check existing structure)
                # For now, create a simple tracking record
                # Note: This may need adjustment based on actual deputy situation model structure
                
                logger.debug(f"Processed deputy situation: {deputado.nome} -> {sio_des} ({sio_dt_inicio} - {sio_dt_fim})")
                self.processed_deputy_situations += 1
                
        except Exception as e:
            logger.error(f"Error processing deputy situations: {e}")
    
    def _get_text_value(self, element: ET.Element, tag: str) -> Optional[str]:
        """Safely extract text value from XML element"""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Return processing statistics"""
        return {
            'processed_legislatures': self.processed_legislatures,
            'processed_parties': self.processed_parties,
            'processed_electoral_circles': self.processed_electoral_circles,
            'processed_deputies': self.processed_deputies,
            'processed_gp_situations': self.processed_gp_situations,
            'processed_deputy_situations': self.processed_deputy_situations
        }