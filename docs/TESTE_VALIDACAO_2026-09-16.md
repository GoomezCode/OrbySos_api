# Teste de Validação — Seed + API (16/09/2026)

> **Data:** 2026-09-16
> **Objetivo:** Validar a API FastAPI contra MySQL real (`orbyt`) após aplicação da seed de dados
> **Resultado:** ✅ OK — todos os fluxos validados, 162 testes pytest passando, smoke OK

---

## 1. Dados do banco após seed

| Tabela | Registros |
|:---|:---|
| `tb_pessoa` | 20 (10 clientes + 8 analistas + 2 seguradoras) |
| `tb_pessoa_fisica` | 18 |
| `tb_pessoa_juridica` | 2 (Horizonte 110 / Órbita 120) |
| `tb_user` | 18 (10 CLIENTE + 8 ANALISTA) |
| `tb_contato` | 4 (urgência/WhatsApp × 2 seguradoras) |
| `tb_veiculo` | 20 |
| `tb_apolice` | 20 (`fk_segurado` 110/120 — todos preenchidos) |
| `tb_analista_seguradora` | 16 (8 × 2) |

---

## 2. Bugs corrigidos durante a validação

### 2.1 — `core/config.py` — variáveis legadas rejeitadas
**Causa:** `Settings()` de pydantic-settings rejeita as variáveis `host/user/password/bank/port`
 do `.env` (legadas, usadas por `database/DataBase.py`) com `extra_forbidden`.
**Fix:** adicionado `extra = "ignore"` ao `Config` de `Settings`.

### 2.2 — Queries de login não selecionavam `u.senha`
**Causa:** `_FIND_CLIENT_BY_CPF` e `_FIND_ANALYST_BY_LOGIN` em `user_repository.py`
não tinham `u.senha` no SELECT — os testes unitários passavam por usar mock, mas com
MySQL real o acesso `row["senha"]` dava `KeyError`.
**Fix:** adicionado `u.senha` ao SELECT de ambas as queries.

### 2.3 — Referência SQL `tu.id_usuario` não existia
**Causa:** queries em `solicitacao_repository.py` e `admin_repository.py` usavam
`tu.id_usuario` mas a coluna real é `tu.id_user`. Os mocks nos testes retornavam
dict com `id_usuario`, escondendo o bug.
**Fix:** trocado por `tu.id_user AS id_usuario` (alias compatível com os DTOs).

### 2.4 — Encoding corrompido na importação do SQL
**Causa:** o `mysql` CLI (ou o ambiente de importação) não estava usando `utf8mb4`,
causando perda de acentos em todos os campos textuais da seed e do schema.
**Fix:** UPDATE manual via `python + mysql.connector` com `charset='utf8mb4'` para
todos os registros corrompidos (pessoas, user, contatos, catálogos).

---

## 3. Endpoints validados contra MySQL real

| # | Método | Endpoint | Resultado |
|:--|:---|:---|:---:|
| 1 | `GET` | `/` (health check) | ✅ 200 |
| 2 | `POST` | `/api/v1/auth/clientes/login` | ✅ 200 + JWT |
| 3 | `POST` | `/api/v1/auth/analistas/login` | ✅ 200 + JWT |
| 4 | `GET` | `/api/v1/auth/me` (cliente) | ✅ 200 |
| 5 | `GET` | `/api/v1/auth/me` (analista) | ✅ 200 |
| 6 | `GET` | `/api/v1/clientes/me` | ✅ 200 |
| 7 | `GET` | `/api/v1/clientes/me/apolices` | ✅ 200 |
| 8 | `GET` | `/api/v1/tipos-ocorrencia` | ✅ 200 |
| 9 | `GET` | `/api/v1/configuracoes/publicas` | ✅ 200 |
| 10 | `GET` | `/api/v1/sync/version` | ✅ 200 (revision=10) |
| 11 | `GET` | `/api/v1/admin/dashboard` | ✅ 200 |
| 12 | `GET` | `/api/v1/admin/solicitacoes` | ✅ 200 |
| 13 | `GET` | `/api/v1/admin/apolices` | ✅ 200 |
| 14 | `GET` | `/api/v1/admin/tipos-assistencia` | ✅ 200 |
| 15 | `POST` | `/api/v1/solicitacoes` | ✅ 201 |
| 16 | `GET` | `/api/v1/solicitacoes/{id}` | ✅ 200 |
| 17 | `GET` | `/api/v1/clientes/me/solicitacoes` | ✅ 200 |
| 18 | `POST` | `/api/v1/admin/solicitacoes/{id}/assumir` | ✅ 200 |
| 19 | `POST` | `/api/v1/admin/solicitacoes/{id}/confirmar` | ✅ 200 |
| 20 | `POST` | `/api/v1/admin/solicitacoes/{id}/iniciar-atendimento` | ✅ 200 |
| 21 | `POST` | `/api/v1/admin/solicitacoes/{id}/assistencias` (GUINCHO) | ✅ 200 + pergunta TAXI |
| 22 | `POST` | `/api/v1/perguntas/{id}/resposta` | ✅ 200 |
| 23 | `PATCH` | `/api/v1/admin/solicitacao-assistencias/{id}` | ✅ 200 |
| 24 | `POST` | `/api/v1/admin/solicitacoes/{id}/concluir` | ✅ 200 |

---

## 4. Regressão

```
pytest tests/ -q  →  162 passed (2 warnings)   (3.39s)
smoke_phase1.py    →  SMOKE_TEST_OK
```

---

## 5. Artefatos gerados

| Arquivo | Caminho |
|:---|:---|
| Seed SQL | `seed_dados_teste.sql` (raiz do repo) |
| Doc seed | `docs/SEED_DADOS_TESE.md` |
| Doc teste (este) | `docs/TESTE_VALIDACAO_2026-09-16.md` |

## 6. Observações

- O processo anterior à API ficava com múltiplos processos (`uvicorn --reload`) por causa
  do WatchFiles. Para testes, o ideal é subir com `uvicorn main:app --no-reload`.
- As variáveis legadas (`host/user/password/bank/port`) no `.env` devem ser eventualmente
  removidas quando o `database/DataBase.py` legado for substituído por `core/database.py`.