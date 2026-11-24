from fastapi.testclient import TestClient
from src.main import criar_aplicacao


def test_endpoint_saude():
    app = criar_aplicacao()

    with TestClient(app) as client:
        resposta = client.get("/healthz")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "status": "ok",
        "service": "qr-engine",
    }


def test_motor_ainda_nao_preparado():
    app = criar_aplicacao()

    with TestClient(app) as client:
        resposta = client.get("/readyz")

    assert resposta.status_code == 503
    assert resposta.headers["content-type"] == "application/problem+json"
    assert resposta.headers["retry-after"] == "1"
    assert resposta.json()["code"] == "SERVICE_UNAVAILABLE"


def test_motor_preparado():
    app = criar_aplicacao()

    with TestClient(app) as client:
        app.state.pronto = True
        resposta = client.get("/readyz")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_encerramento_remove_prontidao():
    app = criar_aplicacao()

    with TestClient(app):
        app.state.pronto = True

    assert app.state.pronto is False


def test_documentacao_indisponivel_em_producao(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    app = criar_aplicacao()

    with TestClient(app) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        assert client.get("/openapi.json").status_code == 404


def test_documentacao_disponivel_em_desenvolvimento(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    app = criar_aplicacao()

    with TestClient(app) as client:
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200
