# Fase 8.1 — Validação de Contratos JSON (Frontend vs API Python)

> **Data:** 2026-09-15
> **Escopo:** Comparar os contratos em `OrbytSos/public/data/api/*.json` (SOMENTE LEITURA) com os DTOs implementados em `OrbySos_api/`.
> **Método:** Leitura integral de cada contrato + routers/services/schemas. Nada foi modificado.

## Arquivos de contrato encontrados (17)

1. `OrbytSos/public/data/api/tipos-ocorrencia.json`
2. `OrbytSos/public/data/api/tipos-assistencia.json`
3. `OrbytSos/public/data/api/solicitacoes-cliente.json`
4. `OrbytSos/public/data/api/solicitacao-detalhe-cliente.json`
5. `OrbytSos/public/data/api/solicitacao-criar.json`
6. `OrbytSos/public/data/api/pergunta-taxi-responder.json`
7. `OrbytSos/public/data/api/erro-padrao.json`
8. `OrbytSos/public/data/api/endpoint-catalog.json`
9. `OrbytSos/public/data/api/configuracoes-publicas.json`
10. `OrbytSos/public/data/api/cliente.json`
11. `OrbytSos/public/data/api/auth.json`
12. `OrbytSos/public/data/api/apolices.json`
13. `OrbytSos/public/data/api/admin-solicitacoes.json`
14. `OrbytSos/public/data/api/admin-solicitacao-detalhe.json`
15. `OrbytSos/public/data/api/admin-dashboard.json`
16. `OrbytSos/public/data/api/admin-comandos.json`
17. `OrbytSos/public/data/api/admin-assistencias.json`

## Nota sobre documentação

As Fases 4 e 5 estão registradas em `docs/PLANO_IMPLEMENTACAO_API.md` (seções 6 e 7) e possuem suas próprias docs/logs: `docs/FASE4_ANALISE_CLIENTE.md` e `docs/FASE5_ANALISE_PERGUNTAS_TAXI.md`. O DTO real foi extraído de `schemas/*.py` e `services/*.py`.

---

## Tabela de Comparação

| # | Arquivo Contrato | Endpoint | Status | Divergências |
|---|---|---|---|---|
| 1 | `auth.json` | POST `/auth/clientes/login`, POST `/auth/analistas/login`, GET `/auth/me`, POST `/auth/logout` | **CONFORME** | — |
| 2 | `cliente.json` | GET `/clientes/me` | **CONFORME** | — |
| 3 | `apolices.json` | GET `/clientes/me/apolices` | **DIVERGENTE** | Query param `status` não aceito pela API |
| 4 | `configuracoes-publicas.json` | GET `/configuracoes/publicas` | **CONFORME** | — |
| 5 | `tipos-ocorrencia.json` | GET `/tipos-ocorrencia` | **CONFORME** | — |
| 6 | `tipos-assistencia.json` | GET `/admin/tipos-assistencia` | **CONFORME** | Query `ativo` não aceita; sempre filtra ativos |
| 7 | `solicitacoes-cliente.json` | GET `/clientes/me/solicitacoes` | **CONFORME** | — |
| 8 | `solicitacao-detalhe-cliente.json` | GET `/solicitacoes/{solicitacao_id}` | **DIVERGENTE** | `perguntas[].necessita_taxi/necessita_acessibilidade/bagagem` com cast `bool()` |
| 9 | `solicitacao-criar.json` | POST `/solicitacoes` | **DIVERGENTE** | Estrutura de response completamente diferente |
| 10 | `pergunta-taxi-responder.json` | POST `/perguntas/{pergunta_id}/resposta` | **CONFORME** | — |
| 11 | `erro-padrao.json` | Todos (formato de erro) | **DIVERGENTE** | Envelope `{detail}` vs `{error, trace_id}` |
| 12 | `admin-solicitacoes.json` | GET `/admin/solicitacoes` | **DIVERGENTE** | Campos extras + query `sort` não aceita |
| 13 | `admin-solicitacao-detalhe.json` | GET `/admin/solicitacoes/{solicitacao_id}` | **DIVERGENTE** | `analista` extra dentro de `solicitacao` |
| 14 | `admin-dashboard.json` | GET `/admin/dashboard` | **DIVERGENTE** | Items da fila com campos extras |
| 15 | `admin-comandos.json` | POST `/admin/solicitacoes/{id}/assumir\|confirmar\|recusar\|iniciar-atendimento\|registrar-prestador-acionado\|concluir` | **DIVERGENTE** | Response retorna aggregate completo vs objeto mínimo |
| 16 | `admin-assistencias.json` | POST `/admin/solicitacoes/{id}/assistencias`, PATCH `/admin/solicitacao-assistencias/{id}` | **DIVERGENTE** | `pergunta_criada` e `solicitacao` com campos extras |
| 17 | `endpoint-catalog.json` | Todos (24 endpoints) | **CONFORME** | Todos os endpoints existem; status codes ok |

