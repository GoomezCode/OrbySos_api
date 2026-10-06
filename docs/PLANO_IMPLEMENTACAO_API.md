# Plano de Implementação — API OrbytSos

> **Data:** 2026-09-14
> **Status:** Planejamento
> **Objetivo:** Reestruturar a API FastAPI para atender integralmente ao frontend já existente (31 endpoints, autenticação JWT, machine de estados, optimistic locking, SSE sync).

---

## 1. Panorama da Gap (Frontend vs API Atual)

| Aspecto | Frontend Espera | API Atual |
|---|---|---|
| Base URL | `/api/v1/*` | `/` (sem prefixo) |
| Autenticação | JWT Bearer + 2 login flows (cliente/analista) | Stub `/me` sem auth |
| Endpoints | 26 (REST + SSE) | ~12 (estrutura diferente) |
| Response shape | Envelope `items[]` + `pagination` | Shapes ad-hoc com índices numéricos |
| DB Schema | SQLite com 28 tabelas (tabela `tb_solicitacao_local`, `tb_configuracao`, `tb_historico_status` com `nome_responsavel`, etc.) | MySQL com 20 tabelas (faltam tabelas, colunas divergentes) |
| Status codes | `RECEBIDA`, `EM_ANALISE`, `CONFIRMADA`, `RECUSADA_SEM_COBERTURA`, `EM_ATENDIMENTO`, `PRESTADOR_ACIONADO`, `CONCLUIDA` | Códigos genéricos por entidade |
| Concurrency | Optimistic locking (`version`) em cada write | Sem controle |
| SSE/Sync | `/sync/version` + `/sync/events` (SSE) | Não existe |
| Máquina de estados | Transições validadas server-side | Não implementada |

---

## 2. Fase 0 — Correções Críticas do Schema MySQL — ✅ FEITA (2026-09-14)

> 📄 Detalhes técnicos completos em `docs/FASE0_ANALISE_SCHEMA_MYSQL.md`.

**Objetivo:** O `database_estrutura.sql` ficar 100% compatível com o que o frontend espera.

| # | Ação | Detalhe |
|---|---|---|
| 0.1 | Corrigir `tb_analista_seguradora` | Converter de sintaxe SQLite para MySQL: `AUTO_INCREMENT` no lugar de `AUTOINCREMENT`, remover `CHECK (ativo IN (0, 1))`, `CURRENT_TIMESTAMP` → `DEFAULT CURRENT_TIMESTAMP` |
| 0.2 | Corrigir `tb_cep.cep` | `int` → `varchar(8)` — CEPs com zeros à esquerda são truncados em `int` |
| 0.3 | Criar `tb_solicitacao_local` | Tabela separada: `id_local PK`, `endereco`, `numero_local`, `cidade`, `estado(2)`, `ponto_referencia`. A `tb_solicitacao` passa a ter `fk_local` apontando para esta tabela |
| 0.4 | Adicionar colunas em `tb_user` | `nome_exibicao varchar(100)`, `email varchar(150)`, `fk_seguradora int NULL` (FK → `tb_pessoa_juridica`) |
| 0.5 | Adicionar coluna em `tb_pessoa_fisica` | `cpf_mascarado varchar(20)` |
| 0.6 | Adicionar coluna em `tb_pessoa_juridica` | `cnpj_mascarado varchar(25)` |
| 0.7 | Adicionar coluna em `tb_veiculo` | `placa_mascarada varchar(10)` |
| 0.8 | Adicionar colunas em `tb_apolice` | `numero_apolice_mascarado varchar(50)`, `possui_solicitacao_ativa boolean DEFAULT false` |
| 0.9 | Renomear `tb_tpAssistencia` → `tb_tipo_assistencia` | Padronizar nomes com o frontend |
| 0.10 | Criar `tb_configuracao` | `id_configuracao PK`, `pais varchar(2)`, `mensagem text`, `servicos_json json` |
| 0.11 | Ajustar `tb_solicitacao` | Adicionar `numero_solicitacao varchar(100) UNIQUE`, separar local para `tb_solicitacao_local`, garantir `version int NOT NULL DEFAULT 1` |
| 0.12 | Ajustar `tb_historico_status` | Adicionar `nome_responsavel varchar(100)`, `data_status datetime` |
| 0.13 | Corrigir FK em `tb_pergunta` | FK deve apontar para `tb_solicitacao(id_solicitacao)`, não `tb_assistencia` |
| 0.14 | Criar índices de performance | Ver item 0.15 abaixo |

### 0.15 — Índices de Performance

```sql
-- Admin list query (seguradora + status + prioridade + data)
CREATE INDEX idx_solicitacao_seguradora_status
  ON tb_solicitacao (fk_seguradora, fk_status, prioridade, data_recebimento);

-- Client request listing (pessoa + data desc)
CREATE INDEX idx_solicitacao_pessoa_data
  ON tb_solicitacao (fk_pessoa, data_recebimento DESC);

-- Active request check per policy
CREATE INDEX idx_solicitacao_apolice
  ON tb_solicitacao (fk_apolice);

-- History ordering
CREATE INDEX idx_historico_solicitacao_data
  ON historico_status (fk_solicitacao, data_status);

-- Assistance per request
CREATE INDEX idx_assistencia_solicitacao
  ON tb_solicitacao_assistencia (fk_solicitacao, status);

-- Analyst-to-insurer lookup
CREATE INDEX idx_analista_seguradora_analista
  ON tb_analista_seguradora (fk_analista, ativo);

-- Insurer-to-analyst lookup
CREATE INDEX idx_analista_seguradora_seguradora
  ON tb_analista_seguradora (fk_seguradora, ativo);
```

### 0.16 — Atualizar INSERTs de Status

```sql
-- Status de SOLICITACAO
INSERT INTO tb_status (codigo, rotulo, entidade) VALUES
  ('RECEBIDA', 'Recebida', 'SOLICITACAO'),
  ('EM_ANALISE', 'Em análise', 'SOLICITACAO'),
  ('CONFIRMADA', 'Confirmada', 'SOLICITACAO'),
  ('RECUSADA_SEM_COBERTURA', 'Recusada sem cobertura', 'SOLICITACAO'),
  ('EM_ATENDIMENTO', 'Em atendimento', 'SOLICITACAO'),
  ('PRESTADOR_ACIONADO', 'Prestador acionado', 'SOLICITACAO'),
  ('CONCLUIDA', 'Concluída', 'SOLICITACAO');

-- Status de ASSISTENCIA (solicitacao_assistencia)
INSERT INTO tb_status (codigo, rotulo, entidade) VALUES
  ('INCLUIDA', 'Incluída', 'ASSISTENCIA_SOLICITACAO'),
  ('PRESTADOR_ACIONADO', 'Prestador acionado', 'ASSISTENCIA_SOLICITACAO'),
  ('REMOVIDA', 'Removida', 'ASSISTENCIA_SOLICITACAO');

-- Status de PERGUNTA
INSERT INTO tb_status (codigo, rotulo, entidade) VALUES
  ('PENDENTE', 'Pendente', 'PERGUNTA'),
  ('RESPONDIDA', 'Respondida', 'PERGUNTA');
```

**Arquivo afetado:** `database_estrutura.sql` ✅ **Concluído — todas as 16 ações (0.1–0.16) aplicadas:** `tb_analista_seguradora` migrada para sintaxe MySQL; `tb_cep.cep` e `tb_endereco.cep` → `varchar(8)`; criadas `tb_solicitacao_local` e `tb_configuracao`; colunas de mascaramento (`cpf_mascarado`, `cnpj_mascarado`, `placa_mascarada`, `numero_apolice_mascarado`), `possui_solicitacao_ativa`, `nome_exibicao`/`email`/`fk_seguradora` em `tb_user`; `tb_tpAssistencia` → `tb_tipo_assistencia` (refs corrigidas); `numero_solicitacao UNIQUE`, `version DEFAULT 1`, `fk_analista_responsavel` nullable e `fk_local → tb_solicitacao_local` em `tb_solicitacao`; `nome_responsavel`/`data_status datetime` em `tb_historico_status`; FK de `tb_pergunta` corrigida para `tb_solicitacao`; 7 índices criados; INSERTs de status (SOLICITACAO, ASSISTENCIA_SOLICITACAO, PERGUNTA) e seed de `tb_configuracao` adicionados.

