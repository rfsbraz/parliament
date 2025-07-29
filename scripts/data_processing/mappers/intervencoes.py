"""
Parliamentary Interventions Mapper
==================================

Schema mapper for parliamentary interventions files (Intervencoes*.xml).
Handles deputy interventions in parliament sessions and maps them to the database.
"""

import xml.etree.ElementTree as ET
import os
import re
from typing import Dict, Optional, Set
import logging

from .base_mapper import SchemaMapper, SchemaError

logger = logging.getLogger(__name__)


class IntervencoesMapper(SchemaMapper):
    """Schema mapper for parliamentary interventions files"""
    
    def get_expected_fields(self) -> Set[str]:
        return {
            'ArrayOfDadosPesquisaIntervencoesOut', 'DadosPesquisaIntervencoesOut',
            'Id', 'DataReuniaoPlenaria', 'TipoIntervencao', 'Resumo', 'Deputados',
            'DadosDeputado', 'DepId', 'DepNome', 'VideoAudio', 'VideoUrl'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict) -> Dict:
        """Map parliamentary interventions to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        unmapped_fields = self.check_schema_coverage(xml_root)
        if unmapped_fields:
            raise SchemaError(f"Unmapped fields found: {', '.join(unmapped_fields)}")
        
        # Extract legislatura from filename
        filename = os.path.basename(file_info['file_path'])
        leg_match = re.search(r'Intervencoes(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)\.xml', filename)
        legislatura_sigla = leg_match.group(1) if leg_match else 'XVII'
        legislatura_id = self._get_or_create_legislatura(legislatura_sigla)
        
        for intervencao in xml_root.findall('.//DadosPesquisaIntervencoesOut'):
            try:
                success = self._process_intervencao_record(intervencao, legislatura_id)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Intervention processing error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['records_processed'] += 1
        
        return results
    
    def _process_intervencao_record(self, intervencao: ET.Element, legislatura_id: int) -> bool:
        """Process individual intervention record"""
        try:
            id_elem = intervencao.find('Id')
            data_elem = intervencao.find('DataReuniaoPlenaria')
            tipo_elem = intervencao.find('TipoIntervencao')
            resumo_elem = intervencao.find('Resumo')
            
            # Extract deputy ID from nested Deputados element
            deputados_elem = intervencao.find('Deputados')
            deputado_cad_id = None
            if deputados_elem is not None:
                deputado_elem = deputados_elem.find('DadosDeputado')
                if deputado_elem is not None:
                    dep_id_elem = deputado_elem.find('DepId')
                    if dep_id_elem is not None:
                        deputado_cad_id = self._safe_int(dep_id_elem.text)
            
            # Extract video URL if available
            video_elem = intervencao.find('VideoAudio')
            video_url = None
            if video_elem is not None:
                video_url_elem = video_elem.find('VideoUrl')
                if video_url_elem is not None:
                    video_url = video_url_elem.text
            
            if id_elem is not None and data_elem is not None:
                # Get deputy ID
                deputado_id = None
                if deputado_cad_id:
                    self.cursor.execute("SELECT id FROM deputados WHERE id_cadastro = ?", (deputado_cad_id,))
                    dep_result = self.cursor.fetchone()
                    if dep_result:
                        deputado_id = dep_result[0]
                
                self.cursor.execute("""
                INSERT OR REPLACE INTO intervencoes 
                (id_externo, deputado_id, legislatura_id, data_intervencao, tipo, resumo, video_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self._safe_int(id_elem.text),
                    deputado_id,
                    legislatura_id,
                    self._parse_date(data_elem.text),
                    tipo_elem.text if tipo_elem is not None else None,
                    resumo_elem.text if resumo_elem is not None else None,
                    video_url
                ))
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing intervention: {e}")
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