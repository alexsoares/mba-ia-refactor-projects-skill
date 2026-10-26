"""Entry point: python app.py"""
import logging

from src.app import create_app
from src.config import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

settings = Settings()
app = create_app(settings)

if __name__ == "__main__":
    logging.getLogger(__name__).info("Servidor iniciado em http://%s:%s", settings.HOST, settings.PORT)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
