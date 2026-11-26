from xml.etree.ElementTree import Element, SubElement

import pytest
from PIL import Image, ImageDraw
from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.fundo import (
    BRANCO,
    TRANSPARENTE,
    EstiloFundo,
    renderizar_fundo_png,
    renderizar_fundo_svg,
)
from src.renderizacao.gradientes import (
    Gradiente,
    PontoCor,
)
from src.renderizacao.gradientes_svg import (
    RegistoGradientesSVG,
)

ROXO = (237, 233, 254, 255)
AZUL = (219, 234, 254, 255)
ROSA = (251, 207, 232, 255)


def criar_gradiente(tipo="linear", alfa=255):
    return Gradiente(
        tipo=tipo,
        angulo=45,
        pontos=(
            PontoCor(0, AZUL),
            PontoCor(
                1,
                (ROSA[0], ROSA[1], ROSA[2], alfa),
            ),
        ),
    )


# Resolução dos preenchimentos


def test_fundo_padrao():
    estilo = EstiloFundo()

    assert estilo.tipo == "solid"
    assert estilo.preenchimento.valor == BRANCO
    assert estilo.opaco


def test_fundo_solido():
    estilo = EstiloFundo(cor=ROXO)

    assert estilo.tipo == "solid"
    assert estilo.preenchimento.valor == ROXO


def test_fundo_gradiente():
    gradiente = criar_gradiente()

    estilo = EstiloFundo(gradiente=gradiente)

    assert estilo.tipo == "gradient"
    assert estilo.preenchimento.valor == gradiente


def test_fundo_transparente():
    estilo = EstiloFundo(transparente=True)

    assert estilo.tipo == "transparent"

    assert estilo.preenchimento.valor == TRANSPARENTE

    assert not estilo.opaco


def test_precedencia_gradiente():
    gradiente = criar_gradiente()

    estilo = EstiloFundo(
        cor=ROXO,
        gradiente=gradiente,
    )

    assert estilo.preenchimento.valor == gradiente


def test_precedencia_transparencia():
    estilo = EstiloFundo(
        cor=ROXO,
        gradiente=criar_gradiente(),
        transparente=True,
    )

    assert estilo.preenchimento.valor == TRANSPARENTE


def test_cor_solida_translucida():
    estilo = EstiloFundo(cor=(237, 233, 254, 128))

    assert not estilo.opaco


def test_gradiente_translucido():
    estilo = EstiloFundo(gradiente=criar_gradiente(alfa=0))

    assert not estilo.opaco


@pytest.mark.parametrize(
    "cor",
    [
        (0, 0, 0),
        (-1, 0, 0, 255),
        (256, 0, 0, 255),
        (0, 0, 0, 256),
        "#FFFFFF",
    ],
)
def test_rejeitar_cor_invalida(cor):
    with pytest.raises(ErroDadosInvalidos):
        EstiloFundo(cor=cor)


@pytest.mark.parametrize("valor", [0, 1, "true", None])
def test_rejeitar_transparencia_invalida(valor):
    with pytest.raises(ErroDadosInvalidos):
        EstiloFundo(transparente=valor)


def test_rejeitar_gradiente_invalido():
    with pytest.raises(ErroDadosInvalidos):
        EstiloFundo(gradiente="linear")


# Renderização PNG


def test_png_fundo_padrao():
    with renderizar_fundo_png(128, 128, EstiloFundo()) as imagem:
        assert imagem.mode == "RGBA"
        assert imagem.size == (128, 128)
        assert imagem.getpixel((0, 0)) == BRANCO


def test_png_fundo_solido():
    with renderizar_fundo_png(
        128,
        128,
        EstiloFundo(cor=ROXO),
    ) as imagem:
        assert imagem.getpixel((0, 0)) == ROXO
        assert imagem.getpixel((64, 64)) == ROXO


def test_png_fundo_transparente():
    with renderizar_fundo_png(
        128,
        128,
        EstiloFundo(transparente=True),
    ) as imagem:
        assert imagem.getbbox() is None

        with imagem.getchannel("A") as alfa:
            assert alfa.getextrema() == (0, 0)


@pytest.mark.parametrize("tipo", ["linear", "radial"])
def test_png_fundo_gradiente(tipo):
    estilo = EstiloFundo(gradiente=criar_gradiente(tipo))

    with renderizar_fundo_png(128, 128, estilo) as imagem:
        assert imagem.getpixel((0, 0)) != imagem.getpixel((64, 64))

        with imagem.getchannel("A") as alfa:
            assert alfa.getextrema() == (255, 255)


