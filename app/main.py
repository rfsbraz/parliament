import os
import sys
import logging
import traceback

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.settings import FLASK_CONFIG
from app.models.parlamento import db
from app.routes.parlamento import parlamento_bp
from app.routes.navegacao_relacional import navegacao_bp
from app.routes.agenda import agenda_bp
from app.routes.health import health_bp

# Configure logging
log_dir = os.path.join(parent_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'flask_server.log')),
        logging.StreamHandler()
    ]
)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static', 'dist'))
app.config.update(FLASK_CONFIG)

# Ativar CORS para permitir requests do frontend
CORS(app)

app.register_blueprint(parlamento_bp, url_prefix='/api')
app.register_blueprint(navegacao_bp, url_prefix='/api')
app.register_blueprint(agenda_bp, url_prefix='/api')
app.register_blueprint(health_bp, url_prefix='/api')

# Initialize database
db.init_app(app)

# Monkey patch to capture ALL exceptions during development
if __name__ == '__main__':
    original_dispatch = app.dispatch_request
    
    def patched_dispatch():
        try:
            return original_dispatch()
        except Exception as e:
            error_msg = f'Caught Exception in dispatch: {str(e)}'
            traceback_msg = f'Traceback: {traceback.format_exc()}'
            
            # Print to console directly
            print(f"\n{'='*50}")
            print(error_msg)
            print(traceback_msg)
            print('='*50)
            
            # Re-raise to let normal Flask error handling continue
            raise
    
    app.dispatch_request = patched_dispatch

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    error_msg = f'Server Error: {error}'
    traceback_msg = f'Traceback: {traceback.format_exc()}'
    
    # Print to console directly
    print(f"\n{'='*50}")
    print(error_msg)
    print(traceback_msg)
    print('='*50)
    
    # Also log via app logger
    app.logger.error(error_msg)
    app.logger.error(traceback_msg)
    
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    error_msg = f'Unhandled Exception: {e}'
    traceback_msg = f'Traceback: {traceback.format_exc()}'
    
    # Print to console directly
    print(f"\n{'='*50}")
    print(error_msg)
    print(traceback_msg)
    print('='*50)
    
    # Also log via app logger
    app.logger.error(error_msg)
    app.logger.error(traceback_msg)
    
    return jsonify({'error': 'Unhandled exception', 'message': str(e)}), 500

# Não criar tabelas pois já existem na base de dados importada
# with app.app_context():
#     db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    # Enable detailed error pages and debugging
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['DEBUG'] = True
    
    # Set Flask's logger to DEBUG level
    app.logger.setLevel(logging.DEBUG)
    
    print("Starting Flask server with detailed error logging...")
    app.run(host='0.0.0.0', port=5000, debug=True)
