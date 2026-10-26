from datetime import datetime, timezone


def utcnow():
    """UTC sem tzinfo, compatível com as colunas DateTime existentes (substitui o deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
