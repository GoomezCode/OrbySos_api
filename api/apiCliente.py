from fastapi import APIRouter, HTTPException
from database.select import *
from classes.classPessoa import *

router = APIRouter(
    prefix="/clientes",
    tags=["cliente"]
)

@router.get("/me")
def cliente():    
    pf = select().select_cliente_pf()
    head = {
    "schema_version": 2,
    "selection_rule": {
        "source": "tb_pessoa.ISJURIDICO",
        "mapping": {
            "false_or_0": "FISICA",
            "true_or_1": "JURIDICA"
        }
    }
    }
    
    body = {
        "response_exemples":{
            "FISICA":{
               
            },
            "JURIDICA":{
                
            }
        }
    }

    
    return body