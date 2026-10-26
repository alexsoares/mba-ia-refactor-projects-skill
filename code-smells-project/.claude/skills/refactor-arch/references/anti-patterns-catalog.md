# Catálogo de Anti-Patterns (Fase 2)

Cada anti-pattern tem: **ID**, **severidade padrão**, **sinais de detecção** (o que procurar, com padrões de grep),
**por que é um problema** e o **padrão do playbook** que o corrige (`references/refactoring-playbook.md`).

## Escala de severidade

| Severidade | Critério |
|---|---|
| **CRITICAL** | Falha grave de arquitetura ou segurança: impede o funcionamento correto, expõe dados sensíveis (credenciais hardcoded, SQL Injection, senha em texto puro) ou viola completamente a separação de responsabilidades (God Class com banco + regra + roteamento). |
| **HIGH** | Forte violação de MVC/SOLID que dificulta muito manutenção e testes: regra de negócio pesada em controller/rota, acoplamento sem injeção de dependência, estado global mutável, operações multi-etapa sem transação. |
| **MEDIUM** | Padronização, duplicação ou performance moderada: N+1, validação ausente/duplicada, tratamento de erro inconsistente, APIs deprecated, middleware inadequado. |
| **LOW** | Legibilidade: nomes ruins, magic numbers/strings, imports e código morto, `print`/`console.log` como log. |

**Ajuste de severidade**: a severidade padrão pode subir um nível quando o problema está num caminho crítico
(autenticação, pagamento, exclusão de dados) ou descer um nível quando o impacto é comprovadamente restrito
(ex.: código morto). Justifique sempre que ajustar.

## Índice

| ID | Anti-pattern | Severidade |
|---|---|---|
| AP-01 | Credenciais / segredos hardcoded | CRITICAL |
| AP-02 | SQL Injection (SQL montado por concatenação/interpolação) | CRITICAL |
| AP-03 | God Class / God File / God Method | CRITICAL |
| AP-04 | Endpoint administrativo ou destrutivo sem autenticação | CRITICAL |
| AP-05 | Armazenamento ou hash de senha inseguro | CRITICAL |
| AP-06 | Exposição de dados sensíveis (resposta, log, health check) | CRITICAL / HIGH |
| AP-07 | Regra de negócio na camada de rota/controller HTTP (Fat Controller) | HIGH |
| AP-08 | Acoplamento forte sem injeção de dependência | HIGH |
| AP-09 | Estado global mutável | HIGH |
| AP-10 | Escrita multi-etapa sem transação / integridade referencial quebrada | HIGH |
| AP-11 | Callback hell / fluxo assíncrono aninhado | HIGH |
| AP-12 | Configuração insegura de execução (debug em produção, autenticação falsa) | HIGH |
| AP-13 | Queries N+1 / consultas repetidas | MEDIUM |
| AP-14 | Validação de entrada ausente, inconsistente ou duplicada | MEDIUM |
| AP-15 | Código duplicado (serialização, regras repetidas) | MEDIUM |
| AP-16 | Tratamento de erro não centralizado / exceção engolida / vazamento de `str(e)` | MEDIUM |
| AP-17 | Uso de APIs deprecated | MEDIUM |
| AP-18 | Efeitos colaterais acoplados ao fluxo da requisição (notificações, e-mail) | MEDIUM |
| AP-19 | Magic numbers / magic strings | LOW |
| AP-20 | Nomenclatura ruim | LOW |
| AP-21 | Imports não utilizados / código morto / dependência declarada sem uso | LOW |
| AP-22 | `print` / `console.log` no lugar de logger estruturado | LOW |
| AP-23 | Lógica condicional verbosa / aninhamento excessivo | LOW |

---

## AP-01 — Credenciais / segredos hardcoded — **CRITICAL**

**Sinais de detecção**
- Literais atribuídos a chaves com nome sensível: `SECRET_KEY`, `password`, `pass`, `pwd`, `senha`, `token`, `api_key`, `apiKey`, `secret`, `gatewayKey`, `smtp`, `dbPass`.
- Prefixos de chaves reais: `pk_live_`, `sk_live_`, `AKIA`, `ghp_`, `xox`.
- Strings de conexão com usuário:senha (`postgres://user:pass@`).
- grep: `grep -rnEi "(secret|passw|pass|pwd|senha|token|api_?key|gateway).{0,20}[:=] *['\"][^'\"]{3,}" --include=*.{py,js,ts}`

