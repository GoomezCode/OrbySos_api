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
    
class select_cliente:
    def __init__(self):
        pass

    def contato_id(self, id):
        query = f'''
        select tc.tipo_contato, tc.valor_contato, tc.principal, ts.rotulo
        from tb_contato tc
        inner join tb_status ts on tc.fk_status = ts.id_status
        where fk_pessoa = {id}
        '''
        return select().pesquisarAll(query)
    
    def pf(self):
        query = 'select tpf.id_pf, tpf.nome, tpf.cpf, tpf.data_nascimento from tb_pessoa_fisica tpf'
        return select().pesquisarAll(query)
    
    def pj(self):
        query = "select tpj.id_pj, tpj.razao_social, tpj.nome_fantasia, tpj.cnpj from tb_pessoa_juridica tpj"
        return select().pesquisarAll(query)

    def apolice(self):
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
            return select().pesquisarAll(query)
    
    def apolice_solicitacao_id(self, id):
        query = f'''select
        ts.id_solicitacao, ts.protocolo_solicitacao, tb_status.codigo, ts.prioridade, ts.data_recebimento
        from tb_solicitacao ts
        inner join tb_status on ts.fk_status = tb_status.id_status
        where fk_apolice = {id}'''
        return select().pesquisarAll(query)
    
    def solicitacao(self):
        query = '''select
        ts.id_solicitacao, ts.protocolo_solicitacao, tst.codigo, ts.prioridade, ts.descricao_evento,
        ts.possui_feridos, ts.risco_imediato, ts.data_recebimento, ts.data_decisao, ts.motivo_recusa, ts.version,
        tv.id_veiculo, tv.marca, tv.modelo, tv.ano_modelo, tv.placa,
        toc.id_ocorrencia,toc.codigo, toc.nome
        from tb_solicitacao ts
        inner join tb_status tst on ts.fk_status = tst.id_status
        inner join tb_veiculo tv on ts.fk_veiculo = tv.id_veiculo
        inner join tb_ocorrencia toc on ts.fk_tipo_ocorrencia = toc.id_ocorrencia'''
        return select().pesquisarAll(query)