---

## 3. Fase 1 — Infraestrutura da API — ✅ FEITA (2026-09-15)

> 📄 Detalhes técnicos completos em `docs/FASE1_ANALISE_INFRAESTRUTURA.md`.

**Objetivo:** Base sólida: prefixo, pooling, JWT, middleware, dependências.

| # | Ação | Arquivo |
|---|---|---|
| 1.1 | Criar estrutura de pastas | `OrbySos_api/core/`, `routers/`, `services/`, `repositories/`, `middleware/`, `schemas/` |
| 1.2 | Configurar prefixo `/api/v1` | `main.py` — todos os routers com `prefix="/api/v1"` |
| 1.3 | Implementar connection pooling | `core/database.py` — `mysql.connector.pooling.MySQLConnectionPool` |
| 1.4 | Configurar JWT | `core/security.py` — `python-jose` para criar/validar tokens |
| 1.5 | Criar middleware de auth | `middleware/auth.py` — extrair Bearer token, validar, injetar session |
| 1.6 | Criar dependências FastAPI | `core/deps.py` — `get_current_session()`, `require_profile()`, `require_ownership()` |
| 1.7 | Configurar `.env` | Adicionar `JWT_SECRET`, `JWT_ALGORITHM=HS256`, `JWT_EXPIRE_SECONDS=3600` |
| 1.8 | Atualizar `requirements.txt` | Adicionar `python-jose[cryptography]`, `passlib[bcrypt]` |

### Estrutura de Pastas Resultante

```
OrbySos_api/
├── main.py
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── config.py          # Settings via pydantic-settings
│   ├── database.py         # Connection pool singleton
│   ├── security.py         # JWT create/decode, password hash
│   └── deps.py             # FastAPI dependencies
├── middleware/
│   ├── __init__.py
│   └── auth.py             # Auth middleware
├── routers/
│   ├── __init__.py
│   ├── auth.py             # /auth/*
│   ├── client.py           # /clientes/*, /solicitacoes, /perguntas/*
│   ├── admin.py            # /admin/*
│   ├── catalogs.py         # /tipos-ocorrencia, /configuracoes/publicas
│   └── sync.py             # /sync/*
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── client_service.py
│   ├── admin_service.py
│   ├── catalog_service.py
│   ├── assistencia_service.py
│   ├── taxi_question_service.py
│   ├── priority_service.py
│   └── protocol_service.py
├── repositories/
│   ├── __init__.py
│   ├── user_repository.py
│   ├── pessoa_repository.py
│   ├── apolice_repository.py
│   ├── solicitacao_repository.py
│   ├── assistencia_repository.py
│   ├── historico_repository.py
│   └── pergunta_repository.py
├── schemas/
│   ├── __init__.py
│   ├── auth.py
│   ├── client.py
│   ├── admin.py
│   ├── solicitacao.py
│   ├── assistencia.py
│   ├── pergunta.py
│   └── common.py           # Pagination, Error envelope
└── database/
    ├── DataBase.py          # (legado, será substituído por core/database.py)
    ├── select.py            # (legado, será substituído por repositories/)
    └── insert.py            # (legado, será substituído por repositories/)
```

### 1.1 — Resultado da Fase 1 (concluída em 2026-09-15)

**Tudo aplicado e validado.** Estrutura criada, prefixo `/api/v1` ativo, pooling, JWT e middleware funcionais.

**Ações (1.1–1.8):**

| # | Ação | Arquivo |
|---|---|---|
| 1.1 | Estrutura de pastas criada (`core/`, `routers/`, `services/`, `repositories/`, `middleware/`, `schemas/`) | todos com `__init__.py` |
| 1.2 | Prefixo `/api/v1` configurado em todos os routers legados (`include_router(..., prefix="/api/v1")`) | `main.py` |
| 1.3 | Connection pooling (`MySQLConnectionPool`, pool_size=5) e função `get_connection()` | `core/database.py` |
| 1.4 | JWT (`create_access_token`, `decode_access_token`) via `python-jose`; hashing via `bcrypt` direto | `core/security.py` |
| 1.5 | Middleware de auth: Bearer obrigatório, paths públicos, injeção de `request.state.session` | `middleware/auth.py` |
| 1.6 | Dependências: `get_current_session()`, `require_perfil(*perfis)` | `core/deps.py` |
| 1.7 | `.env` documentado (`.env.example`) com `JWT_SECRET`, `JWT_ALGORITHM=HS256`, `JWT_EXPIRE_SECONDS=3600` + vars MySQL | `.env.example` |
| 1.8 | `requeriments.txt` atualizado em UTF-8 (era UTF-16 de `pip freeze`) | `requeriments.txt` |

**Outras mudanças:**

- **`main.py`:** reescrito — título/descrição do app, CORS (`allow_origins=["*"]`), middleware de auth instalado, prefixo `/api/v1`, rota `/` como health check público, porta padrão 8080.
- **pydantic-settings:** `core/config.py` com `Settings` cacheado (`get_settings()`) — variáveis do MySQL (`DB_*`) + JWT, com env fallback para os nomes legados (`host/user/password/bank/port`).
- **Código legado preservado:** arquivos em `api/`, `database/`, `classes/`, `util/` continuam funcionando sob `/api/v1`.
- **Decisão técnica:** `passlib[bcrypt]` foi **substituído por `bcrypt` direto** — `passlib==1.7.4` é incompatível com `bcrypt>=4.1` (bug do `bcrypt.__about__.__version__`). O projeto já usava `bcrypt` diretamente em `util/function.py`, então `core/security.py` segue o mesmo padrão. Isso remove `passlib` de `requeriments.txt`.
- **Teste de fumaca criado:** `tests/smoke_phase1.py` (usa `httpx2`, dependência de TESTE apenas — não adicionado ao `requeriments.txt`).
- **`.gitignore`:** adicionado `.venv/`.

**Validação executada (evidence):**

```
GET / (public)                         -> 200
GET /openapi.json (public)             -> 200
GET /api/v1/tipos-ocorrencia (no token)-> 401  (middleware bloqueia)
GET /api/v1/auth/me (no token)         -> 401  (middleware bloqueia)
OPTIONS preflight (CORS + Origin)      -> 200  (Access-Control-Allow-Origin ok)

rotas /api/v1 registradas: 22
  /api/v1/admin/dashboard
  /api/v1/admin/solicitacoes
  /api/v1/admin/solicitacoes/{solicitacao_id}
  /api/v1/admin/tipos-assistencia
  /api/v1/auth/me
  /api/v1/clientes/me
  /api/v1/clientes/me/apolices
  /api/v1/clientes/me/solicitacoes
  /api/v1/configuracoes/publicas
  /api/v1/post/* (9 rotas de cadastro)
  /api/v1/solicitacoes/{solicitacao_id}
  /api/v1/tipos-ocorrencia
```

**Observacao importante:** com o middleware ativo, todo endpoint protegido retorna **401** até a Fase 2 implementar `login` + emissão de JWT. Inclua `JWT_SECRET` real no `.env` em produção.

---

## 4. Fase 2 — Autenticação (4 endpoints) — ✅ FEITA (2026-09-15)

> 📄 Detalhes técnicos completos em `docs/FASE2_ANALISE_AUTENTICACAO.md`.

**Objetivo:** Login cliente, login analista, sessão atual, logout.

| # | Método | Endpoint | Scope | Descrição |
|---|--------|----------|-------|-----------|
| 2.1 | `POST` | `/api/v1/auth/clientes/login` | PÚBLICO | CPF + senha → JWT + session |
| 2.2 | `POST` | `/api/v1/auth/analistas/login` | PÚBLICO | login + senha → JWT + session |
| 2.3 | `GET` | `/api/v1/auth/me` | AUTENTICADO | Decodificar JWT → session |
| 2.4 | `POST` | `/api/v1/auth/logout` | AUTENTICADO | Retornar 204 (stateless) |

