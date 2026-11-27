from base64 import b64decode, b64encode
from io import BytesIO
from xml.etree.ElementTree import Element, fromstring

import pytest
from PIL import Image
from src.core.excecoes import ErroDadosInvalidos
from src.motor.matriz import gerar_matriz
from src.renderizacao.estilos import EstiloRenderizacao
from src.renderizacao.fundo import EstiloFundo
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.gradientes import Gradiente, PontoCor
from src.renderizacao.logotipos import (
    GeometriaLogotipo,
    calcular_geometria_logotipo,
)
from src.renderizacao.logotipos_svg import (
    codificar_logotipo_svg,
    criar_recorte_logotipo_svg,
)
from src.renderizacao.preenchimentos import PreenchimentoVisual
from src.renderizacao.svg import renderizar_svg
from src.schemas.personalizacao import Logotipo

NS = {"svg": "http://www.w3.org/2000/svg"}


def criar_logo(
    formato="PNG",
    cor=(255, 0, 0, 128),
    tamanho=(40, 20),
):
    with Image.new("RGBA", tamanho, cor) as imagem, BytesIO() as memoria:
        if formato == "JPEG":
            with imagem.convert("RGB") as rgb:
                rgb.save(memoria, format="JPEG")
        else:
            imagem.save(memoria, format="PNG")

        dados = b64encode(
            memoria.getvalue(),
        ).decode("ascii")

    return Logotipo(
        mediaType="image/jpeg" if formato == "JPEG" else "image/png",
        base64=dados,
        scale=0.1,
        padding=1,
    )


@pytest.fixture
def matriz():
    return gerar_matriz("ntizoconnect", "H")


@pytest.mark.parametrize("formato", ["PNG", "JPEG"])
def test_incorpora_logotipo(matriz, formato):
    logo = criar_logo(formato)

    resultado = renderizar_svg(
        matriz,
        logotipo=logo,
    )

    assert resultado.media_type == "image/svg+xml"
    assert resultado.largura == 512
    assert resultado.altura == 512

    raiz = fromstring(resultado.dados)

    elemento = raiz.find("svg:image", NS)

    assert elemento is not None
    assert elemento.get("id") == "qr-logo"

    href = elemento.attrib["href"]

    assert href.startswith("data:image/png;base64,")

    dados = b64decode(
        href.split(",", 1)[1],
        validate=True,
    )

    with Image.open(BytesIO(dados)) as imagem:
        assert imagem.format == "PNG"
        assert imagem.mode == "RGBA"

        assert imagem.size == (
            int(elemento.attrib["width"]),
            int(elemento.attrib["height"]),
        )

        assert imagem.info == {}


def test_geometria_logotipo(matriz):
    logo = criar_logo()

    raiz = fromstring(
        renderizar_svg(
            matriz,
            logotipo=logo,
        ).dados,
    )

    g = calcular_geometria(
        matriz.dimensao,
        512,
    )

    r = calcular_geometria_logotipo(
        matriz,
        g,
        logo,
        (40, 20),
    )

    elemento = raiz.find("svg:image", NS)

    assert elemento is not None

    x, y, xf, yf = r.caixa_imagem

    assert elemento.get("x") == str(x)
    assert elemento.get("y") == str(y)
    assert elemento.get("width") == str(xf - x)
    assert elemento.get("height") == str(yf - y)


def test_recorte_logotipo(matriz):
    logo = criar_logo()

    raiz = fromstring(
        renderizar_svg(
            matriz,
            logotipo=logo,
        ).dados,
    )

    recorte = raiz.find(
        "svg:defs/svg:clipPath",
        NS,
    )

    assert recorte is not None
    assert recorte.get("id") == "gqr-logo-clip"
    assert recorte.get("clipPathUnits") == "userSpaceOnUse"

    caminho = recorte.find("svg:path", NS)

    assert caminho is not None
    assert caminho.get("clip-rule") == "evenodd"

    g = calcular_geometria(matriz.dimensao, 512)

    r = calcular_geometria_logotipo(
        matriz,
        g,
        logo,
        (40, 20),
    )

    x, y, xf, yf = r.caixa_protecao

    esperado = f"M0 0H512V512H0ZM{x} {y}H{xf}V{yf}H{x}Z"

    assert caminho.get("d") == esperado

    grupo = raiz.find("svg:g", NS)

    assert grupo is not None
    assert grupo.get("clip-path") == "url(#gqr-logo-clip)"
    assert grupo.find("svg:path", NS) is not None


