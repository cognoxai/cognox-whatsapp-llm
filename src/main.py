import os
from flask import Flask
from flask_cors import CORS
from src.database import db
from src.routes.whatsapp import whatsapp_bp

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Configuração do Banco de Dados
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL").replace("://", "ql://", 1)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Inicializa o db com o app
    db.init_app(app)

    # Cria as tabelas do banco de dados dentro do contexto da aplicação
    with app.app_context():
        db.create_all()

    # Registra os Blueprints
    app.register_blueprint(whatsapp_bp, url_prefix="/api/whatsapp")

    return app

# Este bloco permite rodar localmente para testes, se necessário
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
