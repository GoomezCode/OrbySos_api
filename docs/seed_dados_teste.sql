-- ============================================================================
-- SEED DE DADOS PARA DEMONSTRACAO - API OrbytSos
-- ============================================================================
-- Fonte: OrbytSos/public/data/*.json (fixtures imutaveis - nao modificados)
-- Credenciais: CPFs/logins/senhas do README do frontend (OrbytSos/README.md)
-- Banco alvo: orbyt (MySQL) - apenas dados, NAO altera o database_estrutura.sql
-- Uso:      mysql -h <host> -u <user> -p orbyt < seed_dados_teste.sql
-- Atalho:   mysql -h 192.168.68.63 -u Senac -p orbyt < seed_dados_teste.sql
--
-- Idempotente: todos os INSERTs usam INSERT IGNORE (re-execucao segura).
-- Senha cliente  OrbytTeste#2026   (bcrypt, gerada com core/security.py)
-- Senha analista OrbytAnalista#2026 (bcrypt, gerada com core/security.py)
--
-- Mapeamento de IDs:
--   Clientes      : tb_pessoa 1-10   (tb_pessoa_fisica 1-10, tb_user 101-110)
--   Analistas     : tb_pessoa 101-108(tb_pessoa_fisica 101-108, tb_user 901-908)
--   Seguradoras   : tb_pessoa 110 (Horizonte) e 120 (Orbita)  -> tb_pessoa_juridica
--   Veiculos      : 201-220
--   Apolices      : 1001-1020
--   Contatos      : 3101-3104
-- ============================================================================

SET NAMES utf8mb4;

# |------------------------ tb_pessoa ------------------------|

-- Clientes (isJuridico = 0)
INSERT IGNORE INTO tb_pessoa (id_pessoa, data_cadastro, isJuridico) VALUES
  (1,   NOW(), 0), (2,   NOW(), 0), (3,   NOW(), 0), (4,   NOW(), 0),
  (5,   NOW(), 0), (6,   NOW(), 0), (7,   NOW(), 0), (8,   NOW(), 0),
  (9,   NOW(), 0), (10,  NOW(), 0);

-- Analistas (isJuridico = 0)
INSERT IGNORE INTO tb_pessoa (id_pessoa, data_cadastro, isJuridico) VALUES
  (101, NOW(), 0), (102, NOW(), 0), (103, NOW(), 0), (104, NOW(), 0),
  (105, NOW(), 0), (106, NOW(), 0), (107, NOW(), 0), (108, NOW(), 0);

-- Seguradoras (isJuridico = 1) - id 110 = Horizonte, 120 = Orbita
INSERT IGNORE INTO tb_pessoa (id_pessoa, data_cadastro, isJuridico) VALUES
  (110, NOW(), 1), (120, NOW(), 1);

# |------------------------ tb_pessoa_fisica ------------------------|

-- Clientes (CPF valido do README + cpf_mascarado do fixture)
INSERT IGNORE INTO tb_pessoa_fisica
  (id_pf, nome, cpf, fk_sexo, data_nascimento, cnh, fk_estado_civil, fk_status, cpf_mascarado)
VALUES
  (1,  'Marina Exemplo',        '11144477735', 3, '1985-03-12', '00000000001', 1, 11, '***.444.***-**'),
  (2,  'Rafael Demonstração',   '12345678909', 3, '1992-07-21', '00000000002', 1, 11, '***.456.***-**'),
  (3,  'Cliente Teste Três',    '92974161014', 3, '1978-11-05', '00000000003', 1, 11, '***.000.***-**'),
  (4,  'Cliente Teste Quatro',  '45313922050', 3, '1989-01-30', '00000000004', 1, 11, '***.000.***-**'),
  (5,  'Cliente Teste Cinco',   '80549580050', 3, '1995-09-14', '00000000005', 1, 11, '***.000.***-**'),
  (6,  'Cliente Teste Seis',    '39157673012', 3, '1981-04-18', '00000000006', 1, 11, '***.000.***-**'),
  (7,  'Cliente Teste Sete',    '54635315010', 3, '1990-12-02', '00000000007', 1, 11, '***.000.***-**'),
  (8,  'Cliente Teste Oito',    '56123903004', 3, '1987-06-25', '00000000008', 1, 11, '***.000.***-**'),
  (9,  'Segurado Demo Nove',    '34979659012', 3, '1976-08-09', '00000000009', 1, 11, '***.000.***-**'),
  (10, 'Segurado Demo Dez',     '62608448089', 3, '1993-02-17', '00000000010', 1, 11, '***.000.***-**');

-- Analistas (CPFs ficticios validos - gerados com validate_docbr; nao autenticam por CPF)
INSERT IGNORE INTO tb_pessoa_fisica
  (id_pf, nome, cpf, fk_sexo, data_nascimento, cnh, fk_estado_civil, fk_status, cpf_mascarado)
VALUES
  (101, 'Analista Horizonte',    '18503126800', 3, '1980-05-11', '00000000011', 1, 11, '***.000.***-**'),
  (102, 'Analista Órbita',       '52153087058', 3, '1984-09-23', '00000000012', 1, 11, '***.000.***-**'),
  (103, 'Analista Demo Um',      '68326664200', 3, '1977-01-15', '00000000013', 1, 11, '***.000.***-**'),
  (104, 'Analista Demo Dois',    '57829663190', 3, '1991-10-07', '00000000014', 1, 11, '***.000.***-**'),
  (105, 'Analista Demo Tres',    '82590406037', 3, '1986-03-04', '00000000015', 1, 11, '***.000.***-**'),
  (106, 'Analista Demo Quatro',  '31102003093', 3, '1979-12-28', '00000000016', 1, 11, '***.000.***-**'),
  (107, 'Analista Demo Cinco',   '61741073103', 3, '1994-06-19', '00000000017', 1, 11, '***.000.***-**'),
  (108, 'Analista Demo Seis',    '84158863651', 3, '1988-08-01', '00000000018', 1, 11, '***.000.***-**');

# |------------------------ tb_pessoa_juridica ------------------------|

INSERT IGNORE INTO tb_pessoa_juridica
  (id_pj, isSeguradora, razao_social, nome_fantasia, cnpj, fk_status, cnpj_mascarado)
VALUES
  (110, 1, 'Seguradora Horizonte Demonstração S.A.', 'Horizonte Demo', '94065440596073', 11, '00.000.000/0000-00'),
  (120, 1, 'Seguradora Órbita Demonstração S.A.',     'Órbita Demo',     '44929163706650', 11, '00.000.000/0000-00');

# |------------------------ tb_user ------------------------|

-- Clientes (login do cliente NAO e usado na autenticacao - o login usa CPF;
--    atribuimos o CPF como valor unico para satisfazer a coluna NOT NULL UNIQUE)
INSERT IGNORE INTO tb_user
  (id_user, fk_pessoa, login, senha, perfil, fk_status, nome_exibicao, email, fk_seguradora)
VALUES
  (101, 1,  '11144477735', '$2b$12$sTmOSnnNiMX3BZFiBEvn4ulosCUVAqhdn8a7vppCJuvTuGyWNhL7K', 'CLIENTE',  8, 'Marina Exemplo',       NULL, NULL),
  (102, 2,  '12345678909', '$2b$12$sTmOSnnNiMX3BZFiBEvn4ulosCUVAqhdn8a7vppCJuvTuGyWNhL7K', 'CLIENTE',  8, 'Rafael Demonstração',  NULL, NULL),
  (103, 3,  '92974161014', '$2b$12$sTmOSnnNiMX3BZFiBEvn4ulosCUVAqhdn8a7vppCJuvTuGyWNhL7K', 'CLIENTE',  8, 'Cliente Teste Três',   NULL, NULL),
  (104, 4,  '45313922050', '$2b$12$sTmOSnnNiMX3BZFiBEvn4ulosCUVAqhdn8a7vppCJuvTuGyWNhL7K', 'CLIENTE',  8, 'Cliente Teste Quatro', NULL, NULL),
  (105, 5,  '80549580050', '$2b$12$sTmOSnnNiMX3BZFiBEvn4ulosCUVAqhdn8a7vppCJuvTuGyWNhL7K', 'CLIENTE',  8, 'Cliente Teste Cinco',  NULL, NULL),
  (106, 6,  '39157673012', '$2b$12$sTmOSnnNiMX3BZFiBEvn4ulosCUVAqhdn8a7vppCJuvTuGyWNhL7K', 'CLIENTE',  8, 'Cliente Teste Seis',   NULL, NULL),
  (107, 7,  '54635315010', '$2b$12$sTmOSnnNiMX3BZFiBEvn4ulosCUVAqhdn8a7vppCJuvTuGyWNhL7K', 'CLIENTE',  8, 'Cliente Teste Sete',   NULL, NULL),
  (108, 8,  '56123903004', '$2b$12$sTmOSnnNiMX3BZFiBEvn4ulosCUVAqhdn8a7vppCJuvTuGyWNhL7K', 'CLIENTE',  8, 'Cliente Teste Oito',   NULL, NULL),
  (109, 9,  '34979659012', '$2b$12$sTmOSnnNiMX3BZFiBEvn4ulosCUVAqhdn8a7vppCJuvTuGyWNhL7K', 'CLIENTE',  8, 'Segurado Demo Nove',   NULL, NULL),
  (110, 10, '62608448089', '$2b$12$sTmOSnnNiMX3BZFiBEvn4ulosCUVAqhdn8a7vppCJuvTuGyWNhL7K', 'CLIENTE',  8, 'Segurado Demo Dez',    NULL, NULL);

-- Analistas (logins/senha/email do fixture e do README; fk_seguradora conforme fixture)
INSERT IGNORE INTO tb_user
  (id_user, fk_pessoa, login, senha, perfil, fk_status, nome_exibicao, email, fk_seguradora)
VALUES
  (901, 101, 'analista.horizonte', '$2b$12$H3zkCcMnfFD8SoZTTRTBBuytxPASHYVuO2DqKDc7.EhVv7WxrXPHW', 'ANALISTA', 8, 'Analista Horizonte',   'analista.horizonte@example.invalid', 110),
  (902, 102, 'analista.orbita',    '$2b$12$H3zkCcMnfFD8SoZTTRTBBuytxPASHYVuO2DqKDc7.EhVv7WxrXPHW', 'ANALISTA', 8, 'Analista Órbita',      'analista.orbita@example.invalid',    120),
  (903, 103, 'analista.demo01',    '$2b$12$H3zkCcMnfFD8SoZTTRTBBuytxPASHYVuO2DqKDc7.EhVv7WxrXPHW', 'ANALISTA', 8, 'Analista Demo Um',     'analista.demo01@example.invalid',    110),
  (904, 104, 'analista.demo02',    '$2b$12$H3zkCcMnfFD8SoZTTRTBBuytxPASHYVuO2DqKDc7.EhVv7WxrXPHW', 'ANALISTA', 8, 'Analista Demo Dois',   'analista.demo02@example.invalid',    110),
  (905, 105, 'analista.demo03',    '$2b$12$H3zkCcMnfFD8SoZTTRTBBuytxPASHYVuO2DqKDc7.EhVv7WxrXPHW', 'ANALISTA', 8, 'Analista Demo Tres',   'analista.demo03@example.invalid',    110),
  (906, 106, 'analista.demo04',    '$2b$12$H3zkCcMnfFD8SoZTTRTBBuytxPASHYVuO2DqKDc7.EhVv7WxrXPHW', 'ANALISTA', 8, 'Analista Demo Quatro', 'analista.demo04@example.invalid',    120),
  (907, 107, 'analista.demo05',    '$2b$12$H3zkCcMnfFD8SoZTTRTBBuytxPASHYVuO2DqKDc7.EhVv7WxrXPHW', 'ANALISTA', 8, 'Analista Demo Cinco',  'analista.demo05@example.invalid',    120),
  (908, 108, 'analista.demo06',    '$2b$12$H3zkCcMnfFD8SoZTTRTBBuytxPASHYVuO2DqKDc7.EhVv7WxrXPHW', 'ANALISTA', 8, 'Analista Demo Seis',   'analista.demo06@example.invalid',    120);

# |------------------------ tb_contato (seguradoras) ------------------------|

INSERT IGNORE INTO tb_contato
  (id_contato, fk_pessoa, principal, fk_status, tipo_contato, valor_contato, data_criacao, rotulo)
VALUES
  (3101, 110, 1, 11, 'TELEFONE_URGENCIA', 'CONFIGURAR', NOW(), 'Urgência'),
  (3102, 110, 0, 11, 'WHATSAPP',          'CONFIGURAR', NOW(), 'WhatsApp'),
  (3103, 120, 1, 11, 'TELEFONE_URGENCIA', 'CONFIGURAR', NOW(), 'Urgência'),
  (3104, 120, 0, 11, 'WHATSAPP',          'CONFIGURAR', NOW(), 'WhatsApp');

# |------------------------ tb_veiculo ------------------------|

-- fk_pessoa = titular da apolice correspondente (mesmo mapeamento do fixture).
-- placa/chassi/valor_fipe/versao sao valores FICTICIOS (nao existem no fixture).
INSERT IGNORE INTO tb_veiculo
  (id_veiculo, fk_pessoa, marca, modelo, versao, ano_fabricado, ano_modelo, placa, chassi, valor_fipe, fk_tpUso, blindado, placa_mascarada)
VALUES
  (201, 1,  'Marca Demo',    'Modelo Azul',     '1.0', 2022, 2023, 'DEM0001', '9BDDEM001201DEM0001', '98000.00', 1, 0, 'DEM-****'),
  (202, 1,  'Marca Demo',    'Modelo Prata',    '1.0', 2021, 2022, 'TST0002', '9BDDEM001202TST0002', '87000.00', 1, 0, 'TST-****'),
  (203, 2,  'Marca Fictícia','Modelo Um',       '1.0', 2020, 2021, 'EXM0003', '9BDDEM001203EXM0003', '65000.00', 1, 0, 'EXM-****'),
  (204, 3,  'Marca Fictícia','Modelo Dois',     '1.0', 2019, 2020, 'EXM0004', '9BDDEM001204EXM0004', '59000.00', 1, 0, 'EXM-****'),
  (205, 4,  'Marca Fictícia','Modelo Três',     '1.0', 2023, 2024, 'EXM0005', '9BDDEM001205EXM0005', '112000.00',1, 0, 'EXM-****'),
  (206, 5,  'Marca Fictícia','Modelo Quatro',   '1.0', 2018, 2019, 'EXM0006', '9BDDEM001206EXM0006', '54000.00', 1, 0, 'EXM-****'),
  (207, 6,  'Marca Fictícia','Modelo Cinco',    '1.0', 2022, 2022, 'EXM0007', '9BDDEM001207EXM0007', '92000.00', 1, 0, 'EXM-****'),
  (208, 7,  'Marca Fictícia','Modelo Seis',     '1.0', 2024, 2025, 'EXM0008', '9BDDEM001208EXM0008', '125000.00',1, 0, 'EXM-****'),
  (209, 1,  'Marca Demo',    'Modelo Verde',    '1.0', 2023, 2024, 'SOS0009', '9BDDEM001209SOS0009', '105000.00',1, 0, 'SOS-****'),
  (210, 8,  'Marca Demo',    'Modelo Dez',      '1.0', 2020, 2021, 'DEM0010', '9BDDEM001210DEM0010', '79000.00', 1, 0, 'DEMO-0210'),
  (211, 9,  'Marca Demo',    'Modelo Onze',     '1.0', 2021, 2022, 'DEM0011', '9BDDEM001211DEM0011', '88000.00', 1, 0, 'DEMO-0211'),
  (212, 10, 'Marca Demo',    'Modelo Doze',     '1.0', 2022, 2023, 'DEM0012', '9BDDEM001212DEM0012', '94000.00', 1, 0, 'DEMO-0212'),
  (213, 2,  'Marca Demo',    'Modelo Treze',    '1.0', 2023, 2024, 'DEM0013', '9BDDEM001213DEM0013', '101000.00',1, 0, 'DEMO-0213'),
  (214, 3,  'Marca Demo',    'Modelo Quatorze', '1.0', 2024, 2025, 'DEM0014', '9BDDEM001214DEM0014', '118000.00',1, 0, 'DEMO-0214'),
  (215, 4,  'Marca Demo',    'Modelo Quinze',   '1.0', 2019, 2020, 'DEM0015', '9BDDEM001215DEM0015', '62000.00', 1, 0, 'DEMO-0215'),
  (216, 5,  'Marca Demo',    'Modelo Dezesseis','1.0', 2020, 2021, 'DEM0016', '9BDDEM001216DEM0016', '71000.00', 1, 0, 'DEMO-0216'),
  (217, 6,  'Marca Demo',    'Modelo Dezessete','1.0', 2021, 2022, 'DEM0017', '9BDDEM001217DEM0017', '83000.00', 1, 0, 'DEMO-0217'),
  (218, 7,  'Marca Demo',    'Modelo Dezoito',  '1.0', 2022, 2023, 'DEM0018', '9BDDEM001218DEM0018', '96000.00', 1, 0, 'DEMO-0218'),
  (219, 8,  'Marca Demo',    'Modelo Dezenove', '1.0', 2023, 2024, 'DEM0019', '9BDDEM001219DEM0019', '103000.00',1, 0, 'DEMO-0219'),
  (220, 9,  'Marca Demo',    'Modelo Vinte',    '1.0', 2024, 2025, 'DEM0020', '9BDDEM001220DEM0020', '121000.00',1, 0, 'DEMO-0220');

# |------------------------ tb_apolice ------------------------|

-- numero_apolice = valor FICTICIO completo; numero_apolice_mascarado = do fixture.
-- fk_segurado = seguradora (110 Horizonte / 120 Orbita) conforme fk_seguradora do fixture.
-- fk_status = 2 (APOLICE/ATIVA); possui_solicitacao_ativa conforme fixture.
INSERT IGNORE INTO tb_apolice
  (id_apolice, numero_apolice, numero_apolice_mascarado, fk_pessoa, fk_segurado, fk_veiculo,
   data_inicio, data_fim, cobertura, assistencia, endosso, versao, perfil,
   fk_local_pernoite, fk_status, fk_forma_pagamento, possui_solicitacao_ativa)
VALUES
  (1001, 'ORB-2026-0600', 'ORB-****-1001', 1,  110, 201, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 1),
  (1002, 'ORB-2026-0601', 'ORB-****-1002', 1,  110, 202, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 1),
  (1003, 'ORB-2026-0602', 'ORB-****-1003', 2,  110, 203, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 1),
  (1004, 'ORB-2026-0603', 'ORB-****-1004', 3,  110, 204, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 1),
  (1005, 'ORB-2026-0604', 'ORB-****-1005', 4,  110, 205, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 1),
  (1006, 'ORB-2026-0605', 'ORB-****-1006', 5,  110, 206, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1007, 'ORB-2026-0606', 'ORB-****-1007', 6,  120, 207, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1008, 'ORB-2026-0607', 'ORB-****-1008', 7,  120, 208, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 1),
  (1009, 'ORB-2026-0608', 'ORB-****-1009', 1,  110, 209, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1010, 'ORB-2026-0609', 'ORB-****-1010', 8,  120, 210, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1011, 'ORB-2026-0610', 'ORB-****-1011', 9,  110, 211, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1012, 'ORB-2026-0611', 'ORB-****-1012', 10, 110, 212, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1013, 'ORB-2026-0612', 'ORB-****-1013', 2,  110, 213, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1014, 'ORB-2026-0613', 'ORB-****-1014', 3,  110, 214, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1015, 'ORB-2026-0614', 'ORB-****-1015', 4,  110, 215, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1016, 'ORB-2026-0615', 'ORB-****-1016', 5,  110, 216, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1017, 'ORB-2026-0616', 'ORB-****-1017', 6,  120, 217, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1018, 'ORB-2026-0617', 'ORB-****-1018', 7,  120, 218, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1019, 'ORB-2026-0618', 'ORB-****-1019', 8,  120, 219, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0),
  (1020, 'ORB-2026-0619', 'ORB-****-1020', 9,  110, 220, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 100000.00, 'ASSISTENCIA_24H', NULL, 1, 'COMPLETO',    1, 2, 1, 0);

# |------------------------ tb_analista_seguradora ------------------------|

-- 8 analistas x 2 seguradoras (110 Horizonte / 120 Orbita), ativo = 1
INSERT IGNORE INTO tb_analista_seguradora
  (id_analista_seguradora, fk_analista, fk_seguradora, ativo, data_vinculo)
VALUES
  (1,  901, 110, 1, '2026-08-18 12:00:00'),
  (2,  901, 120, 1, '2026-08-18 12:00:00'),
  (3,  902, 110, 1, '2026-08-18 12:00:00'),
  (4,  902, 120, 1, '2026-08-18 12:00:00'),
  (5,  903, 110, 1, '2026-08-18 12:00:00'),
  (6,  903, 120, 1, '2026-08-18 12:00:00'),
  (7,  904, 110, 1, '2026-08-18 12:00:00'),
  (8,  904, 120, 1, '2026-08-18 12:00:00'),
  (9,  905, 110, 1, '2026-08-18 12:00:00'),
  (10, 905, 120, 1, '2026-08-18 12:00:00'),
  (11, 906, 110, 1, '2026-08-18 12:00:00'),
  (12, 906, 120, 1, '2026-08-18 12:00:00'),
  (13, 907, 110, 1, '2026-08-18 12:00:00'),
  (14, 907, 120, 1, '2026-08-18 12:00:00'),
  (15, 908, 110, 1, '2026-08-18 12:00:00'),
  (16, 908, 120, 1, '2026-08-18 12:00:00');

# |------------------------ fim do seed ------------------------|