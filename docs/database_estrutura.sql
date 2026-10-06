create database orbyt character set utf8mb4 collate utf8mb4_0900_ai_ci;
use orbyt;

# |------------------------ create tables ------------------------|
create table orbyt_meta(
                          chave varchar(64) primary key,
                          valor varchar(255) not null
);

create table tb_estado_civil(
                                id_estado_civil int primary key auto_increment,
                                estado varchar(50) not null
);

create table tb_sexo(
                        id_sexo int primary key auto_increment,
                        sexo varchar(50) not null
);

CREATE TABLE tb_status (
                           id_status INT PRIMARY KEY AUTO_INCREMENT,
                           codigo VARCHAR(50) NOT NULL,
                           rotulo VARCHAR(100) NOT NULL,
                           entidade VARCHAR(30) NOT NULL,

                           CONSTRAINT uq_status_entidade_codigo
                               UNIQUE (entidade, codigo)
);

create table tb_tpLogradouro(
                                id_tpLogradouro int primary key auto_increment,
                                tipo varchar(50) not null
);

create table tb_tpUso(
                         id_tpUso int primary key auto_increment,
                         tipo varchar(50) not null
);

create table tb_cep(
                       id_cep int primary key auto_increment,
                       logradouro varchar(100) not null,
                       bairro varchar(100) not null,
                       cidade varchar(100) not null,
                       estado varchar(2) not null,
                       cep varchar(8) not null -- CEPs com zero à esquerda são truncados em int
);

create table tb_pessoa(
                          id_pessoa int primary key auto_increment,
                          data_cadastro datetime not null,
                          isJuridico bool not null
);

create table tb_forma_pagamento(
                                   id_forma_pagamento int primary key auto_increment,
                                   forma varchar(50) not null
);

create table tb_local_pernoite(
                                  id_local_pernoite int primary key auto_increment,
                                  local varchar(50) not null
);

create table tb_ocorrencia(
                              id_ocorrencia int primary key auto_increment,
                              codigo varchar(100) not null,
                              nome varchar(100) not null,
                              descricao varchar(200) not null,
                              ativo bool not null

);

create table tb_tipo_assistencia(
                                    id_tipo_assistencia int primary key auto_increment,
                                    codigo varchar(100) not null,
                                    nome varchar(100) not null,
                                    descricao varchar(200) not null,
                                    ativo bool not null
);

create table tb_endereco(
                            id_endereco int primary key auto_increment,
                            fk_pessoa int not null,
                            logradouro varchar(100) not null,
                            bairro varchar(100) not null,
                            fk_tpLogradouro int not null,
                            cep varchar(8) not null,
                            cidade varchar(100) not null,
                            estado varchar(2) not null,
                            pais varchar(50) not null,
                            complemento varchar(150),
                            data_criacao datetime not null,

                            foreign key (fk_tpLogradouro) references tb_tpLogradouro(id_tpLogradouro),
                            foreign key (fk_pessoa) references tb_pessoa(id_pessoa) on delete cascade
);

create table tb_pessoa_fisica(
                                 id_pf int primary key,
                                 nome varchar(100) not null,
                                 cpf varchar(11) unique not null,
                                 fk_sexo int not null,
                                 data_nascimento date not null,
                                 cnh varchar(11) unique not null,
                                 fk_estado_civil int not null,
                                 fk_status int not null,
                                 cpf_mascarado varchar(20), -- mascaramento: "***.444.***-**"

                                 foreign key (id_pf) references tb_pessoa(id_pessoa) on delete cascade,
                                 foreign key (fk_sexo) references tb_sexo(id_sexo),
                                 foreign key (fk_estado_civil) references tb_estado_civil(id_estado_civil),
                                 foreign key (fk_status) references tb_status(id_status)
);

create table tb_pessoa_juridica(
                                   id_pj int primary key,
                                   isSeguradora bool not null,
                                   razao_social varchar(100) unique not null,
                                   nome_fantasia varchar(100) unique not null,
                                   cnpj varchar(14) unique not null,
                                   fk_status int not null,
                                   cnpj_mascarado varchar(25), -- mascaramento: "**.***.***/****-**

                                   foreign key (fk_status) references tb_status(id_status),
                                   foreign key (id_pj) references tb_pessoa(id_pessoa) on delete cascade
);

