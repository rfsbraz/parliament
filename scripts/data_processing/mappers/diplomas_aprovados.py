"""
Approved Diplomas Mapper
========================

Schema mapper for approved diplomas files (Diplomas*.xml).
Handles parliamentary diplomas including laws, decrees, and resolutions.
"""

import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime
from typing import Dict, Optional, Set, List
import logging

from .enhanced_base_mapper import SchemaMapper, SchemaError

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import DiplomaAprovado, DiplomaPublicacao, DiplomaIniciativa, DiplomaOrcamContasGerencia, Legislatura

logger = logging.getLogger(__name__)


class DiplomasAprovadosMapper(SchemaMapper):
    """Schema mapper for approved diplomas files"""
    
    def __init__(self, session):
        # Accept SQLAlchemy session directly (passed by unified importer)
        super().__init__(session)
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # Root elements
            'ArrayOfDiplomaOut',
            'ArrayOfDiplomaOut.DiplomaOut',
            
            # Main diploma fields
            'ArrayOfDiplomaOut.DiplomaOut.Id',
            'ArrayOfDiplomaOut.DiplomaOut.Numero',
            'ArrayOfDiplomaOut.DiplomaOut.Titulo',
            'ArrayOfDiplomaOut.DiplomaOut.Tipo',
            'ArrayOfDiplomaOut.DiplomaOut.Legislatura',
            'ArrayOfDiplomaOut.DiplomaOut.Sessao',
            'ArrayOfDiplomaOut.DiplomaOut.AnoCivil',
            'ArrayOfDiplomaOut.DiplomaOut.LinkTexto',
            'ArrayOfDiplomaOut.DiplomaOut.Numero2',
            'ArrayOfDiplomaOut.DiplomaOut.Observacoes',
            'ArrayOfDiplomaOut.DiplomaOut.Tp',
            'ArrayOfDiplomaOut.DiplomaOut.Versao',  # IV Legislature field
            
            # Activities
            'ArrayOfDiplomaOut.DiplomaOut.Actividades',
            'ArrayOfDiplomaOut.DiplomaOut.Actividades.string',
            
            # Publication data
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.idPag',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.supl',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.obs',
            'ArrayOfDiplomaOut.DiplomaOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pagFinalDiarioSupl',
            
            # Initiative data
            'ArrayOfDiplomaOut.DiplomaOut.Iniciativas',
            'ArrayOfDiplomaOut.DiplomaOut.Iniciativas.DiplomaIniciativaOut',
            'ArrayOfDiplomaOut.DiplomaOut.Iniciativas.DiplomaIniciativaOut.IniNr',
            'ArrayOfDiplomaOut.DiplomaOut.Iniciativas.DiplomaIniciativaOut.IniTipo',
            'ArrayOfDiplomaOut.DiplomaOut.Iniciativas.DiplomaIniciativaOut.IniLinkTexto',
            'ArrayOfDiplomaOut.DiplomaOut.Iniciativas.DiplomaIniciativaOut.IniId',
            
            # XIII Legislature fields
            # Attachments
            'ArrayOfDiplomaOut.DiplomaOut.Anexos',
            'ArrayOfDiplomaOut.DiplomaOut.Anexos.string',
            
            # Budget/Management Accounts
            'ArrayOfDiplomaOut.DiplomaOut.OrcamContasGerencia',
            'ArrayOfDiplomaOut.DiplomaOut.OrcamContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut',
            'ArrayOfDiplomaOut.DiplomaOut.OrcamContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.id',
            'ArrayOfDiplomaOut.DiplomaOut.OrcamContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.leg',
            'ArrayOfDiplomaOut.DiplomaOut.OrcamContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.tp',
            'ArrayOfDiplomaOut.DiplomaOut.OrcamContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.titulo',
            'ArrayOfDiplomaOut.DiplomaOut.OrcamContasGerencia.pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut.tipo'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map approved diplomas to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        try:
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Extract legislatura from filename or XML
            legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
        
            # Process diplomas
            for diploma in xml_root.findall('.//DiplomaOut'):
                try:
                    success = self._process_diploma(diploma, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Diploma processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
                    self.session.rollback()
                    if strict_mode:
                        logger.error("STRICT MODE: Exiting due to diploma processing error")
                        raise SchemaError(f"Diploma processing failed in strict mode: {e}")
                    continue
            
            # Commit all changes
            self.session.commit()
            return results
            
        except Exception as e:
            error_msg = f"Critical error processing diplomas: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            self.session.rollback()
            raise SchemaError(f"Critical diploma processing error: {e}")
    
    
    def _process_diploma(self, diploma: ET.Element, legislatura: Legislatura) -> bool:
        """Process individual diploma"""
        try:
            # Extract basic fields
            diploma_id = self._get_int_value(diploma, 'Id')
            numero = self._get_int_value(diploma, 'Numero')
            numero2 = self._get_text_value(diploma, 'Numero2')  # Missing field from schema
            titulo = self._get_text_value(diploma, 'Titulo')
            tipo = self._get_text_value(diploma, 'Tipo')
            sessao = self._get_int_value(diploma, 'Sessao')
            ano_civil = self._get_int_value(diploma, 'AnoCivil')
            link_texto = self._get_text_value(diploma, 'LinkTexto')
            observacoes = self._get_text_value(diploma, 'Observacoes')
            tp = self._get_text_value(diploma, 'Tp')
            versao = self._get_text_value(diploma, 'Versao')
            
            # XIII Legislature fields
            anexos = self._extract_string_array(diploma, 'Anexos')
            
            if not titulo:
                logger.warning("Missing required field: titulo")
                return False
            
            # Check if diploma already exists
            existing = None
            if diploma_id:
                existing = self.session.query(DiplomaAprovado).filter_by(
                    diploma_id=diploma_id
                ).first()
            
            if existing:
                # Update existing record
                existing.numero = numero
                existing.numero2 = numero2
                existing.titulo = titulo
                existing.tipo = tipo
                existing.sessao = sessao
                existing.ano_civil = ano_civil
                existing.link_texto = link_texto
                existing.observacoes = observacoes
                existing.tp = tp
                existing.versao = versao
                existing.anexos = anexos
                existing.legislatura_id = legislatura.id
            else:
                # Create new diploma record
                diploma_record = DiplomaAprovado(
                    diploma_id=diploma_id,
                    numero=numero,
                    numero2=numero2,
                    titulo=titulo,
                    tipo=tipo,
                    sessao=sessao,
                    ano_civil=ano_civil,
                    link_texto=link_texto,
                    observacoes=observacoes,
                    tp=tp,
                    versao=versao,
                    anexos=anexos,
                    legislatura_id=legislatura.id
                )
                self.session.add(diploma_record)
                self.session.flush()  # Get the ID
                existing = diploma_record
            
            # Process publications
            self._process_diploma_publications(diploma, existing)
            
            # Process initiatives
            self._process_diploma_initiatives(diploma, existing)
            
            # Process budget/management accounts (XIII Legislature)
            self._process_orcam_contas_gerencia(diploma, existing)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing diploma: {e}")
            return False
    
    def _extract_string_array(self, parent: ET.Element, tag_name: str) -> Optional[str]:
        """Extract string array from XML element and return as comma-separated string"""
        element = parent.find(tag_name)
        if element is not None:
            strings = element.findall('string')
            if strings:
                return ', '.join([s.text for s in strings if s.text])
            elif element.text:
                return element.text
        return None
    
    def _map_diploma_type(self, tipo: str, tp: str) -> str:
        """Map diploma type to standard activity type"""
        if not tipo:
            return 'DIPLOMA'
        
        tipo_upper = tipo.upper()
        
        if 'LEI' in tipo_upper:
            return 'LEI'
        elif 'DECRETO' in tipo_upper:
            return 'DECRETO'
        elif 'RESOLUÇÃO' in tipo_upper or 'RESOLUCAO' in tipo_upper:
            return 'RESOLUCAO'
        elif 'DELIBERAÇÃO' in tipo_upper or 'DELIBERACAO' in tipo_upper:
            return 'DELIBERACAO'
        else:
            return 'DIPLOMA'
    
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
    
    def _process_diploma_publications(self, diploma: ET.Element, diploma_record: DiplomaAprovado):
        """Process publications for diploma"""
        publicacao = diploma.find('Publicacao')
        if publicacao is not None:
            for pub in publicacao.findall('pt_gov_ar_objectos_PublicacoesOut'):
                pub_nr = self._get_int_value(pub, 'pubNr')
                pub_tipo = self._get_text_value(pub, 'pubTipo')
                pub_tp = self._get_text_value(pub, 'pubTp')
                pub_leg = self._get_text_value(pub, 'pubLeg')
                pub_sl = self._get_int_value(pub, 'pubSL')
                pub_dt = self._parse_date(self._get_text_value(pub, 'pubdt'))
                id_pag = self._get_int_value(pub, 'idPag')
                url_diario = self._get_text_value(pub, 'URLDiario')
                supl = self._get_text_value(pub, 'supl')
                obs = self._get_text_value(pub, 'obs')
                pag_final_diario_supl = self._get_text_value(pub, 'pagFinalDiarioSupl')
                
                # Handle page numbers (can be in <pag><string> elements)
                pag_text = None
                pag_elem = pub.find('pag')
                if pag_elem is not None:
                    string_elems = pag_elem.findall('string')
                    if string_elems:
                        pag_text = ', '.join([s.text for s in string_elems if s.text])
                
                publicacao_record = DiplomaPublicacao(
                    diploma_id=diploma_record.id,
                    pub_nr=pub_nr,
                    pub_tipo=pub_tipo,
                    pub_tp=pub_tp,
                    pub_leg=pub_leg,
                    pub_sl=pub_sl,
                    pub_dt=pub_dt,
                    pag=pag_text,
                    id_pag=id_pag,
                    url_diario=url_diario,
                    supl=supl,
                    obs=obs,
                    pag_final_diario_supl=pag_final_diario_supl
                )
                self.session.add(publicacao_record)
    
    def _process_diploma_initiatives(self, diploma: ET.Element, diploma_record: DiplomaAprovado):
        """Process initiatives for diploma"""
        iniciativas = diploma.find('Iniciativas')
        if iniciativas is not None:
            for ini in iniciativas.findall('DiplomaIniciativaOut'):
                ini_nr = self._get_int_value(ini, 'IniNr')
                ini_tipo = self._get_text_value(ini, 'IniTipo')
                ini_link_texto = self._get_text_value(ini, 'IniLinkTexto')
                ini_id = self._get_int_value(ini, 'IniId')
                
                iniciativa_record = DiplomaIniciativa(
                    diploma_id=diploma_record.id,
                    ini_nr=ini_nr,
                    ini_tipo=ini_tipo,
                    ini_link_texto=ini_link_texto,
                    ini_id=ini_id
                )
                self.session.add(iniciativa_record)
    
    def _process_orcam_contas_gerencia(self, diploma: ET.Element, diploma_record: DiplomaAprovado):
        """Process budget/management accounts for diploma (XIII Legislature)"""
        orcam_contas = diploma.find('OrcamContasGerencia')
        if orcam_contas is not None:
            for orcam in orcam_contas.findall('pt_gov_ar_objectos_OrcamentoContasGerencia_OrcamentoContasGerenciaOut'):
                orcam_id = self._get_int_value(orcam, 'id')
                leg = self._get_text_value(orcam, 'leg')
                tp = self._get_text_value(orcam, 'tp')
                titulo = self._get_text_value(orcam, 'titulo')
                tipo = self._get_text_value(orcam, 'tipo')
                
                # Create record if there's meaningful data
                if any([orcam_id, leg, tp, titulo, tipo]):
                    orcam_record = DiplomaOrcamContasGerencia(
                        diploma_id=diploma_record.id,
                        orcam_id=orcam_id,
                        leg=leg,
                        tp=tp,
                        titulo=titulo,
                        tipo=tipo
                    )
                    self.session.add(orcam_record)
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        try:
            # Handle ISO format: YYYY-MM-DD
            if re.match(r'\\d{4}-\\d{2}-\\d{2}', date_str):
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            # Handle datetime format: YYYY-MM-DDTHH:MM:SS
            if 'T' in date_str:
                return datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').date()
            # Handle DD/MM/YYYY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3 and len(parts[2]) == 4:
                    return datetime.strptime(f"{parts[2]}-{parts[1]}-{parts[0]}", '%Y-%m-%d').date()
            return None
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return None