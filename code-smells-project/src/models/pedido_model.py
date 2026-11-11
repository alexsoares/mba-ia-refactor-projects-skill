"""Acesso a dados de pedidos e itens de pedido."""
from src.constants import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE


class EstoqueInsuficienteError(Exception):
    def __init__(self, produto_id):
        super().__init__(f"Estoque insuficiente para o produto {produto_id}")
        self.produto_id = produto_id


class PedidoModel:
    def __init__(self, get_connection):
        self._conn = get_connection

    def criar(self, usuario_id, itens, total):
        """Cria pedido, itens e debita estoque em uma única transação.

        `itens` é uma lista de dicts com produto_id, quantidade e preco_unitario.
        O débito só acontece se ainda houver estoque (proteção contra concorrência).
        """
        conn = self._conn()
        with conn:
            pedido_id = conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            ).lastrowid
            for item in itens:
                debitado = conn.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                ).rowcount
                if not debitado:
                    raise EstoqueInsuficienteError(item["produto_id"])
                conn.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
                )
        return pedido_id

    def listar(self, usuario_id=None):
        """Pedidos com itens e nome do produto em uma única query (sem N+1)."""
        rows = self._conn().execute(
            """
            SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
                   i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
                   pr.nome AS produto_nome
              FROM pedidos p
              LEFT JOIN itens_pedido i ON i.pedido_id = p.id
              LEFT JOIN produtos pr ON pr.id = i.produto_id
             WHERE (? IS NULL OR p.usuario_id = ?)
             ORDER BY p.id, i.id
            """,
            (usuario_id, usuario_id),
        ).fetchall()

        pedidos = {}
        for row in rows:
            pedido = pedidos.setdefault(row["id"], {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            })
            if row["item_id"] is not None:
                pedido["itens"].append({
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] or "Desconhecido",
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                })
        return list(pedidos.values())

    def buscar_status(self, pedido_id):
        row = self._conn().execute("SELECT status FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        return row["status"] if row else None

    def atualizar_status(self, pedido_id, novo_status, devolver_estoque=False):
        conn = self._conn()
        with conn:
            conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
            if devolver_estoque:
                conn.execute(
                    """
                    UPDATE produtos
                       SET estoque = estoque + (SELECT COALESCE(SUM(i.quantidade), 0)
                                                  FROM itens_pedido i
                                                 WHERE i.pedido_id = ? AND i.produto_id = produtos.id)
                     WHERE id IN (SELECT produto_id FROM itens_pedido WHERE pedido_id = ?)
                    """,
                    (pedido_id, pedido_id),
                )

    def resumo_vendas(self):
        row = self._conn().execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
                   COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
                   COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
              FROM pedidos
            """,
            (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
        ).fetchone()
        return dict(row)
