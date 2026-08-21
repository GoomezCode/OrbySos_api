import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
load_dotenv()

class connectMysql:
    def __init__(self, host, username, password, bank, port):
        self.host = host
        self.username = username
        self.password = password
        self.bank = bank
        self.port = port
        self.conexao = None
    def connect(self):
        try:
            self.conexao = mysql.connector.connect(
                host = self.host,
                database = self.bank,
                user = self.username,
                password = self.password,
                port = self.port,
                auth_plugin='mysql_native_password'
            )
            if self.conexao.is_connected():
                print("Conexão feita")
                return self.conexao
            
        except Error as error:
            print(f"Erro ao conectar: {error}")
            return None

def connectDB():
    db = connectMysql(
        os.getenv("host"),
        os.getenv("user"),
        os.getenv("password"),
        os.getenv("bank"),
        os.getenv("port")
    )
    return db.connect()