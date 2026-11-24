from fastapi.testclient import TestClient
from pydantic import BaseModel
from src.core.excecoes import ErroDadosInvalidos
from src.main import criar_aplicacao


def test_recurso_inexistente():
    with TestClient(criar_aplicacao()) as client:
        resposta = client.get("/rota-inexistente")

    assert resposta.status_code == 404
    assert resposta.json()["code"] == "RESOURCE_NOT_FOUND"
    assert resposta.headers["content-type"] == "application/problem+json"


def test_excecao_nao_expoe_dados_sensiveis():
    app = criar_aplicacao()

    @app.get("/teste-erro")
    def provocar_erro():
        raise ErroDadosInvalidos("password-secreta-exemplo")

    with TestClient(app) as client:
        resposta = client.get("/teste-erro")

    assert resposta.status_code == 422
    assert "password-secreta-exemplo" not in resposta.text


def test_erro_interno_nao_expoe_detalhes_na_resposta():
    app = criar_aplicacao()

    @app.get("/teste-erro")
    def provocar_erro():
        raise RuntimeError("credencial-interna-secreta")

    with TestClient(app, raise_server_exceptions=False) as client:
        resposta = client.get("/teste-erro")

    assert resposta.status_code == 500
    assert resposta.json()["code"] == "INTERNAL_ERROR"
    assert "credencial-interna-secreta" not in resposta.text


def test_validacao_nao_expoe_conteudo_original():
    app = criar_aplicacao()

    class PedidoTeste(BaseModel):
        tamanho: int

    @app.post("/teste-validacao")
    def validar(pedido: PedidoTeste):
        return pedido

    with TestClient(app) as client:
        resposta = client.post(
            "/teste-validacao",
            json={"tamanho": "conteudo-secreto"},
        )

    assert resposta.status_code == 422
    assert "conteudo-secreto" not in resposta.text


def test_json_malformado():
    app = criar_aplicacao()

    class PedidoTeste(BaseModel):
        tamanho: int

    @app.post("/teste-validacao")
    def validar(pedido: PedidoTeste):
        return pedido

    with TestClient(app) as client:
        resposta = client.post(
            "/teste-validacao",
            content="{invalido",
            headers={"Content-Type": "application/json"},
        )

    assert resposta.status_code == 400
    assert resposta.json()["code"] == "INVALID_REQUEST"


def test_identificador_consistente():
    with TestClient(criar_aplicacao()) as client:
        resposta = client.get("/rota-inexistente")

    assert resposta.json()["requestId"] == resposta.headers["X-Request-ID"]
    assert resposta.headers["Cache-Control"] == "no-store"
