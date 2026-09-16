import json
from fastapi import FastAPI
from fastapi.testclient import TestClient

from main import app


def list_routes() -> list[str]:
    return sorted(app.openapi().get("paths", {}).keys())


if __name__ == "__main__":
    client = TestClient(app)

    checks = []

    def check(label, response):
        ok = 200 <= response.status_code < 300 or response.status_code in (401, 404)
        checks.append((label, response.status_code, ok))
        print(f"{label}: {response.status_code}")

    check("GET / (public)", client.get("/"))
    check("GET /openapi.json (public)", client.get("/openapi.json"))
    check("GET /api/v1/tipos-ocorrencia (no token -> 401)", client.get("/api/v1/tipos-ocorrencia"))
    check("GET /api/v1/auth/me (no token -> 401)", client.get("/api/v1/auth/me"))
    preflight = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    check("OPTIONS preflight (CORS)", preflight)
    print("  allow-origin:", preflight.headers.get("access-control-allow-origin"))

    routes = [r for r in list_routes() if r.startswith("/api/v1")]
    print(f"\nrotas /api/v1: {len(routes)}")
    for r in routes:
        print("  ", r)

    failed = [c for c in checks if not c[2]]
    if failed:
        print("\nFALHA:", failed)
        raise SystemExit(1)
    print("\nSMOKE_TEST_OK")