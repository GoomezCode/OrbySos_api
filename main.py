from fastapi import FastAPI
import uvicorn
from api import apiConsulta,apiInsert

app = FastAPI()

app.include_router(apiConsulta.router)
app.include_router(apiInsert.router)

@app.get("/")
def raiz():
    return {"mensagem":"api inicializada..."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, log_level="info", reload=True)