**Por que importa**: qualquer pessoa com acesso ao repositório (ou ao histórico git) obtém as credenciais; impossível rotacionar por ambiente.
**Correção**: Playbook **P-01** (config por variável de ambiente).

## AP-02 — SQL Injection — **CRITICAL**

**Sinais de detecção**
- SQL montado com `+`, f-string, `%`, `.format()` ou template literal contendo dados de entrada:
  - Python: `execute("... " + x`, `execute(f"... {x}")`, `"... '%s'" % x`
  - JS: `` db.run(`... ${x}`) ``, `"... '" + x + "'"`
- grep: `grep -rnE "(execute|run|get|all|query)\(\s*(f?[\"'].*(\+|\{)|\`.*\\$\{)" ` e `grep -rnE "(SELECT|INSERT|UPDATE|DELETE).*[\"'] *\+"`
- Cláusulas `LIKE '%" + termo + "%'` em buscas.
- Endpoint que executa SQL arbitrário recebido do cliente (também AP-04).

**Por que importa**: permite ler/alterar/apagar o banco e burlar login (`' OR '1'='1`).
**Correção**: Playbook **P-02** (queries parametrizadas / ORM).

## AP-03 — God Class / God File / God Method — **CRITICAL**

**Sinais de detecção**
- Um arquivo/classe que acumula 4+ responsabilidades do mapa da Fase 1 (`routing`, `business`, `data-access`, `config`, `bootstrap`...).
- Classe "Manager/Handler/Utils" que cria conexão com banco, cria schema, faz seed **e** registra rotas.
- Arquivo de "models" contendo SQL de vários domínios + regra de negócio (cálculo de desconto, verificação de estoque) + formatação de resposta.
- Método com > 50 linhas ou que trata vários domínios.

**Por que importa**: impossível testar em isolamento; qualquer alteração tem raio de impacto global.
**Correção**: Playbook **P-03** (decomposição em camadas MVC) + P-04.

## AP-04 — Endpoint administrativo/destrutivo sem autenticação — **CRITICAL**

**Sinais de detecção**
- Rotas com `admin`, `reset`, `query`, `exec`, `debug`, `delete` sem verificação de identidade/permissão.
- Handler que executa SQL vindo do corpo da requisição (`cursor.execute(dados["sql"])`).
- Handler que apaga tabelas inteiras (`DELETE FROM x` sem `WHERE`).

**Por que importa**: qualquer cliente pode destruir ou exfiltrar todos os dados.
**Correção**: Playbook **P-12** (middleware de autorização) — e remover execução de SQL arbitrário ou restringi-la.

## AP-05 — Armazenamento ou hash de senha inseguro — **CRITICAL**

**Sinais de detecção**
- Senha persistida como recebida (`INSERT ... senha` com o valor do request).
- Hash rápido/quebrado: `hashlib.md5`, `hashlib.sha1`, `crypto.createHash('md5')`, base64 como "criptografia", loops caseiros.
- Comparação de senha em SQL (`WHERE email = ? AND senha = ?`).
- grep: `grep -rnE "md5|sha1|base64|badCrypto|senha *=|password *=" `

**Por que importa**: vazamento do banco expõe senhas de todos os usuários (reuso em outros sistemas).
**Correção**: Playbook **P-05** (hash adaptativo com salt: `werkzeug.security`, `bcrypt`, `crypto.scrypt`).

## AP-06 — Exposição de dados sensíveis — **CRITICAL** (segredos/senhas/cartão) / **HIGH** (dados internos)

**Sinais de detecção**
- Serialização que inclui `senha`/`password`/hash (`to_dict()` com `'password'`, `SELECT *` devolvido direto).
- Health check / endpoint de diagnóstico retornando `secret_key`, `db_path`, flags de debug.
- Log de dados de cartão, senha ou chave: `console.log(... cc ...)`, `print("... " + senha)`.
- Mensagens de erro com `str(e)` / stack trace devolvidas ao cliente (ver também AP-16).

**Correção**: Playbook **P-06** (DTO/serializer explícito sem campos sensíveis) e P-11.

## AP-07 — Regra de negócio na camada HTTP (Fat Controller / Fat Route) — **HIGH**

**Sinais de detecção**
- Handler de rota que, além de ler o request, faz: cálculo (totais, descontos, estatísticas), loops sobre entidades, decisões de status, criação de várias entidades, verificação de estoque/pagamento.
- Handler com mais de ~30 linhas ou mais de 2 níveis de `if` aninhado.
- Rotas que consultam o ORM/SQL diretamente (`Task.query...`, `db.session...`, `db.get(...)` dentro do handler).

