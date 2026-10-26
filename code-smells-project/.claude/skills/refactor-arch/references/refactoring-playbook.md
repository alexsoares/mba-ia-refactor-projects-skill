# Playbook de Refatoração (Fase 3)

Padrões concretos de transformação. Cada padrão indica os anti-patterns que resolve, os passos e exemplos
**antes/depois** em Python e/ou JavaScript. Adapte nomes e sintaxe ao projeto — o objetivo é o padrão, não copiar o código.

| Padrão | Resolve | Título |
|---|---|---|
| P-01 | AP-01, AP-12 | Configuração por variáveis de ambiente |
| P-02 | AP-02 | Queries parametrizadas |
| P-03 | AP-03 | Decompor God Class em camadas MVC |
| P-04 | AP-07 | Extrair controller de rota gorda (rota fina) |
| P-05 | AP-05 | Hash de senha adaptativo com salt |
| P-06 | AP-06, AP-15 | Serializer/DTO explícito sem campos sensíveis |
| P-07 | AP-08, AP-09 | Injeção de dependência + composition root |
| P-08 | AP-09 | Conexão de banco gerenciada pelo ciclo de vida da app |
| P-09 | AP-10 | Transação / unidade de trabalho |
| P-10 | AP-11 | Callbacks → Promises + async/await |
| P-11 | AP-16, AP-06 | Exceções de domínio + error handler centralizado |
| P-12 | AP-04, AP-12 | Middleware de autorização e token assinado |
| P-13 | AP-13 | Eliminar N+1 (JOIN, eager loading, agregação) |
| P-14 | AP-14 | Validador único por recurso |
| P-15 | AP-15, AP-23 | Regra de domínio no model / função compartilhada |
| P-16 | AP-18 | Efeitos colaterais em serviço injetado |
| P-17 | AP-19 | Constantes nomeadas para magic numbers/strings |
| P-18 | AP-20, AP-21, AP-23 | Nomes expressivos e remoção de código morto |
| P-19 | AP-22 | Logger no lugar de print/console.log |
| P-20 | AP-17 | Substituição de APIs deprecated |

---

## P-01 — Configuração por variáveis de ambiente

**Passos**: criar `config/settings` (único leitor de env) → remover literais sensíveis → `DEBUG` falso por padrão → `.env.example`.

**Antes (Python)**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```
**Depois**
```python
# src/config/settings.py
import os, secrets, logging

def _bool(value, default=False):
    return default if value is None else value.strip().lower() in ("1", "true", "yes", "on")

class Settings:
    def __init__(self, env=os.environ):
        self.SECRET_KEY = env.get("SECRET_KEY") or secrets.token_hex(32)
        if not env.get("SECRET_KEY"):
            logging.getLogger(__name__).warning("SECRET_KEY não definida; usando chave efêmera.")
        self.DEBUG = _bool(env.get("APP_DEBUG"))
        self.HOST = env.get("APP_HOST", "127.0.0.1")
        self.PORT = int(env.get("APP_PORT", "5000"))
        self.DATABASE_PATH = env.get("DATABASE_PATH", "loja.db")

# app.py (entry point)
settings = Settings()
app = create_app(settings)
app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

**Antes (JS)**
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123", port: 3000 };
```
**Depois**
```js
// src/config/index.js
const config = Object.freeze({
  port: Number(process.env.PORT || 3000),
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',   // sem valor real no código
  db: { filename: process.env.DB_FILENAME || ':memory:' },
});
module.exports = config;
```
```dotenv
# .env.example
PORT=3000
PAYMENT_GATEWAY_KEY=
```

## P-02 — Queries parametrizadas

**Antes**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND (nome LIKE '%" + termo + "%')"
```
**Depois**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))

clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
if categoria:
    clauses.append("categoria = ?")
    params.append(categoria)
cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}", params)  # só fragmentos fixos interpolados
```
**JS**
```js
// antes:  db.get(`SELECT * FROM users WHERE email = '${email}'`)
// depois:
await db.get('SELECT * FROM users WHERE email = ?', [email]);
```

## P-03 — Decompor God Class em camadas MVC

**Passos**: listar responsabilidades do arquivo (mapa da Fase 1) → mover cada uma para sua camada → o arquivo original deixa de existir ou vira composition root.

**Antes (JS)**
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE + seeds */ }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { /* validação + SQL + pagamento + auditoria */ });
    app.get('/api/admin/financial-report', (req, res) => { /* N+1 + agregação */ });
  }
}
```
**Depois**
```
src/database/connection.js     → wrapper do driver
src/database/schema.js         → initDb() (DDL + seed)
src/models/courseModel.js      → queries de cursos
src/models/enrollmentModel.js  → matrícula + pagamento
src/services/paymentGateway.js → decisão de pagamento
src/controllers/checkoutController.js → fluxo do checkout
src/views/checkoutRoutes.js    → POST /api/checkout
src/app.js                     → createApp(): monta tudo
```

## P-04 — Extrair controller de rota gorda (rota fina)

**Antes (Flask)**
```python
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data.get('title'): return jsonify({'error': 'Título é obrigatório'}), 400
    if data.get('user_id') and not User.query.get(data['user_id']): return jsonify(...), 404
    task = Task(); task.title = data['title']; ...
    db.session.add(task); db.session.commit()
    return jsonify(task.to_dict()), 201
```
**Depois**
```python
# src/controllers/task_controller.py
class TaskController:
    def __init__(self, session):
        self.session = session

    def create(self, payload):
        data = validate_task(payload, partial=False)          # P-14
        self._ensure_refs(data)                               # lança NotFoundError
        task = Task(**data)
        self.session.add(task)
        self.session.commit()
        return task.to_dict()

# src/views/task_routes.py
def create_task_blueprint(controller):
    bp = Blueprint("tasks", __name__)

    @bp.post("/tasks")
    def create_task():
        return jsonify(controller.create(request.get_json(silent=True))), 201

    return bp
```

## P-05 — Hash de senha adaptativo com salt

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()       # ou senha em texto puro
```
```js
function badCrypto(pwd) { let h = ""; for (...) h += Buffer.from(pwd).toString('base64').substring(0, 2); return h; }
```
**Depois (Python — werkzeug já vem com Flask)**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, raw):
    self.password = generate_password_hash(raw)

def check_password(self, raw):
    return check_password_hash(self.password, raw)
```
Migração de hashes legados (opcional, quando já existe banco com md5): se o hash armazenado tem 32 caracteres hex,
compare com md5 **uma vez** e regrave com `generate_password_hash` no login bem-sucedido.

**Depois (Node — stdlib)**
```js
const crypto = require('node:crypto');
function hashPassword(raw) {
  const salt = crypto.randomBytes(16).toString('hex');
  return `${salt}:${crypto.scryptSync(raw, salt, 64).toString('hex')}`;
}
function verifyPassword(raw, stored) {
  const [salt, hash] = stored.split(':');
  return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), crypto.scryptSync(raw, salt, 64));
}
```
Login: buscar **por e-mail** e verificar o hash em código — nunca `WHERE senha = ?`.

## P-06 — Serializer/DTO explícito sem campos sensíveis

**Antes**
```python
def to_dict(self):
    return {'id': self.id, 'email': self.email, 'password': self.password, ...}
# e 3 cópias manuais do mesmo dict de produto em funções diferentes
```
**Depois**
```python
PRODUTO_FIELDS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")

def produto_to_dict(row):
    return {field: row[field] for field in PRODUTO_FIELDS}

def to_dict(self):                      # User
    return {"id": self.id, "name": self.name, "email": self.email,
            "role": self.role, "active": self.active, "created_at": str(self.created_at)}
```
Health check: devolva apenas `status`, `database`, contagens e versão — nunca `secret_key`, `debug`, caminhos.

