from dataclasses import dataclass

from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.cores import CorRGBA
from src.renderizacao.geometria import GeometriaQR
from src.schemas.personalizacao import Forma

DIMENSAO_OLHO = 7


@dataclass(frozen=True, slots=True)
class EstiloOlhos:
    forma_exterior: Forma
    forma_interior: Forma
    cor_exterior: CorRGBA
    cor_interior: CorRGBA

    def __post_init__(self) -> None:
        formas = ("square", "rounded", "dots")

        if self.forma_exterior not in formas:
            raise ErroDadosInvalidos()

        if self.forma_interior not in formas:
            raise ErroDadosInvalidos()

        if self.cor_exterior.alfa != 255 or self.cor_interior.alfa != 255:
            raise ErroDadosInvalidos()


@dataclass(frozen=True, slots=True)
class RegiaoOlho:
    x: int
    y: int
    dimensao: int
    raio: float = 0.0

    @property
    def caixa(self) -> tuple[int, int, int, int]:
        return (
            self.x,
            self.y,
            self.x + self.dimensao,
            self.y + self.dimensao,
        )


@dataclass(frozen=True, slots=True)
class GeometriaOlho:
    exterior: RegiaoOlho
    abertura: RegiaoOlho
    interior: RegiaoOlho


def posicoes_olhos(
    dimensao_matriz: int,
) -> tuple[tuple[int, int], ...]:
    ultima = dimensao_matriz - DIMENSAO_OLHO

    return (
        (0, 0),
        (0, ultima),
        (ultima, 0),
    )


def pertence_a_olho(
    linha: int,
    coluna: int,
    dimensao_matriz: int,
) -> bool:
    return any(
        inicio_linha <= linha < inicio_linha + DIMENSAO_OLHO
        and inicio_coluna <= coluna < inicio_coluna + DIMENSAO_OLHO
        for inicio_linha, inicio_coluna in posicoes_olhos(dimensao_matriz)
    )


def calcular_raio(
    forma: Forma,
    dimensao: int,
    escala: int,
) -> float:
    if forma == "square":
        return 0.0

    if forma == "rounded":
        return min(
            escala * 1.25,
            dimensao / 2,
        )

    if forma == "dots":
        return dimensao / 2

    raise ErroDadosInvalidos()


def calcular_geometria_olhos(
    geometria: GeometriaQR,
    estilo: EstiloOlhos,
) -> tuple[GeometriaOlho, ...]:
    olhos = []
    escala = geometria.escala

    for linha, coluna in posicoes_olhos(geometria.dimensao_matriz):
        x, y, _, _ = geometria.caixa_modulo(
            linha,
            coluna,
        )

        raio_exterior = calcular_raio(
            estilo.forma_exterior,
            7 * escala,
            escala,
        )

        raio_abertura = max(
            0.0,
            raio_exterior - escala,
        )

        raio_interior = calcular_raio(
            estilo.forma_interior,
            3 * escala,
            escala,
        )

        olhos.append(
            GeometriaOlho(
                exterior=RegiaoOlho(
                    x=x,
                    y=y,
                    dimensao=7 * escala,
                    raio=raio_exterior,
                ),
                abertura=RegiaoOlho(
                    x=x + escala,
                    y=y + escala,
                    dimensao=5 * escala,
                    raio=raio_abertura,
                ),
                interior=RegiaoOlho(
                    x=x + 2 * escala,
                    y=y + 2 * escala,
                    dimensao=3 * escala,
                    raio=raio_interior,
                ),
            )
        )

    return tuple(olhos)