### Respostas Esperadas

**Login Cliente (2.1):**
```json
{
  "access_token": "<jwt>",
  "token_type": "Bearer",
  "expires_in": 3600,
  "session": {
    "id_usuario": 801,
    "id_pessoa": 1,
    "perfil": "CLIENTE",
    "nome_exibicao": "Marina Exemplo",
    "seguradora": null,
    "seguradoras": []
  }
}
```

**Login Analista (2.2):**
```json
{
  "access_token": "<jwt>",
  "token_type": "Bearer",
  "expires_in": 3600,
  "session": {
    "id_usuario": 901,
    "id_pessoa": 101,
    "perfil": "ANALISTA",
    "nome_exibicao": "Analista Horizonte",
    "seguradora": { "id_pj": 10, "nome_fantasia": "Seguradora Horizonte" },
    "seguradoras": [
      { "id_pj": 10, "nome_fantasia": "Seguradora Horizonte" },
      { "id_pj": 20, "nome_fantasia": "Seguradora Orbita" }
    ]
  }
}
```

### Validez de Negócio

- **Cliente login:** CPF normalizado (remover não-dígitos), validar dígitos verificadores, buscar `tb_user` com `perfil='CLIENTE'` + `fk_status` ativo, comparar senha com bcrypt
- **Analista login:** Login lowercase + trim, buscar `tb_user` com `perfil='ANALISTA'` + ativo, montar `seguradoras[]` via `tb_analista_seguradora`

**Arquivos:** `routers/auth.py`, `services/auth_service.py`, `repositories/user_repository.py`

### 2.1 — Resultado da Fase 2 (concluída em 2026-09-15)

**4 endpoints criados e validados.** Login cliente (CPF+senha), login analista (login+senha), `/me`, logout.

**Novos arquivos:**

| # | Arquivo | Conteúdo |
|---|---|---|
| 2.1 | `schemas/auth.py` | `ClienteLoginRequest`, `AnalistaLoginRequest`, `SessaoInfo`, `AuthEnvelope` (Pydantic v2) |
| 2.2 | `repositories/user_repository.py` | Queries parametrizadas: `find_client_by_cpf`, `find_analyst_by_login`, `find_analyst_insurers`, `find_insurer` |
| 2.3 | `services/auth_service.py` | Lógica de login (CPF normalizado + dígitos verificadores, bcrypt compare, sessão de saída), `login_client`, `login_analyst` |
| 2.4 | `routers/auth.py` | 4 endpoints: `POST /auth/clientes/login`, `POST /auth/analistas/login`, `GET /auth/me`, `POST /auth/logout` |

**Arquivos modificados:**

| Arquivo | Mudança |
|---|---|
| `main.py` | `apiAuth` legado removido; novo `routers/auth` incluído |
| `middleware/auth.py` | Session injetada com campos completos (`id_usuario`, `id_pessoa`, `perfil`, `nome_exibicao`, `seguradora`, `seguradoras`) — decodificação do JWT |

**Decisões técnicas:**

- **validate_docbr** usado para validar dígitos verificadores do CPF no login cliente (fail-fast: 401 sem tocar no DB)
- **Seguradora principal** do analista derivada de `tb_user.fk_seguradora`; fallback para primeira da lista `tb_analista_seguradora` se nula
- `/auth/logout` retorna **204 stateless** (o frontend limpa o token localmente; o JWT expira naturalmente)

**Testes executados:**

```
tests/test_auth_service.py   — 10 testes unitários (mock do repositório) — PASS
tests/test_auth_routes.py    — 8 testes HTTP (TestClient, token forjado)  — PASS
tests/smoke_phase1.py        — Sem regressão, 25 rotas /api/v1            — SMOKE_TEST_OK
```

**Pendência:** fluxo ponta-a-ponta (DB real) requer MySQL `orbyt` local com seed de dados.

---

## 5. Fase 3 — Catálogos e Configurações (2 endpoints) — ✅ FEITA (2026-09-15)

> 📄 Detalhes técnicos completos em `docs/FASE3_ANALISE_CATALOGOS.md`.

| # | Método | Endpoint | Scope | Descrição |
|---|--------|----------|-------|-----------|
| 3.1 | `GET` | `/api/v1/tipos-ocorrencia` | AUTENTICADO | Lista de ocorrências ativas |
| 3.2 | `GET` | `/api/v1/configuracoes/publicas` | AUTENTICADO | Configurações do app (país, emergência) |

### Resposta Esperada — Tipos de Ocorrência (3.1)
```json
{
  "items": [
    { "id_tipo_ocorrencia": 1, "codigo": "PANE_MECANICA", "nome": "Pane mecânica", "descricao": "...", "ativo": true, "ordem": 1 }
  ]
}
```

**Arquivo:** `routers/catalogs.py`, `services/catalog_service.py`

### 3.1 — Resultado da Fase 3 (concluída em 2026-09-15)

**2 endpoints criados e validados**, seguindo o DTO limpo do mock (`server/mock-api/mock-api.js`) e os contratos v2 de `public/data/api`.

| # | Endpoint | Status 200 | Detalhe |
|---|---|---|---|
| 3.1 | `GET /api/v1/tipos-ocorrencia` | `{ "items": [ { id_tipo_ocorrencia, codigo, nome, descricao, ativo, ordem } ] }` | query opcional `ativo`; ordenado por `id_ocorrencia`; `ordem` = `id_ocorrencia` |
| 3.2 | `GET /api/v1/configuracoes/publicas` | `{ pais, mensagem, servicos }` | `servicos` vem da coluna `tb_configuracao.servicos_json` (JSON_ARRAY), sem fallback |

**Novos arquivos:**

| Arquivo | Conteúdo |
|---|---|
| `repositories/catalog_repository.py` | `find_occurrences(ativo: bool \| None)` (query condicional `WHERE ativo`) e `get_app_configuration()` (`LIMIT 1`) — mesmo padrão mockável de `user_repository` |
| `services/catalog_service.py` | `list_occurrence_types(ativo=None)` → `{"items"}`, cast `ativo` p/ `bool`, `ordem=id`; `get_public_configurations()` faz `json.loads` do `servicos_json`; erros de repositório/JSON → 500 |
| `tests/test_catalog_service.py` | 6 testes unitários (mock do repositório) |
| `tests/test_catalog_routes.py` | 5 testes HTTP (TestClient, token forjado, repositório mockado) |

**Arquivos modificados:**

| Arquivo | Mudança |
|---|---|
| `api/apiMain.py` | Removidos `GET /tipos-ocorrencia` e `GET /configuracoes/publicas` (legados, envelope `schema_version/response`). Mantido `GET /solicitacoes/{id}` |
| `main.py` | Incluído `catalogs.router` sob `/api/v1` |
| `database_estrutura.sql` | Seed de `tb_configuracao.servicos_json` alterado de `JSON_OBJECT('transporte', TRUE, 'emergencia', TRUE)` para `JSON_ARRAY` com `{codigo, nome, telefone}` (SAMU 192, Bombeiros 193, Polícia 190), conforme decisão do usuário: **apenas seed no banco, sem fallback** |

**Decisões técnicas:**

- Scope `AUTENTICADO` (qualquer perfil): as duas rotas dependem de `get_current_session`; o middleware já devolve 401 sem token.
- Resposta usa o DTO limpo (`items`/`pais` no topo), **não** o envelope `schema_version/request_query/response` do legado — é o que o `unwrapItems(payload)` do frontend parseia (`api-mappers.js`) e o que o mock já devolve.
- `sem fallback decode` de `servicos_json`: se o conteúdo não bater com o contrato (ou a tabela estiver vazia), a API responde 500 — forçando consistência com o seed.

**Testes executados (evidence):**

