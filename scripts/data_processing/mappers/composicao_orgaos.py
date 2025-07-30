"""
Parliamentary Organ Composition Mapper
======================================

Schema mapper for parliamentary organ composition files (OrgaoComposicao*.xml).
Handles composition of various parliamentary organs including plenary, committees,
and other parliamentary bodies with their member assignments.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging

from .base_mapper import SchemaMapper, SchemaError

logger = logging.getLogger(__name__)


class ComposicaoOrgaosMapper(SchemaMapper):
    """Schema mapper for parliamentary organ composition files"""
    
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
        
        # Validate schema coverage according to strict mode
        self.validate_schema_coverage(xml_root, file_info, strict_mode)
        
        # Extract legislatura from filename or XML
        legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
        legislatura_id = self._get_or_create_legislatura(legislatura_sigla)
        
        # Process plenary composition
        plenario = xml_root.find('.//Plenario')
        if plenario is not None:
            success = self._process_plenario(plenario, legislatura_id)
            results['records_processed'] += 1
            if success:
                results['records_imported'] += 1
        
        # Process committees
        comissoes = xml_root.find('.//Comissoes')
        if comissoes is not None:
            for comissao in comissoes:
                try:
                    success = self._process_comissao(comissao, legislatura_id)
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
                    success = self._process_subcomissao(subcomissao, legislatura_id)
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
                    success = self._process_grupo_trabalho(grupo, legislatura_id)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Working group processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
        
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
    
    def _process_plenario(self, plenario: ET.Element, legislatura_id: int) -> bool:
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
            
            # Create or get committee record for plenary
            comissao_id = self._get_or_create_comissao(
                int(float(id_orgao)), sigla_orgao, nome_sigla, 'permanente', legislatura_id
            )
            
            # Process members
            composicao = plenario.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoPlenario'):
                    self._process_deputy_membership(deputado_data, comissao_id, 'membro')
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing plenary: {e}")
            return False
    
    def _process_comissao(self, comissao: ET.Element, legislatura_id: int) -> bool:
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
            comissao_id = self._get_or_create_comissao(
                int(float(id_orgao)), sigla_orgao, nome_sigla or sigla_orgao, 'permanente', legislatura_id
            )
            
            # Process members
            composicao = comissao.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoComissao'):
                    self._process_deputy_committee_membership(deputado_data, comissao_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing committee: {e}")
            return False
    
    def _process_subcomissao(self, subcomissao: ET.Element, legislatura_id: int) -> bool:
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
            comissao_id = self._get_or_create_comissao(
                int(float(id_orgao)), sigla_orgao, nome_sigla or sigla_orgao, 'sub_comissao', legislatura_id
            )
            
            # Process members
            composicao = subcomissao.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoSubComissao'):
                    self._process_deputy_committee_membership(deputado_data, comissao_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing subcommittee: {e}")
            return False
    
    def _process_grupo_trabalho(self, grupo: ET.Element, legislatura_id: int) -> bool:
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
            comissao_id = self._get_or_create_comissao(
                int(float(id_orgao)), sigla_orgao, nome_sigla or sigla_orgao, 'eventual', legislatura_id
            )
            
            # Process members
            composicao = grupo.find('Composicao')
            if composicao is not None:
                for deputado_data in composicao.findall('DadosDeputadoOrgaoGrupoTrabalho'):
                    self._process_deputy_committee_membership(deputado_data, comissao_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing working group: {e}")
            return False
    
    def _process_deputy_membership(self, deputado_data: ET.Element, comissao_id: int, cargo: str = 'membro') -> bool:
        """Process deputy membership in plenary"""
        try:
            dep_id = self._get_text_value(deputado_data, 'DepId')
            dep_nome = self._get_text_value(deputado_data, 'DepNomeParlamentar')
            
            if not dep_id or not dep_nome:
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
            deputado_id = self._get_or_create_deputy(int(float(dep_id)), dep_nome)
            
            # Insert membership record
            self.cursor.execute("""
                INSERT OR IGNORE INTO membros_comissoes (
                    comissao_id, deputado_id, cargo, data_inicio, data_fim, titular
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (comissao_id, deputado_id, cargo, data_inicio, data_fim, True))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing deputy membership: {e}")
            return False
    
    def _process_deputy_committee_membership(self, deputado_data: ET.Element, comissao_id: int) -> bool:
        """Process deputy membership in committee/subcommittee/working group"""
        try:
            dep_id = self._get_text_value(deputado_data, 'DepId')
            dep_nome = self._get_text_value(deputado_data, 'DepNomeParlamentar')
            cargo_des = self._get_text_value(deputado_data, 'CarDes')
            
            if not dep_id or not dep_nome:
                return False
            
            # Map cargo description to standard values
            cargo = self._map_cargo(cargo_des)
            
            # Get dates
            data_inicio = self._parse_date(self._get_text_value(deputado_data, 'DtInicio'))
            data_fim = self._parse_date(self._get_text_value(deputado_data, 'DtFim'))
            
            if not data_inicio:
                return False
            
            # Find or create deputy
            deputado_id = self._get_or_create_deputy(int(float(dep_id)), dep_nome)
            
            # Insert membership record
            self.cursor.execute("""
                INSERT OR IGNORE INTO membros_comissoes (
                    comissao_id, deputado_id, cargo, data_inicio, data_fim, titular
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (comissao_id, deputado_id, cargo, data_inicio, data_fim, True))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing deputy committee membership: {e}")
            return False
    
    def _get_or_create_comissao(self, id_externo: int, sigla: str, nome: str, tipo: str, legislatura_id: int) -> int:
        """Get or create committee record"""
        # Check if committee exists
        self.cursor.execute("""
            SELECT id FROM comissoes WHERE id_externo = ? AND legislatura_id = ?
        """, (id_externo, legislatura_id))
        
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        # Create new committee
        self.cursor.execute("""
            INSERT INTO comissoes (id_externo, legislatura_id, nome, sigla, tipo, ativa)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (id_externo, legislatura_id, nome, sigla, tipo, True))
        
        return self.cursor.lastrowid
    
    def _get_or_create_deputy(self, dep_id: int, nome: str) -> int:
        """Get or create deputy record"""
        # Check if deputy exists
        self.cursor.execute("""
            SELECT id FROM deputados WHERE id_cadastro = ?
        """, (dep_id,))
        
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        # Create basic deputy record (will be enriched by other mappers)
        self.cursor.execute("""
            INSERT INTO deputados (id_cadastro, nome, nome_completo)
            VALUES (?, ?, ?)
        """, (dep_id, nome, nome))
        
        return self.cursor.lastrowid
    
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
    
    def _get_or_create_legislatura(self, legislatura_sigla: str) -> int:
        """Get or create legislatura record"""
        # Check if legislatura exists
        self.cursor.execute("""
            SELECT id FROM legislaturas WHERE numero = ?
        """, (legislatura_sigla,))
        
        result = self.cursor.fetchone()
        if result:
            return result[0]
        
        # Create new legislatura if it doesn't exist
        numero_int = self._convert_roman_to_int(legislatura_sigla)
        
        self.cursor.execute("""
            INSERT INTO legislaturas (numero, designacao, ativa)
            VALUES (?, ?, ?)
        """, (legislatura_sigla, f"{numero_int}.ª Legislatura", False))
        
        return self.cursor.lastrowid
    
    def _convert_roman_to_int(self, roman: str) -> int:
        """Convert Roman numeral to integer"""
        roman_numerals = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
            'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'CONSTITUINTE': 0
        }
        return roman_numerals.get(roman, 17)