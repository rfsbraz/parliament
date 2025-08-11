"""
Parliament API Routes - MySQL Implementation
Clean implementation with proper MySQL/SQLAlchemy patterns
"""
from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc, distinct
from database.connection import DatabaseSession
from database.models import (
    Deputado, Partido, Legislatura, CirculoEleitoral, 
    DeputadoMandatoLegislativo, DeputadoHabilitacao, 
    DeputadoCargoFuncao, DeputadoTitulo, DeputadoCondecoracao,
    DeputadoObraPublicada, IntervencaoParlamentar, IntervencaoDeputado,
    IniciativaParlamentar, IniciativaAutorDeputado, 
    AtividadeParlamentarVotacao, OrcamentoEstadoVotacao, 
    OrcamentoEstadoGrupoParlamentarVoto
)

parlamento_bp = Blueprint('parlamento', __name__)


def deputado_to_dict(deputado, session=None):
    """Convert Deputado object to dictionary for JSON serialization with related data"""
    
    # Get related data if session is provided
    if session:
        # Get mandate info
        mandato = session.query(DeputadoMandatoLegislativo).filter_by(
            deputado_id=deputado.id
        ).first()
        
        # Get legislature info
        legislatura = session.query(Legislatura).filter_by(
            id=deputado.legislatura_id
        ).first()
    else:
        mandato = None
        legislatura = None
    
    return {
        'deputado_id': deputado.id,  # Frontend expects deputado_id
        'id': deputado.id,
        'id_cadastro': deputado.id_cadastro,
        'nome': deputado.nome,
        'nome_completo': deputado.nome_completo,
        'data_nascimento': deputado.data_nascimento.isoformat() if deputado.data_nascimento else None,
        'naturalidade': deputado.naturalidade,
        'profissao': deputado.profissao,
        'legislatura_id': deputado.legislatura_id,
        'foto_url': deputado.foto_url,  # Frontend expects this
        'sexo': deputado.sexo,
        'ativo': deputado.is_active,
        
        # Mandate related data
        'partido_sigla': mandato.par_sigla if mandato else None,
        'circulo': mandato.ce_des if mandato else None,
        
        # Legislature data
        'legislatura_nome': legislatura.designacao if legislatura else None,
        'legislatura_numero': legislatura.numero if legislatura else None,
        
        # Basic career info placeholder (frontend expects this structure)
        'career_info': {
            'is_currently_active': deputado.is_active,
            'is_multi_term': False,  # Would need complex query to determine
            'total_mandates': 1,  # Simplified for now
            'first_mandate': legislatura.numero if legislatura else None,
            'latest_mandate': legislatura.numero if legislatura else None,
            'parties_served': [mandato.par_sigla] if mandato and mandato.par_sigla else []
        }
    }


def partido_to_dict(partido):
    """Convert Partido object to dictionary for JSON serialization"""
    return {
        'id': partido.id,
        'sigla': partido.sigla,
        'nome': partido.nome,
        'designacao': partido.designacao
    }


def legislatura_to_dict(legislatura):
    """Convert Legislatura object to dictionary for JSON serialization"""
    return {
        'id': legislatura.id,
        'numero': legislatura.numero,
        'designacao': legislatura.designacao,
        'data_inicio': legislatura.data_inicio.isoformat() if legislatura.data_inicio else None,
        'data_fim': legislatura.data_fim.isoformat() if legislatura.data_fim else None,
        'ativa': legislatura.ativa
    }


def log_and_return_error(e, endpoint_info="", status_code=500):
    """Helper function to log errors to console and return JSON error response"""
    import traceback
    error_msg = f'Error in {endpoint_info}: {str(e)}'
    traceback_msg = f'Traceback: {traceback.format_exc()}'
    
    # Print to console directly (for debugging)
    print(f"\n{'='*50}")
    print(error_msg)
    print(traceback_msg)
    print('='*50)
    
    # SECURITY: Only expose traceback in debug mode
    from flask import current_app
    if current_app.debug:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), status_code
    else:
        return jsonify({
            'error': 'Internal server error'
        }), status_code


# =============================================================================
# PHASE 1: CORE API ENDPOINTS
# =============================================================================

@parlamento_bp.route('/test', methods=['GET'])
def test_db():
    """Endpoint de teste para verificar conexão com MySQL"""
    try:
        with DatabaseSession() as session:
            count_deputados = session.query(Deputado).count()
            count_partidos = session.query(Partido).count()
            count_legislaturas = session.query(Legislatura).count()
        
        return jsonify({
            'status': 'mysql_ok',
            'database': 'MySQL',
            'deputados': count_deputados,
            'partidos': count_partidos,
            'legislaturas': count_legislaturas
        })
    except Exception as e:
        return log_and_return_error(e, '/api/test')


@parlamento_bp.route('/deputados/<int:deputado_id>', methods=['GET'])
def get_deputado(deputado_id):
    """Retorna detalhes de um deputado específico"""
    try:
        with DatabaseSession() as session:
            deputado = session.query(Deputado).filter_by(id=deputado_id).first()
            if not deputado:
                return jsonify({'error': 'Deputado not found'}), 404
            
            return jsonify(deputado_to_dict(deputado, session))
            
    except Exception as e:
        return log_and_return_error(e, '/api/deputados/<id>')


