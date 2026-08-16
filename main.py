from fastapi import FastAPI
import uvicorn
from api import apiConsulta,apiInsert, apiCliente, apiAdmin

app = FastAPI()

app.include_router(apiConsulta.router)
app.include_router(apiInsert.router)
app.include_router(apiCliente.router)
app.include_router(apiAdmin.router)

def raiz():
    return {"mensagem":"api inicializada..."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)

# Duvidas em Algumas rotas
# /admin/dashboard
# /admin/solicitacoes

# mudar o formato dos status das ocorrencias com codigo - Nome - descricao