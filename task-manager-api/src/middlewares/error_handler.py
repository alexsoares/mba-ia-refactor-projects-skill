import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app, session):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        session.rollback()
        return jsonify({'error': err.message}), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        if isinstance(err, HTTPException):
            return err
        session.rollback()
        logger.exception("Erro inesperado")
        return jsonify({'error': 'Erro interno'}), 500
