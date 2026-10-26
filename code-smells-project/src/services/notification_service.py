"""Notificações de pedidos. Hoje apenas registra no log; um canal real (e-mail, SMS) entra aqui."""
import logging


class NotificationService:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def pedido_criado(self, pedido_id, usuario_id):
        self.logger.info("Notificação: pedido %s criado para usuário %s", pedido_id, usuario_id)

    def pedido_aprovado(self, pedido_id):
        self.logger.info("Notificação: pedido %s aprovado, preparar envio", pedido_id)

    def pedido_cancelado(self, pedido_id):
        self.logger.info("Notificação: pedido %s cancelado, estoque devolvido", pedido_id)
