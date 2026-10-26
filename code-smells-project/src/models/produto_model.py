"""Acesso a dados de produtos."""

PRODUTO_FIELDS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def produto_to_dict(row):
    return {field: row[field] for field in PRODUTO_FIELDS}


class ProdutoModel:
    def __init__(self, get_connection):
        self._conn = get_connection

    def listar(self):
        rows = self._conn().execute("SELECT * FROM produtos").fetchall()
        return [produto_to_dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._conn().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return produto_to_dict(row) if row else None

    def buscar_por_ids(self, produto_ids):
        """Retorna {id: produto} para os ids informados, em uma única query."""
        ids = list(set(produto_ids))
        if not ids:
            return {}
        placeholders = ", ".join("?" for _ in ids)
        rows = self._conn().execute(f"SELECT * FROM produtos WHERE id IN ({placeholders})", ids).fetchall()
        return {row["id"]: produto_to_dict(row) for row in rows}

    def buscar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        clauses, params = [], []
        if termo:
            clauses.append("(nome LIKE ? OR descricao LIKE ?)")
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            clauses.append("categoria = ?")
            params.append(categoria)
        if preco_min is not None:
            clauses.append("preco >= ?")
            params.append(preco_min)
        if preco_max is not None:
            clauses.append("preco <= ?")
            params.append(preco_max)

        where = " AND ".join(clauses) or "1=1"
        rows = self._conn().execute(f"SELECT * FROM produtos WHERE {where}", params).fetchall()
        return [produto_to_dict(row) for row in rows]

    def criar(self, produto):
        conn = self._conn()
        with conn:
            cursor = conn.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (produto["nome"], produto["descricao"], produto["preco"], produto["estoque"], produto["categoria"]),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, produto):
        conn = self._conn()
        with conn:
            conn.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (produto["nome"], produto["descricao"], produto["preco"], produto["estoque"],
                 produto["categoria"], produto_id),
            )

    def deletar(self, produto_id):
        conn = self._conn()
        with conn:
            conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
