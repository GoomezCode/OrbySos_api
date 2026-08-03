from pydantic import BaseModel
    
class tb_pessoa_juridica(BaseModel):
    id_pj:int
    razao_social:str
    nome_fantasia:str
    cnpj:str
    fk_status:int
    
class tb_pessoa_fisica(BaseModel):
    id_pf:int
    nome:str
    cpf:int
    fk_sexo:int
    data_nascimento:str
    cnh:int
    fk_estado_civil:int
    fk_Status:int

class tb_endereco(BaseModel):
    fk_pessoa:int
    logradouro:str
    bairro:str
    fk_tpLogradouro:int
    cep:int
    cidade:str
    estado:str
    pais:str
    complemento:str
    
class tb_user(BaseModel):
    fk_pessoa:int
    login:str
    senha:str
    fk_status:int
    
class tb_veiculo(BaseModel):
    fk_pessoa:int
    marca:str
    modelo:str
    versao:str
    ano_fabricacao:int
    ano_modelo:int
    placa:str
    chassi:str
    valor_fipe:str
    fk_tpUso:int
    blindado:bool
    
class tb_apolice(BaseModel):
    numero_apolice:int
    fk_pessoa:int
    fk_veiculo:int
    data_inicio:str
    data_fim:str
    cobertura:float
    assistencia:str
    endosso:str
    versao:int
    perfil:str
    fk_local_pernoite:int
    fk_status:int
    fk_forma_pagamento:int

class tb_ocorrencia(BaseModel):
    ocorrencia:str

class tb_assistencia(BaseModel):
    assistencia:str

class tb_apolice_ocorencia(BaseModel):
    fk_apolice:int
    fk_ocorrencia:int

class tb_status_ocorrencia(BaseModel):
    fk_apo_ocorrencia:int
    status:str

class tb_ocorrencia_assistencia(BaseModel):
    fk_apo_ocorrencia:int
    fk_assistencia:int
    fk_status:int
    comentario:str
