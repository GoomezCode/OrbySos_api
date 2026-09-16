from pydantic import BaseModel, Field


class ClienteLoginRequest(BaseModel):
    cpf: str = Field(..., min_length=11, max_length=14)
    senha: str = Field(..., min_length=4, max_length=100)


class AnalistaLoginRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=100)
    senha: str = Field(..., min_length=4, max_length=100)


class SeguradoraResumo(BaseModel):
    id_pj: int
    nome_fantasia: str


class SessaoInfo(BaseModel):
    id_usuario: int
    id_pessoa: int
    perfil: str
    nome_exibicao: str | None = None
    seguradora: SeguradoraResumo | None = None
    seguradoras: list[SeguradoraResumo] = []


class AuthEnvelope(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    session: SessaoInfo