```
CATALOG_SERVICE_TESTS_OK (6 testes)   PASS
CATALOG_ROUTES_TESTS_OK (5 testes)    PASS
AUTH_SERVICE_TESTS_OK (10 testes)     regressão PASS
AUTH_ROUTES_TESTS_OK (8 testes)       regressão PASS
SMOKE_TEST_OK                         25 rotas /api/v1 (sem regressão)
```

**Pendência:** validação contra MySQL real (rodar o novo `INSERT` de `tb_configuracao`) requer banco `orbyt` ativo. Em bancos existentes, reexecutar o seed da `tb_configuracao` para o novo formato de `servicos_json`.

---

## 6. Fase 4 — Área do Cliente (5 endpoints) — ✅ FEITA (2026-09-15)

> 📄 Detalhes técnicos completos em `docs/FASE4_ANALISE_CLIENTE.md`.

| # | Método | Endpoint | Scope | Descrição |
|---|--------|----------|-------|-----------|
| 4.1 | `GET` | `/api/v1/clientes/me` | CLIENTE | Perfil do cliente (PF/PJ) |
| 4.2 | `GET` | `/api/v1/clientes/me/apolices` | CLIENTE | Apólices com solicitação ativa |
| 4.3 | `POST` | `/api/v1/solicitacoes` | CLIENTE | Criar nova solicitação |
| 4.4 | `GET` | `/api/v1/clientes/me/solicitacoes` | CLIENTE | Lista de solicitações do cliente |
| 4.5 | `GET` | `/api/v1/solicitacoes/{id}` | CLIENTE_DONO | Detalhe da solicitação |

### Regras de Negócio — Criar Solicitação (4.3)

1. Validar body: `apolice_id`, `tipo_ocorrencia_id`, `descricao_evento`, `possui_feridos`, `risco_imediato`, `local.*`, `data_criacao_cliente`
2. Verificar `Idempotency-Key` header = `id_solicitacao_cliente` no body
3. Verificar apólice pertence ao cliente E está ativa
4. Verificar não há solicitação ativa para esta apólice (`ACTIVE_REQUEST_STATUSES`)
5. Gerar protocolo: `ORB-{YEAR}-{seq 6 dígitos}` sequencial
6. Calcular prioridade: `possui_feridos || risco_imediato` → `CRITICA`, senão `NORMAL`
7. Inserir `tb_solicitacao` + `tb_solicitacao_local` + `historico_status`
8. Retornar 201 com solicitação completa

### Resposta Esperada — Criar Solicitação (4.3)
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

**Arquivos:** `routers/client.py`, `services/client_service.py`, `repositories/solicitacao_repository.py`

### 4.1 — Resultado da Fase 4 (concluída em 2026-09-15)

**5 endpoints criados e validados**, com idempotência, transação e ownership por perfil CLIENTE.

| # | Endpoint | Status | Detalhe |
|---|---|---|---|
| 4.1 | `GET /api/v1/clientes/me` | 200 | Perfil PF/PJ + contatos mascarados; 404 se pessoa não existe |
| 4.2 | `GET /api/v1/clientes/me/apolices` | 200 | Paginado; inclui `solicitacao_ativa` por apólice (5 status ativos) |
| 4.3 | `POST /api/v1/solicitacoes` | 201 | Idempotência via `Idempotency-Key` = `id_solicitacao_cliente`; transação (local + solicitação + histórico + update apólice); prioridade CRITICA/NORMAL; protocolo `ORB-{YEAR}-{seq}` |
| 4.4 | `GET /api/v1/clientes/me/solicitacoes` | 200 | Paginado; filtros `status` e `active_only`; ordenado por `data_recebimento DESC` |
| 4.5 | `GET /api/v1/solicitacoes/{id}` | 200 | Aggregate (solicitação + cliente + apólice + veículo + seguradora + ocorrência + analista + assistências + perguntas + histórico); 404 se não existe ou não pertence ao cliente |

**Novos arquivos:**

| Arquivo | Conteúdo |
|---|---|
| `schemas/client.py` | `LocalInput`, `SolicitacaoCreateRequest` (Pydantic v2) |
| `repositories/client_repository.py` | Queries: `person_by_id`, `pessoa_fisica/juridica_by_id`, `contatos_by_pessoa`, `policies_by_pessoa`, `active_request_by_policy`, `requests_by_pessoa(status, active_only)`, `occurrence_by_id`, `policy_by_id_for_pessoa`, `request_by_client_uuid`, `next_solicitacao_seq` |
| `repositories/solicitacao_repository.py` | Queries: `solicitacao_by_id` (aggregate JOINs), `assistencias_by_solicitacao`, `perguntas_by_solicitacao`, `historico_by_solicitacao`, `apolice_resumo_by_id`, `create_solicitacao` (transaction) |
| `services/client_service.py` | `get_perfil`, `list_apolices`, `criar_solicitacao` (idempotência, validações, transação), `list_solicitacoes`, `get_detalhe_solicitacao` |
| `routers/client.py` | 5 endpoints com `require_perfil("CLIENTE")` |
| `tests/test_client_service.py` | 6 testes unitários |
| `tests/test_client_routes.py` | 11 testes HTTP |

**Arquivos modificados:**

| Arquivo | Mudança |
|---|---|
| `core/deps.py` | Corrigido `require_perfil`: `session` agora usa `Depends(get_current_session)` (antes era default function, não resolvia pelo FastAPI) |
| `main.py` | Removidos imports de `apiMain` e `apiCliente` (rotas `/solicitacoes/{id}` e `/clientes/*` agora no novo `client_router`); incluído `client_router` |
| `api/apiAdmin.py` | Removido endpoint legado `GET /solicitacoes/{id}` (colidia com novo router) |
| `database_estrutura.sql` | Colunas `data_criacao_cliente`, `data_recebimento`, `data_decisao` de `DATE` para `DATETIME` (align contract ISO timestamps); colunas `origem`, `tipo`, `version` adicionadas a `tb_pergunta`; `data_resposta` tornada nullable |

**Decisões técnicas:**

- `tb_solicitacao_local` em vez de `tb_endereco` (bug legado em `database/select.py`).
- Protocolo `ORB-{YEAR}-{seq}`: seq = `MAX(id_solicitacao)+1`; `protocolo_solicitacao = numero_solicitacao` (NOT NULL UNIQUE).
- Datas DATE→DATETIME: preserva timestamp do contrato; leitura via helper `_iso()` → `YYYY-MM-DDTHH:MM:SSZ`.
- `data_criacao_cliente` recebida como string ISO do cliente, convertida para datetime no servidor.

**Testes executados (evidence):**

```
AUTH_SERVICE_TESTS_OK (10 testes)      regressão PASS
AUTH_ROUTES_TESTS_OK (8 testes)        regressão PASS
CATALOG_SERVICE_TESTS_OK (6 testes)    regressão PASS
CATALOG_ROUTES_TESTS_OK (5 testes)     regressão PASS
CLIENT_SERVICE_TESTS_OK (6 testes)     PASS
CLIENT_ROUTES_TESTS_OK (11 testes)     PASS
SMOKE_TEST_OK                          25 rotas /api/v1 (sem regressão)
```

**Pendência:** validação contra MySQL real (rotas novas + transação `create_solicitacao`); DDL de `tb_solicitacao` (DATE→DATETIME) e `tb_pergunta` (novas colunas) precisam ser aplicados ao banco.

---

## 7. Fase 5 — Perguntas/Táxi (1 endpoint) — ✅ FEITA (2026-09-15)

> 📄 Detalhes técnicos completos em `docs/FASE5_ANALISE_PERGUNTAS_TAXI.md`.

| # | Método | Endpoint | Scope | Descrição |
|---|--------|----------|-------|-----------|
| 5.1 | `POST` | `/api/v1/perguntas/{id}/resposta` | CLIENTE_DONO | Responder pergunta de táxi |

### Regras de Negócio

