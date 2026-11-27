from dataclasses import dataclass

from segno.consts import TYPE_DATA_DARK, TYPE_DATA_LIGHT

from src.core.excecoes import ErroDadosInvalidos
from src.motor.matriz import MatrizQR
from src.renderizacao.geometria import GeometriaQR
from src.schemas.personalizacao import Logotipo

Caixa = tuple[int, int, int, int]
ESCALA_PADRAO = 0.15
PADDING_PADRAO = 1


@dataclass(frozen=True, slots=True)
class GeometriaLogotipo:
    caixa_imagem: Caixa
    caixa_protecao: Caixa


def calcular_geometria_logotipo(
    matriz: MatrizQR,
    geometria: GeometriaQR,
    logotipo: Logotipo,
    tamanho: tuple[int, int],
) -> GeometriaLogotipo:
    """Calcular caixas semiabertas em pixels, sem cobrir padrões funcionais."""
    largura, altura = tamanho
    if largura <= 0 or altura <= 0 or matriz.dimensao != geometria.dimensao_matriz:
        raise ErroDadosInvalidos()
    escala = logotipo.scale if logotipo.scale is not None else ESCALA_PADRAO
    padding = logotipo.padding if logotipo.padding is not None else PADDING_PADRAO
    lado = int(geometria.dimensao_qr * escala)
    if lado < 1:
        raise ErroDadosInvalidos()
    maior = max(largura, altura)
    w = max(1, largura * lado // maior)
    h = max(1, altura * lado // maior)
    x = geometria.origem_x + (geometria.dimensao_qr - w) // 2
    y = geometria.origem_y + (geometria.dimensao_qr - h) // 2
    p = padding * geometria.escala
    caixa = (x, y, x + w, y + h)
    protecao = (x - p, y - p, x + w + p, y + h + p)
    x0, y0, x1, y1 = protecao
    ox, oy = geometria.origem_x, geometria.origem_y
    n, s = matriz.dimensao, geometria.escala
    if x0 < ox or y0 < oy or x1 > ox + n * s or y1 > oy + n * s:
        raise ErroDadosInvalidos()
    for linha in range((y0 - oy) // s, (y1 - 1 - oy) // s + 1):
        for coluna in range((x0 - ox) // s, (x1 - 1 - ox) // s + 1):
            if matriz.tipo_modulo(linha, coluna) not in (TYPE_DATA_LIGHT, TYPE_DATA_DARK):
                raise ErroDadosInvalidos()
    return GeometriaLogotipo(caixa, protecao)
