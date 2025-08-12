"""
Parliament API Routes - MySQL Implementation
Clean implementation with proper MySQL/SQLAlchemy patterns
"""
from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc, distinct, or_
from database.connection import DatabaseSession
from database.models import (
    Deputado, Partido, Legislatura, CirculoEleitoral, 
    DeputadoMandatoLegislativo, DeputadoHabilitacao, 
    DeputadoCargoFuncao, DeputadoTitulo, DeputadoCondecoracao,
    DeputadoObraPublicada, IntervencaoParlamentar, IntervencaoDeputado,
    IniciativaParlamentar, IniciativaAutorDeputado, IniciativaEvento, IniciativaEventoVotacao,
    AtividadeParlamentarVotacao, OrcamentoEstadoVotacao, 
    OrcamentoEstadoGrupoParlamentarVoto, Coligacao, ColigacaoPartido,
    RegistoInteressesUnified
)
from scripts.data_processing.mappers.political_entity_queries import PoliticalEntityQueries

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
        'foto_url': deputado.foto_url,  # Deprecated - kept for backward compatibility
        'picture_url': f'https://app.parlamento.pt/webutils/getimage.aspx?id={deputado.id_cadastro}&type=deputado' if deputado.id_cadastro else None,
        'sexo': deputado.sexo,
        'ativo': deputado.is_active,
        
        # Mandate related data - use individual party sigla
        'partido_sigla': (
            mandato.gp_sigla if mandato and mandato.eh_coligacao and mandato.gp_sigla 
            else mandato.par_sigla if mandato 
            else None
        ),
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
            'parties_served': [(
                mandato.gp_sigla if mandato.eh_coligacao and mandato.gp_sigla 
                else mandato.par_sigla
            )] if mandato and (mandato.par_sigla or mandato.gp_sigla) else []
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


@parlamento_bp.route('/deputados/<int:cad_id>', methods=['GET'])
def get_deputado(cad_id):
    """Retorna detalhes de um deputado específico"""
    try:
        with DatabaseSession() as session:
            # Find deputado by cad_id (unique across all legislatures)
            # Get their most recent legislature entry
            deputado = session.query(Deputado).filter(
                Deputado.id_cadastro == cad_id
            ).order_by(Deputado.legislatura_id.desc()).first()
            
            if not deputado:
                return jsonify({'error': 'Deputado not found'}), 404
            
            return jsonify(deputado_to_dict(deputado, session))
            
    except Exception as e:
        return log_and_return_error(e, '/api/deputados/<id>')


def get_latest_legislature_id(session):
    """Get the ID of the latest/current legislature"""
    latest_legislature = session.query(Legislatura).filter_by(ativa=True).first()
    if not latest_legislature:
        # If no active legislature, get the one with highest number
        latest_legislature = session.query(Legislatura).order_by(Legislatura.numero.desc()).first()
    return latest_legislature.id if latest_legislature else None

