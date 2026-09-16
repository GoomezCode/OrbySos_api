# Fase 8 — Documento de Sessão (continuação)

> **Data:** 2026-09-15  
> **Objetivo:** Validar contratos JSON vs API, corrigir divergências reais, testes de fluxo e edge-cases

---

## O que foi feito até agora (Fase 8)

### 8.5 — Auditoria de SQL Injection ✅ CONCLUÍDA
- **57 queries** auditadas em 6 repositórios (`admin_repository`, `client_repository`, `solicitacao_repository`, `sync_repository`, `user_repository`, `catalog_repository`)
- **TODAS SEGURAS** — 100% parameterized com `%s` + tupla
- Único dinamismo: `admin_repository.py` gera `%s` repetidos para `IN (...)` — seguro (tamanho da tupla controlado)
- Relatório em `docs/FASE8_1_VALIDACAO_CONTRATOS.md`

### 8.1 — Validação de Contratos JSON ✅ CONCLUÍDA (relatório)
- 17 contratos avaliados: **8 CONFORME**, **9 DIVERGENTE**
- Relatório completo em `docs/FASE8_1_VALIDACAO_CONTRATOS.md`

### 8.4 — Correções de Divergências REAIS ✅ IMPLEMENTADAS

#### Correção 1: Global Error Envelope (`erro-padrao`)
- **Problema:** API retornava `{"detail": ...}`, mas frontend lê `payload.error.{code, message, fields, current}` + `payload.trace_id`
- **Solução:** Criado `core/errors.py` com `http_exception_handler` + `validation_exception_handler`
- Registrado em `main.py` com `app.add_exception_handler(...)`
- **Impacto:** Todos os erros HTTP agora retornam `{"error": {...}, "trace_id": "trace-xxx"}` — compatível com `createApiError` do frontend
- **Testes afetados:** 6 asserts `["detail"]["code"]` → `["error"]["code"]` (admin_routes + taxi_question_routes)

#### Correção 2: Query `status` em `/clientes/me/apolices`
- **Problema:** Frontend sempre envia `?status=ATIVA`, API ignorava
- **Solução:** Adicionado `status: str | None = Query(default=None)` no router, filtro no service
- **Impacto:** API filtra por `apolice_status` quando `status` informado

#### Correção 3: `bool()` cast em `perguntas[]` (detalhe cliente)
- **Problema:** `bool(None)` → `False` destruía distinção pendente/false; `bool("Mala")` → `True` perdia string
- **Solução:** Trocado para `p.get("necessita_taxi")` / `p.get("bagagem")` etc. (preserva null/0/1/string)
- **Teste novo:** `test_perguntas_preserves_null_and_string_bagagem`

#### Correção 4: Query `sort` em `/admin/solicitacoes`
- **Problema:** Frontend declara `sort` (padrão `data_recebimento:desc`), API tinha ORDER BY fixo
- **Solução:** Whitelist seguro em `admin_repository._parse_sort()` — mapeia campos permitidos para colunas SQL
- **Segurança:** Apenas campos whitelistados; qualquer campo inválido usa ORDER BY padrão

---

## Estado dos testes (sessão anterior — 116 testes)

> Estado antes desta continuação. Ver tabela atualizada na seção "Estado dos testes (13 suites — 136 testes)" abaixo.

| Suite | Status | Qtd |
|---|---|---|
| admin_routes | ✅ OK | 15 |
| admin_service | ✅ OK | 23 |
| auth_routes | ✅ OK | 8 |
| auth_service | ✅ OK | 10 |
| catalog_routes | ✅ OK | 5 |
| catalog_service | ✅ OK | 6 |
| client_routes | ✅ OK | 11 |
| client_service | ✅ OK | 8 |
| sync_routes | ✅ OK | 6 |
| sync_service | ✅ OK | 5 |
| taxi_question_routes | ✅ OK | 10 |
| taxi_question_service | ✅ OK | 9 |
| smoke_phase1 | ✅ OK | 37 rotas |

**Total: 116 testes — TODOS PASSANDO**

