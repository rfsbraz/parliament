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

logger = logging.getLogger(__name__)


class RegistoBiograficoMapper(SchemaMapper):
    """Schema mapper for biographical registry files"""
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # Root elements
            'ArrayOfDadosRegistoBiografico',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico',
            
            # Basic biographical data
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadNomeCompleto',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDtNascimento',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadSexo',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadProfissao',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadNaturalidade',
            
            # Academic qualifications
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadHabilitacoes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadHabilitacoes.DadosHabilitacoes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadHabilitacoes.DadosHabilitacoes.HabId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadHabilitacoes.DadosHabilitacoes.HabDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadHabilitacoes.DadosHabilitacoes.HabTipoId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadHabilitacoes.DadosHabilitacoes.HabEstado',
            
            # Professional roles
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCargosFuncoes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCargosFuncoes.DadosCargosFuncoes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCargosFuncoes.DadosCargosFuncoes.FunId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCargosFuncoes.DadosCargosFuncoes.FunDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCargosFuncoes.DadosCargosFuncoes.FunOrdem',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCargosFuncoes.DadosCargosFuncoes.FunAntiga',
            
            # Organ activities
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.orgId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.orgDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.orgSigla',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.legDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.timDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes.pt_ar_wsgode_objectos_DadosCargosOrgao',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeCom.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes.pt_ar_wsgode_objectos_DadosCargosOrgao.tiaDes',
            
            # Working group activities
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.orgId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.orgDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.orgSigla',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.legDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.timDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes.pt_ar_wsgode_objectos_DadosCargosOrgao',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadActividadeOrgaos.actividadeGT.pt_ar_wsgode_objectos_DadosOrgaos.cargoDes.pt_ar_wsgode_objectos_DadosCargosOrgao.tiaDes',
            
            # Deputy legislature data
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.DepNomeParlamentar',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.LegDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.ParDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.ParSigla',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.GpDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.GpSigla',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.CeDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.IndDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadDeputadoLegis.DadosDeputadoLegis.IndData',
            
            # Titles and honors
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadTitulos',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadTitulos.DadosTitulos',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadTitulos.DadosTitulos.TitId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadTitulos.DadosTitulos.TitDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadTitulos.DadosTitulos.TitOrdem',
            
            # Decorations
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCondecoracoes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCondecoracoes.DadosCondecoracoes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCondecoracoes.DadosCondecoracoes.CodId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCondecoracoes.DadosCondecoracoes.CodDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadCondecoracoes.DadosCondecoracoes.CodOrdem',
            
            # Published works
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadObrasPublicadas',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadObrasPublicadas.DadosObrasPublicadas',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadObrasPublicadas.DadosObrasPublicadas.PubId',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadObrasPublicadas.DadosObrasPublicadas.PubDes',
            'ArrayOfDadosRegistoBiografico.DadosRegistoBiografico.CadObrasPublicadas.DadosObrasPublicadas.PubOrdem'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map biographical data to database"""
        results = {
            'records_processed': 0,
            'records_imported': 0,
            'errors': []
        }
        
        # Validate schema coverage according to strict mode
        self.validate_schema_coverage(xml_root, file_info, strict_mode)
        
        # Process biographical records  
        for record in xml_root.findall('.//DadosRegistoBiografico'):
            try:
                success = self._process_biographical_record(record, file_info)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Record processing error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['records_processed'] += 1
        
        return results
    
    def _process_biographical_record(self, record: ET.Element, file_info: Dict) -> bool:
        """Process individual biographical record"""
        try:
            # Extract basic data
            cad_id_elem = record.find('CadId')
            nome_completo_elem = record.find('CadNomeCompleto')
            data_nascimento_elem = record.find('CadDtNascimento')
            sexo_elem = record.find('CadSexo')
            profissao_elem = record.find('CadProfissao')
            naturalidade_elem = record.find('CadNaturalidade')
            
            id_cadastro = int(float(cad_id_elem.text)) if cad_id_elem is not None and cad_id_elem.text else None
            nome_completo = nome_completo_elem.text if nome_completo_elem is not None else None
            data_nascimento = data_nascimento_elem.text if data_nascimento_elem is not None else None
            sexo = sexo_elem.text if sexo_elem is not None else None
            profissao = profissao_elem.text if profissao_elem is not None else None
            naturalidade = naturalidade_elem.text if naturalidade_elem is not None else None
            
            if not id_cadastro:
                logger.warning("Skipping record without CadId")
                return False
            
            # Process academic qualifications
            habilitacoes_list = []
            habilitacoes_elem = record.find('CadHabilitacoes')
            if habilitacoes_elem is not None:
                for hab in habilitacoes_elem.findall('DadosHabilitacoes'):
                    hab_des = hab.find('HabDes')
                    if hab_des is not None and hab_des.text:
                        habilitacoes_list.append(hab_des.text)
            
            habilitacoes_academicas = '; '.join(habilitacoes_list) if habilitacoes_list else None
            
            # Process organ activities - both committees and working groups
            organ_activities = []
            atividade_orgaos_elem = record.find('CadActividadeOrgaos')
            if atividade_orgaos_elem is not None:
                # Committee activities
                for atividade in atividade_orgaos_elem.findall('.//actividadeCom/pt_ar_wsgode_objectos_DadosOrgaos'):
                    org_data = self._extract_organ_activity(atividade, 'committee')
                    if org_data:
                        organ_activities.append(org_data)
                
                # Working group activities
                for atividade in atividade_orgaos_elem.findall('.//actividadeGT/pt_ar_wsgode_objectos_DadosOrgaos'):
                    org_data = self._extract_organ_activity(atividade, 'working_group')
                    if org_data:
                        organ_activities.append(org_data)
            
            # Update or insert deputy
            updated = self._upsert_deputy(id_cadastro, nome_completo, data_nascimento, 
                                        sexo, profissao, naturalidade, habilitacoes_academicas)
            
            # Process organ activities
            if updated:
                deputado_id = self._get_deputy_id(id_cadastro)
                if deputado_id and organ_activities:
                    for org_activity in organ_activities:
                        self._process_organ_activity(deputado_id, org_activity)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing biographical record: {e}")
            return False
    
    def _extract_organ_activity(self, atividade: ET.Element, activity_type: str = 'committee') -> Optional[Dict]:
        """Extract organ activity data"""
        org_id_elem = atividade.find('orgId')
        org_des_elem = atividade.find('orgDes')
        org_sigla_elem = atividade.find('orgSigla')
        leg_des_elem = atividade.find('legDes')
        tim_des_elem = atividade.find('timDes')
        
        if org_id_elem is not None and org_des_elem is not None:
            org_data = {
                'org_id': int(float(org_id_elem.text)) if org_id_elem.text else None,
                'org_nome': org_des_elem.text,
                'org_sigla': org_sigla_elem.text if org_sigla_elem is not None else None,
                'legislatura': leg_des_elem.text if leg_des_elem is not None else None,
                'tipo_membro': tim_des_elem.text if tim_des_elem is not None else 'Efetivo',
                'activity_type': activity_type
            }
            
            # Extract position if exists
            cargo_elem = atividade.find('.//pt_ar_wsgode_objectos_DadosCargosOrgao/tiaDes')
            if cargo_elem is not None:
                org_data['cargo_codigo'] = cargo_elem.text
            
            return org_data
        
        return None
    
    def _upsert_deputy(self, id_cadastro: int, nome_completo: str, data_nascimento: str,
                      sexo: str, profissao: str, naturalidade: str, habilitacoes_academicas: str) -> bool:
        """Insert or update deputy data"""
        try:
            self.cursor.execute("SELECT id FROM deputados WHERE id_cadastro = ?", (id_cadastro,))
            if self.cursor.fetchone():
                # Update existing
                self.cursor.execute("""
                    UPDATE deputados 
                    SET nome_completo = COALESCE(?, nome_completo),
                        data_nascimento = COALESCE(?, data_nascimento),
                        profissao = COALESCE(?, profissao),
                        naturalidade = COALESCE(?, naturalidade),
                        habilitacoes_academicas = COALESCE(?, habilitacoes_academicas),
                        updated_at = ?
                    WHERE id_cadastro = ?
                """, (nome_completo, self._parse_date(data_nascimento), profissao, 
                      naturalidade, habilitacoes_academicas, datetime.now(), id_cadastro))
                return self.cursor.rowcount > 0
            else:
                logger.warning(f"Deputy with id_cadastro {id_cadastro} not found in database")
                return False
        except Exception as e:
            logger.error(f"Error upserting deputy {id_cadastro}: {e}")
            return False
    
    def _get_deputy_id(self, id_cadastro: int) -> Optional[int]:
        """Get deputy internal ID"""
        try:
            self.cursor.execute("SELECT id FROM deputados WHERE id_cadastro = ?", (id_cadastro,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting deputy ID for {id_cadastro}: {e}")
            return None
    
    def _process_organ_activity(self, deputado_id: int, org_activity: Dict):
        """Process organ activity and create committee membership"""
        try:
            # Get or create legislatura
            legislatura_id = self._get_or_create_legislatura(org_activity.get('legislatura'))
            
            # Get or create committee/organ
            comissao_id = self._get_or_create_comissao(org_activity, legislatura_id)
            
            if comissao_id:
                # Create committee membership
                titular = org_activity.get('tipo_membro', 'Efetivo').lower() == 'efetivo'
                cargo = self._map_cargo_code(org_activity.get('cargo_codigo', ''))
                
                # Check if membership already exists
                self.cursor.execute("""
                    SELECT id FROM membros_comissoes 
                    WHERE comissao_id = ? AND deputado_id = ? AND titular = ?
                """, (comissao_id, deputado_id, titular))
                
                if not self.cursor.fetchone():
                    self.cursor.execute("""
                        INSERT INTO membros_comissoes (comissao_id, deputado_id, cargo, titular, data_inicio, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        comissao_id,
                        deputado_id,
                        cargo,
                        titular,
                        datetime.now().date(),
                        f"Legislatura {org_activity.get('legislatura', 'N/A')} - {org_activity.get('activity_type', 'committee')}"
                    ))
                    logger.debug(f"Created committee membership for deputy {deputado_id} in {org_activity.get('org_nome')}")
                    
        except Exception as e:
            logger.error(f"Error processing organ activity: {e}")
    
    def _get_or_create_legislatura(self, legislatura_str: str) -> Optional[int]:
        """Get or create legislatura"""
        if not legislatura_str:
            return None
            
        try:
            # Convert roman numerals to numbers
            roman_map = {
                'XVII': 17, 'XVI': 16, 'XV': 15, 'XIV': 14, 'XIII': 13,
                'XII': 12, 'XI': 11, 'X': 10, 'IX': 9, 'VIII': 8,
                'VII': 7, 'VI': 6, 'V': 5, 'IV': 4, 'III': 3,
                'II': 2, 'I': 1, 'CONSTITUINTE': 0
            }
            
            legislatura_num = roman_map.get(legislatura_str.upper(), None)
            if legislatura_num is None:
                try:
                    legislatura_num = int(legislatura_str)
                except:
                    return None
            
            self.cursor.execute("SELECT id FROM legislaturas WHERE numero = ?", (legislatura_num,))
            result = self.cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error getting legislatura {legislatura_str}: {e}")
            return None
    
    def _get_or_create_comissao(self, org_activity: Dict, legislatura_id: Optional[int]) -> Optional[int]:
        """Get or create committee/organ"""
        try:
            org_id = org_activity.get('org_id')
            org_nome = org_activity.get('org_nome')
            
            if not org_id or not org_nome:
                return None
            
            # Check if committee exists
            self.cursor.execute("SELECT id FROM comissoes WHERE id_externo = ?", (org_id,))
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # Create new committee
                self.cursor.execute("""
                    INSERT INTO comissoes (id_externo, legislatura_id, nome, sigla, tipo, ativa)
                    VALUES (?, ?, ?, ?, ?, TRUE)
                """, (
                    org_id,
                    legislatura_id,
                    org_nome,
                    org_activity.get('org_sigla'),
                    'permanente'  # Default type
                ))
                return self.cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Error getting/creating committee: {e}")
            return None
    
    def _map_cargo_code(self, cargo_codigo: str) -> str:
        """Map cargo code to database cargo field"""
        if not cargo_codigo:
            return 'membro'
        
        cargo_map = {
            'CGP': 'presidente',
            'VCGP': 'vice_presidente', 
            'SCGP': 'secretario'
        }
        
        return cargo_map.get(cargo_codigo.upper(), 'membro')
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to standard format"""
        if not date_str:
            return None
        
        # Handle different date formats commonly found in Portuguese parliament data
        try:
            # Try standard formats
            from datetime import datetime as dt
            
            # Try YYYY-MM-DD format
            if len(date_str) == 10 and '-' in date_str:
                return date_str
            
            # Try DD-MM-YYYY format
            if len(date_str) == 10 and '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 3 and len(parts[2]) == 4:
                    return f"{parts[2]}-{parts[1]:0>2}-{parts[0]:0>2}"
            
            # Try DD/MM/YYYY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3 and len(parts[2]) == 4:
                    return f"{parts[2]}-{parts[1]:0>2}-{parts[0]:0>2}"
            
            # Return as-is if we can't parse
            return date_str
            
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return date_str