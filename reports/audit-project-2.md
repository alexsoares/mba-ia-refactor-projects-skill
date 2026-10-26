================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express ^4.18.2
Files:   3 analyzed | ~180 lines of code
Date:    2026-10-26

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 3 | LOW: 4

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP-01 | Credenciais de banco e chave live do gateway hardcoded | src/utils.js:1-7 |
| 2 | CRITICAL | AP-03 | God Class `AppManager` (banco, schema, seed, rotas, regras) | src/AppManager.js:4-139 |
| 3 | CRITICAL | AP-04 | Relatório financeiro e exclusão de usuário sem autenticação | src/AppManager.js:80, 131 |
| 4 | CRITICAL | AP-05 | "Criptografia" de senha com base64 truncado + senha padrão | src/utils.js:17-23 |
| 5 | CRITICAL | AP-06 | Número do cartão e chave do gateway escritos no log | src/AppManager.js:45 |
| 6 | HIGH | AP-07 | Fluxo de checkout e agregação do relatório dentro das rotas | src/AppManager.js:28-78 |
| 7 | HIGH | AP-08 | Acoplamento forte: classe cria o próprio banco, sem injeção | src/AppManager.js:5-8 |
| 8 | HIGH | AP-09 | Estado global mutável exportado (`globalCache`, `totalRevenue`) | src/utils.js:9-15 |
| 9 | HIGH | AP-10 | Checkout sem transação e exclusão que deixa órfãos | src/AppManager.js:50-63 |
| 10 | HIGH | AP-11 | Callback hell com contadores manuais e erros ignorados | src/AppManager.js:37-77 |
| 11 | MEDIUM | AP-13 | N+1 no relatório financeiro | src/AppManager.js:89-127 |
| 12 | MEDIUM | AP-14 | Validação de entrada mínima no checkout | src/AppManager.js:29-35 |
| 13 | MEDIUM | AP-16 | Erros engolidos/inconsistentes e sem middleware de erro | src/AppManager.js:133-136 |
| 14 | LOW | AP-19 | Magic strings/numbers (aprovação por prefixo "4", status, senha padrão) | src/AppManager.js:46 |
| 15 | LOW | AP-20 | Nomenclatura ruim (`u`, `e`, `p`, `cid`, `cc`, `self`, `badCrypto`) | src/AppManager.js:29-33 |
| 16 | LOW | AP-21 | Código morto: imports/exports e configs não usados | src/AppManager.js:2 |
| 17 | LOW | AP-22 | `console.log` como log | src/utils.js:13 |

## Findings

### #1 [CRITICAL] Hardcoded Credentials (AP-01)
File: src/utils.js:2-5
Description: Objeto `config` com `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` (prefixo de chave **live**) e `smtpUser` fixos no código.
Impact: Credenciais de produção expostas a qualquer pessoa com acesso ao repositório/histórico git; impossível ter valores por ambiente ou rotacionar.
Recommendation: Módulo `config` lendo `process.env`, sem valores reais no código, e `.env.example` documentando as variáveis (Playbook P-01).

### #2 [CRITICAL] God Class (AP-03)
File: src/AppManager.js:4-139
Description: `AppManager` cria a conexão (`new sqlite3.Database(':memory:')`), cria o schema e o seed (`initDb`), registra todas as rotas (`setupRoutes`) e implementa dentro delas validação, criação de usuário, decisão de pagamento, matrícula, auditoria, relatório financeiro e exclusão.
Impact: Nenhuma regra pode ser testada isoladamente; qualquer alteração afeta toda a aplicação.
Recommendation: Decompor em `database/`, `models/`, `services/`, `controllers/`, `views/` e um composition root `createApp()` (Playbook P-03, P-07).

### #3 [CRITICAL] Endpoints administrativos/destrutivos sem autenticação (AP-04)
File: src/AppManager.js:80
File: src/AppManager.js:131
Description: `GET /api/admin/financial-report` (receita e lista de alunos/pagamentos) e `DELETE /api/users/:id` não exigem nenhuma credencial.
Impact: Qualquer cliente anônimo lê dados financeiros e pessoais de todos os alunos ou apaga usuários.
Recommendation: Middleware de autorização com token administrativo vindo da config (Playbook P-12).

