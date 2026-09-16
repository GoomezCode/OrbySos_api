# Fase 6 — Área do Admin — Análise Técnica (2026-09-15)

## Endpoints

| # | Método | Rota | Scope | Descrição |
|---|--------|------|-------|-----------|
| 6.1 | `GET` | `/admin/dashboard` | ANALISTA | Métricas + fila_prioritaria (5 itens) |
| 6.2 | `GET` | `/admin/solicitacoes` | ANALISTA | Fila filtrada paginada |
| 6.3 | `GET` | `/admin/solicitacoes/{id}` | ANALISTA | Detalhe completo |
| 6.4 | `GET` | `/admin/tipos-assistencia` | ANALISTA | Catálogo ativo |
| 6.5 | `POST` | `/admin/solicitacoes/{id}/assumir` | ANALISTA | Análise: RECEBIDA → EM_ANALISE |
| 6.6 | `POST` | `/admin/solicitacoes/{id}/confirmar` | ANALISTA_RESPONSAVEL | EM_ANALISE → CONFIRMADA |
| 6.7 | `POST` | `/admin/solicitacoes/{id}/recusar` | ANALISTA_RESPONSAVEL | EM_ANALISE → RECUSADA_SEM_COBERTURA |
| 6.8 | `POST` | `/admin/solicitacoes/{id}/iniciar-atendimento` | ANALISTA_RESPONSAVEL | CONFIRMADA → EM_ATENDIMENTO |
| 6.9 | `POST` | `/admin/solicitacoes/{id}/registrar-prestador-acionado` | ANALISTA_RESPONSAVEL | EM_ATENDIMENTO → PRESTADOR_ACIONADO |
| 6.10 | `POST` | `/admin/solicitacoes/{id}/concluir` | ANALISTA_RESPONSAVEL | (EM_ATENDIMENTO / PRESTADOR_ACIONADO) → CONCLUIDA |
| 6.11 | `POST` | `/admin/solicitacoes/{id}/assistencias` | ANALISTA_RESPONSAVEL | Adicionar assistência |
| 6.12 | `PATCH` | `/admin/solicitacao-assistencias/{id}` | ANALISTA_RESPONSAVEL | Alterar status assistência |

## Máquina de Estados Solicitação

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
```

## Máquina de Estados Assistência (tb_solicitacao_assistencia)

```
INCLUIDA ──► AGUARDANDO_PRESTADOR ──► PRESTADOR_ACIONADO ──► EM_DESLOCAMENTO ──► CONCLUIDA (terminal)
   │                                        │                        │
   └──► REMOVIDA (terminal)                 └──► CANCELADA (terminal)
```

## Acesso do Analista (seguradora-scoped)

- `session.seguradoras` → `[{id_pj, nome_fantasia}]`
- `seguradora_ids = {int(s["id_pj"]) for s in session.seguradoras}`
- Query sempre filtra `ts.fk_seguradora IN (seguradora_ids)`
- Endpoints read (6.1-6.4): qualquer analista vinculado
- Endpoints write (6.5): qualquer analista vinculado, desde que a transição seja válida
- Endpoints write (6.6-6.12): exige `fk_analista_responsavel = id_usuario`

## DTOs

### Dashboard (6.1)
```json
{
  "metricas": {
    "criticas_abertas": int,
    "aguardando_analise": int,
    "confirmadas_em_atendimento": int,
    "prestadores_acionados": int,
    "concluidas": int,
    "recusadas_sem_cobertura": int
  },
  "fila_prioritaria": { "items": [requestAggregateDto] }  // primeiros 5
}
```

### Fila solicitacoes (6.2)
```json
{
  "items": [requestAggregateDto],
  "pagination": { "page": 1, "page_size": 20, "total_items": N, "total_pages": M }
}
```

### Detalhe admin (6.3)
```json
{
  "solicitacao": requestCoreDto,
  "cliente": clienteDto,
  "apolice": apoliceDto,
  "veiculo": veiculoDto,
  "seguradora": { "id_pj": N, "nome_fantasia": "..." },
  "ocorrencia": { "id_tipo_ocorrencia": N, "codigo": "...", "nome": "...", "descricao": "..." },
  "analista": analistaDto | null,
  "assistencias": [assistanceDto],
  "perguntas": [questionDto],
  "historico": [historyDto],
  "tipos_assistencia_disponiveis": [assistanceTypeDto]
}
```

### Command responses (6.5-6.10)
```json
{ "solicitacao": requestAggregateDto }
```

### Add assistencia (6.11)
```json
{
  "assistencia": assistanceDto,
  "pergunta_criada": questionDto | null,
  "solicitacao": requestAggregateDto
}
```

### Update assistencia status (6.12)
```json
{ "assistencia": assistanceDto }
```

## Erros de Negocio

| Code | HTTP | Cenario |
|------|------|---------|
| REQUEST_NOT_FOUND | 404 | Solicitacao nao existe ou sem acesso a seguradora |
| ASSISTANCE_NOT_FOUND | 404 | Assistencia nao existe |
| REQUEST_VERSION_CONFLICT | 409 | Versao desatualizada (solicitacao) |
| ASSISTANCE_VERSION_CONFLICT | 409 | Versao desatualizada (assistencia) |
| REQUEST_INVALID_STATUS_TRANSITION | 422 | Transicao invalida de estado |
| ASSISTANCE_INVALID_STATUS_TRANSITION | 422 | Transicao invalida de assistencia |
| REQUEST_REJECTION_REASON_REQUIRED | 422 | motivo_recusa obrigatorio na recusa |
| REQUEST_ASSISTANCES_PENDING | 422 | Nao e possivel concluir — assistencias nao finalizadas |
| ASSISTANCE_COMMENT_REQUIRED | 422 | Comentario obrigatorio apos PRESTADOR_ACIONADO |
| ASSISTANCE_ALREADY_ACTIVE | 422 | Assistencia do mesmo tipo ja esta ativa |
| VALIDATION_ERROR | 422 | Campos obrigatorios invalidos / tipo_assistencia invalido |
| AUTH_FORBIDDEN | 403 | Analista nao vinculado / nao responsavel |

## Schema

### database_estrutura.sql alteracoes

- `tb_solicitacao_assistencia`: data_inclusao/data_atualizacao `DATE` → `DATETIME`, comentario `varchar(255)` nullable
- `tb_historico_status`: comentario `varchar(255)`.
- Seeds `tb_status`: ASSISTENCIA_SOLICITACAO status AGUARDANDO_PRESTADOR, EM_DESLOCAMENTO, CONCLUIDA, CANCELADA

### Arquivos novos

- `routers/admin.py`
- `schemas/admin.py`
- `services/admin_service.py`
- `repositories/admin_repository.py`

### Arquivos modificados

- `database_estrutura.sql`
- `main.py` (remover `apiAdmin` legado, adicionar `admin` router)

## Dependencias de testes

- Mocks: `admin_repository`, `solicitacao_repository`, `catalog_repository` (tipos_assistencia)
- Pattern: same as Fase 4/5 — `TestClient(app)`, `mock.patch.object` nos repos, JWT forjado
