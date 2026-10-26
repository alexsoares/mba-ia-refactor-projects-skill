from src.constants import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PEDIDO_VALIDOS
from src.controllers.validators import validar_pedido
from src.errors import NotFoundError, ValidationError
from src.models.pedido_model import EstoqueInsuficienteError


class PedidoController:
    def __init__(self, pedido_model, produto_model, notification_service):
        self.pedidos = pedido_model
        self.produtos = produto_model
        self.notificacoes = notification_service

    def criar(self, dados):
        usuario_id, itens = validar_pedido(dados)
        produtos = self.produtos.buscar_por_ids(item["produto_id"] for item in itens)

        total = 0
        itens_pedido = []
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise ValidationError(f"Produto {item['produto_id']} não encontrado", payload={"sucesso": False})
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}", payload={"sucesso": False})
            total = total + produto["preco"] * item["quantidade"]
            itens_pedido.append({**item, "preco_unitario": produto["preco"]})

        try:
            pedido_id = self.pedidos.criar(usuario_id, itens_pedido, total)
        except EstoqueInsuficienteError as err:
            nome = produtos[err.produto_id]["nome"]
            raise ValidationError(f"Estoque insuficiente para {nome}", payload={"sucesso": False})

        self.notificacoes.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar_todos(self):
        return self.pedidos.listar()

    def listar_por_usuario(self, usuario_id):
        return self.pedidos.listar(usuario_id=usuario_id)

    def atualizar_status(self, pedido_id, dados):
        novo_status = (dados or {}).get("status", "")
        if novo_status not in STATUS_PEDIDO_VALIDOS:
            raise ValidationError("Status inválido")

        status_atual = self.pedidos.buscar_status(pedido_id)
        if status_atual is None:
            raise NotFoundError("Pedido não encontrado")

        cancelando = novo_status == STATUS_CANCELADO and status_atual != STATUS_CANCELADO
        self.pedidos.atualizar_status(pedido_id, novo_status, devolver_estoque=cancelando)

        if novo_status == STATUS_APROVADO:
            self.notificacoes.pedido_aprovado(pedido_id)
        elif cancelando:
            self.notificacoes.pedido_cancelado(pedido_id)