**Por que importa**: regra presa ao framework HTTP não pode ser reutilizada nem testada sem subir o servidor.
**Correção**: Playbook **P-04** (extrair controller/serviço; rota fina).

## AP-08 — Acoplamento forte sem injeção de dependência — **HIGH**

**Sinais de detecção**
- Funções/classes que chamam `get_db()` global, `new sqlite3.Database(...)`, `NotificationService()` ou importam módulos concretos dentro da lógica.
- Classe que instancia suas próprias dependências no construtor sem permitir substituição.
- Import circular resolvido com import dentro de função.

**Por que importa**: impossível substituir banco/serviços por fakes em testes; troca de infraestrutura exige editar regra de negócio.
**Correção**: Playbook **P-07** (injeção de dependência via construtor/factory + composition root).

## AP-09 — Estado global mutável — **HIGH**

**Sinais de detecção**
- Python: variáveis de módulo reatribuídas com `global x`; listas/dicts de módulo usados como cache/armazenamento.
- JS: `let cache = {}` / `let total = 0` em escopo de módulo, exportados e mutados.
- Conexão de banco singleton global criada sob demanda (`db_connection = None` + `global`).
- Estado em memória por instância de serviço que deveria ser persistido (lista de notificações em atributo).

**Por que importa**: condições de corrida, vazamento de memória, comportamento dependente da ordem das requisições, testes interferindo entre si.
**Correção**: Playbook **P-07** / **P-08** (estado encapsulado e injetado; conexão gerenciada pelo ciclo de vida da app).

## AP-10 — Escrita multi-etapa sem transação / integridade referencial — **HIGH**

**Sinais de detecção**
- Sequência de `INSERT`/`UPDATE` relacionados (pedido + itens + estoque; matrícula + pagamento) sem `BEGIN/COMMIT/ROLLBACK` ou `session` única.
- `DELETE` de entidade-pai sem tratar filhas (comentários do tipo "ficaram sujos no banco", ausência de `ON DELETE CASCADE`).
- Verificação e escrita separadas sem lock (check de estoque e débito em passos distintos).

**Por que importa**: falha no meio deixa o banco inconsistente (pedido sem itens, pagamento sem matrícula, órfãos).
**Correção**: Playbook **P-09** (unidade de trabalho / transação).

## AP-11 — Callback hell / fluxo assíncrono aninhado — **HIGH**

**Sinais de detecção**
- 3+ níveis de callbacks aninhados (`db.get(..., (err, x) => { db.run(..., function(err) { ...`).
- Contadores manuais de pendências (`pending--; if (pending === 0) res.json(...)`).
- `const self = this` para acessar o contexto dentro de callbacks.
- Erros de callback ignorados (`(err) => { res.send(...) }` sem checar `err`).

**Por que importa**: fluxo ilegível, erros silenciosos, respostas duplicadas ou nunca enviadas.
**Correção**: Playbook **P-10** (promisificar + `async/await`).

## AP-12 — Configuração de execução insegura / autenticação falsa — **HIGH**

**Sinais de detecção**
- `debug=True` / `app.config["DEBUG"] = True` fixo (debugger Werkzeug permite execução remota de código).
- `host="0.0.0.0"` fixo junto com debug.
- Tokens "fake" previsíveis (`'fake-jwt-token-' + id`), autenticação que não verifica assinatura.
- CORS liberado para tudo (`CORS(app)` sem origens) em API com dados sensíveis (mencionar, severidade MEDIUM se isolado).

**Correção**: Playbook **P-01** (flags por ambiente) e **P-12** (token assinado / middleware).

## AP-13 — Queries N+1 / consultas repetidas — **MEDIUM**

**Sinais de detecção**
- Query dentro de `for`/`forEach`: `for row in rows: cursor.execute(...)`, `tasks.forEach(t => db.get(...))`, `User.query.get(t.user_id)` em loop.
- Acesso a relacionamento lazy em loop (`len(u.tasks)` para cada usuário).
- Vários `COUNT(*)` separados que poderiam ser um `GROUP BY`.
- Mesma linha buscada duas vezes no mesmo fluxo (busca produto para validar e de novo para inserir).

**Por que importa**: latência cresce linearmente com o volume de dados.
**Correção**: Playbook **P-13** (JOIN / eager loading / agregação).

## AP-14 — Validação ausente, inconsistente ou duplicada — **MEDIUM**

