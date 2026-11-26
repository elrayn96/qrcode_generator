from dataclasses import dataclass
from typing import Literal
from xml.etree.ElementTree import Element, SubElement

from PIL import Image

from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.composicao import (
    criar_preenchimento,
    validar_dimensoes,
)
from src.renderizacao.gradientes import (
    RGBA,
    GeometriaGradiente,
    Gradiente,
)
from src.renderizacao.gradientes_svg import (
    RegistoGradientesSVG,
)
from src.renderizacao.preenchimentos import (
    PreenchimentoVisual,
)

BRANCO: RGBA = (255, 255, 255, 255)
TRANSPARENTE: RGBA = (0, 0, 0, 0)

TipoFundo = Literal[
    "solid",
    "gradient",
    "transparent",
]


@dataclass(frozen=True, slots=True)
class EstiloFundo:
    cor: RGBA | None = None
    gradiente: Gradiente | None = None
    transparente: bool = False

    def __post_init__(self) -> None:
        if type(self.transparente) is not bool:
            raise ErroDadosInvalidos()

        if self.cor is not None:
            PreenchimentoVisual(self.cor)

        if self.gradiente is not None and not isinstance(self.gradiente, Gradiente):
            raise ErroDadosInvalidos()

    @property
    def tipo(self) -> TipoFundo:
        if self.transparente:
            return "transparent"

        if self.gradiente is not None:
            return "gradient"

        return "solid"

    @property
    def preenchimento(self) -> PreenchimentoVisual:
        if self.transparente:
            return PreenchimentoVisual(TRANSPARENTE)

        if self.gradiente is not None:
            return PreenchimentoVisual(self.gradiente)

        return PreenchimentoVisual(self.cor if self.cor is not None else BRANCO)

    @property
    def opaco(self) -> bool:
        return self.preenchimento.opaco


def renderizar_fundo_png(
    largura: int,
    altura: int,
    estilo: EstiloFundo,
) -> Image.Image:
    validar_dimensoes(largura, altura)

    geometria = GeometriaGradiente(
        largura=largura,
        altura=altura,
    )

    return criar_preenchimento(
        largura=largura,
        altura=altura,
        preenchimento=estilo.preenchimento.valor,
        geometria=geometria,
    )


def renderizar_fundo_svg(
    raiz: Element,
    largura: int,
    altura: int,
    estilo: EstiloFundo,
    registo: RegistoGradientesSVG,
) -> Element | None:
    validar_dimensoes(largura, altura)

    if estilo.transparente:
        return None

    geometria = GeometriaGradiente(
        largura=largura,
        altura=altura,
    )

    atributos = registo.atributos_preenchimento(
        estilo.preenchimento.valor,
        geometria,
    )

    return SubElement(
        raiz,
        "rect",
        {
            "id": "qr-background",
            "x": "0",
            "y": "0",
            "width": str(largura),
            "height": str(altura),
            **atributos,
        },
    )