def test_png_preservar_fundo_translucido():
    estilo = EstiloFundo(cor=(237, 233, 254, 128))

    with renderizar_fundo_png(128, 128, estilo) as imagem, imagem.getchannel("A") as alfa:
        assert alfa.getextrema() == (128, 128)


def test_png_composicao_sobre_gradiente():
    estilo = EstiloFundo(gradiente=criar_gradiente())

    with renderizar_fundo_png(128, 128, estilo) as imagem:
        margem = imagem.getpixel((0, 0))

        with Image.new(
            "RGBA",
            (128, 128),
            TRANSPARENTE,
        ) as camada:
            desenho = ImageDraw.Draw(camada)

            desenho.rectangle(
                (16, 16, 31, 31),
                fill=(0, 0, 0, 255),
            )

            imagem.alpha_composite(camada)

        assert imagem.getpixel((0, 0)) == margem

        assert imagem.getpixel((20, 20)) == (0, 0, 0, 255)


# Renderização SVG


def test_svg_fundo_padrao():
    raiz = Element("svg")
    registo = RegistoGradientesSVG(raiz)

    elemento = renderizar_fundo_svg(
        raiz,
        128,
        128,
        EstiloFundo(),
        registo,
    )

    assert elemento is not None
    assert elemento.tag == "rect"
    assert elemento.get("fill") == "#FFFFFF"
    assert elemento.get("width") == "128"
    assert elemento.get("height") == "128"


def test_svg_fundo_solido():
    raiz = Element("svg")
    registo = RegistoGradientesSVG(raiz)

    elemento = renderizar_fundo_svg(
        raiz,
        128,
        128,
        EstiloFundo(cor=ROXO),
        registo,
    )

    assert elemento is not None
    assert elemento.get("fill") == "#EDE9FE"
    assert registo.quantidade == 0


def test_svg_fundo_transparente():
    raiz = Element("svg")
    registo = RegistoGradientesSVG(raiz)

    elemento = renderizar_fundo_svg(
        raiz,
        128,
        128,
        EstiloFundo(transparente=True),
        registo,
    )

    assert elemento is None
    assert len(raiz) == 0


@pytest.mark.parametrize(
    ("tipo", "tag"),
    [
        ("linear", "linearGradient"),
        ("radial", "radialGradient"),
    ],
)
def test_svg_fundo_gradiente(tipo, tag):
    raiz = Element("svg")
    registo = RegistoGradientesSVG(raiz)

    elemento = renderizar_fundo_svg(
        raiz,
        128,
        128,
        EstiloFundo(gradiente=criar_gradiente(tipo)),
        registo,
    )

    assert elemento is not None

    assert elemento.get("fill") == ("url(#gqr-gradient-1)")

    assert raiz.find(f"./defs/{tag}") is not None
    assert registo.quantidade == 1


def test_svg_fundo_translucido():
    raiz = Element("svg")
    registo = RegistoGradientesSVG(raiz)

    elemento = renderizar_fundo_svg(
        raiz,
        128,
        128,
        EstiloFundo(cor=(237, 233, 254, 128)),
        registo,
    )

    assert elemento is not None

    assert float(elemento.attrib["fill-opacity"]) == pytest.approx(128 / 255)


def test_svg_ordem_das_camadas():
    raiz = Element("svg")
    registo = RegistoGradientesSVG(raiz)

    renderizar_fundo_svg(
        raiz,
        128,
        128,
        EstiloFundo(gradiente=criar_gradiente()),
        registo,
    )

    SubElement(
        raiz,
        "g",
        {"id": "qr-modules"},
    )

    SubElement(
        raiz,
        "g",
        {"id": "qr-eyes"},
    )

    assert [elemento.tag for elemento in raiz] == [
        "defs",
        "rect",
        "g",
        "g",
    ]

    assert raiz[1].get("id") == "qr-background"


@pytest.mark.parametrize(
    ("largura", "altura"),
    [
        (0, 128),
        (128, 0),
        (-1, 128),
        (2049, 128),
        (128, 2049),
    ],
)
def test_png_rejeitar_dimensoes_invalidas(largura, altura):
    with pytest.raises(ErroDadosInvalidos):
        renderizar_fundo_png(
            largura,
            altura,
            EstiloFundo(),
        )


@pytest.mark.parametrize(
    ("largura", "altura"),
    [
        (0, 128),
        (128, 0),
        (-1, 128),
        (2049, 128),
        (128, 2049),
    ],
)
def test_svg_rejeitar_dimensoes_invalidas(largura, altura):
    raiz = Element("svg")
    registo = RegistoGradientesSVG(raiz)

    with pytest.raises(ErroDadosInvalidos):
        renderizar_fundo_svg(
            raiz,
            largura,
            altura,
            EstiloFundo(),
            registo,
        )
