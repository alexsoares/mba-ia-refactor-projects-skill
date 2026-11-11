import logging

from src.controllers.validators import validar_filtro_preco, validar_produto
from src.errors import NotFoundError

logger = logging.getLogger(__name__)


class ProdutoController:
    def __init__(self, produto_model):
        self.produtos = produto_model

    def listar(self):
        produtos = self.produtos.listar()
        logger.info("Listando %d produtos", len(produtos))
        return produtos

    def obter(self, produto_id):
        produto = self.produtos.buscar_por_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado", payload={"sucesso": False})
        return produto

    def buscar(self, termo, categoria, preco_min, preco_max):
        return self.produtos.buscar(
            termo=termo,
            categoria=categoria,
            preco_min=validar_filtro_preco(preco_min),
            preco_max=validar_filtro_preco(preco_max),
        )

    def criar(self, dados):
        produto = validar_produto(dados)
        produto_id = self.produtos.criar(produto)
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, dados):
        if not self.produtos.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        self.produtos.atualizar(produto_id, validar_produto(dados))

    def deletar(self, produto_id):
        if not self.produtos.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        self.produtos.deletar(produto_id)
        logger.info("Produto %s deletado", produto_id)
