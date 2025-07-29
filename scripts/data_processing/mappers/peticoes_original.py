"""
Parliamentary Petitions Mapper
==============================

Schema mapper for parliamentary petition files (Peticoes*.xml).
Handles parliamentary petitions submitted by citizens and organizations.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging

from .base_mapper import SchemaMapper, SchemaError

logger = logging.getLogger(__name__)


class PeticoesMapper(SchemaMapper):
    """Schema mapper for parliamentary petition files"""
    
    def get_expected_fields(self) -> Set[str]:
        return {
            'ArrayOfPeticaoOut', 'PeticaoOut', 'PetId', 'PetNr', 'PetLeg', 'PetSel', 
            'PetAssunto', 'PetSituacao', 'PetNrAssinaturas', 'PetDataEntrada', 
            'PetActividadeId', 'PetAutor', 'PublicacaoPeticao', 'DadosComissao', 
            'DataDebate', 'Documentos', 'PublicacaoDebate', 'Intervencoes',
            # Publication related
            'pt_gov_ar_objectos_PublicacoesOut', 'pubNr', 'pubTipo', 'pubTp', 
            'pubLeg', 'pubSL', 'pubdt', 'idPag', 'URLDiario', 'pag',
            # Committee related
            'ComissoesPetOut', 'Legislatura', 'Numero', 'IdComissao', 'Nome', 
            'Admissibilidade', 'DataAdmissibilidade', 'Relatores', 'DadosRelatorioFinal',
            'DataEnvioPAR', 'DataArquivo', 'Situacao', 'DataReaberta', 'RelatorioFinal',
            'DocumentosPeticao', 'Transitada', 'DataBaixaComissao',
            # Documents
            'PeticaoDocsOut', 'TituloDocumento', 'DataDocumento', 'TipoDocumento', 'URL',
            'DocsRelatorioFinal', 'PeticaoDocsRelatorioFinal',
            # Interventions
            'PeticaoIntervencoesOut', 'DataReuniaoPlenaria', 'Oradores', 'PeticaoOradoresOut',
            'FaseSessao', 'Sumario', 'Publicacao', 'Convidados', 'MembrosGoverno',
            # Reporters
            'pt_gov_ar_objectos_RelatoresOut', 'nome', 'gp', 'dataNomeacao', 'dataCessacao', 'id',
            # Report data
            'pt_gov_ar_objectos_peticoes_DadosRelatorioFinalOut', 'data', 'votacao', 'string',
            # Misc
            'idInt'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict) -> Dict:
        """Map parliamentary petitions to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        unmapped_fields = self.check_schema_coverage(xml_root)
        if unmapped_fields:
            logger.warning(f"Some unmapped fields found: {', '.join(list(unmapped_fields)[:10])}")
        
        # Extract legislatura from filename or XML
        legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
        legislatura_id = self._get_or_create_legislatura(legislatura_sigla)
        
        # Process petitions
        for petition in xml_root.findall('.//PeticaoOut'):
            try:
                success = self._process_petition(petition, legislatura_id)
                results['records_processed'] += 1
                if success:
                    results['records_imported'] += 1
            except Exception as e:
                error_msg = f"Petition processing error: {str(e)}"
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
        
        # Try XML content - look for first PetLeg element
        leg_element = xml_root.find('.//PetLeg')
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
    
    def _process_petition(self, petition: ET.Element, legislatura_id: int) -> bool:
        """Process individual petition"""
        try:
            # Extract basic fields
            pet_id = self._get_int_value(petition, 'PetId')
            pet_nr = self._get_int_value(petition, 'PetNr')
            pet_assunto = self._get_text_value(petition, 'PetAssunto')
            pet_situacao = self._get_text_value(petition, 'PetSituacao')
            pet_nr_assinaturas = self._get_int_value(petition, 'PetNrAssinaturas')
            pet_data_entrada_str = self._get_text_value(petition, 'PetDataEntrada')
            pet_autor = self._get_text_value(petition, 'PetAutor')
            
            if not pet_assunto:
                logger.warning("Missing required field: PetAssunto")
                return False
            
            # Parse entry date
            data_atividade = self._parse_date(pet_data_entrada_str)
            if not data_atividade:
                logger.warning(f"Invalid petition entry date: {pet_data_entrada_str}")
                return False
            
            # Create petition title
            titulo = f"Petição {pet_nr}: {pet_assunto}" if pet_nr else f"Petição: {pet_assunto}"
            if pet_autor:
                titulo += f" (Autor: {pet_autor})"
            
            # Check if petition record already exists
            if pet_id:
                self.cursor.execute("""
                    SELECT id FROM atividades_parlamentares_detalhadas
                    WHERE id_externo = ? AND tipo = 'PETICAO'
                """, (pet_id,))
                
                if self.cursor.fetchone():
                    # Update existing record
                    self.cursor.execute("""
                        UPDATE atividades_parlamentares_detalhadas SET
                            titulo = ?, data_atividade = ?, legislatura_id = ?
                        WHERE id_externo = ? AND tipo = 'PETICAO'
                    """, (titulo, data_atividade, legislatura_id, pet_id))
                    return True
            
            # Insert new petition record
            self.cursor.execute("""
                INSERT INTO atividades_parlamentares_detalhadas (
                    id_externo, tipo, titulo, data_atividade, legislatura_id
                ) VALUES (?, ?, ?, ?, ?)
            """, (pet_id, 'PETICAO', titulo, data_atividade, legislatura_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing petition: {e}")
            return False
    
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