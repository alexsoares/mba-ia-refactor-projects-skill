from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class TokenService:
    """Tokens de autenticação assinados com a SECRET_KEY (itsdangerous, dependência do Flask)."""

    def __init__(self, secret_key, max_age_seconds):
        self.serializer = URLSafeTimedSerializer(secret_key, salt='auth-token')
        self.max_age_seconds = max_age_seconds

    def issue(self, user_id):
        return self.serializer.dumps({'user_id': user_id})

    def verify(self, token):
        """Retorna o user_id do token, ou None se inválido/expirado."""
        try:
            return self.serializer.loads(token, max_age=self.max_age_seconds)['user_id']
        except (BadSignature, SignatureExpired):
            return None