create table tb_user(
                        id_user int primary key auto_increment,
                        fk_pessoa int not null,
                        login varchar(100) unique not null,
                        senha varchar(200) not null,
                        perfil varchar(20) not null,
                        fk_status int not null,
                        nome_exibicao varchar(100), -- nome amigavel exibido na session
                        email varchar(150),
                        fk_seguradora int, -- analista vinculado a uma seguradora fixa

                        foreign key (fk_status) references tb_status(id_status),
                        foreign key (fk_pessoa) references tb_pessoa(id_pessoa) on delete cascade,
                        foreign key (fk_seguradora) references tb_pessoa_juridica(id_pj)
);

create table tb_contato(
                           id_contato int primary key auto_increment,
                           fk_pessoa int not null,
                           principal bool not null,
                           fk_status int not null,
                           tipo_contato varchar(30) not null, # email - telefone
                           valor_contato varchar(100) not null,
                           data_criacao datetime not null,
                           rotulo varchar(100) not null,
                           foreign key (fk_pessoa) references tb_pessoa(id_pessoa) on delete cascade,
                           foreign key (fk_status) references tb_status(id_status)
);

create table tb_veiculo(
                           id_veiculo int primary key auto_increment,
                           fk_pessoa int not null,
                           marca varchar(50) not null,
                           modelo varchar(100) not null,
                           versao varchar(20) not null,
                           ano_fabricado int not null,
                           ano_modelo int not null,
                           placa varchar(20) unique not null,
                           chassi varchar(30) unique not null,
                           valor_fipe varchar(15) not null,
                           fk_tpUso int not null,
                           blindado boolean not null,
                           placa_mascarada varchar(10), -- mascaramento: "ABC-1*34"

                           foreign key (fk_pessoa) references tb_pessoa(id_pessoa) on delete cascade,
                           foreign key (fk_tpUso) references tb_tpUso(id_tpUso)
);

create table tb_apolice(
                           id_apolice int primary key auto_increment,
                           numero_apolice varchar(50) not null,
                           fk_pessoa int not null,
                           fk_segurado int,
                           fk_veiculo int not null,
                           data_inicio datetime not null,
                           data_fim datetime not null,
                           cobertura float not null,
                           assistencia varchar(50) not null,
                           endosso varchar(10),
                           versao int not null,
                           perfil varchar(200) not null,
                           fk_local_pernoite int not null,
                           fk_status int not null,
                           fk_forma_pagamento int not null,
                           numero_apolice_mascarado varchar(50), -- mascaramento: "ORB-****-1009"
                           possui_solicitacao_ativa boolean not null default 0, -- realimentado pela API

                           foreign key (fk_local_pernoite) references  tb_local_pernoite(id_local_pernoite),
                           foreign key (fk_forma_pagamento) references tb_forma_pagamento(id_forma_pagamento),
                           foreign key (fk_pessoa) references tb_pessoa(id_pessoa) on delete cascade,
                           foreign key (fk_segurado) references tb_pessoa_juridica(id_pj),
                           foreign key (fk_veiculo) references tb_veiculo(id_veiculo),
                           foreign key (fk_status) references tb_status(id_status)
);

create table tb_apolice_ocorrencia(
                                      id_apolice_ocorrencia int primary key auto_increment,
                                      fk_apolice int not null,
                                      fk_ocorrencia int not null,

                                      foreign key (fk_apolice) references tb_apolice(id_apolice),
                                      foreign key (fk_ocorrencia) references tb_ocorrencia(id_ocorrencia)
);

create table tb_status_ocorrencia(
                                     id_status_ocorrencia int primary key auto_increment,
                                     fk_apo_ocorrencia int not null,
                                     status varchar(200),

                                     foreign key (fk_apo_ocorrencia) references tb_apolice_ocorrencia(id_apolice_ocorrencia)
);

create table tb_ocorrencia_assistencia(
                                          id_ocorrencia_assistencia int primary key auto_increment,
                                          descricao varchar(200) not null,
                                          local varchar(200) not null,
                                          isMachucado bool not null,
                                          fk_apo_ocorrencia int not null,
                                          fk_assistencia int not null,
                                          fk_status int not null,

                                          foreign key (fk_apo_ocorrencia) references tb_apolice_ocorrencia(id_apolice_ocorrencia),
                                          foreign key (fk_assistencia) references tb_tipo_assistencia(id_tipo_assistencia),
                                          foreign key (fk_status) references tb_status(id_status)
);

