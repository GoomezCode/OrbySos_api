# Seed de Dados de Demonstração

> **Data:** 2026-09-16
> **Status:** Criado (arquivo only — NÃO executado no banco)
> **Arquivo:** `seed_dados_teste.sql` (raiz do repo)
> **Objetivo:** Popular o banco `orbyt` (MySQL) com os dados de demonstração do frontend OctbtSos para permitir login (JWT) e acesso às rotas protegidas da API.

---

## 1. Contexto

As rotas protegidas da API retornavam `401` porque o banco `orbyt` estava sem dados: a tabela `tb_user` estava **vazia** (30 tabelas criadas, 0 usuários). Sem usuário/CPF válido não há login → sem JWT → sem acesso.

Decisão do usuário: **criar apenas o arquivo `.sql`** com a estrutura de seed; **não executar** contra o banco neste momento.

## 2. Fontes dos Dados

| Fonte | Uso |
|---|---|
| `OrbytSos/public/data/usuarios.json` | Analistas (logins/senha/email/fk_seguradora) |
| `OrbytSos/public/data/pessoas-fisicas.json` | Clientes (nome, CPF, CPF mascarado) |
| `OrbytSos/public/data/seguradoras.json` | Seguradoras (razão social, nome fantasia) |
| `OrbytSos/public/data/veiculos.json` | Veículos (marca, modelo, anos, placa mascarada, blindado) |
| `OrbytSos/public/data/apolices.json` | Apólices (máscaras, titular, veículo, seguradora, solicitação ativa) |
| `OrbytSos/public/data/contatos.json` | Contatos de urgência/WhatsApp das seguradoras |
| `OrbytSos/public/data/analista-seguradoras.json` | Vínculos analista × seguradora |
| `OrbytSos/README.md` | Credenciais de demonstração (logins/senhas) |
| `core/security.py` | Geração dos hashes bcrypt |

## 3. Mapeamento de IDs

| Entidade | IDs | Observação |
|---|---|---|
| Clientes | `tb_pessoa` 1–10, `tb_pessoa_fisica` 1–10, `tb_user` 101–110 | Perfil `CLIENTE`, senha `ObbytTeste#2026` |
| Analistas | `tb_pessoa` 101–108, `tb_pessoa_fisica` 101–108, `tb_user` 901–908 | Perfil `ANALISTA`, senha `ObbytAnalista#2026` |
| Seguradoras | `tb_pessoa` **110** (Horizonte) e **120** (Órbita) | `isJuridico=1`, `tb_pessoa_juridica`; IDs deslocados de 10/20 para evitar colisão com clientes |
| Veículos | 201–220 | `tb_veiculo`; `fk_pessoa` = titular da apólice |
| Apólices | 1001–1020 | `tb_apolice`; `fk_segurado` → seguradora |
| Contatos | 3101–3104 | `tb_contato` das seguradoras |
| Vínculos | 1–16 | `tb_analista_seguradora` (8 analistas × 2 seguradoras) |

## 4. Credenciais de Demonstração

| Perfil | Login | Senha | Hash bcrypt |
|---|---|---|---|
| Cliente | CPF da pessoa física (ex.: `11144477735`) | `ObbytTeste#2026` | `$2b$12$sTmOSnnNiMX3BZFiBEvn4ulosCUVAqhdn8a7vppCJuvTuGyWNhL7K` |
| Analista | `analista.horizonte`, `analista.orbita`, `analista.demo01..06` | `ObbytAnalista#2026` | `$2b$12$H3zkCcMnfFD8SoZTTRTBBuytxPASHYVuO2DqKDc7.EhVv7WxrXPHW` |

**Nota sobre login de cliente:** o fluxo `find_client_by_cpf` autentica pelo **CPF** (`tb_pessoa_fisica.cpf`), e não pela coluna `tb_user.login`. O `login` dos clientes foi preenchido com o próprio CPF apenas para satisfazer o `NOT NULL UNIQUE`.

## 5. Decisões Técnicas

- **IDs de seguradoras 110/120** (em vez dos 10/20 do fixture): evita conflito de PK com clientes 1–10.
- **CPFs fictícios válidos** para analistas (gerados com `validate_docbr`): não autenticam por CPF, apenas cumprem `varchar(11) UNIQUE NOT NULL`.
- **Dados fictícios** para campos NOT NULL ausentes no fixture: `data_nascimento`, `cnh`, `placa` completa, `chassi`, `valor_fipe`, `cnpj`, `numero_apolice` completo, `versao`, `cobertura`, `assistencia`, `perfil`, `fk_local_pernoite=1`, `fk_forma_pagamento=1`.
- **`fk_sexo=3`** (não informado) e **`fk_estado_civil=1`** (solteiro) — IDs consultados no MySQL real.
- **Status:** pessoa `11` (ATIVA), usuário `8` (ATIVO), apólice `2` (ATIVA).
- **Idempotência:** `INSERT IGNORE` em todas as tabelas; reexecução segura.
- **`tb_apolice.fk_segurado` obrigatoriamente preenchido:** os JOINs de `client_repository._POLICIES_BY_PESSOA` e `apolice_repository._APOLICE_BASE_SELECT` esperam `fk_segurado → tb_pessoa_juridica`.
- **Ordem de inserção respeitando FKs:** `tb_pessoa` → `tb_pessoa_fisica` → `tb_pessoa_juridica` → `tb_user` → `tb_contato` → `tb_veiculo` → `tb_apolice` → `tb_analista_seguradora`.

## 6. Como Aplicar (quando autorizado)

```bash
mysql -h 192.168.68.63 -u Senac -p orbyt < seed_dados_teste.sql
```

## 7. Verificações Realizadas (sem tocar no banco)

- Colunas de cada `INSERT` conferidas contra `tb_*` em `database_estrutura.sql`.
- CPFs dos 10 clientes validados (`validate_docbr` → `True`).
- CPFs fictícios dos 8 analistas validados (`validate_docbr` → `True`).
- Hashes bcrypt gerados e verificados via `core/security.py`.
- `tb_analista_seguradora` com chave única `(fk_analista, fk_seguradora)` → as 16 linhas não violam o constraint.