@parlamento_bp.route('/deputados/<int:deputado_id>/detalhes', methods=['GET'])
def get_deputado_detalhes(deputado_id):
    """Retorna detalhes completos de um deputado com informações do mandato"""
    try:
        with DatabaseSession() as session:
            deputado = session.query(Deputado).filter_by(id=deputado_id).first()
            if not deputado:
                return jsonify({'error': 'Deputado not found'}), 404
            
            # Get mandate information from DeputadoMandatoLegislativo table
            mandato_info = session.query(DeputadoMandatoLegislativo).filter_by(
                deputado_id=deputado_id
            ).first()
            
            # Get legislature information
            legislatura = session.query(Legislatura).filter_by(
                id=deputado.legislatura_id
            ).first()
            
            # Build response with deputy details and mandate info
            response = deputado_to_dict(deputado, session)
            
            # Always provide mandato structure, even if mandate info is missing
            if mandato_info:
                response['mandato'] = {
                    'partido_sigla': mandato_info.par_sigla,
                    'partido_nome': mandato_info.par_des,
                    'circulo_eleitoral': mandato_info.ce_des,
                    'inicio': legislatura.data_inicio.isoformat() if legislatura and legislatura.data_inicio else None,
                    'fim': legislatura.data_fim.isoformat() if legislatura and legislatura.data_fim else None
                }
            else:
                # Provide empty mandato structure with dates from legislature
                response['mandato'] = {
                    'partido_sigla': None,
                    'partido_nome': None,
                    'circulo_eleitoral': None,
                    'inicio': legislatura.data_inicio.isoformat() if legislatura and legislatura.data_inicio else None,
                    'fim': legislatura.data_fim.isoformat() if legislatura and legislatura.data_fim else None
                }
            
            if legislatura:
                response['legislatura'] = {
                    'numero': legislatura.numero,
                    'designacao': legislatura.designacao,
                    'ativa': legislatura.ativa
                }
            
            # Calculate statistics for this deputy
            # Count interventions using id_cadastro
            total_intervencoes = session.query(func.count(IntervencaoParlamentar.id)).join(
                IntervencaoDeputado, IntervencaoParlamentar.id == IntervencaoDeputado.intervencao_id
            ).filter(
                IntervencaoDeputado.id_cadastro == deputado.id_cadastro
            ).scalar() or 0
            
            # Count initiatives authored using id_cadastro
            total_iniciativas = session.query(func.count(IniciativaParlamentar.id)).join(
                IniciativaAutorDeputado, IniciativaParlamentar.id == IniciativaAutorDeputado.iniciativa_id
            ).filter(
                IniciativaAutorDeputado.id_cadastro == deputado.id_cadastro
            ).scalar() or 0
            
            # Count total mandates for this person using id_cadastro
            total_mandatos = session.query(func.count(Deputado.id)).filter(
                Deputado.id_cadastro == deputado.id_cadastro
            ).scalar() or 1
            
            # Get all legislatures served by this person
            legislaturas_servidas_query = session.query(Legislatura.numero).join(
                Deputado, Deputado.legislatura_id == Legislatura.id
            ).filter(
                Deputado.id_cadastro == deputado.id_cadastro
            ).distinct().all()
            
            legislaturas_list = [leg.numero for leg in legislaturas_servidas_query]
            legislaturas_servidas = ', '.join(sorted(legislaturas_list)) if legislaturas_list else legislatura.numero
            
            # Calculate years of service (simplified - from first to current legislature)
            anos_servico = total_mandatos * 4  # Rough estimate: 4 years per mandate
            
            # Add statistics to response
            response['estatisticas'] = {
                'total_intervencoes': total_intervencoes,
                'total_iniciativas': total_iniciativas,
                'taxa_assiduidade': 0.85,  # Placeholder - would need attendance data
                'total_mandatos': total_mandatos,
                'legislaturas_servidas': legislaturas_servidas,
                'anos_servico': anos_servico
            }
            
            return jsonify(response)
            
    except Exception as e:
        return log_and_return_error(e, '/api/deputados/<id>/detalhes')


@parlamento_bp.route('/partidos/<int:partido_id>', methods=['GET'])
def get_partido(partido_id):
    """Retorna detalhes de um partido específico"""
    try:
        with DatabaseSession() as session:
            partido = session.query(Partido).filter_by(id=partido_id).first()
            if not partido:
                return jsonify({'error': 'Partido not found'}), 404
            
            return jsonify(partido_to_dict(partido))
            
    except Exception as e:
        return log_and_return_error(e, '/api/partidos/<id>')


@parlamento_bp.route('/partidos/<string:partido_sigla>/deputados', methods=['GET'])
def get_partido_deputados(partido_sigla):
    """Retorna deputados de um partido usando nova estrutura de dados"""
    try:
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        
        with DatabaseSession() as session:
            # First get the party information from the partidos table
            partido = session.query(Partido).filter_by(sigla=partido_sigla).first()
            
            if not partido:
                return jsonify({'error': 'Party not found'}), 404
            
            # Get deputies from this party
            deputados = session.query(Deputado).join(
                DeputadoMandatoLegislativo, Deputado.id == DeputadoMandatoLegislativo.deputado_id
            ).join(
                Legislatura, Deputado.legislatura_id == Legislatura.id
            ).filter(
                DeputadoMandatoLegislativo.par_sigla == partido_sigla,
                Legislatura.numero == legislatura
            ).all()
            
            return jsonify({
                'deputados': [deputado_to_dict(d, session) for d in deputados],
                'total': len(deputados),
                'partido': {
                    'sigla': partido.sigla,
                    'nome': partido.nome,
                    'designacao_completa': partido.designacao_completa,
                    'cor_hex': partido.cor_hex,
                    'ativo': partido.is_active
                },
                'legislatura': legislatura
            })
            
    except Exception as e:
        return log_and_return_error(e, '/api/partidos/<id>/deputados')


@parlamento_bp.route('/legislaturas', methods=['GET'])
def get_legislaturas():
    """Retorna lista de legislaturas com informação sobre mandatos"""
    try:
        with DatabaseSession() as session:
            legislaturas = session.query(Legislatura).order_by(
                desc(Legislatura.numero)
            ).all()
            
            result = []
            for leg in legislaturas:
                # Count deputies in this legislature
                deputy_count = session.query(func.count(Deputado.id)).filter(
                    Deputado.legislatura_id == leg.id
                ).scalar()
                
                leg_dict = legislatura_to_dict(leg)
                leg_dict['total_deputados'] = deputy_count
                result.append(leg_dict)
            
            return jsonify({'legislaturas': result})
            
    except Exception as e:
        return log_and_return_error(e, '/api/legislaturas')


# =============================================================================
# PHASE 2: STATISTICS & ANALYTICS ENDPOINTS  
# =============================================================================

@parlamento_bp.route('/circulos', methods=['GET'])
def get_circulos():
    """Retorna lista de círculos eleitorais com contagem de deputados"""
    try:
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        
        with DatabaseSession() as session:
            # Get electoral circles with deputy counts using new schema
            circulos_result = session.query(
                DeputadoMandatoLegislativo.ce_des.label('designacao'),
                func.count(Deputado.id).label('num_deputados')
            ).join(
                Deputado, DeputadoMandatoLegislativo.deputado_id == Deputado.id
            ).join(
                Legislatura, Deputado.legislatura_id == Legislatura.id
            ).filter(
                Legislatura.numero == legislatura,
                DeputadoMandatoLegislativo.ce_des.isnot(None)
            ).group_by(
                DeputadoMandatoLegislativo.ce_des
            ).order_by(desc('num_deputados')).all()
            
            result = []
            for c in circulos_result:
                result.append({
                    'designacao': c.designacao,
                    'num_deputados': c.num_deputados
                })
            
            return jsonify({
                'circulos': result,
                'legislatura': legislatura,
                'total_circulos': len(result)
            })
            
    except Exception as e:
        return log_and_return_error(e, '/api/circulos')


