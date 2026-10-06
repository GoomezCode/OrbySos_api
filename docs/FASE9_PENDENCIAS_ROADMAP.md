# FASE 9 — Pendências do Roadmap: DER, Deploy/CI-CD

> **Data:** 2026-09-15
> **Status:** ✅ FEITA
> **Objetivo:** Fechar as pendências do Roadmap do `OrbySos_api/README.md` que não eram código da API em si: Diagrama Entidade-Relacionamento (DER) e Deploy/CI-CD.
> **CRUD de apólice:** registrado em `docs/FASE9_ANALISE_APOLICES.md`.

---

## 1. Diagrama Entidade-Relacionamento (DER)

**Arquivo:** `docs/DER.md` (novo)

- Mermaid `erDiagram` com as **28 tabelas únicas** de `database_estrutura.sql` (banco `orbyt`).
- Legenda explicando a leitura das cardinalidades (ex.: `||--o{`, `o{--o{`).
- Notas de design documentadas:
  - Mascaramento de dados sensíveis (`cpf_mascarado`, `cnpj_mascarado`, `placa_mascarada`, `numero_apolice_mascarado`).
  - Optimistic locking (`version` em `tb_solicitacao`, `tb_pergunta`, `tb_solicitacao_assistencia`, `tb_apolice`).
  - Sync de revisão (`orbyt_meta` + `bump_revision`).
  - Vínculo analista×seguradora (`tb_analista_seguradora`).
- 7 índices documentados (destaque para `idx_solicitacao_seguradora_status` e `idx_analista_seguradora_*`).
- Data de geração e origem (exportação das tabelas do SQL).

## 2. Deploy / CI-CD

### 2.1 GitHub Actions — `.github/workflows/ci.yml`

- Triggers: `push` e `pull_request` nas branches `main` e `develop`.
- Matrix de Python: **3.10, 3.11, 3.12**.
- Passos: `actions/checkout@v4` → setup-python → instala `requeriments.txt` → `pytest tests/ -q` → smoke (`PYTHONPATH=. .venv/bin/python tests/smoke_phase1.py`).
- `working-directory: .` (a raiz do repo git é `OrbySos_api`).
- Como a suíte usa **mocks de repositório** (não exige MySQL no CI), a suíte roda de forma hermética.

### 2.2 Dockerfile

- Base `python:3.12-slim`.
- Instala `requeriments.txt`.
- `EXPOSE 8080`, `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]`.

### 2.3 docker-compose.yml

- Serviço `db`: `mysql:8.0`, env `MYSQL_ROOT_PASSWORD=${DB_PASSWORD:-orbyt_dev}`, `MYSQL_DATABASE=orbyt`, init via `../database_estrutura.sql` em `/docker-entrypoint-initdb.d/01_schema.sql`, healthcheck de MySQL.
- Serviço `api`: build do `Dockerfile`, porta `${API_PORT:-8080}:8080`, env `DB_HOST=db`, `DB_*` e `JWT_*` herdados do `.env` (`env_file`), `depends_on: db (condition: service_healthy)`.
- Validado localmente com `docker compose config -q` → `COMPOSE_OK`.

## 3. Validação executada (evidence)

```
pytest tests/ -q      →  162 passed (2 warnings)
smoke_phase1.py       →  SMOKE_TEST_OK
docker compose config →  COMPOSE_OK
```

## 4. Pendências

- Rodar o pipeline CI/GitHub Actions de fato (requer push para o repo remoto).
- Subir o stack `docker compose up` e validar o endpoint `/` + health do MySQL em ambiente com Docker ativo (o ambiente atual não tem listener 3306).
- No formato CI isolado (sem o workspace com `database_estrutura.sql` na raiz), o `docker-compose.yml` precisa apontar para um cópia do SQL; documentar no próprio compose.