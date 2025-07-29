import os
import sys

from flask import Flask, send_from_directory
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

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static', 'dist'))
app.config.update(FLASK_CONFIG)

# Ativar CORS para permitir requests do frontend
CORS(app)

app.register_blueprint(parlamento_bp, url_prefix='/api')
app.register_blueprint(navegacao_bp, url_prefix='/api')
app.register_blueprint(agenda_bp, url_prefix='/api')

# Initialize database
db.init_app(app)

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
    # Enable detailed error pages
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.run(host='0.0.0.0', port=5000, debug=True)