### #4 [CRITICAL] Hash de senha inseguro (AP-05)
File: src/utils.js:17-23
File: src/AppManager.js:68
File: src/AppManager.js:18
Description: `badCrypto` repete os 2 primeiros caracteres do base64 da senha 10.000 vezes e trunca em 10 caracteres — é reversível e colide para qualquer senha com o mesmo prefixo; quando `pwd` não é enviado é usada a senha padrão `"123456"`; o seed grava `'123'` em texto puro.
Impact: Senhas triviais de recuperar e colisões permitem login com senhas diferentes; usuários criados sem senha recebem uma senha conhecida.
Recommendation: `crypto.scrypt` com salt aleatório (stdlib, sem dependência nova) e senha obrigatória/aleatória (Playbook P-05).

### #5 [CRITICAL] Exposição de dados sensíveis em log (AP-06)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` escreve o número completo do cartão e a chave do gateway no stdout a cada checkout.
Impact: Violação de PCI-DSS; qualquer acesso aos logs expõe cartões e a chave do gateway.
Recommendation: Nunca logar PAN/chaves; registrar apenas o id da matrícula/últimos 4 dígitos se necessário (Playbook P-19, P-06).

### #6 [HIGH] Regra de negócio dentro das rotas (AP-07)
File: src/AppManager.js:28-78
File: src/AppManager.js:80-129
Description: O handler de `POST /api/checkout` decide aprovação do pagamento, cria usuário, matrícula, pagamento e log de auditoria; o handler do relatório faz a agregação de receita por curso.
Impact: Regras presas ao Express, sem possibilidade de reuso ou teste unitário.
Recommendation: `CheckoutController`/`ReportController` com `async/await` recebendo models e serviços; rotas finas (Playbook P-04).

### #7 [HIGH] Acoplamento forte sem injeção de dependência (AP-08)
File: src/AppManager.js:5-8
File: src/app.js:8-10
Description: O construtor instancia o próprio banco em memória e as rotas usam `this.db` por closure; serviços (pagamento, cache, hash) são funções importadas diretamente de `utils`.
Impact: Impossível substituir banco/gateway por fakes; troca de infraestrutura exige editar a regra de negócio.
Recommendation: Injeção via construtor e composition root único (Playbook P-07).

### #8 [HIGH] Estado global mutável (AP-09)
File: src/utils.js:9-10
File: src/utils.js:12-15
File: src/utils.js:25
Description: `let globalCache = {}` e `let totalRevenue = 0` em escopo de módulo, exportados; `logAndCache` grava uma chave nova a cada checkout e nunca remove.
Impact: Crescimento de memória ilimitado, estado compartilhado entre requisições e módulos; `totalRevenue` exportado por valor dá falsa impressão de contador global.
Recommendation: Cache encapsulado em uma classe com limite, instanciado no composition root e injetado (Playbook P-07).

### #9 [HIGH] Escrita multi-etapa sem transação / órfãos (AP-10)
File: src/AppManager.js:50-63
File: src/AppManager.js:131-136
Description: Matrícula, pagamento e auditoria são inseridos em callbacks independentes, sem `BEGIN/COMMIT`; `DELETE /api/users/:id` apaga só o usuário e a própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco".
Impact: Falha no pagamento deixa matrícula sem pagamento; exclusão gera matrículas/pagamentos órfãos que aparecem como "Unknown" no relatório (confirmado no baseline).
Recommendation: Transação única no checkout e exclusão em cascata dentro de transação (Playbook P-09).

### #10 [HIGH] Callback hell (AP-11)
File: src/AppManager.js:37-77
File: src/AppManager.js:83-128
File: src/AppManager.js:26
Description: Até 6 níveis de callbacks aninhados, `const self = this` para alcançar o contexto, e contadores manuais `coursesPending--`/`enrPending--` para saber quando responder; erros de callback ignorados (linhas 57, 92, 104, 106, 133) — em 92, `enrollments` indefinido derrubaria o processo.
Impact: Fluxo ilegível, respostas nunca enviadas ou enviadas duas vezes, falhas silenciosas.
Recommendation: Wrapper Promise para o driver e controllers com `async/await` (Playbook P-10).

