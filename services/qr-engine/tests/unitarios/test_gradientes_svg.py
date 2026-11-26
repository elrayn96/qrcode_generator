from math import hypot
from xml.etree.ElementTree import (
    Element,
    SubElement,
    fromstring,
    tostring,
)

import pytest
from src.renderizacao.gradientes import (
    GeometriaGradiente,
    Gradiente,
    PontoCor,
)
from src.renderizacao.gradientes_svg import (
    RegistoGradientesSVG,
    atributos_cor_solida,
    atributos_ponto_cor,
    converter_hex,
    formatar_numero,
)


def criar_raiz():
    return Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": "512",
            "height": "512",
            "viewBox": "0 0 512 512",
        },
    )


def criar_gradiente(
    tipo="linear",
    angulo=0,
):
    return Gradiente(
        tipo=tipo,
        pontos=(
            PontoCor(
                posicao=0.0,
                cor=(124, 58, 237, 255),
            ),
            PontoCor(
                posicao=1.0,
                cor=(49, 46, 129, 255),
            ),
        ),
        angulo=angulo,
    )


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (0, "0"),
        (-0.0, "0"),
        (1.0, "1"),
        (1.25, "1.25"),
        (512.0, "512"),
        (0.123456789012, "0.123456789"),
    ],
)
def test_formatar_numero(valor, esperado):
    assert formatar_numero(valor) == esperado


def test_converter_hex():
    assert converter_hex((124, 58, 237, 255)) == "#7C3AED"


def test_cor_solida_opaca():
    assert atributos_cor_solida((124, 58, 237, 255)) == {
        "fill": "#7C3AED",
    }


def test_cor_solida_translucida():
    atributos = atributos_cor_solida((124, 58, 237, 128))

    assert atributos["fill"] == "#7C3AED"

    assert float(atributos["fill-opacity"]) == pytest.approx(128 / 255)


def test_cor_solida_transparente():
    atributos = atributos_cor_solida((0, 0, 0, 0))

    assert atributos["fill-opacity"] == "0"


def test_ponto_cor_opaco():
    atributos = atributos_ponto_cor(
        0.5,
        (124, 58, 237, 255),
    )

    assert atributos == {
        "offset": "0.5",
        "stop-color": "#7C3AED",
    }


def test_ponto_cor_translucido():
    atributos = atributos_ponto_cor(
        0.5,
        (124, 58, 237, 128),
    )

    assert float(atributos["stop-opacity"]) == pytest.approx(128 / 255)


def test_registo_inicial_vazio():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    assert registo.quantidade == 0

    assert raiz.find("defs") is None


def test_criar_gradiente_linear():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    identificador = registo.registar(
        criar_gradiente(),
        GeometriaGradiente(512, 512),
    )

    elemento = raiz.find("defs/linearGradient")

    assert elemento is not None

    assert identificador == "gqr-gradient-1"

    assert elemento.get("id") == identificador

    assert elemento.get("gradientUnits") == "userSpaceOnUse"


def test_coordenadas_lineares_horizontais():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    registo.registar(
        criar_gradiente(angulo=0),
        GeometriaGradiente(512, 256),
    )

    elemento = raiz.find("defs/linearGradient")

    assert elemento is not None

    assert elemento.get("x1") == "0"
    assert elemento.get("y1") == "128"

    assert elemento.get("x2") == "512"
    assert elemento.get("y2") == "128"


def test_coordenadas_lineares_verticais():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    registo.registar(
        criar_gradiente(angulo=90),
        GeometriaGradiente(512, 256),
    )

    elemento = raiz.find("defs/linearGradient")

    assert elemento is not None

    assert elemento.get("x1") == "256"
    assert elemento.get("y1") == "0"

    assert elemento.get("x2") == "256"
    assert elemento.get("y2") == "256"


def test_coordenadas_com_origem():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    registo.registar(
        criar_gradiente(),
        GeometriaGradiente(
            largura=200,
            altura=100,
            origem_x=20,
            origem_y=40,
        ),
    )

    elemento = raiz.find("defs/linearGradient")

    assert elemento is not None

    assert elemento.get("x1") == "20"
    assert elemento.get("y1") == "90"

    assert elemento.get("x2") == "220"
    assert elemento.get("y2") == "90"


def test_criar_gradiente_radial():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    registo.registar(
        criar_gradiente(tipo="radial"),
        GeometriaGradiente(512, 256),
    )

    elemento = raiz.find("defs/radialGradient")

    assert elemento is not None

    assert elemento.get("cx") == "256"
    assert elemento.get("cy") == "128"

    assert elemento.get("fx") == "256"
    assert elemento.get("fy") == "128"

    assert float(elemento.attrib["r"]) == pytest.approx(hypot(256, 128))


