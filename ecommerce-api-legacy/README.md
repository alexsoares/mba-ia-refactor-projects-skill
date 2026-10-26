# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch` — **refatorada para MVC**
pela skill (relatório da auditoria em [`../reports/audit-project-2.md`](../reports/audit-project-2.md)).

## Como rodar

```bash
npm install
ADMIN_TOKEN=troque-este-token npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória (configurável por `DB_FILENAME`) e carrega seeds
automaticamente no boot. Exemplos de requisições estão em `api.http` — as rotas administrativas exigem o header
`X-Admin-Token` com o mesmo valor de `ADMIN_TOKEN` (sem `ADMIN_TOKEN` elas ficam bloqueadas com `403`).

| Variável | Uso | Padrão |
|---|---|---|
| `PORT` | Porta HTTP | `3000` |
| `DB_FILENAME` | Arquivo SQLite | `:memory:` |
| `PAYMENT_GATEWAY_KEY` | Chave do gateway de pagamento | vazio |
| `ADMIN_TOKEN` | Token das rotas administrativas | vazio (bloqueadas) |
| `LOG_LEVEL` | `error`, `warn`, `info`, `debug` | `info` |
| `CACHE_MAX_ENTRIES` | Limite do cache em memória | `1000` |

## Estrutura (MVC)

```
src/
├── server.js               # entry point (npm start)
├── app.js                  # composition root (createApp)
├── config/                 # configuração via env + logger
├── constants.js            # status de pagamento e regras nomeadas
├── database/               # wrapper Promise do sqlite3 (fila + transações) e schema/seed
├── errors/AppError.js      # erro de domínio
├── models/                 # users, courses, enrollments/payments, audit_logs
├── controllers/            # checkout, relatório financeiro, usuários
├── views/                  # express.Router finos
├── services/               # gateway de pagamento, hash de senha, cache
└── middlewares/            # errorHandler, asyncHandler, requireAdmin
```
