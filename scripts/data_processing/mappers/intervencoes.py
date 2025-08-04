"""
Parliamentary Interventions Mapper
==================================

Schema mapper for parliamentary interventions files (Intervencoes*.xml).
Handles deputy interventions in parliament sessions and maps them to the database.
"""

import xml.etree.ElementTree as ET
import os
import re
import requests
import time
from typing import Dict, Optional, Set
import logging
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

from .base_mapper import SchemaMapper, SchemaError

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    IntervencaoParlamentar, IntervencaoPublicacao, IntervencaoDeputado,
    IntervencaoMembroGoverno, IntervencaoConvidado, IntervencaoAtividadeRelacionada,
    IntervencaoIniciativa, IntervencaoAudiovisual, Deputado, Legislatura
)

logger = logging.getLogger(__name__)


class IntervencoesMapper(SchemaMapper):
    """Schema mapper for parliamentary interventions files"""
    
    def __init__(self, session):
        # Accept SQLAlchemy session directly (passed by unified importer)
        super().__init__(session)
    
    def get_expected_fields(self) -> Set[str]:
        return {
            # Root elements
            'ArrayOfDadosPesquisaIntervencoesOut',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut',
            
            # Main intervention fields
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Id',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DataReuniaoPlenaria',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.TipoIntervencao',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Resumo',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Sumario',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Legislatura',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Sessao',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Qualidade',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.FaseSessao',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.FaseDebate',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.IdDebate',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Debate',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.ActividadeId',
            
            # Deputy fields
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Deputados',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Deputados.idCadastro',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Deputados.nome',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Deputados.GP',
            
            # Government members
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.MembrosGoverno',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.MembrosGoverno.nome',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.MembrosGoverno.cargo',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.MembrosGoverno.governo',
            
            # Guests
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Convidados',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Convidados.nome',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Convidados.cargo',
            
            # Publication fields
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubdt',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubLeg',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubNr',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubSL',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTipo',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pubTp',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.idInt',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.URLDiario',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Publicacao.pt_gov_ar_objectos_PublicacoesOut.pag.string',
            
            # Related activities
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.ActividadesRelacionadas',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.ActividadesRelacionadas.id',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.ActividadesRelacionadas.tipo',
            
            # Initiatives
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Iniciativas',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Iniciativas.pt_gov_ar_objectos_intervencoes_IniciativasOut',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Iniciativas.pt_gov_ar_objectos_intervencoes_IniciativasOut.id',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Iniciativas.pt_gov_ar_objectos_intervencoes_IniciativasOut.tipo',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.Iniciativas.pt_gov_ar_objectos_intervencoes_IniciativasOut.fase',
            
            # Audiovisual data
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DadosAudiovisual',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DadosAudiovisual.pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DadosAudiovisual.pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut.duracao',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DadosAudiovisual.pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut.assunto',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DadosAudiovisual.pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut.url',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.DadosAudiovisual.pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut.tipoIntervencao',
            
            # Legacy audiovisual structure (for backward compatibility)
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.VideoAudio',
            'ArrayOfDadosPesquisaIntervencoesOut.DadosPesquisaIntervencoesOut.VideoAudio.VideoUrl'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map parliamentary interventions to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        file_path = file_info['file_path']
        filename = os.path.basename(file_path)
        skip_video_processing = file_info.get('skip_video_processing', False)
        
        try:
            # Validate schema coverage according to strict mode
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Extract legislatura from filename
            leg_match = re.search(r'Intervencoes(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)\.xml', filename)
            legislatura_sigla = leg_match.group(1) if leg_match else 'XVII'
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
            
            logger.info(f"Processing interventions from {filename} (Legislatura {legislatura_sigla})")
            
            for intervencao in xml_root.findall('.//DadosPesquisaIntervencoesOut'):
                try:
                    success = self._process_intervencao_record(intervencao, legislatura, filename, skip_video_processing)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Intervention processing error in {filename}: {str(e)}"
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
            error_msg = f"Critical error processing interventions: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            logger.error("Data integrity issue detected - exiting immediately")
            import sys
            sys.exit(1)
            return results
    
    def _process_intervencao_record(self, intervencao: ET.Element, legislatura: Legislatura, filename: str = None, skip_video_processing: bool = False) -> bool:
        """Process individual intervention record with proper normalized storage"""
        try:
            # Extract basic fields
            id_elem = intervencao.find('Id')
            legislatura_elem = intervencao.find('Legislatura')
            sessao_elem = intervencao.find('Sessao')
            tipo_elem = intervencao.find('TipoIntervencao')
            data_elem = intervencao.find('DataReuniaoPlenaria')
            qualidade_elem = intervencao.find('Qualidade')
            fase_sessao_elem = intervencao.find('FaseSessao')
            sumario_elem = intervencao.find('Sumario')
            resumo_elem = intervencao.find('Resumo')
            atividade_id_elem = intervencao.find('ActividadeId')
            id_debate_elem = intervencao.find('IdDebate')
            
            if id_elem is None or data_elem is None:
                return False
            
            try:
                intervencao_id = self._safe_int(id_elem.text)
                
                # Check if intervention already exists
                existing = None
                if intervencao_id:
                    existing = self.session.query(IntervencaoParlamentar).filter_by(
                        intervencao_id=intervencao_id
                    ).first()
                
                if existing:
                    # Update existing intervention
                    existing.legislatura_numero = legislatura_elem.text if legislatura_elem is not None else None
                    existing.sessao_numero = sessao_elem.text if sessao_elem is not None else None
                    existing.tipo_intervencao = tipo_elem.text if tipo_elem is not None else None
                    existing.data_reuniao_plenaria = self._parse_date(data_elem.text)
                    existing.qualidade = qualidade_elem.text if qualidade_elem is not None else None
                    existing.fase_sessao = fase_sessao_elem.text if fase_sessao_elem is not None else None
                    existing.sumario = sumario_elem.text if sumario_elem is not None else None
                    existing.resumo = resumo_elem.text if resumo_elem is not None else None
                    existing.atividade_id = self._safe_int(atividade_id_elem.text) if atividade_id_elem is not None else None
                    existing.id_debate = self._safe_int(id_debate_elem.text) if id_debate_elem is not None else None
                    existing.legislatura_id = legislatura.id
                else:
                    # Create new intervention record
                    intervention = IntervencaoParlamentar(
                        intervencao_id=intervencao_id,
                        legislatura_numero=legislatura_elem.text if legislatura_elem is not None else None,
                        sessao_numero=sessao_elem.text if sessao_elem is not None else None,
                        tipo_intervencao=tipo_elem.text if tipo_elem is not None else None,
                        data_reuniao_plenaria=self._parse_date(data_elem.text),
                        qualidade=qualidade_elem.text if qualidade_elem is not None else None,
                        fase_sessao=fase_sessao_elem.text if fase_sessao_elem is not None else None,
                        sumario=sumario_elem.text if sumario_elem is not None else None,
                        resumo=resumo_elem.text if resumo_elem is not None else None,
                        atividade_id=self._safe_int(atividade_id_elem.text) if atividade_id_elem is not None else None,
                        id_debate=self._safe_int(id_debate_elem.text) if id_debate_elem is not None else None,
                        legislatura_id=legislatura.id
                    )
                    self.session.add(intervention)
                    self.session.flush()  # Get the ID
                    existing = intervention
                
                # Process related data
                self._process_publicacao(intervencao, existing)
                self._process_deputados(intervencao, existing)
                self._process_membros_governo(intervencao, existing)
                self._process_convidados(intervencao, existing)
                self._process_atividades_relacionadas(intervencao, existing)
                self._process_iniciativas(intervencao, existing)
                self._process_audiovisual(intervencao, existing, filename, skip_video_processing)
                
                return True
                
            except Exception as db_error:
                logger.error(f"Database error processing intervention {id_elem.text if id_elem is not None else 'unknown'}: {db_error}")
                raise
            
        except Exception as e:
            logger.error(f"Error processing intervention: {e}")
            return False
    
    def _process_publicacao(self, intervencao: ET.Element, intervention: IntervencaoParlamentar):
        """Process publication data"""
        publicacao_elem = intervencao.find('Publicacao')
        if publicacao_elem is not None:
            pub_dados_elem = publicacao_elem.find('pt_gov_ar_objectos_PublicacoesOut')
            if pub_dados_elem is not None:
                # Extract publication fields
                pub_numero = pub_dados_elem.find('pubNr')
                pub_tipo = pub_dados_elem.find('pubTipo')
                pub_tp = pub_dados_elem.find('pubTp')
                pub_leg = pub_dados_elem.find('pubLeg')
                pub_sl = pub_dados_elem.find('pubSL')
                pub_data = pub_dados_elem.find('pubdt')
                pag_elem = pub_dados_elem.find('pag')
                id_interno = pub_dados_elem.find('idInt')
                url_diario = pub_dados_elem.find('URLDiario')
                
                # Handle page numbers (can be nested)
                paginas = None
                if pag_elem is not None:
                    string_elem = pag_elem.find('string')
                    if string_elem is not None:
                        paginas = string_elem.text
                    else:
                        paginas = pag_elem.text
                
                publicacao = IntervencaoPublicacao(
                    intervencao_id=intervention.id,
                    pub_nr=pub_numero.text if pub_numero is not None else None,
                    pub_tipo=pub_tipo.text if pub_tipo is not None else None,
                    pub_tp=pub_tp.text if pub_tp is not None else None,
                    pub_leg=pub_leg.text if pub_leg is not None else None,
                    pub_sl=self._safe_int(pub_sl.text) if pub_sl is not None else None,
                    pub_dt=self._parse_date(pub_data.text) if pub_data is not None else None,
                    pag=paginas,
                    id_int=self._safe_int(id_interno.text) if id_interno is not None else None,
                    url_diario=url_diario.text if url_diario is not None else None
                )
                self.session.add(publicacao)
    
    def _process_deputados(self, intervencao: ET.Element, intervention: IntervencaoParlamentar):
        """Process deputy data"""
        deputados_elem = intervencao.find('Deputados')
        if deputados_elem is not None:
            # Check if there's actual deputy data (not empty)
            id_cadastro_elem = deputados_elem.find('idCadastro')
            nome_elem = deputados_elem.find('nome')
            gp_elem = deputados_elem.find('GP')
            
            if id_cadastro_elem is not None or nome_elem is not None:
                deputado = IntervencaoDeputado(
                    intervencao_id=intervention.id,
                    id_cadastro=self._safe_int(id_cadastro_elem.text) if id_cadastro_elem is not None else None,
                    nome=nome_elem.text if nome_elem is not None else None,
                    gp=gp_elem.text if gp_elem is not None else None
                )
                self.session.add(deputado)
    
    def _process_membros_governo(self, intervencao: ET.Element, intervention: IntervencaoParlamentar):
        """Process government members data"""
        membros_elem = intervencao.find('MembrosGoverno')
        if membros_elem is not None:
            nome_elem = membros_elem.find('nome')
            cargo_elem = membros_elem.find('cargo')
            governo_elem = membros_elem.find('governo')
            
            if nome_elem is not None or cargo_elem is not None:
                membro_governo = IntervencaoMembroGoverno(
                    intervencao_id=intervention.id,
                    nome=nome_elem.text if nome_elem is not None else None,
                    cargo=cargo_elem.text if cargo_elem is not None else None,
                    governo=governo_elem.text if governo_elem is not None else None
                )
                self.session.add(membro_governo)
    
    def _process_convidados(self, intervencao: ET.Element, intervention: IntervencaoParlamentar):
        """Process invited guests data"""
        convidados_elem = intervencao.find('Convidados')
        if convidados_elem is not None:
            nome_elem = convidados_elem.find('nome')
            cargo_elem = convidados_elem.find('cargo')
            
            if nome_elem is not None or cargo_elem is not None:
                convidado = IntervencaoConvidado(
                    intervencao_id=intervention.id,
                    nome=nome_elem.text if nome_elem is not None else None,
                    cargo=cargo_elem.text if cargo_elem is not None else None
                )
                self.session.add(convidado)
    
    def _process_atividades_relacionadas(self, intervencao: ET.Element, intervention: IntervencaoParlamentar):
        """Process related activities data"""
        atividades_elem = intervencao.find('ActividadesRelacionadas')
        if atividades_elem is not None:
            id_elem = atividades_elem.find('id')
            tipo_elem = atividades_elem.find('tipo')
            
            if id_elem is not None or tipo_elem is not None:
                atividade = IntervencaoAtividadeRelacionada(
                    intervencao_id=intervention.id,
                    atividade_id=self._safe_int(id_elem.text) if id_elem is not None else None,
                    tipo=tipo_elem.text if tipo_elem is not None else None
                )
                self.session.add(atividade)
    
    def _process_iniciativas(self, intervencao: ET.Element, intervention: IntervencaoParlamentar):
        """Process initiatives data"""
        iniciativas_elem = intervencao.find('Iniciativas')
        if iniciativas_elem is not None:
            init_dados_elem = iniciativas_elem.find('pt_gov_ar_objectos_intervencoes_IniciativasOut')
            if init_dados_elem is not None:
                id_elem = init_dados_elem.find('id')
                tipo_elem = init_dados_elem.find('tipo')
                fase_elem = init_dados_elem.find('fase')
                
                if id_elem is not None or tipo_elem is not None:
                    iniciativa = IntervencaoIniciativa(
                        intervencao_id=intervention.id,
                        iniciativa_id=self._safe_int(id_elem.text) if id_elem is not None else None,
                        tipo=tipo_elem.text if tipo_elem is not None else None,
                        fase=fase_elem.text if fase_elem is not None else None
                    )
                    self.session.add(iniciativa)
    
    def _process_audiovisual(self, intervencao: ET.Element, intervention: IntervencaoParlamentar, filename: str = None, skip_video_processing: bool = False):
        """Process audiovisual data with thumbnail extraction"""
        video_url = None
        thumbnail_url = None
        duracao = None
        assunto = None
        tipo_intervencao = None
        
        # Try old VideoAudio structure
        video_elem = intervencao.find('VideoAudio')
        if video_elem is not None:
            video_url_elem = video_elem.find('VideoUrl')
            if video_url_elem is not None:
                video_url = video_url_elem.text
        
        # Try new DadosAudiovisual structure
        if not video_url:
            audiovisual_elem = intervencao.find('DadosAudiovisual')
            if audiovisual_elem is not None:
                dados_elem = audiovisual_elem.find('pt_gov_ar_objectos_intervencoes_DadosAudiovisualOut')
                if dados_elem is not None:
                    url_elem = dados_elem.find('url')
                    duracao_elem = dados_elem.find('duracao')
                    assunto_elem = dados_elem.find('assunto')
                    tipo_elem = dados_elem.find('tipoIntervencao')
                    
                    if url_elem is not None:
                        video_url = url_elem.text
                    if duracao_elem is not None:
                        duracao = duracao_elem.text
                    if assunto_elem is not None:
                        assunto = assunto_elem.text
                    if tipo_elem is not None:
                        tipo_intervencao = tipo_elem.text
        
        # Extract thumbnail if video URL exists and video processing is not skipped
        thumbnail_url = None
        original_video_url = video_url
        if video_url and not skip_video_processing:
            time.sleep(0.5)  # Small delay between requests
            result = self._extract_thumbnail_url_with_fallback(video_url, filename)
            if result:
                thumbnail_url, final_video_url = result
                # If the URL was cleaned during thumbnail extraction, use the cleaned version
                if final_video_url != original_video_url:
                    video_url = final_video_url
                    file_info = f" (from {filename})" if filename else ""
                    logger.info(f"Updated video URL to working version: {video_url}{file_info}")
            else:
                thumbnail_url = None
        elif video_url and skip_video_processing:
            logger.debug(f"Skipping video processing for: {video_url} (skip_video_processing=True)")
        
        # Store audiovisual data
        if video_url or duracao or assunto or tipo_intervencao:
            audiovisual = IntervencaoAudiovisual(
                intervencao_id=intervention.id,
                video_url=video_url,
                duracao=duracao,
                assunto=assunto,
                tipo_intervencao=tipo_intervencao
            )
            self.session.add(audiovisual)
    
    def _get_or_create_legislatura(self, sigla: str) -> Legislatura:
        """Get or create legislatura from sigla"""
        legislatura = self.session.query(Legislatura).filter_by(numero=sigla).first()
        
        if legislatura:
            return legislatura
        
        # Create new legislatura if it doesn't exist
        roman_to_num = {
            'XVII': 17, 'XVI': 16, 'XV': 15, 'XIV': 14, 'XIII': 13,
            'XII': 12, 'XI': 11, 'X': 10, 'IX': 9, 'VIII': 8,
            'VII': 7, 'VI': 6, 'V': 5, 'IV': 4, 'III': 3,
            'II': 2, 'I': 1, 'CONSTITUINTE': 0
        }
        
        numero_int = roman_to_num.get(sigla, 17)
        
        legislatura = Legislatura(
            numero=sigla,
            designacao=f"{numero_int}.ª Legislatura",
            ativa=False
        )
        
        self.session.add(legislatura)
        self.session.flush()  # Get the ID
        return legislatura
    
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
    
    def _extract_thumbnail_url_with_fallback(self, video_url: str, filename: str = None) -> Optional[tuple]:
        """Extract thumbnail URL from video page HTML with 404 fallback
        Returns: (thumbnail_url, final_video_url) or None if failed"""
        if not video_url:
            return None
        
        file_info = f" (from {filename})" if filename else ""
            
        def try_url(url: str) -> Optional[str]:
            """Try to extract thumbnail from a specific URL"""
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Search for the thumbnail URL pattern in HTML
                html_content = response.text
                
                # Pattern: <img loading="lazy" class="meeting-intervention-image" src="/api/v1/videos/Plenary/X/X/X/thumbnail/X" />
                thumbnail_pattern = r'class="meeting-intervention-image"\s+src="([^"]*thumbnail/\d+)"'
                match = re.search(thumbnail_pattern, html_content)
                
                if match:
                    thumbnail_path = match.group(1)
                    # Convert relative URL to absolute URL using video URL domain
                    parsed_video_url = urlparse(url)
                    base_url = f"{parsed_video_url.scheme}://{parsed_video_url.netloc}"
                    thumbnail_url = urljoin(base_url, thumbnail_path)
                    
                    logger.debug(f"Extracted thumbnail URL: {thumbnail_url}")
                    return thumbnail_url
                else:
                    logger.debug(f"No thumbnail found in video page: {url}")
                    return None
                    
            except requests.HTTPError as e:
                if e.response.status_code == 404:
                    logger.debug(f"404 error for URL: {url}{file_info}")
                    return None
                else:
                    logger.warning(f"HTTP error fetching video page {url}: {e}{file_info}")
                    return None
            except requests.RequestException as e:
                logger.warning(f"Failed to fetch video page {url}: {e}{file_info}")
                return None
            except Exception as e:
                logger.error(f"Error extracting thumbnail from {url}: {e}{file_info}")
                return None
        
        # Try the original URL first
        thumbnail_url = try_url(video_url)
        if thumbnail_url:
            return (thumbnail_url, video_url)
        
        # If original URL failed with 404 and has timestamps, try cleaning them
        if ('tI=' in video_url or 'drc=' in video_url):
            try:
                parsed_url = urlparse(video_url)
                query_params = parse_qs(parsed_url.query)
                
                # Remove time-related parameters
                if 'tI' in query_params:
                    del query_params['tI']
                if 'drc' in query_params:
                    del query_params['drc']
                
                # Reconstruct URL without time parameters
                new_query = urlencode(query_params, doseq=True)
                cleaned_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                if new_query:
                    cleaned_url += f"?{new_query}"
                
                logger.info(f"Retrying thumbnail extraction without timestamps: {cleaned_url}{file_info}")
                cleaned_thumbnail = try_url(cleaned_url)
                if cleaned_thumbnail:
                    return (cleaned_thumbnail, cleaned_url)
                
            except Exception as e:
                logger.warning(f"Could not clean timestamps from video URL {video_url}: {e}{file_info}")
        
        return None
    
    def _construct_direct_video_url(self, legislatura_num: int, sessao_num: int, atividade_id: int, intervencao_id: int) -> str:
        """Construct direct video URL using the pattern: /videos/Plenary/{leg}/{session}/{activity}/{intervention}"""
        return f"https://av.parlamento.pt/videos/Plenary/{legislatura_num}/{sessao_num}/{atividade_id}/{intervencao_id}"
    
    def _roman_to_number(self, roman: str) -> Optional[int]:
        """Convert roman numeral to number"""
        roman_map = {
            'XVII': 17, 'XVI': 16, 'XV': 15, 'XIV': 14, 'XIII': 13,
            'XII': 12, 'XI': 11, 'X': 10, 'IX': 9, 'VIII': 8,
            'VII': 7, 'VI': 6, 'V': 5, 'IV': 4, 'III': 3,
            'II': 2, 'I': 1, 'CONSTITUINTE': 0
        }
        return roman_map.get(roman.upper(), None)
    
    def close(self):
        """Close the database session"""
        if hasattr(self, 'session') and self.session:
            self.session.close()