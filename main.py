from fastapi import FastAPI
import uvicorn
from api import apiMain,apiInsert, apiCliente, apiAdmin, apiAuth

app = FastAPI()

app.include_router(apiMain.router)
app.include_router(apiInsert.router)
app.include_router(apiCliente.router)
app.include_router(apiAdmin.router)
app.include_router(apiAuth.router)

def raiz():
    return {"mensagem":"api inicializada..."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)

# Duvidas em Algumas rotas
# /admin/dashboard
# /admin/solicitacoes

# mudar o formato dos status das ocorrencias com codigo - Nome - descricao
# mudar o formato dos status do tipo assistencia com Codigo - nome

# entender o status da tabela Historico_status no database - talvez trocar para um fk_status
# sugerir colocar uma coluna de "isAtivo" na tb_assistencia