@parlamento_bp.route('/estatisticas', methods=['GET'])
def get_estatisticas():
    """Retorna estatísticas gerais do parlamento para uma legislatura específica"""
    try:
        with DatabaseSession() as session:
            legislatura = request.args.get('legislatura', 'XVII', type=str)
            
            # Count unique deputies in the specified legislature - simplified direct approach
            total_deputados = session.query(
                func.count(distinct(DeputadoMandatoLegislativo.deputado_id))
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura
            ).scalar()
            
            # Count distinct political parties represented - simplified direct approach
            total_partidos = session.query(
                func.count(distinct(DeputadoMandatoLegislativo.par_sigla))
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.par_sigla.isnot(None)
            ).scalar()
            
            # Count distinct electoral circles - simplified direct approach
            total_circulos = session.query(
                func.count(distinct(DeputadoMandatoLegislativo.ce_des))
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.ce_des.isnot(None)
            ).scalar()
            
            # Total mandates = total deputies in this context
            total_mandatos = total_deputados
            
            # Distribution by parties - simplified direct approach
            distribuicao_partidos = session.query(
                DeputadoMandatoLegislativo.par_sigla.label('sigla'),
                DeputadoMandatoLegislativo.par_des.label('nome'),
                func.count(distinct(DeputadoMandatoLegislativo.deputado_id)).label('deputados')
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.par_sigla.isnot(None)
            ).group_by(
                DeputadoMandatoLegislativo.par_sigla,
                DeputadoMandatoLegislativo.par_des
            ).order_by(func.count(distinct(DeputadoMandatoLegislativo.deputado_id)).desc()).all()
            
            # Distribution by electoral circles - simplified direct approach
            distribuicao_circulos = session.query(
                DeputadoMandatoLegislativo.ce_des.label('circulo'),
                func.count(distinct(DeputadoMandatoLegislativo.deputado_id)).label('deputados')
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.ce_des.isnot(None)
            ).group_by(
                DeputadoMandatoLegislativo.ce_des
            ).order_by(func.count(distinct(DeputadoMandatoLegislativo.deputado_id)).desc()).limit(10).all()
            
            # Largest party
            maior_partido = distribuicao_partidos[0] if distribuicao_partidos else None
            
            # Largest electoral circle
            maior_circulo = distribuicao_circulos[0] if distribuicao_circulos else None
            
            return jsonify({
                'totais': {
                    'deputados': total_deputados,
                    'partidos': total_partidos,
                    'circulos': total_circulos,
                    'mandatos': total_mandatos
                },
                'distribuicao_partidos': [
                    {
                        'id': p.sigla,  # Frontend expects 'id' field for routing
                        'sigla': p.sigla,
                        'nome': p.nome or 'Partido não especificado',
                        'deputados': p.deputados
                    } for p in distribuicao_partidos
                ],
                'distribuicao_circulos': [
                    {
                        'circulo': c.circulo or 'Círculo não especificado',
                        'deputados': c.deputados
                    } for c in distribuicao_circulos
                ],
                'maior_partido': {
                    'sigla': maior_partido.sigla if maior_partido else None,
                    'deputados': maior_partido.deputados if maior_partido else 0
                },
                'maior_circulo': {
                    'designacao': maior_circulo.circulo if maior_circulo else None,
                    'deputados': maior_circulo.deputados if maior_circulo else 0
                }
            })
        
    except Exception as e:
        return log_and_return_error(e, '/api/estatisticas')


@parlamento_bp.route('/search', methods=['GET'])
def search():
    """Pesquisa global por deputados e partidos"""
    try:
        query_param = request.args.get('q', '', type=str)
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        
        if not query_param:
            return jsonify({'deputados': [], 'partidos': []})
        
        with DatabaseSession() as session:
            # Search deputies (filtered by legislature)
            deputados = session.query(Deputado).join(
                Legislatura, Deputado.legislatura_id == Legislatura.id
            ).filter(
                Deputado.nome_completo.contains(query_param),
                Legislatura.numero == legislatura
            ).limit(10).all()
            
            # Search parties using new structure
            # Get parties from the mandate table for the specified legislature
            partidos_result = session.query(
                DeputadoMandatoLegislativo.par_sigla.label('sigla'),
                DeputadoMandatoLegislativo.par_des.label('nome')
            ).join(
                Deputado, DeputadoMandatoLegislativo.deputado_id == Deputado.id
            ).join(
                Legislatura, Deputado.legislatura_id == Legislatura.id
            ).filter(
                Legislatura.numero == legislatura,
                (DeputadoMandatoLegislativo.par_sigla.contains(query_param) | 
                 DeputadoMandatoLegislativo.par_des.contains(query_param))
            ).distinct().limit(5).all()
            
            # Convert parties result to dict format
            partidos = []
            for p in partidos_result:
                partidos.append({
                    'id': p.sigla,  # Frontend expects 'id' field for routing
                    'sigla': p.sigla,
                    'nome': p.nome or 'Partido não especificado'
                })
            
            return jsonify({
                'deputados': [deputado_to_dict(d, session) for d in deputados],
                'partidos': partidos
            })
        
    except Exception as e:
        return log_and_return_error(e, '/api/search')


@parlamento_bp.route('/partidos', methods=['GET'])
def get_partidos():
    """Retorna lista de partidos com contagem de deputados para a legislatura especificada"""
    try:
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        
        with DatabaseSession() as session:
            # Get parties with deputy counts - simplified direct approach
            partidos_result = session.query(
                DeputadoMandatoLegislativo.par_sigla.label('sigla'),
                DeputadoMandatoLegislativo.par_des.label('nome'),
                func.count(distinct(DeputadoMandatoLegislativo.deputado_id)).label('num_deputados')
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.par_sigla.isnot(None)
            ).group_by(
                DeputadoMandatoLegislativo.par_sigla,
                DeputadoMandatoLegislativo.par_des
            ).order_by(func.count(distinct(DeputadoMandatoLegislativo.deputado_id)).desc()).all()
            
            # Get total deputies count for percentage calculation  
            total_deputados = session.query(
                func.count(distinct(DeputadoMandatoLegislativo.deputado_id))
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura
            ).scalar()
            
            result = []
            for p in partidos_result:
                if p.num_deputados > 0:  # Only show parties with deputies in current legislature
                    partido_dict = {
                        'id': p.sigla,  # Frontend expects 'id' field for routing
                        'sigla': p.sigla,
                        'nome': p.nome or 'Partido não especificado',
                        'num_deputados': p.num_deputados,
                        'percentagem': round((p.num_deputados / total_deputados * 100), 1) if total_deputados > 0 else 0
                    }
                    result.append(partido_dict)
            
            return jsonify({
                'partidos': result,
                'total_deputados': total_deputados
            })
        
    except Exception as e:
        return log_and_return_error(e, '/api/partidos')


