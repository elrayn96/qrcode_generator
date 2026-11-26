from xml.etree.ElementTree import Element

import pytest
from PIL import Image
from src.renderizacao.cores import PRETO
from src.renderizacao.geometria import (
    calcular_geometria,
)
from src.renderizacao.gradientes import (
    Gradiente,
    PontoCor,
)
from src.renderizacao.gradientes_svg import (
    RegistoGradientesSVG,
)
from src.renderizacao.olhos import (
    EstiloOlhos,
    calcular_geometria_olhos,
)
from src.renderizacao.olhos_png import (
    renderizar_olhos_png,
)
from src.renderizacao.olhos_svg import (
    renderizar_olhos_svg,
)
from src.renderizacao.preenchimentos import (
    PreenchimentosOlhos,
    PreenchimentoVisual,
)


def criar_estilo():
    return EstiloOlhos(
        forma_exterior="square",
        forma_interior="square",
        cor_exterior=PRETO,
        cor_interior=PRETO,
    )


def criar_gradiente(tipo="linear"):
    return Gradiente(
        tipo=tipo,
        pontos=(
            PontoCor(0, (30, 27, 75, 255)),
            PontoCor(1, (124, 58, 237, 255)),
        ),
    )


def criar_preenchimentos(
    tipo="linear",
    ambito="local",
):
    return PreenchimentosOlhos(
        exterior=PreenchimentoVisual(
            criar_gradiente(tipo),
            ambito=ambito,
        ),
        interior=PreenchimentoVisual((37, 99, 235, 255)),
    )


@pytest.mark.parametrize("tipo", ["linear", "radial"])
def test_gradientes_png(tipo):
    geometria = calcular_geometria(21, 512)

    with Image.new("RGBA", (512, 512)) as imagem:
        renderizar_olhos_png(
            imagem,
            geometria,
            criar_estilo(),
            criar_preenchimentos(tipo),
        )

        assert imagem.getbbox() is not None
        assert imagem.getpixel((0, 0))[3] == 0


def test_preservar_abertura_png():
    geometria = calcular_geometria(21, 512)
    estilo = criar_estilo()

    with Image.new("RGBA", (512, 512)) as imagem:
        renderizar_olhos_png(
            imagem,
            geometria,
            estilo,
            criar_preenchimentos(),
        )

        for olho in calcular_geometria_olhos(
            geometria,
            estilo,
        ):
            e = geometria.escala

            x = olho.exterior.x
            y = olho.exterior.y

            abertura = (
                x + e + e // 2,
                y + 3 * e + e // 2,
            )

            assert imagem.getpixel(abertura)[3] == 0


def test_preenchimento_independente_png():
    geometria = calcular_geometria(21, 512)

    with Image.new("RGBA", (512, 512)) as imagem:
        renderizar_olhos_png(
            imagem,
            geometria,
            criar_estilo(),
            criar_preenchimentos(),
        )

        e = geometria.escala

        x = geometria.origem_x
        y = geometria.origem_y

        centro = (
            x + 3 * e + e // 2,
            y + 3 * e + e // 2,
        )

        assert imagem.getpixel(centro) == (37, 99, 235, 255)


def test_gradiente_local_repetido_png():
    geometria = calcular_geometria(21, 512)
    estilo = criar_estilo()

    with Image.new("RGBA", (512, 512)) as imagem:
        renderizar_olhos_png(
            imagem,
            geometria,
            estilo,
            criar_preenchimentos(),
        )

        cores = [
            imagem.getpixel((olho.exterior.x, olho.exterior.y))
            for olho in calcular_geometria_olhos(geometria, estilo)
        ]

        assert len(set(cores)) == 1


def test_gradiente_global_png():
    geometria = calcular_geometria(21, 512)
    estilo = criar_estilo()

    with Image.new("RGBA", (512, 512)) as imagem:
        renderizar_olhos_png(
            imagem,
            geometria,
            estilo,
            criar_preenchimentos(ambito="global"),
        )

        olhos = calcular_geometria_olhos(geometria, estilo)

        esquerda = imagem.getpixel((olhos[0].exterior.x, olhos[0].exterior.y))

        direita = imagem.getpixel((olhos[1].exterior.x, olhos[1].exterior.y))

        assert esquerda != direita


@pytest.mark.parametrize("tipo", ["linear", "radial"])
def test_gradientes_locais_svg(tipo):
    raiz = Element("svg")

    registo = RegistoGradientesSVG(raiz)

    renderizar_olhos_svg(
        raiz,
        calcular_geometria(21, 512),
        criar_estilo(),
        criar_preenchimentos(tipo),
        registo,
    )

    grupo = raiz.find("g[@id='qr-eyes']")

    assert grupo is not None
    assert len(grupo) == 6
    assert registo.quantidade == 3


def test_gradiente_global_reutilizado_svg():
    raiz = Element("svg")
    registo = RegistoGradientesSVG(raiz)

    renderizar_olhos_svg(
        raiz,
        calcular_geometria(21, 512),
        criar_estilo(),
        criar_preenchimentos(ambito="global"),
        registo,
    )

    grupo = raiz.find("g[@id='qr-eyes']")

    assert grupo is not None
    assert registo.quantidade == 1

    referencias = {
        elemento.attrib["fill"] for elemento in grupo if elemento.get("fill-rule") == "evenodd"
    }

    assert len(referencias) == 1


def test_preservar_abertura_svg():
    raiz = Element("svg")
    registo = RegistoGradientesSVG(raiz)

    renderizar_olhos_svg(
        raiz,
        calcular_geometria(21, 512),
        criar_estilo(),
        criar_preenchimentos(),
        registo,
    )

    grupo = raiz.find("g[@id='qr-eyes']")

    assert grupo is not None

    assert sum(elemento.get("fill-rule") == "evenodd" for elemento in grupo) == 3
