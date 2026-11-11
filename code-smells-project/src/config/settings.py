"""Configuração da aplicação: único módulo que lê variáveis de ambiente."""
import os
import secrets


def _as_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    APP_VERSION = "1.0.0"

    def __init__(self, env=None):
        env = os.environ if env is None else env

        self.SECRET_KEY_IS_EPHEMERAL = not env.get("SECRET_KEY")
        self.SECRET_KEY = env.get("SECRET_KEY") or secrets.token_hex(32)
        self.DEBUG = _as_bool(env.get("APP_DEBUG"))
        self.HOST = env.get("APP_HOST", "127.0.0.1")
        self.PORT = int(env.get("APP_PORT", "5000"))
        self.APP_ENV = env.get("APP_ENV", "development")
        self.DATABASE_PATH = env.get("DATABASE_PATH", "loja.db")
        self.CORS_ORIGINS = env.get("CORS_ORIGINS", "*")
        # Vazio = rotas /admin/* desabilitadas.
        self.ADMIN_TOKEN = env.get("ADMIN_TOKEN", "")
        # Vazio = senha aleatória (o admin de exemplo não consegue logar).
        self.SEED_ADMIN_PASSWORD = env.get("SEED_ADMIN_PASSWORD", "")
