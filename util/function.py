from database.select import *
import bcrypt

# criptografia da senha
def gerarHash(senha: str) -> str:
    senha = senha.encode('utf-8')

    hash = bcrypt.hashpw(senha, bcrypt.gensalt())
    return hash.decode('utf-8')

# valida por uma senha é uma Hash
def consultHash(senhaDigitada: str, hashCode: str) -> bool:
    return bcrypt.checkpw(
        senhaDigitada.encode('utf-8'),
        hashCode.encode('utf-8')
    )

def isJuridico(id):
    dados = select().select_all("tb_pessoa")
    for i in dados:
        if i[0] == int(id):
            print("Encontrado: ", i)