def test_pontos_do_gradiente():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    registo.registar(
        criar_gradiente(),
        GeometriaGradiente(512, 512),
    )

    pontos = raiz.findall("defs/linearGradient/stop")

    assert len(pontos) == 2

    assert pontos[0].get("offset") == "0"

    assert pontos[0].get("stop-color") == "#7C3AED"

    assert pontos[1].get("offset") == "1"

    assert pontos[1].get("stop-color") == "#312E81"


def test_gradiente_com_transparencia():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    gradiente = Gradiente(
        tipo="linear",
        pontos=(
            PontoCor(
                0.0,
                (0, 0, 0, 0),
            ),
            PontoCor(
                1.0,
                (124, 58, 237, 128),
            ),
        ),
    )

    registo.registar(
        gradiente,
        GeometriaGradiente(512, 512),
    )

    pontos = raiz.findall("defs/linearGradient/stop")

    assert pontos[0].get("stop-opacity") == "0"

    assert float(pontos[1].attrib["stop-opacity"]) == pytest.approx(128 / 255)


def test_reutilizar_gradiente():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    gradiente = criar_gradiente()
    geometria = GeometriaGradiente(512, 512)

    primeiro = registo.registar(
        gradiente,
        geometria,
    )

    segundo = registo.registar(
        gradiente,
        geometria,
    )

    assert primeiro == segundo
    assert registo.quantidade == 1

    assert len(raiz.findall("defs/linearGradient")) == 1


def test_geometrias_distintas():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    gradiente = criar_gradiente()

    primeiro = registo.registar(
        gradiente,
        GeometriaGradiente(512, 512),
    )

    segundo = registo.registar(
        gradiente,
        GeometriaGradiente(128, 128),
    )

    assert primeiro != segundo
    assert registo.quantidade == 2


def test_gradientes_distintos():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    geometria = GeometriaGradiente(512, 512)

    primeiro = registo.registar(
        criar_gradiente(angulo=0),
        geometria,
    )

    segundo = registo.registar(
        criar_gradiente(angulo=90),
        geometria,
    )

    assert primeiro != segundo
    assert registo.quantidade == 2


def test_reutilizar_defs_existente():
    raiz = criar_raiz()

    existente = SubElement(raiz, "defs")

    registo = RegistoGradientesSVG(raiz)

    registo.registar(
        criar_gradiente(),
        GeometriaGradiente(512, 512),
    )

    assert len(raiz.findall("defs")) == 1

    assert existente.find("linearGradient") is not None


def test_evitar_colisao_identificadores():
    raiz = criar_raiz()

    SubElement(
        raiz,
        "g",
        {"id": "gqr-gradient-1"},
    )

    registo = RegistoGradientesSVG(raiz)

    identificador = registo.registar(
        criar_gradiente(),
        GeometriaGradiente(512, 512),
    )

    assert identificador == "gqr-gradient-2"


def test_atributos_preenchimento_solido():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    atributos = registo.atributos_preenchimento(
        (124, 58, 237, 255),
        GeometriaGradiente(512, 512),
    )

    assert atributos == {
        "fill": "#7C3AED",
    }

    assert registo.quantidade == 0

    assert raiz.find("defs") is None


def test_atributos_preenchimento_gradiente():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    atributos = registo.atributos_preenchimento(
        criar_gradiente(),
        GeometriaGradiente(512, 512),
    )

    assert atributos == {
        "fill": "url(#gqr-gradient-1)",
    }


def test_serializacao_svg():
    raiz = criar_raiz()

    registo = RegistoGradientesSVG(raiz)

    atributos = registo.atributos_preenchimento(
        criar_gradiente(),
        GeometriaGradiente(512, 512),
    )

    SubElement(
        raiz,
        "rect",
        {
            "width": "512",
            "height": "512",
            **atributos,
        },
    )

    dados = tostring(
        raiz,
        encoding="utf-8",
    )

    documento = fromstring(dados)

    ns = {
        "svg": "http://www.w3.org/2000/svg",
    }

    gradiente = documento.find(
        "svg:defs/svg:linearGradient",
        ns,
    )

    rectangulo = documento.find(
        "svg:rect",
        ns,
    )

    assert gradiente is not None

    assert rectangulo is not None

    assert rectangulo.get("fill") == ("url(#gqr-gradient-1)")


def test_resultado_deterministico():
    def gerar():
        raiz = criar_raiz()

        registo = RegistoGradientesSVG(raiz)

        registo.registar(
            criar_gradiente(),
            GeometriaGradiente(512, 512),
        )

        return tostring(
            raiz,
            encoding="utf-8",
        )

    assert gerar() == gerar()
