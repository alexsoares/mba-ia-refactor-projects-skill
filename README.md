# Refatoração Arquitetural Automatizada com Skills — `refactor-arch`

Entrega do desafio **"Criação de Skills — Refatoração Arquitetural Automatizada"** (MBA IA). Este repositório contém:

- a skill **`refactor-arch`** para Claude Code (`.claude/skills/refactor-arch/`, copiada nos 3 projetos), que analisa, audita e refatora qualquer backend para o padrão **MVC** em 3 fases;
- o **código refatorado** dos 3 projetos legados (resultado da Fase 3, um commit por projeto);
- os **relatórios de auditoria** da Fase 2 em [`reports/`](reports/);
- esta documentação (análise manual, construção da skill, resultados e como executar).

| Projeto | Stack | Domínio | Relatório |
|---|---|---|---|
| [`code-smells-project/`](code-smells-project/) | Python 3 + Flask 3.1.1 (sqlite3 cru) | API de E-commerce | [`audit-project-1.md`](reports/audit-project-1.md) |
| [`ecommerce-api-legacy/`](ecommerce-api-legacy/) | Node.js 22 + Express 4 (sqlite3 callbacks) | LMS com checkout | [`audit-project-2.md`](reports/audit-project-2.md) |
| [`task-manager-api/`](task-manager-api/) | Python 3 + Flask 3.0 + Flask-SQLAlchemy | Task Manager | [`audit-project-3.md`](reports/audit-project-3.md) |

---

## A) Análise Manual

Antes de escrever a skill, li o código dos três projetos linha a linha e subi as três APIs originais para registrar o comportamento de **todos** os endpoints (baseline). As severidades seguem a escala do desafio: **CRITICAL** = segurança grave ou violação total de responsabilidades; **HIGH** = violação forte de MVC/SOLID; **MEDIUM** = padronização, duplicação ou performance; **LOW** = legibilidade.

### Projeto 1 — code-smells-project (Python/Flask, E-commerce)

| # | Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | **SQL Injection** em praticamente todas as queries (concatenação de strings) | `models.py:28, 47-50, 109-111, 289-297`... | Comprovado no baseline: `POST /login` com `' OR '1'='1` autentica como **Admin** sem senha. |
| 2 | CRITICAL | **Endpoints admin sem autenticação**: `/admin/reset-db` apaga todas as tabelas e `/admin/query` executa **SQL arbitrário** do corpo da requisição | `app.py:47-78` | Backdoor: qualquer cliente anônimo destrói ou exfiltra o banco. |
| 3 | CRITICAL | **Credenciais hardcoded** e expostas: `SECRET_KEY` fixa, repetida na resposta do `/health` | `app.py:7`, `controllers.py:289` | A chave de assinatura do Flask fica pública no repositório **e** na API. |
| 4 | CRITICAL | **Senhas em texto puro**, comparadas no SQL e devolvidas por `GET /usuarios` | `models.py:83, 99, 122-131` | Qualquer cliente lê as senhas de todos os usuários. |
| 5 | CRITICAL | **God File**: `models.py` reúne SQL de 4 domínios, regras de negócio (estoque, desconto) e formatação | `models.py:1-314` | Nada é testável isoladamente; qualquer mudança tem impacto global. |
| 6 | HIGH | **Estado global mutável**: conexão SQLite singleton com `check_same_thread=False` compartilhada entre threads | `database.py:4-10` | Condições de corrida e transações intercaladas entre requisições. |
| 7 | HIGH | **Pedido sem transação**: estoque verificado e debitado em passos separados, sem rollback | `models.py:133-169` | Falha no meio deixa pedido sem itens ou estoque inconsistente. |
| 8 | HIGH | `debug=True` e `host="0.0.0.0"` fixos | `app.py:8, 88` | O debugger do Werkzeug exposto na rede permite execução remota de código. |
| 9 | MEDIUM | **N+1**: uma query por item e por produto em cada pedido listado | `models.py:171-233` | A latência cresce com pedidos × itens. |
| 10 | MEDIUM | `try/except Exception` em todos os handlers devolvendo `str(e)` | `controllers.py` (16 handlers) | Vaza detalhes internos e não existe tratamento centralizado. |
| 11 | MEDIUM | Validação inconsistente: o update de produto não valida o que o create valida; corpo vazio vira 500 | `controllers.py:64-93, 169-171` | Dados inválidos chegam ao banco; erros do cliente viram 500. |
| 12 | LOW | Magic numbers nas faixas de desconto (`10000/0.1`, `5000/0.05`, `1000/0.02`) | `models.py:256-262` | Regra de negócio escondida em literais. |
| 13 | LOW | `print` como log, inclusive com o e-mail de quem faz login | `controllers.py:8, 57, 179-182` | Sem níveis de log e com dado pessoal no stdout. |
| 14 | LOW | Imports não usados (`sqlite3` em models, `os` em database) | `models.py:2`, `database.py:2` | Ruído. |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com checkout)

| # | Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | **Segredos hardcoded**: senha do banco e chave **live** do gateway (`pk_live_...`) | `src/utils.js:2-5` | Credenciais de produção versionadas. |
| 2 | CRITICAL | **God Class `AppManager`**: cria o banco, o schema e o seed, registra rotas e implementa checkout, relatório e exclusão | `src/AppManager.js:4-139` | Zero separação de camadas; nada é testável. |
| 3 | CRITICAL | **"Criptografia" caseira de senha** (`badCrypto`: base64 truncado em 10 caracteres) e senha padrão `"123456"` | `src/utils.js:17-23`, `AppManager.js:68` | É reversível, gera colisões, e todo usuário criado sem senha recebe uma senha conhecida. |
| 4 | CRITICAL | **Número do cartão e chave do gateway no log** | `src/AppManager.js:45` | Violação de PCI-DSS. |
| 5 | CRITICAL | Relatório financeiro e `DELETE /users/:id` **sem autenticação** | `AppManager.js:80, 131` | Qualquer um lê dados financeiros ou apaga usuários. |
| 6 | HIGH | **Callback hell** (6 níveis), contadores manuais `pending--`, erros de callback ignorados | `AppManager.js:37-77, 83-128` | O fluxo é ilegível, há falhas silenciosas e o risco de nunca responder. |
| 7 | HIGH | Checkout sem transação e **exclusão que deixa órfãos** (a própria resposta admite: "ficaram sujos no banco") | `AppManager.js:50-63, 131-136` | O baseline mostra o aluno apagado como "Unknown" no relatório. |
| 8 | HIGH | **Estado global mutável** (`globalCache` cresce sem limite, `totalRevenue` exportado) | `src/utils.js:9-15` | Vazamento de memória e estado compartilhado entre módulos. |
| 9 | MEDIUM | **N+1** no relatório (1 + C + 2·M queries) | `AppManager.js:89-127` | O relatório degrada com o número de matrículas. |
| 10 | MEDIUM | Erros engolidos: o DELETE responde sucesso mesmo com erro ou com id inexistente | `AppManager.js:133-136` | Sucesso falso para o cliente. |
| 11 | LOW | Nomes ruins: `u`, `e`, `p`, `cid`, `cc`, `self`, `badCrypto` | `AppManager.js:29-33` | Legibilidade. |
| 12 | LOW | Regra de pagamento em literal mágico: `cc.startsWith("4")` | `AppManager.js:46` | Regra de negócio escondida. |

### Projeto 3 — task-manager-api (Python/Flask, Task Manager com camadas parciais)

| # | Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | **MD5 sem salt** para senhas | `models/user.py:27-32` | É quebrado por rainbow table; o hash de "1234" aparece no baseline. |
| 2 | CRITICAL | **Hash da senha devolvido** em `GET /users/<id>`, `POST/PUT /users` e no **login** | `models/user.py:21` | Expõe os hashes (triviais de reverter) de todos os usuários. |
| 3 | CRITICAL | `SECRET_KEY` e **senha SMTP hardcoded** | `app.py:13`, `services/notification_service.py:7-10` | Credenciais no repositório. |
| 4 | HIGH | **Rotas gordas**: não existe camada de controller; handlers de 50-70 linhas com validação, ORM, regras e serialização; CRUD de categorias dentro de `report_routes.py` | `routes/*.py` | Mesmo com pastas separadas, a responsabilidade continua concentrada na camada HTTP. |
| 5 | HIGH | **Token falso** `'fake-jwt-token-' + id` e `debug=True` fixo | `routes/user_routes.py:210`, `app.py:34` | Qualquer um forja o token de qualquer usuário. |
| 6 | MEDIUM | **APIs deprecated**: `Model.query.get()` (legado no SQLAlchemy 2.x) e `datetime.utcnow()` (deprecated no Python 3.12) | 16 + 22 ocorrências | Gera warnings hoje e quebra em upgrades. |
| 7 | MEDIUM | **N+1** em `GET /tasks` (2 queries por task), `/users`, `/categories` e no relatório | `routes/task_routes.py:41-57`... | Escala mal. |
| 8 | MEDIUM | **Duplicação**: a regra "atrasada" foi reimplementada 6 vezes, mesmo existindo `Task.is_overdue()` | `routes/*.py` | As correções divergem entre as cópias. |
| 9 | MEDIUM | 12 `except:` nus e validações que estouram `TypeError` → 500 (`priority` string, `title: null`) | `routes/*.py` | Erros invisíveis no log; erro do cliente vira 500. |
| 10 | LOW | Código morto: `utils/helpers.py` quase inteiro sem uso, `NotificationService` nunca instanciado, `marshmallow`/`requests` sem import | `utils/helpers.py`... | Dá a falsa sensação de que existem validações. |
| 11 | LOW | Condicionais verbosas (`if x: return True else: return False`, `type(x) == list`) | `models/task.py:38-60` | Legibilidade. |

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                              # o "prompt": papel, regras invioláveis e as 3 fases
└── references/
    ├── project-analysis.md               # Fase 1 — heurísticas de linguagem, framework, banco, domínio, arquitetura, endpoints
    ├── anti-patterns-catalog.md          # Fase 2 — 23 anti-patterns com sinais de detecção, grep e severidade (inclui APIs deprecated)
    ├── audit-report-template.md          # Fase 2 — template obrigatório do relatório + exemplos bom/ruim
    ├── mvc-guidelines.md                 # Fase 3 — camadas, regra de dependência e estrutura-alvo por stack
    └── refactoring-playbook.md           # Fase 3 — 20 padrões de transformação com código antes/depois
