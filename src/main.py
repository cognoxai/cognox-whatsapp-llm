import os
import sys
from flask import Flask, send_from_directory
from flask_cors import CORS
from .database import db  # Importa a instância do banco de dados
from .routes.whatsapp import whatsapp_bp
from .routes.user import user_bp
from .routes.scheduling import scheduling_bp

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
    
    # Configuração do banco de dados
    # Usar /tmp para o banco de dados SQLite é uma boa prática em ambientes de contêiner
    db_path = os.path.join('/tmp', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa o banco de dados com a aplicação
    db.init_app(app)

    # Habilita CORS
    CORS(app)

    # Registra os blueprints (rotas)
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(whatsapp_bp, url_prefix='/api/whatsapp')
    app.register_blueprint(scheduling_bp, url_prefix='/api/scheduling')

    # Cria as tabelas do banco de dados dentro do contexto da aplicação
    with app.app_context():
        db.create_all()

    # Rota para servir a aplicação frontend (React, Vue, etc.)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return "index.html not found", 404

    return app

# Ponto de entrada da aplicação
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)

