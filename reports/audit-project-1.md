================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-10-26

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 5 | LOW: 4

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP-01 | Hardcoded credentials (SECRET_KEY, senhas seed) | app.py:7 |
| 2 | CRITICAL | AP-02 | SQL Injection em praticamente todas as queries | models.py:28 (+18) |
| 3 | CRITICAL | AP-03 | God File: models.py e app.py acumulam todas as camadas | models.py:1-314 |
| 4 | CRITICAL | AP-04 | Endpoints admin sem autenticação (reset do banco e SQL arbitrário) | app.py:47-78 |
| 5 | CRITICAL | AP-05 | Senhas armazenadas e comparadas em texto puro | models.py:105-131 |
| 6 | CRITICAL | AP-06 | Exposição de senhas e da SECRET_KEY nas respostas | controllers.py:284-290 |
| 7 | HIGH | AP-07 | Regra de negócio e validação acopladas ao HTTP / à camada de dados | controllers.py:24-62 |
| 8 | HIGH | AP-08 | Acoplamento forte via `get_db()` global, sem injeção de dependência | models.py:1 |
| 9 | HIGH | AP-09 | Conexão SQLite global e mutável compartilhada entre threads | database.py:4-10 |
| 10 | HIGH | AP-10 | Criação de pedido sem transação (check/insert/update separados) | models.py:133-169 |
| 11 | HIGH | AP-12 | Debug ligado e bind em 0.0.0.0 fixos | app.py:8, app.py:88 |
| 12 | MEDIUM | AP-13 | Queries N+1 na listagem de pedidos e consultas repetidas | models.py:171-233 |
| 13 | MEDIUM | AP-14 | Validação ausente/inconsistente entre endpoints | controllers.py:64-93 |
| 14 | MEDIUM | AP-15 | Código duplicado (row→dict, listagem de pedidos, validação) | models.py:12-21 |
| 15 | MEDIUM | AP-16 | `try/except Exception` em todo handler devolvendo `str(e)` | controllers.py:10-12 (+15) |
| 16 | MEDIUM | AP-18 | Notificações simuladas com print dentro do fluxo da requisição | controllers.py:208-210 |
| 17 | LOW | AP-19 | Magic numbers/strings (faixas de desconto, categorias, status) | models.py:256-262 |
| 18 | LOW | AP-20 | Nomenclatura ruim (`id` sombreando builtin, `cursor2`, `cursor3`) | models.py:187-193 |
| 19 | LOW | AP-21 | Imports não usados e query redundante | models.py:2 |
| 20 | LOW | AP-22 | `print` como mecanismo de log (inclui e-mail de quem loga) | controllers.py:179-182 |

## Findings

### #1 [CRITICAL] Hardcoded Credentials (AP-01)
File: app.py:7
File: controllers.py:289
File: database.py:75-79
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` fixo no código e repetido literalmente no health check (`"secret_key": "minha-chave-super-secreta-123"`). O seed cria o usuário `admin@loja.com` com senha `admin123` (e `123456`, `senha123`) direto no código.
Impact: Quem tiver acesso ao repositório pode forjar sessões/assinaturas Flask e entrar como admin; a chave não pode variar por ambiente nem ser rotacionada.
Recommendation: Ler `SECRET_KEY` e demais parâmetros de variáveis de ambiente em um módulo de configuração, com `.env.example` sem valores reais; senhas de seed geradas com hash (Playbook P-01, P-05).

### #2 [CRITICAL] SQL Injection (AP-02)
File: models.py:28
File: models.py:47-50
File: models.py:57-61
File: models.py:109-111
File: models.py:126-129
File: models.py:279-281
File: models.py:289-297
File: models.py:68, 92, 140, 148-151, 155, 157-166, 174, 188, 192 (+ demais concatenações)
Description: Todas as queries são montadas por concatenação de strings com dados vindos do request, ex.: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` e `" AND (nome LIKE '%" + termo + "%' ..."`.
Impact: Comprovado no baseline: `POST /login` com `{"email": "' OR '1'='1", "senha": "' OR '1'='1"}` retorna 200 autenticando como **Admin**. Também permite ler/alterar/apagar qualquer tabela via `/produtos/busca?q=`.
Recommendation: Usar placeholders `?` do `sqlite3` em todas as queries e montar filtros dinâmicos com lista de parâmetros (Playbook P-02).

