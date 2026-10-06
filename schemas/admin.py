from pydantic import BaseModel, Field


class VersionRequest(BaseModel):
    version: int = Field(ge=1)


class ConfirmarRequest(VersionRequest):
    comentario: str | None = None


class RecusarRequest(VersionRequest):
    motivo_recusa: str = Field(min_length=1)


class OperacaoRequest(VersionRequest):
    comentario: str | None = None


class AssistenciaAddRequest(BaseModel):
    tipo_assistencia_id: int
    comentario: str | None = None
    request_version: int = Field(ge=1)


class AssistenciaStatusUpdateRequest(BaseModel):
    status: str = Field(min_length=1)
    comentario: str | None = None
    version: int = Field(ge=1)