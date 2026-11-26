from io import BytesIO
from re import findall
from xml.etree.ElementTree import fromstring

import pytest
from PIL import Image
from src.motor.matriz import gerar_matriz
from src.renderizacao.geometria import calcular_geometria
from src.schemas.pedido import PedidoRenderizacao
from src.servicos.renderizacao import renderizar

NS = {"svg": "http://www.w3.org/2000/svg"}

GRADIENTE = {
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
}

ESTILOS = [
    {},
    {
        "modules": {
            "color": "#6D28D9",
        },
    },
    {
        "modules": {
            "shape": "rounded",
            "gradient": GRADIENTE,
        },
    },
    {
        "modules": {
            "shape": "dots",
            "gradient": GRADIENTE,
        },
        "background": {
            "transparent": True,
        },
    },
    {
        "modules": {
            "gradient": GRADIENTE,
        },
        "eyes": {
            "outer": {
                "shape": "rounded",
                "color": "#4C1D95",
            },
            "inner": {
                "shape": "dots",
                "color": "#172554",
            },
        },
    },
]


def criar_pedido(
    formato,
    estilo=None,
    tamanho=512,
    margem=4,
):
    return PedidoRenderizacao.model_validate(
        {
            "content": "ntizoconnect",
            "output": {
                "format": formato,
                "size": tamanho,
                "margin": margem,
            },
            "style": estilo or {},
        }
    )


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize("estilo", ESTILOS)
def test_determinismo(formato, estilo):
    pedido = criar_pedido(formato, estilo)

    primeira = renderizar(pedido)
    segunda = renderizar(pedido)

    assert primeira.dados == segunda.dados


@pytest.mark.parametrize("formato", ["png", "svg"])
def test_isolamento_entre_pedidos(formato):
    pedido = criar_pedido(formato)

    antes = renderizar(pedido)

    for estilo in ESTILOS[1:]:
        renderizar(criar_pedido(formato, estilo))

    depois = renderizar(pedido)

    assert antes.dados == depois.dados


@pytest.mark.parametrize("formato", ["png", "svg"])
def test_pedido_nao_modificado(formato):
    pedido = criar_pedido(
        formato,
        ESTILOS[-1],
    )

    antes = pedido.model_dump(mode="json")

    renderizar(pedido)

    assert antes == pedido.model_dump(mode="json")


@pytest.mark.parametrize("formato", ["png", "svg"])
def test_estilo_padrao_explicito(formato):
    implicito = criar_pedido(formato)

    explicito = criar_pedido(
        formato,
        {
            "modules": {
                "shape": "square",
                "color": "#000000",
            },
            "background": {
                "color": "#FFFFFF",
            },
        },
    )

    assert renderizar(implicito).dados == renderizar(explicito).dados


@pytest.mark.parametrize("formato", ["png", "svg"])
def test_heranca_olhos(formato):
    implicito = criar_pedido(
        formato,
        {
            "modules": {
                "gradient": GRADIENTE,
            },
        },
    )

    explicito = criar_pedido(
        formato,
        {
            "modules": {
                "gradient": GRADIENTE,
            },
            "eyes": {
                "outer": {"shape": "square"},
                "inner": {"shape": "square"},
            },
        },
    )

    assert renderizar(implicito).dados == renderizar(explicito).dados


@pytest.mark.parametrize(
    "tamanho",
    [256, 512, 1024],
)
@pytest.mark.parametrize("margem", [4, 8, 16])
def test_consistencia_matriz_png_svg(
    tamanho,
    margem,
):
    pedido_png = criar_pedido(
        "png",
        tamanho=tamanho,
        margem=margem,
    )

    pedido_svg = criar_pedido(
        "svg",
        tamanho=tamanho,
        margem=margem,
    )

    png = renderizar(pedido_png)
    svg = renderizar(pedido_svg)

    matriz = gerar_matriz(
        conteudo=pedido_png.content,
        correcao_erros=pedido_png.options.errorCorrection,
    )

    geometria = calcular_geometria(
        dimensao_matriz=matriz.dimensao,
        dimensao_imagem=tamanho,
        margem=margem,
    )

    escuros = set()

    with Image.open(BytesIO(png.dados)) as imagem:
        for linha, valores in enumerate(matriz.modulos):
            for coluna, valor in enumerate(valores):
                x0, y0, x1, y1 = geometria.caixa_modulo(
                    linha,
                    coluna,
                )

                centro = (
                    (x0 + x1) // 2,
                    (y0 + y1) // 2,
                )

                esperado = (0, 0, 0, 255) if valor else (255, 255, 255, 255)

                assert imagem.getpixel(centro) == esperado

                if valor:
                    escuros.add((linha, coluna))

        branco = (255, 255, 255, 255)

        inicio = geometria.origem_x
        fim = inicio + geometria.dimensao_qr

        regioes = [
            (0, 0, tamanho, inicio),
            (0, fim, tamanho, tamanho),
            (0, inicio, inicio, fim),
            (fim, inicio, tamanho, fim),
        ]

        for regiao in regioes:
            assert imagem.crop(regiao).getextrema() == tuple((canal, canal) for canal in branco)

    raiz = fromstring(svg.dados)

    caminho = raiz.find("svg:path", NS)

    assert caminho is not None

    dados = caminho.get("d", "")

    segmentos = findall(
        r"M(\d+) (\d+)h(\d+)v(\d+)h(-\d+)z",
        dados,
    )

    assert segmentos

    assert dados == "".join(f"M{x} {y}h{w}v{h}h{retorno}z" for x, y, w, h, retorno in segmentos)

    modulos_svg = set()

    for segmento in segmentos:
        x, y, largura, altura, retorno = map(
            int,
            segmento,
        )

        assert altura == geometria.escala
        assert retorno == -largura
        assert largura % geometria.escala == 0

        assert (x - geometria.origem_x) % geometria.escala == 0
        assert (y - geometria.origem_y) % geometria.escala == 0

        linha = (y - geometria.origem_y) // geometria.escala

        coluna = (x - geometria.origem_x) // geometria.escala

        quantidade = largura // geometria.escala

        for deslocamento in range(quantidade):
            modulos_svg.add((linha, coluna + deslocamento))

    assert modulos_svg == escuros
