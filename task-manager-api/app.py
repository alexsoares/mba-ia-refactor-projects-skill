"""Entry point: python app.py"""
import logging

from src.app import create_app
from src.config import Settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

settings = Settings()
app = create_app(settings)

if __name__ == '__main__':
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
