"""
Parliamentary Activities Mapper
===============================

Schema mapper for parliamentary activities files (Atividades*.xml).
Handles various types of parliamentary activities including debates, 
interpellations, elections, ceremonies, and reports.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging

from .base_mapper import SchemaMapper, SchemaError

logger = logging.getLogger(__name__)


class AtividadesMapper(SchemaMapper):
    """Schema mapper for parliamentary activities files"""
    
    def get_expected_fields(self) -> Set[str]:
        return {
            'Atividades', 'AtividadesGerais', 'Debates', 'Audicoes', 
            'Audiencias', 'Deslocacoes', 'Eventos', 'Relatorios',
            # General Activities
            'Atividade', 'Tipo', 'DescTipo', 'Assunto', 'Legislatura', 'Sessao',
            'DataEntrada', 'Publicacao', 'DataAgendamentoDebate', 'PublicacaoDebate',
            'Numero', 'TipoAutor', 'AutoresGP', 'VotacaoDebate', 'TextosAprovados',
            'OrgaoExterior', 'Eleitos', 'Observacoes', 'Convidados',
            # Publications
            'pt_gov_ar_objectos_PublicacoesOut', 'pubNr', 'pubTipo', 'pubTp', 
            'pubLeg', 'pubSL', 'pubdt', 'pag', 'URLDiario', 'idPag', 'idDeb',
            # Voting
            'pt_gov_ar_objectos_VotacaoOut', 'id', 'resultado', 'reuniao', 
            'publicacao', 'data',
            # Elected members
            'pt_gov_ar_objectos_EleitosOut', 'nome', 'cargo',
            # Guests/Invitees  
            'pt_gov_ar_objectos_ConvidadosOut', 'pais', 'honra',
            # Debates
            'DadosPesquisaDebatesOut', 'DebateId', 'TipoDebateDesig', 'DataDebate',
            'TipoDebate', 'Intervencoes',
            # Reports
            'Relatorio', 'Comissao', 'EntidadesExternas'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict) -> Dict:
        """Map parliamentary activities to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        unmapped_fields = self.check_schema_coverage(xml_root)
        if unmapped_fields:
            logger.warning(f"Some unmapped fields found: {', '.join(list(unmapped_fields)[:10])}")
        
        # Extract legislatura from filename or XML
        legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
        legislatura_id = self._get_or_create_legislatura(legislatura_sigla)
        
        # Process general activities
        atividades_gerais = xml_root.find('.//AtividadesGerais')
        if atividades_gerais is not None:
            for atividade in atividades_gerais.findall('.//Atividade'):
                try:
                    success = self._process_atividade(atividade, legislatura_id)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Activity processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
        
        # Process debates
        debates = xml_root.find('.//Debates')
        if debates is not None:
            for debate in debates.findall('.//DadosPesquisaDebatesOut'):
                try:
                    success = self._process_debate(debate, legislatura_id)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Debate processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
        
        # Process reports
        relatorios = xml_root.find('.//Relatorios')
        if relatorios is not None:
            for relatorio in relatorios.findall('.//Relatorio'):
                try:
                    success = self._process_relatorio(relatorio, legislatura_id)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Report processing error: {str(e)}"
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
    
    def _process_atividade(self, atividade: ET.Element, legislatura_id: int) -> bool:
        """Process individual parliamentary activity"""
        try:
            # Extract basic fields
            tipo = self._get_text_value(atividade, 'Tipo')
            desc_tipo = self._get_text_value(atividade, 'DescTipo')
            assunto = self._get_text_value(atividade, 'Assunto')
            numero = self._get_text_value(atividade, 'Numero')
            
            # Extract dates
            data_entrada_str = self._get_text_value(atividade, 'DataEntrada')
            data_agendamento_str = self._get_text_value(atividade, 'DataAgendamentoDebate')
            
            data_atividade = self._parse_date(data_entrada_str) or self._parse_date(data_agendamento_str)
            if not data_atividade:
                logger.warning(f"No valid date found for activity: {assunto[:50] if assunto else 'Unknown'}")
                return False
            
            if not assunto:
                logger.warning("Missing required field: Assunto")
                return False
            
            # Map activity type
            tipo_atividade = self._map_activity_type(tipo)
            if not tipo_atividade:
                logger.warning(f"Unknown activity type: {tipo}")
                return False
            
            # Create external ID from numero or generate one
            id_externo = None
            if numero:
                try:
                    id_externo = int(numero)
                except ValueError:
                    pass
            
            # Check if record already exists
            if id_externo:
                self.cursor.execute("""
                    SELECT id FROM atividades_parlamentares_detalhadas
                    WHERE id_externo = ?
                """, (id_externo,))
                
                if self.cursor.fetchone():
                    # Update existing record
                    self.cursor.execute("""
                        UPDATE atividades_parlamentares_detalhadas SET
                            tipo = ?, titulo = ?, data_atividade = ?, legislatura_id = ?
                        WHERE id_externo = ?
                    """, (tipo, assunto, data_atividade, legislatura_id, id_externo))
                    return True
            
            # Insert new record
            self.cursor.execute("""
                INSERT INTO atividades_parlamentares_detalhadas (
                    id_externo, tipo, titulo, data_atividade, legislatura_id
                ) VALUES (?, ?, ?, ?, ?)
            """, (id_externo, tipo, assunto, data_atividade, legislatura_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing activity: {e}")
            return False
    
    def _process_debate(self, debate: ET.Element, legislatura_id: int) -> bool:
        """Process debate data"""
        try:
            debate_id = self._get_text_value(debate, 'DebateId')
            assunto = self._get_text_value(debate, 'Assunto')
            data_debate_str = self._get_text_value(debate, 'DataDebate')
            
            if not debate_id or not assunto:
                return False
            
            data_debate = self._parse_date(data_debate_str)
            if not data_debate:
                return False
            
            # Check if already exists
            self.cursor.execute("""
                SELECT id FROM atividades_parlamentares_detalhadas
                WHERE id_externo = ?
            """, (int(debate_id),))
            
            if self.cursor.fetchone():
                return True  # Already exists
            
            # Insert debate as activity
            self.cursor.execute("""
                INSERT INTO atividades_parlamentares_detalhadas (
                    id_externo, tipo, titulo, data_atividade, legislatura_id
                ) VALUES (?, ?, ?, ?, ?)
            """, (int(debate_id), 'DEBATE', assunto, data_debate, legislatura_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing debate: {e}")
            return False
    
    def _process_relatorio(self, relatorio: ET.Element, legislatura_id: int) -> bool:
        """Process report data"""
        try:
            tipo = self._get_text_value(relatorio, 'Tipo')
            assunto = self._get_text_value(relatorio, 'Assunto')
            data_entrada_str = self._get_text_value(relatorio, 'DataEntrada')
            
            if not assunto:
                return False
            
            data_entrada = self._parse_date(data_entrada_str)
            if not data_entrada:
                return False
            
            # Insert report as activity  
            self.cursor.execute("""
                INSERT INTO atividades_parlamentares_detalhadas (
                    tipo, titulo, data_atividade, legislatura_id
                ) VALUES (?, ?, ?, ?)
            """, (tipo or 'RELATORIO', assunto, data_entrada, legislatura_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing report: {e}")
            return False
    
    def _map_activity_type(self, tipo: str) -> Optional[str]:
        """Map XML activity type to database enum"""
        if not tipo:
            return None
        
        # Map common activity types
        type_mapping = {
            'ITG': 'interpelacao',
            'OEX': 'votacao', 
            'SES': 'debate',
            'PRC': 'audiencia',
            'DEBATE': 'debate',
            'RELATORIO': 'audiencia'
        }
        
        return type_mapping.get(tipo.upper(), 'debate')  # Default to debate
    
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