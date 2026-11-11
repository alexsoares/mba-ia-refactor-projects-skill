import logging
import sqlite3

from src.errors import ValidationError

logger = logging.getLogger(__name__)

ENDPOINTS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


class SistemaController:
    def __init__(self, sistema_model, settings):
        self.sistema = sistema_model
        self.settings = settings

    def index(self):
        return {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": self.settings.APP_VERSION,
            "endpoints": ENDPOINTS,
        }

    def health(self):
        """Retorna (payload, status_http). Nunca expõe segredos ou caminhos internos."""
        try:
            contagens = self.sistema.contagens()
        except sqlite3.Error:
            logger.exception("Health check: banco indisponível")
            return {"status": "erro", "database": "disconnected"}, 500
        return {
            "status": "ok",
            "database": "connected",
            "counts": contagens,
            "versao": self.settings.APP_VERSION,
            "ambiente": self.settings.APP_ENV,
        }, 200

    def resetar_banco(self):
        self.sistema.resetar()
        logger.warning("Banco de dados resetado via /admin/reset-db")

    def consultar(self, dados):
        sql = ((dados or {}).get("sql") or "").strip().rstrip(";").strip()
        if not sql:
            raise ValidationError("Query não informada")
        if ";" in sql or not sql.upper().startswith("SELECT"):
            raise ValidationError("Apenas uma consulta SELECT é permitida")
        try:
            return self.sistema.consultar(sql)
        except sqlite3.Error:
            raise ValidationError("Consulta inválida")
