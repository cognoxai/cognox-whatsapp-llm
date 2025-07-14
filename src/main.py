import os
import sys
from flask import Flask, send_from_directory
from flask_cors import CORS
from src.database import db
from src.routes.whatsapp import whatsapp_bp
from src.routes.user import user_bp
from src.routes.scheduling import scheduling_bp

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
    
    db_path = os.path.join('/tmp', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    CORS(app)

    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(whatsapp_bp, url_prefix='/api/whatsapp')
    app.register_blueprint(scheduling_bp, url_prefix='/api/scheduling')

    with app.app_context():
        db.create_all()

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

if __name__ == '__main__':
    app = create_app()
    # O Render usa a variável de ambiente PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
