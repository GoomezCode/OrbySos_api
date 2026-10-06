from pydantic import BaseModel, Field


class ApoliceCreateRequest(BaseModel):
    numero_apolice: str = Field(min_length=1)
    fk_pessoa: int = Field(gt=0)
    fk_segurado: int = Field(gt=0)
    fk_veiculo: int = Field(gt=0)
    data_inicio: str = Field(min_length=1)
    data_fim: str = Field(min_length=1)
    cobertura: float = Field(gt=0)
    assistencia: str = Field(default="")
    endosso: str | None = None
    perfil: str = Field(default="")
    fk_local_pernoite: int = Field(gt=0)
    fk_forma_pagamento: int = Field(gt=0)


class ApoliceUpdateRequest(BaseModel):
    version: int = Field(ge=1)
    numero_apolice: str | None = Field(default=None, min_length=1)
    data_inicio: str | None = None
    data_fim: str | None = None
    cobertura: float | None = Field(default=None, gt=0)
    assistencia: str | None = None
    endosso: str | None = None
    perfil: str | None = None


class ApoliceStatusRequest(BaseModel):
    version: int = Field(ge=1)
    status: str = Field(min_length=1)
    comentario: str | None = None