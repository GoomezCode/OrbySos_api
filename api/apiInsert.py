from fastapi import APIRouter, HTTPException
from database.insert import *
from database.select import *
from util.function import buscarCep, gerarHash, cnpj, cpf
from classes.classPessoa import *

router = APIRouter(
    prefix="/post",
    tags=["post"]
)

@router.post("/pessoa/{isJuridico}")
def pessoa(isJuridico:bool):    
    id_pessoa = insert().insert_pessoa(isJuridico)
    if isJuridico:
        return{"User": "PJ", "id": id_pessoa}
    else:
        return{"User": "PF", "id": id_pessoa}
    
@router.post("/pj")
def pessoaJuridica(dado:tb_pessoa_juridica):
    dados = select().select_pessoa_id(dado.id_pj)
    if dados == None:
        raise HTTPException(
            status_code=404, 
            detail="Usuário não encontrado!!!"
        )
    
    if dados[2] == 0:
         raise HTTPException(
            status_code=400, 
            detail="Usuário não e Pessoa Juridica!!!"
        )
         
    if not cnpj.validate(dado.cnpj):
        raise HTTPException(
            status_code=400,
            detail="CNPJ é inválido!!!"
        )
    
    insert().insert_pessoa_Juridica(dado)
    return {"messagem":f"User: {dado.razao_social} cadastrado com sucesso!!"}

@router.post("/pf")
def pessoaFisica(dado:tb_pessoa_fisica):
    dados = select().select_pessoa_id(dado.id_pf)
    if dados == None:
        raise HTTPException(
            status_code=404, 
            detail="Usuário não encontrado!!!"
        )
    
    if dados[2] == 1:
         raise HTTPException(
            status_code=400, 
            detail="Usuário não e Pessoa Fisica!!"
        )
    
    if not cpf.validate(dado.cpf):
        raise HTTPException(
            status_code=400,
            detail="CPF é inválido!!"
        )
    
    
    insert().insert_pessoa_fisica(dado)
    return {"messagem":f"User: {dado.nome} cadastrado com sucesso!!"}

@router.post("/endereco")
def endereco(dado:tb_endereco):
    dados = select().select_pessoa_id(dado.fk_pessoa)
    if dados == None:
        raise HTTPException(
            status_code=404, 
            detail="Usuário não encontrado!!!"
        )
    
    '''
        # Enquanto o CEP não for encontrado no banco de dados local,
        # o sistema continua tentando obter as informações.
        #
        # 1. Consulta o CEP na tabela local de CEPs.
        # 2. Se o CEP existir, preenche os dados de endereço
        #    (logradouro, bairro, cidade e estado) e encerra o loop.
        # 3. Caso não exista, busca as informações em uma API externa.
        # 4. Se a API retornar código 400, significa que o CEP é inválido
        #    ou não foi encontrado, então o usuário deverá informar os
        #    dados manualmente.
        # 5. Se o CEP for encontrado na API, os dados são gravados no
        #    banco local para futuras consultas.
        # 6. O loop reinicia para buscar novamente o CEP, que agora já
        #    estará cadastrado no banco local.
    '''
    
    while True:
        dadosCep = select().select_cep_cep(dado.cep)
        if dadosCep != None:
            dado.logradouro = dadosCep[1]
            dado.bairro = dadosCep[2]
            dado.cidade = dadosCep[3]
            dado.estado = dadosCep[4]
            break
        else:
            dadosCep = buscarCep(dado.cep)
            if dadosCep == 400:
                return {"messagem": f"Insira os dados do cep manualmente!!"}
            insert().insert_cep(dadosCep)
            continue
        
    insert().insert_endereco(dado)
    return {"messagem":f"Cadastro de endereço para o id_user: {dado.fk_pessoa} feito com sucesso!!"}

@router.post("/user")
def user(dado:tb_user):
    dados = select().select_pessoa_id(dado.fk_pessoa)
    if dados == None:
        raise HTTPException(
            status_code=404, 
            detail="Usuário não encontrado!!!"
        )
    dado.senha = gerarHash(dado.senha)
    
    insert().insert_user(dado)
    return {"messagem":f"User: {dado.fk_pessoa} foi cadastrado com sucesso!!"}

@router.post("/veiculo")
def veiculo(dado:tb_veiculo):
    dados = select().select_pessoa_id(dado.fk_pessoa)
    if dados == None:
        raise HTTPException(
            status_code=404, 
            detail="Usuário não encontrado!!!"
        )
    
    insert().insert_veiculo(dado)
    return{"messagem":f"O veiculo: {dado.marca} foi cadastrado com sucesso para {dado.fk_pessoa}"}

