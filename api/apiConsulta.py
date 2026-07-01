from fastapi import APIRouter
from classes.classPessoa import *
from database.select import select

router = APIRouter(
    prefix="/get",
    tags=["get"]
)

@router.get("/all/{table}")
def getAll(table:str):
    return select().select_all(table)

@router.get("/filter/tbPessoaId/{id}")
def getPessoaId(id:int):
    return select().select_pessoa_id(id)

@router.get("/pessoaJuridica")
def getPessoaJuridica():
    return select().select_pessoaJuridica()

@router.get("/pessoaFisica")
def getPessoaFisica():
    return select().select_pessoaFisica()