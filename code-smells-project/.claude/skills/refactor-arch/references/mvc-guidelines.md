# Guidelines de Arquitetura — MVC Alvo (Fase 3)

Em uma API backend não há "tela": a **View** é a camada de apresentação HTTP — as rotas que traduzem
requisições em chamadas ao controller e o resultado em resposta (JSON/texto). O MVC alvo desta skill é:

```
            HTTP request
                 │
┌────────────────▼────────────────┐
│ VIEWS / ROUTES  (apresentação)  │  parse do request, chama controller, serializa resposta
└────────────────┬────────────────┘
                 │ dados simples (dict/obj), nunca o objeto request
┌────────────────▼────────────────┐
│ CONTROLLERS  (fluxo da app)     │  orquestra o caso de uso, valida, aplica regras, lança erros de domínio
└───────┬─────────────────┬───────┘
        │                 │
┌───────▼───────┐  ┌──────▼────────────┐
│ MODELS        │  │ SERVICES (infra)  │  e-mail, gateway de pagamento, cache, notificação
│ (dados+regras │  └───────────────────┘
│  de entidade) │
└───────┬───────┘
        │
     Banco de dados

Transversais: CONFIG (settings por ambiente) · MIDDLEWARES (erro, auth) · COMPOSITION ROOT (app factory)
```

## Responsabilidades por camada

### Models
- **Fazem**: representar entidades e tabelas; encapsular **todo** acesso a dados (queries parametrizadas, ORM, transações);
  regras intrínsecas da entidade (`task.is_overdue()`, `user.check_password()`); serialização segura da entidade (`to_dict()` sem campos sensíveis).
- **Não fazem**: ler `request`/`req`, devolver respostas HTTP, chamar serviços externos (e-mail), ler variáveis de ambiente.
- Forma: classes de entidade (ORM) e/ou **repositórios** (`ProdutoModel`, `CourseRepository`) que recebem a conexão por injeção.

### Controllers
- **Fazem**: implementar os casos de uso (criar pedido, checkout, relatório); validar entrada (via validadores/schemas);
  coordenar models e serviços; decidir o fluxo (ex.: pagamento negado → erro); lançar **exceções de domínio** (`NotFoundError`, `ValidationError`).
- **Não fazem**: conhecer o framework HTTP (sem `request`, `jsonify`, `res.status`); SQL direto; ler `os.environ`.
- Recebem dependências (models/repositórios, serviços, config) **pelo construtor ou factory** → testáveis com fakes.
- Retornam dados simples (dict, lista, objeto) que a view transforma em resposta.

### Views / Routes
- **Fazem**: declarar rotas (método + path); extrair parâmetros de path/query/body; chamar **um** método do controller;
  converter o retorno em resposta com o status code correto.
- **Não fazem**: regra de negócio, loops sobre entidades, queries, `try/except` genérico (erros sobem para o middleware).
- Meta: cada handler com **≤ ~10 linhas**.

### Services (infraestrutura)
- Integrações externas: e-mail/SMTP, gateway de pagamento, cache, filas. Recebem config por injeção. Chamados por controllers.

### Config
- Único módulo que lê variáveis de ambiente (`os.environ`, `process.env`, `.env` via `python-dotenv` se já for dependência).
- Segredos **sem valor real** no código. Defaults permitidos apenas para valores não sensíveis de desenvolvimento
  (porta, caminho do SQLite). Para `SECRET_KEY` ausente: gerar valor aleatório em runtime (`secrets.token_hex`) e registrar aviso.
- `DEBUG` desligado por padrão; liga só via variável de ambiente.
- Entregar um `.env.example` documentando as variáveis.

### Middlewares
- **Error handler central**: converte exceções de domínio em respostas (`404`, `400`, `409`...) e exceções inesperadas em `500` genérico **sem vazar `str(e)`**, registrando o erro no log.
- **Autorização** de rotas administrativas (token/header) quando aplicável.

### Composition root (app factory) e entry point
- Uma função (`create_app()` / `createApp()`) que: carrega config → cria conexão/ORM → instancia models, services e controllers
  (injeção de dependência) → registra rotas e middlewares → retorna a app. **Nenhuma outra parte do código instancia dependências.**
- Entry point separado e mínimo (`app.py`/`server.js`): chama a factory e sobe o servidor com host/porta/debug vindos da config.

## Regra de dependência (imports permitidos)

