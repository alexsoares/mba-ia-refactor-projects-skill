"""Configuração da aplicação: único módulo que lê variáveis de ambiente (.env opcional)."""
import os
import secrets

from dotenv import load_dotenv


def _as_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    API_VERSION = "1.0"

    def __init__(self, env=None):
        if env is None:
            load_dotenv()
            env = os.environ

        self.SECRET_KEY_IS_EPHEMERAL = not env.get("SECRET_KEY")
        self.SECRET_KEY = env.get("SECRET_KEY") or secrets.token_hex(32)
        self.DEBUG = _as_bool(env.get("APP_DEBUG"))
        self.HOST = env.get("APP_HOST", "127.0.0.1")
        self.PORT = int(env.get("APP_PORT", "5000"))
        self.DATABASE_URL = env.get("DATABASE_URL", "sqlite:///tasks.db")
        self.CORS_ORIGINS = env.get("CORS_ORIGINS", "*")
        self.TOKEN_MAX_AGE_SECONDS = int(env.get("TOKEN_MAX_AGE_SECONDS", "3600"))

        # Notificações por e-mail só são enviadas se SMTP_HOST estiver configurado.
        self.SMTP_HOST = env.get("SMTP_HOST", "")
        self.SMTP_PORT = int(env.get("SMTP_PORT", "587"))
        self.SMTP_USER = env.get("SMTP_USER", "")
        self.SMTP_PASSWORD = env.get("SMTP_PASSWORD", "")
