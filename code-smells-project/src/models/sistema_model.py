"""Operações de sistema: contagens para o health check e rotinas administrativas."""

TABELAS = ("itens_pedido", "pedidos", "produtos", "usuarios")


class SistemaModel:
    def __init__(self, get_connection, get_readonly_connection):
        self._conn = get_connection
        self._readonly_conn = get_readonly_connection

    def contagens(self):
        row = self._conn().execute(
            """
            SELECT (SELECT COUNT(*) FROM produtos) AS produtos,
                   (SELECT COUNT(*) FROM usuarios) AS usuarios,
                   (SELECT COUNT(*) FROM pedidos)  AS pedidos
            """
        ).fetchone()
        return dict(row)

    def resetar(self):
        conn = self._conn()
        with conn:
            for tabela in TABELAS:
                conn.execute(f"DELETE FROM {tabela}")

    def consultar(self, sql):
        """Executa uma consulta em conexão somente leitura (o SQLite rejeita qualquer escrita)."""
        conn = self._readonly_conn()
        try:
            return [dict(row) for row in conn.execute(sql).fetchall()]
        finally:
            conn.close()
