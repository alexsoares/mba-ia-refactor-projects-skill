"""Conexão SQLite por requisição, criação do schema e dados de exemplo."""
import logging
import secrets
import sqlite3
from pathlib import Path

from flask import g
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)

PRODUTOS_EXEMPLO = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

# Clientes fictícios para desenvolvimento local (senhas gravadas com hash).
CLIENTES_EXEMPLO = [
    ("João Silva", "joao@email.com", "123456"),
    ("Maria Santos", "maria@email.com", "senha123"),
]


class Database:
    def __init__(self, path):
        self.path = path

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def connection(self):
        """Conexão da requisição atual (aberta sob demanda, fechada no teardown)."""
        if "db" not in g:
            g.db = self._connect()
        return g.db

    def readonly_connection(self):
        uri = Path(self.path).resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def init_app(self, app):
        app.teardown_appcontext(self.close)

    def close(self, exc=None):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    def initialize(self, admin_password=""):
        """Cria o schema e, se o banco estiver vazio, insere os dados de exemplo."""
        conn = self._connect()
        try:
            with conn:
                for ddl in SCHEMA:
                    conn.execute(ddl)
                if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
                    self._seed(conn, admin_password)
        finally:
            conn.close()

    @staticmethod
    def _seed(conn, admin_password):
        conn.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            PRODUTOS_EXEMPLO,
        )
        if not admin_password:
            admin_password = secrets.token_urlsafe(16)
            logger.warning("SEED_ADMIN_PASSWORD não definida: usuário admin criado com senha aleatória.")
        usuarios = [("Admin", "admin@loja.com", admin_password, "admin")]
        usuarios += [(nome, email, senha, "cliente") for nome, email, senha in CLIENTES_EXEMPLO]
        conn.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            [(nome, email, generate_password_hash(senha), tipo) for nome, email, senha, tipo in usuarios],
        )