---

## O que foi feito nesta continuação (2026-09-15)

### 8.6 — Integração do `bump_revision()` nas escritas ✅ IMPLEMENTADA
- **Refactor `repositories/sync_repository.py`**: criado `bump_revision_cursor(cur, now)` — incremento atômico `CAST(valor AS UNSIGNED) + 1` + `updated_at`, executado no mesmo cursor da transação (NÃO commita sozinho).
  - `bump_revision(now)` público passa a delegar ao `bump_revision_cursor` e retornar `get_version()`.
- **Conexão com as transações existentes** (antes do `conn.commit()`):
  - `repositories/solicitacao_repository.py` — `create_solicitacao` e `answer_pergunta`
  - `repositories/admin_repository.py` — `transicionar_solicitacao`, `add_assistencia`, `update_assistencia_status`
- **Atomicidade:** bump faz parte da MESMA transação (rollback conjunto se algo falhar).

### 8.7 — Testes de integração do bump (novo `tests/test_revision_integration.py`) ✅ 9 TESTES
- FakeConnection/FakeCursor que registram queries e confirma se o bump roda no mesmo cursor antes do commit.
- Cobertos: `create_solicitacao`, `answer_pergunta`, `transicionar_solicitacao`, `add_assistencia`, `update_assistencia_status`.
- Caso de versão obsoleta (`rowcount=0`) verifica que NÃO há bump e que rollback acontece.

### 8.8 — Testes de fluxo completo (novos) ✅
- **`tests/test_flow_cliente.py` (1 teste de fluxo)** — login real → apólices?status=ATIVA → criar solicitação (201, RECEBIDA) → detalhe → responder táxi (RESPONDIDA). Mocks apenas nos repositórios.
- **`tests/test_flow_admin.py` (1 teste de fluxo)** — login real → dashboard → assumir (EM_ANALISE) → confirmar (CONFIRMADA) → iniciar (EM_ATENDIMENTO) → adicionar assistência GUINCHO (201 + pergunta TAXI PENDENTE) → PATCH assistência (CONCLUIDA) → concluir (CONCLUIDA) → detalhe com histórico.

### 8.9 — Testes de edge-cases (novo `tests/test_edge_cases.py`) ✅ 9 TESTES
- 401 sem token / com token inválido, 403 perfil errado, 404, 409 `POLICY_ACTIVE_REQUEST_EXISTS`, 422 com `fields` (login + criação de solicitação), 422 transição inválida admin, e 500 via handler global.
- Todos validam o envelope `{error:{code,message,fields?}, trace_id}`.
- **Correções reais descobertas:**
  - `middleware/auth.py`: 401 agorá usa `make_error_response()` do `core/errors.py` (passava a devolver 401 SEM envelope/trace_id).
  - `main.py`: registrado `unhandled_exception_handler` (`Exception`) → 500 com envelope `INTERNAL_ERROR` (antes estourava body cru).

### 8.10 — Fix `auth_service` ✅
- `detail={"code": "AUTH_INVALID_CREDENTIALS", ...}` (401) e `detail={"code": "AUTH_INACTIVE_USER", ...}` (403) em vez de string simples.

---

## Estado dos testes (13 suites — 136 testes)

| Suite | Status | Qtd |
|---|---|---|
| admin_routes | ✅ OK | 15 |
| admin_service | ✅ OK | 23 |
| auth_routes | ✅ OK | 8 |
| auth_service | ✅ OK | 10 |
| catalog_routes | ✅ OK | 5 |
| catalog_service | ✅ OK | 6 |
| client_routes | ✅ OK | 11 |
| client_service | ✅ OK | 8 |
| edge_cases | ✅ OK | 9 |
| flow_admin | ✅ OK | 1 |
| flow_cliente | ✅ OK | 1 |
| revision_integration | ✅ OK | 9 |
| sync_routes | ✅ OK | 6 |
| sync_service | ✅ OK | 5 |
| taxi_question_routes | ✅ OK | 10 |
| taxi_question_service | ✅ OK | 9 |
| smoke_phase1 | ✅ OK | 37 rotas |

