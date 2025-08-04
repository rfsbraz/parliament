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

from .enhanced_base_mapper import EnhancedSchemaMapper, SchemaError

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    PerguntaRequerimento, PerguntaRequerimentoPublicacao, PerguntaRequerimentoDestinatario,
    PerguntaRequerimentoResposta, PerguntaRequerimentoAutor, Deputado, Legislatura
)

logger = logging.getLogger(__name__)


class PerguntasRequerimentosMapper(EnhancedSchemaMapper):
    """Schema mapper for parliamentary questions and requests files"""
    
    def __init__(self, session):
        # Accept SQLAlchemy session directly (passed by unified importer)
        super().__init__(session)
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # Root elements
            'ArrayOfRequerimentoOut',
            'ArrayOfRequerimentoOut.RequerimentoOut',
            
            # Main request fields
            'ArrayOfRequerimentoOut.RequerimentoOut.Id',
            'ArrayOfRequerimentoOut.RequerimentoOut.Tipo',
            'ArrayOfRequerimentoOut.RequerimentoOut.Nr',
            'ArrayOfRequerimentoOut.RequerimentoOut.ReqTipo',
            'ArrayOfRequerimentoOut.RequerimentoOut.Legislatura',
            'ArrayOfRequerimentoOut.RequerimentoOut.Sessao',
            'ArrayOfRequerimentoOut.RequerimentoOut.Assunto',
            'ArrayOfRequerimentoOut.RequerimentoOut.DtEntrada',
            'ArrayOfRequerimentoOut.RequerimentoOut.DataEnvio',
            'ArrayOfRequerimentoOut.RequerimentoOut.Observacoes',
            'ArrayOfRequerimentoOut.RequerimentoOut.Ficheiro',
            
            # Publication section
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.idPag',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.supl',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.obs',
            'ArrayOfRequerimentoOut.RequerimentoOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pagFinalDiarioSupl',
            
            # Recipients section
            'ArrayOfRequerimentoOut.RequerimentoOut.Destinatarios',
            'ArrayOfRequerimentoOut.RequerimentoOut.Destinatarios.pt_gov_ar_objectos_requerimentos_DestinatariosOut',
            'ArrayOfRequerimentoOut.RequerimentoOut.Destinatarios.pt_gov_ar_objectos_requerimentos_DestinatariosOut.nomeEntidade',
            'ArrayOfRequerimentoOut.RequerimentoOut.Destinatarios.pt_gov_ar_objectos_requerimentos_DestinatariosOut.dataEnvio',
            
            # Responses section
            'ArrayOfRequerimentoOut.RequerimentoOut.Destinatarios.pt_gov_ar_objectos_requerimentos_DestinatariosOut.respostas',
            'ArrayOfRequerimentoOut.RequerimentoOut.Destinatarios.pt_gov_ar_objectos_requerimentos_DestinatariosOut.respostas.pt_gov_ar_objectos_requerimentos_RespostasOut',
            'ArrayOfRequerimentoOut.RequerimentoOut.Destinatarios.pt_gov_ar_objectos_requerimentos_DestinatariosOut.respostas.pt_gov_ar_objectos_requerimentos_RespostasOut.entidade',
            'ArrayOfRequerimentoOut.RequerimentoOut.Destinatarios.pt_gov_ar_objectos_requerimentos_DestinatariosOut.respostas.pt_gov_ar_objectos_requerimentos_RespostasOut.dataResposta',
            'ArrayOfRequerimentoOut.RequerimentoOut.Destinatarios.pt_gov_ar_objectos_requerimentos_DestinatariosOut.respostas.pt_gov_ar_objectos_requerimentos_RespostasOut.ficheiro',
            'ArrayOfRequerimentoOut.RequerimentoOut.Destinatarios.pt_gov_ar_objectos_requerimentos_DestinatariosOut.respostas.pt_gov_ar_objectos_requerimentos_RespostasOut.docRemetida',
            
            # Authors section
            'ArrayOfRequerimentoOut.RequerimentoOut.Autores',
            'ArrayOfRequerimentoOut.RequerimentoOut.Autores.pt_gov_ar_objectos_iniciativas_AutoresDeputadosOut',
            'ArrayOfRequerimentoOut.RequerimentoOut.Autores.pt_gov_ar_objectos_iniciativas_AutoresDeputadosOut.idCadastro',
            'ArrayOfRequerimentoOut.RequerimentoOut.Autores.pt_gov_ar_objectos_iniciativas_AutoresDeputadosOut.nome',
            'ArrayOfRequerimentoOut.RequerimentoOut.Autores.pt_gov_ar_objectos_iniciativas_AutoresDeputadosOut.GP'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map parliamentary questions and requests to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        # Store file_info for use in other methods
        self.file_info = file_info
        
        try:
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Extract legislatura from filename or XML
            legislatura_sigla = self._extract_legislatura(file_info['file_path'], xml_root)
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
        
            # Process requests/questions
            for request in xml_root.findall('.//RequerimentoOut'):
                try:
                    success = self._process_request(request, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Request processing error: {str(e)}"
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
            error_msg = f"Critical error processing requests: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            logger.error("Data integrity issue detected - exiting immediately")
            import sys
            sys.exit(1)
            return results
    
    
    def _process_request(self, request: ET.Element, legislatura: Legislatura) -> bool:
        """Process individual request/question"""
        try:
            # Extract basic fields
            req_id = self._get_int_value(request, 'Id')
            tipo = self._get_text_value(request, 'Tipo')
            nr = self._get_int_value(request, 'Nr')
            req_tipo = self._get_text_value(request, 'ReqTipo')
            sessao = self._get_int_value(request, 'Sessao')
            assunto = self._get_text_value(request, 'Assunto')
            dt_entrada_str = self._get_text_value(request, 'DtEntrada')
            data_envio_str = self._get_text_value(request, 'DataEnvio')
            observacoes = self._get_text_value(request, 'Observacoes')
            ficheiro = self._get_text_value(request, 'Ficheiro')
            
            if not assunto:
                logger.warning("Missing required field: Assunto")
                return False
            
            # Parse dates
            dt_entrada = self._parse_date(dt_entrada_str)
            data_envio = self._parse_date(data_envio_str)
            
            # Check if request already exists
            existing = None
            if req_id:
                existing = self.session.query(PerguntaRequerimento).filter_by(
                    requerimento_id=req_id
                ).first()
            
            if existing:
                # Update existing record
                existing.tipo = tipo
                existing.nr = nr
                existing.req_tipo = req_tipo
                existing.sessao = sessao
                existing.assunto = assunto
                existing.dt_entrada = dt_entrada
                existing.data_envio = data_envio
                existing.observacoes = observacoes
                existing.ficheiro = ficheiro
                existing.legislatura_id = legislatura.id
            else:
                # Create new record
                pergunta_req = PerguntaRequerimento(
                    requerimento_id=req_id,
                    tipo=tipo,
                    nr=nr,
                    req_tipo=req_tipo,
                    sessao=sessao,
                    assunto=assunto,
                    dt_entrada=dt_entrada,
                    data_envio=data_envio,
                    observacoes=observacoes,
                    ficheiro=ficheiro,
                    legislatura_id=legislatura.id
                )
                self.session.add(pergunta_req)
                self.session.flush()  # Get the ID
                existing = pergunta_req
            
            # Process related data
            self._process_request_publications(request, existing)
            self._process_request_destinatarios(request, existing)
            self._process_request_authors(request, existing)
            
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
    
    def _process_request_publications(self, request: ET.Element, pergunta_req: PerguntaRequerimento):
        """Process publications for request"""
        publicacao = request.find('Publicacao')
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
                
                # Handle page numbers
                pag_text = None
                pag_elem = pub.find('pag')
                if pag_elem is not None:
                    string_elems = pag_elem.findall('string')
                    if string_elems:
                        pag_text = ', '.join([s.text for s in string_elems if s.text])
                
                publicacao_record = PerguntaRequerimentoPublicacao(
                    pergunta_requerimento_id=pergunta_req.id,
                    pub_nr=pub_nr,
                    pub_tipo=pub_tipo,
                    pub_tp=pub_tp,
                    pub_leg=pub_leg,
                    pub_sl=pub_sl,
                    pub_dt=pub_dt,
                    id_pag=id_pag,
                    url_diario=url_diario,
                    pag=pag_text,
                    supl=supl,
                    obs=obs,
                    pag_final_diario_supl=pag_final_diario_supl
                )
                self.session.add(publicacao_record)
    
    def _process_request_destinatarios(self, request: ET.Element, pergunta_req: PerguntaRequerimento):
        """Process recipients for request"""
        destinatarios = request.find('Destinatarios')
        if destinatarios is not None:
            for dest in destinatarios.findall('pt_gov_ar_objectos_requerimentos_DestinatariosOut'):
                nome_entidade = self._get_text_value(dest, 'nomeEntidade')
                data_envio = self._parse_date(self._get_text_value(dest, 'dataEnvio'))
                
                destinatario_record = PerguntaRequerimentoDestinatario(
                    pergunta_requerimento_id=pergunta_req.id,
                    nome_entidade=nome_entidade,
                    data_envio=data_envio
                )
                self.session.add(destinatario_record)
                self.session.flush()  # Get the ID
                
                # Process responses
                respostas = dest.find('respostas')
                if respostas is not None:
                    for resp in respostas.findall('pt_gov_ar_objectos_requerimentos_RespostasOut'):
                        entidade = self._get_text_value(resp, 'entidade')
                        data_resposta = self._parse_date(self._get_text_value(resp, 'dataResposta'))
                        ficheiro = self._get_text_value(resp, 'ficheiro')
                        doc_remetida = self._get_text_value(resp, 'docRemetida')
                        
                        resposta_record = PerguntaRequerimentoResposta(
                            destinatario_id=destinatario_record.id,
                            entidade=entidade,
                            data_resposta=data_resposta,
                            ficheiro=ficheiro,
                            doc_remetida=doc_remetida
                        )
                        self.session.add(resposta_record)
    
    def _process_request_authors(self, request: ET.Element, pergunta_req: PerguntaRequerimento):
        """Process authors for request"""
        autores = request.find('Autores')
        if autores is not None:
            for autor in autores.findall('pt_gov_ar_objectos_iniciativas_AutoresDeputadosOut'):
                id_cadastro = self._get_int_value(autor, 'idCadastro')
                nome = self._get_text_value(autor, 'nome')
                gp = self._get_text_value(autor, 'GP')
                
                # Try to find the deputy
                deputado = None
                if id_cadastro:
                    deputado = self.session.query(Deputado).filter_by(id_cadastro=id_cadastro).first()
                    if not deputado and nome:
                        # Create basic deputy record
                        deputado = Deputado(
                            id_cadastro=id_cadastro,
                            nome=nome,
                            nome_completo=nome,
                            legislatura_id=self._get_legislatura_id(self.file_info),
                            ativo=True
                        )
                        self.session.add(deputado)
                        self.session.flush()
                
                autor_record = PerguntaRequerimentoAutor(
                    pergunta_requerimento_id=pergunta_req.id,
                    deputado_id=deputado.id if deputado else None,
                    id_cadastro=id_cadastro,
                    nome=nome,
                    gp=gp
                )
                self.session.add(autor_record)