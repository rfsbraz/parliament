"""
Legislative Initiatives Mapper
==============================

Schema mapper for legislative initiatives files (Iniciativas*.xml).
Handles parliamentary legislative initiatives and maps them to the database.
"""

import xml.etree.ElementTree as ET
import os
import re
from typing import Dict, Optional, Set
import logging

from .base_mapper import SchemaMapper, SchemaError

logger = logging.getLogger(__name__)


class InitiativasMapper(SchemaMapper):
    """Schema mapper for legislative initiatives files"""
    
    def get_expected_fields(self) -> Set[str]:
        return {
            'ArrayOfPt_gov_ar_objectos_iniciativas_DetalhePesquisaIniciativasOut',
            'Pt_gov_ar_objectos_iniciativas_DetalhePesquisaIniciativasOut',
            'IniNr', 'IniTipo', 'IniDescTipo', 'IniTitulo', 'IniId', 'DataInicioleg',
            'IniLeg', 'IniSel', 'IniAutorGrupo', 'IniAutorDeputado', 'IniTipoPesquisa'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map legislative initiatives to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        # Validate schema coverage according to strict mode
        self.validate_schema_coverage(xml_root, file_info, strict_mode)
        
        # Extract legislatura from filename
        filename = os.path.basename(file_info['file_path'])
        leg_match = re.search(r'Iniciativas(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)\.xml', filename)
        legislatura_sigla = leg_match.group(1) if leg_match else 'XVII'
        legislatura_id = self._get_or_create_legislatura(legislatura_sigla)
        
        for iniciativa in xml_root.findall('.//Pt_gov_ar_objectos_iniciativas_DetalhePesquisaIniciativasOut'):
            try:
                success = self._process_iniciativa_record(iniciativa, legislatura_id)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Initiative processing error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['records_processed'] += 1
        
        return results
    
    def _process_iniciativa_record(self, iniciativa: ET.Element, legislatura_id: int) -> bool:
        """Process individual initiative record"""
        try:
            ini_nr = iniciativa.find('IniNr')
            ini_tipo = iniciativa.find('IniTipo')
            ini_desc_tipo = iniciativa.find('IniDescTipo')
            ini_titulo = iniciativa.find('IniTitulo')
            ini_id = iniciativa.find('IniId')
            data_inicio_leg = iniciativa.find('DataInicioleg')
            ini_sel = iniciativa.find('IniSel')
            
            numero = ini_nr.text if ini_nr is not None else None
            tipo = ini_tipo.text if ini_tipo is not None else None
            tipo_descricao = ini_desc_tipo.text if ini_desc_tipo is not None else None
            titulo = ini_titulo.text if ini_titulo is not None else None
            id_externo = ini_id.text if ini_id is not None else None
            data_apresentacao = data_inicio_leg.text if data_inicio_leg is not None else None
            sessao = ini_sel.text if ini_sel is not None else None
            
            if numero and tipo and titulo:
                self.cursor.execute("""
                INSERT OR REPLACE INTO iniciativas_legislativas 
                (id_externo, numero, tipo, titulo, sumario, data_apresentacao, sessao, legislatura_id, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ativo')
                """, (
                    self._safe_int(id_externo),
                    self._safe_int(numero),
                    tipo,
                    titulo,
                    tipo_descricao,  # Using tipo_descricao as sumario
                    self._parse_date(data_apresentacao),
                    self._safe_int(sessao),
                    legislatura_id
                ))
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing initiative: {e}")
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