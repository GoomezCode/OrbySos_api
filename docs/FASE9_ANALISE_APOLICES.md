# FASE 9 — Análise: CRUD Administrativo de Apólice

> **Data:** 2026-09-15
> **Status:** ✅ FEITA
> **Objetivo:** Implementar CRUD administrativo de apólice (sem DELETE físico), com otimistic locking e isolamento por seguradora, conforme decisão do usuário.
> **Fase/pendência de origem:** Roadmap do `OrbySos_api/README.md` → "Rotas de `apólice` (CRUD completo)".

---

## 1. Escopo decidido com o usuário

- **CRUD administrativo** (perfil `ANALISTA`), restrito às seguradoras vinculadas ao analista (`tb_analista_seguradora`).
- **Sem DELETE físico**: transições de status (`ATIVA`, `SUSPENSA`, `INATIVA`) por `POST .../status`.
- **Otimistic locking**: `version` obrigatório em `PATCH` e `POST /status`; divergência → `409 POLICY_VERSION_CONFLICT`.
- **Mascaramento**: `numero_apolice` é armazenado completo, exposto como `ORB-****-{last4}` (padrão dos demais mascaramentos).

## 2. Endpoints adicionados (5)

| Método | Rota | Perfil | Comportamento |
|---|---|---|---|
| `GET` | `/api/v1/admin/apolices` | ANALISTA | Lista paginada + filtros (`status`, `numero_apolice`, `pessoa`, `placa`, `seguradora`) e `sort` (whitelist) |
| `GET` | `/api/v1/admin/apolices/{apolice_id}` | ANALISTA | Detalhe completo (cliente + veículo + seguradora + contatos) |
| `POST` | `/api/v1/admin/apolices` | ANALISTA | Criar (201); valida seguradora do analista e `data_fim > data_inicio` |
| `PATCH` | `/api/v1/admin/apolices/{apolice_id}` | ANALISTA | Atualizar campos (`version` obrigatório) |
| `POST` | `/api/v1/admin/apolices/{apolice_id}/status` | ANALISTA | Transição de status (`version` obrigatório) |

## 3. Arquivos criados/modificados

| Arquivo | Conteúdo |
|---|---|
| `OrbySos_api/schemas/apolice.py` (novo) | `ApoliceCreateRequest`, `ApoliceUpdateRequest` (campos opcionais + `version`), `ApoliceStatusRequest` |
| `OrbySos_api/repositories/apolice_repository.py` (novo) | `_APOLICE_BASE_SELECT` (JOINs cliente/veículo/seguradora), `find_apolices`, `apolice_by_id`, `create_apolice`, `update_apolice`, `update_apolice_status`; máscara `ORB-****-{last4}`; `_parse_sort` com whitelist de colunas |
| `OrbySos_api/services/apolice_service.py` (novo) | `list_apolices`, `get_detalhe`, `criar_apolice`, `atualizar_apolice`, `alterar_status_apolice`; `ApoliceError`; `_require_visible` (404 fora da seguradora) |
| `OrbySos_api/routers/admin.py` (modificado) | +5 rotas registradas com `require_perfil("ANALISTA")` |

## 4. Decisões técnicas

- **Isolamento por seguradora**: em listagem, o repository recebe o `set` de IDs das seguradoras do analista; no detalhe, `_require_visible` retorna `404 POLICY_NOT_FOUND` para apólices de outras seguradoras (não vaza existência).
- **Otimistic locking**: `update_apolice`/`update_apolice_status` usam `UPDATE ... WHERE versao = %s` + `bump_revision_cursor` na mesma transação; se 0 linhas afetadas → serviço devolve `409 POLICY_VERSION_CONFLICT` com o `current` da apólice.
- **Transições de status**: validadas no serviço (`ATIVA/SUSPENSA/INATIVA`) e no banco (`INVALID_POLICY_STATUS`); status igual ao atual → 409.
- **Máscara**: `numero_apolice` completo é gravado em `tb_apolice`; o DTO sempre expõe `numero_apolice_mascarado`.
- **Paginação**: envelope `{items, pagination}` no padrão das demais listas do admin (page ≥ 1, page_size clamp 100).

## 5. Testes executados (evidence)

```
tests/test_apolice_service.py  →  15 testes unitários (mocks do repositório)  PASS
tests/test_apolice_routes.py   →  11 testes HTTP (TestClient + token forjado)  PASS
tests/ suíte completa           →  162 passed (2 warnings)
tests/smoke_phase1.py           →  SMOKE_TEST_OK
```

## 6. Pendência

- Validação ponta-a-ponta contra MySQL real (não há listener 3306 no ambiente de desenvolvimento).