---

## Detalhamento por Contrato

### 1. `auth.json` — CONFORME

| Subcontrato | Contrato (Frontend) | API Python | Resultado |
|---|---|---|---|
| `cliente_login.request` | `{cpf, senha}` | `ClienteLoginRequest{cpf: str, senha: str}` | ✓ |
| `cliente_login.response` | `{access_token, token_type, expires_in, session:{id_usuario, id_pessoa, perfil, nome_exibicao, seguradora:null, seguradoras:[]}}` | `AuthEnvelope` + `SessaoInfo` | ✓ |
| `analista_login.request` | `{login, senha}` | `AnalistaLoginRequest` | ✓ |
| `analista_login.response` | idem com `seguradora:{id_pj,nome_fantasia}` e `seguradoras:[...]` | idem | ✓ |
| `sessao_atual` | `{session:{...}}` | `GET /auth/me` → `{"session": session}` | ✓ |
| `logout` | 204 sem corpo | `POST /auth/logout` → 204 | ✓ |

Observação menor: contrato do login `sessao_atual` vem sem envelope; o router `/auth/me` retorna exatamente `{"session": ...}`. OK.

### 2. `cliente.json` — CONFORME

| Variante | Contrato | API `get_perfil` | Resultado |
|---|---|---|---|
| `FISICA` | `{id_pessoa, tipo_pessoa, nome, cpf_mascarado, data_nascimento, contatos:[{tipo, valor_mascarado, principal}]}` | idêntico | ✓ |
| `JURIDICA` | `{id_pessoa, tipo_pessoa, razao_social, nome_fantasia, cnpj_mascarado, contatos:[...]}` | idêntico | ✓ |

### 3. `apolices.json` — DIVERGENTE

- **Response `items[]`**: estrutura idêntica (`id_apolice, numero_apolice_mascarado, data_inicio, data_fim, status, possui_solicitacao_ativa, cliente, seguradora{incl. contatos}, veiculo, solicitacao_ativa`) + `pagination` idêntico. ✓
- **DIVERGÊNCIA:** `request_query: {status: "ATIVA"}` e `endpoint-catalog.json` declaram `query: ["status"]`, mas o router `client.py:cliente_apolices` **não declara nem aplica** o parâmetro `status`. A API aceita apenas `page` e `page_size`.

### 4. `configuracoes-publicas.json` — CONFORME

`{pais, mensagem, servicos:[{codigo, nome, telefone}]}` — idêntico ao `catalog_service.get_public_configurations`.

### 5. `tipos-ocorrencia.json` — CONFORME

`{items:[{id_tipo_ocorrencia, codigo, nome, descricao, ativo, ordem}]}` — idêntico. `request_query.ativo` implementado via `Query(ativo: bool | None)`.

### 6. `tipos-assistencia.json` — CONFORME

`{items:[{id_tipo_assistencia, codigo, nome, descricao, ativo}]}` — idêntico ao `admin_service.list_tipos_assistencia`.
O contrato e o catálogo declaram `query: ["ativo"]`; a rota `/admin/tipos-assistencia` **não aceita** o param, mas o service **sempre** lista apenas ativos (`WHERE ativo = 1`), o que equivale a `ativo=true`. Divergência irrelevante (comportamento equivalente).

### 7. `solicitacoes-cliente.json` — CONFORME

Item idêntico ao `client_service.list_solicitacoes` + `pagination` idêntico. Query `status`, `active_only`, `page`, `page_size` implementados.

### 8. `solicitacao-detalhe-cliente.json` — DIVERGENTE

- `solicitacao, cliente, apolice, veiculo, seguradora{com contatos}, ocorrencia{com descricao}, analista, assistencias, historico` — ✓ todos idênticos.
- **DIVERGÊNCIA em `perguntas[]`** (`client_service.get_detalhe_solicitacao`, linhas 352–357):
  - Contrato: `necessita_taxi: null`, `necessita_acessibilidade: null`, `bagagem: null` (ex. pergunta pendente).
  - API: `"necessita_taxi": bool(p["necessita_taxi"])` → `null` vira `false`; `"necessita_acessibilidade": bool(...)` → `false`; `"bagagem": bool(...)` → `false` (e quando respondida, o contrato tem `bagagem` como **string**; a API devolve **bool**).
  - Impacto: o frontend não consegue distinguir "pendente (null)" de "não necessita (false)" e perde o texto de bagagem.

