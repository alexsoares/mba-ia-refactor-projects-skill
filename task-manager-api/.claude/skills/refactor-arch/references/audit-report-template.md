# Template do Relatório de Auditoria (Fase 2)

O relatório é impresso no terminal e, quando solicitado, salvo como Markdown (`reports/audit-project-<n>.md`).
Siga a estrutura **exatamente**. Campos entre `<>` são preenchidos; nada fora do template deve ser adicionado,
exceto a seção opcional "Notes".

## Regras de preenchimento

1. **Ordenação**: CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, ordene pelo ID do catálogo (AP-01, AP-02...).
2. **Numeração**: findings numerados sequencialmente (`#1`, `#2`...) depois de ordenados.
3. **Localização**: `File:` sempre com `caminho/relativo:linha` ou `caminho/relativo:inicio-fim`.
   Para ocorrências múltiplas do mesmo anti-pattern, use uma linha `File:` por ocorrência (máximo ~8; acima disso, liste as 8 mais relevantes e informe `(+N ocorrências)`).
   As linhas devem ter sido conferidas lendo o arquivo com numeração.
4. **Description**: concreta — cite o trecho, o valor ou a função (`SECRET_KEY = 'minha-chave-super-secreta-123'`). Proibido texto genérico ("código ruim").
5. **Impact**: consequência real para segurança, manutenção, performance ou corretude.
6. **Recommendation**: ação objetiva + referência ao playbook (`Playbook P-02`).
7. **Summary**: contagens precisam bater com a lista de findings. `Total` = soma.
8. **Deprecated APIs**: seção obrigatória — liste as ocorrências (que também aparecem como findings AP-17) ou declare `none detected`.
9. O relatório termina **sempre** com a linha de confirmação; a skill deve parar após imprimi-la.

## Template

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório do projeto>
Stack:   <Linguagem> + <Framework> <versão>
Files:   <N> analyzed | ~<L> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP-01 | <título curto> | <arquivo:linha> |
| ... | | | | |

## Findings

### #1 [CRITICAL] <Título do anti-pattern> (AP-xx)
File: <arquivo:linha[-linha]>
File: <outra ocorrência, se houver>
Description: <o que foi encontrado, citando o código/valor>
Impact: <consequência concreta>
Recommendation: <o que fazer> (Playbook P-xx)

### #2 [HIGH] <Título> (AP-xx)
File: ...
Description: ...
Impact: ...
Recommendation: ...

<... demais findings na ordem ...>

## Deprecated APIs
- <arquivo:linha> — `<api antiga>` → `<equivalente moderno>` (finding #n)
<ou: none detected for <stack + versões>>

## Notes
<opcional: observações de arquitetura que não são findings (ex.: pontos positivos, premissas da análise)>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Exemplo de finding bem escrito

```markdown
### #2 [CRITICAL] SQL Injection (AP-02)
File: models.py:28
File: models.py:47-50
File: models.py:109-111
Description: Queries montadas por concatenação de strings com dados do request, ex.: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`.
Impact: O payload `' OR '1'='1` no login autentica como o primeiro usuário (admin) sem senha; também permite ler ou apagar qualquer tabela.
Recommendation: Usar placeholders do driver (`?`) em todas as queries e montar filtros dinâmicos com lista de parâmetros (Playbook P-02).
```

## Exemplo de finding mal escrito (não faça)

```markdown
### [HIGH] Código ruim
File: models.py
Description: O código tem vários problemas.
```
(sem linha, sem evidência, sem impacto, sem recomendação acionável)