@parlamento_bp.route('/partidos/<partido_id>/votacoes', methods=['GET'])
def get_partido_votacoes(partido_id):
    """Retorna estatísticas de votações agregadas de um partido"""
    try:
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        
        with DatabaseSession() as session:
            # Find party by sigla from the mandate table since we no longer have direct partido table access
            partido_info = session.query(
                DeputadoMandatoLegislativo.par_sigla.label('sigla'),
                DeputadoMandatoLegislativo.par_des.label('nome')
            ).join(
                Deputado, DeputadoMandatoLegislativo.deputado_id == Deputado.id
            ).join(
                Legislatura, Deputado.legislatura_id == Legislatura.id
            ).filter(
                DeputadoMandatoLegislativo.par_sigla == partido_id,  # Assuming partido_id is actually sigla
                Legislatura.numero == legislatura
            ).first()
            
            if not partido_info:
                return jsonify({'error': 'Party not found in the specified legislature'}), 404
            
            # Get deputies from this party in the specified legislature
            deputados = session.query(Deputado).join(
                DeputadoMandatoLegislativo, Deputado.id == DeputadoMandatoLegislativo.deputado_id
            ).join(
                Legislatura, Deputado.legislatura_id == Legislatura.id
            ).filter(
                DeputadoMandatoLegislativo.par_sigla == partido_id,
                Legislatura.numero == legislatura
            ).all()
            
            deputados_ids = [d.id for d in deputados]
            
            if not deputados_ids:
                return jsonify({
                    'partido': {
                        'sigla': partido_info.sigla,
                        'nome': partido_info.nome
                    },
                    'votacoes': [],
                    'estatisticas': {
                        'total_votacoes': 0,
                        'distribuicao': [],
                        'eficacia_media': 0
                    }
                })
            
            # For now, return that voting data needs to be implemented in MySQL
            return jsonify({
                'error': 'Voting data not yet available in MySQL schema', 
                'partido': {
                    'sigla': partido_info.sigla,
                    'nome': partido_info.nome
                },
                'deputados_count': len(deputados_ids),
                'message': 'This endpoint requires voting tables to be migrated to MySQL'
            }), 501
        
    except Exception as e:
        return log_and_return_error(e, '/api/partidos/<id>/votacoes')


# =============================================================================
# PHASE 3: COMPLEX FEATURES
# =============================================================================

@parlamento_bp.route('/deputados/<int:deputado_id>/atividades', methods=['GET'])
def get_deputado_atividades(deputado_id):
    """Retorna atividades parlamentares de um deputado"""
    try:
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        
        with DatabaseSession() as session:
            # Verify deputy exists using MySQL
            deputado = session.query(Deputado).filter_by(id=deputado_id).first()
            if not deputado:
                return jsonify({'error': 'Deputado not found'}), 404
            
            # Get legislature info for filtering
            leg = session.query(Legislatura).filter_by(numero=legislatura).first()
            if not leg:
                return jsonify({
                    'intervencoes': [],
                    'iniciativas': [],
                    'votacoes': []
                })
            
            # Get interventions for this deputy using id_cadastro
            intervencoes_query = session.query(IntervencaoParlamentar).join(
                IntervencaoDeputado, IntervencaoParlamentar.id == IntervencaoDeputado.intervencao_id
            ).filter(
                IntervencaoDeputado.id_cadastro == deputado.id_cadastro,
                IntervencaoParlamentar.legislatura_id == leg.id
            ).limit(50).all()
            
            intervencoes = []
            for interv in intervencoes_query:
                intervencoes.append({
                    'id': interv.int_id if hasattr(interv, 'int_id') else interv.id,
                    'resumo': interv.int_te if hasattr(interv, 'int_te') else None,
                    'sumario': interv.int_su if hasattr(interv, 'int_su') else None,
                    'data_publicacao': interv.pub_dtreu.isoformat() if hasattr(interv, 'pub_dtreu') and interv.pub_dtreu else None,
                    'tipo_intervencao': interv.tin_ds if hasattr(interv, 'tin_ds') else None,
                    'tipo_publicacao': interv.pub_tp if hasattr(interv, 'pub_tp') else None,
                    'dar_numero': interv.pub_dar if hasattr(interv, 'pub_dar') else None
                })
            
            # Get initiatives authored by this deputy using id_cadastro  
            iniciativas_query = session.query(IniciativaParlamentar).join(
                IniciativaAutorDeputado, IniciativaParlamentar.id == IniciativaAutorDeputado.iniciativa_id
            ).filter(
                IniciativaAutorDeputado.id_cadastro == deputado.id_cadastro,
                IniciativaParlamentar.legislatura_id == leg.id
            ).limit(50).all()
            
            iniciativas = []
            for inic in iniciativas_query:
                iniciativas.append({
                    'id': inic.ini_id if hasattr(inic, 'ini_id') else inic.id,
                    'numero': inic.ini_nr if hasattr(inic, 'ini_nr') else None,
                    'titulo': inic.ini_titulo if hasattr(inic, 'ini_titulo') else None,
                    'tipo': inic.ini_tipo if hasattr(inic, 'ini_tipo') else None,
                    'desc_tipo': inic.ini_desc_tipo if hasattr(inic, 'ini_desc_tipo') else None,
                    'link_texto': inic.ini_link_texto if hasattr(inic, 'ini_link_texto') else None,
                    'observacoes': inic.ini_obs if hasattr(inic, 'ini_obs') else None
                })
            
            return jsonify({
                'deputado': {
                    'id': deputado.id,
                    'nome': deputado.nome,
                    'id_cadastro': deputado.id_cadastro
                },
                'legislatura': {
                    'numero': leg.numero,
                    'designacao': leg.designacao
                },
                'intervencoes': intervencoes,
                'iniciativas': iniciativas,
                'votacoes': []  # Voting data would need separate implementation
            })
        
    except Exception as e:
        return log_and_return_error(e, '/api/deputados/<id>/atividades')


@parlamento_bp.route('/feed/atividades', methods=['GET'])
def get_atividades_feed():
    """Retorna feed de atividades parlamentares organizadas por data"""
    try:
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        tipo_filter = request.args.get('tipo', '')
        
        with DatabaseSession() as session:
            # Get legislature info
            leg = session.query(Legislatura).filter_by(numero=legislatura).first()
            if not leg:
                return jsonify({'atividades': [], 'total': 0})
            
            # For now, return that activity feed data needs to be implemented in MySQL
            return jsonify({
                'error': 'Activity feed data not yet available in MySQL schema',
                'legislatura': {
                    'numero': leg.numero,
                    'designacao': leg.designacao
                },
                'message': 'This endpoint requires initiative, intervention, and voting activity tables to be migrated to MySQL'
            }), 501
        
    except Exception as e:
        import traceback
        return log_and_return_error(e, '/api/deputados/<id>/biografia', 500)


@parlamento_bp.route('/feed/atividades/<string:tipo>/<int:atividade_id>/participantes', methods=['GET'])
def get_atividade_participantes(tipo, atividade_id):
    """Retorna participantes de uma atividade parlamentar específica"""
    try:
        return jsonify({
            'error': 'Activity participants data not yet available in MySQL schema',
            'message': 'This endpoint requires activity participant tables to be migrated to MySQL'
        }), 501
        
    except Exception as e:
        import traceback
        return log_and_return_error(e, '/api/deputados/<id>/biografia', 500)


