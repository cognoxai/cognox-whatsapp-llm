import os
import sys

# DON\'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db as user_db # Renomear para evitar conflito
from src.models.conversation import db as conversation_db # Renomear

# Importar os modelos e blueprints APÓS a inicialização do db
from src.models.conversation import Conversation, Message, SchedulingInfo
from src.routes.user import user_bp
from src.routes.whatsapp import whatsapp_bp
from src.routes.scheduling import scheduling_bp

# Criar uma única instância de SQLAlchemy para ser usada por todos os modelos
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

    # Habilita CORS para todas as rotas
    CORS(app)

    # Configuração do banco de dados
    db_path = os.path.join('/tmp', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar o db com o app
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Registra blueprints APÓS a inicialização do db
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(whatsapp_bp, url_prefix='/api/whatsapp')
    app.register_blueprint(scheduling_bp, url_prefix='/api/scheduling')

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

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
