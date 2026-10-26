from flask import Blueprint, jsonify, request


def create_category_blueprint(controller):
    category_bp = Blueprint('categories', __name__)

    @category_bp.get('/categories')
    def get_categories():
        return jsonify(controller.list()), 200

    @category_bp.post('/categories')
    def create_category():
        return jsonify(controller.create(request.get_json(silent=True))), 201

    @category_bp.put('/categories/<int:cat_id>')
    def update_category(cat_id):
        return jsonify(controller.update(cat_id, request.get_json(silent=True))), 200

    @category_bp.delete('/categories/<int:cat_id>')
    def delete_category(cat_id):
        controller.delete(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200

    return category_bp
