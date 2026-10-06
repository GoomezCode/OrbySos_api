import json
from unittest import mock

import services.catalog_service as catalog_service
import repositories.catalog_repository as catalog_repo

OCCURRENCE_ROWS = [
    {"id_ocorrencia": 1, "codigo": "PANE_MECANICA", "nome": "Pane mecânica", "descricao": "Falha mecânica.", "ativo": 1},
    {"id_ocorrencia": 2, "codigo": "ACIDENTE", "nome": "Acidente", "descricao": "Colisão.", "ativo": 1},
    {"id_ocorrencia": 3, "codigo": "OUTRO", "nome": "Outro", "descricao": "Outra ocorrência.", "ativo": 0},
]

CONFIG_ROW = {
    "pais": "BR",
    "mensagem": "Orbyt Assistência 24h. Em caso de emergência ligue 0800 000 0000.",
    "servicos_json": json.dumps([
        {"codigo": "SAMU", "nome": "SAMU", "telefone": "192"},
        {"codigo": "BOMBEIROS", "nome": "Corpo de Bombeiros", "telefone": "193"},
        {"codigo": "POLICIA", "nome": "Polícia Militar", "telefone": "190"},
    ]),
}


def test_list_occurrence_types_all():
    with mock.patch.object(catalog_repo, "find_occurrences", return_value=OCCURRENCE_ROWS) as mk:
        payload = catalog_service.list_occurrence_types(None)
    assert mk.call_args == mock.call(None)
    items = payload["items"]
    assert len(items) == 3
    assert items[0]["id_tipo_ocorrencia"] == 1
    assert items[0]["codigo"] == "PANE_MECANICA"
    assert items[0]["ativo"] is True
    assert items[0]["ordem"] == 1
    assert items[1]["ordem"] == 2
    assert items[2]["ativo"] is False


def test_list_occurrence_types_active_only():
    with mock.patch.object(catalog_repo, "find_occurrences", return_value=[OCCURRENCE_ROWS[0]]) as mk:
        payload = catalog_service.list_occurrence_types(True)
    assert mk.call_args == mock.call(True)
    assert [i["id_tipo_ocorrencia"] for i in payload["items"]] == [1]


def test_list_occurrence_types_repository_error():
    class Boom(Exception):
        pass

    with mock.patch.object(catalog_repo, "find_occurrences", side_effect=Boom()):
        try:
            catalog_service.list_occurrence_types(None)
            assert False, "deveria ter levantado 500"
        except Exception as exc:
            assert exc.status_code == 500


def test_get_public_configurations_success():
    with mock.patch.object(catalog_repo, "get_app_configuration", return_value=CONFIG_ROW):
        payload = catalog_service.get_public_configurations()
    assert payload["pais"] == "BR"
    assert "0800" in payload["mensagem"]
    assert payload["servicos"][0] == {"codigo": "SAMU", "nome": "SAMU", "telefone": "192"}
    assert [s["codigo"] for s in payload["servicos"]] == ["SAMU", "BOMBEIROS", "POLICIA"]


def test_get_public_configurations_missing_row():
    with mock.patch.object(catalog_repo, "get_app_configuration", return_value=None):
        try:
            catalog_service.get_public_configurations()
            assert False, "deveria ter levantado 500"
        except Exception as exc:
            assert exc.status_code == 500


def test_get_public_configurations_invalid_json():
    with mock.patch.object(catalog_repo, "get_app_configuration", return_value={"pais": "BR", "mensagem": "x", "servicos_json": "not-json"}):
        try:
            catalog_service.get_public_configurations()
            assert False, "deveria ter levantado 500"
        except Exception as exc:
            assert exc.status_code == 500


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = []
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except AssertionError as exc:
            failed.append(test.__name__)
            print(f"FAIL  {test.__name__}: {exc}")
        except Exception as exc:
            failed.append(test.__name__)
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
    if failed:
        raise SystemExit(f"Falhou: {failed}")
    print(f"\nCATALOG_SERVICE_TESTS_OK ({len(tests)} testes)")