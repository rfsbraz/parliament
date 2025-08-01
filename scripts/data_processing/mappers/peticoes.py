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

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    PeticaoParlamentar, PeticaoPublicacao, PeticaoComissao, PeticaoRelator,
    PeticaoRelatorioFinal, PeticaoDocumento, PeticaoIntervencao, PeticaoOrador,
    PeticaoOradorPublicacao, Legislatura
)

logger = logging.getLogger(__name__)


class PeticoesMapper(SchemaMapper):
    """Comprehensive schema mapper for parliamentary petition files"""
    
    def __init__(self, session):
        # Accept SQLAlchemy session directly (passed by unified importer)
        super().__init__(session)
    
    def get_expected_fields(self) -> Set[str]:
        # Complete field list with full XML hierarchy paths to avoid field name conflicts
        return {
            # Root elements
            'ArrayOfPeticaoOut',
            'ArrayOfPeticaoOut.PeticaoOut',
            
            # Core petition fields - with full hierarchy
            'ArrayOfPeticaoOut.PeticaoOut.PetId',
            'ArrayOfPeticaoOut.PeticaoOut.PetNr', 
            'ArrayOfPeticaoOut.PeticaoOut.PetLeg',
            'ArrayOfPeticaoOut.PeticaoOut.PetSel',
            'ArrayOfPeticaoOut.PeticaoOut.PetAssunto',
            'ArrayOfPeticaoOut.PeticaoOut.PetSituacao',
            'ArrayOfPeticaoOut.PeticaoOut.PetNrAssinaturas',
            'ArrayOfPeticaoOut.PeticaoOut.PetDataEntrada',
            'ArrayOfPeticaoOut.PeticaoOut.PetActividadeId',
            'ArrayOfPeticaoOut.PeticaoOut.PetAutor',
            'ArrayOfPeticaoOut.PeticaoOut.DataDebate',
            
            # Publications - with full hierarchy
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoPeticao',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoPeticao.pt_gov_ar_objectos_PublicacoesOut',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoPeticao.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoPeticao.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoPeticao.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoPeticao.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoPeticao.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoPeticao.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoPeticao.pt_gov_ar_objectos_PublicacoesOut.pag',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoPeticao.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoPeticao.pt_gov_ar_objectos_PublicacoesOut.idPag',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoPeticao.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoDebate',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pag',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.idPag',
            'ArrayOfPeticaoOut.PeticaoOut.PublicacaoDebate.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            
            # Committee data - with full hierarchy
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Legislatura',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Numero',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.IdComissao',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Nome',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Admissibilidade',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DataAdmissibilidade',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DataEnvioPAR',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DataArquivo',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Situacao',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DataReaberta',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DataBaixaComissao',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Transitada',
            
            # Reporters - with full hierarchy
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Relatores',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Relatores.pt_gov_ar_objectos_RelatoresOut',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Relatores.pt_gov_ar_objectos_RelatoresOut.id',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Relatores.pt_gov_ar_objectos_RelatoresOut.nome',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Relatores.pt_gov_ar_objectos_RelatoresOut.gp',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Relatores.pt_gov_ar_objectos_RelatoresOut.dataNomeacao',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.Relatores.pt_gov_ar_objectos_RelatoresOut.dataCessacao',
            
            # Final reports - with full hierarchy
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DadosRelatorioFinal',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DadosRelatorioFinal.pt_gov_ar_objectos_peticoes_DadosRelatorioFinalOut',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DadosRelatorioFinal.pt_gov_ar_objectos_peticoes_DadosRelatorioFinalOut.data',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DadosRelatorioFinal.pt_gov_ar_objectos_peticoes_DadosRelatorioFinalOut.votacao',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.RelatorioFinal',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.RelatorioFinal.string',
            
            # Documents - with full hierarchy
            'ArrayOfPeticaoOut.PeticaoOut.Documentos',
            'ArrayOfPeticaoOut.PeticaoOut.Documentos.PeticaoDocsOut',
            'ArrayOfPeticaoOut.PeticaoOut.Documentos.PeticaoDocsOut.TituloDocumento',
            'ArrayOfPeticaoOut.PeticaoOut.Documentos.PeticaoDocsOut.DataDocumento',
            'ArrayOfPeticaoOut.PeticaoOut.Documentos.PeticaoDocsOut.TipoDocumento',
            'ArrayOfPeticaoOut.PeticaoOut.Documentos.PeticaoDocsOut.URL',
            
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DocumentosPeticao',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DocumentosPeticao.DocsRelatorioFinal',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DocumentosPeticao.DocsRelatorioFinal.PeticaoDocsRelatorioFinal',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DocumentosPeticao.DocsRelatorioFinal.PeticaoDocsRelatorioFinal.TituloDocumento',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DocumentosPeticao.DocsRelatorioFinal.PeticaoDocsRelatorioFinal.DataDocumento',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DocumentosPeticao.DocsRelatorioFinal.PeticaoDocsRelatorioFinal.TipoDocumento',
            'ArrayOfPeticaoOut.PeticaoOut.DadosComissao.ComissoesPetOut.DocumentosPeticao.DocsRelatorioFinal.PeticaoDocsRelatorioFinal.URL',
            
            # Interventions - with full hierarchy
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.DataReuniaoPlenaria',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.FaseSessao',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Sumario',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Convidados',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.MembrosGoverno',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Publicacao',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.idInt',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag',
            'ArrayOfPeticaoOut.PeticaoOut.Intervencoes.PeticaoIntervencoesOut.Oradores.PeticaoOradoresOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag.string'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map parliamentary petitions with complete structure to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        try:
            # Validate schema coverage with strict mode support
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Extract legislatura from filename or XML
            legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
            
            # Process petitions
            for petition in xml_root.findall('.//PeticaoOut'):
                try:
                    success = self._process_petition_complete(petition, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Petition processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
                    logger.error("Data integrity issue detected - exiting immediately")
                    import sys
                    sys.exit(1)
            
            # Commit all changes
            self.session.commit()
            return results
            
        except Exception as e:
            error_msg = f"Critical error processing petitions: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            logger.error("Data integrity issue detected - exiting immediately")
            import sys
            sys.exit(1)
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
    
    def _process_petition_complete(self, petition: ET.Element, legislatura: Legislatura) -> bool:
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
            
            # Check if petition already exists
            existing = None
            if pet_id:
                existing = self.session.query(PeticaoParlamentar).filter_by(pet_id=pet_id).first()
            
            if existing:
                # Update existing petition
                existing.pet_nr = pet_nr
                existing.pet_leg = pet_leg
                existing.pet_sel = pet_sel
                existing.pet_assunto = pet_assunto
                existing.pet_situacao = pet_situacao
                existing.pet_nr_assinaturas = pet_nr_assinaturas
                existing.pet_data_entrada = pet_data_entrada
                existing.pet_atividade_id = pet_atividade_id
                existing.pet_autor = pet_autor
                existing.data_debate = data_debate
                existing.legislatura_id = legislatura.id
                existing.updated_at = datetime.now()
            else:
                # Create new petition record
                existing = PeticaoParlamentar(
                    pet_id=pet_id,
                    pet_nr=pet_nr,
                    pet_leg=pet_leg,
                    pet_sel=pet_sel,
                    pet_assunto=pet_assunto,
                    pet_situacao=pet_situacao,
                    pet_nr_assinaturas=pet_nr_assinaturas,
                    pet_data_entrada=pet_data_entrada,
                    pet_atividade_id=pet_atividade_id,
                    pet_autor=pet_autor,
                    data_debate=data_debate,
                    legislatura_id=legislatura.id,
                    updated_at=datetime.now()
                )
                self.session.add(existing)
                self.session.flush()  # Get the ID
            
            # Process all related structures
            self._process_publicacoes(petition, existing)
            self._process_dados_comissao(petition, existing)
            self._process_documentos(petition, existing)
            self._process_intervencoes(petition, existing)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing petition {pet_id}: {e}")
            return False
    
    
    def _process_publicacoes(self, petition: ET.Element, peticao_obj: PeticaoParlamentar):
        """Process all publication types for petition"""
        # Clear existing publications
        for publicacao in peticao_obj.publicacoes:
            self.session.delete(publicacao)
        
        # PublicacaoPeticao
        pub_peticao = petition.find('PublicacaoPeticao')
        if pub_peticao is not None:
            for pub in pub_peticao.findall('pt_gov_ar_objectos_PublicacoesOut'):
                self._insert_publicacao(peticao_obj, pub, 'PublicacaoPeticao')
        
        # PublicacaoDebate
        pub_debate = petition.find('PublicacaoDebate')
        if pub_debate is not None:
            for pub in pub_debate.findall('pt_gov_ar_objectos_PublicacoesOut'):
                self._insert_publicacao(peticao_obj, pub, 'PublicacaoDebate')
    
    def _insert_publicacao(self, peticao_obj: PeticaoParlamentar, pub: ET.Element, tipo: str):
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
        
        publicacao = PeticaoPublicacao(
            peticao_id=peticao_obj.id,
            tipo=tipo,
            pub_nr=pub_nr,
            pub_tipo=pub_tipo,
            pub_tp=pub_tp,
            pub_leg=pub_leg,
            pub_sl=pub_sl,
            pub_dt=pub_dt,
            pag=pag_text,
            id_pag=id_pag,
            url_diario=url_diario
        )
        self.session.add(publicacao)
    
    def _process_dados_comissao(self, petition: ET.Element, peticao_obj: PeticaoParlamentar):
        """Process committee data (can be multiple across legislaturas)"""
        # Clear existing committee data
        for comissao in peticao_obj.comissoes:
            self.session.delete(comissao)
        
        dados_comissao = petition.find('DadosComissao')
        if dados_comissao is not None:
            for comissao in dados_comissao.findall('ComissoesPetOut'):
                comissao_obj = self._process_single_comissao(comissao, peticao_obj)
                if comissao_obj:
                    self._process_comissao_details(comissao, comissao_obj)
    
    def _process_single_comissao(self, comissao: ET.Element, peticao_obj: PeticaoParlamentar) -> Optional[PeticaoComissao]:
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
        
        comissao_obj = PeticaoComissao(
            peticao_id=peticao_obj.id,
            legislatura=legislatura,
            numero=numero,
            id_comissao=id_comissao,
            nome=nome,
            admissibilidade=admissibilidade,
            data_admissibilidade=data_admissibilidade,
            data_envio_par=data_envio_par,
            data_arquivo=data_arquivo,
            situacao=situacao,
            data_reaberta=data_reaberta,
            data_baixa_comissao=data_baixa_comissao,
            transitada=transitada  
        )
        
        self.session.add(comissao_obj)
        self.session.flush()  # Get the ID
        return comissao_obj
    
    def _process_comissao_details(self, comissao: ET.Element, comissao_obj: PeticaoComissao):
        """Process detailed committee structures"""
        # Reporters
        self._process_relatores(comissao, comissao_obj)
        
        # Final reports
        self._process_dados_relatorio_final(comissao, comissao_obj)
        
        # Committee documents
        self._process_documentos_comissao(comissao, comissao_obj)
    
    def _process_relatores(self, comissao: ET.Element, comissao_obj: PeticaoComissao):
        """Process reporters for committee"""
        relatores = comissao.find('Relatores')
        if relatores is not None:
            for relator in relatores.findall('pt_gov_ar_objectos_RelatoresOut'):
                relator_id = self._get_int_value(relator, 'id')
                nome = self._get_text_value(relator, 'nome')
                gp = self._get_text_value(relator, 'gp')
                data_nomeacao = self._parse_date(self._get_text_value(relator, 'dataNomeacao'))
                data_cessacao = self._parse_date(self._get_text_value(relator, 'dataCessacao'))
                
                relator_obj = PeticaoRelator(
                    comissao_peticao_id=comissao_obj.id,
                    relator_id=relator_id,
                    nome=nome,
                    gp=gp,
                    data_nomeacao=data_nomeacao,
                    data_cessacao=data_cessacao
                )
                self.session.add(relator_obj)
    
    def _process_dados_relatorio_final(self, comissao: ET.Element, comissao_obj: PeticaoComissao):
        """Process final report data"""
        dados_relatorio = comissao.find('DadosRelatorioFinal')
        if dados_relatorio is not None:
            for relatorio in dados_relatorio.findall('pt_gov_ar_objectos_peticoes_DadosRelatorioFinalOut'):
                data_relatorio = self._parse_date(self._get_text_value(relatorio, 'data'))
                votacao = self._get_text_value(relatorio, 'votacao')
                
                relatorio_obj = PeticaoRelatorioFinal(
                    comissao_peticao_id=comissao_obj.id,
                    data_relatorio=data_relatorio,
                    votacao=votacao
                )
                self.session.add(relatorio_obj)
        
        # Process RelatorioFinal string elements
        relatorio_final = comissao.find('RelatorioFinal')
        if relatorio_final is not None:
            for string_elem in relatorio_final.findall('string'):
                relatorio_id = string_elem.text
                if relatorio_id:
                    relatorio_obj = PeticaoRelatorioFinal(
                        comissao_peticao_id=comissao_obj.id,
                        relatorio_final_id=relatorio_id
                    )
                    self.session.add(relatorio_obj)
    
    def _process_documentos_comissao(self, comissao: ET.Element, comissao_obj: PeticaoComissao):
        """Process committee-specific documents"""
        documentos_peticao = comissao.find('DocumentosPeticao')
        if documentos_peticao is not None:
            # DocsRelatorioFinal
            docs_relatorio = documentos_peticao.find('DocsRelatorioFinal')
            if docs_relatorio is not None:
                for doc in docs_relatorio.findall('PeticaoDocsRelatorioFinal'):
                    self._insert_documento(None, comissao_obj, doc, 'DocsRelatorioFinal')
    
    def _process_documentos(self, petition: ET.Element, peticao_obj: PeticaoParlamentar):
        """Process main petition documents"""
        documentos = petition.find('Documentos')
        if documentos is not None:
            for doc in documentos.findall('PeticaoDocsOut'):
                self._insert_documento(peticao_obj, None, doc, 'Documentos')
    
    def _insert_documento(self, peticao_obj: Optional[PeticaoParlamentar], comissao_obj: Optional[PeticaoComissao], 
                         doc: ET.Element, categoria: str):
        """Insert document data"""
        titulo_documento = self._get_text_value(doc, 'TituloDocumento')
        data_documento = self._parse_date(self._get_text_value(doc, 'DataDocumento'))
        tipo_documento = self._get_text_value(doc, 'TipoDocumento')
        url = self._get_text_value(doc, 'URL')
        
        documento_obj = PeticaoDocumento(
            peticao_id=peticao_obj.id if peticao_obj else None,
            comissao_peticao_id=comissao_obj.id if comissao_obj else None,
            tipo_documento_categoria=categoria,
            titulo_documento=titulo_documento,
            data_documento=data_documento,
            tipo_documento=tipo_documento,
            url=url
        )
        self.session.add(documento_obj)
    
    def _process_intervencoes(self, petition: ET.Element, peticao_obj: PeticaoParlamentar):
        """Process interventions/debates"""
        # Clear existing interventions
        for intervencao in peticao_obj.intervencoes:
            self.session.delete(intervencao)
        
        intervencoes = petition.find('Intervencoes')
        if intervencoes is not None:
            for intervencao in intervencoes.findall('PeticaoIntervencoesOut'):
                intervencao_obj = self._process_single_intervencao(intervencao, peticao_obj)
                if intervencao_obj:
                    self._process_oradores(intervencao, intervencao_obj)
    
    def _process_single_intervencao(self, intervencao: ET.Element, peticao_obj: PeticaoParlamentar) -> Optional[PeticaoIntervencao]:
        """Process single intervention"""
        data_reuniao_plenaria = self._parse_date(self._get_text_value(intervencao, 'DataReuniaoPlenaria'))
        
        intervencao_obj = PeticaoIntervencao(
            peticao_id=peticao_obj.id,
            data_reuniao_plenaria=data_reuniao_plenaria
        )
        self.session.add(intervencao_obj)
        self.session.flush()  # Get the ID
        return intervencao_obj
    
    def _process_oradores(self, intervencao: ET.Element, intervencao_obj: PeticaoIntervencao):
        """Process speakers in intervention"""
        oradores = intervencao.find('Oradores')
        if oradores is not None:
            for orador in oradores.findall('PeticaoOradoresOut'):
                orador_obj = self._process_single_orador(orador, intervencao_obj)
                if orador_obj:
                    self._process_orador_publicacoes(orador, orador_obj)
    
    def _process_single_orador(self, orador: ET.Element, intervencao_obj: PeticaoIntervencao) -> Optional[PeticaoOrador]:
        """Process single speaker"""
        fase_sessao = self._get_text_value(orador, 'FaseSessao')
        sumario = self._get_text_value(orador, 'Sumario')
        convidados = self._get_text_value(orador, 'Convidados')
        membros_governo = self._get_text_value(orador, 'MembrosGoverno')
        
        orador_obj = PeticaoOrador(
            intervencao_id=intervencao_obj.id,
            fase_sessao=fase_sessao,
            sumario=sumario,
            convidados=convidados,
            membros_governo=membros_governo
        )
        self.session.add(orador_obj)
        self.session.flush()  # Get the ID
        return orador_obj
    
    def _process_orador_publicacoes(self, orador: ET.Element, orador_obj: PeticaoOrador):
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
                
                publicacao_obj = PeticaoOradorPublicacao(
                    orador_id=orador_obj.id,
                    pub_nr=pub_nr,
                    pub_tipo=pub_tipo,
                    pub_tp=pub_tp,
                    pub_leg=pub_leg,
                    pub_sl=pub_sl,
                    pub_dt=pub_dt,
                    pag=pag_text,
                    id_int=id_int,
                    url_diario=url_diario
                )
                self.session.add(publicacao_obj)
    
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
    
    def close(self):
        """Close the database session"""
        if hasattr(self, 'session') and self.session:
            self.session.close()