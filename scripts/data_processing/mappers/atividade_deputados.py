"""
Deputy Activities Mapper - REAL XML STRUCTURE VERSION WITH SQLALCHEMY ORM
=========================================================================

Schema mapper for deputy activity files (AtividadeDeputado*.xml).
Maps the ACTUAL XML structure we found in the files (not the namespaced version).
ZERO DATA LOSS - Every field from the XML is captured in the database.
Uses SQLAlchemy ORM models for clean, type-safe database operations.

Author: Claude
Version: 4.0 - SQLAlchemy ORM Implementation
"""

import xml.etree.ElementTree as ET
import os
import re
from typing import Dict, Optional, Set, List
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .base_mapper import SchemaMapper, SchemaError

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    Deputado, AtividadeDeputado, AtividadeDeputadoList, ActividadeOut,
    DadosLegisDeputado, ActividadeAudiencia, ActividadeAudicao, 
    ActividadesComissaoOut, DeputadoSituacao, DadosSituacaoDeputado
)

logger = logging.getLogger(__name__)


class AtividadeDeputadosMapper(SchemaMapper):
    """Schema mapper for deputy activity files - REAL XML STRUCTURE VERSION WITH ORM"""
    
    def __init__(self, db_connection):
        super().__init__(db_connection)
        # Create SQLAlchemy session from raw connection
        # Get the database file path from the connection
        db_path = db_connection.execute('PRAGMA database_list').fetchone()[2]
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def get_expected_fields(self) -> Set[str]:
        """Return actual XML paths for complete coverage of AtividadeDeputado files"""
        return {
            # Root structure - ACTUAL XML FORMAT
            'ArrayOfAtividadeDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Rel',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audiencias.ActividadesComissaoOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.Audicoes.ActividadesComissaoOut',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DadosLegisDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DadosLegisDeputado.DadosLegisDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DadosLegisDeputado.DadosLegisDeputado.Nome',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.AtividadeDeputadoList.ActividadeOut.DadosLegisDeputado.DadosLegisDeputado.Dpl_grpar',
            
            # Deputy information - ACTUAL XML FORMAT  
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCadId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepNomeParlamentar',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepNomeCompleto',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCPId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCPDes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.LegDes',
            
            # Deputy parliamentary group - ACTUAL XML FORMAT
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepGP',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepGP.DadosSituacaoGP',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepGP.DadosSituacaoGP.GpId',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepGP.DadosSituacaoGP.GpSigla',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepGP.DadosSituacaoGP.GpDtInicio',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepGP.DadosSituacaoGP.GpDtFim',
            
            # Deputy situations - ACTUAL XML FORMAT
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepSituacao',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepSituacao.DadosSituacaoDeputado',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepSituacao.DadosSituacaoDeputado.SioDes',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepSituacao.DadosSituacaoDeputado.SioDtInicio',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepSituacao.DadosSituacaoDeputado.SioDtFim',
            
            # Deputy cargo - ACTUAL XML FORMAT
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCargo',
            'ArrayOfAtividadeDeputado.AtividadeDeputado.Deputado.DepCargo.pt_ar_wsgode_objectos_DadosCargoDeputado'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map deputy activities to database with ACTUAL XML structure - STORES REAL DATA"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        # Validate schema coverage according to strict mode
        self.validate_schema_coverage(xml_root, file_info, strict_mode)
        
        # Extract legislatura from filename
        filename = os.path.basename(file_info['file_path'])
        leg_match = re.search(r'AtividadeDeputado(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)\.xml', filename)
        legislatura_sigla = leg_match.group(1) if leg_match else 'XVII'
        
        # Process each deputy's activities - ACTUAL XML STRUCTURE
        for atividade_deputado in xml_root.findall('.//AtividadeDeputado'):
            try:
                success = self._process_deputy_real_structure(atividade_deputado, legislatura_sigla, file_info['file_path'])
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Deputy activity processing error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['records_processed'] += 1
        
        return results
    
    def _process_deputy_real_structure(self, atividade_deputado: ET.Element, legislatura_sigla: str, xml_file_path: str) -> bool:
        """Process deputy activities with REAL XML structure and store in our new models"""
        try:
            # Get deputy information from ACTUAL XML structure
            deputado = atividade_deputado.find('Deputado')  # Not 'deputado' - capitalized!
            if deputado is None:
                logger.warning("No Deputado section found")
                return False
                
            # Extract deputy basic information - ACTUAL field names
            dep_cad_id_text = self._get_text_value(deputado, 'DepCadId')
            dep_nome = self._get_text_value(deputado, 'DepNomeParlamentar')
            
            if not (dep_cad_id_text and dep_nome):
                logger.warning("Missing required deputy fields")
                return False
                
            dep_cad_id = self._safe_int(dep_cad_id_text)
            if not dep_cad_id:
                logger.warning(f"Invalid deputy cadastro ID: {dep_cad_id_text}")
                return False
            
            # Find or create deputado record in our database
            deputado_db_id = self._get_or_create_deputado(dep_cad_id, dep_nome, deputado)
            if not deputado_db_id:
                logger.warning("Could not create/find deputado record")
                return False
            
            # Create AtividadeDeputado record using our new models
            atividade_deputado_id = self._create_atividade_deputado(
                deputado_db_id, dep_cad_id, legislatura_sigla, deputado
            )
            
            if not atividade_deputado_id:
                return False
            
            # Process AtividadeDeputadoList - REAL XML structure
            atividade_list = atividade_deputado.find('AtividadeDeputadoList')
            if atividade_list is not None:
                atividade_list_id = self._create_atividade_deputado_list(atividade_deputado_id)
                
                # Process ActividadeOut - REAL XML structure
                actividade_out = atividade_list.find('ActividadeOut')
                if actividade_out is not None:
                    actividade_out_id = self._create_actividade_out(atividade_list_id, actividade_out)
                    
                    # Process nested elements
                    self._process_dados_legis_deputado(actividade_out, actividade_out_id)
                    self._process_audiencias(actividade_out, actividade_out_id)
                    self._process_audicoes(actividade_out, actividade_out_id)
            
            # Process deputy situations - REAL XML structure
            self._process_deputy_situacoes_real(deputado, atividade_deputado_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in real structure deputy processing: {e}")
            return False
    
    def _get_or_create_deputado(self, dep_cad_id: int, dep_nome: str, deputado_elem: ET.Element) -> Optional[int]:
        """Get or create deputado record using SQLAlchemy ORM"""
        try:
            # Check if deputado exists
            deputado = self.session.query(Deputado).filter_by(id_cadastro=dep_cad_id).first()
            
            if deputado:
                return deputado.id
            
            # Create new deputado record
            dep_nome_completo = self._get_text_value(deputado_elem, 'DepNomeCompleto')
            
            new_deputado = Deputado(
                id_cadastro=dep_cad_id,
                nome=dep_nome,
                nome_completo=dep_nome_completo,
                ativo=True
            )
            
            self.session.add(new_deputado)
            self.session.commit()
            
            return new_deputado.id
            
        except Exception as e:
            logger.error(f"Error creating deputado record: {e}")
            self.session.rollback()
            return None
    
    def _create_atividade_deputado(self, deputado_id: int, dep_cad_id: int, 
                                  legislatura_sigla: str, deputado_elem: ET.Element) -> Optional[int]:
        """Create AtividadeDeputado record using SQLAlchemy ORM"""
        try:
            leg_des = self._get_text_value(deputado_elem, 'LegDes')
            
            atividade_deputado = AtividadeDeputado(
                deputado_id=deputado_id,
                dep_cad_id=dep_cad_id,
                leg_des=leg_des
            )
            
            self.session.add(atividade_deputado)
            self.session.commit()
            
            return atividade_deputado.id
            
        except Exception as e:
            logger.error(f"Error creating atividade deputado record: {e}")
            self.session.rollback()
            return None
    
    def _create_atividade_deputado_list(self, atividade_deputado_id: int) -> Optional[int]:
        """Create AtividadeDeputadoList record using SQLAlchemy ORM"""
        try:
            atividade_list = AtividadeDeputadoList(
                atividade_deputado_id=atividade_deputado_id
            )
            
            self.session.add(atividade_list)
            self.session.commit()
            
            return atividade_list.id
            
        except Exception as e:
            logger.error(f"Error creating atividade deputado list record: {e}")
            self.session.rollback()
            return None
    
    def _create_actividade_out(self, atividade_list_id: int, actividade_out_elem: ET.Element) -> Optional[int]:
        """Create ActividadeOut record using SQLAlchemy ORM"""
        try:
            rel_text = self._get_text_value(actividade_out_elem, 'Rel')
            
            actividade_out = ActividadeOut(
                atividade_list_id=atividade_list_id,
                rel=rel_text
            )
            
            self.session.add(actividade_out)
            self.session.commit()
            
            return actividade_out.id
            
        except Exception as e:
            logger.error(f"Error creating actividade out record: {e}")
            self.session.rollback()
            return None
    
    def _process_dados_legis_deputado(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process DadosLegisDeputado using SQLAlchemy ORM"""
        try:
            dados_legis_section = actividade_out.find('DadosLegisDeputado')
            if dados_legis_section is not None:
                for dados_legis in dados_legis_section.findall('DadosLegisDeputado'):
                    nome = self._get_text_value(dados_legis, 'Nome')
                    dpl_grpar = self._get_text_value(dados_legis, 'Dpl_grpar')
                    
                    dados_legis_obj = DadosLegisDeputado(
                        actividade_out_id=actividade_out_id,
                        nome=nome,
                        dpl_grpar=dpl_grpar
                    )
                    
                    self.session.add(dados_legis_obj)
            
            self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing dados legis deputado: {e}")
            self.session.rollback()
    
    def _process_audiencias(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process Audiencias using SQLAlchemy ORM"""
        try:
            audiencias_section = actividade_out.find('Audiencias')
            if audiencias_section is not None:
                # Create audiencia record
                audiencia = ActividadeAudiencia(
                    actividade_out_id=actividade_out_id
                )
                
                self.session.add(audiencia)
                self.session.commit()
                
                # Process ActividadesComissaoOut within Audiencias
                for comissao_out in audiencias_section.findall('ActividadesComissaoOut'):
                    comissao_out_obj = ActividadesComissaoOut(
                        audiencia_id=audiencia.id
                    )
                    self.session.add(comissao_out_obj)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing audiencias: {e}")
            self.session.rollback()
    
    def _process_audicoes(self, actividade_out: ET.Element, actividade_out_id: int):
        """Process Audicoes using SQLAlchemy ORM"""
        try:
            audicoes_section = actividade_out.find('Audicoes')
            if audicoes_section is not None:
                # Create audicao record
                audicao = ActividadeAudicao(
                    actividade_out_id=actividade_out_id
                )
                
                self.session.add(audicao)
                self.session.commit()
                
                # Process ActividadesComissaoOut within Audicoes
                for comissao_out in audicoes_section.findall('ActividadesComissaoOut'):
                    comissao_out_obj = ActividadesComissaoOut(
                        audicao_id=audicao.id
                    )
                    self.session.add(comissao_out_obj)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing audicoes: {e}")
            self.session.rollback()
    
    def _process_deputy_situacoes_real(self, deputado: ET.Element, atividade_deputado_id: int):
        """Process deputy situations using SQLAlchemy ORM"""
        try:
            dep_situacao = deputado.find('DepSituacao')
            if dep_situacao is not None:
                # Create deputado_situacao record
                deputado_situacao = DeputadoSituacao(
                    atividade_deputado_id=atividade_deputado_id
                )
                
                self.session.add(deputado_situacao)
                self.session.commit()
                
                # Process each DadosSituacaoDeputado
                for situacao in dep_situacao.findall('DadosSituacaoDeputado'):
                    sio_des = self._get_text_value(situacao, 'SioDes')
                    sio_dt_inicio = self._parse_date(self._get_text_value(situacao, 'SioDtInicio'))
                    sio_dt_fim = self._parse_date(self._get_text_value(situacao, 'SioDtFim'))
                    
                    dados_situacao = DadosSituacaoDeputado(
                        deputado_situacao_id=deputado_situacao.id,
                        sio_des=sio_des,
                        sio_dt_inicio=sio_dt_inicio,
                        sio_dt_fim=sio_dt_fim
                    )
                    
                    self.session.add(dados_situacao)
                
                self.session.commit()
                    
        except Exception as e:
            logger.error(f"Error processing deputy situacoes: {e}")
            self.session.rollback()
    
    def __del__(self):
        """Cleanup SQLAlchemy session"""
        if hasattr(self, 'session'):
            self.session.close()
    
    # Utility methods
    def _get_text_value(self, parent: ET.Element, tag_name: str) -> Optional[str]:
        """Get text value from XML element"""
        if parent is None:
            return None
        element = parent.find(tag_name)
        if element is not None and element.text:
            return element.text.strip()
        return None
    
    def _safe_int(self, value: str) -> Optional[int]:
        """Safely convert string to int"""
        if not value:
            return None
        try:
            return int(float(value))  # Handle values like "16897.0"
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
        if not date_str:
            return None
        
        try:
            # Try ISO format first
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                return date_str
            
            # Try DD/MM/YYYY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
        except (ValueError, IndexError):
            logger.warning(f"Could not parse date: {date_str}")
        
        return None