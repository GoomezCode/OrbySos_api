from fastapi import APIRouter
from classes.classPessoa import *
from database.select import select

router = APIRouter(
    prefix="/get",
    tags=["get"]
)

@router.get("/all/{table}")
def getAll(table:str):
    print(select().select_all(table))
    return select().select_all(table)

@router.get("/filter/tbPessoaId/{id}")
def getPessoaId(id:int):
    return select().select_pessoa_id(id)