# Fase 3 — Catálogos e Configurações — Análise Técnica (2026-09-15)

> **Status:** ✅ FEITA
> **Objetivo:** 2 endpoints de catálogo seguindo o DTO limpo do mock (`server/mock-api/mock-api.js`) e os contratos v2 de `public/data/api`.

## Endpoints

| # | Método | Endpoint | Scope | Descrição |
|---|--------|----------|-------|-----------|
| 3.1 | `GET` | `/api/v1/tipos-ocorrencia` | AUTENTICADO | Lista de ocorrências ativas |
| 3.2 | `GET` | `/api/v1/configuracoes/publicas` | AUTENTICADO | Configurações do app (país, emergência) |

## Resposta Esperada — Tipos de Ocorrência (3.1)

```json
{
  "items": [
    { "id_tipo_ocorrencia": 1, "codigo": "PANE_MECANICA", "nome": "Pane mecânica", "descricao": "...", "ativo": true, "ordem": 1 }
  ]
}
```

## Resultado

| # | Endpoint | Status 200 | Detalhe |
|---|---|---|---|
| 3.1 | `GET /api/v1/tipos-ocorrencia` | `{ "items": [ { id_tipo_ocorrencia, codigo, nome, descricao, ativo, ordem } ] }` | query opcional `ativo`; ordenado por `id_ocorrencia`; `ordem` = `id_ocorrencia` |
| 3.2 | `GET /api/v1/configuracoes/publicas` | `{ pais, mensagem, servicos }` | `servicos` vem da coluna `tb_configuracao.servicos_json` (JSON_ARRAY), sem fallback |

## Arquivos novos

| Arquivo | Conteúdo |
|---|---|
| `repositories/catalog_repository.py` | `find_occurrences(ativo: bool \| None)` (query condicional `WHERE ativo`) e `get_app_configuration()` (`LIMIT 1`) — mesmo padrão mockável de `user_repository` |
| `services/catalog_service.py` | `list_occurrence_types(ativo=None)` → `{"items"}`, cast `ativo` p/ `bool`, `ordem=id`; `get_public_configurations()` faz `json.loads` do `servicos_json`; erros de repositório/JSON → 500 |
| `tests/test_catalog_service.py` | 6 testes unitários (mock do repositório) |
| `tests/test_catalog_routes.py` | 5 testes HTTP (TestClient, token forjado, repositório mockado) |

## Arquivos modificados

| Arquivo | Mudança |
|---|---|
| `api/apiMain.py` | Removidos `GET /tipos-ocorrencia` e `GET /configuracoes/publicas` (legados, envelope `schema_version/response`). Mantido `GET /solicitacoes/{id}` |
| `main.py` | Incluído `catalogs.router` sob `/api/v1` |
| `database_estrutura.sql` | Seed de `tb_configuracao.servicos_json` alterado de `JSON_OBJECT('transporte', TRUE, 'emergencia', TRUE)` para `JSON_ARRAY` com `{codigo, nome, telefone}` (SAMU 192, Bombeiros 193, Polícia 190), conforme decisão do usuário: **apenas seed no banco, sem fallback** |

## Decisões técnicas

- **Scope `AUTENTICADO`** (qualquer perfil): as duas rotas dependem de `get_current_session`; o middleware já devolve 401 sem token.
- **DTO limpo** (`items`/`pais` no topo), **não** o envelope `schema_version/request_query/response` do legado — é o que o `unwrapItems(payload)` do frontend parseia (`api-mappers.js`) e o que o mock já devolve.
- **Sem fallback decode de `servicos_json`:** se o conteúdo não bater com o contrato (ou a tabela estiver vazia), a API responde 500 — forçando consistência com o seed.

## Testes executados (evidence)

```
CATALOG_SERVICE_TESTS_OK (6 testes)   PASS
CATALOG_ROUTES_TESTS_OK (5 testes)    PASS
AUTH_SERVICE_TESTS_OK (10 testes)     regressão PASS
AUTH_ROUTES_TESTS_OK (8 testes)       regressão PASS
SMOKE_TEST_OK                         25 rotas /api/v1 (sem regressão)
```

## Pendências

- Validação contra MySQL real (rodar o novo `INSERT` de `tb_configuracao`) requer banco `orbyt` ativo. Em bancos existentes, reexecutar o seed da `tb_configuracao` para o novo formato de `servicos_json`.