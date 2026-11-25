from io import BytesIO

from PIL import Image, ImageDraw

from src.core.excecoes import ErroDimensaoQR
from src.motor.matriz import MatrizQR
from src.renderizacao.cores import BRANCO, PRETO, CorRGBA
from src.renderizacao.formas import (
    ESCALA_MINIMA_PERSONALIZACAO,
    calcular_forma,
)
from src.renderizacao.geometria import GeometriaQR, calcular_geometria
from src.renderizacao.modulos import (
    ModuloVisual,
    iterar_modulos_escuros,
)
from src.renderizacao.olhos import (
    EstiloOlhos,
    RegiaoOlho,
    calcular_geometria_olhos,
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


def desenhar_regiao_olho(
    desenho: ImageDraw.ImageDraw,
    regiao: RegiaoOlho,
    preenchimento: int,
) -> None:
    x1, y1, x2, y2 = regiao.caixa

    caixa = (
        x1,
        y1,
        x2 - 1,
        y2 - 1,
    )

    if regiao.raio == 0:
        desenho.rectangle(
            caixa,
            fill=preenchimento,
        )

    elif regiao.raio >= regiao.dimensao / 2:
        desenho.ellipse(
            caixa,
            fill=preenchimento,
        )

    else:
        desenho.rounded_rectangle(
            caixa,
            radius=round(regiao.raio),
            fill=preenchimento,
        )


def desenhar_olhos_png(
    imagem: Image.Image,
    geometria: GeometriaQR,
    estilo: EstiloOlhos,
) -> None:
    for olho in calcular_geometria_olhos(
        geometria,
        estilo,
    ):
        dimensao = olho.exterior.dimensao

        origem = (
            olho.exterior.x,
            olho.exterior.y,
        )

        exterior = RegiaoOlho(
            x=0,
            y=0,
            dimensao=dimensao,
            raio=olho.exterior.raio,
        )

        abertura = RegiaoOlho(
            x=geometria.escala,
            y=geometria.escala,
            dimensao=olho.abertura.dimensao,
            raio=olho.abertura.raio,
        )

        interior = RegiaoOlho(
            x=2 * geometria.escala,
            y=2 * geometria.escala,
            dimensao=olho.interior.dimensao,
            raio=olho.interior.raio,
        )

        with Image.new("L", (dimensao, dimensao), 0) as mascara:
            desenho = ImageDraw.Draw(mascara)

            desenhar_regiao_olho(desenho, exterior, 255)

            desenhar_regiao_olho(desenho, abertura, 0)

            imagem.paste(
                estilo.cor_exterior.como_tuplo(),
                origem
                + (
                    origem[0] + dimensao,
                    origem[1] + dimensao,
                ),
                mascara,
            )

        with Image.new("L", (dimensao, dimensao), 0) as mascara:
            desenho = ImageDraw.Draw(mascara)

            desenhar_regiao_olho(desenho, interior, 255)

            imagem.paste(
                estilo.cor_interior.como_tuplo(),
                origem
                + (
                    origem[0] + dimensao,
                    origem[1] + dimensao,
                ),
                mascara,
            )


def renderizar_png(
    matriz: MatrizQR,
    tamanho: int = 512,
    margem: int = 4,
    cor_modulos: CorRGBA = PRETO,
    cor_fundo: CorRGBA = BRANCO,
    forma: Forma = "square",
    olhos: EstiloOlhos | None = None,
) -> ResultadoRenderizacao:
    geometria = calcular_geometria(
        dimensao_matriz=matriz.dimensao,
        dimensao_imagem=tamanho,
        margem=margem,
    )

    personalizacao_curva = forma != "square" or (
        olhos is not None and (olhos.forma_exterior != "square" or olhos.forma_interior != "square")
    )

    if personalizacao_curva and geometria.escala < ESCALA_MINIMA_PERSONALIZACAO:
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
            excluir_olhos=olhos is not None,
        ):
            desenhar_modulo(
                desenho,
                modulo,
                cor_modulos,
            )

        if olhos is not None:
            desenhar_olhos_png(
                imagem,
                geometria,
                olhos,
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
