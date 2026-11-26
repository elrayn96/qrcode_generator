import re
from xml.etree.ElementTree import fromstring

import pytest
from src.motor.matriz import gerar_matriz
from src.renderizacao.estilos import resolver_estilo
from src.renderizacao.svg import SVG_NS, renderizar_svg
from src.schemas.pedido import PedidoRenderizacao

NS = {"svg": SVG_NS}


def criar_gradiente(
    tipo="linear",
    primeira="#6D28D9",
    ultima="#172554",
):
    return {
        "type": tipo,
        "stops": [
            {"position": 0.0, "color": primeira},
            {"position": 1.0, "color": ultima},
        ],
    }


def criar_svg(**personalizacao):
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "ntizoconnect",
            "output": {"format": "svg"},
            "style": personalizacao,
        }
    )

    resultado = renderizar_svg(
        gerar_matriz(pedido.content),
        estilo=resolver_estilo(pedido),
    )

    return fromstring(resultado.dados)


def obter_gradientes(raiz):
    defs = raiz.find("svg:defs", NS)

    return [] if defs is None else list(defs)


def test_svg_solido_sem_definicoes():
    raiz = criar_svg()

    assert raiz.find("svg:defs", NS) is None
    assert raiz.find("svg:path", NS).get("fill") == "#000000"


@pytest.mark.parametrize(
    ("tipo", "elemento"),
    [
        ("linear", "linearGradient"),
        ("radial", "radialGradient"),
    ],
)
@pytest.mark.parametrize(
    "forma",
    ["square", "rounded", "dots"],
)
def test_gradientes_dos_modulos(
    tipo,
    elemento,
    forma,
):
    raiz = criar_svg(
        modules={
            "shape": forma,
            "gradient": criar_gradiente(tipo),
        },
    )

    gradientes = obter_gradientes(raiz)

    assert len(gradientes) == 1

    gradiente = gradientes[0]

    assert gradiente.tag == f"{{{SVG_NS}}}{elemento}"

    assert gradiente.get("gradientUnits") == "userSpaceOnUse"

    identificador = gradiente.get("id")

    caminho = raiz.find("svg:path", NS)

    assert caminho.get("fill") == f"url(#{identificador})"

    if forma != "square":
        grupo = raiz.find("svg:g", NS)

        assert grupo is not None

        assert grupo.get("fill") == f"url(#{identificador})"


def test_olhos_quadrados_herdados():
    gradiente = criar_gradiente()

    convencional = criar_svg(
        modules={"gradient": gradiente},
    )

    personalizado = criar_svg(
        modules={"gradient": gradiente},
        eyes={
            "outer": {"shape": "square"},
            "inner": {"shape": "square"},
        },
    )

    primeiro = convencional.find("svg:path", NS)
    segundo = personalizado.find("svg:path", NS)

    assert primeiro.attrib == segundo.attrib

    assert personalizado.find("svg:g[@id='qr-eyes']", NS) is None

    assert len(obter_gradientes(personalizado)) == 1


def test_gradiente_global_reutilizado_nos_olhos():
    raiz = criar_svg(
        modules={
            "gradient": criar_gradiente(),
        },
        eyes={
            "outer": {"shape": "rounded"},
            "inner": {"shape": "dots"},
        },
    )

    gradientes = obter_gradientes(raiz)

    assert len(gradientes) == 1

    olhos = raiz.find("svg:g[@id='qr-eyes']", NS)

    assert olhos is not None
    assert len(olhos) == 6

    identificador = gradientes[0].get("id")

    assert all(olho.get("fill") == f"url(#{identificador})" for olho in olhos)


def test_gradientes_locais_nos_olhos():
    raiz = criar_svg(
        eyes={
            "outer": {
                "gradient": criar_gradiente(),
            },
            "inner": {
                "gradient": criar_gradiente("radial"),
            },
        }
    )

    gradientes = obter_gradientes(raiz)

    assert len(gradientes) == 6

    assert sum(g.tag == f"{{{SVG_NS}}}linearGradient" for g in gradientes) == 3

    assert sum(g.tag == f"{{{SVG_NS}}}radialGradient" for g in gradientes) == 3


def test_gradiente_no_fundo_svg():
    raiz = criar_svg(
        background={
            "gradient": criar_gradiente(
                primeira="#FFFFFF",
                ultima="#DBEAFE",
            ),
        },
    )

    fundo = raiz.find("svg:rect[@id='qr-background']", NS)

    gradientes = obter_gradientes(raiz)

    assert fundo is not None
    assert len(gradientes) == 1

    identificador = gradientes[0].get("id")

    assert fundo.get("fill") == f"url(#{identificador})"


def test_transparencia_tem_prioridade():
    raiz = criar_svg(
        background={
            "transparent": True,
            "gradient": criar_gradiente(),
        },
    )

    assert raiz.find("svg:rect[@id='qr-background']", NS) is None

    assert not obter_gradientes(raiz)


def test_opacidade_no_gradiente_do_fundo():
    raiz = criar_svg(
        background={
            "gradient": criar_gradiente(
                primeira="#FFFFFF80",
                ultima="#FFFFFF00",
            ),
        },
    )

    gradiente = obter_gradientes(raiz)[0]

    pontos = gradiente.findall("svg:stop", NS)

    assert float(pontos[0].get("stop-opacity")) == pytest.approx(128 / 255)

    assert float(pontos[1].get("stop-opacity")) == 0


def test_referencias_dos_gradientes_validas():
    raiz = criar_svg(
        modules={
            "gradient": criar_gradiente(),
        },
        eyes={
            "outer": {
                "gradient": criar_gradiente("radial"),
            },
        },
        background={
            "gradient": criar_gradiente(
                primeira="#FFFFFF",
                ultima="#DBEAFE",
            ),
        },
    )

    ids = [elemento.get("id") for elemento in raiz.iter() if elemento.get("id") is not None]

    assert len(ids) == len(set(ids))

    for elemento in raiz.iter():
        preenchimento = elemento.get("fill", "")

        if preenchimento.startswith("url("):
            referencia = re.fullmatch(
                r"url\(#([A-Za-z0-9_-]+)\)",
                preenchimento,
            )

            assert referencia is not None
            assert referencia.group(1) in ids


def test_seguranca_svg_com_gradientes():
    raiz = criar_svg(
        modules={
            "shape": "dots",
            "gradient": criar_gradiente(),
        },
        eyes={
            "outer": {
                "gradient": criar_gradiente("radial"),
            },
        },
    )

    permitidos = {
        "svg",
        "defs",
        "linearGradient",
        "radialGradient",
        "stop",
        "rect",
        "path",
        "circle",
        "g",
    }

    for elemento in raiz.iter():
        nome = elemento.tag.split("}")[-1]

        assert nome in permitidos

        for atributo in elemento.attrib:
            nome_atributo = atributo.split("}")[-1].lower()

            assert not nome_atributo.startswith("on")
            assert nome_atributo not in {"href", "src"}


def test_svg_com_gradientes_deterministico():
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "ntizoconnect",
            "style": {
                "modules": {
                    "gradient": criar_gradiente(),
                },
            },
        }
    )

    estilo = resolver_estilo(pedido)
    matriz = gerar_matriz(pedido.content)

    primeiro = renderizar_svg(
        matriz,
        estilo=estilo,
    )

    segundo = renderizar_svg(
        matriz,
        estilo=estilo,
    )

    assert primeiro.dados == segundo.dados
