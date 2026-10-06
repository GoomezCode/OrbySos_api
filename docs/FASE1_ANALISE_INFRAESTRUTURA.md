# Fase 1 — Infraestrutura da API — Análise Técnica (2026-09-15)

> **Status:** ✅ FEITA
> **Objetivo:** Base sólida: prefixo `/api/v1`, connection pooling, JWT, middleware de auth, dependências FastAPI.

## Ações aplicadas (1.1–1.8)

| # | Ação | Arquivo |
|---|---|---|
| 1.1 | Criar estrutura de pastas `core/`, `routers/`, `services/`, `repositories/`, `middleware/`, `schemas/` | todos com `__init__.py` |
| 1.2 | Configurar prefixo `/api/v1` | `main.py` — todos os routers com `prefix="/api/v1"` |
| 1.3 | Implementar connection pooling | `core/database.py` — `mysql.connector.pooling.MySQLConnectionPool` (pool_size=5) + `get_connection()` |
| 1.4 | Configurar JWT | `core/security.py` — `create_access_token`, `decode_access_token` via `python-jose`; hashing via `bcrypt` direto |
| 1.5 | Criar middleware de auth | `middleware/auth.py` — Bearer obrigatório, paths públicos, injeção de `request.state.session` |
| 1.6 | Criar dependências FastAPI | `core/deps.py` — `get_current_session()`, `require_perfil(*perfis)` |
| 1.7 | Configurar `.env` | `.env.example` — `JWT_SECRET`, `JWT_ALGORITHM=HS256`, `JWT_EXPIRE_SECONDS=3600` + vars MySQL |
| 1.8 | Atualizar `requirements.txt` | UTF-8 (era UTF-16 de `pip freeze`) |

## Estrutura de Pastas Resultante

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
└── database/               # (legado, será substituído por core/database.py)
    ├── DataBase.py
    ├── select.py
    └── insert.py
```

## Outras mudanças

- **`main.py`:** reescrito — título/descrição, CORS (`allow_origins=["*"]`), middleware de auth, prefixo `/api/v1`, rota `/` como health check público, porta padrão 8080.
- **pydantic-settings:** `core/config.py` com `Settings` cacheado (`get_settings()`) — vars MySQL (`DB_*`) + JWT, com env fallback para os nomes legados (`host/user/password/bank/port`).
- **Código legado preservado:** arquivos em `api/`, `database/`, `classes/`, `util/` continuam funcionando sob `/api/v1`.
- **`.gitignore`:** adicionado `.venv/`.

## Decisões técnicas

- **`passlib[bcrypt]` substituído por `bcrypt` direto** — `passlib==1.7.4` é incompatível com `bcrypt>=4.1` (bug do `bcrypt.__about__.__version__`). O projeto já usava `bcrypt` diretamente em `util/function.py`. Isso remove `passlib` de `requirements.txt`.
- **Teste de fumaca criado:** `tests/smoke_phase1.py` (usa `httpx2`, dependência de TESTE apenas — não adicionado ao `requirements.txt`).

## Validação executada (evidence)

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

**Observação importante:** com o middleware ativo, todo endpoint protegido retorna **401** até a Fase 2 implementar `login` + emissão de JWT. Inclua `JWT_SECRET` real no `.env` em produção.

## Pendências

- Nenhuma. Base validada e pronta para a Fase 2 (Autenticação).