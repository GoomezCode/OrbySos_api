# Fase 7 — Sync/SSE — Análise Técnica (2026-09-15)

## Endpoints

| # | Método | Endpoint | Scope | Descrição |
|---|--------|----------|-------|-----------|
| 7.1 | `GET` | `/api/v1/sync/version` | PÚBLICO (sem auth) | Versão atual do banco |
| 7.2 | `GET` | `/api/v1/sync/events` | PÚBLICO (sem auth) | SSE stream de mudanças |

## Contrato Exato (Frontend)

### GET /api/v1/sync/version

- **Autenticação:** nenhuma. Rota já listada em `middleware/auth.py` `PUBLIC_PREFIXES`.
- **Headers request:** `Accept: application/json`, `Cache-Control: no-store`.
- **Response 200 JSON:**
  ```json
  {"revision": 0, "updated_at": null}
  ```
  ou
  ```json
  {"revision": 7, "updated_at": "2026-08-18T10:00:00.000Z"}
  ```
- **Validação frontend:** `revision` **deve** ser `Number.isInteger` — se não for ou se a resposta não vier OK, o frontend lança `API_NETWORK_ERROR`.
- **Chamado por:** `api-runtime.js:#readVersion()` (l.63–80), no `initialize()`.

### GET /api/v1/sync/events (SSE)

- **Autenticação:** nenhuma.
- **Headers response:**
  - `Content-Type: text/event-stream; charset=utf-8`
  - `Cache-Control: no-cache, no-transform`
  - `Connection: keep-alive`
- **Frame (evento):** apenas `data:` (sem `event:` nem `id:`):
  ```
  data: {"revision": 7, "updated_at": "2026-08-18T10:00:00.000Z"}\n\n
  ```
- **Comportamento:**
  1. Enviar versão atual **imediatamente** ao conectar.
  2. Depois, a cada mutação (ou polling), enviar se `revision` mudou.
  3. No disconnect, `unsubscribe` (limpar recursos).
- **Dedupe do cliente:** `api-runtime.js` l.42 descarta frames com `revision === this.revision`.

## Referências no Código Frontend

| Arquivo | Linha | Trecho |
|---------|-------|--------|
| `repositories/api/api-runtime.js` | 65 | `${this.baseUrl}/sync/version` |
| `repositories/api/api-runtime.js` | 38 | `${this.baseUrl}/sync/events` |
| `repositories/api/api-runtime.js` | 42 | `if (!Number.isInteger(version?.revision) \|\| version.revision === this.revision) return` |
| `app.js` | 157–159 | `runtime.startStorageSync(...)` |
| `tests/unit/repositories/api-runtime.test.js` | 4 | `function versionResponse(revision)` — payload: `{revision, updated_at: ISO}` |
| `middleware/auth.py` | 15–16 | `"/api/v1/sync/version"`, `"/api/v1/sync/events"` já em `PUBLIC_PREFIXES` |

## Implementação Mock (Node.js — somente referência)

Arquivo: `server/mock-api/mock-api.js`
- Rotas (l.203–209): GET `/sync/version` → `database.getVersion()`, GET `/sync/events` → `#streamChanges()`.
- `getVersion()` (l.228–235): retorna `{revision: Number, updated_at: ISO}` de `orbyt_meta`.
- `#streamChanges()` (l.503–518): SSE headers, `response.write(`data: ${JSON.stringify(version)}\n\n`)`, `request.once('close', unsubscribe)`.
- Revision incrementa em cada transação de escrita (l.202–207).

## Estrutura MySQL Proposta

```sql
CREATE TABLE orbyt_meta (
    chave VARCHAR(64) PRIMARY KEY,
    valor VARCHAR(255) NOT NULL
);

-- Seeds iniciais
INSERT IGNORE INTO orbyt_meta (chave, valor) VALUES ('revision', '0');
```

- `updated_at` é opcional (retornado como `null` se inexistente).
- A tabela ainda **não existe** em `database_estrutura.sql`.

## Estrutura de Arquivos

| Arquivo | Ação | Conteúdo |
|---------|------|----------|
| `repositories/sync_repository.py` | Criar | `get_version()` → lê orbyt_meta, retorna dict com defaults |
| `routers/sync.py` | Criar | 2 endpoints (sem auth); SSE via `StreamingResponse` |
| `main.py` | Editar | Incluir sync router |
| `database_estrutura.sql` | Editar | Criar tabela `orbyt_meta` + seed |
| `tests/test_sync_routes.py` | Criar | Testes dos 2 endpoints |
| `tests/test_sync_service.py` | Criar | Testes da lógica de polling/dedupe |

## Decisões de Design

1. **Polling periódico (2s):** O plano sugere polling ou triggers + CREATE EVENT. Polling é mais simples e não requer permissões especiais. O frontend já deduplica por `revision`.
2. **Sem autenticação:** Ambos endpoints são públicos (já listados em `PUBLIC_PREFIXES`).
3. **`StreamingResponse`:** FastAPI/Starlette fornece `StreamingResponse(media_type="text/event-stream")` que seta headers SSE corretos.
4. **Testes:** Mock de `sync_repo.get_version()` — mesmo padrão das fases anteriores (sem MySQL real).
5. **Nenhum schema body:** Resposta simples, sem Pydantic models (apenas dict serializado via JSON).
