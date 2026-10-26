"""Composition root: monta config, banco, models, controllers e rotas."""
import logging

from flask import Flask
from flask_cors import CORS

from src.config import Settings
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.sistema_controller import SistemaController
from src.controllers.usuario_controller import UsuarioController
from src.database import Database
from src.middlewares.error_handler import register_error_handlers
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.sistema_model import SistemaModel
from src.models.usuario_model import UsuarioModel
from src.services.notification_service import NotificationService
from src.views.pedido_routes import create_pedido_blueprint
from src.views.produto_routes import create_produto_blueprint
from src.views.relatorio_routes import create_relatorio_blueprint
from src.views.sistema_routes import create_sistema_blueprint
from src.views.usuario_routes import create_usuario_blueprint

logger = logging.getLogger(__name__)


def create_app(settings=None):
    settings = settings or Settings()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app, origins=settings.CORS_ORIGINS)
    if settings.SECRET_KEY_IS_EPHEMERAL:
        logger.warning("SECRET_KEY não definida; usando chave aleatória (sessões não sobrevivem a reinícios).")

    database = Database(settings.DATABASE_PATH)
    database.init_app(app)
    database.initialize(admin_password=settings.SEED_ADMIN_PASSWORD)

    produto_model = ProdutoModel(database.connection)
    usuario_model = UsuarioModel(database.connection)
    pedido_model = PedidoModel(database.connection)
    sistema_model = SistemaModel(database.connection, database.readonly_connection)

    app.register_blueprint(create_produto_blueprint(ProdutoController(produto_model)))
    app.register_blueprint(create_usuario_blueprint(UsuarioController(usuario_model)))
    app.register_blueprint(create_pedido_blueprint(
        PedidoController(pedido_model, produto_model, NotificationService())))
    app.register_blueprint(create_relatorio_blueprint(RelatorioController(pedido_model)))
    app.register_blueprint(create_sistema_blueprint(SistemaController(sistema_model, settings), settings))

    register_error_handlers(app)
    return app