```

| Área exigida | Arquivo |
|---|---|
| Análise de projeto | `references/project-analysis.md` |
| Catálogo de anti-patterns | `references/anti-patterns-catalog.md` |
| Template de relatório | `references/audit-report-template.md` |
| Guidelines de arquitetura | `references/mvc-guidelines.md` |
| Playbook de refatoração | `references/refactoring-playbook.md` |

### Decisões de design

- **SKILL.md como orquestrador, referências como conhecimento.** O `SKILL.md` define o papel, as **regras invioláveis** e o roteiro das fases, mas não traz conhecimento de stack. Cada referência é lida **só na fase em que é necessária** (*progressive disclosure*), o que economiza contexto e mantém o foco.
- **Regras invioláveis explícitas**: as Fases 1 e 2 são somente leitura; a Fase 2 **termina obrigatoriamente** com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e a skill para; todo finding precisa de `arquivo:linha` conferido com leitura numerada; o contrato público (rotas, status, formato) é preservado, exceto em correções de segurança, que precisam ser listadas.
- **Formato de saída fixo**: os blocos `PHASE 1`, o relatório e `PHASE 3` têm formato literal, o que torna os resultados comparáveis entre projetos e fáceis de verificar.
- **Validação baseada em evidência**: a Fase 3 exige subir a aplicação, repetir as requisições do **baseline capturado antes da edição**, comparar as respostas e rodar de novo os greps do catálogo. A skill não pode declarar sucesso sem ter executado essas checagens.
- **Adaptação ao nível de organização**: para monólitos, a skill cria a estrutura completa; para projetos com camadas parciais, ela **reaproveita** o que está correto (ex.: models ORM) e completa o que falta (controllers, config, error handler), em vez de reescrever do zero.

### Anti-patterns do catálogo (23) e por quê

| Severidade | Anti-patterns | Motivação |
|---|---|---|
| CRITICAL | AP-01 segredos hardcoded · AP-02 SQL Injection · AP-03 God Class · AP-04 admin sem auth · AP-05 senha insegura · AP-06 exposição de dados sensíveis | Encontrados nos 3 projetos; são os que expõem dados ou impedem qualquer evolução. |
| HIGH | AP-07 fat controller · AP-08 sem DI · AP-09 estado global · AP-10 sem transação/órfãos · AP-11 callback hell · AP-12 debug/token falso | São as violações de MVC/SOLID que bloqueiam testes; o AP-11 cobre o caso específico do Node. |
| MEDIUM | AP-13 N+1 · AP-14 validação · AP-15 duplicação · AP-16 erro não centralizado · **AP-17 APIs deprecated** · AP-18 efeitos colaterais | Problemas de performance e padronização. O AP-17 traz uma tabela de APIs obsoletas por stack (SQLAlchemy 2.x, Python 3.12, Flask 2.3+, Node, Express 5) com o equivalente moderno. |
| LOW | AP-19 magic numbers · AP-20 nomes · AP-21 código morto · AP-22 print/console.log · AP-23 condicionais verbosas | Legibilidade. |

Cada anti-pattern traz **sinais concretos** (ex.: "query dentro de `for`", "`cursor.execute` com `+`", "`const self = this`") e **padrões de grep** prontos, além do padrão do playbook (P-xx) que o corrige.

### Como garanti que a skill é agnóstica de tecnologia

1. **Nenhuma instrução do SKILL.md cita uma stack**: as fases falam em "manifesto", "entry point" e "inventário de rotas", e o conhecimento específico fica nas tabelas das referências.
2. **Tabelas de detecção multi-stack** em `project-analysis.md`: Python, Node/TS, Go, Java, Ruby, PHP e .NET; Flask, FastAPI, Django, Express, Fastify, Nest, Koa, Gin e Spring.
3. **Estrutura-alvo por stack** em `mvc-guidelines.md`: Flask monolítico, Flask com camadas parciais, Express, além de um mapeamento para FastAPI, Django, NestJS e Spring.
4. **Playbook bilíngue**: cada padrão tem exemplos em Python e JavaScript.
5. **Prova prática**: a mesma pasta da skill, byte a byte (verificado com `diff -r`), foi usada nos 3 projetos, em 2 linguagens e com 2 níveis de organização.

### Desafios encontrados e como resolvi (iterações)

| # | Desafio | Solução (o que mudou na skill) |
|---|---|---|
| 1 | O grep `print\(` do catálogo gerava falso positivo em `Blueprint(` | Padrão trocado por `\bprint\(`, com nota explicativa (commit `fix(skill)`). |
| 2 | Na validação do Node, `npm start` cria um processo filho; matar o PID do npm deixou um servidor órfão na porta 3000, e o teste seguinte bateu no servidor errado | A Fase 3.3 passou a exigir `setsid` + `kill -- -PGID` e a confirmação de porta livre (iteração 2). |
| 3 | Sem uma referência objetiva, "os endpoints continuam respondendo" era subjetivo | Passo obrigatório de **captura de baseline** antes de editar, com comparação de status e corpo depois (iteração 2). |
| 4 | Proteger endpoints administrativos poderia "quebrar" o contrato | Regra explícita: token via config, comparação em tempo constante, **fail-closed**, registro como mudança de contrato e atualização de `api.http`/README. |
| 5 | Migrar hashes de senha quebraria o login de bancos já existentes | O playbook P-05 inclui **migração transparente** (texto puro/MD5 aceito uma única vez e regravado com hash forte), testada nos projetos 1 e 3. |
| 6 | `print` em `seed.py` não é um problema | O catálogo AP-22 agora declara que `print` em scripts de CLI não é finding. |
| 7 | `Query.get` e `datetime.utcnow` não podem ser trocados "às cegas" (colunas `DateTime` *naive*) | O playbook P-20 define o helper `utcnow()` que mantém o valor sem tzinfo, compatível com os dados existentes. |

---

## C) Resultados

### Resumo das auditorias (Fase 2)

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total | APIs deprecated |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | 6 | 5 | 5 | 4 | **20** | nenhuma (Flask 3.1 / sqlite3) |
| 2 — ecommerce-api-legacy | 5 | 5 | 3 | 4 | **17** | nenhuma (Express 4 / Node 22) |
| 3 — task-manager-api | 3 | 4 | 5 | 5 | **17** | `Query.get()` ×16, `datetime.utcnow()` ×22 |

Todos os problemas da análise manual (seção A) aparecem nos relatórios, ou seja, bem mais que os 5 exigidos por projeto.

### Saída da Fase 1 em cada projeto

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.10 (runtime local)
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, pedidos, usuários, relatórios de vendas)
Architecture:  Monolítica com separação nominal — app.py tem rotas e SQL admin; models.py mistura SQL e regra de negócio
Source files:  4 files analyzed (~780 lines)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Database:      SQLite (loja.db) via sqlite3 cru
Entry point:   app.py (python app.py, porta 5000)
Endpoints:     20 routes mapped
================================
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js 22, runtime local)
Framework:     Express ^4.18.2
Dependencies:  sqlite3 ^5.1.6
Domain:        LMS (plataforma de cursos) com fluxo de checkout/pagamento, matrículas e relatório financeiro
Architecture:  Monolítica sem camadas — app.js delega tudo à God Class AppManager
Source files:  3 files analyzed (~180 lines)
DB tables:     users, courses, enrollments, payments, audit_logs
Database:      SQLite em memória via sqlite3 (callbacks)
Entry point:   src/app.js (npm start, porta 3000)
Endpoints:     3 routes mapped
================================
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.10 (runtime local)
Framework:     Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1 (sem uso), requests 2.31.0 (sem uso), python-dotenv 1.0.0 (sem uso)
Domain:        Task Manager (tarefas, usuários, categorias, relatórios de produtividade)
Architecture:  Camadas parciais — models/routes/services/utils existem, mas sem controllers; regras e queries nas rotas
Source files:  15 files analyzed (~1160 lines)
DB tables:     tasks, users, categories
Database:      SQLite (instance/tasks.db) via ORM Flask-SQLAlchemy
Entry point:   app.py (python seed.py && python app.py, porta 5000)
Endpoints:     22 routes mapped
================================
```

### Estrutura antes/depois

**Projeto 1 — code-smells-project**

```
ANTES                         DEPOIS
app.py        (config+rotas+  app.py                     # entry point
               SQL admin)     src/
controllers.py (HTTP+regras)  ├── app.py                 # composition root (create_app)
models.py     (SQL+regras+    ├── config/settings.py     # env vars
               formatação)    ├── constants.py · errors.py · database.py (conexão por request + schema/seed)
database.py   (singleton      ├── models/      produto_model, usuario_model, pedido_model, sistema_model
               global + seed) ├── controllers/ produto, usuario, pedido, relatorio, sistema + validators
                              ├── views/       produto_routes, usuario_routes, pedido_routes, relatorio_routes, sistema_routes
                              ├── services/    notification_service
                              └── middlewares/ error_handler, auth (X-Admin-Token)
```

**Projeto 2 — ecommerce-api-legacy**

```
ANTES                         DEPOIS
src/app.js                    src/server.js              # entry point (npm start)
src/AppManager.js (God Class) src/app.js                 # composition root (createApp)
src/utils.js (config+cache+   ├── config/      index.js (env), logger.js
              "crypto")       ├── database/    connection.js (Promise + fila + transação), schema.js
                              ├── models/      userModel, courseModel, enrollmentModel, auditLogModel
                              ├── controllers/ checkoutController, reportController, userController
                              ├── views/       checkoutRoutes, adminRoutes, userRoutes
                              ├── services/    paymentGateway, passwordHasher (scrypt), cache (limitado)
                              ├── middlewares/ errorHandler, asyncHandler, requireAdmin
                              └── errors/AppError.js · constants.js
```

**Projeto 3 — task-manager-api**

```
ANTES                         DEPOIS
app.py (config hardcoded)     app.py                     # entry point
database.py                   seed.py                    # usa create_app()
models/  task, user, category src/
routes/  task, user, report   ├── app.py                 # composition root (create_app)
         (rotas gordas;       ├── config/settings.py     # env + .env (python-dotenv)
          categorias em       ├── extensions.py · errors.py · constants.py · utils/time.py
          report_routes)      ├── models/      task, user, category   (reaproveitados via git mv)
services/notification (morto) ├── controllers/ task, user, report, category + validators   (NOVA camada)
utils/helpers.py (morto)      ├── views/       task, user, report, category, system      (Blueprints finos)
                              ├── services/    notification_service (config injetada), token_service
                              └── middlewares/ error_handler
```

### Checklist de validação

| Item | P1 code-smells | P2 ecommerce-legacy | P3 task-manager |
|---|:-:|:-:|:-:|
| **Fase 1** — Linguagem detectada corretamente | ✅ | ✅ | ✅ |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express ^4.18.2 | ✅ Flask 3.0.0 |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS + checkout | ✅ Task Manager |
| Nº de arquivos condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Findings ordenados CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 20 | ✅ 17 | ✅ 17 |
| Detecção de APIs deprecated (se aplicável) | ✅ declarado "none" | ✅ declarado "none" | ✅ 2 APIs (38 ocorrências) |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3** — Estrutura segue MVC | ✅ | ✅ | ✅ |
| Config extraída (sem hardcoded) + `.env.example` | ✅ | ✅ | ✅ |
| Models abstraem os dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ | ✅ | ✅ |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `app.py` | ✅ `src/server.js` | ✅ `app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem corretamente | ✅ 20 rotas, 28/28 requisições | ✅ 3 rotas, 7/7 requisições | ✅ 22 rotas, 35/35 requisições |

### Logs da validação (aplicações rodando após a refatoração)

Cada aplicação refatorada subiu com o comando oficial. Depois, a **mesma bateria de requisições** foi enviada à versão original (branch `main`) e à refatorada, rodando lado a lado, e os JSON foram comparados campo a campo, ignorando timestamps/tokens e os campos sensíveis removidos de propósito:

```
### Projeto 3 (task-manager-api)
== 35 idênticos, 0 diferentes

### Projeto 1 (code-smells-project)
DIFF POST /login            ← payload de SQL injection {"email": "' OR '1'='1", ...}
   original: 200 {"dados": {"email": "admin@loja.com", "id": 1, "nome": "Admin", "tipo": "admin"}, ...}
   refactor: 401 {"erro": "Email ou senha inválidos", "sucesso": false}
== 27 idênticos, 1 diferentes

### Projeto 2 (ecommerce-api-legacy)
DIFF DELETE /api/users/1
   original: 200 "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."
   refactor: 200 "Usuário deletado, junto com suas matrículas e pagamentos."
DIFF GET /api/admin/financial-report   ← sem o aluno órfão "Unknown"
== 5 idênticos, 2 diferentes
```

As únicas diferenças são as **correções intencionais** de segurança e integridade. Trechos dos logs de boot:

```
# code-smells-project  (python app.py)
WARNING src.app: SECRET_KEY não definida; usando chave aleatória (sessões não sobrevivem a reinícios).
WARNING src.database: SEED_ADMIN_PASSWORD não definida: usuário admin criado com senha aleatória.
INFO __main__: Servidor iniciado em http://127.0.0.1:5000
 * Debug mode: off
INFO src.services.notification_service: Notificação: pedido 1 criado para usuário 2

# ecommerce-api-legacy  (npm start)
[2026-10-26T12:46:09.323Z] INFO LMS API rodando na porta 3000
[2026-10-26T12:46:09.708Z] INFO Cobrança de 497 no cartão final 4444: PAID      ← antes: número completo + chave do gateway
[2026-10-26T12:46:09.829Z] INFO Usuário 1 removido com matrículas e pagamentos

# task-manager-api  (python seed.py && python -W always app.py)
Seed concluído com sucesso!  3 usuários / 4 categorias / 10 tasks
 * Debug mode: off                                                             ← nenhum LegacyAPIWarning/DeprecationWarning
INFO src.controllers.task_controller: Task criada: 11
INFO src.services.notification_service: E-mail não enviado (SMTP não configurado): Nova task atribuída: Nova task
```

Testes adicionais executados:

- **P1**: rotas `/admin/*` → 403 sem token; com token, `SELECT` funciona e `DELETE`/`SELECT 1; DELETE ...` são rejeitados (conexão SQLite em modo somente leitura). Um banco legado com senhas em texto puro faz login normalmente e a senha é regravada como `scrypt:...`. Cancelar um pedido agora devolve o estoque.
- **P2**: 20 checkouts **concorrentes** → 20× 200 e receita consistente (10967 = 11 × 997; 4970 = 10 × 497), o que valida a fila de transações. JSON malformado → 400; id inexistente → 404.
- **P3**: banco legado com MD5 → login 200 e hash migrado para `scrypt`. `priority: "alta"`, `title: null` e `?priority=x` → 400 (antes: 500). Excluir uma categoria deixa 0 tasks com FK órfã.

### Execução independente da skill via CLI (`claude -p "/refactor-arch"`)

Depois da iteração final, rodei a skill pelo comando real do Claude Code em **cópias limpas dos 3 projetos originais** (branch `main`), em modo headless e somente leitura (`--disallowedTools "Edit,Write,NotebookEdit"`), para confirmar que as Fases 1 e 2 funcionam sem ajuda do autor. Os logs completos estão em [`reports/headless-runs/`](reports/headless-runs/).

| Projeto | Stack detectada | Findings (C/H/M/L) | APIs deprecated | Parou na confirmação? | Arquivos modificados |
|---|---|---|---|---|---|
| P1 | Python 3.10 + Flask 3.1.1 | 21 (6/5/5/5) | none detected | ✅ `Proceed with refactoring (Phase 3)? [y/n]` | 0 (`git status` limpo) |
| P2 | Node.js 22 + Express 4 | 18 (5/5/4/4) | none detected | ✅ | 0 |
| P3 | Python 3.10 + Flask 3.0.0 | 19 (5/3/6/5) | `Query.get` (×16), `datetime.utcnow` | ✅ | 0 |

As contagens variam em ±2 em relação aos relatórios oficiais (só no agrupamento e na severidade de findings limítrofes). O resultado é estável: os mesmos CRITICAL/HIGH aparecem em todas as execuções.

### Mudanças de contrato (todas justificadas por segurança/integridade)

| Projeto | Mudança |
|---|---|
| P1 | `senha` removida de `/usuarios`; `secret_key`/`debug`/`db_path` removidos de `/health`; `/admin/*` exigem `X-Admin-Token` (bloqueadas sem `ADMIN_TOKEN`); `/admin/query` aceita só um `SELECT`; `PUT /pedidos/<id>/status` com id inexistente → 404; erros 500 não vazam `str(e)`; bind padrão `127.0.0.1` (`APP_HOST=0.0.0.0` para containers). |
| P2 | `GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem `X-Admin-Token`; o DELETE remove matrículas/pagamentos e responde 404 para id inexistente; checkout valida o formato de e-mail/cartão (400). |
| P3 | `password` removido de todas as respostas; token de login passa a ser assinado (`itsdangerous`); mensagem de data inválida unificada; validações que geravam 500 agora geram 400. |

### Observações sobre o comportamento em stacks diferentes

- **Monólito Python (P1)**: houve a maior transformação. O nome `controllers.py` existia, mas não cumpria o papel; a skill reclassificou a arquitetura como "separação nominal" e criou as camadas do zero. O ganho mais visível foi na segurança (SQLi, backdoor admin, senhas).
- **Node/Express (P2)**: o mesmo catálogo funcionou, mas os anti-patterns dominantes foram outros (callback hell, estado global, falta de transação). O playbook P-10 (Promises + async/await) e uma fila de operações sobre a conexão única do SQLite foram essenciais para manter a consistência sob concorrência.
- **Python com camadas parciais (P3)**: a skill **não reescreveu** o que já estava certo. Os models ORM foram mantidos (com `git mv`, preservando o histórico) e o trabalho se concentrou em criar a camada de controllers que faltava, centralizar validação e erros, e substituir as APIs deprecated. É o único projeto com APIs deprecated detectadas, o que mostra que a checagem por versão funciona e não gera falsos positivos nos outros dois.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude --version`; testado com 2.1.310).
- Python 3.10+ (projetos 1 e 3) e Node.js 18+ (projeto 2; testado com 22).
- `curl` para validar os endpoints.

### Executar a skill

A skill fica em `.claude/skills/refactor-arch/` dentro de cada projeto, e o Claude Code a descobre automaticamente:

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

A skill imprime a Fase 1, depois o relatório da Fase 2, e **para** em `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar e validar. Para rodar só a auditoria sem risco de alteração:

```bash
claude -p "/refactor-arch" --disallowedTools "Edit,Write,NotebookEdit"
```

> Para reexecutar a skill sobre o código **original**, use a branch `main` (`git checkout main`), que tem os projetos antes da refatoração. Esta branch (`dev`) já contém o resultado da Fase 3.

### Validar que a refatoração funcionou

```bash
# Projeto 1 — http://127.0.0.1:5000
cd code-smells-project && pip install -r requirements.txt
ADMIN_TOKEN=meu-token SEED_ADMIN_PASSWORD=admin123 python app.py
curl -s localhost:5000/health
curl -s localhost:5000/produtos
curl -s -H 'Content-Type: application/json' -d '{"email":"joao@email.com","senha":"123456"}' localhost:5000/login
curl -s -X POST -H 'X-Admin-Token: meu-token' -H 'Content-Type: application/json' \
     -d '{"sql":"SELECT id, nome FROM produtos LIMIT 3"}' localhost:5000/admin/query

# Projeto 2 — http://localhost:3000 (ou use api.http)
cd ecommerce-api-legacy && npm install
ADMIN_TOKEN=meu-token npm start
curl -s -H 'Content-Type: application/json' \
     -d '{"usr":"Gui","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}' localhost:3000/api/checkout
curl -s -H 'X-Admin-Token: meu-token' localhost:3000/api/admin/financial-report

# Projeto 3 — http://127.0.0.1:5000
cd task-manager-api && pip install -r requirements.txt
python seed.py && python app.py
curl -s localhost:5000/tasks
curl -s localhost:5000/reports/summary
curl -s -H 'Content-Type: application/json' -d '{"email":"joao@email.com","password":"1234"}' localhost:5000/login
```

Os dados de exemplo (seed) usam senhas de demonstração: `joao@email.com`/`123456` e `maria@email.com`/`senha123` no projeto 1; `joao@email.com`/`1234` no projeto 3. Todas são gravadas com hash.

---

<details>
<summary>Enunciado original do desafio (resumo)</summary>

Criar uma Skill capaz de: analisar uma codebase (linguagem, framework, arquitetura); identificar anti-patterns classificados por severidade com arquivo e linha; gerar um relatório de auditoria; refatorar para MVC; e validar que a aplicação continua funcionando. Ela deve ser agnóstica de tecnologia, ter catálogo com ≥ 8 anti-patterns (incluindo APIs deprecated), playbook com ≥ 8 transformações antes/depois, pausar antes de modificar arquivos e validar boot + endpoints. Projetos-alvo: 2 Python/Flask e 1 Node.js/Express. Referências: [Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code/skills), [The Complete Guide to Building Skills for Claude](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf), [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills).
</details>
