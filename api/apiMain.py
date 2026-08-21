from fastapi import APIRouter
from classes.classPessoa import *
from database.select import select

router = APIRouter(
    prefix="",
    tags=[""]
)

@router.get("/tipos-ocorrencia")
def tipos_ocorrencia():
    items = []
    for i in select().select_all("tb_ocorrencia"):
        items.append({
             "id_tipo_ocorrencia": i[0],
             "codigo": i[1],
             "nome": i[2],
             "descricao": i[3],
             "ativo": i[4],
             "ordem": i[0]
        })
    json = {
        "schema_version": 2,
        "request_query": { "ativo": True },
        "response":{
            "items":items
        }
    }
    return json

@router.get("/configuracoes/publicas")
def configuracoes_publicas():
    json = {
    "schema_version": 2,
    "response": {
            "pais": "BR",
            "mensagem": "Em caso de feridos ou risco imediato, procure os servicos publicos de emergencia.",
            "servicos": [
                { "codigo": "SAMU", "nome": "SAMU", "telefone": "192" },
                { "codigo": "BOMBEIROS", "nome": "Corpo de Bombeiros", "telefone": "193" },
                { "codigo": "POLICIA", "nome": "Policia Militar", "telefone": "190" }
            ]
        }
    }
    return json

@router.get("/solicitacoes/{solicitacao_id}")
def solicitacoes_id(solicitacao_id:int):
    solicitacao = select().solicitacoes_id(solicitacao_id)
    contato = select().contato_pj(solicitacao[33])
    contatos = []
    if contato != []:
        for i in contato:
            contatos.append({
                "tipo": i[0],
                "rotulo": i[1],
                "valor": i[2] 
                })
    else: contato = None

    perguntas = []
    for i in select().selicitacoes_perguntas(solicitacao[0]):
        perguntas.append({
            "id_pergunta": i[0],
            "origem": i[1],
            "tipo": i[2],
            "status": i[3],
            "necessita_taxi": i[4],
            "quantidade_passageiros": i[5],
            "necessita_acessibilidade": i[6],
            "quantidade_criancas": i[7],
            "quantidade_animais": i[8],
            "bagagem": i[9],
            "observacoes": i[10],
            "data_criacao": i[11],
            "data_resposta": i[12],
            "version": 1
        })

    historico = []
    for i in select().solicitacao_historico(solicitacao[0]):
        historico.append({
            "id_historico": i[0], 
            "status": i[1], 
            "data_status": i[2],
            "responsavel": { "id_usuario": i[3], "nome_exibicao": i[4] }, 
            "comentario": i[5]
        })

    json = {
        "schema_version": 2,
        "response": {
            "solicitacao": {
                "id_solicitacao": solicitacao[0],
                "id_solicitacao_cliente": solicitacao[1],
                "numero_solicitacao": solicitacao[2],
                "descricao_evento": solicitacao[3],
                "possui_feridos": solicitacao[4],
                "risco_imediato": solicitacao[5],
                "prioridade": solicitacao[6],
                "local": { "endereco": solicitacao[7], "numero_local": "SEM NUMERO REAL", "cidade": solicitacao[8], "estado": solicitacao[9], "ponto_referencia": solicitacao[10] },
                "status": solicitacao[11],
                "data_criacao_cliente": solicitacao[12],
                "data_recebimento": solicitacao[13],
                "data_decisao": solicitacao[14],
                "motivo_recusa": solicitacao[15],
                "version": solicitacao[16]
            },
            "cliente": { "id_pessoa": solicitacao[17], "tipo_pessoa": "FISICA", "nome": solicitacao[18], "cpf_mascarado": solicitacao[19] },
            "apolice": { "id_apolice": solicitacao[20], "numero_apolice_mascarado": solicitacao[21], "data_inicio": solicitacao[22], "data_fim": solicitacao[23], "status": solicitacao[24] },
            "veiculo": { "id_veiculo": solicitacao[25], "marca": solicitacao[26], "modelo": solicitacao[27], "versao": solicitacao[28], "ano_fabricacao": solicitacao[29], "ano_modelo": solicitacao[30], "placa_mascarada": solicitacao[31], "blindado": solicitacao[32] },
            "seguradora": {
                "id_pj": solicitacao[33],
                "nome_fantasia": solicitacao[34],
                "contatos": contatos
            },
            "ocorrencia": { "id_tipo_ocorrencia": solicitacao[35], "codigo": solicitacao[36], "nome": solicitacao[37], "descricao": solicitacao[38] },
            "analista": { "id_usuario": solicitacao[39], "nome_exibicao": solicitacao[40] },
            "perguntas":perguntas,
            "historico":historico
            
        }
    }
    return json