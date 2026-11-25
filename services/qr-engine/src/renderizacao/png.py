from io import BytesIO

from PIL import Image, ImageDraw

from src.core.excecoes import ErroDimensaoQR
from src.motor.matriz import MatrizQR
from src.renderizacao.cores import BRANCO, PRETO, CorRGBA
from src.renderizacao.formas import (
    ESCALA_MINIMA_PERSONALIZACAO,
    calcular_forma,
)
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.modulos import (
    ModuloVisual,
    iterar_modulos_escuros,
)
from src.renderizacao.resultado import ResultadoRenderizacao
from src.schemas.personalizacao import Forma


def desenhar_modulo(
    desenho: ImageDraw.ImageDraw,
    modulo: ModuloVisual,
    cor: CorRGBA,
) -> None:
    geometria = calcular_forma(
        modulo.x,
        modulo.y,
        modulo.escala,
        modulo.forma,
    )

    x1 = round(geometria.x)
    y1 = round(geometria.y)

    x2 = round(geometria.x + geometria.largura) - 1

    y2 = round(geometria.y + geometria.altura) - 1

    caixa = (x1, y1, x2, y2)
    preenchimento = cor.como_tuplo()

    if modulo.forma == "square":
        desenho.rectangle(
            caixa,
            fill=preenchimento,
        )

    elif modulo.forma == "rounded":
        desenho.rounded_rectangle(
            caixa,
            radius=round(geometria.raio),
            fill=preenchimento,
        )

    elif modulo.forma == "dots":
        desenho.ellipse(
            caixa,
            fill=preenchimento,
        )


def renderizar_png(
    matriz: MatrizQR,
    tamanho: int = 512,
    margem: int = 4,
    cor_modulos: CorRGBA = PRETO,
    cor_fundo: CorRGBA = BRANCO,
    forma: Forma = "square",
) -> ResultadoRenderizacao:
    geometria = calcular_geometria(
        dimensao_matriz=matriz.dimensao,
        dimensao_imagem=tamanho,
        margem=margem,
    )

    if forma != "square" and geometria.escala < ESCALA_MINIMA_PERSONALIZACAO:
        raise ErroDimensaoQR()

    with Image.new(
        "RGBA",
        (tamanho, tamanho),
        cor_fundo.como_tuplo(),
    ) as imagem:
        desenho = ImageDraw.Draw(imagem)

        for modulo in iterar_modulos_escuros(
            matriz,
            geometria,
            forma,
        ):
            desenhar_modulo(
                desenho,
                modulo,
                cor_modulos,
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
