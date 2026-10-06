from fastapi import HTTPException, status

from core.config import get_settings
from core.security import verify_password, create_access_token
from schemas.auth import (
    AuthEnvelope,
    SessaoInfo,
    SeguradoraResumo,
)
import repositories.user_repository as user_repo


def normalize_cpf(cpf: str) -> str:
    return "".join(ch for ch in cpf if ch.isdigit())


def _build_session_user(row: dict) -> SessaoInfo:
    return SessaoInfo(
        id_usuario=row["id_user"],
        id_pessoa=row["fk_pessoa"],
        perfil=row["perfil"],
        nome_exibicao=row.get("nome_exibicao") or row.get("nome"),
        seguradora=None,
        seguradoras=[],
    )


def _build_session_analyst(row: dict, insurers: list[dict]) -> SessaoInfo:
    seguradoras = [SeguradoraResumo(**r) for r in insurers]

    seguradora = None
    fk_seg = row.get("fk_seguradora")
    if fk_seg is not None:
        seguradora = next((s for s in seguradoras if s.id_pj == fk_seg), None)
    if seguradora is None and seguradoras:
        seguradora = seguradoras[0]

    return SessaoInfo(
        id_usuario=row["id_user"],
        id_pessoa=row["fk_pessoa"],
        perfil=row["perfil"],
        nome_exibicao=row.get("nome_exibicao"),
        seguradora=seguradora,
        seguradoras=seguradoras,
    )


def _make_envelope(session: SessaoInfo) -> AuthEnvelope:
    settings = get_settings()
    token = create_access_token(
        subject=session.id_usuario,
        extra={
            "id_usuario": session.id_usuario,
            "id_pessoa": session.id_pessoa,
            "perfil": session.perfil,
            "nome_exibicao": session.nome_exibicao,
            "seguradora": session.seguradora.model_dump() if session.seguradora else None,
            "seguradoras": [s.model_dump() for s in session.seguradoras],
        },
    )
    return AuthEnvelope(
        access_token=token,
        expires_in=settings.jwt_expire_seconds,
        session=session,
    )


_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail={"code": "AUTH_INVALID_CREDENTIALS", "message": "Credenciais inválidas."},
)
_INACTIVE_ERROR = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail={"code": "AUTH_INACTIVE_USER", "message": "Usuário inativo."},
)


def login_client(cpf: str, password: str) -> AuthEnvelope:
    normalized = normalize_cpf(cpf)

    try:
        from validate_docbr import CPF
        if not CPF().validate(normalized):
            raise _CREDENTIALS_ERROR
    except HTTPException:
        raise
    except Exception:
        pass

    row = user_repo.find_client_by_cpf(normalized)
    if not row or row["perfil"] != "CLIENTE":
        raise _CREDENTIALS_ERROR
    if row["status_codigo"] != "ATIVO":
        raise _INACTIVE_ERROR
    if not verify_password(password, row["senha"]):
        raise _CREDENTIALS_ERROR

    session = _build_session_user(row)
    return _make_envelope(session)


def login_analyst(login_str: str, password: str) -> AuthEnvelope:
    login_str = login_str.strip().lower()

    row = user_repo.find_analyst_by_login(login_str)
    if not row or row["perfil"] != "ANALISTA":
        raise _CREDENTIALS_ERROR
    if row["status_codigo"] != "ATIVO":
        raise _INACTIVE_ERROR
    if not verify_password(password, row["senha"]):
        raise _CREDENTIALS_ERROR

    insurers = user_repo.find_analyst_insurers(row["id_user"])
    session = _build_session_analyst(row, insurers)
    return _make_envelope(session)
