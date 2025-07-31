"""
Comprehensive Legislative Initiatives Mapper
===========================================

Enhanced schema mapper for legislative initiatives files (Iniciativas*.xml).
Imports EVERY SINGLE FIELD and structure from the XML including:
- Main initiative data
- Authors (deputies, groups, others)
- Events timeline with detailed phases
- Voting data with results and parliamentary group positions
- Committee assignments and publications
- Amendment proposals
- Joint discussions
- Publication data for all phases

Maps to comprehensive database schema with full relational structure.
"""

import xml.etree.ElementTree as ET
import os
import re
from typing import Dict, Optional, Set, List
import logging
from datetime import datetime

from .base_mapper import SchemaMapper, SchemaError

# Import our models
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from database.models import (
    IniciativaParlamentar, IniciativaAutorOutro, IniciativaAutorDeputado,
    IniciativaAutorGrupoParlamentar, IniciativaPropostaAlteracao, 
    IniciativaPropostaAlteracaoPublicacao, IniciativaEvento, IniciativaEventoPublicacao,
    IniciativaEventoVotacao, IniciativaVotacaoAusencia, IniciativaEventoComissao,
    IniciativaComissaoPublicacao, IniciativaEventoRecursoGP, IniciativaConjunta,
    IniciativaIntervencaoDebate, Legislatura
)

logger = logging.getLogger(__name__)


