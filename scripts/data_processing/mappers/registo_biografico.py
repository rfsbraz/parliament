"""
Biographical Registry Mapper
============================

Schema mapper for biographical registry files (RegistoBiografico*.xml).
Handles complete deputy biographical data including qualifications, roles, and organ activities.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Optional, Set
import logging

from .base_mapper import SchemaMapper, SchemaError

# Import our models
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import Deputado

logger = logging.getLogger(__name__)


class RegistoBiograficoMapper(SchemaMapper):
    """Schema mapper for biographical registry files"""
    
    def __init__(self, session):
        super().__init__(session)
        # Use the passed SQLAlchemy session
        self.session = session
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # I Legislature XML structure - Complete field coverage
            'RegistoBiografico',
            'RegistoBiografico.RegistoBiograficoList',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb',
            
            # Basic biographical data
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadNomeCompleto',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDtNascimento',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadSexo',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadProfissao',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadNaturalidade',
            
            # Academic qualifications (cadHabilitacoes)
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadHabilitacoes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadHabilitacoes.pt_ar_wsgode_objectos_DadosHabilitacoes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadHabilitacoes.pt_ar_wsgode_objectos_DadosHabilitacoes.habId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadHabilitacoes.pt_ar_wsgode_objectos_DadosHabilitacoes.habDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadHabilitacoes.pt_ar_wsgode_objectos_DadosHabilitacoes.habTipoId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadHabilitacoes.pt_ar_wsgode_objectos_DadosHabilitacoes.habEstado',
            
            # Professional roles (cadCargosFuncoes)
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCargosFuncoes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCargosFuncoes.pt_ar_wsgode_objectos_DadosCargosFuncoes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCargosFuncoes.pt_ar_wsgode_objectos_DadosCargosFuncoes.funId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCargosFuncoes.pt_ar_wsgode_objectos_DadosCargosFuncoes.funDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCargosFuncoes.pt_ar_wsgode_objectos_DadosCargosFuncoes.funOrdem',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCargosFuncoes.pt_ar_wsgode_objectos_DadosCargosFuncoes.funAntiga',
            
            # Titles/Awards (cadTitulos)
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadTitulos',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadTitulos.pt_ar_wsgode_objectos_DadosTitulos',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadTitulos.pt_ar_wsgode_objectos_DadosTitulos.titId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadTitulos.pt_ar_wsgode_objectos_DadosTitulos.titDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadTitulos.pt_ar_wsgode_objectos_DadosTitulos.titOrdem',
            
            # Decorations (cadCondecoracoes)
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCondecoracoes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCondecoracoes.pt_ar_wsgode_objectos_DadosCondecoracoes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCondecoracoes.pt_ar_wsgode_objectos_DadosCondecoracoes.codId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCondecoracoes.pt_ar_wsgode_objectos_DadosCondecoracoes.codDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadCondecoracoes.pt_ar_wsgode_objectos_DadosCondecoracoes.codOrdem',
            
            # Published Works (cadObrasPublicadas)
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadObrasPublicadas',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadObrasPublicadas.pt_ar_wsgode_objectos_DadosObrasPublicadas',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadObrasPublicadas.pt_ar_wsgode_objectos_DadosObrasPublicadas.pubId',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadObrasPublicadas.pt_ar_wsgode_objectos_DadosObrasPublicadas.pubDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadObrasPublicadas.pt_ar_wsgode_objectos_DadosObrasPublicadas.pubOrdem',
            
            # Organ activities
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeCom',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadActividadeOrgaos.actividadeGT',
            
            # Deputy legislature data with all I Legislature fields
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.depNomeParlamentar',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.legDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.ceDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.parSigla',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.parDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.gpSigla',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.gpDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.indDes',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.urlVideoBiografia',
            'RegistoBiografico.RegistoBiograficoList.pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb.cadDeputadoLegis.pt_ar_wsgode_objectos_DadosDeputadoLegis.indData',
            
            # Interest Registry V2 (RegistoInteressesV2List)
            'RegistoBiografico.RegistoInteressesV2List',
            'RegistoBiografico.RegistoInteressesV2List.pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2',
            'RegistoBiografico.RegistoInteressesV2List.pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2.cadId',
            'RegistoBiografico.RegistoInteressesV2List.pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2.cadEstadoCivilCod',
            'RegistoBiografico.RegistoInteressesV2List.pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2.cadNomeCompleto',
            'RegistoBiografico.RegistoInteressesV2List.pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2.cadActividadeProfissional',
            'RegistoBiografico.RegistoInteressesV2List.pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2.cadEstadoCivilDes',
            
            # Interest Registry V1 (RegistoInteressesList)
            'RegistoBiografico.RegistoInteressesList',
            
            # Additional Interest Registry versions found in I Legislature files
            'RegistoBiografico.RegistoInteressesV1List',
            'RegistoBiografico.RegistoInteressesV3List', 
            'RegistoBiografico.RegistoInteressesV5List',
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map I Legislature biographical data to database with comprehensive field processing"""
        results = {
            'records_processed': 0,
            'records_imported': 0,
            'errors': []
        }
        
        try:
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Process I Legislature biographical records  
            biografico_list = xml_root.find('RegistoBiograficoList')
            if biografico_list is not None:
                for record in biografico_list.findall('pt_ar_wsgode_objectos_DadosRegistoBiograficoWeb'):
                    try:
                        success = self._process_i_legislature_biographical_record(record, file_info)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                    except Exception as e:
                        error_msg = f"Error processing biographical record: {str(e)}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                        if strict_mode:
                            raise
            
            # Process Interest Registry V2 if present
            interesses_list = xml_root.find('RegistoInteressesV2List')
            if interesses_list is not None:
                for record in interesses_list.findall('pt_ar_wsgode_objectos_DadosDeputadoRgiWebV2'):
                    try:
                        success = self._process_registo_interesses_v2(record, file_info)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                    except Exception as e:
                        error_msg = f"Error processing interest registry V2: {str(e)}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                        if strict_mode:
                            raise
            
            return results
            
        except Exception as e:
            error_msg = f"Error in biographical mapping: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
            if strict_mode:
                raise
            return results
    
    def _process_i_legislature_biographical_record(self, record: ET.Element, file_info: Dict) -> bool:
        """Process comprehensive I Legislature biographical record with all fields"""
        try:
            from database.models import (
                Deputado, DeputadoHabilitacao, DeputadoCargoFuncao, DeputadoTitulo,
                DeputadoCondecoracao, DeputadoObraPublicada, DeputadoMandatoLegislativo
            )
            
            # Extract basic biographical data
            cad_id = self._get_text_value(record, 'cadId')
            if not cad_id:
                return False
                
            cad_id = int(float(cad_id))
            
            # Get or create deputy
            deputy = self.session.query(Deputado).filter(Deputado.id_cadastro == cad_id).first()
            if not deputy:
                deputy = Deputado(
                    id_cadastro=cad_id,
                    nome=self._get_text_value(record, 'cadNomeCompleto') or f"Deputy {cad_id}",
                    nome_completo=self._get_text_value(record, 'cadNomeCompleto'),
                    sexo=self._get_text_value(record, 'cadSexo'),  # New I Legislature field
                    profissao=self._get_text_value(record, 'cadProfissao'),
                    data_nascimento=self._parse_date(self._get_text_value(record, 'cadDtNascimento')),
                    naturalidade=self._get_text_value(record, 'cadNaturalidade')
                )
                self.session.add(deputy)
                self.session.flush()  # Get the ID
            else:
                # Update existing fields
                deputy.nome_completo = self._get_text_value(record, 'cadNomeCompleto') or deputy.nome_completo
                deputy.sexo = self._get_text_value(record, 'cadSexo') or deputy.sexo
                deputy.profissao = self._get_text_value(record, 'cadProfissao') or deputy.profissao
                deputy.data_nascimento = self._parse_date(self._get_text_value(record, 'cadDtNascimento')) or deputy.data_nascimento
                deputy.naturalidade = self._get_text_value(record, 'cadNaturalidade') or deputy.naturalidade
            
            # Process Academic Qualifications (cadHabilitacoes)
            habilitacoes = record.find('cadHabilitacoes')
            if habilitacoes is not None:
                for hab in habilitacoes.findall('pt_ar_wsgode_objectos_DadosHabilitacoes'):
                    hab_id = self._get_text_value(hab, 'habId')
                    if hab_id:
                        # Check if already exists
                        existing = self.session.query(DeputadoHabilitacao).filter(
                            DeputadoHabilitacao.deputado_id == deputy.id,
                            DeputadoHabilitacao.hab_id == int(float(hab_id))
                        ).first()
                        
                        if not existing:
                            qualification = DeputadoHabilitacao(
                                deputado_id=deputy.id,
                                hab_id=int(float(hab_id)),
                                hab_des=self._get_text_value(hab, 'habDes'),
                                hab_tipo_id=self._parse_int(self._get_text_value(hab, 'habTipoId')),
                                hab_estado=self._get_text_value(hab, 'habEstado')  # New I Legislature field
                            )
                            self.session.add(qualification)
            
            # Process Professional Roles (cadCargosFuncoes)
            cargos_funcoes = record.find('cadCargosFuncoes')
            if cargos_funcoes is not None:
                for cargo in cargos_funcoes.findall('pt_ar_wsgode_objectos_DadosCargosFuncoes'):
                    fun_id = self._get_text_value(cargo, 'funId')
                    if fun_id:
                        # Check if already exists
                        existing = self.session.query(DeputadoCargoFuncao).filter(
                            DeputadoCargoFuncao.deputado_id == deputy.id,
                            DeputadoCargoFuncao.fun_id == int(float(fun_id))
                        ).first()
                        
                        if not existing:
                            role = DeputadoCargoFuncao(
                                deputado_id=deputy.id,
                                fun_id=int(float(fun_id)),
                                fun_des=self._get_text_value(cargo, 'funDes'),
                                fun_ordem=self._parse_int(self._get_text_value(cargo, 'funOrdem')),  # New I Legislature field
                                fun_antiga=self._get_text_value(cargo, 'funAntiga')  # New I Legislature field
                            )
                            self.session.add(role)
            
            # Process Titles/Awards (cadTitulos)
            titulos = record.find('cadTitulos')
            if titulos is not None:
                for titulo in titulos.findall('pt_ar_wsgode_objectos_DadosTitulos'):
                    tit_id = self._get_text_value(titulo, 'titId')
                    if tit_id:
                        # Check if already exists
                        existing = self.session.query(DeputadoTitulo).filter(
                            DeputadoTitulo.deputado_id == deputy.id,
                            DeputadoTitulo.tit_id == int(float(tit_id))
                        ).first()
                        
                        if not existing:
                            title = DeputadoTitulo(
                                deputado_id=deputy.id,
                                tit_id=int(float(tit_id)),
                                tit_des=self._get_text_value(titulo, 'titDes'),
                                tit_ordem=self._parse_int(self._get_text_value(titulo, 'titOrdem'))
                            )
                            self.session.add(title)
            
            # Process Decorations (cadCondecoracoes)
            condecoracoes = record.find('cadCondecoracoes')
            if condecoracoes is not None:
                for cond in condecoracoes.findall('pt_ar_wsgode_objectos_DadosCondecoracoes'):
                    cod_id = self._get_text_value(cond, 'codId')
                    if cod_id:
                        # Check if already exists
                        existing = self.session.query(DeputadoCondecoracao).filter(
                            DeputadoCondecoracao.deputado_id == deputy.id,
                            DeputadoCondecoracao.cod_id == int(float(cod_id))
                        ).first()
                        
                        if not existing:
                            decoration = DeputadoCondecoracao(
                                deputado_id=deputy.id,
                                cod_id=int(float(cod_id)),
                                cod_des=self._get_text_value(cond, 'codDes'),
                                cod_ordem=self._parse_int(self._get_text_value(cond, 'codOrdem'))
                            )
                            self.session.add(decoration)
            
            # Process Published Works (cadObrasPublicadas)
            obras = record.find('cadObrasPublicadas')
            if obras is not None:
                for obra in obras.findall('pt_ar_wsgode_objectos_DadosObrasPublicadas'):
                    pub_id = self._get_text_value(obra, 'pubId')
                    if pub_id:
                        # Check if already exists
                        existing = self.session.query(DeputadoObraPublicada).filter(
                            DeputadoObraPublicada.deputado_id == deputy.id,
                            DeputadoObraPublicada.pub_id == int(float(pub_id))
                        ).first()
                        
                        if not existing:
                            publication = DeputadoObraPublicada(
                                deputado_id=deputy.id,
                                pub_id=int(float(pub_id)),
                                pub_des=self._get_text_value(obra, 'pubDes'),
                                pub_ordem=self._parse_int(self._get_text_value(obra, 'pubOrdem'))
                            )
                            self.session.add(publication)
            
            # Process Legislative Mandates (cadDeputadoLegis)
            legislaturas = record.find('cadDeputadoLegis')
            if legislaturas is not None:
                for mandato in legislaturas.findall('pt_ar_wsgode_objectos_DadosDeputadoLegis'):
                    leg_des = self._get_text_value(mandato, 'legDes')
                    ce_des = self._get_text_value(mandato, 'ceDes')
                    
                    if leg_des:
                        # Check if already exists
                        existing = self.session.query(DeputadoMandatoLegislativo).filter(
                            DeputadoMandatoLegislativo.deputado_id == deputy.id,
                            DeputadoMandatoLegislativo.leg_des == leg_des,
                            DeputadoMandatoLegislativo.ce_des == ce_des
                        ).first()
                        
                        if not existing:
                            mandate = DeputadoMandatoLegislativo(
                                deputado_id=deputy.id,
                                dep_nome_parlamentar=self._get_text_value(mandato, 'depNomeParlamentar'),
                                leg_des=leg_des,
                                ce_des=ce_des,  # New I Legislature field
                                par_sigla=self._get_text_value(mandato, 'parSigla'),
                                par_des=self._get_text_value(mandato, 'parDes'),
                                gp_sigla=self._get_text_value(mandato, 'gpSigla'),  # New I Legislature field
                                gp_des=self._get_text_value(mandato, 'gpDes'),  # New I Legislature field
                                ind_des=self._get_text_value(mandato, 'indDes'),  # New I Legislature field
                                url_video_biografia=self._get_text_value(mandato, 'urlVideoBiografia'),  # New I Legislature field
                                ind_data=self._parse_date(self._get_text_value(mandato, 'indData'))  # New I Legislature field
                            )
                            self.session.add(mandate)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing I Legislature biographical record: {e}")
            return False
    
    def _process_registo_interesses_v2(self, record: ET.Element, file_info: Dict) -> bool:
        """Process Interest Registry V2 record"""
        try:
            from database.models import RegistoInteressesV2, Deputado
            
            cad_id = self._get_text_value(record, 'cadId')
            if not cad_id:
                return False
                
            cad_id = int(float(cad_id))
            
            # Find the deputy
            deputy = self.session.query(Deputado).filter(Deputado.id_cadastro == cad_id).first()
            if not deputy:
                logger.warning(f"Deputy with id_cadastro {cad_id} not found for Interest Registry V2")
                return False
            
            # Check if already exists
            existing = self.session.query(RegistoInteressesV2).filter(
                RegistoInteressesV2.deputado_id == deputy.id,
                RegistoInteressesV2.cad_id == cad_id
            ).first()
            
            if not existing:
                interest_registry = RegistoInteressesV2(
                    deputado_id=deputy.id,
                    cad_id=cad_id,
                    cad_estado_civil_cod=self._get_text_value(record, 'cadEstadoCivilCod'),
                    cad_nome_completo=self._get_text_value(record, 'cadNomeCompleto'),  # New I Legislature field
                    cad_actividade_profissional=self._get_text_value(record, 'cadActividadeProfissional'),  # New I Legislature field
                    cad_estado_civil_des=self._get_text_value(record, 'cadEstadoCivilDes')  # New I Legislature field
                )
                self.session.add(interest_registry)
                
                # Also update deputy's marital status
                deputy.estado_civil_cod = self._get_text_value(record, 'cadEstadoCivilCod') or deputy.estado_civil_cod
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Interest Registry V2: {e}")
            return False
    
    def _get_text_value(self, element: ET.Element, tag: str) -> Optional[str]:
        """Get text value from XML element"""
        if element is None:
            return None
        child = element.find(tag)
        return child.text.strip() if child is not None and child.text else None
    
    def _parse_int(self, value: str) -> Optional[int]:
        """Parse integer from string"""
        if not value:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date from string"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
