from collections.abc import Iterator
from dataclasses import dataclass

from segno.consts import TYPE_DATA_DARK

from src.motor.matriz import MatrizQR
from src.renderizacao.geometria import GeometriaQR
from src.renderizacao.olhos import pertence_a_olho
from src.schemas.personalizacao import Forma


@dataclass(frozen=True, slots=True)
class ModuloVisual:
    linha: int
    coluna: int

    x: int
    y: int

    escala: int
    forma: Forma

    funcional: bool


def determinar_forma(
    tipo_modulo: int,
    forma_solicitada: Forma,
) -> Forma:
    """Preserva a geometria dos padrões funcionais."""

    if tipo_modulo == TYPE_DATA_DARK:
        return forma_solicitada

    return "square"


def iterar_modulos_escuros(
    matriz: MatrizQR,
    geometria: GeometriaQR,
    forma: Forma = "square",
    excluir_olhos: bool = False,
) -> Iterator[ModuloVisual]:
    """Produz os módulos visuais de um código QR."""

    for linha, valores in enumerate(matriz.modulos):
        for coluna, valor in enumerate(valores):
            if valor == 0:
                continue

            if excluir_olhos and pertence_a_olho(
                linha,
                coluna,
                matriz.dimensao,
            ):
                continue

            tipo = matriz.tipo_modulo(
                linha,
                coluna,
            )

            x, y, _, _ = geometria.caixa_modulo(
                linha,
                coluna,
            )

            yield ModuloVisual(
                linha=linha,
                coluna=coluna,
                x=x,
                y=y,
                escala=geometria.escala,
                forma=determinar_forma(tipo, forma),
                funcional=tipo != TYPE_DATA_DARK,
            )
