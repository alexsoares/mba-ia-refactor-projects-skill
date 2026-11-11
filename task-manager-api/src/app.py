"""Composition root: monta config, ORM, serviços, controllers e rotas."""
import logging

from flask import Flask
from flask_cors import CORS

from src.config import Settings
from src.controllers.category_controller import CategoryController
from src.controllers.report_controller import ReportController
from src.controllers.task_controller import TaskController
from src.controllers.user_controller import UserController
from src.extensions import db
from src.middlewares.error_handler import register_error_handlers
from src.services.notification_service import NotificationService
from src.services.token_service import TokenService
from src.views.category_routes import create_category_blueprint
from src.views.report_routes import create_report_blueprint
from src.views.system_routes import create_system_blueprint
from src.views.task_routes import create_task_blueprint
from src.views.user_routes import create_user_blueprint

logger = logging.getLogger(__name__)


def create_app(settings=None):
    settings = settings or Settings()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['DEBUG'] = settings.DEBUG
    if settings.SECRET_KEY_IS_EPHEMERAL:
        logger.warning("SECRET_KEY não definida; usando chave aleatória (tokens não sobrevivem a reinícios).")

    CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)

    session = db.session
    notifications = NotificationService.from_settings(settings)
    tokens = TokenService(settings.SECRET_KEY, settings.TOKEN_MAX_AGE_SECONDS)

    app.register_blueprint(create_task_blueprint(TaskController(session, notifications)))
    app.register_blueprint(create_user_blueprint(UserController(session, tokens)))
    app.register_blueprint(create_report_blueprint(ReportController(session)))
    app.register_blueprint(create_category_blueprint(CategoryController(session)))
    app.register_blueprint(create_system_blueprint(settings))
    register_error_handlers(app, session)

    with app.app_context():
        db.create_all()

    return app
