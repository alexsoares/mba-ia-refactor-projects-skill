# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. O projeto já tinha alguma separação
de camadas (`models/`, `routes/`, `services/`, `utils/`) e foi **completado para MVC** pela skill
(relatório da auditoria em [`../reports/audit-project-3.md`](../reports/audit-project-3.md)).

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: carregado automaticamente via python-dotenv
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários,
categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

| Variável | Uso | Padrão |
|---|---|---|
| `SECRET_KEY` | Assinatura dos tokens de login | aleatória por processo |
| `APP_DEBUG` / `APP_HOST` / `APP_PORT` | Execução | `false` / `127.0.0.1` / `5000` |
| `DATABASE_URL` | URI do SQLAlchemy | `sqlite:///tasks.db` |
| `TOKEN_MAX_AGE_SECONDS` | Validade do token | `3600` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Notificação por e-mail ao atribuir task | desligada |

## Estrutura (MVC)

```
app.py                      # entry point
seed.py                     # dados de exemplo (usa create_app)
src/
├── app.py                  # composition root (create_app)
├── config/settings.py      # configuração via variáveis de ambiente
├── constants.py            # status, prioridades, limites, roles
├── extensions.py           # instância do SQLAlchemy
├── errors.py               # exceções de domínio
├── models/                 # Task, User, Category (ORM + regras da entidade)
├── controllers/            # casos de uso: tasks, users, reports, categories + validators
├── views/                  # Blueprints finos (um por recurso)
├── services/               # notificação por e-mail, tokens assinados
├── middlewares/            # error handler central
└── utils/time.py           # utcnow() (substitui datetime.utcnow, deprecated)
```
