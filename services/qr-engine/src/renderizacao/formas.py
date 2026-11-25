from dataclasses import dataclass

from src.schemas.personalizacao import Forma

RAIO_ARREDONDAMENTO = 0.20
DIAMETRO_CIRCULO = 0.90

ESCALA_MINIMA_PERSONALIZACAO = 4


@dataclass(frozen=True, slots=True)
class GeometriaForma:
    x: float
    y: float
    largura: float
    altura: float
    raio: float = 0.0


def calcular_forma(
    x: int,
    y: int,
    escala: int,
    forma: Forma,
) -> GeometriaForma:
    """Calcula a geometria visual de um módulo."""

    if escala < 1:
        raise ValueError("Invalid module scale")

    if forma == "square":
        return GeometriaForma(
            x=x,
            y=y,
            largura=escala,
            altura=escala,
        )

    if forma == "rounded":
        return GeometriaForma(
            x=x,
            y=y,
            largura=escala,
            altura=escala,
            raio=escala * RAIO_ARREDONDAMENTO,
        )

    if forma == "dots":
        diametro = escala * DIAMETRO_CIRCULO
        deslocamento = (escala - diametro) / 2

        return GeometriaForma(
            x=x + deslocamento,
            y=y + deslocamento,
            largura=diametro,
            altura=diametro,
            raio=diametro / 2,
        )

    raise ValueError("Unsupported module shape")
