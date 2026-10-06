# Fase 5 — Perguntas/Táxi — Análise Técnica (2026-09-15)

> **Status:** ✅ FEITA
> **Objetivo:** 1 endpoint de resposta à pergunta de táxi, replicando `TaxiQuestionService` do frontend (`OrbytSos/src/services/taxi-question-service.js`).

## Endpoint

| # | Método | Endpoint | Scope | Descrição |
|---|--------|----------|-------|-----------|
| 5.1 | `POST` | `/api/v1/perguntas/{id}/resposta` | CLIENTE_DONO | Responder pergunta de táxi |

## Regras de Negócio

- Verificar ownership (pergunta pertence a solicitação do cliente)
- `necessita_taxi=true`: exige `quantidade_passageiros >= 1`, `necessita_acessibilidade` boolean, `quantidade_criancas >= 0`, `quantidade_animais >= 0`, `bagagem` não vazio
- `necessita_taxi=false`: payload mínimo (`necessita_taxi: false` + `version`)
- Status muda de `PENDENTE` → `RESPONDIDA`

## Resultado

| # | Endpoint | Status | Detalhe |
|---|---|---|---|
| 5.1 | `POST /api/v1/perguntas/{id}/resposta` | 200 | Responde pergunta TAXI; status `PENDENTE`→`RESPONDIDA`, `version+1`, `data_resposta` setada |

## Regras replicadas do mock/frontend

- **Ownership:** pergunta precisa existir, pertencer a uma solicitação do próprio cliente (senão 404 `TAXI_QUESTION_NOT_FOUND`).
- **Já respondida** (`!== PENDENTE`) → 422 `TAXI_QUESTION_ALREADY_ANSWERED`.
- **Optimistic locking:** `version` do body ≠ `version` do banco → 409 `TAXI_QUESTION_VERSION_CONFLICT`.
- **Validação:** `necessita_taxi` bool; se `false`, payload mínimo; se `true`, exige `quantidade_passageiros >= 1`, `necessita_acessibilidade` bool, `quantidade_criancas >= 0`, `quantidade_animais >= 0`, `bagagem` não-vazio; `observacoes` opcional → 422 `VALIDATION_ERROR` com `fields`.
- **Ao responder `false`**, campos de táxi zerados para `NULL` no banco (conforme mock).
- **Resposta:** `{ "pergunta": { ...DTO questionDto } }`.

## Arquivos novos

| Arquivo | Conteúdo |
|---|---|
| `services/taxi_question_service.py` | `responder_pergunta` (ownership, locking, validação, UPDATE) + `QuestionError` |
| `schemas/client.py` | `PerguntaRespostaRequest` (novo) |
| `tests/test_taxi_question_service.py` | 9 testes unitários |
| `tests/test_taxi_question_routes.py` | 10 testes HTTP (TestClient, token forjado, repo mockado) |

## Arquivos modificados

| Arquivo | Mudança |
|---|---|
| `repositories/solicitacao_repository.py` | `pergunta_by_id`, `answer_pergunta` (UPDATE transacional com `version` conforme), `_id_status_pergunta_respondida` |
| `routers/client.py` | Rota `POST /perguntas/{pergunta_id}/resposta` com `require_perfil("CLIENTE")` |
| `database_estrutura.sql` | `tb_pergunta`: `bagagem` → `varchar(255)` (era `bool`), campos de táxi (`necessita_taxi`, `qtd_passageiros`, `necessita_acessibilidade`, `qtd_criancas`, `qtd_animais`, `observacoes`) → nullable/`varchar(255)` — decisão do usuário: **alinhar SQL ao contrato** |

## Decisões técnicas

- **Optimistic locking** implementado via `version` — comparação server-side com 409 em conflito.
- **DTO de pergunta preserva `null`** (sem cast `bool()`) para que o frontend distinga pendente de não-necessita (detalhe em Fase 8.1).

## Testes executados (evidence)

```
AUTH_SERVICE_TESTS_OK (10 testes)            regressão PASS
AUTH_ROUTES_TESTS_OK (8 testes)              regressão PASS
CATALOG_SERVICE_TESTS_OK (6 testes)          regressão PASS
CATALOG_ROUTES_TESTS_OK (5 testes)           regressão PASS
CLIENT_SERVICE_TESTS_OK (6 testes)           regressão PASS
CLIENT_ROUTES_TESTS_OK (11 testes)           regressão PASS
TAXI_QUESTION_SERVICE_TESTS_OK (9 testes)    PASS
TAXI_QUESTION_ROUTES_TESTS_OK (10 testes)    PASS
SMOKE_TEST_OK                                26 rotas /api/v1 (sem regressão)
```

## Pendências

- Validação contra MySQL real; DDL de `tb_pergunta` (bagagem/nulls) precisa ser aplicado ao banco.
- A criação da pergunta (GUINCHO→TAXI) acontece na Fase 6 (admin), portanto este endpoint depende de dados existentes.