@pytest.mark.parametrize(
    "transparente",
    [True, False],
)
def test_preserva_fundo(matriz, transparente):
    estilo = EstiloRenderizacao(
        forma="square",
        modulos=PreenchimentoVisual(
            (0, 0, 0, 255),
        ),
        fundo=EstiloFundo(
            cor=(100, 150, 200, 128),
            transparente=transparente,
        ),
    )

    raiz = fromstring(
        renderizar_svg(
            matriz,
            estilo=estilo,
            logotipo=criar_logo(),
        ).dados,
    )

    fundo = raiz.find(
        "svg:rect[@id='qr-background']",
        NS,
    )

    if transparente:
        assert fundo is None
    else:
        assert fundo is not None
        assert fundo.get("fill") == "#6496C8"
        assert float(fundo.attrib["fill-opacity"]) == pytest.approx(
            128 / 255,
        )


def test_preserva_alfa(matriz):
    raiz = fromstring(
        renderizar_svg(
            matriz,
            logotipo=criar_logo(),
        ).dados,
    )

    elemento = raiz.find("svg:image", NS)

    assert elemento is not None

    dados = b64decode(
        elemento.attrib["href"].split(",", 1)[1],
    )

    with Image.open(BytesIO(dados)) as imagem:
        assert imagem.getpixel((0, 0))[3] == 128


def test_gradientes_e_recorte(matriz):
    gradiente = Gradiente(
        tipo="linear",
        angulo=45,
        pontos=(
            PontoCor(
                posicao=0.0,
                cor=(109, 40, 217, 255),
            ),
            PontoCor(
                posicao=1.0,
                cor=(23, 37, 84, 255),
            ),
        ),
    )

    estilo = EstiloRenderizacao(
        forma="rounded",
        modulos=PreenchimentoVisual(gradiente),
        fundo=EstiloFundo(gradiente=gradiente),
    )

    raiz = fromstring(
        renderizar_svg(
            matriz,
            estilo=estilo,
            logotipo=criar_logo(),
        ).dados,
    )

    defs = raiz.findall("svg:defs", NS)

    assert len(defs) == 1

    assert (
        defs[0].find(
            "svg:clipPath",
            NS,
        )
        is not None
    )

    assert (
        len(
            defs[0].findall(
                "svg:linearGradient",
                NS,
            ),
        )
        == 2
    )

    ids = [elemento.attrib["id"] for elemento in raiz.iter() if "id" in elemento.attrib]

    assert len(ids) == len(set(ids))


def test_ordem_camadas(matriz):
    raiz = fromstring(
        renderizar_svg(
            matriz,
            logotipo=criar_logo(),
        ).dados,
    )

    ids = [elemento.get("id") for elemento in raiz]

    assert ids.index("qr-background") < ids.index(
        "qr-modules-clipped",
    )

    assert ids.index("qr-modules-clipped") < ids.index(
        "qr-logo",
    )


def test_sem_logotipo(matriz):
    original = renderizar_svg(matriz)

    resultado = renderizar_svg(
        matriz,
        logotipo=None,
    )

    assert original.dados == resultado.dados


def test_determinismo(matriz):
    logo = criar_logo()

    assert (
        renderizar_svg(
            matriz,
            logotipo=logo,
        ).dados
        == renderizar_svg(
            matriz,
            logotipo=logo,
        ).dados
    )


def test_sem_referencias_externas(matriz):
    raiz = fromstring(
        renderizar_svg(
            matriz,
            logotipo=criar_logo(),
        ).dados,
    )

    proibidos = {
        "script",
        "foreignObject",
        "iframe",
    }

    for elemento in raiz.iter():
        nome = elemento.tag.rsplit("}", 1)[-1]

        assert nome not in proibidos

        for atributo, valor in elemento.attrib.items():
            nome_atributo = atributo.rsplit("}", 1)[-1]

            assert not nome_atributo.lower().startswith("on")

            if nome_atributo == "href":
                assert valor.startswith(
                    "data:image/png;base64,",
                )

            if valor.startswith("url("):
                assert valor.startswith("url(#")


def test_rejeita_logotipo_invalido(matriz):
    logo = Logotipo(
        mediaType="image/png",
        base64="AB==",
    )

    with pytest.raises(ErroDadosInvalidos):
        renderizar_svg(
            matriz,
            logotipo=logo,
        )


def test_rejeita_recorte_invalido():
    geometria = GeometriaLogotipo(
        caixa_imagem=(4, 4, 8, 8),
        caixa_protecao=(-1, -1, 10, 10),
    )

    with pytest.raises(ErroDadosInvalidos):
        criar_recorte_logotipo_svg(
            Element("svg"),
            geometria,
            12,
        )


@pytest.mark.parametrize(
    "modo,largura,altura",
    [
        ("RGB", 10, 10),
        ("RGBA", 0, 10),
        ("RGBA", 10, 0),
    ],
)
def test_rejeita_codificacao_invalida(
    modo,
    largura,
    altura,
):
    with Image.new(modo, (10, 10)) as imagem, pytest.raises(ErroDadosInvalidos):
        codificar_logotipo_svg(
            imagem,
            largura,
            altura,
        )
