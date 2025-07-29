"""
Parliamentary Questions and Requests Mapper
===========================================

Schema mapper for parliamentary questions and requests files (PerguntasRequerimentos*.xml).
Handles parliamentary questions and formal requests submitted by deputies.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging

from .base_mapper import SchemaMapper, SchemaError

logger = logging.getLogger(__name__)


class PerguntasRequerimentosMapper(SchemaMapper):
    """Schema mapper for parliamentary questions and requests files"""
    
    def get_expected_fields(self) -> Set[str]:
        return {
            'ArrayOfRequerimentoOut', 'RequerimentoOut', 'Id', 'Tipo', 'Nr', 'ReqTipo', 
            'Legislatura', 'Sessao', 'Assunto', 'DtEntrada', 'DataEnvio', 'Observacoes',
            'Publicacao', 'Ficheiro', 'Destinatarios', 'Autores',
            # Publication related
            'pt_gov_ar_objectos_PublicacoesOut', 'pubNr', 'pubTipo', 'pubTp', 
            'pubLeg', 'pubSL', 'pubdt', 'idPag', 'URLDiario', 'pag', 'supl', 'obs',
            'pagFinalDiarioSupl',
            # Recipients and responses
            'pt_gov_ar_objectos_requerimentos_DestinatariosOut', 'nomeEntidade', 'dataEnvio',
            'respostas', 'pt_gov_ar_objectos_requerimentos_RespostasOut', 'entidade', 
            'dataResposta', 'ficheiro', 'docRemetida',
            # Authors
            'pt_gov_ar_objectos_iniciativas_AutoresDeputadosOut', 'idCadastro', 'nome', 'GP',
            'string'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict) -> Dict:
        """Map parliamentary questions and requests to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        unmapped_fields = self.check_schema_coverage(xml_root)
        if unmapped_fields:
            logger.warning(f"Some unmapped fields found: {', '.join(list(unmapped_fields)[:10])}")
        
        # Extract legislatura from filename or XML
        legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
        legislatura_id = self._get_or_create_legislatura(legislatura_sigla)
        
        # Process requests/questions
        for request in xml_root.findall('.//RequerimentoOut'):
            try:
                success = self._process_request(request, legislatura_id)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Request processing error: {str(e)}"
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
        
        # Try XML content - look for first Legislatura element
        leg_element = xml_root.find('.//Legislatura')
        if leg_element is not None and leg_element.text:
            leg_text = leg_element.text.strip()
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
    
    def _process_request(self, request: ET.Element, legislatura_id: int) -> bool:
        """Process individual request/question"""
        try:
            # Extract basic fields
            req_id = self._get_int_value(request, 'Id')
            tipo = self._get_text_value(request, 'Tipo')
            nr = self._get_int_value(request, 'Nr')
            req_tipo = self._get_text_value(request, 'ReqTipo')
            assunto = self._get_text_value(request, 'Assunto')
            dt_entrada_str = self._get_text_value(request, 'DtEntrada')
            data_envio_str = self._get_text_value(request, 'DataEnvio')
            observacoes = self._get_text_value(request, 'Observacoes')
            
            if not assunto:
                logger.warning("Missing required field: Assunto")
                return False
            
            # Parse entry date
            data_atividade = self._parse_date(dt_entrada_str)
            if not data_atividade:
                logger.warning(f"Invalid request entry date: {dt_entrada_str}")
                return False
            
            # Create request title
            titulo_tipo = tipo or 'Pergunta/Requerimento'
            titulo = f"{titulo_tipo} {nr}: {assunto}" if nr else f"{titulo_tipo}: {assunto}"
            
            # Get author information
            author_info = self._get_author_info(request)
            if author_info:
                titulo += f" (Autor: {author_info})"
            
            # Map request type to standard activity type
            activity_type = self._map_request_type(tipo, req_tipo)
            
            # Check if request record already exists
            if req_id:
                self.cursor.execute("""
                    SELECT id FROM atividades_parlamentares_detalhadas
                    WHERE id_externo = ? AND tipo = ?
                """, (req_id, activity_type))
                
                if self.cursor.fetchone():
                    # Update existing record
                    self.cursor.execute("""
                        UPDATE atividades_parlamentares_detalhadas SET
                            titulo = ?, data_atividade = ?, legislatura_id = ?
                        WHERE id_externo = ? AND tipo = ?
                    """, (titulo, data_atividade, legislatura_id, req_id, activity_type))
                    return True
            
            # Insert new request record
            self.cursor.execute("""
                INSERT INTO atividades_parlamentares_detalhadas (
                    id_externo, tipo, titulo, data_atividade, legislatura_id
                ) VALUES (?, ?, ?, ?, ?)
            """, (req_id, activity_type, titulo, data_atividade, legislatura_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return False
    
    def _get_author_info(self, request: ET.Element) -> Optional[str]:
        """Get author information from request"""
        authors_element = request.find('Autores')
        if authors_element is not None:
            for author in authors_element.findall('pt_gov_ar_objectos_iniciativas_AutoresDeputadosOut'):
                nome = self._get_text_value(author, 'nome')
                gp = self._get_text_value(author, 'GP')
                if nome:
                    return f"{nome} ({gp})" if gp else nome
        return None
    
    def _map_request_type(self, tipo: str, req_tipo: str) -> str:
        """Map request type to standard activity type"""
        if not tipo:
            return 'PERGUNTA_REQUERIMENTO'
        
        tipo_upper = tipo.upper()
        
        if 'PERGUNTA' in tipo_upper:
            return 'PERGUNTA'
        elif 'REQUERIMENTO' in tipo_upper:
            return 'REQUERIMENTO'
        else:
            return 'PERGUNTA_REQUERIMENTO'
    
    def _get_text_value(self, parent: ET.Element, tag_name: str) -> Optional[str]:
        """Get text value from XML element"""
        element = parent.find(tag_name)
        if element is not None and element.text:
            return element.text.strip()
        return None
    
    def _get_int_value(self, parent: ET.Element, tag_name: str) -> Optional[int]:
        """Get integer value from XML element"""
        text_value = self._get_text_value(parent, tag_name)
        if text_value:
            try:
                return int(text_value)
            except ValueError:
                return None
        return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
        if not date_str:
            return None
        
        try:
            # Handle ISO format: YYYY-MM-DD
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                return date_str
            
            # Handle datetime format: DD/MM/YYYY HH:MM:SS
            if ' ' in date_str:
                date_part = date_str.split(' ')[0]
            else:
                date_part = date_str
            
            # Try DD/MM/YYYY format
            if '/' in date_part:
                parts = date_part.split('/')
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