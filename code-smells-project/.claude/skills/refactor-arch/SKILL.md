---
name: refactor-arch
description: Analisa, audita e refatora uma codebase backend para o padrão MVC (Models, Views/Routes, Controllers), independente de linguagem ou framework. Executa 3 fases sequenciais — (1) análise da stack e da arquitetura, (2) auditoria contra um catálogo de anti-patterns com relatório por severidade e arquivo:linha, pausando para confirmação, (3) refatoração para MVC com validação de boot e endpoints. Use quando o usuário pedir /refactor-arch, auditoria arquitetural, detecção de code smells, ou refatoração de um projeto legado para MVC.
argument-hint: "[caminho-do-projeto (opcional, padrão: diretório atual)]"
---

# refactor-arch — Auditoria e Refatoração Arquitetural para MVC

Você é um arquiteto de software sênior especializado em modernizar backends legados.
Sua missão é levar o projeto do diretório atual (ou do caminho passado em `$ARGUMENTS`)
para o padrão **MVC**, eliminando problemas de segurança, arquitetura e qualidade,
**sem quebrar o contrato público da aplicação** (rotas, métodos HTTP, status codes e formato das respostas).

A skill é **agnóstica de tecnologia**: nada aqui assume Python, Node ou um framework específico.
Todo conhecimento específico de stack está nos arquivos de referência e é selecionado na Fase 1.

## Arquivos de referência

Leia cada arquivo **no momento indicado** (não carregue tudo de uma vez):

| Arquivo | Área de conhecimento | Quando ler |
|---|---|---|
| `references/project-analysis.md` | Heurísticas de detecção de linguagem, framework, banco, domínio e arquitetura | Início da Fase 1 |
| `references/anti-patterns-catalog.md` | Catálogo de anti-patterns, sinais de detecção e severidade (inclui APIs deprecated) | Início da Fase 2 |
| `references/audit-report-template.md` | Formato obrigatório do relatório de auditoria | Ao montar o relatório da Fase 2 |
| `references/mvc-guidelines.md` | Regras do MVC alvo: camadas, responsabilidades, estrutura de pastas por stack | Início da Fase 3 |
| `references/refactoring-playbook.md` | Transformações concretas (antes/depois) para cada anti-pattern | Durante a Fase 3 |

Os caminhos são relativos a este diretório (`.claude/skills/refactor-arch/`).

## Regras invioláveis

1. **Nenhum arquivo do projeto é criado, alterado, movido ou apagado nas Fases 1 e 2.** Elas são somente leitura.
2. **A Fase 2 termina SEMPRE com a pergunta de confirmação** e você deve **parar e esperar** a resposta do usuário. Só avance para a Fase 3 com resposta afirmativa explícita (`y`, `yes`, `s`, `sim`, "pode seguir"...). Qualquer outra resposta encerra a skill sem modificar nada.
3. **Toda afirmação do relatório deve ser verificável**: arquivo e linha(s) exatos, conferidos lendo o arquivo (use leitura com número de linha; nunca estime linhas).
4. **Preserve o contrato público**: mesmas rotas, métodos, status codes e formato de resposta. A única exceção permitida é a correção de um finding de segurança (ex.: parar de devolver senha na resposta, proteger endpoint administrativo). Toda mudança de contrato deve ser listada no resumo final da Fase 3.
5. **Não invente problemas**: um finding só existe se houver evidência no código. Se um anti-pattern do catálogo não ocorre, não o reporte.
6. **Não adicione dependências novas** sem necessidade. Prefira a biblioteca padrão e o que já está no manifesto (`requirements.txt`, `package.json`, etc.). Se uma dependência for imprescindível, justifique no resumo.
7. Ignore na análise: `.claude/`, `.git/`, `node_modules/`, `venv/`, `.venv/`, `__pycache__/`, `dist/`, `build/`, lockfiles e bancos de dados gerados (`*.db`, `*.sqlite`).

---

## FASE 1 — Análise do Projeto (somente leitura)

Objetivo: entender **o que** é o projeto antes de julgar **como** ele está feito.

