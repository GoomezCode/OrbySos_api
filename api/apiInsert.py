from fastapi import APIRouter, HTTPException
from database.insert import *
from database.select import *
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
            detail="Usuário não e Pessoa Juridica!!"
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
    
    insert().insert_endereco(dado)
    return {"messagem":f"Cadastro de endereço para o id_user: {dado.fk_pessoa} feito com sucesso!!"}

@router.post("/cep")
def cep(dado:tb_cep):
    
    insert().insert_cep(dado)
    return {"teste":"Daniel bonito"}

@router.post("/user")
def user(dado:tb_user):
    
    insert().insert_user(dado)
    return {"teste":"Daniel bonito"}

@router.post("/veiculo")
def veiculo(dado:tb_veiculo):
    
    insert().insert_veiculo(dado)
    return{"teste":"Daniel bonito"}