from io import BytesIO

from PIL import Image, ImageDraw

from src.motor.matriz import MatrizQR
from src.renderizacao.cores import (
    BRANCO,
    PRETO,
    CorRGBA,
)
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.resultado import ResultadoRenderizacao


def renderizar_png(
    matriz: MatrizQR,
    tamanho: int = 512,
    margem: int = 4,
    cor_modulos: CorRGBA = PRETO,
    cor_fundo: CorRGBA = BRANCO,
) -> ResultadoRenderizacao:
    geometria = calcular_geometria(
        dimensao_matriz=matriz.dimensao,
        dimensao_imagem=tamanho,
        margem=margem,
    )

    with Image.new(
        "RGBA",
        (tamanho, tamanho),
        cor_fundo.como_tuplo(),
    ) as imagem:
        desenho = ImageDraw.Draw(imagem)

        for linha, valores in enumerate(matriz.modulos):
            for coluna, valor in enumerate(valores):
                if valor == 0:
                    continue

                x1, y1, x2, y2 = geometria.caixa_modulo(
                    linha,
                    coluna,
                )

                desenho.rectangle(
                    (x1, y1, x2 - 1, y2 - 1),
                    fill=cor_modulos.como_tuplo(),
                )

        with BytesIO() as memoria:
            imagem.save(
                memoria,
                format="PNG",
                compress_level=6,
            )

            dados = memoria.getvalue()

    return ResultadoRenderizacao(
        dados=dados,
        media_type="image/png",
        largura=tamanho,
        altura=tamanho,
    )
