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

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logging.critical("FATAL: A variável de ambiente DATABASE_URL não foi definida.")
        raise ValueError("DATABASE_URL não está configurada.")
    
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    
    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(whatsapp_bp, url_prefix="/api/whatsapp")
    logging.info("Aplicação criada e configurada com sucesso.")
    return app