@parlamento_bp.route('/deputados/<int:deputado_id>/biografia', methods=['GET'])
def get_deputado_biografia(deputado_id):
    """Retorna dados biográficos de um deputado"""
    try:
        with DatabaseSession() as session:
            # Get the deputado to find their cadastro_id
            deputado = session.query(Deputado).filter_by(id=deputado_id).first()
            if not deputado:
                return jsonify({'error': 'Deputado not found'}), 404
            
            cadastro_id = deputado.id_cadastro
            if not cadastro_id:
                return jsonify({'error': 'Cadastro ID não encontrado para este deputado'}), 404
            
            # Get comprehensive biographical data from MySQL
            habilitacoes = session.query(DeputadoHabilitacao).filter_by(
                deputado_id=deputado.id
            ).all()
            
            cargos_funcoes = session.query(DeputadoCargoFuncao).filter_by(
                deputado_id=deputado.id
            ).all()
            
            titulos = session.query(DeputadoTitulo).filter_by(
                deputado_id=deputado.id
            ).all()
            
            condecoracoes = session.query(DeputadoCondecoracao).filter_by(
                deputado_id=deputado.id
            ).all()
            
            obras_publicadas = session.query(DeputadoObraPublicada).filter_by(
                deputado_id=deputado.id
            ).all()
            
            # Build comprehensive biographical response
            biografia = {
                'deputado': {
                    'id': deputado.id,
                    'nome': deputado.nome,
                    'nome_completo': deputado.nome_completo,
                    'id_cadastro': deputado.id_cadastro,
                    'data_nascimento': deputado.data_nascimento.isoformat() if deputado.data_nascimento else None,
                    'naturalidade': deputado.naturalidade,
                    'profissao': deputado.profissao
                },
                'habilitacoes': [
                    {
                        'id': h.hab_id,
                        'descricao': h.hab_des,
                        'tipo_id': h.hab_tipo_id,
                        'estado': h.hab_estado
                    } for h in habilitacoes
                ],
                'cargos_funcoes': [
                    {
                        'id': c.fun_id,
                        'descricao': c.fun_des,
                        'ordem': c.fun_ordem,
                        'historico': c.fun_antiga == 'S'
                    } for c in cargos_funcoes
                ],
                'titulos': [
                    {
                        'id': t.tit_id,
                        'descricao': t.tit_des,
                        'ordem': t.tit_ordem
                    } for t in titulos
                ],
                'condecoracoes': [
                    {
                        'id': c.con_id,
                        'descricao': c.con_des,
                        'ordem': c.con_ordem
                    } for c in condecoracoes
                ],
                'obras_publicadas': [
                    {
                        'id': o.obr_id,
                        'descricao': o.obr_des,
                        'ordem': o.obr_ordem
                    } for o in obras_publicadas
                ]
            }
            
            return jsonify(biografia)
        
    except Exception as e:
        import traceback
        return log_and_return_error(e, '/api/deputados/<id>/biografia', 500)


@parlamento_bp.route('/deputados/by-name/<string:nome_completo>', methods=['GET'])
def get_deputado_by_name(nome_completo):
    """Encontra um deputado por nome em uma legislatura específica"""
    try:
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        
        with DatabaseSession() as session:
            # Get legislature record
            leg = session.query(Legislatura).filter_by(numero=legislatura).first()
            if not leg:
                return jsonify({'error': 'Legislatura não encontrada'}), 404
            
            # Find deputy by name in the specified legislature using new schema
            # Sanitize input to prevent SQL injection
            sanitized_name = nome_completo.replace('%', '\\%').replace('_', '\\_')
            deputado = session.query(Deputado).join(
                Legislatura, Deputado.legislatura_id == Legislatura.id
            ).filter(
                Deputado.nome_completo.ilike(f'%{sanitized_name}%'),
                Legislatura.numero == legislatura
            ).first()
            
            if not deputado:
                return jsonify({'error': 'Deputado não encontrado'}), 404
            
            return jsonify(deputado_to_dict(deputado, session))
        
    except Exception as e:
        return log_and_return_error(e, '/api/deputados/by-name/<nome>')


@parlamento_bp.route('/deputados/<int:deputado_id>/conflitos-interesse', methods=['GET'])
def get_deputado_conflitos_interesse(deputado_id):
    """Retorna declarações de conflitos de interesse de um deputado"""
    try:
        # Return empty conflicts structure until data is migrated to MySQL
        return jsonify({
            'deputado_id': deputado_id,
            'conflitos': [],  # Frontend expects this array
            'declaracoes': []  # Frontend expects this array
        })
        
    except Exception as e:
        import traceback
        return log_and_return_error(e, '/api/deputados/<id>/biografia', 500)


# =============================================================================
# VOTING RECORDS ENDPOINTS
# =============================================================================

@parlamento_bp.route('/deputados/<int:deputado_id>/votacoes', methods=['GET'])
def get_deputado_votacoes(deputado_id):
    """Retorna histórico de votações de um deputado específico"""
    try:
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        with DatabaseSession() as session:
            # Get deputy
            deputado = session.query(Deputado).filter_by(id=deputado_id).first()
            if not deputado:
                return jsonify({'error': 'Deputado não encontrado'}), 404
            
            # Get legislature
            leg = session.query(Legislatura).filter_by(numero=legislatura).first()
            if not leg:
                return jsonify({'error': 'Legislatura não encontrada'}), 404
            
            # Get parliamentary activity voting records
            parlamentar_votacoes = session.query(AtividadeParlamentarVotacao).join(
                IntervencaoDeputado, AtividadeParlamentarVotacao.atividade_id == IntervencaoDeputado.intervencao_id
            ).filter(
                IntervencaoDeputado.id_cadastro == deputado.id_cadastro
            ).order_by(desc(AtividadeParlamentarVotacao.data)).offset(offset).limit(limit).all()
            
            # Get budget voting records for this deputy's party
            mandato = session.query(DeputadoMandatoLegislativo).filter_by(
                id_cadastro=deputado.id_cadastro
            ).first()
            
            orcamento_votacoes = []
            if mandato:
                # Get budget votes where this deputy's party participated
                orcamento_votacoes = session.query(OrcamentoEstadoVotacao).join(
                    OrcamentoEstadoGrupoParlamentarVoto, 
                    OrcamentoEstadoVotacao.id == OrcamentoEstadoGrupoParlamentarVoto.votacao_id
                ).filter(
                    OrcamentoEstadoGrupoParlamentarVoto.grupo_parlamentar.like(f'%{mandato.par_sigla}%')
                ).order_by(desc(OrcamentoEstadoVotacao.data_votacao)).limit(20).all()
            
            # Format parliamentary voting records
            parlamentar_votos = []
            for votacao in parlamentar_votacoes:
                parlamentar_votos.append({
                    'id': votacao.id,
                    'tipo': 'parlamentar',
                    'data': votacao.data.isoformat() if votacao.data else None,
                    'resultado': votacao.resultado,
                    'unanime': votacao.unanime,
                    'descricao': votacao.descricao,
                    'reuniao': votacao.reuniao,
                    'publicacao': votacao.publicacao,
                    'detalhe': votacao.detalhe,
                    'ausencias': votacao.ausencias
                })
            
            # Format budget voting records
            orcamento_votos = []
            for votacao in orcamento_votacoes:
                # Get party vote for this voting record
                party_vote = session.query(OrcamentoEstadoGrupoParlamentarVoto).filter_by(
                    votacao_id=votacao.id
                ).filter(
                    OrcamentoEstadoGrupoParlamentarVoto.grupo_parlamentar.like(f'%{mandato.par_sigla}%')
                ).first()
                
                orcamento_votos.append({
                    'id': votacao.id,
                    'tipo': 'orcamento',
                    'data': votacao.data_votacao.isoformat() if votacao.data_votacao else None,
                    'resultado': votacao.resultado,
                    'descricao': votacao.descricao,
                    'voto_partido': party_vote.voto if party_vote else None,
                    'partido': mandato.par_sigla if mandato else None
                })
            
            # Combine and sort by date
            all_votes = parlamentar_votos + orcamento_votos
            all_votes.sort(key=lambda x: x['data'] or '', reverse=True)
            
            return jsonify({
                'deputado': {
                    'id': deputado.id,
                    'nome': deputado.nome,
                    'id_cadastro': deputado.id_cadastro
                },
                'votacoes': all_votes[:limit],
                'total_parlamentares': len(parlamentar_votos),
                'total_orcamento': len(orcamento_votos),
                'total': len(all_votes),
                'legislatura': legislatura
            })
            
    except Exception as e:
        return log_and_return_error(e, f'/api/deputados/{deputado_id}/votacoes')