### 9. `solicitacao-criar.json` — DIVERGENTE (estrutura)

**Contrato — Response (201):**
```json
{
  "solicitacao": {
    "...core...", 
    "cliente": {...}, "apolice": {id_apolice, numero_apolice_mascarado, status},
    "veiculo": {id_veiculo, marca, modelo, ano_modelo, placa_mascarada},
    "seguradora": {id_pj, nome_fantasia},
    "ocorrencia": {id_tipo_ocorrencia, codigo, nome},
    "analista": null
  }
}
```
- Agregados **aninhados dentro** de `solicitacao`.
- `apolice` ENXUTA (sem `data_inicio/data_fim`).
- `veiculo` ENXUTO (sem `versao/ano_fabricacao/blindado`).
- `seguradora` SEM `contatos`.
- `ocorrencia` SEM `descricao`.
- SEM `assistencias`, `perguntas`, `historico`.

**API** (`client_service.criar_solicitacao` retorna `get_detalhe_solicitacao`):
```json
{
  "solicitacao": {"...core..."},        // agregados NÃO aninhados
  "cliente": {...}, "apolice": {...com data_inicio,data_fim...},
  "veiculo": {...com versao,ano_fabricacao,blindado...},
  "seguradora": {...com contatos...},
  "ocorrencia": {...com descricao...},
  "analista": null,
  "assistencias": [...], "perguntas": [...], "historico": [...]
}
```
- **Divergência 1:** agregados são **irmãos** de `solicitacao`, não aninhados dentro dela.
- **Divergência 2:** `apolice/veiculo/seguradora/ocorrencia` retornam campos **extras** em relação ao contrato de criação.
- **Divergência 3:** API inclui `assistencias`, `perguntas` e `historico` que o contrato de criação **não prevê**.

Request e header `Idempotency-Key` — ✓ compatíveis (`SolicitacaoCreateRequest` + validação `id_solicitacao_cliente == Idempotency-Key`).

### 10. `pergunta-taxi-responder.json` — CONFORME

Request `{necessita_taxi, quantidade_passageiros, necessita_acessibilidade, quantidade_criancas, quantidade_animais, bagagem, observacoes, version}` — ✓ `PerguntaRespostaRequest`.
Response `{pergunta: {id_pergunta, origem, tipo, status, ..., version}}` — ✓ `taxi_question_service._pergunta_dto` (SEM cast `bool`, preserva `null`).

### 11. `erro-padrao.json` — DIVERGENTE (envelope)

**Contrato:**
```json
{ "error": { "code": "...", "message": "...", "fields": [{"field","message"}] }, "trace_id": "..." }
```
**API:** `HTTPException(detail=...)` — FastAPI entrega `{"detail": {...}}` (ou `{"detail": "string"}` nos erros de `deps/auth`). Não há wrapper `error`, não há `trace_id`, e os códigos variam (ex.: `deps.py` usa `FORBIDDEN`/`UNAUTHORIZED` em vez de `AUTH_FORBIDDEN`; `auth_service` usa string simples). Nenhum handler global de exceção foi registrado em `main.py`.

### 12. `admin-solicitacoes.json` — DIVERGENTE

- **Query:** contrato e catálogo declaram `sort` (ex.: `data_recebimento:desc`); o router `admin.solicitacoes` **não tem** parâmetro `sort` (ordenção fixa `ORDER BY data_recebimento DESC, id_solicitacao DESC`). Demais filtros ✓.
- **Campos extras por item** (via `_aggregate_dto`):
  - `id_solicitacao_cliente`, `local{...}`, `data_criacao_cliente` — não constam no item do contrato.
  - `apolice` → contrato: `{id_apolice, numero_apolice_mascarado}`; API adiciona `data_inicio, data_fim, status`.
  - `veiculo` → contrato: `{id_veiculo, marca, modelo, ano_modelo, placa_mascarada}`; API adiciona `versao, ano_fabricacao, blindado`.
  - `ocorrencia` → contrato: `{id_tipo_ocorrencia, codigo, nome}`; API adiciona `descricao`.

### 13. `admin-solicitacao-detalhe.json` — DIVERGENTE

