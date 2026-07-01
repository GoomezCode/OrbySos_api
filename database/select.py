from database.DataBase import connectDB
class select:
    def __init__(self):
        self.db = connectDB()
        self.cursor = self.db.cursor()
        
    def select_all(self, table):
        query = f'select * from {table}'
        self.cursor.execute(query)
        resultado = self.cursor.fetchall()
        self.cursor.close()
        return resultado
    
    def select_pessoa_id(self, id):
        query = f'select * from tb_pessoa where id_pessoa = {id}'
        self.cursor.execute(query)
        resultado = self.cursor.fetchone()
        self.cursor.close()
        return resultado