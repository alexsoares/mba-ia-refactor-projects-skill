"""Acesso a dados de usuários. A senha (hash) nunca sai deste módulo nos dicts públicos."""

USUARIO_PUBLIC_FIELDS = ("id", "nome", "email", "tipo", "criado_em")


def usuario_to_dict(row):
    return {field: row[field] for field in USUARIO_PUBLIC_FIELDS}


class UsuarioModel:
    def __init__(self, get_connection):
        self._conn = get_connection

    def listar(self):
        rows = self._conn().execute("SELECT * FROM usuarios").fetchall()
        return [usuario_to_dict(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._conn().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return usuario_to_dict(row) if row else None

    def buscar_credenciais(self, email):
        """Retorna (usuario_publico, hash_da_senha) ou (None, None)."""
        row = self._conn().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        if not row:
            return None, None
        return usuario_to_dict(row), row["senha"]

    def criar(self, nome, email, senha_hash, tipo):
        conn = self._conn()
        with conn:
            cursor = conn.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_hash, tipo),
            )
        return cursor.lastrowid

    def atualizar_senha(self, usuario_id, senha_hash):
        conn = self._conn()
        with conn:
            conn.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))
