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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    SubCommitteeHistoricalComposition, Deputado, Legislatura
)

logger = logging.getLogger(__name__)


class ComposicaoOrgaosMapper(SchemaMapper):
    """Schema mapper for parliamentary organ composition files"""
    
    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
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
            'DadosDeputadoOrgaoSubComissao', 'DadosDeputadoOrgaoGrupoTrabalho'
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
        
            # Process plenary composition
            plenario = xml_root.find('.//Plenario')
            if plenario is not None:
                success = self._process_plenario(plenario, legislatura)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
        
            # Process committees
            comissoes = xml_root.find('.//Comissoes')
            if comissoes is not None:
                for comissao in comissoes:
                    try:
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
    
    def _convert_roman_to_int(self, roman: str) -> int:
        """Convert Roman numeral to integer"""
        roman_numerals = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
            'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'CONSTITUINTE': 0
        }
        return roman_numerals.get(roman, 17)