-- Local da ocorrencia (separado da solicitacao)
create table tb_solicitacao_local(
                                     id_local int primary key auto_increment,
                                     endereco varchar(200) not null,
                                     numero_local varchar(20) not null,
                                     cidade varchar(100) not null,
                                     estado varchar(2) not null,
                                     ponto_referencia varchar(200)
);

create table tb_solicitacao(
                               id_solicitacao int primary key auto_increment,
                               id_solicitacao_cliente varchar(100) not null unique, -- idempotencia (Idempotency-Key)
                               protocolo_solicitacao varchar(100) not null unique,
                               numero_solicitacao varchar(100) unique, -- protocolo de exibicao: ORB-YYYY-NNNNNN
                               descricao_evento varchar(200) not null,
                               possui_feridos bool not null,
                               risco_imediato bool not null,
                               prioridade varchar(20),
                               data_criacao_cliente datetime not null,
                               data_recebimento datetime not null,
                               data_decisao datetime,
                               motivo_recusa varchar(100),
                               version int not null default 1, -- optimistic locking

                               fk_apolice int not null,
                               fk_pessoa int not null,
                               fk_seguradora int not null,
                               fk_veiculo int not null,
                               fk_tipo_ocorrencia int not null,
                               fk_local int not null unique, -- endereco do local da ocorrencia
                               fk_status int not null,
                               fk_analista_responsavel int, -- null enquanto nao assumida

                               foreign key (fk_apolice) references tb_apolice(id_apolice),
                               foreign key (fk_pessoa) references tb_pessoa(id_pessoa),
                               foreign key (fk_seguradora) references tb_pessoa_juridica(id_pj),
                               foreign key (fk_veiculo) references tb_veiculo(id_veiculo),
                               foreign key (fk_tipo_ocorrencia) references tb_ocorrencia(id_ocorrencia),
                               foreign key (fk_local) references tb_solicitacao_local(id_local),
                               foreign key (fk_status) references tb_status(id_status),
                               foreign key (fk_analista_responsavel) references tb_user(id_user)
);

create table tb_assistencia(
                               id_assistencia int primary key auto_increment,
                               fk_id_tipo_assistencia int not null,
                               nome varchar(50) not null,
                               descricao varchar(100) not null,
                               fk_status int not null,

                               foreign key (fk_id_tipo_assistencia) references tb_tipo_assistencia(id_tipo_assistencia),
                               foreign key (fk_status) references tb_status(id_status)
);

create table tb_solicitacao_assistencia(
                                            id_solicitacao_assistencia int primary key auto_increment,
                                            status varchar(20) not null,
                                            comentario varchar(255),
                                            data_inclusao datetime not null,
                                            data_atualizacao datetime not null,
                                            version int not null,

                                           fk_solicitacao int not null,
                                           fk_assistencia int not null,
                                           fk_usuario_responsavel int not null,

                                           foreign key (fk_solicitacao) references tb_solicitacao(id_solicitacao),
                                           foreign key (fk_assistencia) references tb_assistencia(id_assistencia),
                                           foreign key (fk_usuario_responsavel) references tb_user(id_user)
);

create table tb_historico_status(
                                    id_historico int primary key auto_increment,
                                    status varchar(50) not null,
                                    data_status datetime not null,
                                    comentario varchar(255) not null,
                                    nome_responsavel varchar(100), -- nome de quem executou a transicao
                                    fk_solicitacao int not null,
                                    fk_usuario_responsavel int,

                                    foreign key (fk_solicitacao) references tb_solicitacao(id_solicitacao),
                                    foreign key (fk_usuario_responsavel) references tb_user(id_user)
);

create table tb_pergunta(
                            id_pergunta int primary key auto_increment,
                            origem varchar(30) not null default 'GUINCHO',
                            tipo varchar(30) not null default 'TAXI',
                            necessita_taxi bool,
                            qtd_passageiros int,
                            necessita_acessibilidade bool,
                            qtd_criancas int,
                            qtd_animais int,
                            bagagem varchar(255),
                            observacoes varchar(255),
                            data_criacao datetime not null,
                            data_resposta datetime,
                            version int not null default 1,

                            fk_solicitacao int not null,
                            fk_assistencia int,
                            fk_status int not null,

                            foreign key (fk_solicitacao) references tb_solicitacao(id_solicitacao),
                            foreign key (fk_assistencia) references tb_assistencia(id_assistencia),
                            foreign key (fk_status) references tb_status(id_status)
);

