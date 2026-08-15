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

    def select_cliente_pj(self):
        query = "select tpj.id_pj, tpj.razao_social, tpj.nome_fantasia, tpj.cnpj from tb_pessoa_juridica tpj"
        return self.pesquisarAll(query)
    def select_cliente_apolice(self):
        query = '''select
        ta.id_apolice, ta.numero_apolice, ta.data_inicio, ta.data_fim, ts.rotulo,
        tpf.id_pf, tpf.nome, tpf.cpf,
        tpj.id_pj, tpj.nome_fantasia,
        tv.id_veiculo, tv.marca, tv.modelo, tv.ano_fabricado, tv.ano_modelo, tv.placa
        from tb_apolice ta
        inner join tb_status ts on ta.fk_status = ts.id_status
        inner join tb_pessoa_fisica tpf on ta.fk_pessoa = tpf.id_pf
        inner join tb_pessoa_juridica tpj on ta.fk_segurado = tpj.id_pj
        inner join tb_veiculo tv on ta.fk_veiculo = tv.id_veiculo'''
        return self.pesquisarAll(query)
    def select_cliente_apolice_solicitacao_id(self, id):
        query = f'''select
        ts.id_solicitacao, ts.protocolo_solicitacao, tb_status.codigo, ts.prioridade, ts.data_recebimento
        from tb_solicitacao ts
        inner join tb_status on ts.fk_status = tb_status.id_status
        where fk_apolice = {id}'''
        return self.pesquisarAll(query)