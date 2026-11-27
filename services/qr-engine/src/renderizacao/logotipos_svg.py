from base64 import b64encode
from io import BytesIO
from xml.etree.ElementTree import Element, SubElement

from PIL import Image

from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.logotipos import GeometriaLogotipo

ID_RECORTE_LOGOTIPO = "gqr-logo-clip"


def criar_recorte_logotipo_svg(
    raiz: Element,
    geometria: GeometriaLogotipo,
    tamanho: int,
) -> Element:
    """Criar um grupo que exclui a região de protecção do logótipo."""
    x, y, xf, yf = geometria.caixa_protecao

    if not (0 <= x < xf <= tamanho and 0 <= y < yf <= tamanho):
        raise ErroDadosInvalidos()

    defs = raiz.find("defs")

    if defs is None:
        defs = Element("defs")
        raiz.insert(0, defs)

    recorte = SubElement(
        defs,
        "clipPath",
        {
            "id": ID_RECORTE_LOGOTIPO,
            "clipPathUnits": "userSpaceOnUse",
        },
    )

    exterior = f"M0 0H{tamanho}V{tamanho}H0Z"
    interior = f"M{x} {y}H{xf}V{yf}H{x}Z"

    SubElement(
        recorte,
        "path",
        {
            "d": exterior + interior,
            "clip-rule": "evenodd",
        },
    )

    return SubElement(
        raiz,
        "g",
        {
            "id": "qr-modules-clipped",
            "clip-path": f"url(#{ID_RECORTE_LOGOTIPO})",
        },
    )


def codificar_logotipo_svg(
    logotipo: Image.Image,
    largura: int,
    altura: int,
) -> str:
    """Codificar o logótipo normalizado como PNG incorporável."""
    if logotipo.mode != "RGBA" or largura <= 0 or altura <= 0:
        raise ErroDadosInvalidos()

    with (
        logotipo.resize(
            (largura, altura),
            resample=Image.Resampling.LANCZOS,
        ) as redimensionado,
        BytesIO() as memoria,
    ):
        redimensionado.save(
            memoria,
            format="PNG",
            compress_level=6,
        )

        dados = b64encode(
            memoria.getvalue(),
        ).decode("ascii")

    return f"data:image/png;base64,{dados}"


def renderizar_logotipo_svg(
    raiz: Element,
    logotipo: Image.Image,
    geometria: GeometriaLogotipo,
) -> Element:
    """Incorporar o logótipo sem referências a recursos externos."""
    x, y, xf, yf = geometria.caixa_imagem

    largura = xf - x
    altura = yf - y

    dados = codificar_logotipo_svg(
        logotipo,
        largura,
        altura,
    )

    return SubElement(
        raiz,
        "image",
        {
            "id": "qr-logo",
            "x": str(x),
            "y": str(y),
            "width": str(largura),
            "height": str(altura),
            "preserveAspectRatio": "none",
            "href": dados,
        },
    )