-- vinculo analista x seguradora (sintaxe MySQL)
CREATE TABLE tb_analista_seguradora (
  id_analista_seguradora INT PRIMARY KEY AUTO_INCREMENT,
  fk_analista INT NOT NULL,
  fk_seguradora INT NOT NULL,
  ativo TINYINT(1) NOT NULL DEFAULT 1,
  data_vinculo DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT uq_analista_seguradora
    UNIQUE (fk_analista, fk_seguradora),

  FOREIGN KEY (fk_analista)
    REFERENCES tb_user(id_user)
    ON DELETE CASCADE,

  FOREIGN KEY (fk_seguradora)
    REFERENCES tb_pessoa_juridica(id_pj)
    ON DELETE CASCADE
);

-- configuracoes globais consumidas pelo frontend
create table tb_configuracao(
                                id_configuracao int primary key auto_increment,
                                pais varchar(2) not null,
                                mensagem text not null,
                                servicos_json json not null
);
# |------------------------ create tables ------------------------|


# |------------------------ create indexes ------------------------|
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
  ON tb_historico_status (fk_solicitacao, data_status);

-- Assistance per request
CREATE INDEX idx_assistencia_solicitacao
  ON tb_solicitacao_assistencia (fk_solicitacao, status);

-- Analyst-to-insurer lookup
CREATE INDEX idx_analista_seguradora_analista
  ON tb_analista_seguradora (fk_analista, ativo);

-- Insurer-to-analyst lookup
CREATE INDEX idx_analista_seguradora_seguradora
  ON tb_analista_seguradora (fk_seguradora, ativo);
# |------------------------ create indexes ------------------------|


# |------------------------ insert into values ------------------------|

insert into tb_sexo(sexo)
values ('masculino'), ('feminino'), ('nao_informado');

INSERT INTO tb_status (codigo, rotulo, entidade)
VALUES
    ('INATIVA', 'Inativa', 'APOLICE'),
    ('ATIVA', 'Ativa', 'APOLICE'),
    ('SUSPENSA', 'Suspensa', 'APOLICE'),

    ('LOCALIZADO', 'Localizado', 'OCORRENCIA'),
    ('A_CAMINHO', 'A caminho', 'OCORRENCIA'),
    ('INDISPONIVEL', 'Indisponível', 'OCORRENCIA'),

    ('INATIVO', 'Inativo', 'USUARIO'),
    ('ATIVO', 'Ativo', 'USUARIO'),
    ('SUSPENSO', 'Suspenso', 'USUARIO'),

    ('INATIVA', 'Inativa', 'PESSOA'),
    ('ATIVA', 'Ativa', 'PESSOA'),
    ('SUSPENSA', 'Suspensa', 'PESSOA'),

    ('RECEBIDO', 'Recebido', 'ASSISTENCIA'),
    ('EM_ANALISE', 'Em análise', 'ASSISTENCIA'),
    ('CONFIRMADO', 'Confirmado', 'ASSISTENCIA'),
    ('PRESTADOR_ACIONADO', 'Prestador acionado', 'ASSISTENCIA'),
    ('EM_ATENDIMENTO', 'Em atendimento', 'ASSISTENCIA'),
    ('CONCLUIDO', 'Concluído', 'ASSISTENCIA'),
    ('RECUSADO', 'Recusado', 'ASSISTENCIA'),

    ('LOCALIZADO', 'Localizado', 'PRESTADOR'),
    ('INDISPONIVEL', 'Indisponível', 'PRESTADOR'),
    ('EM_DESLOCAMENTO', 'Em deslocamento', 'PRESTADOR');

-- Status de SOLICITACAO (machine de estados da solicitacao)
INSERT INTO tb_status (codigo, rotulo, entidade)
VALUES
    ('RECEBIDA', 'Recebida', 'SOLICITACAO'),
    ('EM_ANALISE', 'Em análise', 'SOLICITACAO'),
    ('CONFIRMADA', 'Confirmada', 'SOLICITACAO'),
    ('RECUSADA_SEM_COBERTURA', 'Recusada sem cobertura', 'SOLICITACAO'),
    ('EM_ATENDIMENTO', 'Em atendimento', 'SOLICITACAO'),
    ('PRESTADOR_ACIONADO', 'Prestador acionado', 'SOLICITACAO'),
    ('CONCLUIDA', 'Concluída', 'SOLICITACAO');

