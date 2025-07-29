"""
Rotas para Agenda Parlamentar - Parlamento Português
Implementa funcionalidades de agenda diária, ordens de trabalho e eventos
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, date, timedelta
import sqlite3
import os
import html
import re

agenda_bp = Blueprint('agenda', __name__)

def get_db_connection():
    """Obtém conexão com a base de dados."""
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'parlamento.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def format_time_display(time_str):
    """Format time string for display without seconds"""
    if not time_str:
        return None
    
    # Remove seconds if present (HH:MM:SS -> HH:MM)
    if len(time_str) >= 5:
        return time_str[:5]  # Take first 5 characters (HH:MM)
    
    return time_str

def clean_html_content(content):
    """Clean HTML entities and tags from content, converting br tags to line breaks"""
    if not content:
        return content
    
    # Decode HTML entities first
    decoded = html.unescape(content)
    
    # Convert <br /> and <br> tags to line breaks
    with_breaks = re.sub(r'<br\s*/?>', '\n', decoded, flags=re.IGNORECASE)
    
    # Remove remaining HTML tags
    clean_text = re.sub(r'<[^>]+>', '', with_breaks)
    
    # Clean up extra whitespace but preserve line breaks
    clean_text = re.sub(r'[ \t]+', ' ', clean_text)  # Only clean horizontal whitespace
    clean_text = clean_text.strip()
    
    return clean_text

@agenda_bp.route('/agenda/hoje', methods=['GET'])
def get_agenda_hoje():
    """Obtém agenda parlamentar para hoje usando dados reais."""
    try:
        hoje = date.today()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar eventos reais da agenda para hoje
        cursor.execute('''
            SELECT id, id_externo, titulo, subtitulo, data_evento, hora_inicio, hora_fim,
                   descricao, local_evento, grupo_parlamentar, estado
            FROM agenda_parlamentar 
            WHERE date(data_evento) = ?
            ORDER BY hora_inicio
        ''', (hoje.isoformat(),))
        
        rows = cursor.fetchall()
        eventos = []
        
        for row in rows:
            # Determine event type based on title content
            titulo_lower = row['titulo'].lower()
            if 'plenár' in titulo_lower or 'sessão' in titulo_lower:
                tipo = 'plenario'
            elif 'comissão' in titulo_lower or 'comité' in titulo_lower:
                tipo = 'comissao'
            elif 'conferência' in titulo_lower or 'reunião' in titulo_lower:
                tipo = 'reuniao'
            else:
                tipo = 'evento'
            
            eventos.append({
                'id': row['id'],
                'id_externo': row['id_externo'],
                'titulo': row['titulo'],
                'subtitulo': clean_html_content(row['subtitulo']),
                'hora_inicio': format_time_display(str(row['hora_inicio']) if row['hora_inicio'] else None),
                'hora_fim': format_time_display(str(row['hora_fim']) if row['hora_fim'] else None),
                'tipo': tipo,
                'descricao': clean_html_content(row['descricao']),
                'local': row['local_evento'],
                'grupo_parlamentar': row['grupo_parlamentar'],
                'estado': row['estado'] or 'agendado'
            })
        
        conn.close()
        
        return jsonify({
            'data': hoje.isoformat(),
            'eventos': eventos,
            'total': len(eventos),
            'resumo': {
                'sessoes_plenarias': len([e for e in eventos if e['tipo'] == 'plenario']),
                'reunioes_comissao': len([e for e in eventos if e['tipo'] == 'comissao']),
                'outros_eventos': len([e for e in eventos if e['tipo'] not in ['plenario', 'comissao']])
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/agenda/semana', methods=['GET'])
def get_agenda_semana():
    """Obtém agenda parlamentar para a semana atual usando dados reais."""
    try:
        hoje = date.today()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar todos os eventos da semana
        cursor.execute('''
            SELECT id, titulo, subtitulo, data_evento, hora_inicio, hora_fim,
                   local_evento, grupo_parlamentar, estado
            FROM agenda_parlamentar 
            WHERE date(data_evento) BETWEEN ? AND ?
            ORDER BY data_evento, hora_inicio
        ''', (inicio_semana.isoformat(), fim_semana.isoformat()))
        
        eventos_semana = cursor.fetchall()
        conn.close()
        
        # Organizar eventos por dia
        agenda_semana = []
        for i in range(7):
            data_dia = inicio_semana + timedelta(days=i)
            
            # Filtrar eventos para este dia
            eventos_dia = []
            for evento in eventos_semana:
                if evento['data_evento'] == data_dia.isoformat():
                    # Determine event type
                    titulo_lower = evento['titulo'].lower()
                    if 'plenár' in titulo_lower or 'sessão' in titulo_lower:
                        tipo = 'plenario'
                    elif 'comissão' in titulo_lower:
                        tipo = 'comissao'
                    else:
                        tipo = 'evento'
                    
                    eventos_dia.append({
                        'id': evento['id'],
                        'titulo': evento['titulo'],
                        'subtitulo': clean_html_content(evento['subtitulo']),
                        'hora_inicio': format_time_display(str(evento['hora_inicio']) if evento['hora_inicio'] else None),
                        'hora_fim': format_time_display(str(evento['hora_fim']) if evento['hora_fim'] else None),
                        'tipo': tipo,
                        'local': evento['local_evento'],
                        'grupo_parlamentar': evento['grupo_parlamentar'],
                        'estado': evento['estado'] or 'agendado'
                    })
            
            agenda_semana.append({
                'data': data_dia.isoformat(),
                'dia_semana': data_dia.strftime('%A'),
                'eventos': eventos_dia,
                'total_eventos': len(eventos_dia)
            })
        
        return jsonify({
            'periodo': {
                'inicio': inicio_semana.isoformat(),
                'fim': fim_semana.isoformat()
            },
            'agenda': agenda_semana,
            'resumo': {
                'total_eventos': sum(dia['total_eventos'] for dia in agenda_semana),
                'dias_com_atividade': len([dia for dia in agenda_semana if dia['total_eventos'] > 0])
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/agenda/mes', methods=['GET'])
def get_agenda_mes():
    """Obtém agenda parlamentar para o mês atual."""
    try:
        hoje = date.today()
        ano = request.args.get('ano', hoje.year, type=int)
        mes = request.args.get('mes', hoje.month, type=int)
        
        # Primeiro dia do mês
        primeiro_dia = date(ano, mes, 1)
        
        # Último dia do mês
        if mes == 12:
            ultimo_dia = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(ano, mes + 1, 1) - timedelta(days=1)
        
        # Simular eventos do mês
        eventos_mes = []
        data_atual = primeiro_dia
        
        while data_atual <= ultimo_dia:
            if data_atual.weekday() < 5:  # Segunda a sexta
                num_eventos = 0
                
                # Simular padrão de eventos
                if data_atual.weekday() in [1, 3]:  # Terça e quinta - sessões plenárias
                    num_eventos += 1
                
                if data_atual.day % 3 == 0:  # A cada 3 dias - comissões
                    num_eventos += 1
                
                if num_eventos > 0:
                    eventos_mes.append({
                        'data': data_atual.isoformat(),
                        'dia': data_atual.day,
                        'dia_semana': data_atual.strftime('%A'),
                        'num_eventos': num_eventos,
                        'tem_plenario': data_atual.weekday() in [1, 3],
                        'tem_comissoes': data_atual.day % 3 == 0
                    })
            
            data_atual += timedelta(days=1)
        
        return jsonify({
            'periodo': {
                'ano': ano,
                'mes': mes,
                'nome_mes': primeiro_dia.strftime('%B'),
                'primeiro_dia': primeiro_dia.isoformat(),
                'ultimo_dia': ultimo_dia.isoformat()
            },
            'eventos': eventos_mes,
            'resumo': {
                'total_dias_atividade': len(eventos_mes),
                'total_eventos': sum(e['num_eventos'] for e in eventos_mes),
                'sessoes_plenarias': len([e for e in eventos_mes if e['tem_plenario']]),
                'reunioes_comissoes': len([e for e in eventos_mes if e['tem_comissoes']])
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/agenda/<data_evento>', methods=['GET'])
def get_agenda_data(data_evento):
    """Obtém agenda parlamentar para uma data específica."""
    try:
        # Validar formato da data
        try:
            data_obj = datetime.strptime(data_evento, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        # Simular eventos para a data específica
        eventos = []
        
        # Se for dia útil, simular alguns eventos
        if data_obj.weekday() < 5:
            if data_obj.weekday() in [1, 3]:  # Terça e quinta
                eventos.append({
                    'id': f'plen_{data_evento}',
                    'titulo': 'Sessão Plenária',
                    'hora_inicio': '14:30',
                    'hora_fim': '18:00',
                    'tipo': 'plenario',
                    'descricao': 'Ordem do dia com debate e votação de iniciativas',
                    'local': 'Hemiciclo',
                    'estado': 'agendado',
                    'ordem_trabalhos': [
                        'Projeto de Lei n.º 123/XVII - Alteração ao Código Civil',
                        'Proposta de Lei n.º 45/XVII - Orçamento do Estado',
                        'Requerimento n.º 67/XVII - Audição do Ministro da Justiça'
                    ]
                })
            
            if data_obj.day % 2 == 0:  # Dias pares
                eventos.append({
                    'id': f'com_{data_evento}',
                    'titulo': 'Comissão de Assuntos Constitucionais',
                    'hora_inicio': '10:00',
                    'hora_fim': '12:00',
                    'tipo': 'comissao',
                    'descricao': 'Análise de propostas legislativas',
                    'local': 'Sala 1.1',
                    'estado': 'agendado'
                })
        
        return jsonify({
            'data': data_evento,
            'dia_semana': data_obj.strftime('%A'),
            'eventos': eventos,
            'total': len(eventos),
            'resumo': {
                'tem_atividade': len(eventos) > 0,
                'tipos_eventos': list(set(e['tipo'] for e in eventos))
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/votacoes/recentes', methods=['GET'])
def get_votacoes_recentes():
    """Obtém votações recentes usando dados reais."""
    try:
        limite = request.args.get('limite', 10, type=int)
        legislatura = request.args.get('legislatura', '17', type=str)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar votações reais mais recentes
        cursor.execute('''
            SELECT v.id, v.data_votacao, v.hora_votacao, v.objeto_votacao, v.tipo_votacao,
                   v.resultado, v.votos_favor, v.votos_contra, v.abstencoes, v.ausencias,
                   l.numero as legislatura_numero
            FROM votacoes v
            JOIN legislaturas l ON v.legislatura_id = l.id
            WHERE l.numero = ?
            ORDER BY v.data_votacao DESC, v.hora_votacao DESC
            LIMIT ?
        ''', (legislatura, limite))
        
        rows = cursor.fetchall()
        votacoes = []
        
        for row in rows:
            votacoes.append({
                'id': row['id'],
                'data': row['data_votacao'],
                'hora': str(row['hora_votacao']) if row['hora_votacao'] else None,
                'titulo': row['objeto_votacao'] or f'Votação #{row["id"]}',
                'descricao': row['objeto_votacao'],
                'resultado': row['resultado'] or 'desconhecido',
                'votos_favor': row['votos_favor'] or 0,
                'votos_contra': row['votos_contra'] or 0,
                'abstencoes': row['abstencoes'] or 0,
                'ausencias': row['ausencias'] or 0,
                'tipo_votacao': row['tipo_votacao'] or 'nominal',
                'legislatura': row['legislatura_numero']
            })
        
        conn.close()
        
        # If no real data, provide a message
        if not votacoes:
            return jsonify({
                'votacoes': [],
                'total': 0,
                'message': f'Nenhuma votação encontrada para a {legislatura}ª Legislatura',
                'resumo': {
                    'aprovadas': 0,
                    'rejeitadas': 0,
                    'periodo': f'Legislatura {legislatura}'
                }
            })
        
        return jsonify({
            'votacoes': votacoes,
            'total': len(votacoes),
            'resumo': {
                'aprovadas': len([v for v in votacoes if v['resultado'] and 'aprovad' in v['resultado'].lower()]),
                'rejeitadas': len([v for v in votacoes if v['resultado'] and 'rejeitad' in v['resultado'].lower()]),
                'periodo': f'Legislatura {legislatura} - Últimas {len(votacoes)} votações'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/ordem-trabalhos/<data_evento>', methods=['GET'])
def get_ordem_trabalhos(data_evento):
    """Obtém ordem de trabalhos para uma data específica."""
    try:
        # Validar formato da data
        try:
            data_obj = datetime.strptime(data_evento, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        # Simular ordem de trabalhos
        ordem_trabalhos = []
        
        if data_obj.weekday() in [1, 3]:  # Terça e quinta - sessões plenárias
            ordem_trabalhos = [
                {
                    'numero': 1,
                    'tipo': 'projeto_lei',
                    'titulo': 'Projeto de Lei n.º 123/XVII',
                    'descricao': 'Alteração ao Código Civil - regime de bens',
                    'autor': 'Grupo Parlamentar do PSD',
                    'fase': 'votacao_final_global',
                    'tempo_estimado': '30 minutos',
                    'urgente': False
                },
                {
                    'numero': 2,
                    'tipo': 'proposta_lei',
                    'titulo': 'Proposta de Lei n.º 45/XVII',
                    'descricao': 'Orçamento do Estado para 2025',
                    'autor': 'Governo',
                    'fase': 'discussao_generalidade',
                    'tempo_estimado': '120 minutos',
                    'urgente': True
                },
                {
                    'numero': 3,
                    'tipo': 'requerimento',
                    'titulo': 'Requerimento n.º 67/XVII',
                    'descricao': 'Audição do Ministro da Justiça',
                    'autor': 'Grupo Parlamentar do PS',
                    'fase': 'votacao',
                    'tempo_estimado': '15 minutos',
                    'urgente': False
                },
                {
                    'numero': 4,
                    'tipo': 'interpelacao',
                    'titulo': 'Interpelação ao Governo n.º 12/XVII',
                    'descricao': 'Política de habitação',
                    'autor': 'Grupo Parlamentar do Chega',
                    'fase': 'discussao',
                    'tempo_estimado': '45 minutos',
                    'urgente': False
                }
            ]
        
        return jsonify({
            'data': data_evento,
            'ordem_trabalhos': ordem_trabalhos,
            'total_itens': len(ordem_trabalhos),
            'tempo_total_estimado': sum(
                int(item['tempo_estimado'].split()[0]) 
                for item in ordem_trabalhos
            ),
            'itens_urgentes': len([item for item in ordem_trabalhos if item['urgente']]),
            'resumo_tipos': {
                tipo: len([item for item in ordem_trabalhos if item['tipo'] == tipo])
                for tipo in set(item['tipo'] for item in ordem_trabalhos)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agenda_bp.route('/estatisticas/atividade', methods=['GET'])
def get_estatisticas_atividade():
    """Obtém estatísticas reais de atividade parlamentar."""
    try:
        legislatura = request.args.get('legislatura', '17', type=str)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get legislatura_id
        cursor.execute('SELECT id FROM legislaturas WHERE numero = ?', (legislatura,))
        leg_result = cursor.fetchone()
        if not leg_result:
            return jsonify({'error': f'Legislatura {legislatura} não encontrada'}), 404
        
        leg_id = leg_result['id']
        
        # Contar sessões plenárias (eventos que contêm "plenár" ou "sessão")
        cursor.execute("""
            SELECT COUNT(*) FROM agenda_parlamentar 
            WHERE legislatura_id = ? AND (
                LOWER(titulo) LIKE '%plenár%' OR 
                LOWER(titulo) LIKE '%sessão%'
            )
        """, (leg_id,))
        sessoes_plenarias = cursor.fetchone()[0]
        
        # Estatísticas de votações
        cursor.execute("SELECT COUNT(*) FROM votacoes WHERE legislatura_id = ?", (leg_id,))
        total_votacoes = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM votacoes 
            WHERE legislatura_id = ? AND LOWER(resultado) LIKE '%aprovad%'
        """, (leg_id,))
        votacoes_aprovadas = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM votacoes 
            WHERE legislatura_id = ? AND LOWER(resultado) LIKE '%rejeitad%'
        """, (leg_id,))
        votacoes_rejeitadas = cursor.fetchone()[0]
        
        # Estatísticas de iniciativas
        cursor.execute("SELECT COUNT(*) FROM iniciativas_legislativas WHERE legislatura_id = ?", (leg_id,))
        total_iniciativas = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM iniciativas_legislativas 
            WHERE legislatura_id = ? AND LOWER(estado) LIKE '%discussão%'
        """, (leg_id,))
        iniciativas_discussao = cursor.fetchone()[0]
        
        # Estatísticas de intervenções
        cursor.execute("SELECT COUNT(*) FROM intervencoes WHERE legislatura_id = ?", (leg_id,))
        total_intervencoes = cursor.fetchone()[0]
        
        # Reuniões de comissão (aproximação baseada em títulos)
        cursor.execute("""
            SELECT COUNT(*) FROM agenda_parlamentar 
            WHERE legislatura_id = ? AND LOWER(titulo) LIKE '%comissão%'
        """, (leg_id,))
        reunioes_comissao = cursor.fetchone()[0]
        
        # Última atividade na agenda
        cursor.execute("""
            SELECT MAX(data_evento) FROM agenda_parlamentar 
            WHERE legislatura_id = ? AND data_evento <= ?
        """, (leg_id, date.today().isoformat()))
        ultima_atividade = cursor.fetchone()[0]
        
        conn.close()
        
        # Calcular taxa de aprovação
        taxa_aprovacao = 0
        if total_votacoes > 0:
            taxa_aprovacao = round((votacoes_aprovadas / total_votacoes) * 100, 1)
        
        estatisticas = {
            'sessoes_plenarias': {
                'total_ano': sessoes_plenarias,
                'media_mensal': round(sessoes_plenarias / 12, 1) if sessoes_plenarias > 0 else 0,
                'ultima_sessao': ultima_atividade,
                'proxima_sessao': None  # Would need future data
            },
            'votacoes': {
                'total_ano': total_votacoes,
                'aprovadas': votacoes_aprovadas,
                'rejeitadas': votacoes_rejeitadas,
                'taxa_aprovacao': taxa_aprovacao
            },
            'iniciativas': {
                'apresentadas': total_iniciativas,
                'em_discussao': iniciativas_discussao,
                'aprovadas': 0,  # Would need more detailed state data
                'rejeitadas': 0   # Would need more detailed state data
            },
            'intervencoes': {
                'total': total_intervencoes,
                'media_por_deputado': round(total_intervencoes / 230, 1) if total_intervencoes > 0 else 0  # Approximation
            },
            'comissoes': {
                'reunioes_mes': reunioes_comissao,
                'audiencias_mes': 0,  # Would need specific data
                'pareceres_emitidos': 0  # Would need specific data
            }
        }
        
        return jsonify({
            'periodo': f'Legislatura {legislatura}',
            'ultima_atualizacao': datetime.now().isoformat(),
            'estatisticas': estatisticas,
            'dados_reais': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

