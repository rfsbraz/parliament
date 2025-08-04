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

from .enhanced_base_mapper import SchemaMapper, SchemaError

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    DelegacaoPermanente, DelegacaoPermanenteMembro, DelegacaoPermanenteComissao, 
    DelegacaoPermanenteComissaoMembro, Deputado, Legislatura
)

logger = logging.getLogger(__name__)


class DelegacaoPermanenteMapper(SchemaMapper):
    """Schema mapper for parliamentary permanent delegation files"""
    
    def __init__(self, session):
        # Accept SQLAlchemy session directly (passed by unified importer)
        super().__init__(session)
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # Root elements
            'ArrayOfDelegacaoPermanenteOut',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut',
            
            # Main delegation fields
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Id',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Nome',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Legislatura',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Sessao',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.DataEleicao',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Composicao',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Comissoes',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Reunioes',
            
            # Members (IX Legislature composition structure)
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Composicao.DelegacaoPermanenteMembroOut',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Composicao.DelegacaoPermanenteMembroOut.Id',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Composicao.DelegacaoPermanenteMembroOut.Nome',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Composicao.DelegacaoPermanenteMembroOut.Gp',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Composicao.DelegacaoPermanenteMembroOut.Cargo',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Composicao.DelegacaoPermanenteMembroOut.DataInicio',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Composicao.DelegacaoPermanenteMembroOut.DataFim',
            
            # XIII Legislature commission structure with XML namespace
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Comissoes.Comissao',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Comissoes.Comissao.{http://parlamento.pt/AP/svc/}nome',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Comissoes.Comissao.{http://parlamento.pt/AP/svc/}composicao',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Comissoes.Comissao.{http://parlamento.pt/AP/svc/}subcomissoes',
            
            # XI Legislature deeper nested commission member structure with XML namespace
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Comissoes.Comissao.{http://parlamento.pt/AP/svc/}composicao.{http://parlamento.pt/AP/svc/}Membro',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Comissoes.Comissao.{http://parlamento.pt/AP/svc/}composicao.{http://parlamento.pt/AP/svc/}Membro.{http://parlamento.pt/AP/svc/}nome',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Comissoes.Comissao.{http://parlamento.pt/AP/svc/}composicao.{http://parlamento.pt/AP/svc/}Membro.{http://parlamento.pt/AP/svc/}gp',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Comissoes.Comissao.{http://parlamento.pt/AP/svc/}composicao.{http://parlamento.pt/AP/svc/}Membro.{http://parlamento.pt/AP/svc/}cargo',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Comissoes.Comissao.{http://parlamento.pt/AP/svc/}composicao.{http://parlamento.pt/AP/svc/}Membro.{http://parlamento.pt/AP/svc/}dataInicio',
            'ArrayOfDelegacaoPermanenteOut.DelegacaoPermanenteOut.Comissoes.Comissao.{http://parlamento.pt/AP/svc/}composicao.{http://parlamento.pt/AP/svc/}Membro.{http://parlamento.pt/AP/svc/}dataFim'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map parliamentary permanent delegations to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        try:
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Extract legislatura from filename or XML
            legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
            
            # Process permanent delegations
            for delegation in xml_root.findall('.//DelegacaoPermanenteOut'):
                try:
                    success = self._process_delegation(delegation, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Permanent delegation processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
                    self.session.rollback()
                    if strict_mode:
                        logger.error("STRICT MODE: Exiting due to permanent delegation processing error")
                        raise SchemaError(f"Permanent delegation processing failed in strict mode: {e}")
                    continue
            
            # Commit all changes
            self.session.commit()
            return results
            
        except Exception as e:
            error_msg = f"Critical error processing permanent delegations: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            self.session.rollback()
            raise SchemaError(f"Critical permanent delegation processing error: {e}")
    
    
    def _process_delegation(self, delegation: ET.Element, legislatura: Legislatura) -> bool:
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
            data_eleicao = self._parse_date(data_eleicao_str)
            
            # Check if delegation already exists
            existing = None
            if id_externo:
                existing = self.session.query(DelegacaoPermanente).filter_by(
                    delegacao_id=id_externo
                ).first()
            
            if existing:
                # Update existing record
                existing.nome = nome
                existing.sessao = sessao
                existing.data_eleicao = data_eleicao
                existing.legislatura_id = legislatura.id
            else:
                # Create new delegation record
                delegacao = DelegacaoPermanente(
                    delegacao_id=id_externo,
                    nome=nome,
                    sessao=sessao,
                    data_eleicao=data_eleicao,
                    legislatura_id=legislatura.id
                )
                self.session.add(delegacao)
                self.session.flush()  # Get the ID
                existing = delegacao
            
            # Process members
            composicao = delegation.find('Composicao')
            if composicao is not None:
                for member in composicao.findall('DelegacaoPermanenteMembroOut'):
                    self._process_delegation_member(member, existing)
            
            # Process commissions (XIII Legislature)
            comissoes = delegation.find('Comissoes')
            if comissoes is not None:
                for comissao in comissoes.findall('Comissao'):
                    self._process_delegation_commission(comissao, existing)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing permanent delegation: {e}")
            return False
    
    def _process_delegation_member(self, member: ET.Element, delegacao: DelegacaoPermanente) -> bool:
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
            
            # Check if member record already exists
            existing = None
            if member_id:
                existing = self.session.query(DelegacaoPermanenteMembro).filter_by(
                    membro_id=member_id,
                    delegacao_id=delegacao.id
                ).first()
            
            if existing:
                # Update existing member
                existing.nome = nome
                existing.gp = gp
                existing.cargo = cargo
                existing.data_inicio = data_inicio
                existing.data_fim = data_fim
            else:
                # Create new member record
                membro = DelegacaoPermanenteMembro(
                    delegacao_id=delegacao.id,
                    membro_id=member_id,
                    nome=nome,
                    gp=gp,
                    cargo=cargo,
                    data_inicio=data_inicio,
                    data_fim=data_fim
                )
                self.session.add(membro)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing delegation member: {e}")
            return False
    
    def _process_delegation_commission(self, comissao: ET.Element, delegacao: DelegacaoPermanente) -> bool:
        """Process delegation commission (XIII Legislature with XML namespace)"""
        try:
            # Extract commission fields with namespace using base class methods
            nome = self._get_namespaced_text(comissao, 'ap', 'nome')
            composicao = self._get_namespaced_text(comissao, 'ap', 'composicao')
            subcomissoes = self._get_namespaced_text(comissao, 'ap', 'subcomissoes')
            
            # Create commission record if there's meaningful data
            comissao_record = None
            if any([nome, composicao, subcomissoes]):
                comissao_record = DelegacaoPermanenteComissao(
                    delegacao_id=delegacao.id,
                    nome=nome,
                    composicao=composicao,
                    subcomissoes=subcomissoes
                )
                self.session.add(comissao_record)
                self.session.flush()  # Get the ID for nested members
            
            # Process nested commission members (XI Legislature)
            composicao_elem = self._get_namespaced_element(comissao, 'ap', 'composicao')
            if composicao_elem is not None and comissao_record is not None:
                for membro in composicao_elem.findall('.//{http://parlamento.pt/AP/svc/}Membro'):
                    self._process_commission_member(membro, comissao_record)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing delegation commission: {e}")
            return False
    
    def _process_commission_member(self, membro: ET.Element, comissao: DelegacaoPermanenteComissao) -> bool:
        """Process commission member (XI Legislature nested structure with XML namespace)"""
        try:
            # Extract member fields with namespace using base class methods
            nome = self._get_namespaced_text(membro, 'ap', 'nome')
            gp = self._get_namespaced_text(membro, 'ap', 'gp')
            cargo = self._get_namespaced_text(membro, 'ap', 'cargo')
            data_inicio_str = self._get_namespaced_text(membro, 'ap', 'dataInicio')
            data_fim_str = self._get_namespaced_text(membro, 'ap', 'dataFim')
            
            # Parse dates
            data_inicio = self._parse_date(data_inicio_str) if data_inicio_str else None
            data_fim = self._parse_date(data_fim_str) if data_fim_str else None
            
            # Create member record if there's meaningful data
            if any([nome, gp, cargo, data_inicio, data_fim]):
                membro_record = DelegacaoPermanenteComissaoMembro(
                    comissao_id=comissao.id,
                    nome=nome,
                    gp=gp,
                    cargo=cargo,
                    data_inicio=data_inicio,
                    data_fim=data_fim
                )
                self.session.add(membro_record)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing commission member: {e}")
            return False
    
    # Utility methods now inherited from base class