- Estrutura geral ✓ (solicitacao, cliente, apolice, veiculo, seguradora SEM contatos ✓, ocorrencia, analista, assistencias, perguntas, historico, tipos_assistencia_disponiveis).
- **Divergência:** `_solicitacao_core_dto` inclui `"analista": {...}` **dentro** do objeto `solicitacao` (linha 205 do admin_service). No contrato, `solicitacao` é enxuto (até `version`) e `analista` existe apenas como campo top-level. Campo extra.

### 14. `admin-dashboard.json` — DIVERGENTE

- `metricas` ✓ idêntico (6 chaves com mesmos critérios).
- `fila_prioritaria.items` — mesmas divergências do item de `admin-solicitacoes.json` (campos extras: id_solicitacao_cliente, local, data_criacao_cliente, descricao, apolice/veiculo/ocorrencia com campos extras).

### 15. `admin-comandos.json` — DIVERGENTE

**Contrato (resposta mínima):**
- `assumir`: `{solicitacao:{id_solicitacao, numero_solicitacao, status, prioridade, version, analista}}`
- `confirmar`/`recusar`: idem + `data_decisao`, `motivo_recusa`
- `iniciar_atendimento`/`registrar_prestador_acionado`/`concluir`: `{solicitacao:{id_solicitacao, numero_solicitacao, status, version, analista}}`

**API:** todos retornam `{"solicitacao": _aggregate_dto(...)}` — o **aggregate completo** (id_solicitacao_cliente, descricao_evento, possui_feridos, risco_imediato, prioridade, local, data_criacao_cliente, data_recebimento, data_decisao, motivo_recusa, + cliente/apolice/veiculo/seguradora/ocorrencia aninhados). Mutíssimos campos extras vs o sub-object mínimo do contrato.

Requests ✓ compatíveis (`VersionRequest`, `ConfirmarRequest{version,comentario}`, `RecusarRequest{version,motivo_recusa}`, `OperacaoRequest{version,comentario}`).

### 16. `admin-assistencias.json` — DIVERGENTE

- **`incluir` (`POST /admin/solicitacoes/{id}/assistencias`, 201):**
  - `assistencia` ✓ idêntico.
  - `pergunta_criada` → contrato: `{id_pergunta, origem, tipo, status, necessita_taxi, data_criacao, data_resposta, version}`; API (`_pergunta_dto`) devolve **+6 campos extras**: `quantidade_passageiros, necessita_acessibilidade, quantidade_criancas, quantidade_animais, bagagem, observacoes`.
  - `solicitacao` → contrato: `{id_solicitacao, numero_solicitacao, status, version}`; API devolve **aggregate completo** (extra: id_solicitacao_cliente, descricao_evento, possuí_feridos, risco_imediato, prioridade, local, data_criacao_cliente, data_recebimento, data_decisao, motivo_recusa, analista, cliente, apolice, veiculo, seguradora, ocorrencia).
- **`alterar_status` (PATCH, 200):** `{assistencia: {...}}` ✓ idêntico.
- **`remover_logicamente`:** não é endpoint separado (usa o mesmo PATCH com status REMOVIDA) — ✓.

### 17. `endpoint-catalog.json` — CONFORME (presença de endpoints)

Todos os 24 endpoints do catálogo existem na API com mesmos métodos, rotas, scopes e `success_status` (200 / 201 para criar & incluir assistência / 204 para logout). Divergências de query param (`status` em apólices, `sort` em admin) já listadas nos itens 3 e 12.

---

## Resumo Executivo

- **CONFORMES (8):** auth, cliente, configuracoes-publicas, tipos-ocorrencia, tipos-assistencia, solicitacoes-cliente, pergunta-taxi-responder, endpoint-catalog.
- **DIVERGENTES (9):** apolices (query `status`), solicitacao-detalhe-cliente (`bool()` em perguntas), solicitacao-criar (estrutura do response), erro-padrao (envelope), admin-solicitacoes (campos extras + `sort`), admin-solicitacao-detalhe (`analista` extra), admin-dashboard (campos extras), admin-comandos (aggregate vs mínimo), admin-assistencias (campos extras em `pergunta_criada`/`solicitacao`).

## Próximos passos sugeridos

1. Decidir se os "campos extras" (superset) são aceitáveis ou se a API deve emitir DTOs minimalistas por endpoint (ex.: DTO de criação específico, DTO de comando enxuto).
2. Corrigir o cast `bool()` em `perguntas[]` do detalhe do cliente (preservar `null` e string `bagagem`).
3. Adicionar query `status` em `/clientes/me/apolices` e `sort` em `/admin/solicitacoes`.
4. Implementar handler global de erro no padrão `{error: {...}, trace_id}` (FastAPI `exception_handler`).
