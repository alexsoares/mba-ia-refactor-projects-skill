================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
Files:   15 analyzed | ~1160 lines of code
Date:    2026-10-26

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 5 | LOW: 5

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP-01 | SECRET_KEY e senha SMTP hardcoded | app.py:13 |
| 2 | CRITICAL | AP-05 | Senhas com MD5 sem salt | models/user.py:27-32 |
| 3 | CRITICAL | AP-06 | Hash da senha devolvido nas respostas (inclusive no login) | models/user.py:21 |
| 4 | HIGH | AP-07 | Rotas gordas: validação, regras, queries e serialização nos handlers | routes/task_routes.py:11-63 |
| 5 | HIGH | AP-08 | Sem app factory/DI: rotas acessam ORM direto, serviço cria a própria config | app.py:9-31 |
| 6 | HIGH | AP-10 | Exclusão de categoria deixa tasks com FK órfã | routes/report_routes.py:211-223 |
| 7 | HIGH | AP-12 | Token de autenticação falso e debug ligado | routes/user_routes.py:210 |
| 8 | MEDIUM | AP-13 | Queries N+1 e contagens repetidas | routes/task_routes.py:41-57 |
| 9 | MEDIUM | AP-14 | Validação inconsistente (TypeError → 500) e validadores existentes não usados | routes/task_routes.py:113 |
| 10 | MEDIUM | AP-15 | Lógica de "atrasada", serialização e listas de status duplicadas | routes/task_routes.py:30-39 |
| 11 | MEDIUM | AP-16 | `except:` nu em 12 pontos e nenhum error handler central | routes/task_routes.py:62 |
| 12 | MEDIUM | AP-17 | APIs deprecated: `Query.get()` e `datetime.utcnow()` | routes/task_routes.py:42 (+15) |
| 13 | LOW | AP-19 | Magic numbers/strings (prioridades, tamanhos, cores) | routes/task_routes.py:96-114 |
| 14 | LOW | AP-20 | Nomenclatura ruim (`t`, `u`, `c`, `d`, `p1..p5`) | routes/report_routes.py:24-28 |
| 15 | LOW | AP-21 | Imports, funções, serviço e dependências não utilizados | utils/helpers.py:1-116 |
| 16 | LOW | AP-22 | `print` como log | routes/task_routes.py:149 |
| 17 | LOW | AP-23 | Condicionais verbosas (`if: return True else: return False`, `type(x) == list`) | models/task.py:38-60 |

## Findings

### #1 [CRITICAL] Hardcoded Credentials (AP-01)
File: app.py:13
File: services/notification_service.py:7-10
File: app.py:11
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'`; `NotificationService` fixa `email_user = 'taskmanager@gmail.com'` e `email_password = 'senha123'`; URI do banco fixa.
Impact: Chave de assinatura e senha de e-mail expostas no repositório; sem configuração por ambiente (o `python-dotenv` declarado no requirements nunca é usado).
Recommendation: `src/config/settings.py` lendo variáveis de ambiente (com `load_dotenv`), `.env.example` sem valores reais e serviço de notificação recebendo a config por injeção (Playbook P-01).

### #2 [CRITICAL] Hash de senha inseguro (AP-05)
File: models/user.py:27-32
Description: `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()` sem salt e `check_password` compara com `==`.
Impact: MD5 sem salt é quebrado por rainbow tables em segundos; senhas iguais geram hashes iguais (ex.: `81dc9bdb52d04dc20036dbd8313ed055` = "1234", visível no baseline).
Recommendation: `werkzeug.security.generate_password_hash`/`check_password_hash`, com migração transparente de hashes MD5 legados no login (Playbook P-05).