- Verificar ownership (pergunta pertence a solicitação do cliente)
- `necessita_taxi=true`: exige `quantidade_passageiros >= 1`, `necessita_acessibilidade` boolean, `quantidade_criancas >= 0`, `quantidade_animais >= 0`, `bagagem` não vazio
- `necessita_taxi=false`: payload mínimo (`necessita_taxi: false` + `version`)
- Status muda de `PENDENTE` → `RESPONDIDA`

**Arquivo:** `routers/client.py`, `services/taxi_question_service.py`

### 5.1 — Resultado da Fase 5 (concluída em 2026-09-15)

**1 endpoint criado e validado**, replicando `TaxiQuestionService` do frontend (`OrbytSos/src/services/taxi-question-service.js`).

| # | Endpoint | Status | Detalhe |
|---|---|---|---|
| 5.1 | `POST /api/v1/perguntas/{id}/resposta` | 200 | Responde pergunta TAXI; status `PENDENTE`→`RESPONDIDA`, `version+1`, `data_resposta` setada |

**Regras replicadas do mock/frontend:**

- Ownership: pergunta precisa existir, pertencer a uma solicitação do próprio cliente (senão 404 `TAXI_QUESTION_NOT_FOUND`).
- Já respondida (`!== PENDENTE`) → 422 `TAXI_QUESTION_ALREADY_ANSWERED`.
- Optimistic locking: `version` do body ≠ `version` do banco → 409 `TAXI_QUESTION_VERSION_CONFLICT`.
- Validação: `necessita_taxi` bool; se `false`, payload mínimo; se `true`, exige `quantidade_passageiros >= 1`, `necessita_acessibilidade` bool, `quantidade_criancas >= 0`, `quantidade_animais >= 0`, `bagagem` não-vazio; `observacoes` opcional → 422 `VALIDATION_ERROR` com `fields`.
- Ao responder `false`, campos de táxi zerados para `NULL` no banco (conforme mock).
- Resposta: `{ "pergunta": { ...DTO questionDto } }`.

**Novos arquivos:**

| Arquivo | Conteúdo |
|---|---|
| `services/taxi_question_service.py` | `responder_pergunta` (ownership, locking, validação, UPDATE) + `QuestionError` |
| `schemas/client.py` | `PerguntaRespostaRequest` (novo) |
| `tests/test_taxi_question_service.py` | 9 testes unitários |
| `tests/test_taxi_question_routes.py` | 10 testes HTTP (TestClient, token forjado, repo mockado) |

**Arquivos modificados:**

| Arquivo | Mudança |
|---|---|
| `repositories/solicitacao_repository.py` | `pergunta_by_id`, `answer_pergunta` (UPDATE transacional com `version` conforme), `_id_status_pergunta_respondida` |
| `routers/client.py` | Rota `POST /perguntas/{pergunta_id}/resposta` com `require_perfil("CLIENTE")` |
| `database_estrutura.sql` | `tb_pergunta`: `bagagem` → `varchar(255)` (era `bool`), campos de táxi (`necessita_taxi`, `qtd_passageiros`, `necessita_acessibilidade`, `qtd_criancas`, `qtd_animais`, `observacoes`) → nullable/`varchar(255)` — decisão do usuário: **alinhar SQL ao contrato** |

**Testes executados (evidence):**

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

**Pendência:** validação contra MySQL real; DDL de `tb_pergunta` (bagagem/nulls) precisa ser aplicado ao banco. A criação da pergunta (GUINCHO→TAXI) acontece na Fase 6 (admin), portanto este endpoint depende de dados existentes.

---

## 8. Fase 6 — Área do Admin (12 endpoints)

> ✅ **FEITA (2026-09-15)** — Implementada e testada (23 testes de serviço + 15 de rotas, todos passando; smoke OK). Detalhes técnicos completos em `docs/FASE6_ANALISE_ADMIN.md`.

| # | Método | Endpoint | Scope | Descrição |
|---|--------|----------|-------|-----------|
| 6.1 | `GET` | `/api/v1/admin/dashboard` | ANALISTA | Métricas + fila prioritária |
| 6.2 | `GET` | `/api/v1/admin/solicitacoes` | ANALISTA | Fila filtrada + paginação |
| 6.3 | `GET` | `/api/v1/admin/solicitacoes/{id}` | ANALISTA | Detalhe completo |
| 6.4 | `GET` | `/api/v1/admin/tipos-assistencia` | ANALISTA | Catálogo de assistências |
| 6.5 | `POST` | `/api/v1/admin/solicitacoes/{id}/assumir` | ANALISTA | Atribuir a si mesmo |
| 6.6 | `POST` | `/api/v1/admin/solicitacoes/{id}/confirmar` | ANALISTA_RESPONSAVEL | Confirmar cobertura |
| 6.7 | `POST` | `/api/v1/admin/solicitacoes/{id}/recusar` | ANALISTA_RESPONSAVEL | Recusar (sem cobertura) |
| 6.8 | `POST` | `/api/v1/admin/solicitacoes/{id}/iniciar-atendimento` | ANALISTA_RESPONSAVEL | Iniciar atendimento |
| 6.9 | `POST` | `/api/v1/admin/solicitacoes/{id}/registrar-prestador-acionado` | ANALISTA_RESPONSAVEL | Prestador acionado |
| 6.10 | `POST` | `/api/v1/admin/solicitacoes/{id}/concluir` | ANALISTA_RESPONSAVEL | Concluir atendimento |
| 6.11 | `POST` | `/api/v1/admin/solicitacoes/{id}/assistencias` | ANALISTA_RESPONSAVEL | Adicionar assistência |
| 6.12 | `PATCH` | `/api/v1/admin/solicitacao-assistencias/{id}` | ANALISTA_RESPONSAVEL | Atualizar status assistência |

### O que foi alterado/implementado na Fase 6

- **`OrbySos_api/routers/admin.py`** (novo): as 12 rotas com `require_perfil("ANALISTA")`, prefixo `/admin`; filtros de fila via query params; `assistencias` retorna 201.
- **`OrbySos_api/services/admin_service.py`** (novo): transições, DTOs, paginação, scopes 6.5 (ANALISTA) vs 6.6–6.12 (ANALISTA_RESPONSAVEL via `fk_analista_responsavel == session.id_usuario`), validação de versão (409), máquinas de estado, `concluir` exige assistências terminais, acesso por seguradora.
- **`OrbySos_api/repositories/admin_repository.py`** (novo): `find_solicitacoes` (com filtros), `tipos_assistencia_ativos`, `add_assistencia` (find-or-create `tb_assistencia` + pergunta TAXI p/ GUINCHO + sync CONFIRMADA→EM_ATENDIMENTO), `update_assistencia_status` (sync solicitação p/ PRESTADOR_ACIONADO), `transicionar_solicitacao` (UPDATE com guard de version+status + histórico + release de apólice).
- **`OrbySos_api/schemas/admin.py`** (novo): `VersionRequest`, `ConfirmarRequest`, `RecusarRequest`, `OperacaoRequest`, `AssistenciaAddRequest`, `AssistenciaStatusUpdateRequest`.
- **`OrbySos_api/main.py`**: removido router legado `apiAdmin` (3 rotas colidiam com o novo contrato), incluído `routers/admin`.
- **`database_estrutura.sql`**: `tb_solicitacao_assistencia.comentario` → `varchar(255)`; `data_inclusao`/`data_atualizacao` → `datetime`; `tb_historico_status.comentario` → `varchar(255)`; seeds de status `ASSISTENCIA_SOLICITACAO` agora incluem `AGUARDANDO_PRESTADOR`, `EM_DESLOCAMENTO`, `CONCLUIDA`, `CANCELADA`.
- Tests: `tests/test_admin_service.py` (23) e `tests/test_admin_routes.py` (15). Suíte completa (103 testes) e `smoke_phase1.py` OK.
- **Pendência:** validação ponta-a-ponta contra MySQL real (sem listener 3306 no ambiente) e aplicação do DDL/seed ao banco.

### Máquina de Estados — Solicitação