**Total: 136 testes — TODOS PASSANDO**

---

## O que ainda falta para completar a Fase 8

### Prioridade Média
5. **Registrar Fase 8 no `docs/PLANO_IMPLEMENTACAO_API.md`** — marcar ✅ FEITA
   - Perguntar ao usuário antes de prosseguir (regra do AGENTS.md)

6. **Revisar supersets aceitáveis** — ✅ DECISÃO TOMADA (todos ACEITÁVEIS):
   - `admin-comandos`: responses retornam aggregate completo vs mínimo declarado — **ACEITÁVEL** (frontend usa spread/optional chaining)
   - `admin-assistencias`: `pergunta_criada` com 6 campos extras — **ACEITÁVEL**
   - `admin-solicitacoes`: campos extras (local, data_criacao, etc.) — **ACEITÁVEL**
   - `admin-dashboard`: fila_prioritaria com campos extras — **ACEITÁVEL**
   - `solicitacao-criar`: estrutura diferente (irmãos vs aninhados) — **ACEITÁVEL** (frontend lê apenas `id_solicitacao`)

### Prioridade Baixa
7. **Tratar erros com string detail em auth_service** — ✅ FEITO (`AUTH_INVALID_CREDENTIALS` 401 / `AUTH_INACTIVE_USER` 403, seção 8.10)

---

## Arquivos modificados nesta continuação

| Arquivo | Ação |
|---|---|
| `repositories/sync_repository.py` | **EDITADO** — `bump_revision_cursor()` atômico; `bump_revision()` delega |
| `repositories/solicitacao_repository.py` | **EDITADO** — bump dentro de `create_solicitacao` e `answer_pergunta` (antes do commit) |
| `repositories/admin_repository.py` | **EDITADO** — bump dentro de `transicionar_solicitacao`, `add_assistencia`, `update_assistencia_status` |
| `core/errors.py` | **EDITADO** — `make_error_response()` + `unhandled_exception_handler` (500) |
| `main.py` | **EDITADO** — registro do handler de `Exception` |
| `middleware/auth.py` | **EDITADO** — 401 agora usa envelope com `trace_id` |
| `services/auth_service.py` | **EDITADO** — códigos específicos 401/403 |
| `tests/test_revision_integration.py` | **CRIADO** — 9 testes (bump dentro das transações) |
| `tests/test_flow_cliente.py` | **CRIADO** — fluxo cliente completo |
| `tests/test_flow_admin.py` | **CRIADO** — fluxo admin completo |
| `tests/test_edge_cases.py` | **CRIADO** — 9 testes de envelope |
| `README.md` | **REESCRITO** — documentação alinhada à arquitetura atual (26 endpoints, JWT, SSE, erros, testes); rotas legadas `/post/*` omitidas e banner "em construção" removido |

---

## Atualização do README (OrbySos_api)

README (`OrbySos_api/README.md`) reescrito para refletir a arquitetura real após Fase 8:

- **Estrutura** atualizada: `core/`, `routers/`, `services/`, `repositories/`, `schemas/`, `middleware/`, `tests/`.
- **26 endpoints** documentados por módulo (auth, catálogos, cliente, admin, sync) com prefixo `/api/v1`, perfis exigidos e SSE.
- **Autenticação** por Bearer JWT + rotas públicas listadas.
- **Padrão de erro** com envelope `{error, trace_id}` e tabela de códigos (401/403/404/409/422/500).
- **Instalação/execução** com `.env.example` (DB + JWT), venv e referência ao `../database_estrutura.sql`.
- **Testes**: comando pytest (136) + smoke.
- **Roadmap**: itens concluídos marcados; pendências reais mantidas.
- Decisões do usuário: omitir legado `/api/v1/post/*` e remover banner "em construção".

---

## Como continuar (próximos passos)

1. Atualizar `docs/PLANO_IMPLEMENTACAO_API.md` → Fase 8 ✅ FEITA
2. Perguntar ao usuário antes de avançar