### #3 [CRITICAL] Exposição de dados sensíveis (AP-06)
File: models/user.py:21
File: routes/user_routes.py:33
File: routes/user_routes.py:85
File: routes/user_routes.py:129
File: routes/user_routes.py:209
Description: `User.to_dict()` inclui `'password': self.password`, e esse dict é devolvido em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e na resposta do `POST /login`.
Impact: Qualquer cliente obtém os hashes MD5 (triviais de reverter, ver #2) de qualquer usuário.
Recommendation: Serializer sem o campo de senha (Playbook P-06).

### #4 [HIGH] Rotas gordas — regra de negócio na camada HTTP (AP-07)
File: routes/task_routes.py:11-63
File: routes/task_routes.py:85-154
File: routes/task_routes.py:156-223
File: routes/user_routes.py:42-90
File: routes/report_routes.py:12-101
File: routes/report_routes.py:157-223
Description: Os handlers de Blueprint fazem validação, consultas ORM, regras (atraso, contagens, estatísticas de produtividade), montagem manual de dicts e commits; `report_routes.py` ainda abriga o CRUD de categorias (responsabilidade fora do lugar). Não existe camada de controller.
Impact: Regras só testáveis com o servidor HTTP; arquivos de rota com 200–300 linhas; mudanças de regra exigem tocar na camada HTTP.
Recommendation: Extrair controllers por recurso (tasks, users, reports, categories), deixando as views com handlers de poucas linhas (Playbook P-04, P-03).

### #5 [HIGH] Acoplamento forte sem injeção de dependência (AP-08)
File: app.py:9-31
File: seed.py:2
File: services/notification_service.py:5-10
File: routes/task_routes.py:2-5
Description: A app é criada no import do módulo (sem `create_app`), `db.create_all()` roda como efeito colateral do import, `seed.py` importa `app` diretamente; rotas importam `db` e models concretos; `NotificationService` monta sua própria configuração no construtor.
Impact: Impossível criar instâncias isoladas para teste (ex.: banco em memória); qualquer import de `app` cria tabelas no banco real.
Recommendation: App factory como composition root, controllers recebendo sessão/serviços por construtor (Playbook P-07).

### #6 [HIGH] Integridade referencial — exclusão sem tratar dependentes (AP-10)
File: routes/report_routes.py:211-223
Description: `DELETE /categories/<id>` apaga a categoria sem tratar as tasks que a referenciam (o SQLite não aplica FKs por padrão), deixando `tasks.category_id` apontando para um registro inexistente.
Impact: Dados inconsistentes: tasks com categoria fantasma e relatórios por categoria incorretos.
Recommendation: Na mesma transação, desassociar (`category_id = NULL`) as tasks da categoria antes de excluí-la (Playbook P-09).

### #7 [HIGH] Autenticação falsa e configuração insegura (AP-12)
File: routes/user_routes.py:210
File: app.py:34
Description: O login devolve `'fake-jwt-token-' + str(user.id)` — token previsível, não assinado; o servidor sobe com `debug=True` e `host='0.0.0.0'` fixos.
Impact: Qualquer um pode "fabricar" o token de qualquer usuário; o debugger Werkzeug exposto permite execução remota de código.
Recommendation: Token assinado com `itsdangerous` (dependência do Flask) usando a `SECRET_KEY`; debug/host via config (Playbook P-12, P-01).

### #8 [MEDIUM] Queries N+1 e contagens repetidas (AP-13)
File: routes/task_routes.py:41-57
File: routes/user_routes.py:22
File: routes/report_routes.py:53-68
File: routes/report_routes.py:159-164
File: routes/report_routes.py:15-28
File: routes/task_routes.py:275-279
Description: `GET /tasks` faz `User.query.get` e `Category.query.get` para cada task; `GET /users` carrega `u.tasks` (lazy) por usuário; o resumo faz uma query por usuário e 12 `count()` separados; `GET /categories` conta tasks por categoria em loop.
Impact: Número de queries cresce com o volume de dados (1 + 2N em `/tasks`).
Recommendation: `joinedload` para relacionamentos e agregações `GROUP BY` (Playbook P-13).

### #9 [MEDIUM] Validação inconsistente (AP-14)
File: routes/task_routes.py:113
File: routes/task_routes.py:166-170
File: routes/task_routes.py:182
File: routes/task_routes.py:261-264
File: routes/report_routes.py:196-197
File: routes/user_routes.py:102-103
File: utils/helpers.py:57-108
Description: `priority < 1` com valor string gera `TypeError` (500); `len(data['title'])` com `null` gera 500; `int(priority)` na busca com valor inválido gera 500; `update_category` usa `data` sem checar `None`; nome do usuário não é validado no update; cor da categoria não é validada (`is_valid_color` existe e não é usada); `process_task_data` implementa a validação de task mas nunca é chamada.
Impact: Erros de cliente viram 500 e as regras divergem entre criação e atualização.
Recommendation: Validadores centralizados por recurso reutilizados em create/update, preservando as mensagens atuais (Playbook P-14).

### #10 [MEDIUM] Código duplicado (AP-15)
File: routes/task_routes.py:30-39
File: routes/task_routes.py:71-80
File: routes/task_routes.py:283-287
File: routes/user_routes.py:171-180
File: routes/report_routes.py:34-36
File: routes/report_routes.py:132-135
File: routes/task_routes.py:17-28
File: routes/user_routes.py:61
Description: A regra "atrasada" é reimplementada em 6 lugares embora exista `Task.is_overdue()` (models/task.py:50-60); `get_tasks` remonta manualmente o dict de `Task.to_dict()`; a lista de status válidos aparece em 5 lugares; a regex de e-mail em 3.
Impact: Correções divergentes; alto custo de manutenção.
Recommendation: Regra no model, serializer único e constantes de domínio compartilhadas (Playbook P-15, P-06, P-17).

### #11 [MEDIUM] Tratamento de erro não centralizado (AP-16)
File: routes/task_routes.py:62
File: routes/task_routes.py:137
File: routes/task_routes.py:204
File: routes/task_routes.py:236
File: routes/user_routes.py:130
File: routes/user_routes.py:149
File: routes/report_routes.py:186
File: routes/report_routes.py:207
Description: 12 blocos `except:` nus (+ `report_routes.py:221`, `utils/helpers.py:46, 49, 88`), que capturam inclusive `KeyboardInterrupt`/`SystemExit` e escondem a causa; não há `errorhandler` registrado.
Impact: Falhas invisíveis no log e respostas de erro montadas à mão em cada rota.
Recommendation: Exceções de domínio + error handler central que registra a exceção (Playbook P-11).

### #12 [MEDIUM] APIs deprecated (AP-17)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227
File: routes/user_routes.py:29, 94, 136, 155
File: routes/report_routes.py:105, 192, 213
File: models/task.py:15-16
File: models/task.py:52
File: models/user.py:14
File: models/category.py:11
File: routes/report_routes.py:35, 42, 45, 71, 133
Description: `Model.query.get(id)` é API legada no SQLAlchemy 2.x (Flask-SQLAlchemy 3.1 emite `LegacyAPIWarning`); `datetime.utcnow()` é deprecated desde o Python 3.12 (usado também em `routes/task_routes.py:31, 72, 215, 285`, `routes/user_routes.py:172`, `utils/helpers.py:38`, `services/notification_service.py:35`, `seed.py:66-74`).
Impact: Warnings hoje e quebra em upgrades futuros do SQLAlchemy/Python.
Recommendation: `db.session.get(Model, id)` e helper `utcnow()` baseado em `datetime.now(timezone.utc)` (Playbook P-20).

### #13 [LOW] Magic numbers / strings (AP-19)
File: routes/task_routes.py:96-114
File: routes/task_routes.py:182
File: routes/report_routes.py:129
File: routes/user_routes.py:64
File: routes/report_routes.py:180
Description: Limites de título `3`/`200`, faixa de prioridade `1..5`, "alta prioridade" `<= 2`, senha mínima `4`, cor padrão `'#000000'` como literais — enquanto `utils/helpers.py:110-116` declara constantes equivalentes que ninguém usa.
Impact: Regras espalhadas e fáceis de divergir.
Recommendation: Constantes de domínio em um único módulo, efetivamente usadas (Playbook P-17).

### #14 [LOW] Nomenclatura ruim (AP-20)
File: routes/report_routes.py:24-28
File: routes/task_routes.py:16
File: routes/user_routes.py:14
File: models/category.py:14
Description: `p1`…`p5`, `t`, `u`, `c`, `cat`, `d` como nomes de variáveis em lógica não trivial.
Impact: Leitura mais lenta e propensa a erro.
Recommendation: Nomes expressivos (Playbook P-18).

### #15 [LOW] Código morto e dependências sem uso (AP-21)
File: app.py:7
File: routes/task_routes.py:7
File: routes/user_routes.py:6
File: routes/report_routes.py:7-8
File: models/task.py:3
File: utils/helpers.py:3-7
File: utils/helpers.py:9-108
File: services/notification_service.py:1-48
Description: Imports não usados (`os, sys, json, time, hashlib, math`); quase todas as funções de `helpers.py` nunca são chamadas; `NotificationService` nunca é instanciado; `validate_status`/`validate_priority` do model não são usados; `marshmallow` e `requests` estão no requirements sem nenhum import.
Impact: Ruído, superfície de ataque e falsa sensação de que validações existem.
Recommendation: Remover ou passar a usar de fato (Playbook P-18).

### #16 [LOW] `print` como log (AP-22)
File: routes/task_routes.py:149
File: routes/task_routes.py:153
File: routes/task_routes.py:219
File: routes/task_routes.py:234
File: routes/user_routes.py:83
File: routes/user_routes.py:89
File: routes/user_routes.py:147
File: services/notification_service.py:21-24
Description: Eventos e erros registrados com `print`.
Impact: Sem níveis, sem integração com o logger do Flask.
Recommendation: `logging` (Playbook P-19).

### #17 [LOW] Condicionais verbosas (AP-23)
File: models/task.py:38-60
File: models/user.py:34-38
File: routes/task_routes.py:141
File: routes/task_routes.py:210
Description: `if x: return True else: return False`, três `if` aninhados em `is_overdue`, `p >= 1 and p <= 5`, `type(tags) == list`.
Impact: Código mais longo e menos legível.
Recommendation: Expressões booleanas diretas, `isinstance`, comparação encadeada (Playbook P-15, P-18).

## Deprecated APIs
- routes/task_routes.py:42 (+15 ocorrências em routes/) — `Model.query.get(id)` → `db.session.get(Model, id)` (finding #12)
- models/task.py:15-16, models/user.py:14, models/category.py:11 (+ rotas, helpers, seed) — `datetime.utcnow` → `datetime.now(timezone.utc)` (finding #12)

## Notes
- Arquitetura atual: camadas parciais — já existem `models/` (ORM), `routes/` (Blueprints), `services/` e `utils/`, mas falta a camada de controller, a configuração está no entry point e o tratamento de erro é manual em cada rota.
- Pontos positivos a preservar: models ORM com relacionamentos, Blueprints por recurso, queries via ORM (sem SQL injection).

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