@parlamento_bp.route('/partidos/<string:partido_sigla>/votacoes', methods=['GET'])
def get_partido_votacoes_by_sigla(partido_sigla):
    """Retorna padrões de votação de um partido específico"""
    try:
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        limit = request.args.get('limit', 50, type=int)
        
        with DatabaseSession() as session:
            # Get party
            partido = session.query(Partido).filter_by(sigla=partido_sigla).first()
            if not partido:
                return jsonify({'error': 'Partido não encontrado'}), 404
            
            # Get budget voting records where this party participated
            party_votes = session.query(OrcamentoEstadoVotacao).join(
                OrcamentoEstadoGrupoParlamentarVoto,
                OrcamentoEstadoVotacao.id == OrcamentoEstadoGrupoParlamentarVoto.votacao_id
            ).filter(
                OrcamentoEstadoGrupoParlamentarVoto.grupo_parlamentar.like(f'%{partido_sigla}%')
            ).order_by(desc(OrcamentoEstadoVotacao.data_votacao)).limit(limit).all()
            
            # Format voting records
            votacoes = []
            vote_summary = {'Favor': 0, 'Contra': 0, 'Abstenção': 0}
            
            for votacao in party_votes:
                # Get this party's specific vote
                party_vote = session.query(OrcamentoEstadoGrupoParlamentarVoto).filter_by(
                    votacao_id=votacao.id
                ).filter(
                    OrcamentoEstadoGrupoParlamentarVoto.grupo_parlamentar.like(f'%{partido_sigla}%')
                ).first()
                
                vote_result = party_vote.voto if party_vote else 'N/A'
                if vote_result in vote_summary:
                    vote_summary[vote_result] += 1
                
                votacoes.append({
                    'id': votacao.id,
                    'data': votacao.data_votacao.isoformat() if votacao.data_votacao else None,
                    'descricao': votacao.descricao,
                    'resultado_geral': votacao.resultado,
                    'voto_partido': vote_result,
                    'tipo': 'orcamento'
                })
            
            return jsonify({
                'partido': {
                    'sigla': partido_sigla,
                    'nome': partido.nome
                },
                'votacoes': votacoes,
                'total': len(votacoes),
                'resumo_votos': vote_summary,
                'legislatura': legislatura
            })
            
    except Exception as e:
        return log_and_return_error(e, f'/api/partidos/{partido_sigla}/votacoes')


@parlamento_bp.route('/votacoes', methods=['GET'])
def get_votacoes():
    """Retorna lista de votações por legislatura"""
    try:
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        tipo = request.args.get('tipo', 'all', type=str)  # 'all', 'parlamentar', 'orcamento'
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        with DatabaseSession() as session:
            votacoes = []
            
            # Get budget voting records
            if tipo in ['all', 'orcamento']:
                orcamento_votacoes = session.query(OrcamentoEstadoVotacao).order_by(
                    desc(OrcamentoEstadoVotacao.data_votacao)
                ).offset(offset).limit(limit).all()
                
                for votacao in orcamento_votacoes:
                    # Get all party votes for this voting record
                    party_votes = session.query(OrcamentoEstadoGrupoParlamentarVoto).filter_by(
                        votacao_id=votacao.id
                    ).all()
                    
                    votacoes.append({
                        'id': votacao.id,
                        'tipo': 'orcamento',
                        'data': votacao.data_votacao.isoformat() if votacao.data_votacao else None,
                        'descricao': votacao.descricao,
                        'resultado': votacao.resultado,
                        'votos_partidos': [
                            {
                                'partido': pv.grupo_parlamentar,
                                'voto': pv.voto
                            } for pv in party_votes
                        ],
                        'total_partidos': len(party_votes)
                    })
            
            # Get parliamentary voting records  
            if tipo in ['all', 'parlamentar']:
                parlamentar_votacoes = session.query(AtividadeParlamentarVotacao).order_by(
                    desc(AtividadeParlamentarVotacao.data)
                ).offset(offset).limit(min(limit, 25)).all()
                
                for votacao in parlamentar_votacoes:
                    votacoes.append({
                        'id': votacao.id,
                        'tipo': 'parlamentar',
                        'data': votacao.data.isoformat() if votacao.data else None,
                        'descricao': votacao.descricao,
                        'resultado': votacao.resultado,
                        'unanime': votacao.unanime,
                        'reuniao': votacao.reuniao,
                        'publicacao': votacao.publicacao
                    })
            
            # Sort by date
            votacoes.sort(key=lambda x: x['data'] or '', reverse=True)
            
            return jsonify({
                'votacoes': votacoes[:limit],
                'total': len(votacoes),
                'legislatura': legislatura,
                'tipo': tipo
            })
            
    except Exception as e:
        return log_and_return_error(e, '/api/votacoes')