## P-07 — Injeção de dependência + composition root

**Antes**
```python
# models.py
from database import get_db
def get_todos_produtos():
    db = get_db()          # dependência global escondida
```
**Depois**
```python
# src/models/produto_model.py
class ProdutoModel:
    def __init__(self, get_connection):
        self._conn = get_connection          # injetado

    def listar(self):
        return [produto_to_dict(r) for r in self._conn().execute("SELECT * FROM produtos")]

# src/app.py (composition root)
def create_app(settings):
    app = Flask(__name__)
    database = Database(settings.DATABASE_PATH)
    produto_model = ProdutoModel(database.connection)
    produto_controller = ProdutoController(produto_model)
    app.register_blueprint(create_produto_blueprint(produto_controller))
    register_error_handlers(app)
    return app
```
**JS**
```js
// src/app.js
function createApp({ config, db }) {
  const courses = new CourseModel(db);
  const checkout = new CheckoutController({ courses, users: new UserModel(db), payments: new PaymentGateway(config) });
  const app = express();
  app.use(express.json());
  app.use('/api', checkoutRoutes(checkout));
  app.use(errorHandler);
  return app;
}
```

## P-08 — Conexão de banco gerenciada pelo ciclo de vida

**Antes**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```
**Depois**
```python
# src/database.py
import sqlite3
from flask import g

class Database:
    def __init__(self, path):
        self.path = path

    def connection(self):
        if "db" not in g:
            g.db = sqlite3.connect(self.path)
            g.db.row_factory = sqlite3.Row
        return g.db

    def init_app(self, app):
        app.teardown_appcontext(self.close)

    def close(self, exc=None):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()
```

## P-09 — Transação / unidade de trabalho

**Antes**
```python
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ...")
db.commit()                         # falha no meio = estado parcial
```
**Depois (sqlite3: o connection como context manager faz commit/rollback)**
```python
with conn:                          # BEGIN ... COMMIT, ou ROLLBACK em exceção
    pedido_id = conn.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                             (usuario_id, total)).lastrowid
    conn.executemany("INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                     [(pedido_id, i["produto_id"], i["quantidade"], precos[i["produto_id"]]) for i in itens])
    conn.executemany("UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                     [(i["quantidade"], i["produto_id"]) for i in itens])
```
**JS**
```js
async transaction(work) {
  await this.run('BEGIN');
  try { const result = await work(); await this.run('COMMIT'); return result; }
  catch (err) { await this.run('ROLLBACK'); throw err; }
}
// exclusão sem órfãos
await db.transaction(async () => {
  await db.run('DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)', [id]);
  await db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
  await db.run('DELETE FROM users WHERE id = ?', [id]);
});
```
> Atenção: com SQLite e uma única conexão compartilhada, serialize as transações (fila/mutex) para que requisições concorrentes não intercalem `BEGIN`s.

## P-10 — Callbacks → Promises + async/await

**Antes**
```js
this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
  this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
    this.db.run("INSERT INTO enrollments ...", [userId, cid], function (err) {
      self.db.run("INSERT INTO payments ...", [this.lastID, ...], function (err) { res.json(...) });
    });
  });
});
```
**Depois**
```js
// src/database/connection.js
run(sql, params = []) {
  return new Promise((resolve, reject) =>
    this.db.run(sql, params, function (err) { err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes }); }));
}
get(sql, params = []) { return new Promise((res, rej) => this.db.get(sql, params, (e, row) => (e ? rej(e) : res(row)))); }

// src/controllers/checkoutController.js
async checkout({ name, email, password, courseId, card }) {
  const course = await this.courses.findActiveById(courseId);
  if (!course) throw new AppError(404, 'Curso não encontrado');
  const user = (await this.users.findByEmail(email)) ?? (await this.users.create({ name, email, password }));
  ...
}
```

## P-11 — Exceções de domínio + error handler centralizado

**Antes**
```python
def buscar_produto(id):
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500     # repetido em todo handler, vaza detalhes
```
**Depois**
```python
# src/errors.py
class AppError(Exception):
    status_code = 400
    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code or self.status_code
        self.payload = payload or {}

