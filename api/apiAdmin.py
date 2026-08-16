from fastapi import APIRouter, HTTPException
from database.select import *
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
        ocorrencia = { "id_tipo_ocorrencia": i[18], "codigo": i[19], "nome": i[19] }
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
        ocorrencia = { "id_tipo_ocorrencia": i[23], "codigo": i[24], "nome": i[24] }

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

@router.get("/solicitacoes/{solicitacao_id}")
def solicitacoes_id(solicitacao_id:int):
    dado_solicitacao = select_admin() .solicitacao_id(solicitacao_id)
    json = {
        "schema_version": 2,
        "response":{
            "solicitacao":{""
                "id_solicitacao": dado_solicitacao[0],
                "id_solicitacao_cliente": dado_solicitacao[1],
                "numero_solicitacao": dado_solicitacao[2],
                "descricao_evento": dado_solicitacao[3],
                "possui_feridos": dado_solicitacao[4],
                "risco_imediato": dado_solicitacao[5],
                "prioridade": dado_solicitacao[6],
                "local": { "endereco": dado_solicitacao[7], "numero_local": "SEM NUMERO REAL", "cidade": dado_solicitacao[8], "estado": dado_solicitacao[9], "ponto_referencia": dado_solicitacao[10] },
                "status": dado_solicitacao[11],
                "data_criacao_cliente": dado_solicitacao[12],
                "data_recebimento": dado_solicitacao[13],
                "data_decisao": dado_solicitacao[14],
                "motivo_recusa": dado_solicitacao[15],
                "version": dado_solicitacao[16]
            },
            "cliente": { "id_pessoa": dado_solicitacao[17], "tipo_pessoa": "FISICA", "nome": dado_solicitacao[18], "cpf_mascarado": dado_solicitacao[19] },
            "apolice": {"id_apolice": dado_solicitacao[20], "numero_apolice_mascarado": dado_solicitacao[21], "data_inicio": dado_solicitacao[22], "data_fim": dado_solicitacao[23], "status": dado_solicitacao[24]},
            "veiculo": {"id_veiculo": dado_solicitacao[25], "marca": dado_solicitacao[26], "modelo": dado_solicitacao[27], "ano_fabricacao": dado_solicitacao[28], "ano_modelo": dado_solicitacao[29], "placa_mascarada": dado_solicitacao[30], "blindado": dado_solicitacao[31]},
            "seguradora": { "id_pj": dado_solicitacao[32], "nome_fantasia": dado_solicitacao[33] },
            "ocorrencia": {"id_tipo_ocorrencia": 1, "codigo": "PANE_MECANICA", "nome": "Pane mecanica", "descricao": "Falha mecanica que impede a continuidade da viagem."},
            "analista":{"id_usuario": 901, "nome_exibicao": "Analista Horizonte"},
            "assistencias":[],
            # Entender como funciona essa perguntas (talvez criar uma tabela para ela)
            "perguntas": [{ "id_pergunta": 7001, "origem": "GUINCHO", "tipo": "TAXI", "status": "PENDENTE", "necessita_taxi": None, "quantidade_passageiros": None, "necessita_acessibilidade": None, "quantidade_criancas": None, "quantidade_animais": None, "bagagem": None, "observacoes": None, "data_criacao": "2026-08-06T12:11:01Z", "data_resposta": None, "version": 1 }],
            "historico":[],
            "tipos_assistencia_disponiveis":[]
        }
    }
    return json
