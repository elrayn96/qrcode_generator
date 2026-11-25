from dataclasses import dataclass

from src.core.excecoes import ErroDimensaoQR


@dataclass(frozen=True, slots=True)
class GeometriaQR:
    dimensao_imagem: int
    dimensao_matriz: int
    margem: int
    escala: int
    origem_x: int
    origem_y: int

    @property
    def dimensao_qr(self) -> int:
        return self.dimensao_matriz * self.escala

    @property
    def margem_pixels(self) -> int:
        return self.margem * self.escala

    def caixa_modulo(
        self,
        linha: int,
        coluna: int,
    ) -> tuple[int, int, int, int]:
        if not (0 <= linha < self.dimensao_matriz and 0 <= coluna < self.dimensao_matriz):
            raise IndexError("Coordenadas fora da matriz")

        x = self.origem_x + coluna * self.escala
        y = self.origem_y + linha * self.escala

        return (
            x,
            y,
            x + self.escala,
            y + self.escala,
        )


def calcular_geometria(
    dimensao_matriz: int,
    dimensao_imagem: int,
    margem: int = 4,
) -> GeometriaQR:
    if (
        type(dimensao_matriz) is not int
        or type(dimensao_imagem) is not int
        or type(margem) is not int
    ):
        raise ErroDimensaoQR()

    if not 21 <= dimensao_matriz <= 177 or (dimensao_matriz - 21) % 4 != 0:
        raise ErroDimensaoQR()

    if not 128 <= dimensao_imagem <= 2048:
        raise ErroDimensaoQR()

    if not 4 <= margem <= 32:
        raise ErroDimensaoQR()

    total_modulos = dimensao_matriz + 2 * margem

    escala = dimensao_imagem // total_modulos

    if escala < 1:
        raise ErroDimensaoQR()

    dimensao_ocupada = total_modulos * escala
    espaco_residual = dimensao_imagem - dimensao_ocupada

    deslocamento = espaco_residual // 2

    origem = deslocamento + margem * escala

    return GeometriaQR(
        dimensao_imagem=dimensao_imagem,
        dimensao_matriz=dimensao_matriz,
        margem=margem,
        escala=escala,
        origem_x=origem,
        origem_y=origem,
    )