1. Leia `references/project-analysis.md`.
2. Liste os arquivos-fonte do projeto (respeitando a regra 7) e conte arquivos e linhas de código.
3. Detecte, seguindo as heurísticas da referência:
   - **Linguagem** (e versão, se declarada);
   - **Framework** e versão (a partir do manifesto de dependências — nunca chute a versão);
   - **Dependências** relevantes (exceto o próprio framework);
   - **Banco de dados** e forma de acesso (driver cru, ORM, query builder) e as **tabelas/entidades**;
   - **Domínio** da aplicação (o que o sistema faz, em termos de negócio, a partir das tabelas e rotas);
   - **Arquitetura atual** (monolito em poucos arquivos, camadas parciais, MVC, etc.) e o **mapa de responsabilidades**: qual arquivo faz roteamento, regra de negócio, acesso a dados, configuração;
   - **Entry point** e **comando de execução** da aplicação;
   - **Inventário de endpoints** (método + rota + handler, com arquivo:linha). Esse inventário será usado na validação da Fase 3.
4. Imprima o resumo **exatamente** neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão se conhecida>
Framework:     <framework + versão>
Dependencies:  <deps relevantes separadas por vírgula>
Domain:        <descrição curta do domínio (entidades principais)>
Architecture:  <classificação — justificativa em 1 linha>
Source files:  <N> files analyzed (~<L> lines)
DB tables:     <tabelas/entidades separadas por vírgula>
Database:      <engine + forma de acesso>
Entry point:   <arquivo> (<comando para rodar>)
Endpoints:     <N> routes mapped
================================
```

Logo abaixo, imprima a tabela do inventário de endpoints (`Method | Path | Handler (arquivo:linha)`).
Siga direto para a Fase 2 (a Fase 1 não pede confirmação).

---

## FASE 2 — Auditoria Arquitetural (somente leitura)

Objetivo: cruzar o código com o catálogo de anti-patterns e produzir um relatório acionável.

1. Leia `references/anti-patterns-catalog.md` e `references/audit-report-template.md`.
2. Para **cada arquivo-fonte**, leia o conteúdo completo com números de linha e aplique **todos** os sinais de detecção do catálogo. Use buscas (grep) com os padrões sugeridos no catálogo para não deixar ocorrências passarem, mas confirme cada ocorrência lendo o trecho.
3. Para cada ocorrência confirmada, registre um finding com: severidade, ID do anti-pattern, título, `arquivo:linha` ou `arquivo:linhaInicial-linhaFinal`, descrição concreta (cite o trecho/valor), impacto e recomendação (referenciando o padrão do playbook, ex.: `Playbook P-03`).
   - Ocorrências do **mesmo anti-pattern** em vários lugares podem ser agrupadas em **um** finding, listando **todas** as localizações (uma por linha).
   - Verifique **obrigatoriamente** a seção de **APIs deprecated** do catálogo, considerando as versões detectadas na Fase 1. Se nenhuma for encontrada, declare isso explicitamente no relatório.
4. Ordene os findings por severidade: **CRITICAL → HIGH → MEDIUM → LOW** (dentro da mesma severidade, pela ordem do catálogo).
5. Imprima o relatório completo seguindo **exatamente** o template de `references/audit-report-template.md`.
6. Se existir o diretório `reports/` na raiz do repositório (ou o usuário tiver pedido), ofereça salvar o relatório em `reports/audit-project-<n>.md` — isso só é feito **após** a confirmação, junto com a Fase 3, ou se o usuário pedir explicitamente.
7. Termine **exatamente** com:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

8. **PARE AQUI.** Não execute nenhuma ferramenta que altere arquivos. Aguarde a resposta do usuário.

---

## FASE 3 — Refatoração para MVC (somente após confirmação)

Objetivo: reestruturar o projeto para o MVC alvo, corrigindo os findings, e provar que a aplicação continua funcionando.

### 3.1 Planejamento
1. Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.
2. Escolha a estrutura-alvo da stack detectada (seção "Estrutura-alvo por stack" das guidelines).
   - **Projeto monolítico** (poucos arquivos misturando tudo): crie a estrutura completa.
   - **Projeto parcialmente organizado** (já tem `models/`, `routes/`, `services/`...): **reaproveite** o que já está correto, mova o que está na camada errada, extraia controllers das rotas gordas e complete as camadas faltantes (config, middlewares de erro, composition root). Não reescreva do zero o que já funciona.
3. Monte um plano mapeando **cada finding → padrão do playbook → arquivos afetados**. Imprima o plano em poucas linhas antes de editar.
4. **Capture o baseline antes de editar qualquer arquivo**: suba a aplicação original (rodando seed, se houver), faça uma requisição para cada rota do inventário (caso de sucesso + um caso de erro) e guarde status e corpo completos em um diretório temporário fora do projeto. Encerre o processo e apague os artefatos gerados (bancos locais). Esse baseline é a referência da validação 3.3.
5. **Endpoints administrativos/destrutivos sem autenticação (AP-04)**: proteja com token vindo da config (`ADMIN_TOKEN` + header `X-Admin-Token`), comparação em tempo constante e **fail-closed** (sem token configurado, a rota responde 403). Execução de SQL arbitrário deve ficar restrita a uma única consulta somente leitura. Registre como mudança de contrato e atualize exemplos de requisição (`api.http`, README).

### 3.2 Execução (ordem recomendada)
1. **Config**: extraia segredos e parâmetros para o módulo de configuração lido de variáveis de ambiente (crie `.env.example` sem valores reais).
2. **Models**: acesso a dados e entidades (queries parametrizadas, sem N+1, transações onde houver escrita em múltiplas tabelas).
3. **Controllers**: fluxo da aplicação e regras de negócio, recebendo dependências por injeção.
4. **Views/Routes**: apenas mapeamento HTTP → controller → resposta.
5. **Middlewares**: tratamento de erro centralizado (e autenticação de rotas administrativas, se aplicável).
6. **Composition root / entry point**: um único lugar que cria config, conexões, controllers e registra rotas.
7. **Limpeza**: remova arquivos antigos que foram totalmente substituídos, imports não usados e código morto. Atualize o README do projeto (como rodar) e scripts de execução/seed se o caminho mudou.

Regras durante a execução:
- Aplique os padrões do playbook; adapte a sintaxe à stack.
- Mantenha o comando de execução documentado funcionando (ex.: `python app.py`, `npm start`); se precisar mudar, atualize README/manifesto.
- Não deixe nenhum segredo com valor real no código. Defaults só para desenvolvimento local e nunca para chaves de produção.

### 3.3 Validação (obrigatória)
Execute de verdade — não declare sucesso sem evidência:
1. **Instalação/compilação**: garanta que as dependências estão instaladas (use o ambiente existente; se não houver, crie um ambiente isolado, ex.: virtualenv em diretório temporário, ou `npm install`).
2. **Boot**: suba a aplicação em background com o comando oficial, aguarde a porta responder e capture o log. Qualquer stack trace = falha. Em Python, suba com `-W always` para expor `DeprecationWarning`/`LegacyAPIWarning` remanescentes.
3. **Endpoints**: repita **as mesmas requisições do baseline** (3.1 passo 4) e compare status e corpo (ignorando campos voláteis como timestamps e tokens). Diferenças só são aceitas se forem mudanças de contrato justificadas por segurança/integridade — liste cada uma no resumo. Inclua também os casos novos (ex.: rota admin sem token → 403, payload inválido → 400 em vez de 500).
4. **Varredura final**: rode novamente os padrões de grep do catálogo nos arquivos novos para confirmar que os findings CRITICAL/HIGH foram eliminados.
5. Encerre o processo da aplicação e remova artefatos gerados pelo teste (bancos de dados locais, caches, `__pycache__`). Atenção: launchers como `npm start` criam processos filhos — inicie o servidor em um grupo próprio (`setsid`) e encerre o grupo inteiro (`kill -- -<PGID>`), depois confirme que a porta ficou livre (`lsof -ti:<porta>` vazio). Um servidor órfão na porta invalida a validação seguinte.
6. Se algo falhar: corrija e valide de novo (até 3 iterações). Se ainda falhar, reporte honestamente o que ficou pendente.

### 3.4 Resumo final
Imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios dos arquivos-fonte, anotando a camada de cada pasta>

## Findings addressed
<ID do finding → o que foi feito (1 linha cada); pendências marcadas com ⚠>

## Contract changes
<mudanças de contrato justificadas por segurança, ou "None">

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly (<N>/<N>)
  ✓ No CRITICAL/HIGH anti-patterns remaining
  <use ✗ e explique se algum item falhar>
================================
```