```
RECEBIDA ──────────► EM_ANALISE
                         │
                    ┌────┴────┐
                    ▼         ▼
              CONFIRMADA  RECUSADA_SEM_COBERTURA
                    │         (terminal)
                    ▼
             EM_ATENDIMENTO
                    │
              ┌─────┴─────┐
              ▼           ▼
    PRESTADOR_ACIONADO  CONCLUIDA
              │         (terminal)
              ▼
          CONCLUIDA
         (terminal)
```

### Máquina de Estados — Assistência

```
INCLUIDA ──► PRESTADOR_ACIONADO ──► CONCLUIDA (terminal)
   │                                     
   └──► REMOVIDA (terminal)
```

### Dashboard — Métricas (6.1)

```json
{
  "metricas": {
    "criticas_abertas": 1,       // prioridade=CRITICA AND status NOT IN (CONCLUIDA, RECUSADA_SEM_COBERTURA)
    "aguardando_analise": 2,     // status=RECEBIDA
    "confirmadas_em_atendimento": 2, // status IN (CONFIRMADA, EM_ATENDIMENTO)
    "prestadores_acionados": 1,  // status=PRESTADOR_ACIONADO
    "concluidas": 0,             // status=CONCLUIDA
    "recusadas_sem_cobertura": 1 // status=RECUSADA_SEM_COBERTURA
  },
  "fila_prioritaria": { "items": [...] }
}
```

### Assistência com GUINCHO cria Pergunta TAXI (6.11)

Quando `tipo_assistencia_id = 1` (GUINCHO), o servidor cria automaticamente uma `tb_pergunta` com tipo `TAXI` e status `PENDENTE`.

### Controle de Versão (Optimistic Locking)

Todos os endpoints de write recebem `version` no body. O servidor compara com o `version` atual no DB. Se diferir, retorna **409 Conflict**.

**Arquivos:** `routers/admin.py`, `services/admin_service.py`, `repositories/admin_repository.py`

---

## 9. Fase 7 — Sync/SSE (2 endpoints)

| # | Método | Endpoint | Scope | Descrição |
|---|--------|----------|-------|-----------|
| 7.1 | `GET` | `/api/v1/sync/version` | PÚBLICO | Versão atual do banco |
| 7.2 | `GET` | `/api/v1/sync/events` | PÚBLICO | SSE stream de mudanças |

### Implementação

- `sync/version` → `SELECT revision FROM orbyt_meta WHERE chave='revision'`
- `sync/events` → `StreamingResponse` com `media_type="text/event-stream"`, polling periódico do `revision` ou uso de MySQL triggers + `CREATE EVENT` para notificação

**Arquivo:** `routers/sync.py`

### O que foi alterado/implementado na Fase 7

> ✅ **FEITA (2026-09-15)** — Implementada e testada (5 testes de serviço + 6 de rotas, todos passando; regressão completa 114 testes + smoke OK). Detalhes técnicos completos em `docs/FASE7_ANALISE_SYNC.md`.

- **`OrbySos_api/routers/sync.py`** (novo): `GET /sync/version` (JSON público) e `GET /sync/events` (`StreamingResponse` com `media_type="text/event-stream"`, headers `Cache-Control: no-cache, no-transform`, `Connection: keep-alive`, `X-Accel-Buffering: no`). Ambos sem auth (já constavam em `PUBLIC_PREFIXES` no `middleware/auth.py`).
- **`OrbySos_api/services/sync_service.py`** (novo): `get_version()`, `_sse_frame()` (formato `data: {...}\n\n`, sem `event:`/`id:`) e `version_stream()` — generator async com polling a cada 2s, dedupe por `revision` e envio imediato ao conectar (igual ao mock `#streamChanges`).
- **`OrbySos_api/repositories/sync_repository.py`** (novo): `get_version()` (lê `orbyt_meta`, defaults `revision=0`/`updated_at=null`) e `bump_revision()` (incrementa `revision` + grava `updated_at` com `ON DUPLICATE KEY UPDATE`).
- **`database_estrutura.sql`**: nova tabela `orbyt_meta (chave VARCHAR(64) PK, valor VARCHAR(255) NOT NULL)` + seed `('revision', '0')`.
- **`main.py`**: incluído `routers/sync`.
- Tests: `tests/test_sync_service.py` (5) e `tests/test_sync_routes.py` (6). Suíte completa (114 testes) e `smoke_phase1.py` OK (37 rotas `/api/v1`).
- **Pendência:** `bump_revision()` ainda não é chamado pelos demais repositórios (cada escrita deveria invocá-lo para propagar a revisão). Validação ponta-a-ponta contra MySQL real também pendente (sem listener 3306).

---

## 10. Fase 8 — Validação e Testes — ✅ FEITA (2026-09-15)

> ✅ **FEITA (2026-09-15)** — Contratos validados, 4 divergências reais corrigidas, `bump_revision` integrado nas escritas, testes de fluxo (cliente/admin), edge-cases com envelope global `{error, trace_id}`, auditoria de SQL Injection concluída e códigos específicos no `auth_service`. Suíte total: 136 testes + smoke OK.
> 📄 Documentos Fase 8: `docs/FASE8_SESSAO.md`, `docs/FASE8_1_VALIDACAO_CONTRATOS.md`, `docs/FASE8_5_AUDITORIA_SQL_INJECTION.md`.
> 🗂️ Logs/sub-docs: `docs/FASE8_SESSAO.md` (seções 8.6–8.10), `docs/FASE8_1_VALIDACAO_CONTRATOS.md` (8.1), `docs/FASE8_5_AUDITORIA_SQL_INJECTION.md` (8.5).

| # | Ação | Método |
|---|---|---|
| 8.1 | Testar cada endpoint contra os contratos | Comparar responses com `public/data/api/*.json` ✅ |
| 8.2 | Fluxo cliente completo | Login → listar apólices → criar solicitação → ver detalhe → responder táxi ✅ (`test_flow_cliente.py`) |
| 8.3 | Fluxo admin completo | Login → dashboard → assumir → confirmar → iniciar → adicionar assistência → concluir ✅ (`test_flow_admin.py`) |
| 8.4 | Edge cases | Version conflict (409), ownership violation (403), insurer access denied (403), body validation (422) ✅ (`test_edge_cases.py`) |
| 8.5 | SQL injection | Verificar que TODAS as queries usam parameterized statements ✅ |
| 8.6 | Integrar `bump_revision()` nas escritas | Pendência da Fase 7 — bump dentro das transações de `admin_repository` e `solicitacao_repository` ✅ (`test_revision_integration.py`) |

### 8.6 — Resultado (concluída em 2026-09-15)

> ✅ **`bump_revision()` integrado** — `sync_repository.bump_revision_cursor()` (incremento atômico) roda no mesmo cursor antes do `conn.commit()` em: `create_solicitacao`, `answer_pergunta`, `transicionar_solicitacao`, `add_assistencia`, `update_assistencia_status`.

### 8.7 — Correções reais adicionais (Fase 8.4/8.9)

- **`middleware/auth.py`** — 401 sem envelope → passa a usar `make_error_response()` com `trace_id`.
- **`main.py`** — registrado `unhandled_exception_handler` (`Exception`) → 500 com envelope `INTERNAL_ERROR`.
- **`services/auth_service.py`** — códigos específicos `AUTH_INVALID_CREDENTIALS` (401) / `AUTH_INACTIVE_USER` (403).

### 8.5 — Resultado da Fase 8.5 (concluída em 2026-09-15)

> ✅ **Auditoria de SQL Injection CONCLUÍDA** — 57 chamadas `cur.execute()` auditadas em 6 arquivos, ~114 parâmetros verificados. **TODAS AS QUERIES SEGURAS.** Detalhes completos em `docs/FASE8_5_AUDITORIA_SQL_INJECTION.md`.

**Arquivos auditados:**

