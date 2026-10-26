import hmac
import logging

from werkzeug.security import check_password_hash, generate_password_hash

from src.constants import TIPO_USUARIO_PADRAO
from src.controllers.validators import validar_login, validar_novo_usuario
from src.errors import NotFoundError, UnauthorizedError

logger = logging.getLogger(__name__)

# Prefixos dos hashes gerados pelo werkzeug; qualquer outro valor é senha legada em texto puro.
_HASH_PREFIXES = ("scrypt:", "pbkdf2:")


class UsuarioController:
    def __init__(self, usuario_model):
        self.usuarios = usuario_model

    def listar(self):
        return self.usuarios.listar()

    def obter(self, usuario_id):
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados):
        nome, email, senha = validar_novo_usuario(dados)
        usuario_id = self.usuarios.criar(nome, email, generate_password_hash(senha), TIPO_USUARIO_PADRAO)
        logger.info("Usuário criado: id=%s", usuario_id)
        return usuario_id

    def login(self, dados):
        email, senha = validar_login(dados)
        usuario, senha_hash = self.usuarios.buscar_credenciais(email)
        if not usuario or not self._senha_confere(usuario["id"], senha_hash, senha):
            logger.info("Falha de login")
            raise UnauthorizedError("Email ou senha inválidos", payload={"sucesso": False})
        logger.info("Login bem-sucedido: usuário id=%s", usuario["id"])
        return {campo: usuario[campo] for campo in ("id", "nome", "email", "tipo")}

    def _senha_confere(self, usuario_id, senha_armazenada, senha):
        if not senha_armazenada:
            return False
        if senha_armazenada.startswith(_HASH_PREFIXES):
            return check_password_hash(senha_armazenada, senha)
        # Migração transparente de bancos antigos com senha em texto puro.
        if hmac.compare_digest(senha_armazenada.encode(), senha.encode()):
            self.usuarios.atualizar_senha(usuario_id, generate_password_hash(senha))
            return True
        return False
