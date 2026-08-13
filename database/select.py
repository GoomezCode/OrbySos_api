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
    
    def select_contato_id(self, id):
        query = f'''
        select tc.tipo_contato, tc.valor_contato, tc.principal, ts.rotulo
        from tb_contato tc
        inner join tb_status ts on tc.fk_status = ts.id_status
        where fk_pessoa = {id}
        '''
        return self.pesquisarAll(query)
    
    def select_cliente_pf(self):
        query = 'select tpf.id_pf, tpf.nome, tpf.cpf, tpf.data_nascimento from tb_pessoa_fisica tpf'
        return self.pesquisarAll(query)
