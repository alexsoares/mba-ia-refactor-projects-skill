from datetime import datetime

from flask import Blueprint


def create_system_blueprint(settings):
    system_bp = Blueprint('system', __name__)

    @system_bp.get('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.now())}

    @system_bp.get('/')
    def index():
        return {'message': 'Task Manager API', 'version': settings.API_VERSION}

    return system_bp
