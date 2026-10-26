from flask import Blueprint, jsonify, request

from src.middlewares.auth import require_admin_token


def create_sistema_blueprint(controller, settings):
    bp = Blueprint("sistema", __name__)
    admin_only = require_admin_token(settings)

    @bp.get("/")
    def index():
        return jsonify(controller.index())

    @bp.get("/health")
    def health_check():
        payload, status = controller.health()
        return jsonify(payload), status

    @bp.post("/admin/reset-db")
    @admin_only
    def reset_database():
        controller.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @bp.post("/admin/query")
    @admin_only
    def executar_query():
        return jsonify({"dados": controller.consultar(request.get_json(silent=True)), "sucesso": True}), 200

    return bp
