from flask import Blueprint, jsonify, request
from sqlalchemy import func, desc, asc, or_, and_
from app.models.parlamento import db, Deputado, Partido, Legislatura, Mandato, CirculoEleitoral
import sqlite3
import os

parlamento_bp = Blueprint('parlamento', __name__)

def log_and_return_error(e, endpoint_info="", status_code=500):
    """Helper function to log errors to console and return JSON error response"""
    import traceback
    error_msg = f'Error in {endpoint_info}: {str(e)}'
    traceback_msg = f'Traceback: {traceback.format_exc()}'
    
    # Print to console directly
    print(f"\n{'='*50}")
    print(error_msg)
    print(traceback_msg)
    print('='*50)
    
    return jsonify({
        'error': str(e),
        'traceback': traceback.format_exc()
    }), status_code

@parlamento_bp.route('/test', methods=['GET'])
def test_db():
    """Endpoint de teste para verificar conexão com DB"""
    try:
        # Testar contagem simples
        count_deputados = db.session.query(Deputado).count()
        count_partidos = db.session.query(Partido).count()
        
        return jsonify({
            'status': 'ok',
            'deputados': count_deputados,
            'partidos': count_partidos
        })
    except Exception as e:
        return log_and_return_error(e, '/api/test')

@parlamento_bp.route('/deputados', methods=['GET'])
def get_deputados():
    """Retorna lista paginada de deputados com filtros opcionais"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        legislatura = request.args.get('legislatura', '17', type=str)
        
        # Handle both string and integer numero values
        try:
            legislatura_num = int(legislatura)
            leg_filter = Legislatura.numero == legislatura_num
        except ValueError:
            leg_filter = Legislatura.numero == legislatura
        
        # Query deputados with mandatos for the specified legislatura
        query = db.session.query(Deputado).join(
            Mandato, Deputado.id == Mandato.deputado_id
        ).join(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(
            leg_filter,
            Deputado.ativo == True
        )
        
        # Apply search filter if exists
        if search:
            query = query.filter(
                or_(
                    Deputado.nome_completo.contains(search),
                    Deputado.nome.contains(search)
                )
            )
        
        # Order by name
        query = query.order_by(Deputado.nome)
        
        # Pagination
        deputados_paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Build response
        deputados_data = []
        for deputado in deputados_paginated.items:
            deputados_data.append(deputado.to_dict())
        
        return jsonify({
            'deputados': deputados_data,
            'pagination': {
                'total': deputados_paginated.total,
                'pages': deputados_paginated.pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': deputados_paginated.has_next,
                'has_prev': deputados_paginated.has_prev
            }
        })
        
    except Exception as e:
        return log_and_return_error(e, '/api/deputados')


@parlamento_bp.route('/deputados/<int:deputado_id>', methods=['GET'])
def get_deputado(deputado_id):
    """Retorna detalhes de um deputado específico"""
    try:
        deputado = Deputado.query.get_or_404(deputado_id)
        return jsonify(deputado.to_dict())
    except Exception as e:
        return log_and_return_error(e, '/api/deputados/<id>')

@parlamento_bp.route('/deputados/<int:deputado_id>/detalhes', methods=['GET'])
def get_deputado_detalhes(deputado_id):
    """Retorna detalhes completos de um deputado com partido, círculo e estatísticas"""
    try:
        legislatura = request.args.get('legislatura', '17', type=str)
        
        # Buscar o deputado
        deputado = Deputado.query.get_or_404(deputado_id)
        
        # Buscar mandato para a legislatura específica
        leg = db.session.query(Legislatura).filter_by(numero=legislatura).first()
        mandato = None
        
        if leg:
            mandato = db.session.query(Mandato).filter_by(
                deputado_id=deputado_id,
                legislatura_id=leg.id
            ).first()
        
        # Se não encontrar para a legislatura específica, buscar o mais recente
        if not mandato:
            mandato = db.session.query(Mandato).filter_by(
                deputado_id=deputado_id
            ).order_by(Mandato.data_inicio.desc()).first()
        
        deputado_dict = deputado.to_dict()
        
        if mandato:
            # Buscar partido
            partido = db.session.get(Partido, mandato.partido_id)
            if partido:
                deputado_dict['partido'] = {
                    'id': partido.id,
                    'sigla': partido.sigla,
                    'nome': partido.nome
                }
            
            # Buscar círculo eleitoral
            circulo = db.session.get(CirculoEleitoral, mandato.circulo_id)
            if circulo:
                deputado_dict['circulo'] = circulo.designacao
            
            # Determinar se o mandato está "ativo" baseado na legislatura selecionada
            # Um mandato é considerado ativo se for da legislatura atual selecionada
            mandato_ativo = (leg and mandato.legislatura_id == leg.id)
            
            # Informações do mandato
            deputado_dict['mandato'] = {
                'id': mandato.id,
                'inicio': mandato.data_inicio.isoformat() if mandato.data_inicio else None,
                'fim': mandato.data_fim.isoformat() if mandato.data_fim else None,
                'ativo': mandato_ativo,
                'legislatura': legislatura,
                'posicao_lista': mandato.posicao_lista,
                'votos_obtidos': mandato.votos_obtidos
            }
        else:
            deputado_dict['partido'] = None
            deputado_dict['circulo'] = None
            deputado_dict['mandato'] = None
        
        # Get legislatura_id for filtering statistics
        leg = db.session.query(Legislatura).filter_by(numero=legislatura).first()
        leg_id = leg.id if leg else None
        
        # Get committee memberships (organ activities) for this deputy
        comissoes_query = """
        SELECT c.nome, c.sigla, mc.cargo, mc.titular, c.tipo, 
               CASE WHEN mc.titular = 1 THEN 'Efetivo' ELSE 'Suplente' END as tipo_membro,
               mc.observacoes, c.id as comissao_id
        FROM membros_comissoes mc
        JOIN comissoes c ON mc.comissao_id = c.id
        WHERE mc.deputado_id = ?
        ORDER BY c.nome
        """
        
        import sqlite3
        import os
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'parlamento.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(comissoes_query, (deputado_id,))
        comissoes_data = cursor.fetchall()
        
        # Format committee data
        deputado_dict['atividades_orgaos'] = []
        for comissao_row in comissoes_data:
            deputado_dict['atividades_orgaos'].append({
                'nome': comissao_row[0],
                'sigla': comissao_row[1],
                'cargo': comissao_row[2],
                'titular': bool(comissao_row[3]),
                'tipo': comissao_row[4],
                'tipo_membro': comissao_row[5],
                'observacoes': comissao_row[6],
                'comissao_id': comissao_row[7]
            })
        
        # Calcular estatísticas reais filtradas por legislatura
        
        # Contar intervenções na legislatura específica (join with intervencoes_deputados)
        if leg_id:
            cursor.execute('''
                SELECT COUNT(*) 
                FROM intervencoes i
                JOIN intervencoes_deputados id ON i.id = id.intervencao_id
                JOIN deputados d ON id.id_cadastro = d.id_cadastro
                WHERE d.id = ? AND i.legislatura_numero = ?
            ''', (deputado_id, legislatura))
            total_intervencoes = cursor.fetchone()[0]
        else:
            total_intervencoes = 0
        
        # Contar iniciativas na legislatura específica (usa deputado.id)
        if leg_id:
            cursor.execute('''
                SELECT COUNT(*) FROM autores_iniciativas a 
                JOIN iniciativas_legislativas i ON a.iniciativa_id = i.id
                WHERE a.deputado_id = ? AND i.legislatura_id = ?
            ''', (deputado_id, leg_id))
            total_iniciativas = cursor.fetchone()[0]
        else:
            total_iniciativas = 0
        
        # Contar votações na legislatura específica (usa deputado.id)
        if leg_id:
            cursor.execute('''
                SELECT COUNT(*) FROM votos_individuais vi
                JOIN votacoes v ON vi.votacao_id = v.id
                WHERE vi.deputado_id = ? AND v.legislatura_id = ?
            ''', (deputado_id, leg_id))
            total_votacoes = cursor.fetchone()[0]
        else:
            total_votacoes = 0
        
        # Get real attendance data from metricas_deputados for the selected legislatura
        attendance_query = """
        SELECT taxa_assiduidade, total_votacoes_participadas 
        FROM metricas_deputados 
        WHERE deputado_id = ? AND legislatura_id = (
            SELECT id FROM legislaturas WHERE numero = ?
        )
        """
        cursor.execute(attendance_query, (deputado_id, legislatura))
        attendance_result = cursor.fetchone()
        
        if attendance_result:
            taxa_assiduidade = attendance_result[0] / 100.0  # Convert percentage to decimal
            total_votacoes_participadas = attendance_result[1]
        else:
            # Fallback if no metrics found for this legislatura
            taxa_assiduidade = 0.0
            total_votacoes_participadas = total_votacoes
        
        conn.close()
        
        deputado_dict['estatisticas'] = {
            'total_intervencoes': total_intervencoes,
            'total_iniciativas': total_iniciativas,
            'total_votacoes': total_votacoes_participadas,
            'taxa_assiduidade': taxa_assiduidade,
            'total_mandatos': db.session.query(Mandato).filter_by(deputado_id=deputado_id).count()
        }
        
        return jsonify(deputado_dict)
        
    except Exception as e:
        return log_and_return_error(e, '/api/deputados/<id>/detalhes')

@parlamento_bp.route('/deputados/<int:deputado_id>/atividades', methods=['GET'])
def get_deputado_atividades(deputado_id):
    """Retorna atividades parlamentares de um deputado"""
    try:
        # Verificar se o deputado existe
        deputado = Deputado.query.get_or_404(deputado_id)
        legislatura = request.args.get('legislatura', '17', type=str)
        
        # Get legislatura_id for filtering
        leg = db.session.query(Legislatura).filter_by(numero=legislatura).first()
        if not leg:
            return jsonify({
                'intervencoes': [],
                'iniciativas': [],
                'votacoes': []
            })
        
        # Use both deputado.id and deputado.id_cadastro for different tables
        deputado_id = deputado.id
        id_cadastro = deputado.id_cadastro
        
        
        # Fetch initiatives (uses id_cadastro via autores_iniciativas)
        # Only proceed if deputado has id_cadastro
        iniciativas_query = """
            SELECT i.titulo, i.data_apresentacao, i.tipo, i.tipo_descricao, i.estado, i.resultado
            FROM iniciativas_legislativas i
            JOIN autores_iniciativas a ON i.id = a.iniciativa_id
            WHERE a.deputado_id = ? AND i.legislatura_id = ?
            ORDER BY i.data_apresentacao DESC
            LIMIT 20
        """
        
        # Fetch recent votes (uses deputado.id)
        votos_query = """
            SELECT v.objeto_votacao, v.data_votacao, v.resultado, vi.voto, vi.justificacao
            FROM votacoes v
            JOIN votos_individuais vi ON v.id = vi.votacao_id
            WHERE vi.deputado_id = ? AND v.legislatura_id = ?
            ORDER BY v.data_votacao DESC
            LIMIT 20
        """
        
        # Execute queries using raw SQL
        import sqlite3
        import os
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'parlamento.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get interventions with comprehensive data
        intervencoes_query = """
            SELECT 
                i.tipo_intervencao, i.data_reuniao_plenaria, i.sumario, i.resumo, 
                i.fase_sessao, i.sessao_numero, i.qualidade, i.atividade_id, i.id_debate,
                av.url_video, av.thumbnail_url, av.assunto, av.duracao,
                p.pub_numero, p.pub_tipo, p.pub_data, p.paginas, p.url_diario,
                p.pub_legislatura, p.pub_serie_legislatura
            FROM intervencoes i
            JOIN intervencoes_deputados id ON i.id = id.intervencao_id
            JOIN deputados d ON id.id_cadastro = d.id_cadastro
            LEFT JOIN intervencoes_audiovisual av ON i.id = av.intervencao_id
            LEFT JOIN intervencoes_publicacoes p ON i.id = p.intervencao_id
            WHERE d.id = ? AND i.legislatura_numero = ?
            ORDER BY i.data_reuniao_plenaria DESC
            LIMIT 20
        """
        
        # Convert numeric legislatura to Roman numeral for interventions query
        roman_map = {
            '17': 'XVII', '16': 'XVI', '15': 'XV', '14': 'XIV', '13': 'XIII',
            '12': 'XII', '11': 'XI', '10': 'X', '9': 'IX', '8': 'VIII',
            '7': 'VII', '6': 'VI', '5': 'V', '4': 'IV', '3': 'III',
            '2': 'II', '1': 'I', '0': 'CONSTITUINTE'
        }
        legislatura_roman = roman_map.get(legislatura, legislatura)
        
        cursor.execute(intervencoes_query, (deputado_id, legislatura_roman))
        intervencoes = []
        for row in cursor.fetchall():
            intervencao = {
                'tipo': row[0],
                'data': row[1],
                'sumario': row[2],
                'resumo': row[3],
                'fase_sessao': row[4],
                'sessao_numero': row[5],
                'qualidade': row[6],
                'atividade_id': row[7],
                'id_debate': row[8],
                'url_video': row[9],
                'thumbnail_url': row[10],
                'assunto': row[11],
                'duracao_video': row[12],
                'publicacao': {
                    'pub_numero': row[13],
                    'pub_tipo': row[14],
                    'pub_data': row[15],
                    'paginas': row[16],
                    'url_diario': row[17],
                    'pub_legislatura': row[18],
                    'pub_serie_legislatura': row[19]
                } if row[13] or row[17] else None
            }
            intervencoes.append(intervencao)
        
        # Get initiatives (use deputado.id)
        cursor.execute(iniciativas_query, (deputado_id, leg.id))
        iniciativas = []
        for row in cursor.fetchall():
            iniciativas.append({
                'titulo': row[0],
                'data_apresentacao': row[1],
                'tipo': row[2],
                'tipo_descricao': row[3],
                'estado': row[4],
                'resultado': row[5]
            })
        
        # Get votes (use deputado.id)
        cursor.execute(votos_query, (deputado_id, leg.id))
        votacoes = []
        for row in cursor.fetchall():
            votacoes.append({
                'objeto_votacao': row[0],
                'data_votacao': row[1],
                'resultado': row[2],
                'voto_deputado': row[3],
                'justificacao': row[4]
            })
        
        conn.close()
        
        return jsonify({
            'intervencoes': intervencoes,
            'iniciativas': iniciativas,
            'votacoes': votacoes
        })
        
    except Exception as e:
        return log_and_return_error(e, '/api/deputados/<id>/atividades')


@parlamento_bp.route('/partidos/<int:partido_id>', methods=['GET'])
def get_partido(partido_id):
    """Retorna detalhes de um partido específico"""
    try:
        partido = Partido.query.get_or_404(partido_id)
        return jsonify(partido.to_dict())
    except Exception as e:
        return log_and_return_error(e, '/api/partidos/<id>')

@parlamento_bp.route('/partidos/<int:partido_id>/deputados', methods=['GET'])
def get_partido_deputados(partido_id):
    """Retorna detalhes de um partido com seus deputados"""
    try:
        legislatura = request.args.get('legislatura', '17', type=str)
        
        # Buscar o partido
        partido = Partido.query.get_or_404(partido_id)
        
        # Buscar deputados do partido com mandatos na legislatura especificada
        deputados_query = db.session.query(Deputado, Mandato, CirculoEleitoral).join(
            Mandato, Deputado.id == Mandato.deputado_id
        ).join(
            CirculoEleitoral, Mandato.circulo_id == CirculoEleitoral.id
        ).join(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(
            Mandato.partido_id == partido_id,
            Legislatura.numero == legislatura
        ).order_by(Deputado.nome_completo)
        
        deputados_data = []
        for deputado, mandato, circulo in deputados_query.all():
            deputado_dict = deputado.to_dict()
            deputado_dict['circulo'] = circulo.designacao
            # Calculate if mandate is truly active (no end date and marked as active)
            # Explicitly convert to boolean to handle SQLAlchemy types
            deputado_dict['mandato_ativo'] = bool(mandato.ativo) and (mandato.data_fim is None)
            deputados_data.append(deputado_dict)
        
        return jsonify({
            'partido': partido.to_dict(),
            'deputados': deputados_data,
            'total': len(deputados_data)
        })
        
    except Exception as e:
        return log_and_return_error(e, '/api/partidos/<id>/deputados')

@parlamento_bp.route('/partidos/<int:partido_id>/votacoes', methods=['GET'])
def get_partido_votacoes(partido_id):
    """Retorna estatísticas de votações agregadas de um partido"""
    try:
        legislatura = request.args.get('legislatura', '17', type=str)
        
        # Buscar o partido
        partido = Partido.query.get_or_404(partido_id)
        
        # Buscar todos os deputados do partido na legislatura especificada
        deputados_ids = db.session.query(Deputado.id).join(
            Mandato, Deputado.id == Mandato.deputado_id
        ).join(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(
            Mandato.partido_id == partido_id,
            Legislatura.numero == legislatura
        ).all()
        
        deputados_ids = [d[0] for d in deputados_ids]
        
        if not deputados_ids:
            return jsonify({
                'partido': partido.to_dict(),
                'votacoes': [],
                'estatisticas': {
                    'total_votacoes': 0,
                    'distribuicao': [],
                    'eficacia_media': 0
                }
            })
        
        # Connect to parlamento.db for voting data
        parliament_db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'parlamento.db')
        conn = sqlite3.connect(parliament_db_path)
        cursor = conn.cursor()
        
        # Get all votes from all deputies in the party
        placeholders = ','.join(['?' for _ in deputados_ids])
        cursor.execute(f"""
            SELECT vi.voto, v.resultado, COUNT(*) as count
            FROM votos_individuais vi
            JOIN votacoes v ON vi.votacao_id = v.id
            WHERE vi.deputado_id IN ({placeholders})
            GROUP BY vi.voto, v.resultado
            ORDER BY vi.voto, v.resultado
        """, deputados_ids)
        
        vote_results = cursor.fetchall()
        
        # Calculate aggregated statistics
        total_votes = 0
        vote_distribution = {}
        successful_votes = 0
        
        for voto, resultado, count in vote_results:
            total_votes += count
            
            # Count vote types
            vote_type = 'A Favor' if voto == 'favor' else \
                       'Contra' if voto == 'contra' else 'Abstenção'
            vote_distribution[vote_type] = vote_distribution.get(vote_type, 0) + count
            
            # Count successful votes (align with outcome)
            if (voto == 'favor' and resultado == 'aprovada') or \
               (voto == 'contra' and resultado == 'rejeitada'):
                successful_votes += count
        
        # Prepare distribution data for pie chart
        distribution = []
        for vote_type, count in vote_distribution.items():
            distribution.append({
                'name': vote_type,
                'value': count,
                'percentage': round((count / total_votes * 100), 1) if total_votes > 0 else 0
            })
        
        efficacy = round((successful_votes / total_votes * 100), 1) if total_votes > 0 else 0
        
        # Get recent votes for display
        cursor.execute(f"""
            SELECT v.objeto_votacao, vi.voto, v.resultado, v.data_votacao, COUNT(*) as deputy_count
            FROM votos_individuais vi
            JOIN votacoes v ON vi.votacao_id = v.id
            WHERE vi.deputado_id IN ({placeholders})
            GROUP BY v.objeto_votacao, vi.voto, v.resultado, v.data_votacao
            ORDER BY v.data_votacao DESC
            LIMIT 20
        """, deputados_ids)
        
        recent_votes = []
        for row in cursor.fetchall():
            objeto, voto, resultado, data, deputy_count = row
            recent_votes.append({
                'objeto_votacao': objeto,
                'voto_deputado': voto,
                'resultado': resultado,
                'data_votacao': data,
                'deputy_count': deputy_count
            })
        
        conn.close()
        
        return jsonify({
            'partido': partido.to_dict(),
            'votacoes': recent_votes,
            'estatisticas': {
                'total_votacoes': total_votes,
                'distribuicao': distribution,
                'eficacia_media': efficacy,
                'total_deputados': len(deputados_ids)
            }
        })
        
    except Exception as e:
        return log_and_return_error(e, '/api/partidos/<id>/votacoes')

@parlamento_bp.route('/circulos', methods=['GET'])
def get_circulos():
    """Retorna lista de círculos eleitorais com contagem de deputados para a legislatura especificada"""
    try:
        legislatura = request.args.get('legislatura', '17', type=str)
        
        circulos = db.session.query(
            CirculoEleitoral,
            func.count(Mandato.id).label('num_deputados')
        ).outerjoin(Mandato, CirculoEleitoral.id == Mandato.circulo_id).outerjoin(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(
            Legislatura.numero == legislatura
        ).group_by(CirculoEleitoral.id).order_by(desc('num_deputados')).all()
        
        result = []
        for circulo, num_deputados in circulos:
            if num_deputados > 0:  # Only show circles with deputies in current legislature
                circulo_dict = circulo.to_dict()
                circulo_dict['num_deputados'] = num_deputados
                result.append(circulo_dict)
        
        return jsonify(result)
        
    except Exception as e:
        return log_and_return_error(e, '/api/circulos')

@parlamento_bp.route('/estatisticas', methods=['GET'])
def get_estatisticas():
    """Retorna estatísticas gerais do parlamento para uma legislatura específica"""
    try:
        legislatura = request.args.get('legislatura', '17', type=str)
        
        # Totais baseados na legislatura especificada
        total_deputados = db.session.query(func.count(func.distinct(Mandato.deputado_id))).join(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(Legislatura.numero == legislatura).scalar()
        
        total_partidos = db.session.query(func.count(func.distinct(Mandato.partido_id))).join(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(Legislatura.numero == legislatura).scalar()
        
        total_circulos = db.session.query(func.count(func.distinct(Mandato.circulo_id))).join(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(Legislatura.numero == legislatura).scalar()
        
        total_mandatos = db.session.query(func.count(Mandato.id)).join(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(Legislatura.numero == legislatura).scalar()
        
        # Distribuição por partidos para a legislatura especificada
        distribuicao_partidos = db.session.query(
            Partido.sigla,
            Partido.designacao_completa.label('nome'),
            func.count(Mandato.id).label('deputados')
        ).outerjoin(Mandato).outerjoin(Legislatura, Mandato.legislatura_id == Legislatura.id).filter(
            Legislatura.numero == legislatura
        ).group_by(Partido.id).order_by(desc('deputados')).all()
        
        # Distribuição por círculos eleitorais para a legislatura especificada
        distribuicao_circulos = db.session.query(
            CirculoEleitoral.designacao.label('circulo'),
            func.count(Mandato.id).label('deputados')
        ).outerjoin(Mandato, CirculoEleitoral.id == Mandato.circulo_id).outerjoin(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(
            Legislatura.numero == legislatura
        ).group_by(CirculoEleitoral.id).order_by(desc('deputados')).limit(10).all()
        
        # Maior partido
        maior_partido = distribuicao_partidos[0] if distribuicao_partidos else None
        
        # Maior círculo eleitoral
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
                    'sigla': p.sigla,
                    'nome': p.nome,
                    'deputados': p.deputados
                } for p in distribuicao_partidos
            ],
            'distribuicao_circulos': [
                {
                    'circulo': c.circulo,
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
        return jsonify({'error': str(e)}), 500


@parlamento_bp.route('/search', methods=['GET'])
def search():
    """Pesquisa global por deputados e partidos"""
    try:
        query = request.args.get('q', '', type=str)
        legislatura = request.args.get('legislatura', '17', type=str)
        
        if not query:
            return jsonify({'deputados': [], 'partidos': []})
        
        # Pesquisar deputados (filtrado por legislatura)
        deputados = db.session.query(Deputado).join(
            Mandato, Deputado.id == Mandato.deputado_id
        ).join(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(
            Deputado.nome_completo.contains(query),
            Legislatura.numero == legislatura
        ).limit(10).all()
        
        # Pesquisar partidos (filtrado por legislatura)
        partidos = db.session.query(Partido).join(
            Mandato, Partido.id == Mandato.partido_id
        ).join(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(
            (Partido.sigla.contains(query) | Partido.designacao_completa.contains(query)),
            Legislatura.numero == legislatura
        ).limit(5).all()
        
        return jsonify({
            'deputados': [d.to_dict() for d in deputados],
            'partidos': [p.to_dict() for p in partidos]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parlamento_bp.route('/feed/atividades', methods=['GET'])
def get_atividades_feed():
    """Retorna feed de atividades parlamentares organizadas por data"""
    try:
        legislatura = request.args.get('legislatura', '17', type=str)
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        tipo_filter = request.args.get('tipo', '')
        
        # Get legislatura_id
        leg = db.session.query(Legislatura).filter_by(numero=legislatura).first()
        if not leg:
            return jsonify({'atividades': [], 'total': 0})
        
        import sqlite3
        import os
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'parlamento.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query to get all activities ordered by date (initiatives, interventions, votes)
        offset = (page - 1) * per_page
        
        # Build query based on type filter
        iniciativas_query = '''
        SELECT 'iniciativa' as tipo, 
               i.id, i.titulo as titulo, i.data_apresentacao as data, 
               i.tipo as subtipo, i.tipo_descricao as descricao,
               NULL as resultado_votacao
        FROM iniciativas_legislativas i 
        WHERE i.legislatura_id = ? AND i.data_apresentacao IS NOT NULL
        '''
        
        intervencoes_query = '''
        SELECT 'intervencao' as tipo,
               int.id, int.tipo_intervencao as titulo, int.data_intervencao as data,
               int.tipo_intervencao as subtipo, int.resumo as descricao,
               NULL as resultado_votacao, 
               int.url_video, int.thumbnail_url, int.assunto, int.duracao_video
        FROM intervencoes int
        WHERE int.legislatura_id = ? AND int.data_intervencao IS NOT NULL
        '''
        
        votacoes_query = '''
        SELECT 'votacao' as tipo,
               v.id, v.objeto_votacao as titulo, v.data_votacao as data,
               v.tipo_votacao as subtipo, v.objeto_votacao as descricao,
               v.resultado as resultado_votacao
        FROM votacoes v
        WHERE v.legislatura_id = ? AND v.data_votacao IS NOT NULL
        '''
        
        # Build final query based on filter
        if tipo_filter == 'iniciativa':
            query = iniciativas_query + ' ORDER BY data DESC LIMIT ? OFFSET ?'
            query_params = (leg.id, per_page, offset)
            cursor.execute(query, query_params)
            atividades = []
            for row in cursor.fetchall():
                atividade = {
                    'tipo': row[0],
                    'id': row[1],
                    'titulo': row[2],
                    'data': row[3],
                    'subtipo': row[4],
                    'descricao': row[5][:200] + '...' if row[5] and len(row[5]) > 200 else row[5],
                    'resultado_votacao': None
                }
                atividades.append(atividade)
        elif tipo_filter == 'intervencao':
            query = intervencoes_query + ' ORDER BY data DESC LIMIT ? OFFSET ?'
            query_params = (leg.id, per_page, offset)
            cursor.execute(query, query_params)
            atividades = []
            for row in cursor.fetchall():
                atividade = {
                    'tipo': row[0],
                    'id': row[1],
                    'titulo': row[2],
                    'data': row[3],
                    'subtipo': row[4],
                    'descricao': row[5][:200] + '...' if row[5] and len(row[5]) > 200 else row[5],
                    'resultado_votacao': None,
                    'url_video': row[7],
                    'thumbnail_url': row[8],
                    'assunto': row[9],
                    'duracao_video': row[10]
                }
                atividades.append(atividade)
        elif tipo_filter == 'votacao':
            query = votacoes_query + ' ORDER BY data DESC LIMIT ? OFFSET ?'
            query_params = (leg.id, per_page, offset)
            cursor.execute(query, query_params)
            atividades = []
            for row in cursor.fetchall():
                atividade = {
                    'tipo': row[0],
                    'id': row[1],
                    'titulo': row[2],
                    'data': row[3],
                    'subtipo': row[4],
                    'descricao': row[5][:200] + '...' if row[5] and len(row[5]) > 200 else row[5],
                    'resultado_votacao': row[6]
                }
                atividades.append(atividade)
        else:
            # All types - handle each separately to include video data for interventions
            atividades = []
            
            # Get initiatives
            cursor.execute(iniciativas_query + ' ORDER BY data DESC LIMIT ?', (leg.id, per_page // 3))
            for row in cursor.fetchall():
                atividade = {
                    'tipo': row[0],
                    'id': row[1],
                    'titulo': row[2],
                    'data': row[3],
                    'subtipo': row[4],
                    'descricao': row[5][:200] + '...' if row[5] and len(row[5]) > 200 else row[5],
                    'resultado_votacao': None
                }
                atividades.append(atividade)
            
            # Get interventions with video data
            cursor.execute(intervencoes_query + ' ORDER BY data DESC LIMIT ?', (leg.id, per_page // 3))
            for row in cursor.fetchall():
                atividade = {
                    'tipo': row[0],
                    'id': row[1],
                    'titulo': row[2],
                    'data': row[3],
                    'subtipo': row[4],
                    'descricao': row[5][:200] + '...' if row[5] and len(row[5]) > 200 else row[5],
                    'resultado_votacao': None,
                    'url_video': row[7],
                    'thumbnail_url': row[8],
                    'assunto': row[9],
                    'duracao_video': row[10]
                }
                atividades.append(atividade)
            
            # Get votes
            cursor.execute(votacoes_query + ' ORDER BY data DESC LIMIT ?', (leg.id, per_page // 3))
            for row in cursor.fetchall():
                atividade = {
                    'tipo': row[0],
                    'id': row[1],
                    'titulo': row[2],
                    'data': row[3],
                    'subtipo': row[4],
                    'descricao': row[5][:200] + '...' if row[5] and len(row[5]) > 200 else row[5],
                    'resultado_votacao': row[6]
                }
                atividades.append(atividade)
            
            # Sort all activities by date
            atividades.sort(key=lambda x: x['data'], reverse=True)
            atividades = atividades[:per_page]
        
        # Get total count based on filter
        if tipo_filter == 'iniciativa':
            count_query = 'SELECT COUNT(*) FROM iniciativas_legislativas WHERE legislatura_id = ? AND data_apresentacao IS NOT NULL'
            count_params = (leg.id,)
        elif tipo_filter == 'intervencao':
            count_query = 'SELECT COUNT(*) FROM intervencoes WHERE legislatura_id = ? AND data_intervencao IS NOT NULL'
            count_params = (leg.id,)
        elif tipo_filter == 'votacao':
            count_query = 'SELECT COUNT(*) FROM votacoes WHERE legislatura_id = ? AND data_votacao IS NOT NULL'
            count_params = (leg.id,)
        else:
            count_query = '''
            SELECT COUNT(*) FROM (
                SELECT 1 FROM iniciativas_legislativas WHERE legislatura_id = ? AND data_apresentacao IS NOT NULL
                UNION ALL
                SELECT 1 FROM intervencoes WHERE legislatura_id = ? AND data_intervencao IS NOT NULL  
                UNION ALL
                SELECT 1 FROM votacoes WHERE legislatura_id = ? AND data_votacao IS NOT NULL
            )
            '''
            count_params = (leg.id, leg.id, leg.id)
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'atividades': atividades,
            'total': total,
            'page': page,
            'per_page': per_page,
            'has_next': offset + per_page < total,
            'has_prev': page > 1
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@parlamento_bp.route('/feed/atividades/<string:tipo>/<int:atividade_id>/participantes', methods=['GET'])
def get_atividade_participantes(tipo, atividade_id):
    """Retorna todos os deputados que participaram numa atividade específica"""
    try:
        legislatura = request.args.get('legislatura', '17', type=str)
        
        import sqlite3
        import os
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'parlamento.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        participantes = []
        
        if tipo == 'iniciativa':
            # Get authors of initiative
            query = '''
            SELECT d.id, d.nome_completo, d.nome, p.sigla as partido, 
                   ai.tipo_autor, 'autor' as papel
            FROM autores_iniciativas ai
            JOIN deputados d ON ai.deputado_id = d.id
            LEFT JOIN mandatos m ON d.id = m.deputado_id
            LEFT JOIN partidos p ON m.partido_id = p.id
            WHERE ai.iniciativa_id = ?
            '''
            cursor.execute(query, (atividade_id,))
            
        elif tipo == 'intervencao':
            # Get deputy who made the intervention
            query = '''
            SELECT d.id, d.nome_completo, d.nome, p.sigla as partido,
                   'orador' as tipo_autor, 'orador' as papel
            FROM intervencoes i
            JOIN deputados d ON i.deputado_id = d.id
            LEFT JOIN mandatos m ON d.id = m.deputado_id  
            LEFT JOIN partidos p ON m.partido_id = p.id
            WHERE i.id = ?
            '''
            cursor.execute(query, (atividade_id,))
            
        elif tipo == 'votacao':
            # Get all deputies who voted
            query = '''
            SELECT d.id, d.nome_completo, d.nome, p.sigla as partido,
                   vi.voto as tipo_autor, vi.voto as papel
            FROM votos_individuais vi
            JOIN deputados d ON vi.deputado_id = d.id
            LEFT JOIN mandatos m ON d.id = m.deputado_id
            LEFT JOIN partidos p ON m.partido_id = p.id
            WHERE vi.votacao_id = ?
            ORDER BY vi.voto, d.nome_completo
            '''
            cursor.execute(query, (atividade_id,))
        
        for row in cursor.fetchall():
            participante = {
                'deputado_id': row[0],
                'nome_completo': row[1],
                'nome': row[2],
                'partido': row[3],
                'tipo_participacao': row[4],
                'papel': row[5]
            }
            participantes.append(participante)
        
        conn.close()
        
        return jsonify({
            'tipo_atividade': tipo,
            'atividade_id': atividade_id,
            'participantes': participantes,
            'total_participantes': len(participantes)
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@parlamento_bp.route('/deputados/<int:deputado_id>/biografia', methods=['GET'])
def get_deputado_biografia(deputado_id):
    """Retorna dados biográficos de um deputado"""
    try:
        # Get the deputado to find their cadastro_id
        deputado = Deputado.query.get_or_404(deputado_id)
        cadastro_id = deputado.id_cadastro
        
        if not cadastro_id:
            return jsonify({'error': 'Cadastro ID não encontrado para este deputado'}), 404
        
        # Connect to parliament_data.db for biographical data
        parliament_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'parliament_data.db')
        conn = sqlite3.connect(parliament_db_path)
        cursor = conn.cursor()
        
        # Get biographical record - now using integer matching
        cursor.execute("""
            SELECT cadastro_id, nome_completo, data_nascimento, sexo, profissao
            FROM biographical_records 
            WHERE cadastro_id = ?
        """, (cadastro_id,))
        
        bio_result = cursor.fetchone()
        if not bio_result:
            conn.close()
            return jsonify({'error': 'Dados biográficos não encontrados'}), 404
        
        biografia = {
            'cadastro_id': bio_result[0],
            'nome_completo': bio_result[1],
            'data_nascimento': bio_result[2],
            'sexo': bio_result[3],
            'profissao': bio_result[4]
        }
        
        # Get qualifications
        cursor.execute("""
            SELECT descricao, tipo_id, estado
            FROM qualifications 
            WHERE cadastro_id = ?
            ORDER BY tipo_id
        """, (cadastro_id,))
        
        qualifications = []
        for row in cursor.fetchall():
            qualifications.append({
                'descricao': row[0],
                'tipo_id': row[1],
                'estado': row[2]
            })
        
        # Get positions
        cursor.execute("""
            SELECT descricao, ordem, antiga
            FROM positions 
            WHERE cadastro_id = ?
            ORDER BY ordem
        """, (cadastro_id,))
        
        positions = []
        for row in cursor.fetchall():
            positions.append({
                'descricao': row[0],
                'ordem': row[1],
                'antiga': row[2]
            })
        
        # Get decorations
        cursor.execute("""
            SELECT descricao, ordem
            FROM decorations 
            WHERE cadastro_id = ?
            ORDER BY ordem
        """, (cadastro_id,))
        
        decorations = []
        for row in cursor.fetchall():
            decorations.append({
                'descricao': row[0],
                'ordem': row[1]
            })
        
        conn.close()
        
        biografia['qualifications'] = qualifications
        biografia['positions'] = positions
        biografia['decorations'] = decorations
        
        return jsonify(biografia)
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@parlamento_bp.route('/deputados/<int:deputado_id>/conflitos-interesse', methods=['GET'])
def get_deputado_conflitos_interesse(deputado_id):
    """Retorna dados de conflitos de interesse de um deputado"""
    try:
        # Get the deputado to find their full name for matching
        deputado = Deputado.query.get_or_404(deputado_id)
        
        # Connect to parlamento.db for conflicts of interest data
        parliament_db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'parlamento.db')
        conn = sqlite3.connect(parliament_db_path)
        cursor = conn.cursor()
        
        # Get the current legislatura from request
        legislatura = request.args.get('legislatura', '17', type=str)
        
        # Get conflicts of interest record - match by full name and legislatura
        cursor.execute("""
            SELECT record_id, legislatura, full_name, marital_status, spouse_name, matrimonial_regime, exclusivity, dgf_number
            FROM conflicts_of_interest 
            WHERE (full_name LIKE ? OR full_name LIKE ?) AND legislatura = ?
        """, (f"%{deputado.nome_completo}%", f"%{deputado.nome}%", legislatura))
        
        conflicts_result = cursor.fetchone()
        conn.close()
        
        if not conflicts_result:
            return jsonify({'error': 'Dados de conflitos de interesse não encontrados'}), 404
        
        spouse_name = conflicts_result[4]
        spouse_deputy = None
        
        # Check if spouse is also a deputy
        if spouse_name:
            # Clean up spouse name for better matching
            spouse_name_clean = spouse_name.strip()
            
            # Only try exact matches to avoid false positives
            # Try exact match with full name (case insensitive)
            spouse_deputy_query = db.session.query(Deputado).filter(
                func.lower(Deputado.nome_completo) == func.lower(spouse_name_clean)
            ).first()
            
            # If no exact match, try exact match with short name
            if not spouse_deputy_query:
                spouse_deputy_query = db.session.query(Deputado).filter(
                    func.lower(Deputado.nome) == func.lower(spouse_name_clean)
                ).first()
            
            # Only if we have at least 3 name parts, try very strict matching
            # This requires first name + at least one middle name + last name to match
            if not spouse_deputy_query and len(spouse_name_clean.split()) >= 3:
                name_parts = spouse_name_clean.split()
                first_name = name_parts[0].lower()
                second_name = name_parts[1].lower() if len(name_parts) > 1 else ""
                last_name = name_parts[-1].lower()
                
                # Ultra-strict matching: first name, second name, AND last name must all match
                # This significantly reduces false positives
                if len(second_name) > 2:  # Only match meaningful second names (not "de", "da", etc.)
                    spouse_deputy_query = db.session.query(Deputado).filter(
                        and_(
                            func.lower(Deputado.nome_completo).like(f'{first_name} %'),     # First name at start
                            func.lower(Deputado.nome_completo).like(f'% {second_name} %'), # Second name as whole word
                            func.lower(Deputado.nome_completo).like(f'% {last_name}%')     # Last name as whole word
                        )
                    ).first()
                    
                    # Alternative: first name + second name at start, last name at end
                    if not spouse_deputy_query:
                        spouse_deputy_query = db.session.query(Deputado).filter(
                            and_(
                                func.lower(Deputado.nome_completo).like(f'{first_name} {second_name} %'),
                                func.lower(Deputado.nome_completo).like(f'% {last_name}%')
                            )
                        ).first()
            
            if spouse_deputy_query:
                # Get party information for the spouse
                spouse_mandato = db.session.query(Mandato).join(Partido).filter(
                    Mandato.deputado_id == spouse_deputy_query.id
                ).first()
                
                spouse_deputy = {
                    'id': spouse_deputy_query.id,
                    'nome': spouse_deputy_query.nome,
                    'nome_completo': spouse_deputy_query.nome_completo,
                    'partido_sigla': spouse_mandato.partido.sigla if spouse_mandato else 'Sem partido'
                }

        conflitos = {
            'record_id': conflicts_result[0],
            'legislatura': conflicts_result[1],
            'full_name': conflicts_result[2],
            'marital_status': conflicts_result[3],
            'spouse_name': spouse_name,
            'spouse_deputy': spouse_deputy,
            'matrimonial_regime': conflicts_result[5],
            'exclusivity': conflicts_result[6],
            'dgf_number': conflicts_result[7],
            'has_conflict_potential': conflicts_result[6] == 'N',  # Non-exclusive indicates potential conflicts
            'exclusivity_description': 'Exercício exclusivo' if conflicts_result[6] == 'S' else 'Exercício não exclusivo (possíveis conflitos)'
        }
        
        return jsonify(conflitos)
        
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@parlamento_bp.route('/legislaturas', methods=['GET'])
def get_legislaturas():
    """Retorna lista de todas as legislaturas disponíveis"""
    try:
        # Order legislaturas properly - numeric ones by number desc, then special ones
        legislaturas = db.session.query(Legislatura).order_by(
            desc(Legislatura.numero)
        ).all()
        
        result = []
        for leg in legislaturas:
            leg_dict = leg.to_dict()
            # Count mandates for this legislature
            mandatos_count = db.session.query(func.count(Mandato.id)).filter_by(legislatura_id=leg.id).scalar()
            leg_dict['mandatos_count'] = mandatos_count
            result.append(leg_dict)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parlamento_bp.route('/partidos', methods=['GET']) 
def get_partidos():
    """Retorna lista de partidos com contagem de deputados para a legislatura especificada"""
    try:
        legislatura = request.args.get('legislatura', '17', type=str)
        
        # Handle both string and integer numero values
        try:
            legislatura_num = int(legislatura)
            leg_filter = Legislatura.numero == legislatura_num
        except ValueError:
            leg_filter = Legislatura.numero == legislatura
        
        partidos = db.session.query(
            Partido,
            func.count(Mandato.id).label('num_deputados')
        ).outerjoin(Mandato, Partido.id == Mandato.partido_id).outerjoin(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(
            leg_filter
        ).group_by(Partido.id).order_by(desc('num_deputados')).all()
        
        total_deputados = db.session.query(func.count(Mandato.id)).join(
            Legislatura, Mandato.legislatura_id == Legislatura.id
        ).filter(leg_filter).scalar()
        
        result = []
        for partido, num_deputados in partidos:
            if num_deputados > 0:  # Only show parties with deputies in current legislature
                partido_dict = partido.to_dict()
                partido_dict['num_deputados'] = num_deputados  
                partido_dict['percentagem'] = round((num_deputados / total_deputados * 100), 1) if total_deputados > 0 else 0
                result.append(partido_dict)
        
        return jsonify({
            'partidos': result,
            'total_deputados': total_deputados
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500