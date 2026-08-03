from database.DataBase import connectDB
from datetime import datetime
from classes.classPessoa import *

class insert:
    def __init__(self):
        self.db = connectDB()
        self.cursor = self.db.cursor()
    def execute_sql(self, query, dados):
        self.cursor.execute(query, dados)
        self.db.commit()
        
        self.cursor.close()
        self.db.close()
        
    def insert_pessoa(self, isJuridico:bool):
        query = f'insert into tb_pessoa(data_cadastro, isJuridico) value (%s, %s)'
        dados = (
            datetime.now(),
            isJuridico
            )
        self.cursor.execute(query, dados)
        self.db.commit()
        
        id_pessoa = self.cursor.lastrowid
        
        self.cursor.close()
        self.db.close()
        return id_pessoa
        
    def insert_pessoa_Juridica(self, pessoa_juridica:tb_pessoa_juridica):
        query = f'insert into tb_pessoa_juridica(id_pj, razao_social, nome_fantasia, cnpj, fk_status) VALUE (%s,%s,%s,%s,%s)'
        dados = (
            pessoa_juridica.id_pj,
            pessoa_juridica.razao_social,
            pessoa_juridica.nome_fantasia,
            pessoa_juridica.cnpj,
            pessoa_juridica.fk_status
            )
        self.execute_sql(query, dados)
        
    def insert_pessoa_fisica(self, pessoa_fisica:tb_pessoa_fisica):
        query = f'insert into tb_pessoa_fisica (id_pf,nome, cpf, fk_sexo, data_nascimento, cnh, fk_estado_civil, fk_status) value (%s,%s,%s,%s,%s,%s,%s,%s)'
        dados = (
            pessoa_fisica.id_pf,
            pessoa_fisica.nome,
            pessoa_fisica.cpf,
            pessoa_fisica.fk_sexo,
            pessoa_fisica.data_nascimento,
            pessoa_fisica.cnh,
            pessoa_fisica.fk_estado_civil,
            pessoa_fisica.fk_Status
        )
        self.execute_sql(query, dados)
        
    def insert_endereco(self, endereco:tb_endereco):
        query = f'''insert into tb_endereco (fk_pessoa, logradouro,bairro,fk_tpLogradouro,cep,cidade,estado,pais,complemento,
        data_criacao) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        dados = (
            endereco.fk_pessoa,
            endereco.logradouro,
            endereco.bairro,
            endereco.fk_tpLogradouro,
            endereco.cep,
            endereco.cidade,
            endereco.estado,
            endereco.pais,
            endereco.complemento,
            datetime.now()
        )
        self.execute_sql(query, dados)
    def insert_cep(self, cep):
        query = f'''insert into tb_cep (logradouro,bairro,cidade,estado,cep) values (%s,%s,%s,%s,%s)'''
        dados = (
            cep["logradouro"],
            cep["bairro"],
            cep["cidade"],
            cep["estado"],
            cep["cep"]
        )
        self.execute_sql(query, dados)
    
    def insert_user(self, user:tb_user):
        query = f'''insert into tb_user (fk_pessoa,login,senha,fk_status) values (%s,%s,%s,%s)'''
        dados = (
            user.fk_pessoa,
            user.login,
            user.senha,
            user.fk_status,
        )
        self.execute_sql(query, dados)
    
    
    def insert_veiculo(self, user:tb_veiculo):
            query = f'''insert into tb_veiculo(fk_pessoa, marca, modelo, versao, ano_fabricado, ano_modelo, placa, chassi, valor_fipe, fk_tpUso, blindado)
            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            dados = (
                user.fk_pessoa,
                user.marca,
                user.modelo,
                user.versao,
                user.ano_fabricacao,
                user.ano_modelo,
                user.placa,
                user.chassi,
                user.valor_fipe,
                user.fk_tpUso,
                user.blindado
            )  
            self.execute_sql(query, dados)

    def insert_apolice(self, apolice:tb_apolice):
        query = f'''insert into tb_apolice (numero_apolice, fk_pessoa, fk_veiculo, data_inicio, data_fim, cobertura, 
        assistencia, endosso, versao, perfil, fk_local_pernoite, fk_status, fk_forma_pagamento) 
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        dados = (
            apolice.numero_apolice,
            apolice.fk_pessoa,
            apolice.fk_veiculo,
            apolice.data_inicio,
            apolice.data_fim,
            apolice.cobertura,
            apolice.assistencia,
            apolice.endosso,
            apolice.versao,
            apolice.perfil,
            apolice.fk_local_pernoite,
            apolice.fk_status,
            apolice.fk_forma_pagamento
        )
        self.execute_sql(query, dados)
    
    def insert_ocorrencia(self, ocorrencia:tb_ocorrencia):
        query = f'''insert into tb_ocorrencia (ocorrencia) values (%s)'''
        dados = (
            ocorrencia.ocorrencia
        )
        self.execute_sql(query, dados)
    
    def insert_assistencia(self, assistencia:tb_assistencia):
        query = f'''insert into tb_assistencia (assistencia) values (%s)'''
        dados = (
            assistencia.assistencia
        )
        self.execute_sql(query, dados)
    
    def insert_apolice_ocorrencia(self, apolice_ocorrencia:tb_apolice_ocorrencia):
        query = f'''insert into tb_apolice_ocorrencia (fk_apolice, fk_ocorrencia) values (%s,%s)'''
        dados = (
            apolice_ocorrencia.fk_apolice,
            apolice_ocorrencia.fk_ocorrencia
        )
        self.execute_sql(query, dados)
    
    def insert_status_ocorrencia(self, status_ocorrencia:tb_status_ocorrencia):
        query = f'''insert into tb_status_ocorrencia (fk_apo_ocorrencia, status) values (%s,%s)'''
        dados = (
            status_ocorrencia.fk_apo_ocorrencia,
            status_ocorrencia.status
        )
        self.execute_sql(query, dados)
    
    def insert_ocorrencia_assistencia(self, ocorrencia_assistencia:tb_ocorrencia_assistencia):
        query = f'''insert into tb_ocorrencia_assistencia (fk_apo_ocorrencia, fk_assistencia, fk_status, comentario) values (%s,%s,%s,%s)'''
        dados = (
            ocorrencia_assistencia.fk_apo_ocorrencia,
            ocorrencia_assistencia.fk_assistencia,
            ocorrencia_assistencia.fk_status,
            ocorrencia_assistencia.comentario
        )
        self.execute_sql(query, dados)