| Camada | Pode importar | Não pode importar |
|---|---|---|
| views/routes | controllers (via injeção), framework HTTP | models, banco, services |
| controllers | models, services (via injeção), errors, validators | framework HTTP, config/env |
| models | driver/ORM, errors | controllers, views, framework HTTP |
| services | config injetada, libs de integração | controllers, views |
| middlewares | framework HTTP, errors, logger | models |
| config | stdlib | qualquer camada |

## Estrutura-alvo por stack

### Python / Flask — projeto monolítico (SQL cru)

```
<projeto>/
├── app.py                       # entry point mínimo: create_app() + app.run(config)
├── requirements.txt
├── .env.example
└── src/
    ├── __init__.py
    ├── app.py                   # composition root: create_app()
    ├── config/
    │   ├── __init__.py
    │   └── settings.py          # lê env vars
    ├── database.py              # conexão (por requisição via flask.g) + schema + seed
    ├── errors.py                # exceções de domínio
    ├── models/
    │   ├── __init__.py
    │   └── <entidade>_model.py  # repositório com queries parametrizadas
    ├── controllers/
    │   ├── __init__.py
    │   └── <entidade>_controller.py
    ├── views/
    │   ├── __init__.py
    │   └── <entidade>_routes.py # Blueprints finos
    ├── services/                # opcional: notificações, integrações
    └── middlewares/
        ├── __init__.py
        ├── error_handler.py
        └── auth.py              # se houver rotas admin
```

### Python / Flask — projeto com camadas parciais (ORM)

Reaproveite `models/` (entidades ORM) e `services/`; transforme `routes/` em **views** finas e extraia **controllers**:

```
<projeto>/
├── app.py                       # entry point
├── seed.py                      # atualizado para usar create_app()
└── src/
    ├── app.py                   # create_app()
    ├── config/settings.py
    ├── extensions.py            # db = SQLAlchemy()
    ├── errors.py
    ├── models/                  # entidades ORM (sem senha no to_dict, regras da entidade)
    ├── controllers/             # casos de uso extraídos das rotas
    ├── views/                   # blueprints finos (um por recurso; recurso fora do lugar ganha arquivo próprio)
    ├── services/                # notificação etc., com config injetada
    ├── validators/ ou utils/    # validação centralizada, constantes de domínio
    └── middlewares/error_handler.py
```

### Node.js / Express

```
<projeto>/
├── package.json                 # "start": "node src/server.js"
├── .env.example
└── src/
    ├── server.js                # entry point: createApp() + listen(config.port)
    ├── app.js                   # composition root: createApp()
    ├── config/
    │   └── index.js             # lê process.env
    ├── database/
    │   ├── connection.js        # wrapper Promise do driver (run/get/all/transaction)
    │   └── schema.js            # DDL + seed
    ├── errors/AppError.js
    ├── models/                  # <entidade>Model.js — acesso a dados
    ├── controllers/             # <recurso>Controller.js — casos de uso (async/await)
    ├── views/ (ou routes/)      # <recurso>Routes.js — express.Router fino
    ├── services/                # paymentGateway, cache, passwordHasher...
    └── middlewares/
        ├── errorHandler.js
        └── asyncHandler.js
```

### Outras stacks (mapeamento)

| Stack | Views/Routes | Controllers | Models | Error handling |
|---|---|---|---|---|
| FastAPI | `APIRouter` em `views/` | classes injetadas via `Depends` | SQLAlchemy/repos | `@app.exception_handler` |
| Django | `urls.py` + views finas | `services.py`/use cases | `models.py` (ORM) | middleware |
| NestJS | `@Controller` (já é a view HTTP) | `@Injectable` services | entities/repositories | `ExceptionFilter` |
| Spring | `@RestController` | `@Service` | `@Entity` + `Repository` | `@ControllerAdvice` |

## Critérios de pronto (Definition of Done da Fase 3)

- [ ] Estrutura de diretórios com `models`, `views` (ou `routes`), `controllers`, `config`, `middlewares`.
- [ ] Nenhum segredo com valor real no código; config lida do ambiente; `.env.example` presente.
- [ ] Models encapsulam todo acesso a dados; zero SQL concatenado.
- [ ] Rotas finas (sem regra de negócio e sem acesso a banco).
- [ ] Controllers concentram o fluxo e recebem dependências injetadas.
- [ ] Error handling centralizado; nenhuma resposta com `str(e)`.
- [ ] Entry point claro e composition root único.
- [ ] Aplicação sobe sem erros e todos os endpoints do inventário respondem com o mesmo contrato.
