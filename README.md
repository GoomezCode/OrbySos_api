<div align="center">

# 🚨 OrbySOS API

### API REST para gestão de seguros veiculares, ocorrências e assistências

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow?style=for-the-badge)]()

</div>

---

<div align="center">

> ⚠️ **Este documento está em construção.**
> Ainda falta muita coisa para ser documentada — esta versão existe apenas para que o repositório não fique sem README.
> Conforme o projeto evoluir, esta documentação será atualizada.

</div>

---

## 📖 Sobre o projeto

<div align="center">

**OrbySOS** é uma API desenvolvida com **FastAPI** para o gerenciamento de dados de
**pessoas físicas e jurídicas**, **veículos**, **endereços**, **apólices de seguro**,
**ocorrências** e **assistências** — voltada para um sistema de atendimento e
suporte semelhante a um SOS de seguradora.

A API se conecta a um banco de dados **MySQL** e conta com integração à
[BrasilAPI](https://brasilapi.com.br/) para consulta automática de **CEP**.

</div>

---

## 🛠️ Tecnologias utilizadas

<div align="center">

| Tecnologia | Finalidade |
|:---:|:---:|
| **FastAPI** | Framework web para construção da API |
| **Uvicorn** | Servidor ASGI para execução da aplicação |
| **MySQL Connector** | Conexão com o banco de dados MySQL |
| **Pydantic** | Validação e tipagem dos dados de entrada |
| **python-dotenv** | Gerenciamento de variáveis de ambiente |
| **bcrypt** | Criptografia de senhas |
| **validate-docbr** | Validação de CPF e CNPJ |
| **requests** | Consumo da API externa de CEP (BrasilAPI) |

</div>

---

## 📂 Estrutura do projeto

```
OrbySos_api/
├── api/
│   ├── apiConsulta.py     # Rotas de consulta (GET)
│   └── apiInsert.py       # Rotas de cadastro (POST)
├── classes/
│   └── classPessoa.py     # Modelos Pydantic (schemas)
├── database/
│   ├── DataBase.py        # Conexão com o MySQL
│   ├── insert.py          # Funções de inserção no banco
│   └── select.py          # Funções de consulta no banco
├── util/
│   └── function.py        # Funções utilitárias (hash, CEP, validações)
├── main.py                # Ponto de entrada da aplicação
└── requeriments.txt       # Dependências do projeto
```

---

## 🚀 Como executar o projeto

<div align="center">

### 1️⃣ Clone o repositório

```bash
git clone https://github.com/GoomezCode/OrbySos_api.git
cd OrbySos_api
```

### 2️⃣ Instale as dependências

```bash
pip install -r requeriments.txt
```

### 3️⃣ Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com os dados do seu banco MySQL:

```env
host=localhost
user=seu_usuario
password=sua_senha
bank=nome_do_banco
port=3306
```

### 4️⃣ Execute a aplicação

```bash
python main.py
```

A API ficará disponível em:

```
http://localhost:8080
```

</div>

---

## 📡 Endpoints principais

<div align="center">

### 🔍 Consultas (`/get`)

| Método | Rota | Descrição |
|:---:|:---|:---|
| `GET` | `/get/all/{table}` | Retorna todos os registros de uma tabela |
| `GET` | `/get/filter/tbPessoaId/{id}` | Busca uma pessoa pelo ID |
| `GET` | `/get/pessoaJuridica` | Lista todas as pessoas jurídicas |
| `GET` | `/get/pessoaFisica` | Lista todas as pessoas físicas |

### 📝 Cadastros (`/post`)

| Método | Rota | Descrição |
|:---:|:---|:---|
| `POST` | `/post/pessoa/{isJuridico}` | Cria um registro base de pessoa |
| `POST` | `/post/pj` | Cadastra dados de pessoa jurídica |
| `POST` | `/post/pf` | Cadastra dados de pessoa física |
| `POST` | `/post/endereco` | Cadastra endereço (com busca automática de CEP) |
| `POST` | `/post/user` | Cadastra usuário (login/senha) |
| `POST` | `/post/veiculo` | Cadastra veículo vinculado a uma pessoa |
| `POST` | `/post/ocorrencia/{ocorrencia}` | Cadastra um tipo de ocorrência |
| `POST` | `/post/assistencia/{assistencia}` | Cadastra um tipo de assistência |
| `POST` | `/post/apolice_ocorrencia` | Vincula uma ocorrência a uma apólice |
| `POST` | `/post/status_ocorrencia` | Registra o status de uma ocorrência |
| `POST` | `/post/ocorrencia_assistencia` | Vincula uma assistência a uma ocorrência |

</div>

---

## 🗺️ Roadmap / Pendências

<div align="center">

> Lista aberta do que ainda falta ser feito ou revisado no projeto.

| Item | Status |
|:---|:---:|
| Documentação completa dos endpoints (request/response) | ⏳ Pendente |
| Testes automatizados | ⏳ Pendente |
| Autenticação e autorização (JWT) | ⏳ Pendente |
| Rotas de `apólice` (CRUD completo) | ⏳ Pendente |
| Padronização das mensagens de erro | ⏳ Pendente |
| Diagrama do banco de dados (DER) | ⏳ Pendente |
| Deploy / CI-CD | ⏳ Pendente |

</div>

---

<div align="center">

### 👤 Autor

Desenvolvido por **[GoomezCode](https://github.com/GoomezCode)**
</div>
