from fastapi import APIRouter, HTTPException
from database.select import select_admin
from classes.classPessoa import *

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.get("/me")
def me():
    return "hello"