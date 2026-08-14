from fastapi import APIRouter, HTTPException
from database.select import *
from classes.classPessoa import *

router = APIRouter(
    prefix="/clientes",
    tags=["clientes"]
)

@router.get("/me")
def cliente():    
    fisica = []
    for i in select().select_cliente_pf():
        contatos = []
        for j in select().select_contato_id(i[0]):
            contatos.append({"tipo": j[0], "valor_mascarado": j[1], "principal": j[2]})
        

        fisicaJson ={
            "id_pessoa": i[0],
            "tipo_pessoa": "FISICA",
            "nome": i[1],
            "cpf_mascarado": i[2],
            "data_nascimento": i[3],
            "contatos": contatos
        }
        fisica.append(fisicaJson)

    juridica = []
    for i in select().select_cliente_pj():
        contatos = []
        for j in select().select_contato_id(i[0]):
            contatos.append({"tipo": j[0], "valor_mascarado": j[1], "principal": j[2]})

        juridicaJson = {
            "id_pessoa": i[0],
            "tipo_pessoa": "JURIDICA",
            "razao_social": i[1],
            "nome_fantasia": i[2],
            "cnpj_mascarado": i[3],
            "contatos": contatos
        }        
        juridica.append(juridicaJson)
    
    json = {
    "schema_version": 2,
    "selection_rule": {
        "source": "tb_pessoa.ISJURIDICO",
        "mapping": {
            "false_or_0": "FISICA",
            "true_or_1": "JURIDICA"
        }
    },
    "response_exemples":{
            "FISICA":fisica,
            "JURIDICA":juridica
        }
    }
    return json