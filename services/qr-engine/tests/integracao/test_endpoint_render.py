import pytest
from fastapi.testclient import TestClient
from src.api.rotas import LIMITE_CORPO
from src.main import criar_aplicacao

ROTA = "/internal/v1/render"


@pytest.mark.parametrize("formato,tipo", [("png", "image/png"), ("svg", "image/svg+xml")])
def test_render(formato, tipo):
    with TestClient(criar_aplicacao()) as client:
        r = client.post(ROTA, json={"content": "ntizoconnect", "output": {"format": formato}})
    assert r.status_code == 200
    assert r.headers["content-type"] == tipo
    assert r.headers["cache-control"] == "no-store"
    assert r.headers["x-request-id"].startswith("req_")
    assert r.content.startswith(b"\x89PNG" if formato == "png" else b"<?xml")


@pytest.mark.parametrize(
    "corpo,tipo,status",
    [
        (b"{", "application/json", 400),
        (b"{}", "application/json", 422),
        (b"{}", "text/plain", 415),
        (b"\xff", "application/json", 400),
        (b" " * (LIMITE_CORPO + 1), "application/json", 413),
    ],
)
def test_erros(corpo, tipo, status):
    with TestClient(criar_aplicacao()) as client:
        r = client.post(ROTA, content=corpo, headers={"Content-Type": tipo})
    assert r.status_code == status
    assert r.headers["content-type"] == "application/problem+json"
    assert r.json()["requestId"] == r.headers["x-request-id"]


def test_indisponivel():
    with TestClient(criar_aplicacao()) as client:
        client.app.state.pronto = False
        r = client.post(ROTA, json={"content": "abc"})
    assert r.status_code == 503