class NotFoundError(AppError):
    status_code = 404

# src/middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, **err.payload}), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err
        app.logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
```
**JS**
```js
// src/middlewares/asyncHandler.js
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
// src/middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
  if (err instanceof AppError) return res.status(err.status).send(err.message);
  console.error(err);
  res.status(500).send('Erro interno');
};
```
Mantenha a **chave de erro original** do contrato (`erro`, `error`, texto puro) para não quebrar clientes.

## P-12 — Middleware de autorização e token assinado

**Antes**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json()["sql"])     # SQL arbitrário, sem auth
...
return {'token': 'fake-jwt-token-' + str(user.id)}
```
**Depois**
```python
# src/middlewares/auth.py
def require_admin_token(settings):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            token = request.headers.get("X-Admin-Token", "")
            if not settings.ADMIN_TOKEN or not hmac.compare_digest(token, settings.ADMIN_TOKEN):
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)
        return wrapper
    return decorator
# rota administrativa: desabilitada se ADMIN_TOKEN não estiver configurado; consulta só leitura (SELECT único).

# token assinado sem dependência nova (itsdangerous vem com Flask)
from itsdangerous import URLSafeTimedSerializer
serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="auth")
token = serializer.dumps({"user_id": user.id})
```

## P-13 — Eliminar N+1