### #11 [MEDIUM] Queries N+1 (AP-13)
File: src/AppManager.js:89-127
Description: Para cada curso, uma query de matrículas; para cada matrícula, uma query de usuário e outra de pagamento (1 + C + 2·M consultas).
Impact: O relatório degrada linearmente com o número de matrículas.
Recommendation: Um único `SELECT` com `LEFT JOIN` courses → enrollments → users → payments agrupado em memória (Playbook P-13).

### #12 [MEDIUM] Validação de entrada insuficiente (AP-14)
File: src/AppManager.js:29-35
Description: O checkout só verifica presença de `usr`, `eml`, `c_id`, `card`; não valida formato do e-mail, tipo de `c_id` nem formato do cartão; `pwd` é opcional.
Impact: Dados inválidos persistidos e usuários criados sem senha escolhida.
Recommendation: Função de validação/parsing única para o payload de checkout, preservando o contrato (`400 Bad Request`) (Playbook P-14).

### #13 [MEDIUM] Tratamento de erro inconsistente (AP-16)
File: src/AppManager.js:38
File: src/AppManager.js:133-136
File: src/app.js:5-10
Description: Erro de banco ao buscar curso vira `404 Curso não encontrado`; `DELETE /api/users/:id` ignora `err` e responde sucesso mesmo para id inexistente; não existe middleware de erro do Express.
Impact: Falhas reais mascaradas; cliente recebe sucesso falso.
Recommendation: `AppError` + `asyncHandler` + middleware `errorHandler` central (Playbook P-11).

### #14 [LOW] Magic numbers / strings (AP-19)
File: src/AppManager.js:46
File: src/AppManager.js:21
File: src/AppManager.js:108
File: src/AppManager.js:68
File: src/utils.js:19-22
Description: Aprovação de pagamento decidida por `cc.startsWith("4")`; status `"PAID"`/`"DENIED"` repetidos como literais; senha padrão `"123456"`; `10000` iterações e `substring(0, 10)` sem nome.
Impact: Regras de negócio escondidas em literais.
Recommendation: Constantes nomeadas (`PaymentStatus`, `APPROVED_CARD_PREFIX`) (Playbook P-17).

### #15 [LOW] Nomenclatura ruim (AP-20)
File: src/AppManager.js:29-33
File: src/AppManager.js:26
File: src/AppManager.js:89
File: src/utils.js:17
Description: Variáveis `u`, `e`, `p`, `cid`, `cc`, `c`, `enr`; `const self = this`; nomes que não dizem o que fazem (`AppManager`, `badCrypto`, `utils` contendo configuração).
Impact: Leitura difícil; `e` é usado tanto para e-mail quanto (convencionalmente) para erro.
Recommendation: Desestruturar o payload com nomes expressivos, mantendo os campos do contrato (`usr`, `eml`...) (Playbook P-18).

### #16 [LOW] Código morto (AP-21)
File: src/AppManager.js:2
File: src/utils.js:2-5
File: src/utils.js:25
Description: `totalRevenue` importado e nunca usado; `dbUser`, `dbPass`, `smtpUser` nunca lidos; `globalCache` exportado sem consumidor.
Impact: Ruído e segredos desnecessários no código.
Recommendation: Remover (Playbook P-18).

### #17 [LOW] `console.log` como log (AP-22)
File: src/utils.js:13
File: src/AppManager.js:45
File: src/app.js:13
Description: Log feito com `console.log` sem nível nem controle.
Impact: Sem distinção entre info e erro; impossível silenciar em testes.
Recommendation: Logger simples com níveis encapsulado em um módulo (Playbook P-19).

## Deprecated APIs
none detected for Node.js 22 + Express ^4.18.2 + sqlite3 ^5.1.6 (sem `new Buffer`, `url.parse`, `body-parser` separado, `req.param` ou `res.send(status)`). Observação: a API de callbacks do `sqlite3` não é deprecated, mas é o estilo legado que origina o finding #10.

## Notes
- Arquitetura atual: monolítica sem camadas — `app.js` delega tudo para a classe `AppManager`.
- O banco é SQLite em memória (`:memory:`), recriado a cada boot com seed; o relatório e o checkout dependem desse seed.

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