@parlamento_bp.route('/votacoes/<int:votacao_id>', methods=['GET'])
def get_votacao_detalhes(votacao_id):
    """Retorna detalhes de uma votação específica"""
    try:
        tipo = request.args.get('tipo', 'orcamento', type=str)  # 'parlamentar' or 'orcamento'
        
        with DatabaseSession() as session:
            if tipo == 'orcamento':
                # Get budget voting record
                votacao = session.query(OrcamentoEstadoVotacao).filter_by(id=votacao_id).first()
                if not votacao:
                    return jsonify({'error': 'Votação não encontrada'}), 404
                
                # Get all party votes
                party_votes = session.query(OrcamentoEstadoGrupoParlamentarVoto).filter_by(
                    votacao_id=votacao.id
                ).all()
                
                return jsonify({
                    'id': votacao.id,
                    'tipo': 'orcamento',
                    'data': votacao.data_votacao.isoformat() if votacao.data_votacao else None,
                    'descricao': votacao.descricao,
                    'resultado': votacao.resultado,
                    'votos_partidos': [
                        {
                            'partido': pv.grupo_parlamentar,
                            'voto': pv.voto
                        } for pv in party_votes
                    ],
                    'resumo': {
                        'total_partidos': len(party_votes),
                        'favor': len([pv for pv in party_votes if pv.voto == 'Favor']),
                        'contra': len([pv for pv in party_votes if pv.voto == 'Contra']),
                        'abstencoes': len([pv for pv in party_votes if pv.voto == 'Abstenção'])
                    }
                })
                
            else:  # parlamentar
                votacao = session.query(AtividadeParlamentarVotacao).filter_by(id=votacao_id).first()
                if not votacao:
                    return jsonify({'error': 'Votação não encontrada'}), 404
                
                return jsonify({
                    'id': votacao.id,
                    'tipo': 'parlamentar',
                    'data': votacao.data.isoformat() if votacao.data else None,
                    'descricao': votacao.descricao,
                    'resultado': votacao.resultado,
                    'unanime': votacao.unanime,
                    'reuniao': votacao.reuniao,
                    'publicacao': votacao.publicacao,
                    'detalhe': votacao.detalhe,
                    'ausencias': votacao.ausencias
                })
                
    except Exception as e:
        return log_and_return_error(e, f'/api/votacoes/{votacao_id}')


# =============================================================================
# ANALYTICS ENDPOINTS (Advanced features)
# =============================================================================

@parlamento_bp.route('/deputados/<int:deputado_id>/voting-analytics', methods=['GET'])
def get_deputado_voting_analytics(deputado_id):
    """Retorna análises avançadas de votação para um deputado específico"""
    try:
        with DatabaseSession() as session:
            # Get deputy information
            deputado = session.query(Deputado).filter_by(id=deputado_id).first()
            if not deputado:
                return jsonify({'error': 'Deputado não encontrado'}), 404
            
            # Get deputy's party information from most recent mandate
            mandato_recente = session.query(DeputadoMandatoLegislativo).filter_by(
                deputado_id=deputado.id
            ).order_by(desc(DeputadoMandatoLegislativo.id)).first()
            
            partido_info = None
            partido_sigla = None
            if mandato_recente:
                partido_sigla = mandato_recente.par_sigla
                partido_info = session.query(Partido).filter_by(sigla=partido_sigla).first()
            
            # Get parliamentary activity voting records for this deputy
            parlamentar_votacoes = session.query(AtividadeParlamentarVotacao).join(
                IntervencaoDeputado, AtividadeParlamentarVotacao.atividade_id == IntervencaoDeputado.intervencao_id
            ).filter(
                IntervencaoDeputado.id_cadastro == deputado.id_cadastro
            ).all()
            
            # Get budget voting records through party affiliation
            orcamento_votacoes = []
            if partido_sigla:
                orcamento_party_votes = session.query(OrcamentoEstadoGrupoParlamentarVoto).filter_by(
                    grupo_parlamentar=partido_sigla
                ).all()
                
                # Get corresponding voting records
                for party_vote in orcamento_party_votes:
                    orcamento_vote = session.query(OrcamentoEstadoVotacao).filter_by(
                        id=party_vote.votacao_id
                    ).first()
                    if orcamento_vote:
                        orcamento_votacoes.append({
                            'votacao': orcamento_vote,
                            'voto_partido': party_vote.voto
                        })
            
            # Calculate analytics
            total_parlamentar = len(parlamentar_votacoes)
            total_orcamento = len(orcamento_votacoes)
            
            # Parliamentary voting patterns
            parlamentar_unanimes = len([v for v in parlamentar_votacoes if v.unanime])
            
            # Budget voting patterns (party-level)
            orcamento_favor = len([v for v in orcamento_votacoes if v['voto_partido'] == 'Favor'])
            orcamento_contra = len([v for v in orcamento_votacoes if v['voto_partido'] == 'Contra'])
            orcamento_abstencoes = len([v for v in orcamento_votacoes if v['voto_partido'] == 'Abstenção'])
            
            return jsonify({
                'deputado': {
                    'id': deputado.id,
                    'nome': deputado.nome_completo,
                    'partido': partido_sigla or 'N/A'
                },
                'resumo': {
                    'total_votacoes_parlamentares': total_parlamentar,
                    'total_votacoes_orcamento': total_orcamento,
                    'total_geral': total_parlamentar + total_orcamento
                },
                'parlamentar': {
                    'total': total_parlamentar,
                    'unanimes': parlamentar_unanimes,
                    'nao_unanimes': total_parlamentar - parlamentar_unanimes,
                    'percentual_unanimes': round((parlamentar_unanimes / total_parlamentar * 100) if total_parlamentar > 0 else 0, 1)
                },
                'orcamento': {
                    'total': total_orcamento,
                    'favor': orcamento_favor,
                    'contra': orcamento_contra,
                    'abstencoes': orcamento_abstencoes,
                    'percentual_favor': round((orcamento_favor / total_orcamento * 100) if total_orcamento > 0 else 0, 1),
                    'percentual_contra': round((orcamento_contra / total_orcamento * 100) if total_orcamento > 0 else 0, 1),
                    'percentual_abstencoes': round((orcamento_abstencoes / total_orcamento * 100) if total_orcamento > 0 else 0, 1)
                }
            })
        
    except Exception as e:
        return log_and_return_error(e, f'/api/deputados/{deputado_id}/voting-analytics')


