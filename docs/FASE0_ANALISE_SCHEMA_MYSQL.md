# Fase 0 — Correções Críticas do Schema MySQL — Análise Técnica (2026-09-14)

> **Status:** ✅ FEITA
> **Objetivo:** Deixar o `database_estrutura.sql` 100% compatível com o que o frontend (OrbytSos) espera.

## Contexto

- Schema legado era SQLite (MVP antigo) e não MySQL.
- Faltavam tabelas, colunas divergiam do contrato do frontend e nomes não padronizados.
- Escopo: apenas o **conteúdo** de `database_estrutura.sql` (permissão de escrita exclusiva deste arquivo).

## Ações aplicadas (0.1–0.16)

| # | Ação | Detalhe |
|---|---|---|
| 0.1 | Corrigir `tb_analista_seguradora` | Sintaxe SQLite → MySQL: `AUTO_INCREMENT` no lugar de `AUTOINCREMENT`, remover `CHECK (ativo IN (0, 1))`, `CURRENT_TIMESTAMP` → `DEFAULT CURRENT_TIMESTAMP` |
| 0.2 | Corrigir `tb_cep.cep` | `int` → `varchar(8)` — CEPs com zeros à esquerda são truncados em `int` |
| 0.3 | Criar `tb_solicitacao_local` | Tabela separada: `id_local PK`, `endereco`, `numero_local`, `cidade`, `estado(2)`, `ponto_referencia`. `tb_solicitacao` passa a ter `fk_local` |
| 0.4 | Adicionar colunas em `tb_user` | `nome_exibicao varchar(100)`, `email varchar(150)`, `fk_seguradora int NULL` (FK → `tb_pessoa_juridica`) |
| 0.5 | Adicionar coluna em `tb_pessoa_fisica` | `cpf_mascarado varchar(20)` |
| 0.6 | Adicionar coluna em `tb_pessoa_juridica` | `cnpj_mascarado varchar(25)` |
| 0.7 | Adicionar coluna em `tb_veiculo` | `placa_mascarada varchar(10)` |
| 0.8 | Adicionar colunas em `tb_apolice` | `numero_apolice_mascarado varchar(50)`, `possui_solicitacao_ativa boolean DEFAULT false` |
| 0.9 | Renomear `tb_tpAssistencia` → `tb_tipo_assistencia` | Padronizar nomes com o frontend (refs corrigidas) |
| 0.10 | Criar `tb_configuracao` | `id_configuracao PK`, `pais varchar(2)`, `mensagem text`, `servicos_json json` |
| 0.11 | Ajustar `tb_solicitacao` | Adicionar `numero_solicitacao varchar(100) UNIQUE`, separar local para `tb_solicitacao_local`, garantir `version int NOT NULL DEFAULT 1`; `fk_analista_responsavel` nullable |
| 0.12 | Ajustar `tb_historico_status` | Adicionar `nome_responsavel varchar(100)`, `data_status datetime` |
| 0.13 | Corrigir FK em `tb_pergunta` | FK deve apontar para `tb_solicitacao(id_solicitacao)`, não `tb_assistencia` |
| 0.14/0.15 | Criar índices de performance | 7 índices (ver abaixo) |
| 0.16 | Atualizar INSERTs de status | Status de SOLICITACAO, ASSISTENCIA_SOLICITACAO, PERGUNTA + seed de `tb_configuracao` |

## 0.15 — Índices de Performance

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

## 0.16 — Seeds de Status

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

## Arquivo afetado

- `database_estrutura.sql`

## Resultado

Todas as 16 ações (0.1–0.16) aplicadas: `tb_analista_seguradora` migrada para sintaxe MySQL; `tb_cep.cep` e `tb_endereco.cep` → `varchar(8)`; criadas `tb_solicitacao_local` e `tb_configuracao`; colunas de mascaramento (`cpf_mascarado`, `cnpj_mascarado`, `placa_mascarada`, `numero_apolice_mascarado`), `possui_solicitacao_ativa`, `nome_exibicao`/`email`/`fk_seguradora` em `tb_user`; `tb_tpAssistencia` → `tb_tipo_assistencia` (refs corrigidas); `numero_solicitacao UNIQUE`, `version DEFAULT 1`, `fk_analista_responsavel` nullable e `fk_local → tb_solicitacao_local` em `tb_solicitacao`; `nome_responsavel`/`data_status datetime` em `tb_historico_status`; FK de `tb_pergunta` corrigida para `tb_solicitacao`; 7 índices criados; INSERTs de status e seed de `tb_configuracao` adicionados.