import re
from xml.etree.ElementTree import fromstring

import pytest
from src.core.excecoes import ErroDimensaoQR
from src.motor.matriz import gerar_matriz
from src.renderizacao.cores import (
    PRETO,
    TRANSPARENTE,
    converter_cor,
)
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.modulos import iterar_modulos_escuros
from src.renderizacao.olhos import EstiloOlhos
from src.renderizacao.svg import (
    SVG_NS,
    renderizar_svg,
)


def test_documento_svg_valido():
    resultado = renderizar_svg(gerar_matriz("ntizoconnect"))

    raiz = fromstring(resultado.dados)

    assert raiz.tag == f"{{{SVG_NS}}}svg"
    assert resultado.media_type == "image/svg+xml"


@pytest.mark.parametrize("tamanho", [128, 512, 1024, 2048])
def test_dimensao_svg(tamanho):
    resultado = renderizar_svg(
        gerar_matriz("ntizoconnect"),
        tamanho=tamanho,
    )

    raiz = fromstring(resultado.dados)

    assert raiz.attrib["width"] == str(tamanho)
    assert raiz.attrib["height"] == str(tamanho)

    assert raiz.attrib["viewBox"] == (f"0 0 {tamanho} {tamanho}")


def test_cor_modulos_svg():
    resultado = renderizar_svg(
        gerar_matriz("ntizoconnect"),
        cor_modulos=converter_cor("#7C3AED"),
    )

    raiz = fromstring(resultado.dados)
    caminho = raiz.find(f"{{{SVG_NS}}}path")

    assert caminho is not None
    assert caminho.attrib["fill"] == "#7C3AED"


def test_fundo_transparente_svg():
    resultado = renderizar_svg(
        gerar_matriz("ntizoconnect"),
        cor_fundo=TRANSPARENTE,
    )

    raiz = fromstring(resultado.dados)

    assert raiz.find(f"{{{SVG_NS}}}rect") is None


def test_opacidade_fundo_svg():
    resultado = renderizar_svg(
        gerar_matriz("ntizoconnect"),
        cor_fundo=converter_cor("#FFFFFF80"),
    )

    raiz = fromstring(resultado.dados)
    fundo = raiz.find(f"{{{SVG_NS}}}rect")

    assert fundo is not None

    assert float(fundo.attrib["fill-opacity"]) == pytest.approx(128 / 255)


def test_apenas_elementos_permitidos():
    matriz = gerar_matriz("<script>alert('ntizoconnect')</script>")

    resultado = renderizar_svg(matriz)
    raiz = fromstring(resultado.dados)

    permitidos = {"svg", "rect", "path"}

    assert all(elemento.tag.split("}")[-1] in permitidos for elemento in raiz.iter())

    assert b"<script>" not in resultado.dados
    assert b"alert(" not in resultado.dados


def test_correspondencia_matriz_svg():
    matriz = gerar_matriz("ntizoconnect")

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
    matriz = gerar_matriz("ntizoconnect")

    assert renderizar_svg(matriz).dados == renderizar_svg(matriz).dados


@pytest.mark.parametrize(
    "forma",
    ["square", "rounded", "dots"],
)
def test_renderizar_formas_svg(forma):
    resultado = renderizar_svg(
        gerar_matriz("ntizoconnect"),
        forma=forma,
    )

    raiz = fromstring(resultado.dados)

    assert raiz.tag == f"{{{SVG_NS}}}svg"


def test_modulos_arredondados_svg():
    resultado = renderizar_svg(
        gerar_matriz("ntizoconnect"),
        forma="rounded",
    )

    raiz = fromstring(resultado.dados)

    grupo = raiz.find(f"{{{SVG_NS}}}g")

    assert grupo is not None

    modulos = grupo.findall(f"{{{SVG_NS}}}rect")

    assert modulos

    assert all(float(modulo.attrib["rx"]) > 0 for modulo in modulos)


def test_modulos_circulares_svg():
    resultado = renderizar_svg(
        gerar_matriz("ntizoconnect"),
        forma="dots",
    )

    raiz = fromstring(resultado.dados)

    circulos = raiz.findall(f".//{{{SVG_NS}}}circle")

    assert circulos

    assert all(float(circulo.attrib["r"]) > 0 for circulo in circulos)


@pytest.mark.parametrize(
    "forma",
    ["rounded", "dots"],
)
def test_padroes_funcionais_svg(forma):
    matriz = gerar_matriz("ntizoconnect")

    resultado = renderizar_svg(
        matriz,
        forma=forma,
    )

    raiz = fromstring(resultado.dados)
    caminho = raiz.find(f"{{{SVG_NS}}}path")

    assert caminho is not None

    assert caminho.attrib["shape-rendering"] == "crispEdges"

    assert caminho.attrib["d"]


