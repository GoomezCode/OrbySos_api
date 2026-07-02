from database.DataBase import connectDB
class select:
    def __init__(self):
        self.db = connectDB()
        self.cursor = self.db.cursor()
    
    def pesquisarAll(self, query):
        self.cursor.execute(query)
        resultado = self.cursor.fetchall()
        self.cursor.close()
        return resultado
    def pesquisarOne(self, query):
        self.cursor.execute(query)
        resultado = self.cursor.fetchone()
        self.cursor.close()
        return resultado
    
    def select_all(self, table):
        query = f'select * from {table}'
        return self.pesquisarAll(query)
    
    def select_pessoaJuridica(self):
        query = f'''
        select tpj.razao_social, tpj.nome_fantasia, tpj.cnpj, ts.status, tp.data_cadastro
        from tb_pessoa_juridica tpj
        inner join tb_pessoa tp on tpj.id_pj = tp.id_pessoa
        inner join tb_status ts on tpj.fk_status = ts.id_status;
        '''
        return self.pesquisarAll(query)
    
    def select_pessoaFisica(self):
        query = f'''
        select tpf.nome, tpf.cpf, ts.sexo, tpf.data_nascimento, tpf.cnh, tec.estado, tst.status
        from tb_pessoa_fisica tpf
        inner join tb_sexo ts on tpf.fk_sexo = ts.id_sexo
        inner join tb_estado_civil tec on tpf.fk_estado_civil = tec.id_estado_civil
        inner join tb_status tst on tpf.fk_status = tst.id_status;
        '''
        return self.pesquisarAll(query)
    
    def select_pessoa_id(self, id):
        query = f'select * from tb_pessoa where id_pessoa = {id}'
        return self.pesquisarOne(query)
    
    def select_cep_cep(self, cep):
        query = f'select * from tb_cep where  cep = {cep}'
        return self.pesquisarOne(query)