class select_admin:
    def __init__(self):
        pass
    def dashboard(self):
        query = '''select
        ts.id_solicitacao, ts.protocolo_solicitacao, ts.prioridade, tst.codigo, ts.data_recebimento, ts.version,
        tpf.id_pf, tpf.nome, tpf.cpf, ta.id_apolice, ta.numero_apolice,
        tv.id_veiculo, tv.marca, tv.modelo, tv.ano_modelo, tv.placa,
        tpj.id_pj, tpj.nome_fantasia, toc.id_ocorrencia,toc.codigo, toc.nome
        from tb_solicitacao ts
        inner join tb_status tst on ts.fk_status = tst.id_status
        inner join tb_pessoa_fisica tpf on ts.fk_pessoa = tpf.id_pf
        inner join tb_apolice ta on ts.fk_apolice = ta.id_apolice
        inner join tb_veiculo tv on ts.fk_veiculo = tv.id_veiculo
        inner join tb_pessoa_juridica tpj on ts.fk_seguradora = tpj.id_pj
        inner join tb_ocorrencia toc on ts.fk_tipo_ocorrencia = toc.id_ocorrencia'''
        return select().pesquisarAll(query) 
    def solicitacao(self):
        query = '''select
        ts.id_solicitacao, ts.protocolo_solicitacao, ts.descricao_evento, ts.possui_feridos, ts.risco_imediato, ts.prioridade,
        tst.codigo, ts.data_recebimento, ts.data_decisao, ts.motivo_recusa, ts.version,
        tpf.id_pf, tpf.nome, tpf.cpf, ta.id_apolice, ta.numero_apolice,
        tv.id_veiculo, tv.marca, tv.modelo, tv.ano_modelo, tv.placa,
        tpj.id_pj, tpj.nome_fantasia, toc.id_ocorrencia,toc.codigo, toc.nome
        from tb_solicitacao ts
        inner join tb_status tst on ts.fk_status = tst.id_status
        inner join tb_pessoa_fisica tpf on ts.fk_pessoa = tpf.id_pf
        inner join tb_apolice ta on ts.fk_apolice = ta.id_apolice
        inner join tb_veiculo tv on ts.fk_veiculo = tv.id_veiculo
        inner join tb_pessoa_juridica tpj on ts.fk_seguradora = tpj.id_pj
        inner join tb_ocorrencia toc on ts.fk_tipo_ocorrencia = toc.id_ocorrencia;'''
        return select().pesquisarAll(query)
    def solicitacao_id(query, id):
        query = f'''select
            ts.id_solicitacao, ts.id_solicitacao_cliente, ts.protocolo_solicitacao, ts.descricao_evento, ts.possui_feridos, ts.risco_imediato, ts.prioridade,
            te.logradouro, te.cidade, te.estado, te.complemento, tst.codigo, ts.data_criacao_cliente, ts.data_recebimento, ts.data_decisao, ts.motivo_recusa, ts.version,
            tpf.id_pf, tpf.nome, tpf.cpf, ta.id_apolice, ta.numero_apolice, ta.data_inicio, ta.data_fim, tsta.codigo,
            tv.id_veiculo, tv.marca, tv.modelo, tv.ano_fabricado,tv.ano_modelo, tv.placa, tv.blindado,
            tpj.id_pj, tpj.nome_fantasia, toc.id_ocorrencia, toc.codigo, toc.nome, toc.descricao, tu.id_user, tu.login
            from tb_solicitacao ts
            inner join tb_endereco te on ts.fk_local = te.id_endereco
            inner join tb_status tst on ts.fk_status = tst.id_status
            inner join tb_pessoa_fisica tpf on ts.fk_pessoa = tpf.id_pf
            inner join tb_apolice ta on ts.fk_apolice = ta.id_apolice
            inner join tb_status tsta on ta.fk_status = tsta.id_status
            inner join tb_veiculo tv on ts.fk_veiculo = tv.id_veiculo
            inner join tb_pessoa_juridica tpj on ts.fk_seguradora = tpj.id_pj
            inner join tb_ocorrencia toc on ts.fk_tipo_ocorrencia = toc.id_ocorrencia
            inner join tb_user tu on ts.fk_analista_responsavel = tu.id_user
            where ta.id_apolice = {id}'''
        return select().pesquisarOne(query)
    def solicitacao_assistencia_idSolicitacao(query, id):
        query = f'''select
        tsa.id_solicitacao_assistencia, tpa.id_tpAssistencia, tpa.codigo, tpa.nome,
        ts.codigo, tsa.comentario, tu.id_user, tu.login, tsa.data_inclusao, tsa.data_atualizacao, tsa.version
        from tb_solicitacao_assistencia tsa
        inner join tb_assistencia ta on tsa.fk_assistencia = ta.id_assistencia
        inner join tb_tpAssistencia tpa on ta.fk_id_tpAssistencia = tpa.id_tpAssistencia
        inner join tb_status ts on ta.fk_status = ts.id_status
        inner join tb_user tu on tsa.fk_usuario_responsavel = tu.id_user
        where tsa.fk_solicitacao = {id}'''
        return select().pesquisarAll(query)
    def historico_idSolicitacao(query, id):
        query = f'''select
        hs.id_historico, hs.status, hs.data_status, tu.id_user, tu.login, hs.comentario
        from historico_status hs
        inner join tb_user tu on hs.fk_usuario_responsavel = tu.id_user
        where hs.fk_solicitacao = {id}'''
        return select().pesquisarAll(query)
    def tipos_assistencia_disponiveis(query):
        query = '''select
        tpa.id_tpAssistencia, tpa.codigo, tpa.nome, tpa.descricao, tpa.ativo
        from  tb_tpAssistencia tpa'''
        return select().pesquisarAll(query)
    def tipos_assistencia(self):
        return select().select_all("tb_tpAssistencia")
        
