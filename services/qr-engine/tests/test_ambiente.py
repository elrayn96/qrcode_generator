from io import BytesIO

import segno
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image


def test_fastapi():
    app = FastAPI()

    @app.get("/healthz")
    def health():
        return {"status": "ok"}

    with TestClient(app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_geracao_qr():
    qr = segno.make_qr("https://ntizoconnect.me")

    assert qr.matrix
    assert qr.version >= 1


def test_exportacao_png():
    qr = segno.make_qr("https://ntizoconnect.me")
    buffer = BytesIO()

    qr.save(buffer, kind="png", scale=10)
    buffer.seek(0)

    with Image.open(buffer) as imagem:
        assert imagem.format == "PNG"
        assert imagem.width > 0
        assert imagem.height > 0
        assert imagem.width == imagem.height
        imagem.verify()
