from dataclasses import dataclass
from math import cos, hypot, isfinite, radians, sin
from typing import Literal

from src.core.excecoes import ErroDadosInvalidos

TipoGradiente = Literal["linear", "radial"]
RGBA = tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class PontoCor:
    posicao: float
    cor: RGBA

    def __post_init__(self) -> None:
        if not 0 <= self.posicao <= 1:
            raise ErroDadosInvalidos()

        if len(self.cor) != 4:
            raise ErroDadosInvalidos()

        if any(
            not isinstance(c, int) or isinstance(c, bool) or not 0 <= c <= 255 for c in self.cor
        ):
            raise ErroDadosInvalidos()


@dataclass(frozen=True, slots=True)
class Gradiente:
    tipo: TipoGradiente
    pontos: tuple[PontoCor, ...]
    angulo: int = 0

    def __post_init__(self) -> None:
        if self.tipo not in ("linear", "radial"):
            raise ErroDadosInvalidos()

        if not 0 <= self.angulo <= 360:
            raise ErroDadosInvalidos()

        if not 2 <= len(self.pontos) <= 8:
            raise ErroDadosInvalidos()

        posicoes = [ponto.posicao for ponto in self.pontos]

        if any(
            anterior >= seguinte
            for anterior, seguinte in zip(
                posicoes[:-1],
                posicoes[1:],
                strict=True,
            )
        ):
            raise ErroDadosInvalidos()


def limitar_posicao(posicao: float) -> float:
    if not isfinite(posicao):
        raise ErroDadosInvalidos()

    return max(0.0, min(1.0, posicao))


def interpolar_cores(
    primeira: RGBA,
    segunda: RGBA,
    posicao: float,
) -> RGBA:
    t = limitar_posicao(posicao)

    r1, g1, b1, a1 = primeira
    r2, g2, b2, a2 = segunda

    return (
        round(r1 + (r2 - r1) * t),
        round(g1 + (g2 - g1) * t),
        round(b1 + (b2 - b1) * t),
        round(a1 + (a2 - a1) * t),
    )


def obter_cor(
    gradiente: Gradiente,
    posicao: float,
) -> RGBA:
    t = limitar_posicao(posicao)
    pontos = gradiente.pontos

    if t <= pontos[0].posicao:
        return pontos[0].cor

    if t >= pontos[-1].posicao:
        return pontos[-1].cor

    for anterior, seguinte in zip(
        pontos[:-1],
        pontos[1:],
        strict=True,
    ):
        if anterior.posicao <= t <= seguinte.posicao:
            intervalo = seguinte.posicao - anterior.posicao

            proporcao = (t - anterior.posicao) / intervalo

            return interpolar_cores(
                anterior.cor,
                seguinte.cor,
                proporcao,
            )

    raise ErroDadosInvalidos()


@dataclass(frozen=True, slots=True)
class GeometriaGradiente:
    largura: float
    altura: float
    origem_x: float = 0
    origem_y: float = 0

    def __post_init__(self) -> None:
        valores = (
            self.largura,
            self.altura,
            self.origem_x,
            self.origem_y,
        )

        if not all(map(isfinite, valores)):
            raise ErroDadosInvalidos()

        if self.largura <= 0 or self.altura <= 0:
            raise ErroDadosInvalidos()

    @property
    def centro(self) -> tuple[float, float]:
        return (
            self.origem_x + self.largura / 2,
            self.origem_y + self.altura / 2,
        )

    @property
    def raio(self) -> float:
        return hypot(
            self.largura / 2,
            self.altura / 2,
        )

    def extremos_lineares(
        self,
        angulo: int,
    ) -> tuple[float, float, float, float]:
        theta = radians(angulo % 360)

        dx = cos(theta)
        dy = sin(theta)

        cx, cy = self.centro

        alcance = (abs(dx) * self.largura + abs(dy) * self.altura) / 2

        return (
            cx - dx * alcance,
            cy - dy * alcance,
            cx + dx * alcance,
            cy + dy * alcance,
        )


def calcular_posicao(
    gradiente: Gradiente,
    geometria: GeometriaGradiente,
    x: float,
    y: float,
) -> float:
    if gradiente.tipo == "radial":
        cx, cy = geometria.centro

        return limitar_posicao(hypot(x - cx, y - cy) / geometria.raio)

    x1, y1, x2, y2 = geometria.extremos_lineares(gradiente.angulo)

    dx = x2 - x1
    dy = y2 - y1

    projecao = (x - x1) * dx + (y - y1) * dy

    comprimento_quadrado = dx**2 + dy**2

    return limitar_posicao(projecao / comprimento_quadrado)


def calcular_cor(
    gradiente: Gradiente,
    geometria: GeometriaGradiente,
    x: float,
    y: float,
) -> RGBA:
    posicao = calcular_posicao(
        gradiente,
        geometria,
        x,
        y,
    )

    return obter_cor(
        gradiente,
        posicao,
    )