### #3 [CRITICAL] God Class / God File (AP-03)
File: models.py:1-314
File: app.py:1-88
Description: `models.py` concentra SQL de 4 domínios (produtos, usuários, pedidos, relatórios), regras de negócio (verificação de estoque em `criar_pedido`, faixas de desconto em `relatorio_vendas`) e formatação de resposta. `app.py` mistura configuração, registro de 20 rotas, handlers com SQL direto (`/admin/*`) e bootstrap do servidor.
Impact: Impossível testar regras isoladamente; qualquer mudança em um domínio afeta os demais; não há fronteira clara entre dados, regra e HTTP.
Recommendation: Decompor em `models/` (um repositório por entidade), `controllers/` (casos de uso), `views/` (Blueprints finos), `config/` e composition root (Playbook P-03, P-04, P-07).

### #4 [CRITICAL] Endpoints administrativos sem autenticação (AP-04)
File: app.py:47-57
File: app.py:59-78
Description: `POST /admin/reset-db` executa `DELETE FROM` em todas as tabelas e `POST /admin/query` executa qualquer SQL recebido em `dados["sql"]` (`cursor.execute(query)`), ambos sem qualquer verificação de identidade.
Impact: Qualquer cliente anônimo pode apagar todo o banco ou exfiltrar/alterar qualquer dado (backdoor de SQL).
Recommendation: Proteger com middleware de autorização baseado em token de admin vindo da config (desabilitado se não configurado) e restringir o endpoint de consulta a uma única instrução `SELECT` (Playbook P-12).