-- Status de ASSISTENCIA na solicitacao (solicitacao_assistencia)
INSERT INTO tb_status (codigo, rotulo, entidade)
VALUES
    ('INCLUIDA', 'Incluída', 'ASSISTENCIA_SOLICITACAO'),
    ('AGUARDANDO_PRESTADOR', 'Aguardando prestador', 'ASSISTENCIA_SOLICITACAO'),
    ('PRESTADOR_ACIONADO', 'Prestador acionado', 'ASSISTENCIA_SOLICITACAO'),
    ('EM_DESLOCAMENTO', 'Em deslocamento', 'ASSISTENCIA_SOLICITACAO'),
    ('CONCLUIDA', 'Concluída', 'ASSISTENCIA_SOLICITACAO'),
    ('CANCELADA', 'Cancelada', 'ASSISTENCIA_SOLICITACAO'),
    ('REMOVIDA', 'Removida', 'ASSISTENCIA_SOLICITACAO');

-- Status de PERGUNTA
INSERT INTO tb_status (codigo, rotulo, entidade)
VALUES
    ('PENDENTE', 'Pendente', 'PERGUNTA'),
    ('RESPONDIDA', 'Respondida', 'PERGUNTA');

insert into tb_tpLogradouro(tipo)
values ('avenida'), ('rua'), ('estrada'), ('rodovia');

insert into tb_estado_civil(estado)
values ('solteiro'), ('casado'), ('separado'), ('divorciado'), ('viuvo');

insert into tb_tpUso(tipo)
values ('particular'), ('comercial'), ('app'), ('taxi');

insert into tb_forma_pagamento(forma)
values ('Pix'),('Boleto Bancario'),('Cartao de Credito'),
       ('Cartao de Debito'),('Transferencia Bancaria'),('Deposito Bancario'),
       ('Debito em Conta'),('Dinheiro');

insert into tb_local_pernoite(local)
values ('Garagem Residencial Fechada'),('Garagem Residencial Aberta'),('Condominio Residencial'),
       ('Estacionamento Privativo'),('Estacionamento Coberto'),('Estacionamento Descoberto'),
       ('Empresa'),('Patio da Empresa'),('Via Publica'),('Residencia Rural'),('Garagem Comercial');

INSERT INTO tb_ocorrencia
(id_ocorrencia, codigo, nome, descricao, ativo)
VALUES
    (1, 'PANE_MECANICA',      'Pane mecânica',        'Falha mecânica que impede a continuidade da viagem.', 1),
    (2, 'ACIDENTE',           'Acidente',              'Colisão ou outro evento acidental.',                   1),
    (3, 'PNEU_FURADO',        'Pneu furado',           'Dano em um ou mais pneus.',                            1),
    (4, 'FALTA_COMBUSTIVEL',  'Falta de combustível', 'Impossibilidade de continuar por falta de combustível.', 1),
    (5, 'OUTRO',              'Outro',                 'Outra ocorrência que precisa de avaliação.',           1);

INSERT INTO tb_tipo_assistencia
(id_tipo_assistencia, codigo, nome, descricao, ativo)
VALUES
    (1, 'GUINCHO',    'Guincho',       'Remoção do veículo por prestador especializado.',             1),
    (2, 'TAXI',       'Táxi',          'Transporte de ocupantes após análise manual da cobertura.',    1),
    (3, 'CHAVEIRO',   'Chaveiro',      'Atendimento para abertura ou chave veicular.',                 1),
    (4, 'TROCA_PNEU', 'Troca de pneu', 'Apoio para substituição de pneu.',                             1),
    (5, 'MECANICO',   'Mecânico',      'Avaliação mecânica no local.',                                 1);

INSERT INTO tb_configuracao (pais, mensagem, servicos_json)
VALUES ('BR', 'Orbyt Assistência 24h. Em caso de emergência ligue 0800 000 0000.',
        JSON_ARRAY(
            JSON_OBJECT('codigo', 'SAMU', 'nome', 'SAMU', 'telefone', '192'),
            JSON_OBJECT('codigo', 'BOMBEIROS', 'nome', 'Corpo de Bombeiros', 'telefone', '193'),
            JSON_OBJECT('codigo', 'POLICIA', 'nome', 'Polícia Militar', 'telefone', '190')
        ));

INSERT IGNORE INTO orbyt_meta (chave, valor) VALUES ('revision', '0');

# |------------------------ insert into values ------------------------|