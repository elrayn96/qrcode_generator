from io import BytesIO
from xml.etree.ElementTree import fromstring

import pytest
from PIL import Image
from src.core.excecoes import ErroDimensaoQR
from src.schemas.pedido import PedidoRenderizacao
from src.servicos.renderizacao import renderizar

NS = {"svg": "http://www.w3.org/2000/svg"}

CONTEUDOS = [
    "ntizoconnect",
    "https://ntizoconnect.me",
    "Olá, Moçambique!",
    "WIFI:T:WPA;S:GQR-Test;P:teste12345;;",
    "mailto:teste@example.com",
    "tel:+258840000000",
    "SMSTO:+258840000000:ntizoconnect",
    "geo:-25.9655,32.5832",
    ("BEGIN:VCARD\nVERSION:3.0\nFN:GQR Test\nTEL:+258840000000\nEND:VCARD"),
]


def criar_gradiente(tipo="linear"):
    return {
        "type": tipo,
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
    }


def criar_pedido(
    formato="png",
    conteudo="ntizoconnect",
    tamanho=512,
    margem=4,
    correcao="M",
    estilo=None,
):
    return PedidoRenderizacao.model_validate(
        {
            "content": conteudo,
            "output": {
                "format": formato,
                "size": tamanho,
                "margin": margem,
            },
            "options": {
                "errorCorrection": correcao,
            },
            "style": estilo or {},
        }
    )


def validar_resultado(resultado, formato, tamanho):
    assert resultado.extensao == formato
    assert resultado.largura == tamanho
    assert resultado.altura == tamanho

    assert resultado.tamanho_bytes == len(resultado.dados)

    if formato == "png":
        assert resultado.media_type == "image/png"

        with Image.open(BytesIO(resultado.dados)) as imagem:
            assert imagem.format == "PNG"
            assert imagem.size == (tamanho, tamanho)
            assert imagem.mode == "RGBA"

            imagem.verify()

    else:
        assert resultado.media_type == "image/svg+xml"

        raiz = fromstring(resultado.dados)

        assert raiz.tag == f"{{{NS['svg']}}}svg"
        assert raiz.get("width") == str(tamanho)
        assert raiz.get("height") == str(tamanho)

        assert raiz.get("viewBox") == (f"0 0 {tamanho} {tamanho}")


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize("conteudo", CONTEUDOS)
def test_renderizacao_conteudos(formato, conteudo):
    pedido = criar_pedido(
        formato=formato,
        conteudo=conteudo,
    )

    validar_resultado(
        renderizar(pedido),
        formato,
        512,
    )


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize("correcao", ["L", "M", "Q", "H"])
@pytest.mark.parametrize("forma", ["square", "rounded", "dots"])
def test_formas_e_correcao(formato, correcao, forma):
    pedido = criar_pedido(
        formato=formato,
        correcao=correcao,
        estilo={
            "modules": {
                "shape": forma,
                "gradient": criar_gradiente(),
            },
        },
    )

    validar_resultado(
        renderizar(pedido),
        formato,
        512,
    )


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize(
    "tamanho",
    [128, 256, 512, 1024, 2048],
)
def test_resolucoes(formato, tamanho):
    pedido = criar_pedido(
        formato=formato,
        tamanho=tamanho,
    )

    validar_resultado(
        renderizar(pedido),
        formato,
        tamanho,
    )


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize("margem", [4, 8, 16, 32])
def test_margens(formato, margem):
    pedido = criar_pedido(
        formato=formato,
        margem=margem,
    )

    validar_resultado(
        renderizar(pedido),
        formato,
        512,
    )


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize("forma", ["rounded", "dots"])
def test_escala_insuficiente(formato, forma):
    pedido = criar_pedido(
        formato=formato,
        tamanho=128,
        margem=32,
        estilo={
            "modules": {
                "shape": forma,
            },
        },
    )

    with pytest.raises(ErroDimensaoQR):
        renderizar(pedido)


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize("tipo", ["linear", "radial"])
def test_personalizacao_completa(formato, tipo):
    pedido = criar_pedido(
        formato=formato,
        tamanho=768,
        margem=6,
        correcao="H",
        estilo={
            "modules": {
                "shape": "rounded",
                "gradient": criar_gradiente(tipo),
            },
            "eyes": {
                "outer": {
                    "shape": "rounded",
                    "gradient": criar_gradiente("linear"),
                },
                "inner": {
                    "shape": "dots",
                    "gradient": criar_gradiente("radial"),
                },
            },
            "background": {
                "gradient": {
                    "type": "radial",
                    "stops": [
                        {
                            "position": 0.0,
                            "color": "#FFFFFF",
                        },
                        {
                            "position": 1.0,
                            "color": "#E0E7FF",
                        },
                    ],
                },
            },
        },
    )

    resultado = renderizar(pedido)

    validar_resultado(resultado, formato, 768)

    if formato == "svg":
        raiz = fromstring(resultado.dados)

        assert len(raiz.findall("svg:defs/*", NS)) == 8

        olhos = raiz.find(
            "svg:g[@id='qr-eyes']",
            NS,
        )

        assert olhos is not None
        assert len(olhos) == 6


@pytest.mark.parametrize("formato", ["png", "svg"])
def test_gradiente_oito_pontos(formato):
    cores = [
        "#172554",
        "#1E3A8A",
        "#1D4ED8",
        "#4338CA",
        "#5B21B6",
        "#6D28D9",
        "#7E22CE",
        "#581C87",
    ]

    pedido = criar_pedido(
        formato=formato,
        estilo={
            "modules": {
                "gradient": {
                    "type": "linear",
                    "angle": 90,
                    "stops": [
                        {
                            "position": i / 7,
                            "color": cor,
                        }
                        for i, cor in enumerate(cores)
                    ],
                },
            },
        },
    )

    resultado = renderizar(pedido)

    validar_resultado(resultado, formato, 512)

    if formato == "svg":
        raiz = fromstring(resultado.dados)

        assert (
            len(
                raiz.findall(
                    ".//svg:linearGradient/svg:stop",
                    NS,
                )
            )
            == 8
        )
