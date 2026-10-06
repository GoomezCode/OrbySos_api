# Fase 4 — Área do Cliente — Análise Técnica (2026-09-15)

> **Status:** ✅ FEITA
> **Objetivo:** 5 endpoints da área do cliente, com idempotência, transação e ownership por perfil CLIENTE.

## Endpoints

| # | Método | Endpoint | Scope | Descrição |
|---|--------|----------|-------|-----------|
| 4.1 | `GET` | `/api/v1/clientes/me` | CLIENTE | Perfil do cliente (PF/PJ) |
| 4.2 | `GET` | `/api/v1/clientes/me/apolices` | CLIENTE | Apólices com solicitação ativa |
| 4.3 | `POST` | `/api/v1/solicitacoes` | CLIENTE | Criar nova solicitação |
| 4.4 | `GET` | `/api/v1/clientes/me/solicitacoes` | CLIENTE | Lista de solicitações do cliente |
| 4.5 | `GET` | `/api/v1/solicitacoes/{id}` | CLIENTE_DONO | Detalhe da solicitação |

## Regras de Negócio — Criar Solicitação (4.3)

1. Validar body: `apolice_id`, `tipo_ocorrencia_id`, `descricao_evento`, `possui_feridos`, `risco_imediato`, `local.*`, `data_criacao_cliente`
2. Verificar `Idempotency-Key` header = `id_solicitacao_cliente` no body
3. Verificar apólice pertence ao cliente E está ativa
4. Verificar não há solicitação ativa para esta apólice (`ACTIVE_REQUEST_STATUSES`)
5. Gerar protocolo: `ORB-{YEAR}-{seq 6 dígitos}` sequencial
6. Calcular prioridade: `possui_feridos || risco_imediato` → `CRITICA`, senão `NORMAL`
7. Inserir `tb_solicitacao` + `tb_solicitacao_local` + `historico_status`
8. Retornar 201 com solicitação completa

## Resposta Esperada — Criar Solicitação (4.3)

```json
{
  "solicitacao": {
    "id_solicitacao": 58,
    "id_solicitacao_cliente": "550e8400-...",
    "numero_solicitacao": "ORB-2026-000058",
    "status": "RECEBIDA",
    "prioridade": "NORMAL",
    "version": 1,
    "cliente": { "id_pessoa": 1, "tipo_pessoa": "FISICA", "nome": "...", "cpf_mascarado": "***.444.***-**" },
    "apolice": { "id_apolice": 1009, "numero_apolice_mascarado": "ORB-****-1009", "status": "ATIVA" },
    "veiculo": { ... },
    "seguradora": { ... },
    "ocorrencia": { ... },
    "analista": null
  }
}
```

## Resultado

| # | Endpoint | Status | Detalhe |
|---|---|---|---|
| 4.1 | `GET /api/v1/clientes/me` | 200 | Perfil PF/PJ + contatos mascarados; 404 se pessoa não existe |
| 4.2 | `GET /api/v1/clientes/me/apolices` | 200 | Paginado; inclui `solicitacao_ativa` por apólice (5 status ativos) |
| 4.3 | `POST /api/v1/solicitacoes` | 201 | Idempotência via `Idempotency-Key` = `id_solicitacao_cliente`; transação (local + solicitação + histórico + update apólice); prioridade CRITICA/NORMAL; protocolo `ORB-{YEAR}-{seq}` |
| 4.4 | `GET /api/v1/clientes/me/solicitacoes` | 200 | Paginado; filtros `status` e `active_only`; ordenado por `data_recebimento DESC` |
| 4.5 | `GET /api/v1/solicitacoes/{id}` | 200 | Aggregate (solicitação + cliente + apólice + veículo + seguradora + ocorrência + analista + assistências + perguntas + histórico); 404 se não existe ou não pertence ao cliente |

## Arquivos novos

| Arquivo | Conteúdo |
|---|---|
| `schemas/client.py` | `LocalInput`, `SolicitacaoCreateRequest` (Pydantic v2) |
| `repositories/client_repository.py` | Queries: `person_by_id`, `pessoa_fisica/juridica_by_id`, `contatos_by_pessoa`, `policies_by_pessoa`, `active_request_by_policy`, `requests_by_pessoa(status, active_only)`, `occurrence_by_id`, `policy_by_id_for_pessoa`, `request_by_client_uuid`, `next_solicitacao_seq` |
| `repositories/solicitacao_repository.py` | Queries: `solicitacao_by_id` (aggregate JOINs), `assistencias_by_solicitacao`, `perguntas_by_solicitacao`, `historico_by_solicitacao`, `apolice_resumo_by_id`, `create_solicitacao` (transaction) |
| `services/client_service.py` | `get_perfil`, `list_apolices`, `criar_solicitacao` (idempotência, validações, transação), `list_solicitacoes`, `get_detalhe_solicitacao` |
| `routers/client.py` | 5 endpoints com `require_perfil("CLIENTE")` |
| `tests/test_client_service.py` | 6 testes unitários |
| `tests/test_client_routes.py` | 11 testes HTTP |

## Arquivos modificados

| Arquivo | Mudança |
|---|---|
| `core/deps.py` | Corrigido `require_perfil`: `session` agora usa `Depends(get_current_session)` (antes era default function, não resolvia pelo FastAPI) |
| `main.py` | Removidos imports de `apiMain` e `apiCliente` (rotas `/solicitacoes/{id}` e `/clientes/*` agora no novo `client_router`); incluído `client_router` |
| `api/apiAdmin.py` | Removido endpoint legado `GET /solicitacoes/{id}` (colidia com novo router) |
| `database_estrutura.sql` | Colunas `data_criacao_cliente`, `data_recebimento`, `data_decisao` de `DATE` para `DATETIME` (align contract ISO timestamps); colunas `origem`, `tipo`, `version` adicionadas a `tb_pergunta`; `data_resposta` tornada nullable |

## Decisões técnicas

- `tb_solicitacao_local` em vez de `tb_endereco` (bug legado em `database/select.py`).
- Protocolo `ORB-{YEAR}-{seq}`: seq = `MAX(id_solicitacao)+1`; `protocolo_solicitacao = numero_solicitacao` (NOT NULL UNIQUE).
- Datas DATE→DATETIME: preserva timestamp do contrato; leitura via helper `_iso()` → `YYYY-MM-DDTHH:MM:SSZ`.
- `data_criacao_cliente` recebida como string ISO do cliente, convertida para datetime no servidor.

## Testes executados (evidence)

```
AUTH_SERVICE_TESTS_OK (10 testes)      regressão PASS
AUTH_ROUTES_TESTS_OK (8 testes)        regressão PASS
CATALOG_SERVICE_TESTS_OK (6 testes)    regressão PASS
CATALOG_ROUTES_TESTS_OK (5 testes)     regressão PASS
CLIENT_SERVICE_TESTS_OK (6 testes)     PASS
CLIENT_ROUTES_TESTS_OK (11 testes)     PASS
SMOKE_TEST_OK                          25 rotas /api/v1 (sem regressão)
```

## Pendências

- Validação contra MySQL real (rotas novas + transação `create_solicitacao`); DDL de `tb_solicitacao` (DATE→DATETIME) e `tb_pergunta` (novas colunas) precisam ser aplicados ao banco.