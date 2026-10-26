from flask import Blueprint, jsonify, request


def create_user_blueprint(controller):
    user_bp = Blueprint('users', __name__)

    @user_bp.get('/users')
    def get_users():
        return jsonify(controller.list()), 200

    @user_bp.get('/users/<int:user_id>')
    def get_user(user_id):
        return jsonify(controller.get(user_id)), 200

    @user_bp.post('/users')
    def create_user():
        return jsonify(controller.create(request.get_json(silent=True))), 201

    @user_bp.put('/users/<int:user_id>')
    def update_user(user_id):
        return jsonify(controller.update(user_id, request.get_json(silent=True))), 200

    @user_bp.delete('/users/<int:user_id>')
    def delete_user(user_id):
        controller.delete(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200

    @user_bp.get('/users/<int:user_id>/tasks')
    def get_user_tasks(user_id):
        return jsonify(controller.tasks(user_id)), 200

    @user_bp.post('/login')
    def login():
        return jsonify(controller.login(request.get_json(silent=True))), 200

    return user_bp
