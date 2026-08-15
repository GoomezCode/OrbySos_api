from fastapi import APIRouter, HTTPException
from database.select import *
from classes.classPessoa import *

router = APIRouter(
    prefix="/clientes",
    tags=["clientes"]
)

@router.get("/me")
def me():    
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

@router.get("/me/apolices")
def me_apolices():
    items = []
    for i in select().select_cliente_apolice():
        solicitacao = select().select_cliente_apolice_solicitacao_id(i[0])[0]
        if str(solicitacao[2]).lower() == "concluido" or str(solicitacao[2]).lower() == "recusado":
            isAtiva = False
        else: isAtiva = True    

        contatos = []
        for j in select().select_contato_id(i[8]):
            contatos.append({"tipo": j[0], "valor_mascarado": j[1], "principal": j[2]})

        veiculo = {
            "id_veiculo": i[10],
            "marca": i[11],
            "modelo": i[12],
            "ano_fabricacao": i[13],
            "ano_modelo": i[14],
            "placa_mascarada": i[15]
        }
        if isAtiva:
            solicitacao_ativa = {
                "id_solicitacao": solicitacao[0],
                "numero_solicitacao": solicitacao[1],
                "status": solicitacao[2],
                "prioridade": solicitacao[3],
                "data_recebimento": solicitacao[4]
            }
        else:solicitacao_ativa = None
        
        apolice = {
            "id_apolice": i[0],
            "numero_apolice_mascarado": i[1],
            "data_inicio": i[2],
            "data_fim": i[3],
            "status": i[4],
            "possui_solicitacao_ativa": isAtiva,
            "clientes": { "id_pessoa": i[5], "tipo_pessoa": "FISICA", "nome": i[6], "cpf_mascarado": i[7]},
            "seguradora": {
            "id_pj": i[8],
            "nome_fantasia": i[9],
            "contatos":contatos,
            "veiculo": veiculo,
            "solicitacao_ativa":solicitacao_ativa
            }
        }
        items.append(apolice)

    json = {
        "schema_version": 2,
        "request_query": { "status": "ATIVA" },
        "response": {
            "items": items,
            "pagination": {"page":1,"page_size":20, "total_items":1, "total_pages": 1}
        }
    }
    return json

@router.get("/me/solicitacoes")
def me_solicitacoes():
    return "hello"