**Antes (SQL cru)**
```python
for row in pedidos:
    itens = cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        prod = cursor.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**Depois**
```python
rows = conn.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
      FROM pedidos p
      LEFT JOIN itens_pedido i ON i.pedido_id = p.id
      LEFT JOIN produtos pr    ON pr.id = i.produto_id
     WHERE (? IS NULL OR p.usuario_id = ?)
  ORDER BY p.id, i.id""", (usuario_id, usuario_id)).fetchall()
# agrupar em Python por p.id
```
**Antes (ORM)**
```python
for t in Task.query.all():
    user = User.query.get(t.user_id)            # 1 query por task
```
**Depois**
```python
from sqlalchemy.orm import joinedload
tasks = db.session.execute(
    db.select(Task).options(joinedload(Task.user), joinedload(Task.category))
).scalars().all()

# contagens: uma query agregada
counts = dict(db.session.execute(db.select(Task.status, db.func.count()).group_by(Task.status)).all())
```
**JS (relatório)**
```js
const rows = await db.all(`
  SELECT c.id AS course_id, c.title, u.name AS student, p.amount, p.status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u       ON u.id = e.user_id
    LEFT JOIN payments p    ON p.enrollment_id = e.id
   ORDER BY c.id, e.id`);
```

## P-14 — Validador único por recurso

**Antes**: validação de produto copiada em `criar_produto` e `atualizar_produto`, com regras diferentes; `priority < 1` estoura `TypeError` se vier string.
**Depois**
```python
# src/controllers/validators.py  (ou src/validators/)
def validate_produto(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    for campo, msg in (("nome", "Nome é obrigatório"), ("preco", "Preço é obrigatório"), ("estoque", "Estoque é obrigatório")):
        if campo not in dados:
            raise ValidationError(msg)
    preco, estoque = dados["preco"], dados["estoque"]
    if not isinstance(preco, (int, float)) or preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    ...
    return {"nome": nome, "descricao": dados.get("descricao", ""), "preco": preco, "estoque": estoque, "categoria": categoria}
```
Preserve as **mensagens originais** de erro (fazem parte do contrato).
**JS**
```js
function parseCheckout(body = {}) {
  const { usr: name, eml: email, pwd: password, c_id: courseId, card } = body;
  if (!name || !email || !courseId || !card) throw new AppError(400, 'Bad Request');
  return { name, email, password, courseId, card };
}
```

## P-15 — Regra de domínio no model / função compartilhada

**Antes** (repetido em 5 handlers)
```python
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            overdue = True
```
**Depois**
```python
# src/models/task.py
CLOSED_STATUSES = ("done", "cancelled")

def is_overdue(self, now=None):
    now = now or utcnow()
    return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)
```
Todos os pontos passam a chamar `task.is_overdue()`.

## P-16 — Efeitos colaterais em serviço injetado

**Antes**
```python
resultado = models.criar_pedido(usuario_id, itens)
print("ENVIANDO EMAIL: Pedido ...")
print("ENVIANDO SMS: ...")
```
**Depois**
```python
# src/services/notification_service.py
class NotificationService:
    def __init__(self, logger):
        self.logger = logger
    def pedido_criado(self, pedido_id, usuario_id):
        self.logger.info("Notificação: pedido %s criado para usuário %s", pedido_id, usuario_id)

# controller (após o commit)
pedido = self.pedidos.criar(usuario_id, itens)
self.notifications.pedido_criado(pedido["pedido_id"], usuario_id)
```
Serviços SMTP recebem host/porta/usuário/senha da config injetada (P-01) — nunca literais.

## P-17 — Constantes nomeadas

**Antes**
```python
if faturamento > 10000: desconto = faturamento * 0.1
elif faturamento > 5000: desconto = faturamento * 0.05
```
```js
let status = cc.startsWith("4") ? "PAID" : "DENIED";
```
**Depois**
```python
# faixas (limiar, percentual) em ordem decrescente
DESCONTO_POR_FATURAMENTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))

def calcular_desconto(faturamento):
    return next((faturamento * pct for limite, pct in DESCONTO_POR_FATURAMENTO if faturamento > limite), 0)
```
```js
const PaymentStatus = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });
const APPROVED_CARD_PREFIX = '4'; // regra do gateway simulado
```

## P-18 — Nomes expressivos e remoção de código morto

**Antes**
```js
let u = req.body.usr; let e = req.body.eml; let p = req.body.pwd; let cid = req.body.c_id; let cc = req.body.card;
const { config, logAndCache, badCrypto, totalRevenue } = require('./utils');   // totalRevenue nunca usado
```
```python
import os, sys, json, datetime     # só datetime é usado
def is_admin(self):
    if self.role == 'admin':
        return True
    else:
        return False
```
**Depois**
```js
const { usr: name, eml: email, pwd: password, c_id: courseId, card } = req.body;   // contrato preservado
```
```python
import datetime
def is_admin(self):
    return self.role == "admin"
```

## P-19 — Logger no lugar de print/console.log

**Antes**
```python
print("Login bem-sucedido: " + email)
print("ERRO: " + str(e))
```
**Depois**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Login bem-sucedido para usuário id=%s", usuario["id"])   # sem dado sensível
logger.exception("Falha ao criar pedido")                            # dentro do error handler
```
```js
const logger = require('../config/logger');   // wrapper com níveis; nunca logar cartão/chave
logger.info(`Checkout concluído: enrollment ${enrollmentId}`);
```

## P-20 — Substituição de APIs deprecated

**Antes**
```python
task = Task.query.get(task_id)
created_at = db.Column(db.DateTime, default=datetime.utcnow)
```
**Depois**
```python
from datetime import datetime, timezone

def utcnow():
    """UTC 'naive' para colunas DateTime sem timezone (compatível com dados existentes)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

task = db.session.get(Task, task_id)
created_at = db.Column(db.DateTime, default=utcnow)
```
```js
// antes: new Buffer(pwd)            depois: Buffer.from(pwd)
// antes: url.parse(req.url)         depois: new URL(req.url, `http://${req.headers.host}`)
// antes: app.use(bodyParser.json()) depois: app.use(express.json())
```