@parlamento_bp.route('/partidos/<string:partido_sigla>/voting-analytics', methods=['GET'])
def get_partido_voting_analytics(partido_sigla):
    """Retorna análises avançadas de votação para um partido específico"""
    try:
        with DatabaseSession() as session:
            # Get party information
            partido = session.query(Partido).filter_by(sigla=partido_sigla).first()
            if not partido:
                return jsonify({'error': 'Partido não encontrado'}), 404
            
            # Get all budget voting records for this party
            orcamento_party_votes = session.query(OrcamentoEstadoGrupoParlamentarVoto).filter_by(
                grupo_parlamentar=partido_sigla
            ).all()
            
            # Get corresponding voting details
            orcamento_votacoes = []
            for party_vote in orcamento_party_votes:
                orcamento_vote = session.query(OrcamentoEstadoVotacao).filter_by(
                    id=party_vote.votacao_id
                ).first()
                if orcamento_vote:
                    orcamento_votacoes.append({
                        'votacao': orcamento_vote,
                        'voto': party_vote.voto,
                        'data': orcamento_vote.data_votacao
                    })
            
            # Get parliamentary activity voting records from party deputies
            # Get deputies who have mandates with this party
            deputados_partido_ids = session.query(DeputadoMandatoLegislativo.deputado_id).filter_by(
                par_sigla=partido_sigla
            ).distinct().all()
            
            deputados_partido = session.query(Deputado).filter(
                Deputado.id.in_([d[0] for d in deputados_partido_ids])
            ).all()
            
            parlamentar_votacoes = []
            
            for deputado in deputados_partido:
                dep_parlamentar_votacoes = session.query(AtividadeParlamentarVotacao).join(
                    IntervencaoDeputado, AtividadeParlamentarVotacao.atividade_id == IntervencaoDeputado.intervencao_id
                ).filter(
                    IntervencaoDeputado.id_cadastro == deputado.id_cadastro
                ).all()
                parlamentar_votacoes.extend(dep_parlamentar_votacoes)
            
            # Remove duplicates (same voting record from multiple deputies)
            unique_parlamentar = {}
            for votacao in parlamentar_votacoes:
                unique_parlamentar[votacao.id] = votacao
            parlamentar_votacoes = list(unique_parlamentar.values())
            
            # Calculate analytics
            total_orcamento = len(orcamento_votacoes)
            total_parlamentar = len(parlamentar_votacoes)
            
            # Budget voting patterns
            orcamento_favor = len([v for v in orcamento_votacoes if v['voto'] == 'Favor'])
            orcamento_contra = len([v for v in orcamento_votacoes if v['voto'] == 'Contra'])
            orcamento_abstencoes = len([v for v in orcamento_votacoes if v['voto'] == 'Abstenção'])
            
            # Parliamentary voting patterns  
            parlamentar_unanimes = len([v for v in parlamentar_votacoes if v.unanime])
            
            # Recent voting patterns (last 6 months)
            from datetime import datetime, timedelta
            six_months_ago = datetime.now().date() - timedelta(days=180)
            
            def get_date(dt):
                """Convert datetime or date to date for comparison"""
                if hasattr(dt, 'date'):
                    return dt.date()
                return dt
            
            recent_orcamento = [v for v in orcamento_votacoes if v['data'] and get_date(v['data']) >= six_months_ago]
            recent_parlamentar = [v for v in parlamentar_votacoes if v.data and get_date(v.data) >= six_months_ago]
            
            recent_orcamento_favor = len([v for v in recent_orcamento if v['voto'] == 'Favor'])
            recent_orcamento_contra = len([v for v in recent_orcamento if v['voto'] == 'Contra'])
            
            return jsonify({
                'partido': {
                    'sigla': partido.sigla,
                    'nome': partido.nome,
                    'numero_deputados': len(deputados_partido)
                },
                'resumo': {
                    'total_votacoes_orcamento': total_orcamento,
                    'total_votacoes_parlamentares': total_parlamentar,
                    'total_geral': total_orcamento + total_parlamentar
                },
                'orcamento': {
                    'total': total_orcamento,
                    'favor': orcamento_favor,
                    'contra': orcamento_contra,
                    'abstencoes': orcamento_abstencoes,
                    'percentual_favor': round((orcamento_favor / total_orcamento * 100) if total_orcamento > 0 else 0, 1),
                    'percentual_contra': round((orcamento_contra / total_orcamento * 100) if total_orcamento > 0 else 0, 1),
                    'percentual_abstencoes': round((orcamento_abstencoes / total_orcamento * 100) if total_orcamento > 0 else 0, 1)
                },
                'parlamentar': {
                    'total': total_parlamentar,
                    'unanimes': parlamentar_unanimes,
                    'nao_unanimes': total_parlamentar - parlamentar_unanimes,
                    'percentual_unanimes': round((parlamentar_unanimes / total_parlamentar * 100) if total_parlamentar > 0 else 0, 1)
                },
                'tendencias_recentes': {
                    'periodo': '6 meses',
                    'orcamento': {
                        'total': len(recent_orcamento),
                        'favor': recent_orcamento_favor,
                        'contra': recent_orcamento_contra,
                        'tendencia_favor': round((recent_orcamento_favor / len(recent_orcamento) * 100) if recent_orcamento else 0, 1)
                    },
                    'parlamentar': {
                        'total': len(recent_parlamentar)
                    }
                }
            })
        
    except Exception as e:
        return log_and_return_error(e, f'/api/partidos/{partido_sigla}/voting-analytics')


# =============================================================================
# ADDITIONAL UTILITY ENDPOINTS
# =============================================================================

@parlamento_bp.route('/deputados', methods=['GET'])
def get_deputados():
    """Retorna lista de deputados com paginação e filtros"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '', type=str)
        legislatura = request.args.get('legislatura', None, type=str)  # Specific legislature filter
        
        with DatabaseSession() as session:
            if legislatura:
                # Filter by specific legislature when explicitly requested
                query = session.query(Deputado).join(
                    DeputadoMandatoLegislativo, Deputado.id == DeputadoMandatoLegislativo.deputado_id
                ).filter(
                    DeputadoMandatoLegislativo.leg_des == legislatura
                )
            else:
                # Default: Return all unique deputies by id_cadastro (latest entry per person)
                subquery = session.query(
                    Deputado.id_cadastro,
                    func.max(Deputado.id).label('latest_id')
                ).group_by(Deputado.id_cadastro).subquery()
                
                query = session.query(Deputado).join(
                    subquery, Deputado.id == subquery.c.latest_id
                )
            
            # Apply search filter if provided
            if search:
                query = query.filter(
                    Deputado.nome_completo.contains(search)
                )
            
            # Get total count for pagination
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            deputados = query.offset(offset).limit(per_page).all()
            
            # Get additional statistics for filters
            if legislatura:
                # When filtering by legislature, total mandates = total unique people in that legislature
                total_mandatos = total
                view_type = f'legislature_{legislatura}'
            else:
                # When showing all unique deputies, also get total mandate count
                total_mandatos = session.query(func.count(Deputado.id)).scalar()
                view_type = 'all_unique'
            
            return jsonify({
                'deputados': [deputado_to_dict(d, session) for d in deputados],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page,
                    'has_next': offset + per_page < total,
                    'has_prev': page > 1
                },
                'filters': {
                    'total_deputy_records': total_mandatos,
                    'view_type': view_type,
                    'legislatura': legislatura,
                    'show_all_unique': not bool(legislatura)
                },
                'legislatura': legislatura
            })
        
    except Exception as e:
        return log_and_return_error(e, '/api/deputados')