| # | Arquivo | Chamadas execute() | Seguranca |
|---|---|---|---|
| 1 | admin_repository.py | 21 | OK |
| 2 | catalog_repository.py | 3 | OK |
| 3 | client_repository.py | 13 | OK |
| 4 | solicitacao_repository.py | 13 | OK |
| 5 | sync_repository.py | 3 | OK |
| 6 | user_repository.py | 4 | OK |
| 7 | __init__.py | 0 (vazio) | -- |

**Padroes perigosos verificados (todos ausentes):**

- 0 f-strings com dados interpolados em queries SQL
- 0 uso de `.format()` em queries
- 0 concatenacao com valores de usuario em queries
- 0 interpolacao de nomes de coluna/tabela

**Construcoes dinamicas verificadas e validadas como seguras:**

- `admin_repository.py:81` — `IN (...)` com `, ".join(["%s"] * len(allowed))` + parametros via `tuple(params)`
- `admin_repository.py:491` — UPDATE dinamico com `, ".join(sets)` onde `sets` contem apenas fragmentos SQL com `%s`

**Conclusao:** Nenhuma acao corretiva necessaria. O padrao de projeto e consistente e seguro contra SQL Injection.

### Regressão Final da Fase 8

> **136 testes passando** (12 suites de pytest + smoke): admin_routes 15, admin_service 23, auth_routes 8, auth_service 10, catalog_routes 5, catalog_service 6, client_routes 11, client_service 8, edge_cases 9, flow_admin 1, flow_cliente 1, revision_integration 9, sync_routes 6, sync_service 5, taxi_question_routes 10, taxi_question_service 9. Comando de regressão: `PYTHONPATH=. .venv/bin/python -m pytest tests/ -q` + `PYTHONPATH=. .venv/bin/python tests/smoke_phase1.py`

---

## 11. Catálogo Completo de Endpoints (26 total)

| # | Método | Endpoint | Auth | Perfil |
|---|--------|----------|------|--------|
| 1 | `POST` | `/api/v1/auth/clientes/login` | Não | — |
| 2 | `POST` | `/api/v1/auth/analistas/login` | Não | — |
| 3 | `GET` | `/api/v1/auth/me` | JWT | Qualquer |
| 4 | `POST` | `/api/v1/auth/logout` | JWT | Qualquer |
| 5 | `GET` | `/api/v1/clientes/me` | JWT | CLIENTE |
| 6 | `GET` | `/api/v1/clientes/me/apolices` | JWT | CLIENTE |
| 7 | `GET` | `/api/v1/tipos-ocorrencia` | JWT | Qualquer |
| 8 | `GET` | `/api/v1/configuracoes/publicas` | JWT | Qualquer |
| 9 | `POST` | `/api/v1/solicitacoes` | JWT | CLIENTE |
| 10 | `GET` | `/api/v1/clientes/me/solicitacoes` | JWT | CLIENTE |
| 11 | `GET` | `/api/v1/solicitacoes/{id}` | JWT | CLIENTE (dono) |
| 12 | `POST` | `/api/v1/perguntas/{id}/resposta` | JWT | CLIENTE (dono) |
| 13 | `GET` | `/api/v1/admin/dashboard` | JWT | ANALISTA |
| 14 | `GET` | `/api/v1/admin/solicitacoes` | JWT | ANALISTA |
| 15 | `GET` | `/api/v1/admin/solicitacoes/{id}` | JWT | ANALISTA |
| 16 | `GET` | `/api/v1/admin/tipos-assistencia` | JWT | ANALISTA |
| 17 | `POST` | `/api/v1/admin/solicitacoes/{id}/assumir` | JWT | ANALISTA |
| 18 | `POST` | `/api/v1/admin/solicitacoes/{id}/confirmar` | JWT | ANALISTA_RESPONSAVEL |
| 19 | `POST` | `/api/v1/admin/solicitacoes/{id}/recusar` | JWT | ANALISTA_RESPONSAVEL |
| 20 | `POST` | `/api/v1/admin/solicitacoes/{id}/iniciar-atendimento` | JWT | ANALISTA_RESPONSAVEL |
| 21 | `POST` | `/api/v1/admin/solicitacoes/{id}/registrar-prestador-acionado` | JWT | ANALISTA_RESPONSAVEL |
| 22 | `POST` | `/api/v1/admin/solicitacoes/{id}/concluir` | JWT | ANALISTA_RESPONSAVEL |
| 23 | `POST` | `/api/v1/admin/solicitacoes/{id}/assistencias` | JWT | ANALISTA_RESPONSAVEL |
| 24 | `PATCH` | `/api/v1/admin/solicitacao-assistencias/{id}` | JWT | ANALISTA_RESPONSAVEL |
| 25 | `GET` | `/api/v1/sync/version` | Não | — |
| 26 | `GET` | `/api/v1/sync/events` | Não | — (SSE) |

---

## 12. Enums de Status do Sistema

### Solicitação (`solicitacao.status`)
`RECEBIDA` | `EM_ANALISE` | `CONFIRMADA` | `RECUSADA_SEM_COBERTURA` | `EM_ATENDIMENTO` | `PRESTADOR_ACIONADO` | `CONCLUIDA`

### Prioridade (`solicitacao.prioridade`)
`NORMAL` | `CRITICA`

### Assistência (`assistencia.status`)
`INCLUIDA` | `PRESTADOR_ACIONADO` | `REMOVIDA`

### Pergunta (`pergunta.status`)
`PENDENTE` | `RESPONDIDA`

### Perfil (`user.perfil`)
`CLIENTE` | `ANALISTA`

### Grupos de Fila
| Grupo | Status |
|-------|--------|
| `PENDENTES` | `RECEBIDA` |
| `EM_ANDAMENTO` | `EM_ANALISE`, `CONFIRMADA`, `EM_ATENDIMENTO`, `PRESTADOR_ACIONADO` |
| `FINALIZADAS` | `CONCLUIDA`, `RECUSADA_SEM_COBERTURA` |

---

## 13. Regras de Negócio Consolidadas

1. **Uma solicitação ativa por apólice** — não pode criar outra se houver uma com status ativo
2. **Prioridade binária** — `NORMAL` ou `CRITICA` (calculada automaticamente)
3. **Protocolo sequencial** — `ORB-{YEAR}-{6 dígitos}`, sequencial por ano
4. **Idempotência na criação** — `Idempotency-Key` header = `id_solicitacao_cliente` body
5. **Acesso do analista é por seguradora** — só vê solicitações das seguradoras vinculadas em `tb_analista_seguradora`
6. **Transições validadas** — máquina de estados server-side, rejeita transições inválidas
7. **Optimistic locking** — cada write exige `version` atual, rejeita se desatualizado
8. **Histórico imutável** — cada transição gera registro em `historico_status`, nunca é alterado
9. **GUINCHO cria pergunta TAXI** — automaticamente ao incluir assistência tipo GUINCHO
10. **Resposta TAXI não inclui táxi automaticamente** — analista decide após revisar cobertura
11. **Senhas com bcrypt** — nunca armazenar senhas em texto plano
12. **Mascarar dados sensíveis** — CPF, CNPJ, placa retornam mascarados nos endpoints

---

## 14. Dependências Atualizadas (`requirements.txt`)

```
fastapi
uvicorn[standard]
mysql-connector-python
python-jose[cryptography]
passlib[bcrypt]
python-dotenv
pydantic>=2.0
pydantic-settings
requests
validate_docbr
```

---

## 15. Ordem de Implementação Sugerida

```
Fase 0 (Schema MySQL)
    ↓
Fase 1 (Infraestrutura API)
    ↓
Fase 2 (Autenticação) ──── testar login
    ↓
Fase 3 (Catálogos) ──────── testar tipos-ocorrencia
    ↓
Fase 4 (Área Cliente) ──── testar CRUD de solicitação
    ↓
Fase 5 (Perguntas/Táxi) ── testar resposta de táxi
    ↓
Fase 6 (Área Admin) ────── testar fluxo completo
    ↓
Fase 7 (Sync/SSE) ──────── testar real-time
    ↓
Fase 8 (Validação) ──────── ✅ FEITA (136 testes + smoke OK)
    ↓
Fase 9 (Roadmap: DER, CI/CD, CRUD de apólice) ──── ✅ FEITA (162 testes + smoke OK)
```

