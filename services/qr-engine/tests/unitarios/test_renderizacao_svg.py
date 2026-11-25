import re
from xml.etree.ElementTree import fromstring

import pytest
from src.motor.matriz import gerar_matriz
from src.renderizacao.cores import (
    TRANSPARENTE,
    converter_cor,
)
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.svg import (
    SVG_NS,
    renderizar_svg,
)


def test_documento_svg_valido():
    resultado = renderizar_svg(gerar_matriz("example"))

    raiz = fromstring(resultado.dados)

    assert raiz.tag == f"{{{SVG_NS}}}svg"
    assert resultado.media_type == "image/svg+xml"


@pytest.mark.parametrize("tamanho", [128, 512, 1024, 2048])
def test_dimensao_svg(tamanho):
    resultado = renderizar_svg(
        gerar_matriz("example"),
        tamanho=tamanho,
    )

    raiz = fromstring(resultado.dados)

    assert raiz.attrib["width"] == str(tamanho)
    assert raiz.attrib["height"] == str(tamanho)

    assert raiz.attrib["viewBox"] == (f"0 0 {tamanho} {tamanho}")


def test_cor_modulos_svg():
    resultado = renderizar_svg(
        gerar_matriz("example"),
        cor_modulos=converter_cor("#7C3AED"),
    )

    raiz = fromstring(resultado.dados)
    caminho = raiz.find(f"{{{SVG_NS}}}path")

    assert caminho is not None
    assert caminho.attrib["fill"] == "#7C3AED"


def test_fundo_transparente_svg():
    resultado = renderizar_svg(
        gerar_matriz("example"),
        cor_fundo=TRANSPARENTE,
    )

    raiz = fromstring(resultado.dados)

    assert raiz.find(f"{{{SVG_NS}}}rect") is None


def test_opacidade_fundo_svg():
    resultado = renderizar_svg(
        gerar_matriz("example"),
        cor_fundo=converter_cor("#FFFFFF80"),
    )

    raiz = fromstring(resultado.dados)
    fundo = raiz.find(f"{{{SVG_NS}}}rect")

    assert fundo is not None

    assert float(fundo.attrib["fill-opacity"]) == pytest.approx(128 / 255)


def test_apenas_elementos_permitidos():
    matriz = gerar_matriz("<script>alert('example')</script>")

    resultado = renderizar_svg(matriz)
    raiz = fromstring(resultado.dados)

    permitidos = {"svg", "rect", "path"}

    assert all(elemento.tag.split("}")[-1] in permitidos for elemento in raiz.iter())

    assert b"<script>" not in resultado.dados
    assert b"alert(" not in resultado.dados


def test_correspondencia_matriz_svg():
    matriz = gerar_matriz("example")

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    resultado = renderizar_svg(matriz)

    raiz = fromstring(resultado.dados)
    caminho = raiz.find(f"{{{SVG_NS}}}path")

    assert caminho is not None

    segmentos = re.findall(
        r"M(\d+) (\d+)h(\d+)v(\d+)h(-\d+)z",
        caminho.attrib["d"],
    )

    reconstruida = [[0] * matriz.dimensao for _ in range(matriz.dimensao)]

    for x, y, largura, altura, retorno in segmentos:
        x = int(x)
        y = int(y)
        largura = int(largura)

        assert int(altura) == geometria.escala
        assert int(retorno) == -largura

        linha = (y - geometria.origem_y) // geometria.escala

        coluna = (x - geometria.origem_x) // geometria.escala

        quantidade = largura // geometria.escala

        for indice in range(coluna, coluna + quantidade):
            reconstruida[linha][indice] = 1

    assert tuple(tuple(linha) for linha in reconstruida) == matriz.modulos


def test_svg_deterministico():
    matriz = gerar_matriz("example")

    assert renderizar_svg(matriz).dados == renderizar_svg(matriz).dados