@parlamento_bp.route('/deputados/<int:cad_id>/detalhes', methods=['GET'])
def get_deputado_detalhes(cad_id):
    """Retorna detalhes completos de um deputado com informações do mandato"""
    try:
        with DatabaseSession() as session:
            # Find deputado by cad_id (unique across all legislatures)
            # Get their most recent legislature entry
            deputado = session.query(Deputado).filter(
                Deputado.id_cadastro == cad_id
            ).order_by(Deputado.legislatura_id.desc()).first()
            
            if not deputado:
                return jsonify({'error': 'Deputado not found'}), 404
            
            # Get mandate information from DeputadoMandatoLegislativo table
            mandato_info = session.query(DeputadoMandatoLegislativo).filter_by(
                deputado_id=deputado.id
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
            
            # Get all legislatures served by this person with dates
            legislaturas_servidas_query = session.query(Legislatura).join(
                Deputado, Deputado.legislatura_id == Legislatura.id
            ).filter(
                Deputado.id_cadastro == deputado.id_cadastro
            ).distinct().all()
            
            legislaturas_list = [leg.numero for leg in legislaturas_servidas_query]
            legislaturas_servidas = ', '.join(sorted(legislaturas_list)) if legislaturas_list else legislatura.numero
            
            # Calculate actual years of service based on legislature dates
            anos_servico = 0
            if legislaturas_servidas_query:
                from datetime import datetime
                today = datetime.now().date()
                
                for leg in legislaturas_servidas_query:
                    if leg.data_inicio:
                        # If legislature has ended, use full duration
                        if leg.data_fim and leg.data_fim < today:
                            years = (leg.data_fim - leg.data_inicio).days / 365.25
                        # If legislature is ongoing, calculate from start to today
                        else:
                            years = (today - leg.data_inicio).days / 365.25
                        anos_servico += years
                
                # Round to 1 decimal place
                anos_servico = round(anos_servico, 1)
            
            # Calculate real attendance rate based on actual session attendance records
            taxa_assiduidade = 0.85  # Default value if no attendance data available
            
            if deputado.nome:
                # Query the meeting_attendances table for this deputy's session attendance
                from sqlalchemy import text
                
                attendance_query = text("""
                    SELECT 
                        sigla_falta,
                        COUNT(*) as session_count
                    FROM meeting_attendances 
                    WHERE dep_nome_parlamentar = :deputy_name
                    AND dt_reuniao IS NOT NULL
                    GROUP BY sigla_falta
                """)
                
                attendance_records = session.execute(attendance_query, {'deputy_name': deputado.nome}).fetchall()
                
                if attendance_records:
                    # Count different types of attendance
                    present_sessions = 0  # PR = Present
                    justified_absences = 0  # FJ, ME, QVJ, MP = Justified absences
                    unjustified_absences = 0  # FI = Unjustified absences  
                    total_sessions = 0
                    
                    for record in attendance_records:
                        sigla_falta, count = record
                        total_sessions += count
                        
                        if sigla_falta == 'PR':  # Present
                            present_sessions += count
                        elif sigla_falta in ['FJ', 'ME', 'QVJ', 'MP']:  # Justified absences
                            justified_absences += count
                        elif sigla_falta in ['FI', 'FA']:  # Unjustified absences
                            unjustified_absences += count
                        else:
                            # For unknown codes, treat as justified absence
                            justified_absences += count
                    
                    if total_sessions > 0:
                        # Calculate attendance rate:
                        # Present sessions count as 100% attendance
                        # Justified absences count as neutral (don't hurt attendance)
                        # Unjustified absences hurt attendance
                        
                        # Method 1: Simple presence rate (only count actual presence)
                        simple_attendance = present_sessions / total_sessions
                        
                        # Method 2: Adjusted rate (justify absences don't count against)
                        # Only penalize for unjustified absences
                        attendance_eligible_sessions = present_sessions + justified_absences
                        adjusted_attendance = attendance_eligible_sessions / total_sessions
                        
                        # Use the adjusted method for fairer calculation
                        taxa_assiduidade = round(adjusted_attendance, 3)
                        
                        # Cap at reasonable maximum (95%) to account for some expected absences
                        if taxa_assiduidade > 0.95:
                            taxa_assiduidade = 0.95
            
            # Add statistics to response
            response['estatisticas'] = {
                'total_intervencoes': total_intervencoes,
                'total_iniciativas': total_iniciativas,
                'taxa_assiduidade': taxa_assiduidade,
                'total_mandatos': total_mandatos,
                'legislaturas_servidas': legislaturas_servidas,
                'anos_servico': anos_servico
            }
            
            # Get all mandates for this person across all legislatures
            mandatos_historico = []
            if deputado.id_cadastro:
                # Get unique deputy records for this person (one per legislature)
                all_mandates = session.query(Deputado, Legislatura).join(
                    Legislatura, Deputado.legislatura_id == Legislatura.id
                ).filter(
                    Deputado.id_cadastro == deputado.id_cadastro
                ).order_by(desc(Legislatura.numero)).all()
                
                # Process each unique mandate
                seen_legislatures = set()
                for dep, leg in all_mandates:
                    # Skip if we've already processed this legislature
                    if leg.numero in seen_legislatures:
                        continue
                    seen_legislatures.add(leg.numero)
                    
                    # Get the mandate info for this deputy (just the first one if multiple exist)
                    mand = session.query(DeputadoMandatoLegislativo).filter_by(
                        deputado_id=dep.id
                    ).first()
                    
                    mandato_data = {
                        'deputado_id': dep.id,
                        'legislatura_numero': leg.numero,
                        'legislatura_nome': leg.designacao,
                        'mandato_inicio': leg.data_inicio.isoformat() if leg.data_inicio else None,
                        'mandato_fim': leg.data_fim.isoformat() if leg.data_fim else None,
                        'circulo': mand.ce_des if mand else None,  # Electoral circle from mandate info
                        'partido_sigla': mand.par_sigla if mand else None,
                        'partido_nome': mand.par_des if mand else None,
                        'is_current': dep.id == deputado.id  # Mark current mandate
                    }
                    mandatos_historico.append(mandato_data)
            
            response['mandatos_historico'] = mandatos_historico
            
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


@parlamento_bp.route('/partidos/<path:partido_sigla>/deputados', methods=['GET'])
def get_partido_deputados(partido_sigla):
    """Retorna deputados de um partido usando nova estrutura de dados"""
    try:
        # URL decode the party sigla to handle special characters like slashes
        from urllib.parse import unquote
        partido_sigla = unquote(partido_sigla)
        
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        
        with DatabaseSession() as session:
            # First try to get the party information from the partidos table
            partido = session.query(Partido).filter_by(sigla=partido_sigla).first()
            
            # If not found in partidos table, check if it exists in mandate table
            if not partido:
                mandate_exists = session.query(DeputadoMandatoLegislativo).filter(
                    DeputadoMandatoLegislativo.par_sigla == partido_sigla
                ).first()
                
                if not mandate_exists:
                    return jsonify({'error': 'Party not found'}), 404
                
                # Create a mock party object with data from mandate table
                class MockParty:
                    def __init__(self, sigla, nome):
                        self.sigla = sigla
                        self.nome = nome
                        self.designacao_completa = nome
                        self.cor_hex = None
                        self.is_active = True
                
                partido = MockParty(partido_sigla, mandate_exists.par_des or partido_sigla)
            
            # Get deputies from this party using the simplified direct approach
            deputados = session.query(Deputado).join(
                DeputadoMandatoLegislativo, Deputado.id == DeputadoMandatoLegislativo.deputado_id
            ).filter(
                DeputadoMandatoLegislativo.par_sigla == partido_sigla,
                DeputadoMandatoLegislativo.leg_des == legislatura
            ).all()
            
            # Check if this party is part of any coalition
            coalition_info = session.query(
                DeputadoMandatoLegislativo.coligacao_id,
                DeputadoMandatoLegislativo.eh_coligacao
            ).filter(
                DeputadoMandatoLegislativo.par_sigla == partido_sigla,
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.eh_coligacao == 1
            ).first()
            
            coalition_data = None
            if coalition_info and coalition_info.coligacao_id:
                # Get coalition information
                coalition = session.query(Coligacao).filter_by(id=coalition_info.coligacao_id).first()
                if coalition:
                    coalition_data = {
                        'sigla': coalition.sigla,
                        'nome': coalition.nome,
                        'id': coalition.id
                    }
            
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
                'coligacao': coalition_data,
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
            
            # Get legislature information
            legislature_info = session.query(Legislatura).filter_by(numero=legislatura).first()
            
            # Count unique deputies in the specified legislature - simplified direct approach
            total_deputados = session.query(
                func.count(distinct(DeputadoMandatoLegislativo.deputado_id))
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura
            ).scalar()
            
            # Count distinct individual parties represented (not coalitions)
            individual_parties = session.query(
                distinct(DeputadoMandatoLegislativo.par_sigla)
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.eh_coligacao == False,
                DeputadoMandatoLegislativo.par_sigla.isnot(None)
            ).all()
            
            coalition_parties = session.query(
                distinct(DeputadoMandatoLegislativo.gp_sigla)
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.eh_coligacao == True,
                DeputadoMandatoLegislativo.gp_sigla.isnot(None)
            ).all()
            
            # Combine unique parties
            all_parties = set([p[0] for p in individual_parties] + [p[0] for p in coalition_parties])
            total_partidos = len(all_parties)
            
            # Count distinct electoral circles - simplified direct approach
            total_circulos = session.query(
                func.count(distinct(DeputadoMandatoLegislativo.ce_des))
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.ce_des.isnot(None)
            ).scalar()
            
            # Total mandates = total deputies in this context
            total_mandatos = total_deputados
            
            # Distribution by individual parties (not coalitions)
            # First get individual party records
            individual_party_dist = session.query(
                DeputadoMandatoLegislativo.par_sigla.label('sigla'),
                DeputadoMandatoLegislativo.par_des.label('nome'),
                func.count(distinct(DeputadoMandatoLegislativo.deputado_id)).label('deputados')
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.eh_coligacao == False,
                DeputadoMandatoLegislativo.par_sigla.isnot(None)
            ).group_by(
                DeputadoMandatoLegislativo.par_sigla,
                DeputadoMandatoLegislativo.par_des
            ).all()
            
            # Then get coalition records using gp_sigla (parliamentary group = individual party)
            coalition_party_dist = session.query(
                DeputadoMandatoLegislativo.gp_sigla.label('sigla'),
                DeputadoMandatoLegislativo.gp_des.label('nome'),
                func.count(distinct(DeputadoMandatoLegislativo.deputado_id)).label('deputados')
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.eh_coligacao == True,
                DeputadoMandatoLegislativo.gp_sigla.isnot(None)
            ).group_by(
                DeputadoMandatoLegislativo.gp_sigla,
                DeputadoMandatoLegislativo.gp_des
            ).all()
            
            # Combine and aggregate party counts
            party_counts = {}
            for party in individual_party_dist:
                party_counts[party.sigla] = {
                    'sigla': party.sigla,
                    'nome': party.nome,
                    'deputados': party.deputados
                }
                
            for party in coalition_party_dist:
                if party.sigla in party_counts:
                    party_counts[party.sigla]['deputados'] += party.deputados
                else:
                    party_counts[party.sigla] = {
                        'sigla': party.sigla,
                        'nome': party.nome,
                        'deputados': party.deputados
                    }
            
            # Convert to list and sort by deputy count
            distribuicao_partidos = sorted(
                party_counts.values(), 
                key=lambda x: x['deputados'], 
                reverse=True
            )
            
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
                        'id': p['sigla'],  # Frontend expects 'id' field for routing
                        'sigla': p['sigla'],
                        'nome': p['nome'] or 'Partido não especificado',
                        'deputados': p['deputados']
                    } for p in distribuicao_partidos
                ],
                'distribuicao_circulos': [
                    {
                        'circulo': c.circulo or 'Círculo não especificado',
                        'deputados': c.deputados
                    } for c in distribuicao_circulos
                ],
                'maior_partido': {
                    'sigla': maior_partido['sigla'] if maior_partido else None,
                    'deputados': maior_partido['deputados'] if maior_partido else 0
                },
                'maior_circulo': {
                    'designacao': maior_circulo.circulo if maior_circulo else None,
                    'deputados': maior_circulo.deputados if maior_circulo else 0
                },
                'legislatura': {
                    'numero': legislature_info.numero if legislature_info else legislatura,
                    'designacao': legislature_info.designacao if legislature_info else f'{legislatura} Legislatura',
                    'data_inicio': legislature_info.data_inicio.isoformat() if legislature_info and legislature_info.data_inicio else None,
                    'data_fim': legislature_info.data_fim.isoformat() if legislature_info and legislature_info.data_fim else None,
                    'ativa': legislature_info.ativa if legislature_info else True
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
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        with DatabaseSession() as session:
            # Get all parties from the partidos table (source of truth for individual parties)
            all_parties = session.query(Partido).all()
            
            # Get deputy counts for each party in the specified legislature
            deputy_counts = {}
            
            # Count deputies by individual party sigla (for parties not in coalitions)
            individual_counts = session.query(
                DeputadoMandatoLegislativo.par_sigla,
                func.count(distinct(DeputadoMandatoLegislativo.deputado_id)).label('count')
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.eh_coligacao == False
            ).group_by(DeputadoMandatoLegislativo.par_sigla).all()
            
            for party_sigla, count in individual_counts:
                deputy_counts[party_sigla] = deputy_counts.get(party_sigla, 0) + count
            
            # For coalition records, use gp_sigla (parliamentary group) to get individual party counts
            coalition_counts = session.query(
                DeputadoMandatoLegislativo.gp_sigla,
                func.count(distinct(DeputadoMandatoLegislativo.deputado_id)).label('count')
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.eh_coligacao == True,
                DeputadoMandatoLegislativo.gp_sigla.isnot(None)
            ).group_by(DeputadoMandatoLegislativo.gp_sigla).all()
            
            for party_sigla, count in coalition_counts:
                deputy_counts[party_sigla] = deputy_counts.get(party_sigla, 0) + count
            
            # Get total deputies count for percentage calculation
            total_deputados = session.query(
                func.count(distinct(DeputadoMandatoLegislativo.deputado_id))
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura
            ).scalar()
            
            result = []
            
            for partido in all_parties:
                num_deputados = deputy_counts.get(partido.sigla, 0)
                
                # Filter by active_only if requested
                if active_only and num_deputados == 0:
                    continue
                    
                partido_dict = {
                    'id': partido.sigla,  # Frontend expects 'id' field for routing
                    'sigla': partido.sigla,
                    'nome': partido.nome,
                    'designacao_completa': partido.designacao_completa,
                    'tipo_entidade': 'partido',
                    'num_deputados': num_deputados,
                    'percentagem': round((num_deputados / total_deputados * 100), 1) if total_deputados > 0 else 0,
                    'ativo': num_deputados > 0  # Party is active if it has deputies in current legislature
                }
                
                result.append(partido_dict)
            
            # Sort by number of deputies (descending), then by name
            result.sort(key=lambda x: (-x['num_deputados'], x['sigla']))
            
            return jsonify({
                'partidos': result,
                'total_deputados': total_deputados,
                'active_only': active_only,
                'legislatura': legislatura,
                'total_parties': len(result)
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

@parlamento_bp.route('/deputados/<int:cad_id>/atividades', methods=['GET'])
def get_deputado_atividades(cad_id):
    """Retorna atividades parlamentares de um deputado"""
    try:
        with DatabaseSession() as session:
            # Find deputado by cad_id (unique across all legislatures)
            # Get their most recent legislature entry
            deputado = session.query(Deputado).filter(
                Deputado.id_cadastro == cad_id
            ).order_by(Deputado.legislatura_id.desc()).first()
            
            if not deputado:
                return jsonify({'error': 'Deputado not found'}), 404
            
            # Use the deputy's actual legislature for filtering
            leg = session.query(Legislatura).filter_by(id=deputado.legislatura_id).first()
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


@parlamento_bp.route('/deputados/<int:cad_id>/biografia', methods=['GET'])
def get_deputado_biografia(cad_id):
    """Retorna dados biográficos de um deputado"""
    try:
        with DatabaseSession() as session:
            # Find deputado by cad_id (unique across all legislatures)
            # Get their most recent legislature entry
            deputado = session.query(Deputado).filter(
                Deputado.id_cadastro == cad_id
            ).order_by(Deputado.legislatura_id.desc()).first()
            
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


@parlamento_bp.route('/deputados/<int:cad_id>/conflitos-interesse', methods=['GET'])
def get_deputado_conflitos_interesse(cad_id):
    """Retorna declarações de conflitos de interesse de um deputado"""
    try:
        with DatabaseSession() as session:
            # Find deputado by cad_id (unique across all legislatures)
            deputado = session.query(Deputado).filter(
                Deputado.id_cadastro == cad_id
            ).order_by(Deputado.legislatura_id.desc()).first()
            
            if not deputado:
                return jsonify({'error': 'Deputado não encontrado'}), 404
            
            # Get all deputado records with this cad_id (may be multiple across legislatures)
            all_deputados = session.query(Deputado).filter(
                Deputado.id_cadastro == cad_id
            ).all()
            
            deputado_ids = [d.id for d in all_deputados]
            
            # Get interest declarations for any of these deputy records
            interesse_records = session.query(RegistoInteressesUnified).filter(
                RegistoInteressesUnified.deputado_id.in_(deputado_ids)
            ).all()
            
            # Process the records to match frontend expectations
            conflitos_interesse = None
            if interesse_records:
                # Take the most recent record (or first one if only one exists)
                record = interesse_records[0]
                
                # Check if deputy's spouse is also a deputy
                spouse_deputy = None
                if record.spouse_name:
                    # Search for spouse by name in deputados table
                    spouse_dep = session.query(Deputado).filter(
                        func.lower(Deputado.nome_completo).contains(func.lower(record.spouse_name.strip()))
                    ).first()
                    
                    if spouse_dep:
                        # Get spouse's party info
                        spouse_mandato = session.query(DeputadoMandatoLegislativo).filter_by(
                            deputado_id=spouse_dep.id
                        ).order_by(DeputadoMandatoLegislativo.id.desc()).first()
                        
                        spouse_deputy = {
                            'cad_id': spouse_dep.id_cadastro,
                            'id': spouse_dep.id,
                            'partido_sigla': spouse_mandato.par_sigla if spouse_mandato else None
                        }
                
                # Determine if there's conflict potential
                has_conflict_potential = bool(
                    record.spouse_name or  # Has spouse
                    (record.exclusivity and record.exclusivity.lower() == 'n') or  # Not exclusive
                    record.professional_activity  # Has other professional activities
                )
                
                conflitos_interesse = {
                    'has_conflict_potential': has_conflict_potential,
                    'exclusivity_description': 'Exclusivo' if record.exclusivity == 'S' else 'Não exclusivo' if record.exclusivity == 'N' else None,
                    'full_name': record.full_name,
                    'dgf_number': record.dgf_number,
                    'marital_status': record.marital_status_desc,
                    'matrimonial_regime': record.matrimonial_regime,
                    'spouse_name': record.spouse_name,
                    'spouse_deputy': spouse_deputy,
                    'professional_activity': record.professional_activity
                }
            
            # Return the data in the format the frontend expects
            if conflitos_interesse:
                # Return the conflict data directly with some metadata
                result = conflitos_interesse.copy()
                result['deputado_id'] = cad_id
                result['total_declaracoes'] = len(interesse_records)
                return jsonify(result)
            else:
                # No conflict data found
                return jsonify({
                    'deputado_id': cad_id,
                    'has_conflict_potential': False,
                    'total_declaracoes': 0,
                    'message': 'Nenhuma declaração de interesses encontrada'
                })
        
    except Exception as e:
        import traceback
        return log_and_return_error(e, '/api/deputados/<id>/conflitos-interesse', 500)


@parlamento_bp.route('/deputados/<int:cad_id>/attendance', methods=['GET'])
def get_deputado_attendance(cad_id):
    """Retorna timeline de presenças/faltas de um deputado"""
    try:
        with DatabaseSession() as session:
            # Find deputado by cad_id (unique across all legislatures)
            # Get their most recent legislature entry
            deputado = session.query(Deputado).filter(
                Deputado.id_cadastro == cad_id
            ).order_by(Deputado.legislatura_id.desc()).first()
            
            if not deputado:
                return jsonify({'error': 'Deputado não encontrado'}), 404
            
            # Query attendance records from meeting_attendances table
            from sqlalchemy import text
            
            attendance_query = text("""
                SELECT 
                    dt_reuniao,
                    tipo_reuniao,
                    sigla_falta,
                    motivo_falta,
                    pres_justificacao,
                    observacoes,
                    sigla_grupo
                FROM meeting_attendances 
                WHERE dep_nome_parlamentar = :deputy_name
                AND dt_reuniao IS NOT NULL
                ORDER BY dt_reuniao DESC
                LIMIT 200
            """)
            
            attendance_records = session.execute(attendance_query, {'deputy_name': deputado.nome}).fetchall()
            
            # Process attendance records
            timeline = []
            summary = {
                'total_sessions': 0,
                'present': 0,
                'justified_absence': 0,
                'unjustified_absence': 0,
                'other': 0
            }
            
            # Attendance code meanings (based on analysis)
            attendance_codes = {
                'PR': {'type': 'present', 'description': 'Presente', 'status': 'success'},
                'FJ': {'type': 'justified', 'description': 'Falta Justificada', 'status': 'warning'},
                'ME': {'type': 'justified', 'description': 'Missão Especial', 'status': 'info'},
                'QVJ': {'type': 'justified', 'description': 'Questão de Voto Justificada', 'status': 'info'},
                'MP': {'type': 'justified', 'description': 'Missão Parlamentar', 'status': 'info'},
                'FI': {'type': 'unjustified', 'description': 'Falta Injustificada', 'status': 'danger'},
                'FA': {'type': 'unjustified', 'description': 'Falta', 'status': 'danger'},
                'PNO': {'type': 'other', 'description': 'Presente Não Oficial', 'status': 'secondary'},
                'QV': {'type': 'other', 'description': 'Questão de Voto', 'status': 'secondary'},
                'CO': {'type': 'other', 'description': 'Comissão', 'status': 'secondary'},
                'FIJ': {'type': 'justified', 'description': 'Falta Injustificada (Justificada)', 'status': 'warning'}
            }
            
            for record in attendance_records:
                dt_reuniao, tipo_reuniao, sigla_falta, motivo_falta, pres_justificacao, observacoes, sigla_grupo = record
                
                # Get attendance info
                attendance_info = attendance_codes.get(sigla_falta, {
                    'type': 'other', 
                    'description': f'Código: {sigla_falta}', 
                    'status': 'secondary'
                })
                
                # Build timeline entry
                timeline_entry = {
                    'date': dt_reuniao.isoformat() if dt_reuniao else None,
                    'session_type': tipo_reuniao,
                    'attendance_code': sigla_falta,
                    'attendance_type': attendance_info['type'],
                    'attendance_description': attendance_info['description'],
                    'status': attendance_info['status'],
                    'reason': motivo_falta,
                    'justification': pres_justificacao,
                    'observations': observacoes,
                    'parliamentary_group': sigla_grupo
                }
                
                timeline.append(timeline_entry)
                
                # Update summary
                summary['total_sessions'] += 1
                if attendance_info['type'] == 'present':
                    summary['present'] += 1
                elif attendance_info['type'] == 'justified':
                    summary['justified_absence'] += 1
                elif attendance_info['type'] == 'unjustified':
                    summary['unjustified_absence'] += 1
                else:
                    summary['other'] += 1
            
            # Calculate attendance rate
            attendance_rate = 0
            if summary['total_sessions'] > 0:
                # Present + justified absences count as good attendance
                good_attendance = summary['present'] + summary['justified_absence']
                attendance_rate = good_attendance / summary['total_sessions']
            
            return jsonify({
                'deputado': {
                    'id': deputado.id,
                    'nome': deputado.nome,
                    'nome_completo': deputado.nome_completo
                },
                'summary': {
                    **summary,
                    'attendance_rate': round(attendance_rate, 3)
                },
                'timeline': timeline,
                'codes_legend': attendance_codes
            })
            
    except Exception as e:
        return log_and_return_error(e, f'/api/deputados/{cad_id}/attendance')


# =============================================================================
# VOTING RECORDS ENDPOINTS
# =============================================================================

@parlamento_bp.route('/deputados/<int:cad_id>/votacoes', methods=['GET'])
def get_deputado_votacoes(cad_id):
    """Retorna histórico de votações de um deputado específico"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        with DatabaseSession() as session:
            # Find deputado by cad_id (unique across all legislatures)
            # Get their most recent legislature entry
            deputado = session.query(Deputado).filter(
                Deputado.id_cadastro == cad_id
            ).order_by(Deputado.legislatura_id.desc()).first()
            
            if not deputado:
                return jsonify({'error': 'Deputado não encontrado'}), 404
            
            # Get legislature
            leg = session.query(Legislatura).filter_by(id=deputado.legislatura_id).first()
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
                deputado_id=deputado.id
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
                'legislatura': leg.numero
            })
            
    except Exception as e:
        return log_and_return_error(e, f'/api/deputados/{cad_id}/votacoes')


@parlamento_bp.route('/partidos/<path:partido_sigla>/votacoes', methods=['GET'])
def get_partido_votacoes_by_sigla(partido_sigla):
    """Retorna padrões de votação de um partido específico"""
    try:
        # URL decode the party sigla to handle special characters like slashes
        from urllib.parse import unquote
        partido_sigla = unquote(partido_sigla)
        
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

@parlamento_bp.route('/deputados/<int:cad_id>/voting-analytics', methods=['GET'])
def get_deputado_voting_analytics(cad_id):
    """Retorna análises avançadas de votação para um deputado específico"""
    try:
        from datetime import datetime, timedelta
        import random
        
        with DatabaseSession() as session:
            # Find deputado by cad_id (unique across all legislatures)
            # Get their most recent legislature entry
            deputado = session.query(Deputado).filter(
                Deputado.id_cadastro == cad_id
            ).order_by(Deputado.legislatura_id.desc()).first()
            
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
            
            # Get all initiative voting records to analyze party voting patterns
            all_initiative_votes = session.query(IniciativaEventoVotacao).filter(
                IniciativaEventoVotacao.detalhe.isnot(None)
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
            
            # Parse party voting patterns from initiative votes
            import re
            
            def parse_vote_details(detalhe):
                """Parse the HTML-like vote details to extract both party positions and individual deputy votes"""
                if not detalhe:
                    return {}, {}
                
                # Get valid party siglas from database
                valid_party_siglas = set()
                try:
                    # Add known parties from Partido table
                    parties = session.query(Partido.sigla).distinct().all()
                    for party in parties:
                        if party.sigla:
                            valid_party_siglas.add(party.sigla.strip())
                    
                    # Add parties from mandate data (includes coalitions like PPD/PSD.CDS-PP)
                    mandate_siglas = session.query(DeputadoMandatoLegislativo.par_sigla).distinct().all()
                    for sigla in mandate_siglas:
                        if sigla.par_sigla:
                            valid_party_siglas.add(sigla.par_sigla.strip())
                except Exception:
                    # Fallback to known parties if database query fails
                    valid_party_siglas = {
                        'PSD', 'PS', 'CH', 'IL', 'L', 'PCP', 'CDS-PP', 'PAN', 'JPP', 'BE',
                        'CDU', 'PAF', 'PPD', 'PPD/PSD', 'PPD/PSD.CDS-PP', 'PPD/PSD.CDS-PP.PPM'
                    }
                
                # Clean up HTML tags
                detalhe = detalhe.replace('<I>', '').replace('</I>', '').replace('<BR>', ';')
                
                party_positions = {}
                individual_votes = {}  # {deputy_name: {'vote': vote_type, 'party': party_sigla}}
                
                # Parse each voting position
                for section in detalhe.split(';'):
                    vote_type = None
                    if 'A Favor:' in section:
                        vote_type = 'favor'
                        content = section.replace('A Favor:', '')
                    elif 'Contra:' in section:
                        vote_type = 'contra'
                        content = section.replace('Contra:', '')
                    elif 'Abstenção:' in section or 'Absten��o:' in section:
                        vote_type = 'abstencao'
                        content = section.replace('Abstenção:', '').replace('Absten��o:', '')
                    else:
                        continue
                    
                    if not vote_type:
                        continue
                        
                    # Extract all items from this section
                    items = [item.strip() for item in content.split(',') if item.strip()]
                    
                    for item in items:
                        # Check if it's a valid party sigla
                        if item in valid_party_siglas:
                            party_positions[item] = vote_type
                        # Check if it's an individual deputy vote (contains parentheses with party)
                        elif '(' in item and ')' in item:
                            # Extract deputy name and party: "Sandra Lopes (PS)" -> name="Sandra Lopes", party="PS"
                            try:
                                name_part = item.split('(')[0].strip()
                                party_part = item.split('(')[1].split(')')[0].strip()
                                
                                if party_part in valid_party_siglas:
                                    individual_votes[name_part] = {
                                        'vote': vote_type,
                                        'party': party_part
                                    }
                            except (IndexError, ValueError):
                                continue
                
                return party_positions, individual_votes
            
            # Analyze party's voting record and individual deputy discipline
            party_votes = {'favor': 0, 'contra': 0, 'abstencao': 0, 'ausente': 0}
            party_discipline_data = []
            cross_party_data = {}
            
            # Track individual deputy's alignment with party for discipline calculation
            deputy_alignment_votes = {'aligned': 0, 'total': 0}
            
            if partido_sigla:
                for vote in all_initiative_votes:
                    party_positions, individual_votes = parse_vote_details(vote.detalhe)
                    
                    # Check if deputy's party voted
                    if partido_sigla in party_positions:
                        party_position = party_positions[partido_sigla]
                        party_votes[party_position] += 1
                        
                        # Check if this specific deputy voted individually (breaking party discipline)
                        deputy_individual_vote = None
                        deputy_aligned = True  # Default: assume deputy follows party line
                        
                        # Look for individual votes from deputies of this party
                        for deputy_name, vote_info in individual_votes.items():
                            if vote_info['party'] == partido_sigla:
                                # Check if voting record name matches deputy's parliamentary name
                                deputy_found = False
                                
                                # First try exact match with parliamentary name (nome field)
                                if deputado.nome and deputy_name == deputado.nome:
                                    deputy_found = True
                                # Fallback: check if voting record name matches parts of full name
                                elif deputado.nome_completo and deputy_name:
                                    deputy_name_parts = set(deputy_name.split())
                                    full_name_parts = set(deputado.nome_completo.split())
                                    # If at least 2 name parts match, consider it the same person
                                    matching_parts = deputy_name_parts.intersection(full_name_parts)
                                    if len(matching_parts) >= 2:
                                        deputy_found = True
                                
                                if deputy_found:
                                    deputy_individual_vote = vote_info['vote']
                                    deputy_aligned = (deputy_individual_vote == party_position)
                                    break
                        
                        # Update discipline tracking
                        if vote.data_votacao:
                            deputy_alignment_votes['total'] += 1
                            if deputy_aligned:
                                deputy_alignment_votes['aligned'] += 1
                            
                            party_discipline_data.append({
                                'date': vote.data_votacao.isoformat(),
                                'aligned': deputy_aligned,
                                'vote_type': deputy_individual_vote if deputy_individual_vote else party_position,
                                'party_position': party_position,
                                'individual_vote': deputy_individual_vote is not None
                            })
                        
                        # Track cross-party collaboration
                        for other_party, other_position in party_positions.items():
                            if other_party != partido_sigla:
                                if other_party not in cross_party_data:
                                    cross_party_data[other_party] = {'aligned': 0, 'total': 0}
                                cross_party_data[other_party]['total'] += 1
                                if other_position == party_position:
                                    cross_party_data[other_party]['aligned'] += 1
                    else:
                        # Party was absent from this vote
                        party_votes['ausente'] += 1
            
            # Add budget vote data if available
            for vote_data in orcamento_votacoes:
                voto = vote_data['voto_partido'].lower()
                if voto in party_votes:
                    party_votes[voto] += 1
            
            # Build response structure that matches frontend expectations
            # Using REAL voting data from initiatives
            
            # 1. Vote Distribution - use actual party voting data
            vote_distribution = party_votes
            
            # 2. Party Discipline - calculate real alignment based on individual vs party votes
            party_discipline = None
            if partido_sigla and party_discipline_data:
                # Calculate actual discipline score from individual voting data
                if deputy_alignment_votes['total'] > 0:
                    discipline_score = deputy_alignment_votes['aligned'] / deputy_alignment_votes['total']
                else:
                    # If no individual voting data, assume typical discipline
                    discipline_score = 0.85
                
                # Use real voting timeline data
                timeline = party_discipline_data[-30:]  # Last 30 votes
                
                party_discipline = {
                    'overall_alignment': round(discipline_score, 3),
                    'timeline': timeline,
                    'alignment_stats': {
                        'aligned_votes': deputy_alignment_votes['aligned'],
                        'total_votes': deputy_alignment_votes['total'],
                        'individual_dissent_votes': deputy_alignment_votes['total'] - deputy_alignment_votes['aligned']
                    }
                }
            
            # 3. Participation Timeline - use real voting dates
            participation_timeline = []
            if party_discipline_data:
                # Group votes by date and create participation timeline
                from collections import defaultdict
                daily_participation = defaultdict(lambda: {'participated': 0, 'abstained': 0, 'absent': 0})
                
                for vote_data in party_discipline_data:
                    date = vote_data['date']
                    vote_type = vote_data['vote_type']
                    
                    if vote_type in ['favor', 'contra']:
                        daily_participation[date]['participated'] += 1
                    elif vote_type == 'abstencao':
                        daily_participation[date]['abstained'] += 1
                    else:
                        daily_participation[date]['absent'] += 1
                
                # Convert to list format for frontend
                for date, data in sorted(daily_participation.items(), reverse=True)[:10]:
                    participation_timeline.append({
                        'date': date,
                        **data
                    })
            
            # 4. Cross-party collaboration - use REAL cross-party data
            cross_party_collaboration = []
            if partido_sigla and cross_party_data:
                # Get party names for display
                for other_party_sigla, data in cross_party_data.items():
                    party_obj = session.query(Partido).filter_by(sigla=other_party_sigla).first()
                    alignment_rate = data['aligned'] / data['total'] if data['total'] > 0 else 0
                    
                    cross_party_collaboration.append({
                        'party': other_party_sigla,
                        'party_name': party_obj.nome if party_obj else other_party_sigla,
                        'alignment_rate': round(alignment_rate, 3),
                        'aligned_votes': data['aligned'],
                        'total_votes': data['total']
                    })
                
                # Sort by alignment rate
                cross_party_collaboration.sort(key=lambda x: x['alignment_rate'], reverse=True)
            
            # 5. Theme Analysis - placeholder as we don't have theme categorization
            theme_analysis = []  # Empty array for now - would need vote categorization
            
            # 6. Critical Votes - use actual voting records marked as important
            critical_votes = []
            
            # Get recent important votes (non-unanimous votes are typically more critical)
            important_votes = [v for v in all_initiative_votes if v.unanime != 'Sim'][-10:]
            
            for vote in important_votes:
                party_positions, individual_votes = parse_vote_details(vote.detalhe)
                party_position = party_positions.get(partido_sigla, 'ausente')
                
                critical_votes.append({
                    'id': vote.id,
                    'date': vote.data_votacao.isoformat() if vote.data_votacao else None,
                    'title': vote.descricao or f'Votação Iniciativa ID {vote.id}',
                    'type': 'legislative',  # Initiative votes
                    'deputy_vote': party_position,
                    'result': 'approved' if vote.resultado == 'Aprovado' else 'rejected',
                    'vote_breakdown': party_positions
                })
            
            # Add budget votes as critical too
            for i, vote_data in enumerate(orcamento_votacoes[:3]):
                vote = vote_data['votacao']
                critical_votes.append({
                    'id': f'budget_{vote.id}',
                    'date': vote.data.isoformat() if vote.data else None,
                    'title': vote.descricao or f'Votação Orçamento {i+1}',
                    'type': 'budget',
                    'deputy_vote': vote_data['voto_partido'],
                    'result': 'approved' if vote.resultado == 'Aprovado' else 'rejected'
                })
            
            # Build complete response
            return jsonify({
                'deputy_info': {
                    'id': deputado.id,
                    'name': deputado.nome_completo,
                    'party': {
                        'sigla': partido_sigla,
                        'nome': partido_info.nome if partido_info else None
                    } if partido_sigla else None
                },
                'vote_distribution': vote_distribution,
                'party_discipline': party_discipline,
                'participation_timeline': participation_timeline,
                'cross_party_collaboration': cross_party_collaboration,
                'theme_analysis': theme_analysis,
                'critical_votes': critical_votes
            })
        
    except Exception as e:
        return log_and_return_error(e, f'/api/deputados/{cad_id}/voting-analytics')


@parlamento_bp.route('/partidos/<path:partido_sigla>/voting-analytics', methods=['GET'])
def get_partido_voting_analytics(partido_sigla):
    """Retorna análises avançadas de votação para um partido específico"""
    try:
        # URL decode the party sigla to handle special characters like slashes
        from urllib.parse import unquote
        partido_sigla = unquote(partido_sigla)
        
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
# COALITION API ENDPOINTS
# =============================================================================

@parlamento_bp.route('/coligacoes', methods=['GET'])
def get_coligacoes():
    """Retorna lista de coligações com informações detalhadas"""
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        include_components = request.args.get('include_components', 'false').lower() == 'true'
        
        with DatabaseSession() as session:
            political_queries = PoliticalEntityQueries(session)
            
            # Get all coalitions
            coalitions = session.query(Coligacao).order_by(Coligacao.sigla).all()
            
            # Filter by activity status using calculated property if needed
            if not include_inactive:
                coalitions = [c for c in coalitions if c.ativo]
            
            result = []
            for coalition in coalitions:
                coalition_info = political_queries._format_coalition_entity(coalition, include_components)
                result.append(coalition_info)
            
            return jsonify({
                'coligacoes': result,
                'total': len(result),
                'include_inactive': include_inactive,
                'include_components': include_components
            })
        
    except Exception as e:
        return log_and_return_error(e, '/api/coligacoes')


@parlamento_bp.route('/coligacoes/<path:coligacao_sigla>', methods=['GET'])
def get_coligacao_details(coligacao_sigla):
    """Retorna detalhes de uma coligação específica"""
    try:
        
        include_components = request.args.get('include_components', 'true').lower() == 'true'
        
        with DatabaseSession() as session:
            political_queries = PoliticalEntityQueries(session)
            
            coalition_info = political_queries.get_entity_by_sigla(
                coligacao_sigla, 
                include_components=include_components
            )
            
            if not coalition_info or coalition_info.get('tipo_entidade') != 'coligacao':
                return jsonify({
                    'error': 'Coligação não encontrada',
                    'sigla': coligacao_sigla
                }), 404
            
            return jsonify(coalition_info)
        
    except Exception as e:
        return log_and_return_error(e, f'/api/coligacoes/{coligacao_sigla}')


@parlamento_bp.route('/coligacoes/<path:coligacao_sigla>/deputados', methods=['GET'])
def get_coligacao_deputados(coligacao_sigla):
    """Retorna deputados de uma coligação para uma legislatura específica"""
    try:
        legislatura = request.args.get('legislatura', 'XVII', type=str)
        
        with DatabaseSession() as session:
            political_queries = PoliticalEntityQueries(session)
            
            # Verify coalition exists
            coalition_info = political_queries.get_entity_by_sigla(coligacao_sigla, include_components=False)
            if not coalition_info or coalition_info.get('tipo_entidade') != 'coligacao':
                return jsonify({
                    'error': 'Coligação não encontrada',
                    'sigla': coligacao_sigla
                }), 404
            
            # Get deputies from mandates with coalition context
            deputados_query = session.query(Deputado).join(
                DeputadoMandatoLegislativo, 
                Deputado.id == DeputadoMandatoLegislativo.deputado_id
            ).filter(
                DeputadoMandatoLegislativo.leg_des == legislatura,
                DeputadoMandatoLegislativo.coligacao_contexto_sigla == coligacao_sigla
            ).distinct().order_by(Deputado.nome_completo)
            
            deputados = deputados_query.all()
            
            return jsonify({
                'coligacao': {
                    'sigla': coalition_info['sigla'],
                    'nome': coalition_info['nome'],
                    'tipo_coligacao': coalition_info.get('tipo_coligacao')
                },
                'deputados': [deputado_to_dict(d, session) for d in deputados],
                'total_deputados': len(deputados),
                'legislatura': legislatura
            })
        
    except Exception as e:
        return log_and_return_error(e, f'/api/coligacoes/{coligacao_sigla}/deputados')


@parlamento_bp.route('/coligacoes/<path:coligacao_sigla>/partidos', methods=['GET'])
def get_coligacao_partidos(coligacao_sigla):
    """Retorna partidos componentes de uma coligação"""
    try:
        with DatabaseSession() as session:
            political_queries = PoliticalEntityQueries(session)
            
            coalition_info = political_queries.get_entity_by_sigla(
                coligacao_sigla, 
                include_components=True
            )
            
            if not coalition_info or coalition_info.get('tipo_entidade') != 'coligacao':
                return jsonify({
                    'error': 'Coligação não encontrada',
                    'sigla': coligacao_sigla
                }), 404
            
            return jsonify({
                'coligacao': {
                    'sigla': coalition_info['sigla'],
                    'nome': coalition_info['nome'],
                    'tipo_coligacao': coalition_info.get('tipo_coligacao'),
                    'espectro_politico': coalition_info.get('espectro_politico')
                },
                'partidos_componentes': coalition_info.get('component_parties', []),
                'total_partidos': len(coalition_info.get('component_parties', []))
            })
        
    except Exception as e:
        return log_and_return_error(e, f'/api/coligacoes/{coligacao_sigla}/partidos')


@parlamento_bp.route('/entidades-politicas/search', methods=['GET'])
def search_political_entities():
    """Pesquisa unificada por coligações e partidos"""
    try:
        query_param = request.args.get('q', '', type=str)
        entity_type = request.args.get('type', None, type=str)  # 'coligacao', 'partido', or None for both
        limit = request.args.get('limit', 20, type=int)
        
        if not query_param:
            return jsonify({'entidades': [], 'total': 0})
        
        with DatabaseSession() as session:
            political_queries = PoliticalEntityQueries(session)
            
            entities = political_queries.search_entities(
                query=query_param,
                entity_type=entity_type,
                limit=limit
            )
            
            return jsonify({
                'entidades': entities,
                'total': len(entities),
                'query': query_param,
                'entity_type': entity_type
            })
        
    except Exception as e:
        return log_and_return_error(e, '/api/entidades-politicas/search')


@parlamento_bp.route('/entidades-politicas/statistics', methods=['GET'])
def get_political_entities_statistics():
    """Estatísticas gerais sobre entidades políticas (coligações e partidos)"""
    try:
        with DatabaseSession() as session:
            political_queries = PoliticalEntityQueries(session)
            
            stats = political_queries.get_entity_statistics()
            
            return jsonify({
                'estatisticas': stats,
                'timestamp': func.now()
            })
        
    except Exception as e:
        return log_and_return_error(e, '/api/entidades-politicas/statistics')


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
        active_only = request.args.get('active_only', 'true').lower() == 'true'  # Show only active deputies by default
        
        with DatabaseSession() as session:
            if legislatura:
                # Filter by specific legislature when explicitly requested
                query = session.query(Deputado).join(
                    DeputadoMandatoLegislativo, Deputado.id == DeputadoMandatoLegislativo.deputado_id
                ).filter(
                    DeputadoMandatoLegislativo.leg_des == legislatura
                )
            elif active_only:
                # Default behavior: Show only active deputies (current legislature XVII)
                query = session.query(Deputado).join(
                    DeputadoMandatoLegislativo, Deputado.id == DeputadoMandatoLegislativo.deputado_id
                ).filter(
                    DeputadoMandatoLegislativo.leg_des == 'XVII'  # Current active legislature
                )
            else:
                # Show all unique deputies by id_cadastro (latest entry per person)
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
            elif active_only:
                # When showing active deputies, total = current legislature count
                total_mandatos = total
                view_type = 'active_only'
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
                    'active_only': active_only,
                    'show_all_unique': not bool(legislatura) and not active_only
                },
                'legislatura': legislatura
            })
        
    except Exception as e:
        return log_and_return_error(e, '/api/deputados')