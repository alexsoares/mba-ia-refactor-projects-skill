# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch` — **refatorada para MVC** pela skill
(relatório da auditoria em [`../reports/audit-project-1.md`](../reports/audit-project-1.md)).

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: ajuste as variáveis e exporte-as no shell
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (host/porta configuráveis por `APP_HOST`/`APP_PORT`). O banco SQLite (`loja.db`)
é criado automaticamente no primeiro boot, com produtos e usuários de exemplo (senhas gravadas com hash).

| Variável | Uso | Padrão |
|---|---|---|
| `SECRET_KEY` | Chave do Flask | aleatória por processo |
| `APP_DEBUG` | Liga o modo debug | `false` |
| `APP_HOST` / `APP_PORT` | Bind do servidor | `127.0.0.1` / `5000` |
| `DATABASE_PATH` | Arquivo SQLite | `loja.db` |
| `ADMIN_TOKEN` | Valor exigido no header `X-Admin-Token` das rotas `/admin/*` | vazio (rotas admin bloqueadas) |
| `SEED_ADMIN_PASSWORD` | Senha do `admin@loja.com` criado no seed | aleatória |

## Estrutura (MVC)

```
app.py                      # entry point
src/
├── app.py                  # composition root (create_app)
├── config/settings.py      # configuração via variáveis de ambiente
├── constants.py            # regras de negócio nomeadas
├── database.py             # conexão por requisição, schema e seed
├── errors.py               # exceções de domínio
├── models/                 # acesso a dados (produto, usuario, pedido, sistema)
├── controllers/            # casos de uso + validators
├── views/                  # Blueprints (rotas finas)
├── services/               # notificações
└── middlewares/            # error handler central e autorização admin
```