**Sinais de detecção**
- `request.get_json()` / `req.body` usado sem checar `None`/tipo (`dados.get(...)` quebra com 500 quando o corpo é vazio).
- Comparações numéricas com valores não convertidos (`if priority < 1` quando pode vir string → `TypeError` → 500).
- Regras de validação diferentes para criar e atualizar o mesmo recurso.
- Funções de validação existentes (ex.: `process_task_data`, `validate_email`) não usadas e reimplementadas inline.

**Correção**: Playbook **P-14** (validador/schema único por recurso).

## AP-15 — Código duplicado — **MEDIUM**

**Sinais de detecção**
- Mesmo bloco de conversão row→dict repetido em várias funções.
- Mesma regra (ex.: "está atrasada?", "lista de status válidos") reimplementada em vários arquivos, mesmo existindo um método no model.
- Funções quase idênticas que diferem apenas por um filtro (`get_pedidos_usuario` vs `get_todos_pedidos`).

**Correção**: Playbook **P-06** (serializer único) e **P-15** (regra no model / função compartilhada).

## AP-16 — Tratamento de erro não centralizado — **MEDIUM**

**Sinais de detecção**
- `try/except Exception` (ou `except:` nu) repetido em todo handler, retornando `str(e)` ao cliente.
- `except: pass` / erro engolido; callbacks Node que ignoram `err`.
- Respostas de erro com formatos diferentes entre endpoints.
- Ausência de error handler global (`@app.errorhandler`, middleware `(err, req, res, next)`).

**Correção**: Playbook **P-11** (exceções de domínio + error handler central).

## AP-17 — Uso de APIs deprecated — **MEDIUM**

Verifique **sempre**, considerando as versões detectadas na Fase 1. Recomende o equivalente moderno.

| Stack | API deprecated (sinal de grep) | Situação | Equivalente moderno |
|---|---|---|---|
| SQLAlchemy ≥ 2.0 / Flask-SQLAlchemy ≥ 3.0 | `Model.query.get(id)` (`\.query\.get\(`) | Legacy API (`LegacyAPIWarning`), removida no futuro | `db.session.get(Model, id)` |
| SQLAlchemy ≥ 2.0 | `Model.query.filter(...)` em código novo | Estilo 1.x legado | `db.session.execute(db.select(Model).where(...)).scalars()` |
| Python ≥ 3.12 | `datetime.utcnow()` / `datetime.utcfromtimestamp()` | Deprecated (`DeprecationWarning`) | `datetime.now(timezone.utc)` (se a coluna for naive: `.replace(tzinfo=None)`) |
| Python | `default=datetime.utcnow` em colunas ORM | Mesma deprecação acima | `default=utcnow` (helper com `datetime.now(timezone.utc)`) |
| Python | `hashlib.md5` para senhas | Inseguro (não é deprecated da linguagem, mas obsoleto para senha) | `werkzeug.security.generate_password_hash` / `bcrypt` / `argon2` |
| Flask ≥ 2.3 | `app.before_first_request`, `flask.json.JSONEncoder`, `app.json_encoder` | Removido no Flask 2.3/3.0 | `with app.app_context():` na factory; `app.json` provider |
| Flask | `FLASK_ENV` | Removido no Flask 2.3 | `FLASK_DEBUG` / config própria |
| Node.js | `new Buffer(x)` | Deprecated (DEP0005) | `Buffer.from(x)` / `Buffer.alloc(n)` |
| Node.js | `require('url').parse()` | Deprecated (legacy) | `new URL(input, base)` |
| Node.js | `crypto.createCipher` | Removido (DEP0106) | `crypto.createCipheriv` |
| Express 4 → 5 | `body-parser` separado, `req.param()`, `res.send(status)` , `app.del()` | Deprecated no Express 4, removidos no 5 | `express.json()`, `req.params`/`req.query`, `res.sendStatus()`, `app.delete()` |
| node-sqlite3 | API de callbacks aninhados | Não deprecated, mas obsoleta frente a Promises | wrapper com Promises (`util.promisify`) ou `node:sqlite` (Node ≥ 22.5, experimental) |
| JS | `var`, `arguments`, `substr()` | Obsoleto (`substr` é legacy no ECMAScript) | `let/const`, rest params, `slice()`/`substring()` |

Se nenhuma API deprecated for encontrada, escreva no relatório: `Deprecated APIs: none detected for <stack/versões>`.

## AP-18 — Efeitos colaterais acoplados à requisição — **MEDIUM**