@pytest.mark.parametrize(
    ("forma", "elemento"),
    [
        ("rounded", "rect"),
        ("dots", "circle"),
    ],
)
def test_quantidade_modulos_personalizados_svg(
    forma,
    elemento,
):
    matriz = gerar_matriz("ntizoconnect")

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    quantidade = sum(
        not modulo.funcional
        for modulo in iterar_modulos_escuros(
            matriz,
            geometria,
            forma,
        )
    )

    resultado = renderizar_svg(
        matriz,
        forma=forma,
    )

    raiz = fromstring(resultado.dados)
    grupo = raiz.find(f"{{{SVG_NS}}}g")

    assert grupo is not None

    elementos = grupo.findall(f"{{{SVG_NS}}}{elemento}")

    assert len(elementos) == quantidade


@pytest.mark.parametrize(
    "forma",
    ["rounded", "dots"],
)
def test_escala_insuficiente_svg(forma):
    matriz = gerar_matriz("ntizoconnect")

    with pytest.raises(ErroDimensaoQR):
        renderizar_svg(
            matriz,
            tamanho=128,
            margem=32,
            forma=forma,
        )


@pytest.mark.parametrize(
    "forma",
    ["square", "rounded", "dots"],
)
def test_seguranca_svg_personalizado(forma):
    resultado = renderizar_svg(
        gerar_matriz("<script>alert(1)</script>"),
        forma=forma,
    )

    raiz = fromstring(resultado.dados)

    permitidos = {
        "svg",
        "rect",
        "path",
        "g",
        "circle",
    }

    for elemento in raiz.iter():
        nome = elemento.tag.split("}")[-1]

        assert nome in permitidos

        assert all(not atributo.lower().startswith("on") for atributo in elemento.attrib)

    assert b"<script>" not in resultado.dados


@pytest.mark.parametrize("exterior", ["square", "rounded", "dots"])
@pytest.mark.parametrize("interior", ["square", "rounded", "dots"])
def test_formas_olhos_svg(exterior, interior):
    resultado = renderizar_svg(
        gerar_matriz("ntizoconnect"),
        olhos=EstiloOlhos(
            forma_exterior=exterior,
            forma_interior=interior,
            cor_exterior=PRETO,
            cor_interior=PRETO,
        ),
    )

    raiz = fromstring(resultado.dados)

    grupo = raiz.find(f"{{{SVG_NS}}}g[@id='qr-eyes']")

    assert grupo is not None
    assert len(grupo) == 6


def test_cores_independentes_olhos_svg():
    resultado = renderizar_svg(
        gerar_matriz("ntizoconnect"),
        olhos=EstiloOlhos(
            forma_exterior="rounded",
            forma_interior="dots",
            cor_exterior=converter_cor("#4C1D95"),
            cor_interior=converter_cor("#7C3AED"),
        ),
    )

    raiz = fromstring(resultado.dados)

    grupo = raiz.find(f"{{{SVG_NS}}}g[@id='qr-eyes']")

    assert grupo is not None

    elementos = list(grupo)

    for indice in (0, 2, 4):
        assert elementos[indice].attrib["fill"] == "#4C1D95"

        assert elementos[indice].attrib["fill-rule"] == "evenodd"

        assert elementos[indice + 1].attrib["fill"] == "#7C3AED"


def test_olhos_transparentes_svg():
    resultado = renderizar_svg(
        gerar_matriz("ntizoconnect"),
        cor_fundo=TRANSPARENTE,
        olhos=EstiloOlhos(
            forma_exterior="rounded",
            forma_interior="square",
            cor_exterior=PRETO,
            cor_interior=PRETO,
        ),
    )

    raiz = fromstring(resultado.dados)

    assert raiz.find(f"{{{SVG_NS}}}rect") is None

    grupo = raiz.find(f"{{{SVG_NS}}}g[@id='qr-eyes']")

    assert grupo is not None

    assert sum(elemento.attrib.get("fill-rule") == "evenodd" for elemento in grupo) == 3


def test_caminhos_olhos_svg_deterministicos():
    matriz = gerar_matriz("ntizoconnect")

    estilo = EstiloOlhos(
        forma_exterior="rounded",
        forma_interior="dots",
        cor_exterior=PRETO,
        cor_interior=PRETO,
    )

    assert renderizar_svg(matriz, olhos=estilo).dados == renderizar_svg(matriz, olhos=estilo).dados
