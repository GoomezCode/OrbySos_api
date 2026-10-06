from fastapi import APIRouter, HTTPException
from database.select import select_admin
from classes.classPessoa import *

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

@router.get("/dashboard")
def dashboard():
    metricas = { # Automizar as Metricas com os dados corretos - saber aonde puxar esses dados
        "criticas_abertas": 1,
        "aguardando_analise": 2,
        "confirmadas_em_atendimento": 2,
        "prestadores_acionados": 1,
        "concluidas": 0,
        "recusadas_sem_cobertura": 1
    }

    items =[]
    for i in select_admin().dashboard():
        cliente = { "id_pessoa": i[6], "tipo_pessoa": "FISICA", "nome": i[7], "cpf_mascarado": i[8] }
        apolice = { "id_apolice": i[9], "numero_apolice_mascarado": i[10]}
        veiculo = { "id_veiculo": i[11], "marca": i[12], "modelo": i[13], "ano_modelo": i[14], "placa_mascarada": i[15] }
        seguradora = { "id_pj": i[16], "nome_fantasia": i[17] }
        ocorrencia = { "id_tipo_ocorrencia": i[18], "codigo": i[19], "nome": i[20] }
        items.append({
          "id_solicitacao": i[0],
          "numero_solicitacao": i[1],
          "prioridade": i[2],
          "status": i[3],
          "data_recebimento": i[4],
          "version": i[5],
          "cliente": cliente,
          "apolice": apolice,
          "veiculo": veiculo,
          "seguradora": seguradora,
          "ocorrencia": ocorrencia,
          "analista": None # descobrir qual dados o sistema ira usar caso n seja null
        })


    json = {
        "schema_version": 2,
        "response": {
            "metricas": metricas,
            "fila_prioritaria":{
                "items":items
            }
        }
    }
    return json

@router.get("/solicitacoes")
def solicitacoes():
    request_query={ # enteder como que funciona esse request_query
        "status": "RECEBIDA",
        "prioridade": "CRITICA",
        "tipo_ocorrencia_id": 2,
        "data_inicio": "2026-08-01",
        "data_fim": "2026-08-31",
        "numero_solicitacao": "ORB-2026",
        "pessoa": "Marina",
        "placa": "TST",
        "page": 1,
        "page_size": 20,
        "sort": "prioridade:desc,data_recebimento:asc"
    }

    items = []
    for i in select_admin().solicitacao():
        cliente = { "id_pessoa": i[11], "tipo_pessoa": "FISICA", "nome": i[12], "cpf_mascarado": i[13] }
        apolice = { "id_apolice": i[14], "numero_apolice_mascarado": i[15] }
        veiculo = { "id_veiculo": i[16], "marca": i[17], "modelo": i[18], "ano_modelo": i[19], "placa_mascarada": i[20] }
        seguradora = { "id_pj": i[21], "nome_fantasia": i[22] }
        ocorrencia = { "id_tipo_ocorrencia": i[23], "codigo": i[24], "nome": i[25] }

        items.append({
            "id_solicitacao": i[0],
            "numero_solicitacao": i[1],
            "descricao_evento": i[2],
            "possui_feridos": i[3],
            "risco_imediato": i[4],
            "prioridade": i[5],
            "status": i[6],
            "data_recebimento": i[7],
            "data_decisao": i[8],
            "motivo_recusa": i[9],
            "version": i[10],
            "cliente": cliente,
            "apolice": apolice,
            "veiculo": veiculo,
            "seguradora": seguradora,
            "ocorrencia": ocorrencia,
            "analista": None # Entender como funciona esse analista 
            })

    json ={
    "schema_version": 2,
    "request_query": request_query,
    "response": {
        "items":items,
        "pagination": { "page": 1, "page_size": 20, "total_items": 1, "total_pages": 1 }
      }
    }
    return json

@router.get("/tipos-assistencia")
def tipos_assistencia():
    items =[]
    for i in select_admin().tipos_assistencia():
        items.append({
            "id_tipo_assistencia": i[0],
            "codigo": i[1],
            "nome": i[2],
            "descricao": i[3],
            "ativo": i[4]
        })
    json = {
        "schema_version": 2,
        "request_query": { "ativo": True },
        "response": {
            "items":items
        }
    }
    return json