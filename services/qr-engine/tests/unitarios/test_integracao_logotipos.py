from base64 import b64encode
from io import BytesIO
from xml.etree.ElementTree import fromstring

import pytest
from PIL import Image
from src.core.excecoes import (
    ErroDadosInvalidos,
    ErroFormatoNaoSuportado,
)
from src.schemas.pedido import PedidoRenderizacao
from src.servicos.renderizacao import renderizar

NS = {"svg": "http://www.w3.org/2000/svg"}


def criar_logo(formato="PNG"):
    with (
        Image.new("RGB", (80, 40), "red") as imagem,
        BytesIO() as memoria,
    ):
        imagem.save(memoria, format=formato)

        dados = b64encode(
            memoria.getvalue(),
        ).decode("ascii")

    return {
        "mediaType": ("image/jpeg" if formato == "JPEG" else "image/png"),
        "base64": dados,
        "scale": 0.1,
        "padding": 1,
    }


def criar_pedido(
    formato="png",
    correcao="H",
    estilo=None,
    tamanho=512,
):
    return PedidoRenderizacao.model_validate(
        {
            "content": "ntizoconnect",
            "output": {
                "format": formato,
                "size": tamanho,
                "margin": 4,
            },
            "options": {
                "errorCorrection": correcao,
            },
            "style": estilo or {},
        },
    )


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize("formato_logo", ["PNG", "JPEG"])
def test_renderiza_pedido_com_logotipo(
    formato,
    formato_logo,
):
    pedido = criar_pedido(
        formato=formato,
        estilo={
            "logo": criar_logo(formato_logo),
        },
    )

    resultado = renderizar(pedido)

    assert resultado.largura == 512
    assert resultado.altura == 512

    if formato == "png":
        assert resultado.media_type == "image/png"

        with Image.open(BytesIO(resultado.dados)) as imagem:
            assert imagem.format == "PNG"

            r, g, b, a = imagem.getpixel((256, 256))

            assert r >= 250
            assert g <= 5
            assert b <= 5
            assert a == 255
    else:
        assert resultado.media_type == "image/svg+xml"

        raiz = fromstring(resultado.dados)

        logo = raiz.find("svg:image", NS)

        assert logo is not None

        assert logo.attrib["href"].startswith(
            "data:image/png;base64,",
        )


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize("correcao", ["L", "M", "Q"])
def test_exige_correcao_h(formato, correcao):
    pedido = criar_pedido(
        formato=formato,
        correcao=correcao,
        estilo={
            "logo": criar_logo(),
        },
    )

    with pytest.raises(ErroDadosInvalidos):
        renderizar(pedido)


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize("correcao", ["L", "M", "Q", "H"])
def test_sem_logotipo_aceita_correcao(
    formato,
    correcao,
):
    pedido = criar_pedido(
        formato=formato,
        correcao=correcao,
    )

    resultado = renderizar(pedido)

    assert resultado.dados


@pytest.mark.parametrize("formato", ["png", "svg"])
def test_rejeita_base64_invalido(formato):
    logo = criar_logo()
    logo["base64"] = "AB=="

    pedido = criar_pedido(
        formato=formato,
        estilo={"logo": logo},
    )

    with pytest.raises(ErroDadosInvalidos):
        renderizar(pedido)


@pytest.mark.parametrize("formato", ["png", "svg"])
def test_rejeita_formato_incompativel(formato):
    logo = criar_logo("PNG")
    logo["mediaType"] = "image/jpeg"

    pedido = criar_pedido(
        formato=formato,
        estilo={"logo": logo},
    )

    with pytest.raises(ErroFormatoNaoSuportado):
        renderizar(pedido)


@pytest.mark.parametrize("formato", ["png", "svg"])
def test_rejeita_colisao(formato):
    logo = criar_logo()
    logo["scale"] = 0.2
    logo["padding"] = 4

    pedido = criar_pedido(
        formato=formato,
        estilo={"logo": logo},
    )

    with pytest.raises(ErroDadosInvalidos):
        renderizar(pedido)


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize("tamanho", [256, 512, 1024, 2048])
def test_resolucoes(formato, tamanho):
    pedido = criar_pedido(
        formato=formato,
        tamanho=tamanho,
        estilo={
            "logo": criar_logo(),
        },
    )

    resultado = renderizar(pedido)

    assert resultado.largura == tamanho
    assert resultado.altura == tamanho


@pytest.mark.parametrize("formato", ["png", "svg"])
def test_personalizacao_completa(formato):
    pedido = criar_pedido(
        formato=formato,
        estilo={
            "modules": {
                "shape": "rounded",
                "gradient": {
                    "type": "linear",
                    "angle": 45,
                    "stops": [
                        {
                            "position": 0.0,
                            "color": "#6D28D9",
                        },
                        {
                            "position": 1.0,
                            "color": "#172554",
                        },
                    ],
                },
            },
            "eyes": {
                "outer": {
                    "shape": "rounded",
                    "color": "#172554",
                },
                "inner": {
                    "shape": "dots",
                    "color": "#6D28D9",
                },
            },
            "background": {
                "color": "#F5F3FF",
            },
            "logo": criar_logo(),
        },
    )

    resultado = renderizar(pedido)

    assert resultado.dados


@pytest.mark.parametrize("formato", ["png", "svg"])
def test_determinismo(formato):
    pedido = criar_pedido(
        formato=formato,
        estilo={
            "logo": criar_logo(),
        },
    )

    assert renderizar(pedido).dados == renderizar(pedido).dados
