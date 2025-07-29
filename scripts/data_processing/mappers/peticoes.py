"""
Comprehensive Parliamentary Petitions Mapper
============================================

Enhanced schema mapper for parliamentary petition files (Peticoes*.xml).
Imports EVERY SINGLE FIELD and structure from the XML including:
- Main petition data
- Committee handling across multiple legislaturas
- Reporters and their assignments
- Final reports with voting data
- Documents (texts, final reports)
- Interventions/debates with speakers
- Publications for all phases
- Complete audit trail of petition lifecycle

Maps to comprehensive database schema with full relational structure.
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
    """Comprehensive schema mapper for parliamentary petition files"""
    
    def get_expected_fields(self) -> Set[str]:
        # Complete field list from XML analysis
        return {
            # Root elements
            'ArrayOfPeticaoOut', 'PeticaoOut',
            # Core petition fields
            'PetId', 'PetNr', 'PetLeg', 'PetSel', 'PetAssunto', 'PetSituacao', 
            'PetNrAssinaturas', 'PetDataEntrada', 'PetActividadeId', 'PetAutor',
            'DataDebate',
            # Publications
            'PublicacaoPeticao', 'PublicacaoDebate', 'pt_gov_ar_objectos_PublicacoesOut', 
            'pubNr', 'pubTipo', 'pubTp', 'pubLeg', 'pubSL', 'pubdt', 'pag', 'string',
            'idPag', 'URLDiario', 'idInt',
            # Committee data
            'DadosComissao', 'ComissoesPetOut', 'Legislatura', 'Numero', 'IdComissao', 
            'Nome', 'Admissibilidade', 'DataAdmissibilidade', 'DataEnvioPAR', 'DataArquivo', 
            'Situacao', 'DataReaberta', 'DataBaixaComissao', 'Transitada',
            # Reporters
            'Relatores', 'pt_gov_ar_objectos_RelatoresOut', 'nome', 'gp', 
            'dataNomeacao', 'dataCessacao', 'id',
            # Final reports
            'DadosRelatorioFinal', 'pt_gov_ar_objectos_peticoes_DadosRelatorioFinalOut', 
            'data', 'votacao', 'RelatorioFinal',
            # Documents
            'Documentos', 'DocumentosPeticao', 'PeticaoDocsOut', 'DocsRelatorioFinal', 
            'PeticaoDocsRelatorioFinal', 'TituloDocumento', 'DataDocumento', 
            'TipoDocumento', 'URL',
            # Interventions
            'Intervencoes', 'PeticaoIntervencoesOut', 'DataReuniaoPlenaria', 'Oradores', 
            'PeticaoOradoresOut', 'FaseSessao', 'Sumario', 'Publicacao', 'Convidados', 
            'MembrosGoverno'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map parliamentary petitions with complete structure to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        # Validate schema coverage with strict mode support
        self.validate_schema_coverage(xml_root, file_info, strict_mode)
        
        # Extract legislatura from filename or XML
        legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
        legislatura_id = self._get_or_create_legislatura(legislatura_sigla)
        
        # Process petitions
        for petition in xml_root.findall('.//PeticaoOut'):
            try:
                success = self._process_petition_complete(petition, legislatura_id)
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
    
    def _process_petition_complete(self, petition: ET.Element, legislatura_id: int) -> bool:
        """Process complete petition with all structures"""
        try:
            # Extract core petition data
            pet_id = self._get_int_value(petition, 'PetId')
            pet_nr = self._get_int_value(petition, 'PetNr')
            pet_leg = self._get_text_value(petition, 'PetLeg')
            pet_sel = self._get_int_value(petition, 'PetSel')
            pet_assunto = self._get_text_value(petition, 'PetAssunto')
            pet_situacao = self._get_text_value(petition, 'PetSituacao')
            pet_nr_assinaturas = self._get_int_value(petition, 'PetNrAssinaturas')
            pet_data_entrada = self._parse_date(self._get_text_value(petition, 'PetDataEntrada'))
            pet_atividade_id = self._get_int_value(petition, 'PetActividadeId')
            pet_autor = self._get_text_value(petition, 'PetAutor')
            data_debate = self._parse_date(self._get_text_value(petition, 'DataDebate'))
            
            if not pet_id or not pet_assunto:
                logger.warning("Missing required fields: pet_id or pet_assunto")
                return False
            
            # Insert or update main petition record
            self.cursor.execute("""
                INSERT OR REPLACE INTO peticoes_detalhadas (
                    pet_id, pet_nr, pet_leg, pet_sel, pet_assunto, pet_situacao,
                    pet_nr_assinaturas, pet_data_entrada, pet_atividade_id, 
                    pet_autor, data_debate, legislatura_id, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pet_id, pet_nr, pet_leg, pet_sel, pet_assunto, pet_situacao,
                pet_nr_assinaturas, pet_data_entrada, pet_atividade_id,
                pet_autor, data_debate, legislatura_id, datetime.now().isoformat()
            ))
            
            peticao_db_id = self.cursor.lastrowid or self._get_peticao_db_id(pet_id)
            
            # Process all related structures
            self._process_publicacoes(petition, peticao_db_id)
            self._process_dados_comissao(petition, peticao_db_id)
            self._process_documentos(petition, peticao_db_id)
            self._process_intervencoes(petition, peticao_db_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing petition {pet_id}: {e}")
            return False
    
    def _get_peticao_db_id(self, pet_id: int) -> int:
        """Get database ID for petition"""
        self.cursor.execute("SELECT id FROM peticoes_detalhadas WHERE pet_id = ?", (pet_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def _process_publicacoes(self, petition: ET.Element, peticao_db_id: int):
        """Process all publication types for petition"""
        # Clear existing publications
        self.cursor.execute("DELETE FROM peticoes_publicacoes WHERE peticao_id = ?", (peticao_db_id,))
        
        # PublicacaoPeticao
        pub_peticao = petition.find('PublicacaoPeticao')
        if pub_peticao is not None:
            for pub in pub_peticao.findall('pt_gov_ar_objectos_PublicacoesOut'):
                self._insert_publicacao(peticao_db_id, pub, 'PublicacaoPeticao')
        
        # PublicacaoDebate
        pub_debate = petition.find('PublicacaoDebate')
        if pub_debate is not None:
            for pub in pub_debate.findall('pt_gov_ar_objectos_PublicacoesOut'):
                self._insert_publicacao(peticao_db_id, pub, 'PublicacaoDebate')
    
    def _insert_publicacao(self, peticao_id: int, pub: ET.Element, tipo: str):
        """Insert publication data"""
        pub_nr = self._get_int_value(pub, 'pubNr')
        pub_tipo = self._get_text_value(pub, 'pubTipo')
        pub_tp = self._get_text_value(pub, 'pubTp')
        pub_leg = self._get_text_value(pub, 'pubLeg')
        pub_sl = self._get_int_value(pub, 'pubSL')
        pub_dt = self._parse_date(self._get_text_value(pub, 'pubdt'))
        id_pag = self._get_int_value(pub, 'idPag')
        url_diario = self._get_text_value(pub, 'URLDiario')
        
        # Handle page numbers
        pag_text = None
        pag_elem = pub.find('pag')
        if pag_elem is not None:
            string_elems = pag_elem.findall('string')
            if string_elems:
                pag_text = ', '.join([s.text for s in string_elems if s.text])
        
        self.cursor.execute("""
            INSERT INTO peticoes_publicacoes (
                peticao_id, tipo, pub_nr, pub_tipo, pub_tp, pub_leg, pub_sl,
                pub_dt, pag, id_pag, url_diario
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (peticao_id, tipo, pub_nr, pub_tipo, pub_tp, pub_leg, pub_sl, pub_dt, pag_text, id_pag, url_diario))
    
    def _process_dados_comissao(self, petition: ET.Element, peticao_db_id: int):
        """Process committee data (can be multiple across legislaturas)"""
        # Clear existing committee data
        self.cursor.execute("DELETE FROM peticoes_comissoes WHERE peticao_id = ?", (peticao_db_id,))
        
        dados_comissao = petition.find('DadosComissao')
        if dados_comissao is not None:
            for comissao in dados_comissao.findall('ComissoesPetOut'):
                comissao_db_id = self._process_single_comissao(comissao, peticao_db_id)
                if comissao_db_id:
                    self._process_comissao_details(comissao, comissao_db_id)
    
    def _process_single_comissao(self, comissao: ET.Element, peticao_db_id: int) -> Optional[int]:
        """Process single committee record"""
        legislatura = self._get_text_value(comissao, 'Legislatura')
        numero = self._get_int_value(comissao, 'Numero')
        id_comissao = self._get_int_value(comissao, 'IdComissao')
        nome = self._get_text_value(comissao, 'Nome')
        admissibilidade = self._get_text_value(comissao, 'Admissibilidade')
        data_admissibilidade = self._parse_date(self._get_text_value(comissao, 'DataAdmissibilidade'))
        data_envio_par = self._parse_date(self._get_text_value(comissao, 'DataEnvioPAR'))
        data_arquivo = self._parse_date(self._get_text_value(comissao, 'DataArquivo'))
        situacao = self._get_text_value(comissao, 'Situacao')
        data_reaberta = self._parse_date(self._get_text_value(comissao, 'DataReaberta'))
        data_baixa_comissao = self._parse_date(self._get_text_value(comissao, 'DataBaixaComissao'))
        transitada = self._get_text_value(comissao, 'Transitada')
        
        self.cursor.execute("""
            INSERT INTO peticoes_comissoes (
                peticao_id, legislatura, numero, id_comissao, nome, admissibilidade,
                data_admissibilidade, data_envio_par, data_arquivo, situacao,
                data_reaberta, data_baixa_comissao, transitada
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            peticao_db_id, legislatura, numero, id_comissao, nome, admissibilidade,
            data_admissibilidade, data_envio_par, data_arquivo, situacao,
            data_reaberta, data_baixa_comissao, transitada
        ))
        
        return self.cursor.lastrowid
    
    def _process_comissao_details(self, comissao: ET.Element, comissao_db_id: int):
        """Process detailed committee structures"""
        # Reporters
        self._process_relatores(comissao, comissao_db_id)
        
        # Final reports
        self._process_dados_relatorio_final(comissao, comissao_db_id)
        
        # Committee documents
        self._process_documentos_comissao(comissao, comissao_db_id)
    
    def _process_relatores(self, comissao: ET.Element, comissao_db_id: int):
        """Process reporters for committee"""
        relatores = comissao.find('Relatores')
        if relatores is not None:
            for relator in relatores.findall('pt_gov_ar_objectos_RelatoresOut'):
                relator_id = self._get_int_value(relator, 'id')
                nome = self._get_text_value(relator, 'nome')
                gp = self._get_text_value(relator, 'gp')
                data_nomeacao = self._parse_date(self._get_text_value(relator, 'dataNomeacao'))
                data_cessacao = self._parse_date(self._get_text_value(relator, 'dataCessacao'))
                
                self.cursor.execute("""
                    INSERT INTO peticoes_relatores (
                        comissao_peticao_id, relator_id, nome, gp, 
                        data_nomeacao, data_cessacao
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (comissao_db_id, relator_id, nome, gp, data_nomeacao, data_cessacao))
    
    def _process_dados_relatorio_final(self, comissao: ET.Element, comissao_db_id: int):
        """Process final report data"""
        dados_relatorio = comissao.find('DadosRelatorioFinal')
        if dados_relatorio is not None:
            for relatorio in dados_relatorio.findall('pt_gov_ar_objectos_peticoes_DadosRelatorioFinalOut'):
                data_relatorio = self._parse_date(self._get_text_value(relatorio, 'data'))
                votacao = self._get_text_value(relatorio, 'votacao')
                
                self.cursor.execute("""
                    INSERT INTO peticoes_relatorios_finais (
                        comissao_peticao_id, data_relatorio, votacao
                    ) VALUES (?, ?, ?)
                """, (comissao_db_id, data_relatorio, votacao))
        
        # Process RelatorioFinal string elements
        relatorio_final = comissao.find('RelatorioFinal')
        if relatorio_final is not None:
            for string_elem in relatorio_final.findall('string'):
                relatorio_id = string_elem.text
                if relatorio_id:
                    self.cursor.execute("""
                        INSERT INTO peticoes_relatorios_finais (
                            comissao_peticao_id, relatorio_final_id
                        ) VALUES (?, ?)
                    """, (comissao_db_id, relatorio_id))
    
    def _process_documentos_comissao(self, comissao: ET.Element, comissao_db_id: int):
        """Process committee-specific documents"""
        documentos_peticao = comissao.find('DocumentosPeticao')
        if documentos_peticao is not None:
            # DocsRelatorioFinal
            docs_relatorio = documentos_peticao.find('DocsRelatorioFinal')
            if docs_relatorio is not None:
                for doc in docs_relatorio.findall('PeticaoDocsRelatorioFinal'):
                    self._insert_documento(None, comissao_db_id, doc, 'DocsRelatorioFinal')
    
    def _process_documentos(self, petition: ET.Element, peticao_db_id: int):
        """Process main petition documents"""
        documentos = petition.find('Documentos')
        if documentos is not None:
            for doc in documentos.findall('PeticaoDocsOut'):
                self._insert_documento(peticao_db_id, None, doc, 'Documentos')
    
    def _insert_documento(self, peticao_id: Optional[int], comissao_peticao_id: Optional[int], 
                         doc: ET.Element, categoria: str):
        """Insert document data"""
        titulo_documento = self._get_text_value(doc, 'TituloDocumento')
        data_documento = self._parse_date(self._get_text_value(doc, 'DataDocumento'))
        tipo_documento = self._get_text_value(doc, 'TipoDocumento')
        url = self._get_text_value(doc, 'URL')
        
        self.cursor.execute("""
            INSERT INTO peticoes_documentos (
                peticao_id, comissao_peticao_id, tipo_documento_categoria,
                titulo_documento, data_documento, tipo_documento, url
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (peticao_id, comissao_peticao_id, categoria, titulo_documento, data_documento, tipo_documento, url))
    
    def _process_intervencoes(self, petition: ET.Element, peticao_db_id: int):
        """Process interventions/debates"""
        # Clear existing interventions
        self.cursor.execute("DELETE FROM peticoes_intervencoes WHERE peticao_id = ?", (peticao_db_id,))
        
        intervencoes = petition.find('Intervencoes')
        if intervencoes is not None:
            for intervencao in intervencoes.findall('PeticaoIntervencoesOut'):
                intervencao_db_id = self._process_single_intervencao(intervencao, peticao_db_id)
                if intervencao_db_id:
                    self._process_oradores(intervencao, intervencao_db_id)
    
    def _process_single_intervencao(self, intervencao: ET.Element, peticao_db_id: int) -> Optional[int]:
        """Process single intervention"""
        data_reuniao_plenaria = self._parse_date(self._get_text_value(intervencao, 'DataReuniaoPlenaria'))
        
        self.cursor.execute("""
            INSERT INTO peticoes_intervencoes (peticao_id, data_reuniao_plenaria)
            VALUES (?, ?)
        """, (peticao_db_id, data_reuniao_plenaria))
        
        return self.cursor.lastrowid
    
    def _process_oradores(self, intervencao: ET.Element, intervencao_db_id: int):
        """Process speakers in intervention"""
        oradores = intervencao.find('Oradores')
        if oradores is not None:
            for orador in oradores.findall('PeticaoOradoresOut'):
                orador_db_id = self._process_single_orador(orador, intervencao_db_id)
                if orador_db_id:
                    self._process_orador_publicacoes(orador, orador_db_id)
    
    def _process_single_orador(self, orador: ET.Element, intervencao_db_id: int) -> Optional[int]:
        """Process single speaker"""
        fase_sessao = self._get_text_value(orador, 'FaseSessao')
        sumario = self._get_text_value(orador, 'Sumario')
        convidados = self._get_text_value(orador, 'Convidados')
        membros_governo = self._get_text_value(orador, 'MembrosGoverno')
        
        self.cursor.execute("""
            INSERT INTO peticoes_oradores (
                intervencao_id, fase_sessao, sumario, convidados, membros_governo
            ) VALUES (?, ?, ?, ?, ?)
        """, (intervencao_db_id, fase_sessao, sumario, convidados, membros_governo))
        
        return self.cursor.lastrowid
    
    def _process_orador_publicacoes(self, orador: ET.Element, orador_db_id: int):
        """Process speaker publications"""
        publicacao = orador.find('Publicacao')
        if publicacao is not None:
            for pub in publicacao.findall('pt_gov_ar_objectos_PublicacoesOut'):
                pub_nr = self._get_int_value(pub, 'pubNr')
                pub_tipo = self._get_text_value(pub, 'pubTipo')
                pub_tp = self._get_text_value(pub, 'pubTp')
                pub_leg = self._get_text_value(pub, 'pubLeg')
                pub_sl = self._get_int_value(pub, 'pubSL')
                pub_dt = self._parse_date(self._get_text_value(pub, 'pubdt'))
                id_int = self._get_int_value(pub, 'idInt')
                url_diario = self._get_text_value(pub, 'URLDiario')
                
                # Handle page numbers
                pag_text = None
                pag_elem = pub.find('pag')
                if pag_elem is not None:
                    string_elems = pag_elem.findall('string')
                    if string_elems:
                        pag_text = ', '.join([s.text for s in string_elems if s.text])
                
                self.cursor.execute("""
                    INSERT INTO peticoes_oradores_publicacoes (
                        orador_id, pub_nr, pub_tipo, pub_tp, pub_leg, pub_sl,
                        pub_dt, pag, id_int, url_diario
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (orador_db_id, pub_nr, pub_tipo, pub_tp, pub_leg, pub_sl, pub_dt, pag_text, id_int, url_diario))
    
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
            
            # Handle datetime format: DD/MM/YYYY HH:MM:SS or DD/MM/YYYY
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