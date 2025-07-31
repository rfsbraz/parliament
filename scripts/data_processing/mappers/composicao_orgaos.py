"""
Parliamentary Organ Composition Mapper - SQLAlchemy ORM Version
==============================================================

Schema mapper for parliamentary organ composition files (OrgaoComposicao*.xml).
Handles composition of various parliamentary organs including plenary, committees,
and other parliamentary bodies with their member assignments.
Uses comprehensive OrganizacaoAR SQLAlchemy models for zero data loss.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging

from .base_mapper import SchemaMapper, SchemaError

# Import our comprehensive OrganizacaoAR models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    ParliamentaryOrganization, AdministrativeCouncil, LeaderConference,
    CommissionPresidentConference, Commission, ARBoard, WorkGroup,
    PermanentCommittee, SubCommittee, Plenary, PlenaryComposition,
    AdministrativeCouncilHistoricalComposition, LeaderConferenceHistoricalComposition,
    CommissionHistoricalComposition, ARBoardHistoricalComposition,
    WorkGroupHistoricalComposition, PermanentCommitteeHistoricalComposition,
    SubCommitteeHistoricalComposition, OrganMeeting, MeetingAttendance, Deputado, Legislatura
)

logger = logging.getLogger(__name__)


class ComposicaoOrgaosMapper(SchemaMapper):
    """Schema mapper for parliamentary organ composition files"""
    
    def __init__(self, session):
        super().__init__(session)
        # Use the passed SQLAlchemy session
        self.session = session
    
    def get_expected_fields(self) -> Set[str]:
        return {
            'OrganizacaoAR', 'ConselhoAdministracao', 'ConferenciaLideres', 
            'ConferenciaPresidentesComissoes', 'ComissaoPermanente', 'MesaAR',
            'Comissoes', 'SubComissoes', 'GruposTrabalho', 'Plenario',
            # Organ details
            'DetalheOrgao', 'idOrgao', 'siglaOrgao', 'nomeSigla', 'numeroOrgao', 
            'siglaLegislatura', 'Composicao',
            # Deputy information in plenary
            'DadosDeputadoOrgaoPlenario', 'DepId', 'DepCadId', 'DepNomeParlamentar',
            'DepGP', 'DepCPId', 'DepCPDes', 'LegDes', 'DepSituacao', 'DepNomeCompleto',
            # Parliamentary group info
            'pt_ar_wsgode_objectos_DadosSituacaoGP', 'gpId', 'gpSigla', 'gpDtInicio', 'gpDtFim',
            # Deputy situation info
            'pt_ar_wsgode_objectos_DadosSituacaoDeputado', 'sioDes', 'sioDtInicio', 'sioDtFim',
            # Committee member info
            'DadosDeputadoOrgaoComissao', 'CarId', 'CarDes', 'DtInicio', 'DtFim',
            # Subcommittee and working group info
            'DadosDeputadoOrgaoSubComissao', 'DadosDeputadoOrgaoGrupoTrabalho',
            
            # Constituinte legislature full path mappings
            'OrganizacaoAR.MesaAR',
            'OrganizacaoAR.ConferenciaLideres',
            'OrganizacaoAR.GruposTrabalho',
            'OrganizacaoAR.Comissoes',
            'OrganizacaoAR.SubComissoes',
            'OrganizacaoAR.ConferenciaPresidentesComissoes',
            'OrganizacaoAR.ConselhoAdministracao',
            'OrganizacaoAR.ComissaoPermanente',
            'OrganizacaoAR.Plenario',
            
            # MesaAR detailed mappings
            'OrganizacaoAR.MesaAR.DetalheOrgao',
            'OrganizacaoAR.MesaAR.DetalheOrgao.numeroOrgao',
            'OrganizacaoAR.MesaAR.DetalheOrgao.idOrgao',
            'OrganizacaoAR.MesaAR.DetalheOrgao.siglaLegislatura',
            'OrganizacaoAR.MesaAR.DetalheOrgao.siglaOrgao',
            'OrganizacaoAR.MesaAR.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.MesaAR.Composicao',
            
            # Plenario detailed mappings
            'OrganizacaoAR.Plenario.DetalheOrgao',
            'OrganizacaoAR.Plenario.DetalheOrgao.numeroOrgao',
            'OrganizacaoAR.Plenario.DetalheOrgao.idOrgao',
            'OrganizacaoAR.Plenario.DetalheOrgao.siglaOrgao',
            'OrganizacaoAR.Plenario.DetalheOrgao.siglaLegislatura',
            'OrganizacaoAR.Plenario.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.Plenario.Composicao',
            'OrganizacaoAR.Plenario.Reunioes',
            
            # Deputy data in plenary - full paths
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepId',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepCadId',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepCPId',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepNomeParlamentar',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepNomeCompleto',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepCPDes',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.LegDes',
            
            # Parliamentary group data - full paths
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepGP',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpId',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpSigla',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtInicio',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepGP.pt_ar_wsgode_objectos_DadosSituacaoGP.gpDtFim',
            
            # Deputy situation data - full paths
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepSituacao',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDes',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDtInicio',
            'OrganizacaoAR.Plenario.Composicao.DadosDeputadoOrgaoPlenario.DepSituacao.pt_ar_wsgode_objectos_DadosSituacaoDeputado.sioDtFim',
            
            # III Legislature additional mappings - extended structure
            # ComissaoPermanente detailed mappings
            'OrganizacaoAR.ComissaoPermanente.DetalheOrgao.siglaLegislatura',
            'OrganizacaoAR.ComissaoPermanente.DetalheOrgao.numeroOrgao',
            
            # Comissoes extended structure
            'OrganizacaoAR.Comissoes.OrgaoBase',
            'OrganizacaoAR.Comissoes.OrgaoBase.DetalheOrgao',
            'OrganizacaoAR.Comissoes.OrgaoBase.DetalheOrgao.numeroOrgao',
            'OrganizacaoAR.Comissoes.OrgaoBase.DetalheOrgao.idOrgao',
            'OrganizacaoAR.Comissoes.OrgaoBase.DetalheOrgao.siglaOrgao',
            'OrganizacaoAR.Comissoes.OrgaoBase.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.Comissoes.OrgaoBase.DetalheOrgao.siglaLegislatura',
            'OrganizacaoAR.Comissoes.OrgaoBase.Composicao',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes',
            
            # Meeting data structures
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTarId',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTirDes',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuLocal',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuData',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuHora',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuTipo',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuEstado',
            
            # Plenary meeting structures - III Legislature
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.selNumero',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuData',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuHora',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuLocal',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuTipo',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuEstado',
            
            # Presencas (attendance) structures
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.tipoReuniao',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.pt_ar_wsgode_objectos_DadosPresenca',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.pt_ar_wsgode_objectos_DadosPresenca.depId',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.pt_ar_wsgode_objectos_DadosPresenca.depCadId',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.pt_ar_wsgode_objectos_DadosPresenca.depNomeParlamentar',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.pt_ar_wsgode_objectos_DadosPresenca.presTipo',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.pt_ar_wsgode_objectos_DadosPresenca.presJustificacao',
            
            # Additional missing III Legislature fields
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Presencas.dtReuniao',
            'OrganizacaoAR.ComissaoPermanente.DetalheOrgao.nomeSigla',
            'OrganizacaoAR.ComissaoPermanente.DetalheOrgao.idOrgao',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuDataHora',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuNumero',
            'OrganizacaoAR.Comissoes.OrgaoBase.Reunioes.pt_ar_wsgode_objectos_DadosReuniao.reuFinalPlenario',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuTirDes',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.legDes',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuDataHora',
            'OrganizacaoAR.Plenario.Reunioes.ReuniaoPlenario.Reuniao.reuId'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map parliamentary organ composition to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        try:
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Extract legislatura from filename or XML
            legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
        
            # Process MesaAR (AR Board)
            mesa_ar = xml_root.find('.//MesaAR')
            if mesa_ar is not None:
                try:
                    success = self._process_mesa_ar(mesa_ar, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"MesaAR processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
            
            # Process ConselhoAdministracao (Administrative Council)
            conselho_admin = xml_root.find('.//ConselhoAdministracao')
            if conselho_admin is not None:
                try:
                    success = self._process_conselho_administracao(conselho_admin, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"ConselhoAdministracao processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
            
            # Process ComissaoPermanente (Permanent Committee)
            comissao_permanente = xml_root.find('.//ComissaoPermanente')
            if comissao_permanente is not None:
                try:
                    success = self._process_comissao_permanente(comissao_permanente, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"ComissaoPermanente processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
            
            # Process ConferenciaLideres (Leader Conference)
            conferencia_lideres = xml_root.find('.//ConferenciaLideres')
            if conferencia_lideres is not None:
                try:
                    success = self._process_conferencia_lideres(conferencia_lideres, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"ConferenciaLideres processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1

            # Process plenary composition
            plenario = xml_root.find('.//Plenario')
            if plenario is not None:
                try:
                    success = self._process_plenario(plenario, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Plenario processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
        
            # Process committees
            comissoes = xml_root.find('.//Comissoes')
            if comissoes is not None:
                # Handle both direct committee structure and OrgaoBase structure
                for comissao in comissoes:
                    try:
                        # Check if this is an OrgaoBase structure (III Legislature)
                        if comissao.tag == 'OrgaoBase':
                            success = self._process_orgao_base(comissao, legislatura)
                        else:
                            success = self._process_comissao(comissao, legislatura)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                    except Exception as e:
                        error_msg = f"Committee processing error: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
        
            # Process subcommittees
            subcomissoes = xml_root.find('.//SubComissoes')
            if subcomissoes is not None:
                for subcomissao in subcomissoes:
                    try:
                        success = self._process_subcomissao(subcomissao, legislatura)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                    except Exception as e:
                        error_msg = f"Subcommittee processing error: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
        
            # Process working groups
            grupos_trabalho = xml_root.find('.//GruposTrabalho')
            if grupos_trabalho is not None:
                for grupo in grupos_trabalho:
                    try:
                        success = self._process_grupo_trabalho(grupo, legislatura)
                        results['records_processed'] += 1
                        if success:
                            results['records_imported'] += 1
                    except Exception as e:
                        error_msg = f"Working group processing error: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        results['records_processed'] += 1
            
            # Commit all changes
            self.session.commit()
            return results
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in validate_and_map: {e}")
            results['errors'].append(str(e))
            return results
    
    def _extract_legislatura(self, file_path: str, xml_root: ET.Element) -> str:
        """Extract legislatura from filename or XML content"""
        # Try filename first
        filename = os.path.basename(file_path)
        leg_match = re.search(r'(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)', filename)
        if leg_match:
            return leg_match.group(1)
        
        # Try XML content - look for siglaLegislatura
        sigla_leg = xml_root.find('.//siglaLegislatura')
        if sigla_leg is not None and sigla_leg.text:
            leg_text = sigla_leg.text.strip()
            # Convert abbreviations
            if leg_text.lower() == 'cons':
                return 'CONSTITUINTE'
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
    
    def _process_plenario(self, plenario: ET.Element, legislatura: Legislatura) -> bool:
        """Process plenary composition"""
        try:
            # Get or create plenary as a committee
            detalhe_orgao = plenario.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao') or 'PL'
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla') or 'Plenário'
            
            if not id_orgao:
                return False
            
            # Create or get plenary record
            plenary = self._get_or_create_plenary(
                int(float(id_orgao)), sigla_orgao, nome_sigla, legislatura
            )
            
            # Process members
            composicao = plenario.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoPlenario'):
                    self._process_deputy_plenary_membership(deputado_data, plenary)
            
            # Process meetings (Reunioes) - handle both simple and ReuniaoPlenario structures
            reunioes = plenario.find('Reunioes')
            if reunioes is not None:
                # Handle simple Reuniao structure
                for reuniao in reunioes.findall('Reuniao'):
                    self._process_organ_meeting(reuniao, plenary=plenary)
                
                # Handle ReuniaoPlenario structure (III Legislature)
                for reuniao_plenario in reunioes.findall('ReuniaoPlenario'):
                    self._process_reuniao_plenario(reuniao_plenario, plenary)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing plenary: {e}")
            return False
    
    def _process_comissao(self, comissao: ET.Element, legislatura: Legislatura) -> bool:
        """Process committee composition"""
        try:
            detalhe_orgao = comissao.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao')
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla')
            
            if not id_orgao or not sigla_orgao:
                return False
            
            # Create or get committee record
            committee = self._get_or_create_committee(
                int(float(id_orgao)), sigla_orgao, nome_sigla or sigla_orgao, legislatura
            )
            
            # Process members
            composicao = comissao.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoComissao'):
                    self._process_deputy_committee_membership(deputado_data, committee)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing committee: {e}")
            return False
    
    def _process_subcomissao(self, subcomissao: ET.Element, legislatura: Legislatura) -> bool:
        """Process subcommittee composition"""
        try:
            detalhe_orgao = subcomissao.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao')
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla')
            
            if not id_orgao or not sigla_orgao:
                return False
            
            # Create or get subcommittee record
            subcommittee = self._get_or_create_subcommittee(
                int(float(id_orgao)), sigla_orgao, nome_sigla or sigla_orgao, legislatura
            )
            
            # Process members
            composicao = subcomissao.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoSubComissao'):
                    self._process_deputy_subcommittee_membership(deputado_data, subcommittee)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing subcommittee: {e}")
            return False
    
    def _process_grupo_trabalho(self, grupo: ET.Element, legislatura: Legislatura) -> bool:
        """Process working group composition"""
        try:
            detalhe_orgao = grupo.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao')
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla')
            
            if not id_orgao or not sigla_orgao:
                return False
            
            # Create or get working group record
            work_group = self._get_or_create_work_group(
                int(float(id_orgao)), sigla_orgao, nome_sigla or sigla_orgao, legislatura
            )
            
            # Process members
            composicao = grupo.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoGrupoTrabalho'):
                    self._process_deputy_work_group_membership(deputado_data, work_group)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing working group: {e}")
            return False
    
    def _process_deputy_plenary_membership(self, deputado_data: ET.Element, plenary: Plenary) -> bool:
        """Process deputy membership in plenary"""
        try:
            dep_cad_id = self._get_text_value(deputado_data, 'DepCadId')
            dep_nome = self._get_text_value(deputado_data, 'DepNomeParlamentar')
            dep_nome_completo = self._get_text_value(deputado_data, 'DepNomeCompleto')
            
            if not dep_cad_id or not dep_nome:
                return False
            
            # Get dates from situation data
            situacao = deputado_data.find('DepSituacao')
            data_inicio = None
            data_fim = None
            
            if situacao is not None:
                sit_data = situacao.find('pt_ar_wsgode_objectos_DadosSituacaoDeputado')
                if sit_data is not None:
                    data_inicio = self._parse_date(self._get_text_value(sit_data, 'sioDtInicio'))
                    data_fim = self._parse_date(self._get_text_value(sit_data, 'sioDtFim'))
            
            if not data_inicio:
                return False
            
            # Find or create deputy
            deputado = self._get_or_create_deputado(int(float(dep_cad_id)), dep_nome, dep_nome_completo)
            
            # Create plenary composition record
            plenary_composition = PlenaryComposition(
                plenary_id=plenary.id,
                deputado_id=deputado.id,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            
            self.session.add(plenary_composition)
            return True
            
        except Exception as e:
            logger.error(f"Error processing deputy plenary membership: {e}")
            self.session.rollback()
            return False
    
    def _process_deputy_committee_membership(self, deputado_data: ET.Element, committee: Commission) -> bool:
        """Process deputy membership in committee"""
        try:
            dep_cad_id = self._get_text_value(deputado_data, 'DepCadId')
            dep_nome = self._get_text_value(deputado_data, 'DepNomeParlamentar')
            dep_nome_completo = self._get_text_value(deputado_data, 'DepNomeCompleto')
            cargo_des = self._get_text_value(deputado_data, 'CarDes')
            
            if not dep_cad_id or not dep_nome:
                return False
            
            # Map cargo description to standard values
            cargo = self._map_cargo(cargo_des)
            
            # Get dates
            data_inicio = self._parse_date(self._get_text_value(deputado_data, 'DtInicio'))
            data_fim = self._parse_date(self._get_text_value(deputado_data, 'DtFim'))
            
            if not data_inicio:
                return False
            
            # Find or create deputy
            deputado = self._get_or_create_deputado(int(float(dep_cad_id)), dep_nome, dep_nome_completo)
            
            # Create commission historical composition record
            composition = CommissionHistoricalComposition(
                commission_id=committee.id,
                deputado_id=deputado.id,
                cargo=cargo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                titular=True
            )
            
            self.session.add(composition)
            return True
            
        except Exception as e:
            logger.error(f"Error processing deputy committee membership: {e}")
            self.session.rollback()
            return False
    
    def _process_deputy_subcommittee_membership(self, deputado_data: ET.Element, subcommittee: SubCommittee) -> bool:
        """Process deputy membership in subcommittee"""
        try:
            dep_cad_id = self._get_text_value(deputado_data, 'DepCadId')
            dep_nome = self._get_text_value(deputado_data, 'DepNomeParlamentar')
            dep_nome_completo = self._get_text_value(deputado_data, 'DepNomeCompleto')
            cargo_des = self._get_text_value(deputado_data, 'CarDes')
            
            if not dep_cad_id or not dep_nome:
                return False
            
            # Map cargo description to standard values
            cargo = self._map_cargo(cargo_des)
            
            # Get dates
            data_inicio = self._parse_date(self._get_text_value(deputado_data, 'DtInicio'))
            data_fim = self._parse_date(self._get_text_value(deputado_data, 'DtFim'))
            
            if not data_inicio:
                return False
            
            # Find or create deputy
            deputado = self._get_or_create_deputado(int(float(dep_cad_id)), dep_nome, dep_nome_completo)
            
            # Create subcommittee historical composition record
            composition = SubCommitteeHistoricalComposition(
                subcommittee_id=subcommittee.id,
                deputado_id=deputado.id,
                cargo=cargo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                titular=True
            )
            
            self.session.add(composition)
            return True
            
        except Exception as e:
            logger.error(f"Error processing deputy subcommittee membership: {e}")
            self.session.rollback()
            return False
    
    def _process_deputy_work_group_membership(self, deputado_data: ET.Element, work_group: WorkGroup) -> bool:
        """Process deputy membership in work group"""
        try:
            dep_cad_id = self._get_text_value(deputado_data, 'DepCadId')
            dep_nome = self._get_text_value(deputado_data, 'DepNomeParlamentar')
            dep_nome_completo = self._get_text_value(deputado_data, 'DepNomeCompleto')
            cargo_des = self._get_text_value(deputado_data, 'CarDes')
            
            if not dep_cad_id or not dep_nome:
                return False
            
            # Map cargo description to standard values
            cargo = self._map_cargo(cargo_des)
            
            # Get dates
            data_inicio = self._parse_date(self._get_text_value(deputado_data, 'DtInicio'))
            data_fim = self._parse_date(self._get_text_value(deputado_data, 'DtFim'))
            
            if not data_inicio:
                return False
            
            # Find or create deputy
            deputado = self._get_or_create_deputado(int(float(dep_cad_id)), dep_nome, dep_nome_completo)
            
            # Create work group historical composition record
            composition = WorkGroupHistoricalComposition(
                work_group_id=work_group.id,
                deputado_id=deputado.id,
                cargo=cargo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                titular=True
            )
            
            self.session.add(composition)
            return True
            
        except Exception as e:
            logger.error(f"Error processing deputy work group membership: {e}")
            self.session.rollback()
            return False
    
    def _get_or_create_plenary(self, id_externo: int, sigla: str, nome: str, legislatura: Legislatura) -> Plenary:
        """Get or create plenary record"""
        plenary = self.session.query(Plenary).filter_by(
            external_id=id_externo,
            legislatura_id=legislatura.id
        ).first()
        
        if plenary:
            return plenary
        
        # Create new plenary
        plenary = Plenary(
            external_id=id_externo,
            legislatura_id=legislatura.id,
            nome=nome,
            sigla=sigla,
            ativa=True
        )
        
        self.session.add(plenary)
        self.session.flush()  # Get the ID
        return plenary
        
    def _get_or_create_committee(self, id_externo: int, sigla: str, nome: str, legislatura: Legislatura) -> Commission:
        """Get or create committee record"""
        committee = self.session.query(Commission).filter_by(
            external_id=id_externo,
            legislatura_id=legislatura.id
        ).first()
        
        if committee:
            return committee
        
        # Create new committee
        committee = Commission(
            external_id=id_externo,
            legislatura_id=legislatura.id,
            nome=nome,
            sigla=sigla,
            ativa=True
        )
        
        self.session.add(committee)
        self.session.flush()  # Get the ID
        return committee
        
    def _get_or_create_subcommittee(self, id_externo: int, sigla: str, nome: str, legislatura: Legislatura) -> SubCommittee:
        """Get or create subcommittee record"""
        subcommittee = self.session.query(SubCommittee).filter_by(
            external_id=id_externo,
            legislatura_id=legislatura.id
        ).first()
        
        if subcommittee:
            return subcommittee
        
        # Create new subcommittee
        subcommittee = SubCommittee(
            external_id=id_externo,
            legislatura_id=legislatura.id,
            nome=nome,
            sigla=sigla,
            ativa=True
        )
        
        self.session.add(subcommittee)
        self.session.flush()  # Get the ID
        return subcommittee
        
    def _get_or_create_work_group(self, id_externo: int, sigla: str, nome: str, legislatura: Legislatura) -> WorkGroup:
        """Get or create work group record"""
        work_group = self.session.query(WorkGroup).filter_by(
            external_id=id_externo,
            legislatura_id=legislatura.id
        ).first()
        
        if work_group:
            return work_group
        
        # Create new work group
        work_group = WorkGroup(
            external_id=id_externo,
            legislatura_id=legislatura.id,
            nome=nome,
            sigla=sigla,
            ativa=True
        )
        
        self.session.add(work_group)
        self.session.flush()  # Get the ID
        return work_group
    
    def _get_or_create_deputado(self, dep_cad_id: int, nome: str, nome_completo: str = None) -> Deputado:
        """Get or create deputy record"""
        deputado = self.session.query(Deputado).filter_by(id_cadastro=dep_cad_id).first()
        
        if deputado:
            # Update name if we have more complete info
            if nome_completo and not deputado.nome_completo:
                deputado.nome_completo = nome_completo
            return deputado
        
        # Create basic deputy record (will be enriched by other mappers)
        deputado = Deputado(
            id_cadastro=dep_cad_id,
            nome=nome,
            nome_completo=nome_completo or nome,
            ativo=True
        )
        
        self.session.add(deputado)
        self.session.flush()  # Get the ID
        return deputado
    
    def _map_cargo(self, cargo_des: str) -> str:
        """Map cargo description to standard values"""
        if not cargo_des:
            return 'membro'
        
        cargo_lower = cargo_des.lower()
        if 'presidente' in cargo_lower:
            return 'presidente'
        elif 'vice' in cargo_lower:
            return 'vice_presidente'
        elif 'secretário' in cargo_lower or 'secretario' in cargo_lower:
            return 'secretario'
        else:
            return 'membro'
    
    def _get_text_value(self, parent: ET.Element, tag_name: str) -> Optional[str]:
        """Get text value from XML element"""
        element = parent.find(tag_name)
        if element is not None and element.text:
            return element.text.strip()
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
    
    def _process_mesa_ar(self, mesa_ar: ET.Element, legislatura: Legislatura) -> bool:
        """Process AR Board (Mesa da Assembleia da República)"""
        try:
            detalhe_orgao = mesa_ar.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao') or 'MAR'
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla') or 'Mesa da Assembleia da República'
            numero_orgao = self._get_text_value(detalhe_orgao, 'numeroOrgao')
            
            if not id_orgao:
                return False
            
            # Create or get AR Board record
            ar_board = self._get_or_create_ar_board(
                int(float(id_orgao)), sigla_orgao, nome_sigla, numero_orgao, legislatura
            )
            
            # Process members
            composicao = mesa_ar.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgao'):
                    self._process_deputy_ar_board_membership(deputado_data, ar_board)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Mesa AR: {e}")
            return False
    
    def _process_conselho_administracao(self, conselho: ET.Element, legislatura: Legislatura) -> bool:
        """Process Administrative Council"""
        try:
            detalhe_orgao = conselho.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao') or 'CA'
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla') or 'Conselho de Administração'
            numero_orgao = self._get_text_value(detalhe_orgao, 'numeroOrgao')
            
            if not id_orgao:
                return False
            
            # Create or get Administrative Council record
            admin_council = self._get_or_create_administrative_council(
                int(float(id_orgao)), sigla_orgao, nome_sigla, numero_orgao, legislatura
            )
            
            # Process members
            composicao = conselho.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgao'):
                    self._process_deputy_admin_council_membership(deputado_data, admin_council)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Administrative Council: {e}")
            return False
    
    def _process_comissao_permanente(self, comissao: ET.Element, legislatura: Legislatura) -> bool:
        """Process Permanent Committee"""
        try:
            detalhe_orgao = comissao.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao') or 'CP'
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla') or 'Comissão Permanente'
            numero_orgao = self._get_text_value(detalhe_orgao, 'numeroOrgao')
            
            if not id_orgao:
                return False
            
            # Create or get Permanent Committee record
            permanent_committee = self._get_or_create_permanent_committee(
                int(float(id_orgao)), sigla_orgao, nome_sigla, numero_orgao, legislatura
            )
            
            # Process members
            composicao = comissao.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgao'):
                    self._process_deputy_permanent_committee_membership(deputado_data, permanent_committee)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Permanent Committee: {e}")
            return False
    
    def _process_conferencia_lideres(self, conferencia: ET.Element, legislatura: Legislatura) -> bool:
        """Process Leader Conference"""
        try:
            detalhe_orgao = conferencia.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao') or 'CL'
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla') or 'Conferência de Líderes'
            numero_orgao = self._get_text_value(detalhe_orgao, 'numeroOrgao')
            
            if not id_orgao:
                return False
            
            # Create or get Leader Conference record
            leader_conference = self._get_or_create_leader_conference(
                int(float(id_orgao)), sigla_orgao, nome_sigla, numero_orgao, legislatura
            )
            
            # Process members
            composicao = conferencia.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgao'):
                    self._process_deputy_leader_conference_membership(deputado_data, leader_conference)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Leader Conference: {e}")
            return False
    
    def _process_organ_meeting(self, reuniao: ET.Element, **kwargs) -> bool:
        """Process organ meeting (Reuniao) - can be associated with different organ types"""
        try:
            # Extract meeting data
            reu_tar_sigla = self._get_text_value(reuniao, 'ReuTarSigla')
            reu_local = self._get_text_value(reuniao, 'ReuLocal')
            reu_data_str = self._get_text_value(reuniao, 'ReuData')
            reu_hora = self._get_text_value(reuniao, 'ReuHora')
            reu_tipo = self._get_text_value(reuniao, 'ReuTipo')
            reu_estado = self._get_text_value(reuniao, 'ReuEstado')
            
            # Parse date
            reu_data = None
            if reu_data_str:
                try:
                    # Assume format DD/MM/YYYY or similar
                    if '/' in reu_data_str:
                        day, month, year = reu_data_str.split('/')
                        from datetime import date
                        reu_data = date(int(year), int(month), int(day))
                    elif '-' in reu_data_str:
                        # ISO format YYYY-MM-DD
                        from datetime import date
                        year, month, day = reu_data_str.split('-')
                        reu_data = date(int(year), int(month), int(day))
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse meeting date: {reu_data_str}")
            
            # Create meeting record - determine which organ type this is for
            meeting = OrganMeeting(
                commission_id=kwargs.get('commission').id if kwargs.get('commission') else None,
                work_group_id=kwargs.get('work_group').id if kwargs.get('work_group') else None,
                permanent_committee_id=kwargs.get('permanent_committee').id if kwargs.get('permanent_committee') else None,
                sub_committee_id=kwargs.get('sub_committee').id if kwargs.get('sub_committee') else None,
                # Note: Plenary meetings would need a separate field in the model
                reu_tar_sigla=reu_tar_sigla,
                reu_local=reu_local,
                reu_data=reu_data,
                reu_hora=reu_hora,
                reu_tipo=reu_tipo,
                reu_estado=reu_estado
            )
            
            self.session.add(meeting)
            return True
            
        except Exception as e:
            logger.error(f"Error processing organ meeting: {e}")
            return False
    
    def _process_orgao_base(self, orgao_base: ET.Element, legislatura: Legislatura) -> bool:
        """Process OrgaoBase structure (III Legislature committees)"""
        try:
            detalhe_orgao = orgao_base.find('DetalheOrgao')
            if detalhe_orgao is None:
                return False
            
            id_orgao = self._get_text_value(detalhe_orgao, 'idOrgao')
            sigla_orgao = self._get_text_value(detalhe_orgao, 'siglaOrgao')
            nome_sigla = self._get_text_value(detalhe_orgao, 'nomeSigla')
            numero_orgao = self._get_text_value(detalhe_orgao, 'numeroOrgao')
            
            if not id_orgao or not sigla_orgao:
                return False
            
            # Create or get committee record
            committee = self._get_or_create_committee(
                int(float(id_orgao)), sigla_orgao, nome_sigla or sigla_orgao, legislatura
            )
            
            # Process members
            composicao = orgao_base.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoComissao'):
                    self._process_deputy_committee_membership(deputado_data, committee)
            
            # Process meetings with namespace structure
            reunioes = orgao_base.find('Reunioes')
            if reunioes is not None:
                for dados_reuniao in reunioes.findall('pt_ar_wsgode_objectos_DadosReuniao'):
                    self._process_organ_meeting_namespace(dados_reuniao, committee=committee)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing OrgaoBase: {e}")
            return False
    
    def _process_reuniao_plenario(self, reuniao_plenario: ET.Element, plenary) -> bool:
        """Process ReuniaoPlenario structure (III Legislature plenary meetings)"""
        try:
            # Process the main meeting data
            reuniao = reuniao_plenario.find('Reuniao')
            if reuniao is not None:
                # Extract meeting information
                sel_numero = self._get_text_value(reuniao, 'selNumero')
                reu_data_str = self._get_text_value(reuniao, 'reuData')
                reu_hora = self._get_text_value(reuniao, 'reuHora')
                reu_local = self._get_text_value(reuniao, 'reuLocal')
                reu_tipo = self._get_text_value(reuniao, 'reuTipo')
                reu_estado = self._get_text_value(reuniao, 'reuEstado')
                
                # Parse date
                reu_data = None
                if reu_data_str:
                    try:
                        if '/' in reu_data_str:
                            day, month, year = reu_data_str.split('/')
                            from datetime import date
                            reu_data = date(int(year), int(month), int(day))
                        elif '-' in reu_data_str:
                            from datetime import date
                            year, month, day = reu_data_str.split('-')
                            reu_data = date(int(year), int(month), int(day))
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse plenary meeting date: {reu_data_str}")
                
                # Extract additional III Legislature fields
                reu_id = self._get_int_value(reuniao, 'reuId')
                reu_data_hora = self._get_text_value(reuniao, 'reuDataHora')
                reu_tir_des = self._get_text_value(reuniao, 'reuTirDes')
                leg_des = self._get_text_value(reuniao, 'legDes')
                
                # Create meeting record with all available fields
                meeting = OrganMeeting(
                    # Basic fields
                    reu_tar_sigla=sel_numero,  # Use selNumero as identifier
                    reu_local=reu_local,
                    reu_data=reu_data,
                    reu_hora=reu_hora,
                    reu_tipo=reu_tipo,
                    reu_estado=reu_estado,
                    
                    # Extended III Legislature fields
                    reu_id=reu_id,
                    reu_data_hora=reu_data_hora,
                    reu_tir_des=reu_tir_des,
                    leg_des=leg_des,
                    sel_numero=sel_numero
                )
                
                self.session.add(meeting)
                self.session.flush()
                
                # Process attendance data (Presencas)
                presencas = reuniao_plenario.find('Presencas')
                if presencas is not None:
                    self._process_meeting_attendance(presencas, meeting)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing ReuniaoPlenario: {e}")
            return False
    
    def _process_organ_meeting_namespace(self, dados_reuniao: ET.Element, **kwargs) -> bool:
        """Process meeting data with pt_ar_wsgode_objectos namespace structure"""
        try:
            # Extract meeting data from namespace structure
            reu_tar_id = self._get_text_value(dados_reuniao, 'reuTarId')
            reu_tir_des = self._get_text_value(dados_reuniao, 'reuTirDes')
            reu_local = self._get_text_value(dados_reuniao, 'reuLocal')
            reu_data_str = self._get_text_value(dados_reuniao, 'reuData')
            reu_hora = self._get_text_value(dados_reuniao, 'reuHora')
            reu_tipo = self._get_text_value(dados_reuniao, 'reuTipo')
            reu_estado = self._get_text_value(dados_reuniao, 'reuEstado')
            
            # Parse date
            reu_data = None
            if reu_data_str:
                try:
                    if '/' in reu_data_str:
                        day, month, year = reu_data_str.split('/')
                        from datetime import date
                        reu_data = date(int(year), int(month), int(day))
                    elif '-' in reu_data_str:
                        from datetime import date
                        year, month, day = reu_data_str.split('-')
                        reu_data = date(int(year), int(month), int(day))
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse meeting date: {reu_data_str}")
            
            # Extract additional III Legislature namespace fields
            reu_numero = self._get_int_value(dados_reuniao, 'reuNumero')
            reu_data_hora = self._get_text_value(dados_reuniao, 'reuDataHora')
            reu_final_plenario = self._get_boolean_value(dados_reuniao, 'reuFinalPlenario')
            
            # Create meeting record with all available fields
            meeting = OrganMeeting(
                # Organ associations
                commission_id=kwargs.get('committee').id if kwargs.get('committee') else None,
                work_group_id=kwargs.get('work_group').id if kwargs.get('work_group') else None,
                permanent_committee_id=kwargs.get('permanent_committee').id if kwargs.get('permanent_committee') else None,
                sub_committee_id=kwargs.get('sub_committee').id if kwargs.get('sub_committee') else None,
                
                # Basic fields
                reu_tar_sigla=reu_tar_id,  # Use tar_id as identifier
                reu_local=reu_local,
                reu_data=reu_data,
                reu_hora=reu_hora,
                reu_tipo=reu_tipo,
                reu_estado=reu_estado,
                
                # Extended III Legislature fields
                reu_numero=reu_numero,
                reu_data_hora=reu_data_hora,
                reu_final_plenario=reu_final_plenario,
                reu_tir_des=reu_tir_des
            )
            
            self.session.add(meeting)
            return True
            
        except Exception as e:
            logger.error(f"Error processing namespace meeting data: {e}")
            return False
    
    def _process_meeting_attendance(self, presencas: ET.Element, meeting: OrganMeeting) -> bool:
        """Process meeting attendance data (Presencas) - now stores in MeetingAttendance model"""
        try:
            tipo_reuniao = self._get_text_value(presencas, 'tipoReuniao')
            dt_reuniao_str = self._get_text_value(presencas, 'dtReuniao')
            
            # Parse meeting date for attendance
            dt_reuniao = None
            if dt_reuniao_str:
                try:
                    if '/' in dt_reuniao_str:
                        day, month, year = dt_reuniao_str.split('/')
                        from datetime import date
                        dt_reuniao = date(int(year), int(month), int(day))
                    elif '-' in dt_reuniao_str:
                        from datetime import date
                        year, month, day = dt_reuniao_str.split('-')
                        dt_reuniao = date(int(year), int(month), int(day))
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse attendance date: {dt_reuniao_str}")
            
            attendance_count = 0
            for dados_presenca in presencas.findall('pt_ar_wsgode_objectos_DadosPresenca'):
                dep_id = self._get_int_value(dados_presenca, 'depId')
                dep_cad_id = self._get_int_value(dados_presenca, 'depCadId')
                dep_nome = self._get_text_value(dados_presenca, 'depNomeParlamentar')
                pres_tipo = self._get_text_value(dados_presenca, 'presTipo')
                pres_justificacao = self._get_text_value(dados_presenca, 'presJustificacao')
                
                # Create attendance record
                attendance = MeetingAttendance(
                    meeting_id=meeting.id,
                    dep_id=dep_id,
                    dep_cad_id=dep_cad_id,
                    dep_nome_parlamentar=dep_nome,
                    pres_tipo=pres_tipo,
                    pres_justificacao=pres_justificacao,
                    dt_reuniao=dt_reuniao,
                    tipo_reuniao=tipo_reuniao
                )
                
                self.session.add(attendance)
                attendance_count += 1
            
            logger.info(f"Stored {attendance_count} attendance records for meeting {meeting.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing meeting attendance: {e}")
            return False
    
    def _get_or_create_ar_board(self, id_orgao: int, sigla: str, nome: str, numero: str, legislatura: Legislatura):
        """Get or create AR Board record"""
        # First get or create parliamentary organization
        organization = self._get_or_create_parliamentary_organization(legislatura)
        
        ar_board = self.session.query(ARBoard).filter_by(
            id_orgao=id_orgao,
            organization_id=organization.id
        ).first()
        
        if ar_board:
            return ar_board
        
        ar_board = ARBoard(
            organization_id=organization.id,
            id_orgao=id_orgao,
            sigla_orgao=sigla,
            nome_sigla=nome,
            numero_orgao=int(numero) if numero and numero.isdigit() else None,
            sigla_legislatura=legislatura.numero
        )
        
        self.session.add(ar_board)
        self.session.flush()
        return ar_board
    
    def _get_or_create_administrative_council(self, id_orgao: int, sigla: str, nome: str, numero: str, legislatura: Legislatura):
        """Get or create Administrative Council record"""
        # First get or create parliamentary organization
        organization = self._get_or_create_parliamentary_organization(legislatura)
        
        admin_council = self.session.query(AdministrativeCouncil).filter_by(
            id_orgao=id_orgao,
            organization_id=organization.id
        ).first()
        
        if admin_council:
            return admin_council
        
        admin_council = AdministrativeCouncil(
            organization_id=organization.id,
            id_orgao=id_orgao,
            sigla_orgao=sigla,
            nome_sigla=nome,
            numero_orgao=int(numero) if numero and numero.isdigit() else None,
            sigla_legislatura=legislatura.numero
        )
        
        self.session.add(admin_council)
        self.session.flush()
        return admin_council
    
    def _get_or_create_permanent_committee(self, id_orgao: int, sigla: str, nome: str, numero: str, legislatura: Legislatura):
        """Get or create Permanent Committee record"""
        # First get or create parliamentary organization
        organization = self._get_or_create_parliamentary_organization(legislatura)
        
        permanent_committee = self.session.query(PermanentCommittee).filter_by(
            id_orgao=id_orgao,
            organization_id=organization.id
        ).first()
        
        if permanent_committee:
            return permanent_committee
        
        permanent_committee = PermanentCommittee(
            organization_id=organization.id,
            id_orgao=id_orgao,
            sigla_orgao=sigla,
            nome_sigla=nome,
            numero_orgao=int(numero) if numero and numero.isdigit() else None,
            sigla_legislatura=legislatura.numero
        )
        
        self.session.add(permanent_committee)
        self.session.flush()
        return permanent_committee
    
    def _get_or_create_leader_conference(self, id_orgao: int, sigla: str, nome: str, numero: str, legislatura: Legislatura):
        """Get or create Leader Conference record"""
        # First get or create parliamentary organization
        organization = self._get_or_create_parliamentary_organization(legislatura)
        
        leader_conference = self.session.query(LeaderConference).filter_by(
            id_orgao=id_orgao,
            organization_id=organization.id
        ).first()
        
        if leader_conference:
            return leader_conference
        
        leader_conference = LeaderConference(
            organization_id=organization.id,
            id_orgao=id_orgao,
            sigla_orgao=sigla,
            nome_sigla=nome,
            numero_orgao=int(numero) if numero and numero.isdigit() else None,
            sigla_legislatura=legislatura.numero
        )
        
        self.session.add(leader_conference)
        self.session.flush()
        return leader_conference
    
    def _process_deputy_ar_board_membership(self, deputado_data: ET.Element, ar_board) -> bool:
        """Process deputy membership in AR Board"""
        try:
            # Create historical composition record
            composition = ARBoardHistoricalComposition(
                board_id=ar_board.id,
                leg_des=self._get_text_value(deputado_data, 'LegDes'),
                dep_id=self._get_int_value(deputado_data, 'DepId'),
                dep_cad_id=self._get_int_value(deputado_data, 'DepCadId'),
                dep_nome_parlamentar=self._get_text_value(deputado_data, 'DepNomeParlamentar'),
                org_id=ar_board.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = deputado_data.find('DepGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, ar_board_composition=composition)
            
            # Process deputy situations
            dep_situacao = deputado_data.find('DepSituacao')
            if dep_situacao is not None:
                self._process_deputy_situations(dep_situacao, ar_board_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing AR Board deputy membership: {e}")
            return False
    
    def _process_deputy_admin_council_membership(self, deputado_data: ET.Element, admin_council) -> bool:
        """Process deputy membership in Administrative Council"""
        try:
            # Create historical composition record
            composition = AdministrativeCouncilHistoricalComposition(
                council_id=admin_council.id,
                leg_des=self._get_text_value(deputado_data, 'LegDes'),
                dep_id=self._get_int_value(deputado_data, 'DepId'),
                dep_cad_id=self._get_int_value(deputado_data, 'DepCadId'),
                dep_nome_parlamentar=self._get_text_value(deputado_data, 'DepNomeParlamentar'),
                org_id=admin_council.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = deputado_data.find('DepGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, admin_council_composition=composition)
            
            # Process deputy situations
            dep_situacao = deputado_data.find('DepSituacao')
            if dep_situacao is not None:
                self._process_deputy_situations(dep_situacao, admin_council_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Administrative Council deputy membership: {e}")
            return False
    
    def _process_deputy_permanent_committee_membership(self, deputado_data: ET.Element, permanent_committee) -> bool:
        """Process deputy membership in Permanent Committee"""
        try:
            # Create historical composition record
            composition = PermanentCommitteeHistoricalComposition(
                permanent_committee_id=permanent_committee.id,
                leg_des=self._get_text_value(deputado_data, 'LegDes'),
                dep_id=self._get_int_value(deputado_data, 'DepId'),
                dep_cad_id=self._get_int_value(deputado_data, 'DepCadId'),
                dep_nome_parlamentar=self._get_text_value(deputado_data, 'DepNomeParlamentar'),
                org_id=permanent_committee.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = deputado_data.find('DepGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, permanent_committee_composition=composition)
            
            # Process deputy situations
            dep_situacao = deputado_data.find('DepSituacao')
            if dep_situacao is not None:
                self._process_deputy_situations(dep_situacao, permanent_committee_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Permanent Committee deputy membership: {e}")
            return False
    
    def _process_deputy_leader_conference_membership(self, deputado_data: ET.Element, leader_conference) -> bool:
        """Process deputy membership in Leader Conference"""
        try:
            # Create historical composition record
            composition = LeaderConferenceHistoricalComposition(
                leader_conference_id=leader_conference.id,
                leg_des=self._get_text_value(deputado_data, 'LegDes'),
                dep_id=self._get_int_value(deputado_data, 'DepId'),
                dep_cad_id=self._get_int_value(deputado_data, 'DepCadId'),
                dep_nome_parlamentar=self._get_text_value(deputado_data, 'DepNomeParlamentar'),
                org_id=leader_conference.id_orgao
            )
            
            self.session.add(composition)
            self.session.flush()
            
            # Process parliamentary group situations
            dep_gp = deputado_data.find('DepGP')
            if dep_gp is not None:
                self._process_gp_situations(dep_gp, leader_conference_composition=composition)
            
            # Process deputy situations
            dep_situacao = deputado_data.find('DepSituacao')
            if dep_situacao is not None:
                self._process_deputy_situations(dep_situacao, leader_conference_composition=composition)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing Leader Conference deputy membership: {e}")
            return False
    
    def _convert_roman_to_int(self, roman: str) -> int:
        """Convert Roman numeral to integer"""
        roman_numerals = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
            'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'CONSTITUINTE': 0
        }
        return roman_numerals.get(roman, 17)
    
    def _get_boolean_value(self, parent: ET.Element, tag_name: str) -> bool:
        """Get boolean value from XML element"""
        text_value = self._get_text_value(parent, tag_name)
        if text_value:
            return text_value.lower() in ('true', '1', 'yes', 'sim')
        return False