---

## 16. Fase 9 — Pendências do Roadmap (DER, Deploy/CI-CD, CRUD de Apólice) — ✅ FEITA (2026-09-15)

> ✅ **FEITA (2026-09-15)** — As 3 pendências do Roadmap/README foram resolvidas: DER documentado, CI/CD (GitHub Actions + Docker Compose) e CRUD administrativo de apólice com otimistic locking.
> 📄 Logs Fase 9: `docs/FASE9_ANALISE_APOLICES.md`, `docs/FASE9_PENDENCIAS_ROADMAP.md`, `docs/DER.md`.

| # | Item | O que foi feito |
|---|---|---|
| 9.1 | Diagrama do banco (DER) | ✅ `docs/DER.md` — Mermaid `erDiagram` com as 28 tabelas únicas de `database_estrutura.sql`, legenda de cardinalidade, notas de design (mascaramento, optimistic locking, sync, analista×seguradora) e 7 índices |
| 9.2 | Deploy / CI-CD | ✅ `.github/workflows/ci.yml` (push/PR em `main`/`develop`, matrix Python 3.10/3.11/3.12, pytest + smoke), `Dockerfile` (`python:3.12-slim`, uvicorn :8080) e `docker-compose.yml` (mysql 8 + api com healthcheck e init via `../database_estrutura.sql`) — validado com `docker compose config` |
| 9.3a | CRUD apólice — schemas | ✅ `schemas/apolice.py` — `ApoliceCreateRequest`, `ApoliceUpdateRequest` (com `version`), `ApoliceStatusRequest` |
| 9.3b | CRUD apólice — repositório | ✅ `repositories/apolice_repository.py` — SELECT base com JOINs (cliente/veículo/seguradora), `find_apolices` com filtros + `_parse_sort` whitelist, `apolice_by_id`, `create_apolice`, `update_apolice` (guard de versão), `update_apolice_status`, máscara `ORB-****-{last4}` + bump de revisão |
| 9.3c | CRUD apólice — serviço | ✅ `services/apolice_service.py` — `list_apolices`, `get_detalhe`, `criar_apolice` (valida seguradora do analista, data_fim > data_inicio), `atualizar_apolice` e `alterar_status_apolice` (409 `POLICY_VERSION_CONFLICT`), `_require_visible` (404 fora da seguradora) |
| 9.3d | CRUD apólice — rotas | ✅ 5 rotas adicionadas em `routers/admin.py` (perfil ANALISTA): `GET/GET{id}/POST/PATCH/POST{id}/status` — total de endpoints 26 → 31 |
| 9.3e | CRUD apólice — testes | ✅ `tests/test_apolice_service.py` (15) + `tests/test_apolice_routes.py` (11) |

**O que foi alterado (arquivos):**

| Arquivo | Mudança |
|---|---|
| `OrbySos_api/schemas/apolice.py` | **novo** — schemas de requisição de apólice (create/update/status) |
| `OrbySos_api/repositories/apolice_repository.py` | **novo** — acesso a dados de apólice (queries parametrizadas) |
| `OrbySos_api/services/apolice_service.py` | **novo** — regras de negócio do CRUD de apólice |
| `OrbySos_api/routers/admin.py` | +5 rotas de apólice (listar, detalhe, criar, atualizar, status) |
| `OrbySos_api/tests/test_apolice_service.py` | **novo** — 15 testes unitários |
| `OrbySos_api/tests/test_apolice_routes.py` | **novo** — 11 testes HTTP |
| `OrbySos_api/.github/workflows/ci.yml` | **novo** — pipeline CI (test matrix 3.10/3.11/3.12 + smoke) |
| `OrbySos_api/Dockerfile` | **novo** — imagem da API (python:3.12-slim, uvicorn :8080) |
| `OrbySos_api/docker-compose.yml` | **novo** — orquestração db (mysql 8) + api |
| `docs/DER.md` | **novo** — diagrama entidade-relacionamento (Mermaid) |
| `docs/FASE9_ANALISE_APOLICES.md` | **novo** — log do CRUD de apólice |
| `docs/FASE9_PENDENCIAS_ROADMAP.md` | **novo** — log do fechamento das pendências |
| `OrbySos_api/README.md` | Roadmap ✅ (DER, Deploy/CI-CD, CRUD apólice); tabela de endpoints 26 → 31; total de testes 136 → 162 |

**Validação executada (evidence):**

```
pytest tests/ -q  →  162 passed (2 warnings)   (136 + 15 service + 11 routes)
smoke_phase1.py   →  SMOKE_TEST_OK
docker compose config  →  COMPOSE_OK
```

**Pendência:** validação ponta-a-ponta contra MySQL real (não há listener 3306 no ambiente) e execução do pipeline CI/Docker em um ambiente com Docker rodando.

---

## 17. Validação ponta-a-ponta contra MySQL real — ✅ FEITA (2026-09-16)

> 📄 Detalhes completos em `docs/TESTE_VALIDACAO_2026-09-16.md` e `docs/SEED_DADOS_TESE.md`.

**Objetivo:** confirmar que a API funciona de ponta a ponta com o banco MySQL real (`orbyt`, `192.168.68.63`) após importação da seed de dados.

### 17.1 — Seed de dados

| Ação | Status |
|:---|:---|
| Arquivo `seed_dados_teste.sql` criado (raiz do repo, 20 pessoas, 18 users, 20 veículos, 20 apólices, 16 vínculos analista×seguradora) | ✅ |
| Seed executada no MySQL (`192.168.68.63`, user `Senac`) | ✅ |
| Acentos corrompidos pela importação CLI (`charset` errado) → corrigidos via UPDATE `utf8mb4` | ✅ |

### 17.2 — Bugs corrigidos durante a validação

| Bug | Arquivo | Fix |
|:---|:---|:---|
| Variáveis legadas `host/user/password/bank/port` rejeitadas por `pydantic-settings` | `core/config.py` | Adicionado `extra = "ignore"` ao `Config` |
| Queries de login não selecionavam `u.senha` → `KeyError` com DB real | `repositories/user_repository.py` | `u.senha` adicionado a `_FIND_CLIENT_BY_CPF` e `_FIND_ANALYST_BY_LOGIN` |
| Queries referenciavam `tu.id_usuario` (coluna inexistente, era `id_user`) | `repositories/solicitacao_repository.py`, `repositories/admin_repository.py` | `tu.id_user AS id_usuario` (alias compatível com DTOs) |

### 17.3 — Endpoints validados contra MySQL real

Login cliente (CPF), login analista (login), `/me`, `/clientes/me`, `/clientes/me/apolices`,
`/solicitacoes` (criação 201), `/solicitacoes/{id}` (detalhe),
`/admin/dashboard`, `/admin/solicitacoes`, `/admin/apolices`, `/admin/tipos-assistencia`,
transições de estado (assumir → confirmar → iniciar → assistência → concluir),
pergunta TAXI criada automaticamente (GUINCHO), resposta do cliente,
SSE version com `revision` incremental — **todos OK**.

### 17.4 — Regressão

```
pytest tests/ -q  →  162 passed (2 warnings)
smoke_phase1.py   →  SMOKE_TEST_OK
```

### 17.5 — Novos artefatos

| Arquivo | Descrição |
|:---|:---|
| `seed_dados_teste.sql` | Dados de demonstração (18 users, 20 apólices, etc.) |
| `docs/SEED_DADOS_TESE.md` | Documentação da seed |
| `docs/TESTE_VALIDACAO_2026-09-16.md` | Log completo da validação ponta-a-ponta |
| `OrbySos_api/README.md` | Atualizado: seção Documentação, roadmap seed+validação, contagens 136→162 |

**Pendência restante:** execução do pipeline CI/Docker em ambiente com Docker rodando (o pipeline testa com MySQL em container, mas o banco do host é usado no desenvolvimento local).
