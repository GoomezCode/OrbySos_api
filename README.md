<div align="center">

# 🚨 OrbySOS API

### API REST para gestão de seguros veiculares, ocorrências e assistências

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Status](https://img.shields.io/badge/status-est%C3%A1vel-2ea44f?style=for-the-badge)]()

</div>

---

## 📖 Sobre o projeto

<div align="center">

**OrbySOS** é uma API desenvolvida com **FastAPI** para o gerenciamento de
**clientes**, **veículos**, **endereços**, **apólices de seguro**, **ocorrências**
e **assistências** — voltada para um sistema de atendimento e suporte semelhante
a um SOS de seguradora.

A API possui **autenticação por JWT**, dois perfis de acesso (CLIENTE e ANALISTA),
conexão com banco **MySQL** (pool de conexões), sincronização em tempo real via
**Server-Sent Events (SSE)**, integração à [BrasilAPI](https://brasilapi.com.br/)
para consulta automática de **CEP** e mais de **130 testes automatizados**.

</div>

---

## 🛠️ Tecnologias utilizadas

<div align="center">

| Tecnologia | Finalidade |
|:---:|:---:|
| **FastAPI** | Framework web para construção da API |
| **Uvicorn** | Servidor ASGI para execução da aplicação |
| **MySQL Connector** | Pool de conexões com o banco de dados MySQL |
| **Pydantic v2** | Validação e tipagem dos dados de entrada/saída |
| **python-jose** | Geração e verificação de tokens JWT |
| **bcrypt** | Criptografia de senhas |
| **python-dotenv / pydantic-settings** | Configuração via variáveis de ambiente |
| **requests** | Consumo da API externa de CEP (BrasilAPI) |
| **validate-docbr** | Validação de CPF e CNPJ |

</div>

---

## 📂 Estrutura do projeto

```
OrbySos_api/
├── main.py                # FastAPI app, handler global de erros, CORS, registro dos routers
├── core/                  # config (.env), pool MySQL, security (JWT), deps, errors
│   ├── config.py          #   Settings via pydantic-settings
│   ├── database.py        #   Pool de conexões MySQL (5 conexões)
│   ├── security.py        #   Geração/decodificação de tokens JWT
│   ├── deps.py            #   Dependências: sessão atual, require_perfil
│   └── errors.py          #   Envelope padrão de erro {error, trace_id}
├── routers/               # Camada HTTP — 31 endpoints (prefixo /api/v1)
│   ├── auth.py            #   login clientes/analistas, me, logout
│   ├── catalogs.py        #   tipos-ocorrencia, configurações públicas
│   ├── client.py          #   área do cliente (solicitações, apólices, perguntas)
│   ├── admin.py           #   área do analista (fila, transições, assistências)
│   └── sync.py            #   version + SSE de sincronização
├── services/              # Camada de negócio
├── repositories/          # Acesso a dados (SQL parameterizado, bump de revisão)
├── schemas/               # Modelos Pydantic
├── middleware/            # auth (Bearer token JWT)
├── tests/                 # 136 testes (pytest) + smoke
├── .env.example           # Variáveis de ambiente de exemplo
└── requeriments.txt       # Dependências do projeto
```

---

## 🚀 Como executar o projeto

<div align="center">

### 1️⃣ Clone o repositório e acesse a pasta

```bash
git clone https://github.com/GoomezCode/OrbySos_api.git
cd OrbySos_api
```

### 2️⃣ Crie e ative a virtualenv, e instale as dependências

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows
pip install -r requeriments.txt
```

### 3️⃣ Configure as variáveis de ambiente

Copie o `.env.example` para `.env` e ajuste os valores do seu banco MySQL e do JWT:

```bash
cp .env.example .env
```

```env
# ===== MySQL =====
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=orbyt
DB_PORT=3306

# ===== JWT =====
JWT_SECRET=CHANGE_ME_IN_PRODUCTION
JWT_ALGORITHM=HS256
JWT_EXPIRE_SECONDS=3600
```

> ⚠️ Em produção, troque `JWT_SECRET` por um valor forte e aleatório.

### 4️⃣ Prepare o banco de dados

O schema MySQL completo está no arquivo `../database_estrutura.sql` (na raiz do
workspace, banco `orbyt`). Importe-o antes da primeira execução.

### 5️⃣ Execute a aplicação

```bash
python main.py
```

A API ficará disponível em **http://localhost:8080**:

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
- OpenAPI JSON: http://localhost:8080/openapi.json
- Health check: http://localhost:8080/

</div>

---

## 🔐 Autenticação

<div align="center">

Quase todos os endpoints exigem o header `Authorization: Bearer <token>`.
Os tokens são obtidos nos endpoints de login e decodificados pelo middleware
`middleware/auth.py`.

**Perfis de acesso:**

| Perfil | Login | Acesso |
|:---|:---|:---|
| **CLIENTE** | `POST /api/v1/auth/clientes/login` | Área do cliente |
| **ANALISTA** | `POST /api/v1/auth/analistas/login` | Área administrativa |

**Rotas públicas** (não exigem token): `/`, `/docs`, `/redoc`, `/openapi.json`,
`/api/v1/auth/clientes/login`, `/api/v1/auth/analistas/login`,
`/api/v1/sync/version`, `/api/v1/sync/events`.

**Exemplo de uso:**

```bash
# Login
curl -s -X POST http://localhost:8080/api/v1/auth/clientes/login \
  -H "Content-Type: application/json" \
  -d '{"cpf":"123.456.789-00","senha":"sua_senha"}'

# Acesso autenticado
curl -s http://localhost:8080/api/v1/clientes/me \
  -H "Authorization: Bearer <token>"
```

</div>

---

## 📡 Endpoints (31 total — prefixo `/api/v1`)

### 🔑 Auth

| Método | Rota | Perfil |
|:---:|:---|:---:|
| `POST` | `/auth/clientes/login` | Público |
| `POST` | `/auth/analistas/login` | Público |
| `GET` | `/auth/me` | Qualquer |
| `POST` | `/auth/logout` | Qualquer |

### 📚 Catálogos

| Método | Rota | Perfil |
|:---:|:---|:---:|
| `GET` | `/tipos-ocorrencia?ativo=` | Qualquer |
| `GET` | `/configuracoes/publicas` | Qualquer |

### 👤 Área do Cliente

| Método | Rota | Perfil |
|:---:|:---|:---:|
| `GET` | `/clientes/me` | CLIENTE |
| `GET` | `/clientes/me/apolices?status=&page=&page_size=` | CLIENTE |
| `POST` | `/solicitacoes` (header `Idempotency-Key`) | CLIENTE |
| `GET` | `/clientes/me/solicitacoes?status=&active_only=&page=&page_size=` | CLIENTE |
| `GET` | `/solicitacoes/{solicitacao_id}` | CLIENTE (dono) |
| `POST` | `/perguntas/{pergunta_id}/resposta` | CLIENTE (dono) |

### 🛠️ Área do Analista

| Método | Rota | Perfil |
|:---:|:---|:---:|
| `GET` | `/admin/dashboard` | ANALISTA |
| `GET` | `/admin/solicitacoes` (filtros: status, prioridade, tipo_ocorrencia_id, datas, numero, pessoa, placa, sort, paginação) | ANALISTA |
| `GET` | `/admin/solicitacoes/{solicitacao_id}` | ANALISTA |
| `GET` | `/admin/tipos-assistencia` | ANALISTA |
| `POST` | `/admin/solicitacoes/{id}/assumir` | ANALISTA |
| `POST` | `/admin/solicitacoes/{id}/confirmar` | ANALISTA |
| `POST` | `/admin/solicitacoes/{id}/recusar` | ANALISTA |
| `POST` | `/admin/solicitacoes/{id}/iniciar-atendimento` | ANALISTA |
| `POST` | `/admin/solicitacoes/{id}/registrar-prestador-acionado` | ANALISTA |
| `POST` | `/admin/solicitacoes/{id}/concluir` | ANALISTA |
| `POST` | `/admin/solicitacoes/{id}/assistencias` | ANALISTA |
| `PATCH` | `/admin/solicitacao-assistencias/{assistance_id}` | ANALISTA |
| `GET` | `/admin/apolices` (filtros: status, numero_apolice, pessoa, placa, seguradora, sort, paginação) | ANALISTA |
| `GET` | `/admin/apolices/{apolice_id}` | ANALISTA |
| `POST` | `/admin/apolices` | ANALISTA |
| `PATCH` | `/admin/apolices/{apolice_id}` (`version` obrigatório) | ANALISTA |
| `POST` | `/admin/apolices/{apolice_id}/status` (`version` obrigatório) | ANALISTA |

> A maioria das ações no admin exige `version` no body — **controle de concorrência
> otimista** retorna `409 REQUEST_VERSION_CONFLICT` se a versão estiver obsoleta
> (nas apólices, `POLICY_VERSION_CONFLICT`).

### 🔄 Sincronização em tempo real

| Método | Rota | Descrição |
|:---:|:---|:---|
| `GET` | `/sync/version` | Revisão atual do banco (`{revision, updated_at}`) |
| `GET` | `/sync/events` | SSE — eventos de mudança de revisão |

O `GET /api/v1/sync/events` é um **Server-Sent Event** (`text/event-stream`) que
mantém a conexão aberta e emite a nova revisão sempre que o banco muda (`revision`
é incrementada atomicamente em toda transação de escrita — ver `sync_repository.py`).

---

## ⚠️ Padrão de erro

<div align="center">

Todos os erros seguem um envelope padronizado com `error` e `trace_id`:

```json
{
  "trace_id": "trace-2c550360b7ca4e90a37d236cb23292d4",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Erro de validação.",
    "fields": {
      "senha": "Senha deve conter pelo menos 6 caracteres."
    }
  }
}
```

| Status | Código típico |
|:---:|:---|
| `400` | Erro de negócio |
| `401` | `UNAUTHORIZED` / `INVALID_TOKEN` / `AUTH_INVALID_CREDENTIALS` |
| `403` | `FORBIDDEN` / `AUTH_INACTIVE_USER` |
| `404` | `NOT_FOUND` |
| `409` | `REQUEST_VERSION_CONFLICT` / `POLICY_ACTIVE_REQUEST_EXISTS` |
| `422` | `VALIDATION_ERROR` (com `fields`) |
| `500` | `INTERNAL_ERROR` |

</div>

---

## 🧪 Testes

<div align="center">

A suíte possui **136 testes** distribuídos em 16 módulos (auth, catálogos, cliente,
admin, sync, taxi, revisão, fluxos completos e edge-cases) além de um smoke test.

```bash
# Executar toda a suíte
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q

# Smoke test (rotas públicas, CORS, 401)
PYTHONPATH=. .venv/bin/python tests/smoke_phase1.py
```

| Item | Status |
|:---|:---:|
| Total de testes | ✅ 136 passando |
| Smoke test | ✅ `SMOKE_TEST_OK` |
| Fluxo cliente completo | ✅ `test_flow_cliente.py` |
| Fluxo admin completo | ✅ `test_flow_admin.py` |
| Edge-cases (401/403/404/409/422/500) | ✅ `test_edge_cases.py` |
| Auditoria de SQL Injection | ✅ Todas as queries parameterizadas |

</div>

---

## 🗺️ Roadmap / Pendências

<div align="center">

| Item | Status |
|:---|:---:|
| Autenticação e autorização (JWT) | ✅ Concluído |
| Testes automatizados | ✅ Concluído (162) |
| Padronização das mensagens de erro | ✅ Concluído (envelope único) |
| Sincronização em tempo real (SSE) | ✅ Concluído |
| Controle de concorrência otimista (`version`) | ✅ Concluído |
| Diagrama do banco de dados (DER) | ✅ Concluído — [docs/DER.md](../docs/DER.md) |
| Deploy / CI-CD | ✅ Concluído — GitHub Actions + Docker (`ci.yml`, `Dockerfile`, `docker-compose.yml`) |
| Rotas de `apólice` (CRUD completo) | ✅ Concluído — Admin: listar, detalhe, criar, atualizar, status |

</div>

---

<div align="center">

### 👤 Autor

Desenvolvido por **[GoomezCode](https://github.com/GoomezCode)**
</div>