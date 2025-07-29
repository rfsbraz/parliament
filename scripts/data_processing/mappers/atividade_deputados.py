"""
Deputy Activities Mapper
========================

Schema mapper for deputy activity files (AtividadeDeputado*.xml).
Handles parliamentary activities including initiatives with URLs and IDs.
"""

import xml.etree.ElementTree as ET
import os
import re
from typing import Dict, Optional, Set
import logging

from .base_mapper import SchemaMapper, SchemaError

logger = logging.getLogger(__name__)


class AtividadeDeputadosMapper(SchemaMapper):
    """Schema mapper for deputy activity files"""
    
    def get_expected_fields(self) -> Set[str]:
        return {
            'ArrayOfAtividadeDeputado', 'AtividadeDeputado', 'AtividadeDeputadoList',
            'ActividadeOut', 'Ini', 'IniciativasOut', 'IniId', 'IniNr', 'IniTp', 
            'IniTpdesc', 'IniSelLg', 'IniSelNr', 'IniTi', 'Req', 'RequerimentosAtivDepOut',
            'ReqId', 'ReqNr', 'ReqLg', 'ReqSl', 'ReqAs', 'ReqDt', 'ReqPerTp',
            'Intev', 'IntervencoesOut', 'IntId', 'IntTe', 'IntSu', 'PubDtreu',
            'PubTp', 'PubLg', 'PubSl', 'PubNr', 'TinDs', 'PubDar',
            'ActP', 'ActividadesParlamentaresOut', 'ActId', 'ActNr', 'ActTp',
            'ActTpdesc', 'ActSelLg', 'ActSelNr', 'ActDtent', 'ActDtdeb', 'ActAs',
            'Rel', 'RelatoresIniciativas', 'RelatoresIniciativasOut', 'RelFase',
            'Cms', 'ComissoesOut', 'CmsNo', 'CmsCd', 'CmsLg', 'CmsCargo', 'CmsSituacao',
            'DadosLegisDeputado', 'Nome', 'Dpl_lg', 'Dpl_grpar',
            'Audicoes', 'ActividadesComissaoOut', 'AccDtaud', 'NomeEntidadeExterna',
            'ActLg', 'CmsAb', 'Deputado', 'DepId', 'DepCadId', 'DepNomeParlamentar',
            'DepGP', 'DadosSituacaoGP', 'GpId', 'GpSigla', 'GpDtInicio', 'GpDtFim',
            'DepCPId', 'DepCPDes', 'LegDes', 'DepSituacao', 'DadosSituacaoDeputado',
            'SioDes', 'SioDtInicio', 'DepNomeCompleto', 'Scgt', 'SubComissoesGruposTrabalhoOut',
            'CcmDscom', 'ScmCd', 'ScmComCd', 'ScmComLg'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict) -> Dict:
        """Map deputy activities to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        unmapped_fields = self.check_schema_coverage(xml_root)
        if unmapped_fields:
            logger.warning(f"Some unmapped fields found: {', '.join(list(unmapped_fields)[:10])}")
        
        # Extract legislatura from filename
        filename = os.path.basename(file_info['file_path'])
        leg_match = re.search(r'AtividadeDeputado(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)\.xml', filename)
        legislatura_sigla = leg_match.group(1) if leg_match else 'XVII'
        legislatura_id = self._get_or_create_legislatura(legislatura_sigla)
        
        # Process each deputy's activities
        for atividade_deputado in xml_root.findall('.//AtividadeDeputado'):
            try:
                success = self._process_deputy_activities(atividade_deputado, legislatura_id)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Deputy activity processing error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['records_processed'] += 1
        
        return results
    
    def _process_deputy_activities(self, atividade_deputado: ET.Element, legislatura_id: int) -> bool:
        """Process individual deputy activity record"""
        try:
            # Get deputy information
            deputado = atividade_deputado.find('.//Deputado')
            if deputado is None:
                return False
                
            dep_id = deputado.find('DepId')
            dep_cad_id = deputado.find('DepCadId')
            dep_nome = deputado.find('DepNomeParlamentar')
            
            if not (dep_id and dep_cad_id and dep_nome):
                return False
                
            deputado_id = self._safe_int(dep_id.text)
            deputado_cad_id = self._safe_int(dep_cad_id.text)
            deputado_nome = dep_nome.text
            
            # Process initiatives for this deputy
            initiatives_processed = 0
            atividade_list = atividade_deputado.find('.//AtividadeDeputadoList/ActividadeOut')
            if atividade_list is not None:
                ini_section = atividade_list.find('Ini')
                if ini_section is not None:
                    for iniciativa in ini_section.findall('IniciativasOut'):
                        if self._process_initiative_with_urls(iniciativa, deputado_id, deputado_cad_id, legislatura_id):
                            initiatives_processed += 1
            
            return initiatives_processed > 0
            
        except Exception as e:
            logger.error(f"Error processing deputy activities: {e}")
            return False
    
    def _process_initiative_with_urls(self, iniciativa: ET.Element, deputado_id: int, deputado_cad_id: int, legislatura_id: int) -> bool:
        """Process individual initiative with URL data"""
        try:
            ini_id = iniciativa.find('IniId')
            ini_nr = iniciativa.find('IniNr')
            ini_tp = iniciativa.find('IniTp')
            ini_tpdesc = iniciativa.find('IniTpdesc')
            ini_sel_lg = iniciativa.find('IniSelLg')
            ini_sel_nr = iniciativa.find('IniSelNr')
            ini_ti = iniciativa.find('IniTi')
            
            if not (ini_id and ini_nr and ini_tp and ini_ti):
                return False
                
            id_externo_ini = self._safe_int(ini_id.text)
            numero = self._safe_int(ini_nr.text)
            tipo = ini_tp.text
            tipo_descricao = ini_tpdesc.text if ini_tpdesc is not None else None
            titulo = ini_ti.text
            sessao = self._safe_int(ini_sel_nr.text) if ini_sel_nr is not None else None
            
            # Generate URLs based on the Parliament structure
            url_documento = f"https://www.parlamento.pt/ActividadeParlamentar/Paginas/DetalheIniciativa.aspx?BID={id_externo_ini}" if id_externo_ini else None
            url_debates = f"https://debates.parlamento.pt/catalogo/serie1?q={numero}&tipo=iniciativa&lg=XVII" if numero else None
            url_oficial = f"https://www.parlamento.pt/ActividadeParlamentar/Paginas/DetalhePerguntaRequerimento.aspx?BID={id_externo_ini}" if id_externo_ini else None
            
            # Insert or update the initiative
            self.cursor.execute("""
            INSERT OR REPLACE INTO iniciativas_legislativas 
            (id_externo, numero, tipo, tipo_descricao, titulo, sessao, legislatura_id, estado, 
             id_externo_ini, url_documento, url_debates, url_oficial)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ativo', ?, ?, ?, ?)
            """, (
                id_externo_ini,  # Use ini_id as id_externo too
                numero,
                tipo,
                tipo_descricao,
                titulo,
                sessao,
                legislatura_id,
                id_externo_ini,  # id_externo_ini
                url_documento,
                url_debates,
                url_oficial
            ))
            
            # Link the deputy to the initiative if not already linked
            initiative_id = self.cursor.lastrowid
            if initiative_id:
                self.cursor.execute("""
                INSERT OR IGNORE INTO autores_iniciativas (iniciativa_id, deputado_id)
                VALUES (?, ?)
                """, (initiative_id, deputado_cad_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing initiative with URLs: {e}")
            return False
    
    def _get_or_create_legislatura(self, sigla: str) -> int:
        """Get or create legislatura from sigla"""
        roman_to_num = {
            'XVII': 17, 'XVI': 16, 'XV': 15, 'XIV': 14, 'XIII': 13,
            'XII': 12, 'XI': 11, 'X': 10, 'IX': 9, 'VIII': 8,
            'VII': 7, 'VI': 6, 'V': 5, 'IV': 4, 'III': 3,
            'II': 2, 'I': 1, 'CONSTITUINTE': 0
        }
        
        numero = roman_to_num.get(sigla, 17)
        self.cursor.execute("SELECT id FROM legislaturas WHERE numero = ?", (numero,))
        result = self.cursor.fetchone()
        return result[0] if result else 1  # Fallback to first legislatura
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert to int"""
        if not value:
            return None
        try:
            return int(float(value)) if '.' in str(value) else int(value)
        except (ValueError, TypeError):
            return None