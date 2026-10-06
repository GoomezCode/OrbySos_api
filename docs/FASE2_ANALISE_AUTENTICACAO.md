# Fase 2 — Autenticação — Análise Técnica (2026-09-15)

> **Status:** ✅ FEITA
> **Objetivo:** 4 endpoints de autenticação (login cliente, login analista, sessão atual, logout).

## Endpoints

| # | Método | Endpoint | Scope | Descrição |
|---|--------|----------|-------|-----------|
| 2.1 | `POST` | `/api/v1/auth/clientes/login` | PÚBLICO | CPF + senha → JWT + session |
| 2.2 | `POST` | `/api/v1/auth/analistas/login` | PÚBLICO | login + senha → JWT + session |
| 2.3 | `GET` | `/api/v1/auth/me` | AUTENTICADO | Decodificar JWT → session |
| 2.4 | `POST` | `/api/v1/auth/logout` | AUTENTICADO | Retornar 204 (stateless) |

## Respostas Esperadas

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

## Validezes de Negócio

- **Cliente login:** CPF normalizado (remover não-dígitos), validar dígitos verificadores, buscar `tb_user` com `perfil='CLIENTE'` + `fk_status` ativo, comparar senha com bcrypt
- **Analista login:** Login lowercase + trim, buscar `tb_user` com `perfil='ANALISTA'` + ativo, montar `seguradoras[]` via `tb_analista_seguradora`

## Arquivos novos

| # | Arquivo | Conteúdo |
|---|---|---|
| 2.1 | `schemas/auth.py` | `ClienteLoginRequest`, `AnalistaLoginRequest`, `SessaoInfo`, `AuthEnvelope` (Pydantic v2) |
| 2.2 | `repositories/user_repository.py` | Queries parametrizadas: `find_client_by_cpf`, `find_analyst_by_login`, `find_analyst_insurers`, `find_insurer` |
| 2.3 | `services/auth_service.py` | Lógica de login (CPF normalizado + dígitos verificadores, bcrypt compare, sessão de saída), `login_client`, `login_analyst` |
| 2.4 | `routers/auth.py` | 4 endpoints: `POST /auth/clientes/login`, `POST /auth/analistas/login`, `GET /auth/me`, `POST /auth/logout` |

## Arquivos modificados

| Arquivo | Mudança |
|---|---|
| `main.py` | `apiAuth` legado removido; novo `routers/auth` incluído |
| `middleware/auth.py` | Session injetada com campos completos (`id_usuario`, `id_pessoa`, `perfil`, `nome_exibicao`, `seguradora`, `seguradoras`) — decodificação do JWT |

## Decisões técnicas

- **validate_docbr** usado para validar dígitos verificadores do CPF no login cliente (fail-fast: 401 sem tocar no DB)
- **Seguradora principal** do analista derivada de `tb_user.fk_seguradora`; fallback para primeira da lista `tb_analista_seguradora` se nula
- `/auth/logout` retorna **204 stateless** (o frontend limpa o token localmente; o JWT expira naturalmente)

## Testes executados (evidence)

```
tests/test_auth_service.py   — 10 testes unitários (mock do repositório) — PASS
tests/test_auth_routes.py    — 8 testes HTTP (TestClient, token forjado)  — PASS
tests/smoke_phase1.py        — Sem regressão, 25 rotas /api/v1            — SMOKE_TEST_OK
```

## Pendências

- Fluxo ponta-a-ponta (DB real) requer MySQL `orbyt` local com seed de dados.