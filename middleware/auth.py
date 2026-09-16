from fastapi import Request

from core.errors import make_error_response
from core.security import decode_access_token

PUBLIC_EXACT = frozenset({
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
})

PUBLIC_PREFIXES = (
    "/api/v1/auth/clientes/login",
    "/api/v1/auth/analistas/login",
    "/api/v1/sync/version",
    "/api/v1/sync/events",
)


def is_public_path(path: str) -> bool:
    if path in PUBLIC_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


async def auth_middleware(request: Request, call_next):
    path = request.url.path

    if is_public_path(path) or request.method == "OPTIONS":
        return await call_next(request)

    authorization = request.headers.get("Authorization", "")
    if not authorization.lower().startswith("bearer "):
        return make_error_response(401, "UNAUTHORIZED", "Token de autenticação não informado.")

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    if not payload:
        return make_error_response(401, "INVALID_TOKEN", "Token inválido ou expirado.")

    request.state.session = {
        "id_usuario": payload.get("id_usuario") or int(payload.get("sub")),
        "id_pessoa": payload.get("id_pessoa"),
        "perfil": payload.get("perfil"),
        "nome_exibicao": payload.get("nome_exibicao"),
        "seguradora": payload.get("seguradora"),
        "seguradoras": payload.get("seguradoras") or [],
    }
    return await call_next(request)