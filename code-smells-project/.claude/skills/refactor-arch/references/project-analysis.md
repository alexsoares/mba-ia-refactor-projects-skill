# Análise de Projeto — Heurísticas (Fase 1)

Este guia diz **onde olhar** e **como concluir** cada item do resumo da Fase 1.
Regra geral: toda conclusão deve vir de uma evidência no repositório (arquivo de manifesto,
import, chamada de API). Se não houver evidência, escreva `unknown` em vez de chutar.

## 1. Inventário de arquivos

- Liste arquivos-fonte ignorando: `.git/`, `.claude/`, `node_modules/`, `venv/`, `.venv/`, `env/`,
  `__pycache__/`, `dist/`, `build/`, `target/`, `vendor/`, `coverage/`, lockfiles
  (`package-lock.json`, `yarn.lock`, `poetry.lock`, `Pipfile.lock`), bancos gerados (`*.db`, `*.sqlite*`).
- Conte como "source files" apenas código executável da aplicação (ex.: `.py`, `.js`, `.ts`, `.go`, `.java`, `.rb`, `.php`, `.cs`).
  Arquivos `__init__.py` vazios e scripts auxiliares (seed, migrations) entram na contagem, mas mencione-os separadamente se forem relevantes.
- Linhas: `wc -l` nos arquivos-fonte. Arredonde no resumo (`~800 lines`).

## 2. Linguagem

| Evidência | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, arquivos `.py` | Python |
| `package.json` + `.js`/`.mjs`/`.cjs` | JavaScript (Node.js) |
| `package.json` + `tsconfig.json` / `.ts` | TypeScript (Node.js) |
| `go.mod` | Go |
| `pom.xml`, `build.gradle(.kts)` | Java / Kotlin |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `*.csproj` | C# / .NET |

Versão da linguagem: `python_requires`/`.python-version`/`runtime.txt`; `engines.node` no `package.json`/`.nvmrc`.
Se não declarada, informe a versão do runtime instalado (ex.: `python3 --version`, `node --version`) indicando que é o runtime local.

## 3. Framework e dependências

Leia o manifesto e procure os imports no código para confirmar que a dependência é realmente usada.

| Manifesto contém | Import/uso no código | Framework |
|---|---|---|
| `flask` | `from flask import Flask`, `Blueprint` | Flask |
| `fastapi` | `from fastapi import FastAPI`, `APIRouter` | FastAPI |
| `django` | `django.conf`, `urls.py`, `views.py` | Django |
| `express` | `require('express')` / `import express` | Express |
| `fastify` | `require('fastify')` | Fastify |
| `@nestjs/core` | decorators `@Controller` | NestJS |
| `koa` | `new Koa()` | Koa |
| `gin-gonic/gin` | `gin.Default()` | Gin |
| `spring-boot-starter-web` | `@RestController` | Spring Boot |

- Versão: **sempre** do manifesto (`flask==3.1.1`, `"express": "^4.18.2"`). Se houver range (`^4.18.2`), informe o range ou a versão resolvida no lockfile.
- Dependências: liste as relevantes para a arquitetura (ORM, driver de banco, CORS, validação, HTTP client, auth).
  Marque dependências **declaradas mas não usadas** (ex.: `marshmallow` no manifesto sem nenhum import) — isso alimenta o catálogo (AP-21).

## 4. Banco de dados e acesso a dados

| Sinal | Conclusão |
|---|---|
| `import sqlite3`, `sqlite3.connect(...)` | SQLite via driver cru (SQL manual) |
| `require('sqlite3')`, `new sqlite3.Database(':memory:')` | SQLite em memória via driver cru (callbacks) |
| `flask_sqlalchemy`, `db.Model`, `db.Column` | ORM SQLAlchemy (Flask-SQLAlchemy) |
| `SQLALCHEMY_DATABASE_URI = 'sqlite:///x.db'` | SQLite em arquivo via ORM |
| `psycopg2`, `pg`, `mysql2`, `pymysql` | PostgreSQL / MySQL via driver |
| `sequelize`, `typeorm`, `prisma`, `mongoose` | ORM/ODM Node |

**Tabelas/entidades**: extraia de `CREATE TABLE <nome>`, `__tablename__ = '<nome>'`, `class X(db.Model)`,
`sequelize.define('<nome>'`, schemas Prisma/Mongoose. Liste na ordem em que aparecem.

## 5. Domínio da aplicação

Deduza a partir de **nomes de tabelas + rotas + mensagens**. Descreva em termos de negócio, não técnicos:

- `produtos`, `pedidos`, `itens_pedido`, `usuarios` → "E-commerce API (produtos, pedidos, usuários)".
- `courses`, `enrollments`, `payments`, rota `/checkout` → "LMS (plataforma de cursos) com fluxo de checkout/pagamento".
- `tasks`, `categories`, `users`, rotas `/reports` → "Task Manager (tarefas, categorias, usuários, relatórios)".

## 6. Arquitetura atual

Classifique usando a tabela abaixo e justifique em uma linha:

| Classificação | Sinais |
|---|---|
| **Monolítica sem camadas** | ≤ 5 arquivos; o mesmo arquivo contém rotas + SQL + regra de negócio; ou uma classe "Manager" faz tudo |
| **Monolítica com separação nominal** | Existem arquivos chamados `models`/`controllers`, mas o "model" tem regra de negócio e formatação, o "controller" acessa banco ou o entry point também tem rotas com SQL |
| **Camadas parciais** | Pastas `models/`, `routes/`, `services/`, `utils/`, mas rotas contêm lógica de negócio, validação e queries; config hardcoded no entry point |
| **MVC / Layered adequado** | Rotas finas → controllers → models/repositórios; config isolada; erro centralizado |

**Mapa de responsabilidades** — para cada arquivo, marque quais responsabilidades ele carrega:
`[routing] [http-parsing] [validation] [business] [data-access] [serialization] [config] [bootstrap] [side-effects]`.
Um arquivo com 4+ responsabilidades é candidato a God Class (AP-03).

## 7. Entry point e execução

| Stack | Onde procurar |
|---|---|
| Python | `if __name__ == "__main__":` + `app.run(...)`; `README` (`python app.py`); `Procfile`; `wsgi.py` |
| Node | `package.json` → `scripts.start` e `main`; `app.listen(...)` |

Registre também a **porta** (`port=5000`, `config.port`) — ela é usada na validação.
Se existir script de seed/migração (`seed.py`, `migrate`), registre que precisa ser executado antes do boot.

## 8. Inventário de endpoints

Busque todas as declarações de rota e registre `METHOD PATH -> handler (arquivo:linha)`:

| Stack | Padrões de busca (grep -n) |
|---|---|
| Flask | `@app.route(`, `@<bp>.route(`, `add_url_rule(`, `methods=[` |
| FastAPI | `@app.get(`, `@router.post(` ... |
| Express | `app.get(`, `app.post(`, `app.put(`, `app.delete(`, `router.<verbo>(` |
| Django | `path(` em `urls.py` |

Atenção: no Flask, a mesma URL com métodos diferentes são endpoints distintos; prefixos de Blueprint (`url_prefix`) devem ser somados ao path.

## 9. Saída esperada (exemplo)

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.10 (runtime local)
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica com separação nominal — app.py tem rotas e SQL; models.py mistura SQL e regra de negócio
Source files:  4 files analyzed (~780 lines)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Database:      SQLite (loja.db) via sqlite3 cru
Entry point:   app.py (python app.py, porta 5000)
Endpoints:     19 routes mapped
================================
```