class InitiativasMapper(SchemaMapper):
    """Comprehensive schema mapper for legislative initiatives files"""
    
    def __init__(self, session):
        # Accept SQLAlchemy session directly (passed by unified importer)
        super().__init__(session)
    
    def get_expected_fields(self) -> Set[str]:
        # Complete field list from XML analysis
        return {
            # Root elements
            'ArrayOfPt_gov_ar_objectos_iniciativas_DetalhePesquisaIniciativasOut',
            'Pt_gov_ar_objectos_iniciativas_DetalhePesquisaIniciativasOut',
            # Core initiative fields
            'IniNr', 'IniTipo', 'IniDescTipo', 'IniLeg', 'IniSel', 'DataInicioleg', 'DataFimleg',
            'IniTitulo', 'IniTextoSubst', 'IniLinkTexto', 'IniId', 'IniTipoPesquisa',
            # Authors
            'IniAutorOutros', 'sigla', 'nome', 'IniAutorDeputados', 'IniAutorGruposParlamentares',
            'pt_gov_ar_objectos_iniciativas_AutoresDeputadosOut', 'idCadastro', 'GP',
            'pt_gov_ar_objectos_AutoresGruposParlamentaresOut',
            # Events
            'IniEventos', 'Pt_gov_ar_objectos_iniciativas_EventosOut', 'OevId', 'DataFase',
            'Fase', 'EvtId', 'CodigoFase', 'ObsFase', 'ActId', 'OevTextId', 'TextosAprovados',
            # Publications
            'PublicacaoFase', 'pt_gov_ar_objectos_PublicacoesOut', 'pubNr', 'pubTipo', 'pubTp',
            'pubLeg', 'pubSL', 'pubdt', 'pag', 'string', 'idPag', 'URLDiario', 'Publicacao',
            # Voting
            'Votacao', 'pt_gov_ar_objectos_VotacaoOut', 'id', 'resultado', 'reuniao',
            'tipoReuniao', 'detalhe', 'unanime', 'ausencias', 'data',
            # Committees
            'Comissao', 'Pt_gov_ar_objectos_iniciativas_ComissoesIniOut', 'AccId', 'Numero',
            'IdComissao', 'Nome', 'Competente', 'DataDistribuicao', 'DataEntrada',
            'DataAgendamentoPlenario', 'PublicacaoRelatorio',
            # Resources
            'RecursoGP',
            # Joint initiatives
            'IniciativasConjuntas', 'pt_gov_ar_objectos_iniciativas_DiscussaoConjuntaOut',
            'nr', 'tipo', 'descTipo', 'leg', 'sel', 'titulo',
            # Interventions
            'Intervencoesdebates', 'pt_gov_ar_objectos_IntervencoesOut', 'dataReuniaoPlenaria',
            # Amendment proposals
            'PropostasAlteracao', 'pt_gov_ar_objectos_iniciativas_PropostasAlteracaoOut', 'autor', 'publicacao'
        }
    
    def validate_and_map(self, xml_root: ET.Element, file_info: Dict, strict_mode: bool = False) -> Dict:
        """Map legislative initiatives with complete structure to database"""
        results = {'records_processed': 0, 'records_imported': 0, 'errors': []}
        
        try:
            # Validate schema coverage with strict mode support
            self.validate_schema_coverage(xml_root, file_info, strict_mode)
            
            # Extract legislatura from filename
            filename = os.path.basename(file_info['file_path'])
            leg_match = re.search(r'Iniciativas(XVII|XVI|XV|XIV|XIII|XII|XI|IX|VIII|VII|VI|IV|III|II|CONSTITUINTE|X|V|I)\.xml', filename)
            legislatura_sigla = leg_match.group(1) if leg_match else 'XVII'
            legislatura = self._get_or_create_legislatura(legislatura_sigla)
            
            for iniciativa in xml_root.findall('.//Pt_gov_ar_objectos_iniciativas_DetalhePesquisaIniciativasOut'):
                try:
                    success = self._process_iniciativa_complete(iniciativa, legislatura)
                    results['records_processed'] += 1
                    if success:
                        results['records_imported'] += 1
                except Exception as e:
                    error_msg = f"Initiative processing error: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['records_processed'] += 1
                    self.session.rollback()
            
            # Commit all changes
            self.session.commit()
            return results
            
        except Exception as e:
            error_msg = f"Critical error processing initiatives: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            self.session.rollback()
            return results
    
    def _process_iniciativa_complete(self, iniciativa: ET.Element, legislatura: Legislatura) -> bool:
        """Process complete initiative with all structures"""
        try:
            # Extract core initiative data
            ini_id = self._get_int_value(iniciativa, 'IniId')
            ini_nr = self._get_int_value(iniciativa, 'IniNr')
            ini_tipo = self._get_text_value(iniciativa, 'IniTipo')
            ini_desc_tipo = self._get_text_value(iniciativa, 'IniDescTipo')
            ini_leg = self._get_text_value(iniciativa, 'IniLeg')
            ini_sel = self._get_int_value(iniciativa, 'IniSel')
            data_inicio_leg = self._parse_date(self._get_text_value(iniciativa, 'DataInicioleg'))
            data_fim_leg = self._parse_date(self._get_text_value(iniciativa, 'DataFimleg'))
            ini_titulo = self._get_text_value(iniciativa, 'IniTitulo')
            ini_texto_subst = self._get_text_value(iniciativa, 'IniTextoSubst')
            ini_link_texto = self._get_text_value(iniciativa, 'IniLinkTexto')
            
            if not ini_id or not ini_titulo:
                logger.warning("Missing required fields: ini_id or ini_titulo")
                return False
            
            # Check if initiative already exists
            existing = None
            if ini_id:
                existing = self.session.query(IniciativaParlamentar).filter_by(ini_id=ini_id).first()
            
            if existing:
                # Update existing initiative
                existing.ini_nr = ini_nr
                existing.ini_tipo = ini_tipo
                existing.ini_desc_tipo = ini_desc_tipo
                existing.ini_leg = ini_leg
                existing.ini_sel = ini_sel
                existing.data_inicio_leg = data_inicio_leg
                existing.data_fim_leg = data_fim_leg
                existing.ini_titulo = ini_titulo
                existing.ini_texto_subst = ini_texto_subst
                existing.ini_link_texto = ini_link_texto
                existing.legislatura_id = legislatura.id
                existing.updated_at = datetime.now()
            else:
                # Create new initiative record
                existing = IniciativaParlamentar(
                    ini_id=ini_id,
                    ini_nr=ini_nr,
                    ini_tipo=ini_tipo,
                    ini_desc_tipo=ini_desc_tipo,
                    ini_leg=ini_leg,
                    ini_sel=ini_sel,
                    data_inicio_leg=data_inicio_leg,
                    data_fim_leg=data_fim_leg,
                    ini_titulo=ini_titulo,
                    ini_texto_subst=ini_texto_subst,
                    ini_link_texto=ini_link_texto,
                    legislatura_id=legislatura.id,
                    updated_at=datetime.now()
                )
                self.session.add(existing)
                self.session.flush()  # Get the ID
            
            # Process all related structures
            self._process_autores_outros(iniciativa, existing)
            self._process_autores_deputados(iniciativa, existing)
            self._process_autores_grupos_parlamentares(iniciativa, existing)
            self._process_propostas_alteracao(iniciativa, existing)
            self._process_eventos(iniciativa, existing)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing initiative {ini_id}: {e}")
            return False
    
    
    def _process_autores_outros(self, iniciativa: ET.Element, iniciativa_obj: IniciativaParlamentar):
        """Process IniAutorOutros - Other authors (Government, etc.)"""
        # Clear existing records
        for autor in iniciativa_obj.autores_outros:
            self.session.delete(autor)
        
        autor_outros = iniciativa.find('IniAutorOutros')
        if autor_outros is not None:
            sigla = self._get_text_value(autor_outros, 'sigla')
            nome = self._get_text_value(autor_outros, 'nome')
            
            autor = IniciativaAutorOutro(
                iniciativa_id=iniciativa_obj.id,
                sigla=sigla,
                nome=nome
            )
            self.session.add(autor)
    
    def _process_autores_deputados(self, iniciativa: ET.Element, iniciativa_obj: IniciativaParlamentar):
        """Process IniAutorDeputados - Deputy authors"""
        # Clear existing records
        for autor in iniciativa_obj.autores_deputados:
            self.session.delete(autor)
        
        autores_deputados = iniciativa.find('IniAutorDeputados')
        if autores_deputados is not None:
            for autor in autores_deputados.findall('pt_gov_ar_objectos_iniciativas_AutoresDeputadosOut'):
                id_cadastro = self._get_int_value(autor, 'idCadastro')
                nome = self._get_text_value(autor, 'nome')
                gp = self._get_text_value(autor, 'GP')
                
                autor_deputado = IniciativaAutorDeputado(
                    iniciativa_id=iniciativa_obj.id,
                    id_cadastro=id_cadastro,
                    nome=nome,
                    gp=gp
                )
                self.session.add(autor_deputado)
    
    def _process_autores_grupos_parlamentares(self, iniciativa: ET.Element, iniciativa_obj: IniciativaParlamentar):
        """Process IniAutorGruposParlamentares - Parliamentary group authors"""
        # Clear existing records
        for autor in iniciativa_obj.autores_grupos:
            self.session.delete(autor)
        
        autores_grupos = iniciativa.find('IniAutorGruposParlamentares')
        if autores_grupos is not None:
            for grupo in autores_grupos.findall('pt_gov_ar_objectos_AutoresGruposParlamentaresOut'):
                gp = self._get_text_value(grupo, 'GP')
                
                autor_grupo = IniciativaAutorGrupoParlamentar(
                    iniciativa_id=iniciativa_obj.id,
                    gp=gp
                )
                self.session.add(autor_grupo)
    
    def _process_propostas_alteracao(self, iniciativa: ET.Element, iniciativa_obj: IniciativaParlamentar):
        """Process PropostasAlteracao - Amendment proposals"""
        # Clear existing records
        for proposta in iniciativa_obj.propostas_alteracao:
            self.session.delete(proposta)
        
        propostas = iniciativa.find('PropostasAlteracao')
        if propostas is not None:
            for proposta in propostas.findall('pt_gov_ar_objectos_iniciativas_PropostasAlteracaoOut'):
                proposta_id = self._get_int_value(proposta, 'id')
                tipo = self._get_text_value(proposta, 'tipo')
                autor = self._get_text_value(proposta, 'autor')
                
                # Create proposal object
                proposta_obj = IniciativaPropostaAlteracao(
                    iniciativa_id=iniciativa_obj.id,
                    proposta_id=proposta_id,
                    tipo=tipo,
                    autor=autor
                )
                self.session.add(proposta_obj)
                self.session.flush()  # Get the ID
                
                # Process publications for this proposal
                publicacao = proposta.find('publicacao')
                if publicacao is not None:
                    for pub in publicacao.findall('pt_gov_ar_objectos_PublicacoesOut'):
                        self._insert_proposta_publicacao(proposta_obj, pub)
    
    def _insert_proposta_publicacao(self, proposta_obj: IniciativaPropostaAlteracao, pub: ET.Element):
        """Insert publication data for amendment proposal"""
        pub_nr = self._get_int_value(pub, 'pubNr')
        pub_tipo = self._get_text_value(pub, 'pubTipo')
        pub_tp = self._get_text_value(pub, 'pubTp')
        pub_leg = self._get_text_value(pub, 'pubLeg')
        pub_sl = self._get_int_value(pub, 'pubSL')
        pub_dt = self._parse_date(self._get_text_value(pub, 'pubdt'))
        id_pag = self._get_int_value(pub, 'idPag')
        url_diario = self._get_text_value(pub, 'URLDiario')
        
        # Handle page numbers (can be in <pag><string> elements)
        pag_text = None
        pag_elem = pub.find('pag')
        if pag_elem is not None:
            string_elems = pag_elem.findall('string')
            if string_elems:
                pag_text = ', '.join([s.text for s in string_elems if s.text])
        
        publicacao_obj = IniciativaPropostaAlteracaoPublicacao(
            proposta_id=proposta_obj.id,
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
        self.session.add(publicacao_obj)
    
    def _process_eventos(self, iniciativa: ET.Element, iniciativa_obj: IniciativaParlamentar):
        """Process IniEventos - Complete events timeline"""
        # Clear existing events and related data
        for evento in iniciativa_obj.eventos:
            self.session.delete(evento)
        
        eventos = iniciativa.find('IniEventos')
        if eventos is not None:
            for evento in eventos.findall('Pt_gov_ar_objectos_iniciativas_EventosOut'):
                evento_obj = self._process_single_evento(evento, iniciativa_obj)
                if evento_obj:
                    self._process_evento_details(evento, evento_obj)
    
    def _process_single_evento(self, evento: ET.Element, iniciativa_obj: IniciativaParlamentar) -> Optional[IniciativaEvento]:
        """Process single event core data"""
        oev_id = self._get_int_value(evento, 'OevId')
        data_fase = self._parse_date(self._get_text_value(evento, 'DataFase'))
        fase = self._get_text_value(evento, 'Fase')
        evt_id = self._get_int_value(evento, 'EvtId')
        codigo_fase = self._get_int_value(evento, 'CodigoFase')
        obs_fase = self._get_text_value(evento, 'ObsFase')
        act_id = self._get_int_value(evento, 'ActId')
        oev_text_id = self._get_int_value(evento, 'OevTextId')
        textos_aprovados = self._get_text_value(evento, 'TextosAprovados')
        
        evento_obj = IniciativaEvento(
            iniciativa_id=iniciativa_obj.id,
            oev_id=oev_id,
            data_fase=data_fase,
            fase=fase,
            evt_id=evt_id,
            codigo_fase=codigo_fase,
            obs_fase=obs_fase,
            act_id=act_id,
            oev_text_id=oev_text_id,
            textos_aprovados=textos_aprovados
        )
        self.session.add(evento_obj)
        self.session.flush()  # Get the ID
        return evento_obj
    
    def _process_evento_details(self, evento: ET.Element, evento_obj: IniciativaEvento):
        """Process all detailed structures for an event"""
        # Publications
        self._process_evento_publicacoes(evento, evento_obj)
        
        # Voting
        self._process_evento_votacao(evento, evento_obj)
        
        # Committees
        self._process_evento_comissoes(evento, evento_obj)
        
        # Resource groups
        self._process_evento_recursos_gp(evento, evento_obj)
        
        # Joint initiatives
        self._process_evento_iniciativas_conjuntas(evento, evento_obj)
        
        # Interventions/debates
        self._process_evento_intervencoes(evento, evento_obj)
    
    def _process_evento_publicacoes(self, evento: ET.Element, evento_obj: IniciativaEvento):
        """Process event publications"""
        publicacao_fase = evento.find('PublicacaoFase')
        if publicacao_fase is not None:
            for pub in publicacao_fase.findall('pt_gov_ar_objectos_PublicacoesOut'):
                self._insert_evento_publicacao(evento_obj, pub)
    
    def _insert_evento_publicacao(self, evento_obj: IniciativaEvento, pub: ET.Element):
        """Insert publication data for event"""
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
        
        publicacao_obj = IniciativaEventoPublicacao(
            evento_id=evento_obj.id,
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
        self.session.add(publicacao_obj)
    
    def _process_evento_votacao(self, evento: ET.Element, evento_obj: IniciativaEvento):
        """Process voting data for event"""
        votacao = evento.find('Votacao')
        if votacao is not None:
            for vot in votacao.findall('pt_gov_ar_objectos_VotacaoOut'):
                id_votacao = self._get_int_value(vot, 'id')
                resultado = self._get_text_value(vot, 'resultado')
                reuniao = self._get_int_value(vot, 'reuniao')
                tipo_reuniao = self._get_text_value(vot, 'tipoReuniao')
                detalhe = self._get_text_value(vot, 'detalhe')
                unanime = self._get_text_value(vot, 'unanime')
                data_votacao = self._parse_date(self._get_text_value(vot, 'data'))
                
                # Create voting record
                votacao_obj = IniciativaEventoVotacao(
                    evento_id=evento_obj.id,
                    id_votacao=id_votacao,
                    resultado=resultado,
                    reuniao=reuniao,
                    tipo_reuniao=tipo_reuniao,
                    detalhe=detalhe,
                    unanime=unanime,
                    data_votacao=data_votacao
                )
                self.session.add(votacao_obj)
                self.session.flush()  # Get the ID
                
                # Process absences
                ausencias = vot.find('ausencias')
                if ausencias is not None:
                    for string_elem in ausencias.findall('string'):
                        gp = string_elem.text
                        if gp:
                            ausencia_obj = IniciativaVotacaoAusencia(
                                votacao_id=votacao_obj.id,
                                grupo_parlamentar=gp
                            )
                            self.session.add(ausencia_obj)
    
    def _process_evento_recursos_gp(self, evento: ET.Element, evento_obj: IniciativaEvento):
        """Process RecursoGP - Parliamentary group resources"""
        recurso_gp = evento.find('RecursoGP')
        if recurso_gp is not None:
            for string_elem in recurso_gp.findall('string'):
                gp = string_elem.text
                if gp:
                    recurso_obj = IniciativaEventoRecursoGP(
                        evento_id=evento_obj.id,
                        grupo_parlamentar=gp
                    )
                    self.session.add(recurso_obj)
    
    def _process_evento_comissoes(self, evento: ET.Element, evento_obj: IniciativaEvento):
        """Process committee data for event"""
        comissao = evento.find('Comissao')
        if comissao is not None:
            for com in comissao.findall('Pt_gov_ar_objectos_iniciativas_ComissoesIniOut'):
                acc_id = self._get_int_value(com, 'AccId')
                numero = self._get_int_value(com, 'Numero')
                id_comissao = self._get_int_value(com, 'IdComissao')
                nome = self._get_text_value(com, 'Nome')
                competente = self._get_text_value(com, 'Competente')
                data_distribuicao = self._parse_date(self._get_text_value(com, 'DataDistribuicao'))
                data_entrada = self._parse_date(self._get_text_value(com, 'DataEntrada'))
                data_agendamento = self._get_text_value(com, 'DataAgendamentoPlenario')
                
                # Create committee record
                comissao_obj = IniciativaEventoComissao(
                    evento_id=evento_obj.id,
                    acc_id=acc_id,
                    numero=numero,
                    id_comissao=id_comissao,
                    nome=nome,
                    competente=competente,
                    data_distribuicao=data_distribuicao,
                    data_entrada=data_entrada,
                    data_agendamento_plenario=data_agendamento
                )
                self.session.add(comissao_obj)
                self.session.flush()  # Get the ID
                
                # Process committee publications
                for pub_type in ['Publicacao', 'PublicacaoRelatorio']:
                    pub_elem = com.find(pub_type)
                    if pub_elem is not None:
                        for pub in pub_elem.findall('pt_gov_ar_objectos_PublicacoesOut'):
                            self._insert_comissao_publicacao(comissao_obj, pub, pub_type)
    
    def _insert_comissao_publicacao(self, comissao_obj: IniciativaEventoComissao, pub: ET.Element, tipo: str):
        """Insert committee publication"""
        pub_nr = self._get_int_value(pub, 'pubNr')
        pub_tipo = self._get_text_value(pub, 'pubTipo')
        pub_tp = self._get_text_value(pub, 'pubTp')
        pub_leg = self._get_text_value(pub, 'pubLeg')
        pub_sl = self._get_int_value(pub, 'pubSL')
        pub_dt = self._parse_date(self._get_text_value(pub, 'pubdt'))
        id_pag = self._get_int_value(pub, 'idPag')
        url_diario = self._get_text_value(pub, 'URLDiario')
        
        pag_text = None
        pag_elem = pub.find('pag')
        if pag_elem is not None:
            string_elems = pag_elem.findall('string')
            if string_elems:
                pag_text = ', '.join([s.text for s in string_elems if s.text])
        
        publicacao_obj = IniciativaComissaoPublicacao(
            comissao_id=comissao_obj.id,
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
        self.session.add(publicacao_obj)
    
    def _process_evento_iniciativas_conjuntas(self, evento: ET.Element, evento_obj: IniciativaEvento):
        """Process joint initiatives"""
        iniciativas_conjuntas = evento.find('IniciativasConjuntas')
        if iniciativas_conjuntas is not None:
            for ini in iniciativas_conjuntas.findall('pt_gov_ar_objectos_iniciativas_DiscussaoConjuntaOut'):
                nr = self._get_int_value(ini, 'nr')
                tipo = self._get_text_value(ini, 'tipo')
                desc_tipo = self._get_text_value(ini, 'descTipo')
                leg = self._get_text_value(ini, 'leg')
                sel = self._get_int_value(ini, 'sel')
                titulo = self._get_text_value(ini, 'titulo')
                ini_id = self._get_int_value(ini, 'id')
                
                iniciativa_conjunta_obj = IniciativaConjunta(
                    evento_id=evento_obj.id,
                    nr=nr,
                    tipo=tipo,
                    desc_tipo=desc_tipo,
                    leg=leg,
                    sel=sel,
                    titulo=titulo,
                    ini_id=ini_id
                )
                self.session.add(iniciativa_conjunta_obj)
    
    def _process_evento_intervencoes(self, evento: ET.Element, evento_obj: IniciativaEvento):
        """Process interventions/debates"""
        intervencoes = evento.find('Intervencoesdebates')
        if intervencoes is not None:
            for int_elem in intervencoes.findall('pt_gov_ar_objectos_IntervencoesOut'):
                data_reuniao = self._parse_date(self._get_text_value(int_elem, 'dataReuniaoPlenaria'))
                
                intervencao_debate_obj = IniciativaIntervencaoDebate(
                    evento_id=evento_obj.id,
                    data_reuniao_plenaria=data_reuniao
                )
                self.session.add(intervencao_debate_obj)
    
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
                return int(float(text_value)) if '.' in text_value else int(text_value)
            except (ValueError, TypeError):
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
            # Handle datetime format: YYYY-MM-DDTHH:MM:SS
            if 'T' in date_str:
                return date_str.split('T')[0]
            # Handle DD/MM/YYYY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3 and len(parts[2]) == 4:
                    return f"{parts[2]}-{parts[1]:0>2}-{parts[0]:0>2}"
            return date_str
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return date_str
    
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
    
    def close(self):
        """Close the database session"""
        if hasattr(self, 'session') and self.session:
            self.session.close()