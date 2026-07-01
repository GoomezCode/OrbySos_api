from database.select import *
import requests
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

def buscarCep(cep):
    url = f"https://brasilapi.com.br/api/cep/v1/{cep}"
    response = requests.get(url)
    dados = []
    if response.status_code == 200:
        dados = response.json()
        return {
            "logradouro":dados["street"],
            "bairro":dados["neighborhood"],
            "cidade":dados["city"],
            "estado":dados["state"],
            "cep":dados["cep"]
        }
    else:
        return response.status_code