### #5 [CRITICAL] Senhas em texto puro (AP-05)
File: models.py:122-131
File: models.py:105-111
File: database.py:75-83
Description: `criar_usuario` grava `senha` exatamente como recebida; `login_usuario` compara a senha dentro do SQL (`WHERE email = ... AND senha = ...`); o seed insere senhas em texto puro.
Impact: Um vazamento do arquivo `loja.db` (ou o endpoint #4) expõe as senhas reais de todos os clientes.
Recommendation: Persistir hash adaptativo com salt (`werkzeug.security.generate_password_hash`, já disponível com Flask) e verificar com `check_password_hash` após buscar o usuário pelo e-mail (Playbook P-05).

### #6 [CRITICAL] Exposição de dados sensíveis (AP-06)
File: models.py:83
File: models.py:99
File: controllers.py:284-290
Description: `GET /usuarios` e `GET /usuarios/<id>` devolvem o campo `senha`; `GET /health` devolve `secret_key`, `debug: True`, `db_path` e `ambiente: producao`.
Impact: Senhas e a chave secreta ficam acessíveis para qualquer cliente da API, sem autenticação.
Recommendation: Serializers explícitos sem campos sensíveis; health check apenas com status, conectividade e contagens (Playbook P-06).

### #7 [HIGH] Regra de negócio acoplada à camada HTTP e à camada de dados (AP-07)
File: controllers.py:24-62
File: controllers.py:188-220
File: models.py:139-146
File: models.py:256-262
Description: Os "controllers" leem `request` diretamente, validam, aplicam regras (categorias válidas) e formatam `jsonify` no mesmo bloco; a regra de estoque do pedido e o cálculo de desconto do relatório estão no arquivo de acesso a dados.
Impact: Regras não podem ser reutilizadas nem testadas sem Flask e sem banco; a camada de dados decide regras de negócio.
Recommendation: Controllers sem dependência do Flask recebendo dados simples; models apenas com acesso a dados; views finas fazendo a tradução HTTP (Playbook P-04).

### #8 [HIGH] Acoplamento forte sem injeção de dependência (AP-08)
File: models.py:1
File: controllers.py:2-3
File: controllers.py:266
File: app.py:3-4
Description: Todas as funções chamam `get_db()` importado globalmente; `controllers.py` importa o módulo `models` inteiro e também acessa o banco diretamente no `health_check`.
Impact: Não é possível substituir o banco por um fake em testes nem trocar a infraestrutura sem editar a regra de negócio.
Recommendation: Repositórios recebem a conexão por construtor; controllers recebem os repositórios; um composition root (`create_app`) monta o grafo (Playbook P-07).

### #9 [HIGH] Estado global mutável — conexão singleton (AP-09)
File: database.py:4-10
Description: `db_connection = None` em escopo de módulo, reatribuída via `global` e aberta com `check_same_thread=False`, compartilhada por todas as requisições/threads do servidor.
Impact: Condições de corrida e transações intercaladas entre requisições concorrentes; conexão nunca é fechada; testes interferem entre si.
Recommendation: Conexão por requisição gerenciada pelo ciclo de vida da app (`flask.g` + `teardown_appcontext`) (Playbook P-08).

### #10 [HIGH] Escrita multi-etapa sem transação (AP-10)
File: models.py:133-169
File: controllers.py:247-250
Description: `criar_pedido` valida estoque em um loop, insere o pedido, depois insere itens e debita estoque em outro loop, com um único `commit` no fim e sem rollback; ao cancelar um pedido apenas um `print` diz "Devolver estoque", sem efeito real.
Impact: Exceção no meio deixa pedido sem itens ou estoque debitado parcialmente (o `commit` seguinte de outra requisição persiste o estado parcial na conexão compartilhada).
Recommendation: Executar inserções e débitos em uma única transação (`with conn:`), lendo os preços uma única vez (Playbook P-09).

### #11 [HIGH] Configuração de execução insegura (AP-12)
File: app.py:8
File: app.py:88
Description: `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` fixos no código.
Impact: O debugger do Werkzeug exposto na rede permite execução remota de código; stack traces vazam para o cliente.
Recommendation: `DEBUG`, host e porta vindos da configuração, com debug desligado por padrão (Playbook P-01).

### #12 [MEDIUM] Queries N+1 e consultas repetidas (AP-13)
File: models.py:171-201
File: models.py:203-233
File: models.py:154-156
File: models.py:239-254
Description: Para cada pedido é feita uma query de itens e, para cada item, uma query do nome do produto (`cursor2`, `cursor3`); `criar_pedido` busca cada produto duas vezes; o relatório faz 5 consultas separadas que poderiam ser uma agregação.
Impact: Latência cresce linearmente com pedidos × itens; carga desnecessária no banco.
Recommendation: Um `SELECT` com `LEFT JOIN` entre pedidos, itens e produtos agrupado em memória; agregação com `SUM/COUNT ... CASE` (Playbook P-13).

### #13 [MEDIUM] Validação ausente ou inconsistente (AP-14)
File: controllers.py:64-93
File: controllers.py:169-171
File: controllers.py:239-240
File: controllers.py:195-201
Description: `atualizar_produto` não valida tamanho do nome nem categoria (que `criar_produto` valida); `login` e `atualizar_status_pedido` chamam `dados.get` sem checar corpo vazio (`AttributeError` → 500); `criar_pedido` não valida `quantidade` positiva nem formato dos itens.
Impact: Dados inválidos chegam ao banco (quantidades negativas aumentam o estoque) e erros de cliente viram 500.
Recommendation: Um validador por recurso reutilizado em criação e atualização, preservando as mensagens originais (Playbook P-14).

### #14 [MEDIUM] Código duplicado (AP-15)
File: models.py:12-21
File: models.py:31-40
File: models.py:304-313
File: models.py:79-86
File: models.py:95-102
File: models.py:171-233
File: controllers.py:28-46
File: controllers.py:72-90
Description: O dict de produto é montado manualmente 3 vezes, o de usuário 2 vezes; `get_pedidos_usuario` e `get_todos_pedidos` são cópias que diferem só no `WHERE`; a validação de produto está duplicada entre criar e atualizar.
Impact: Correções precisam ser feitas em vários lugares (ex.: remover `senha` exigiria 2 edições) e as cópias divergem.
Recommendation: Serializer único por entidade e uma função de listagem de pedidos com filtro opcional (Playbook P-06, P-15).

### #15 [MEDIUM] Tratamento de erro não centralizado (AP-16)
File: controllers.py:10-12
File: controllers.py:21-22
File: controllers.py:60-62
File: controllers.py:218-220
File: controllers.py:291-292
File: app.py:77-78
Description: Os 16 handlers repetem `try/except Exception as e: return jsonify({"erro": str(e)}), 500` (+ demais ocorrências no mesmo padrão em controllers.py); não há `errorhandler` global.
Impact: Mensagens internas (SQL, caminhos) vazam para o cliente; formato de erro inconsistente; boilerplate em todos os handlers.
Recommendation: Exceções de domínio (`NotFoundError`, `ValidationError`) e um error handler central que responde 500 genérico e registra o erro no log (Playbook P-11).

### #16 [MEDIUM] Efeitos colaterais acoplados à requisição (AP-18)
File: controllers.py:208-210
File: controllers.py:247-250
Description: Envio de e-mail/SMS/push simulado com `print("ENVIANDO EMAIL: ...")` dentro do handler de criação de pedido; notificações de status também via `print` no handler.
Impact: Integração real exigiria editar o controller HTTP; impossível desligar/substituir em testes.
Recommendation: `NotificationService` injetado e chamado pelo controller após a transação (Playbook P-16).

### #17 [LOW] Magic numbers / strings (AP-19)
File: models.py:256-262
File: controllers.py:47-52
File: controllers.py:242
File: app.py:85
Description: Faixas de desconto `10000/0.1`, `5000/0.05`, `1000/0.02` soltas; limites de nome `2`/`200` e lista de categorias inline; lista de status inline; porta `5000` repetida.
Impact: Regras de negócio escondidas em literais, difíceis de achar e alterar com segurança.
Recommendation: Constantes nomeadas no módulo de domínio/config (Playbook P-17).

### #18 [LOW] Nomenclatura ruim (AP-20)
File: models.py:187-193
File: models.py:24
File: controllers.py:56
Description: `cursor2`, `cursor3`, `prod`; parâmetro `id` sombreando o builtin `id()` em várias funções (`get_produto_por_id(id)`, `id = models.criar_produto(...)`).
Impact: Leitura mais difícil e risco de bugs sutis ao usar o builtin.
Recommendation: Nomes expressivos (`produto_id`, `itens_rows`) (Playbook P-18).

### #19 [LOW] Imports não utilizados e código redundante (AP-21)
File: models.py:2
File: database.py:2
File: controllers.py:268
Description: `import sqlite3` em models.py e `import os` em database.py não são usados; `cursor.execute("SELECT 1")` no health check é seguido de outras queries e não tem efeito.
Impact: Ruído e falsa impressão de dependências.
Recommendation: Remover (Playbook P-18).

### #20 [LOW] `print` como log (AP-22)
File: controllers.py:8
File: controllers.py:57
File: controllers.py:161
File: controllers.py:179-182
File: app.py:56
File: app.py:83-86
Description: Eventos e erros registrados com `print`, incluindo o e-mail do usuário em logins bem-sucedidos e falhos.
Impact: Sem níveis nem destino configurável; dados pessoais em stdout.
Recommendation: Usar `logging` com níveis e sem dados pessoais (Playbook P-19).

## Deprecated APIs
none detected for Python 3.10 + Flask 3.1.1 + flask-cors 5.0.1 + sqlite3 (stdlib). Nenhum uso de `before_first_request`, `JSONEncoder`, `FLASK_ENV` ou adaptadores de data deprecated do `sqlite3`.

## Notes
- Arquitetura atual: monolítica com separação nominal — existem arquivos chamados `models.py` e `controllers.py`, mas eles não respeitam as camadas (models com regra de negócio, controllers acoplados ao Flask, `app.py` com SQL).
- O CORS está aberto para qualquer origem (`CORS(app)`, app.py:9); mantido por compatibilidade, recomenda-se restringir por config em produção.

================================
Total: 20 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
