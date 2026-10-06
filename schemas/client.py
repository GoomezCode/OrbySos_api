from pydantic import BaseModel, Field


class LocalInput(BaseModel):
    endereco: str = Field(min_length=1)
    numero_local: str = Field(min_length=1)
    cidade: str = Field(min_length=1)
    estado: str = Field(min_length=2, max_length=2)
    ponto_referencia: str | None = None


class SolicitacaoCreateRequest(BaseModel):
    id_solicitacao_cliente: str = Field(min_length=1)
    apolice_id: int
    tipo_ocorrencia_id: int
    descricao_evento: str = Field(min_length=1)
    possui_feridos: bool
    risco_imediato: bool
    local: LocalInput
    data_criacao_cliente: str = Field(min_length=1)


class PerguntaRespostaRequest(BaseModel):
    necessita_taxi: bool
    quantidade_passageiros: int | None = None
    necessita_acessibilidade: bool | None = None
    quantidade_criancas: int | None = None
    quantidade_animais: int | None = None
    bagagem: str | None = None
    observacoes: str | None = None
    version: int = Field(default=1, ge=1)