**Sinais de detecção**
- Envio de e-mail/SMS/push (ou `print("ENVIANDO EMAIL...")` simulando) dentro do handler.
- Conexão SMTP síncrona aberta dentro do fluxo da requisição.
- Comentários/prints prometendo ações não executadas ("Devolver estoque" sem código que devolva).

**Correção**: Playbook **P-16** (serviço de notificação injetado, chamado pelo controller após o commit).

## AP-19 — Magic numbers / magic strings — **LOW**

**Sinais de detecção**
- Limiares e percentuais soltos (`if faturamento > 10000: desconto = faturamento * 0.1`).
- Listas de valores válidos repetidas inline (`['pending', 'in_progress', 'done', 'cancelled']`).
- Números de porta, tamanhos mínimos (`len(password) < 4`), prioridades (`priority <= 2`) sem nome.
- Regras de negócio codificadas em literais (`cc.startsWith("4")` decide pagamento).

**Correção**: Playbook **P-17** (constantes/enum nomeados no módulo de domínio ou config).

## AP-20 — Nomenclatura ruim — **LOW**

**Sinais de detecção**
- Identificadores de 1–3 letras fora de loops triviais: `u`, `e`, `p`, `cid`, `cc`, `d`, `t`, `c`.
- Campos de API abreviados (`usr`, `eml`, `pwd`, `c_id`) — **não renomeie o contrato público**; renomeie apenas as variáveis internas.
- Nomes que mentem (`badCrypto`, `AppManager`, `utils` contendo config) ou genéricos (`data`, `result`, `cursor2`, `cursor3`).
- Parâmetros que sombreiam builtins (`id`, `type`).

**Correção**: Playbook **P-18**.

## AP-21 — Imports não utilizados / código morto / dependências sem uso — **LOW**

**Sinais de detecção**
- Python: `import os, sys, json, time` sem uso; funções nunca chamadas (`grep -rn "nome_funcao("` retorna só a definição).
- JS: valores importados/exportados e nunca usados (`totalRevenue`, `globalCache`).
- Dependência no manifesto sem import correspondente (ex.: `marshmallow`, `requests`).
- Constantes declaradas e não usadas (`VALID_STATUSES` em helpers enquanto as rotas repetem a lista).

**Correção**: remover (Playbook **P-18**), ou reutilizar a constante existente (P-17).

## AP-22 — `print` / `console.log` como log — **LOW**

**Sinais de detecção**
- `print(` / `console.log(` em código de aplicação para registrar eventos e erros (grep: `\bprint\(` — sem o `\b` o padrão casa com `Blueprint(`).
- Mensagens de log com dados pessoais (e-mail no login) — sobe para AP-06 se houver segredo.

**Correção**: Playbook **P-19** (logger da stack: `logging` / `console` encapsulado com níveis).

## AP-23 — Lógica condicional verbosa / aninhamento excessivo — **LOW**

**Sinais de detecção**
- `if cond: return True else: return False`.
- `if a: if b: if c:` aninhados que poderiam ser uma expressão.
- Comparações encadeadas `p >= 1 and p <= 5` (Python: `1 <= p <= 5`).
- `type(x) == list` (use `isinstance`).

**Correção**: Playbook **P-15** / **P-18** (simplificação, guard clauses).

---

## Checklist de varredura (use na Fase 2 e na validação da Fase 3)

```bash
# Segredos
grep -rnEi "(secret|passw|pwd|senha|token|api_?key|gateway)[a-z_]*['\"]?\s*[:=]\s*['\"][^'\"]{3,}" <src>
# SQL concatenado
grep -rnE "(SELECT|INSERT|UPDATE|DELETE)[^\"'\`]*[\"'\`]\s*\+|\+\s*str\(|\\$\{" <src>
# Debug/host fixos
grep -rnE "debug\s*=\s*True|DEBUG\"?\]?\s*=\s*True" <src>
# Hash fraco
grep -rnE "md5|sha1\(|base64|badCrypto" <src>
# Query em loop (inspecionar manualmente os resultados)
grep -rnE "for .* in |forEach\(" <src>
# Exceções genéricas
grep -rnE "except:|except Exception|catch\s*\(\w*\)\s*\{\s*\}" <src>
# APIs deprecated
grep -rnE "\.query\.get\(|utcnow\(|new Buffer\(|url\.parse\(|createCipher\(" <src>
# Logs
# (o \b evita falso positivo com "Blueprint(")
grep -rnE "\bprint\(|console\.log\(" <src>
```
