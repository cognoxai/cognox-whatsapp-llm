from flask import Blueprint, request, jsonify
from src.database import db
from src.models.user import User

user_bp = Blueprint('user_bp', __name__)
# ... (o resto do arquivo permanece o mesmo)
@user_bp.route("/users", methods=["POST"])
def create_user():
    data = request.json
    if not data or not 'username' in data or not 'email' in data:
        return jsonify({"error": "Missing username or email"}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 409
        
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already exists"}), 409

    new_user = User(username=data['username'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify(new_user.to_dict()), 201

@user_bp.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])
