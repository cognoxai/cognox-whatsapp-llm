import os
from flask import Flask
from flask_cors import CORS
from src.database import db
from src.routes.whatsapp import whatsapp_bp
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_app():
    app = Flask(__name__)
    CORS(app)

    # A forma CORRETA e SIMPLES. Confiamos que o Render fornecerá a URL correta.
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("FATAL: DATABASE_URL não está configurada. Verifique se o banco de dados está linkado ao serviço no dashboard do Render.")
    
    # O SQLAlchemy moderno lida com "postgres://" vs "postgresql://". Removemos a lógica de replace.
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    
    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(whatsapp_bp, url_prefix="/api/whatsapp")
    logging.info("Aplicação criada e configurada com sucesso.")
    return app
