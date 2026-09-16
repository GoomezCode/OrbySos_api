import uuid

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.errors import http_exception_handler, validation_exception_handler, unhandled_exception_handler
from middleware.auth import auth_middleware
from api import apiInsert
from routers import auth as auth_router
from routers import catalogs as catalogs_router
from routers import client as client_router
from routers import admin as admin_router
from routers import sync as sync_router

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title="OrbySOS API",
    description="API REST para gestão de seguros veiculares, ocorrências e assistências",
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(auth_middleware)

app.include_router(apiInsert.router, prefix=API_V1_PREFIX)
app.include_router(auth_router.router, prefix=API_V1_PREFIX)
app.include_router(catalogs_router.router, prefix=API_V1_PREFIX)
app.include_router(client_router.router, prefix=API_V1_PREFIX)
app.include_router(admin_router.router, prefix=API_V1_PREFIX)
app.include_router(sync_router.router, prefix=API_V1_PREFIX)


@app.get("/", tags=["health"])
def root():
    return {"mensagem": "OrbySOS API v1 — inicializada com sucesso."}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, log_level="info", reload=True)
