from flask import Blueprint, jsonify
import sqlite3
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for container orchestration"""
    try:
        # Check database connectivity
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'parlamento.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM deputados LIMIT 1")
            cursor.fetchone()
            conn.close()
            db_status = "healthy"
        else:
            db_status = "database_file_missing"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return jsonify({
        'status': 'healthy',
        'service': 'parliament-backend',
        'database': db_status,
        'version': '1.0.0'
    }), 200

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check for Kubernetes/ECS"""
    try:
        # Check if all required services are ready
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'parlamento.db')
        if not os.path.exists(db_path):
            return jsonify({
                'status': 'not_ready',
                'reason': 'database_not_available'
            }), 503
        
        # Test database query
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM deputados")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            return jsonify({
                'status': 'not_ready',
                'reason': 'database_empty'
            }), 503
        
        return jsonify({
            'status': 'ready',
            'deputies_count': count
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'reason': str(e)
        }), 503