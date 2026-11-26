from PIL import Image, ImageDraw

from src.renderizacao.composicao import (
    aplicar_preenchimento,
)
from src.renderizacao.geometria import GeometriaQR
from src.renderizacao.gradientes import (
    GeometriaGradiente,
)
from src.renderizacao.olhos import (
    EstiloOlhos,
    RegiaoOlho,
    calcular_geometria_olhos,
)
from src.renderizacao.preenchimentos import (
    PreenchimentosOlhos,
    PreenchimentoVisual,
)


def deslocar_regiao(
    regiao: RegiaoOlho,
    x: int,
    y: int,
) -> RegiaoOlho:
    return RegiaoOlho(
        x=regiao.x - x,
        y=regiao.y - y,
        dimensao=regiao.dimensao,
        raio=regiao.raio,
    )


def desenhar_regiao(
    desenho: ImageDraw.ImageDraw,
    regiao: RegiaoOlho,
    valor: int,
) -> None:
    x1, y1, x2, y2 = regiao.caixa

    caixa = (
        x1,
        y1,
        x2 - 1,
        y2 - 1,
    )

    if regiao.raio == 0:
        desenho.rectangle(caixa, fill=valor)

    elif regiao.raio >= regiao.dimensao / 2:
        desenho.ellipse(caixa, fill=valor)

    else:
        desenho.rounded_rectangle(
            caixa,
            radius=round(regiao.raio),
            fill=valor,
        )


def geometria_regiao(
    regiao: RegiaoOlho,
) -> GeometriaGradiente:
    return GeometriaGradiente(
        largura=regiao.dimensao,
        altura=regiao.dimensao,
        origem_x=regiao.x,
        origem_y=regiao.y,
    )


def aplicar_regiao(
    camada: Image.Image,
    regiao: RegiaoOlho,
    preenchimento: PreenchimentoVisual,
    geometria_global: GeometriaGradiente,
    abertura: RegiaoOlho | None = None,
) -> None:
    with Image.new("L", camada.size, 0) as mascara:
        desenho = ImageDraw.Draw(mascara)

        desenhar_regiao(
            desenho,
            regiao,
            255,
        )

        if abertura is not None:
            desenhar_regiao(
                desenho,
                abertura,
                0,
            )

        geometria = preenchimento.resolver_geometria(
            local=geometria_regiao(regiao),
            global_=geometria_global,
        )

        aplicar_preenchimento(
            imagem=camada,
            mascara=mascara,
            preenchimento=preenchimento.valor,
            geometria=geometria,
        )


def renderizar_olhos_png(
    imagem: Image.Image,
    geometria: GeometriaQR,
    estilo: EstiloOlhos,
    preenchimentos: PreenchimentosOlhos,
) -> None:
    dimensao_matriz = geometria.dimensao_matriz * geometria.escala

    for olho in calcular_geometria_olhos(
        geometria,
        estilo,
    ):
        x = olho.exterior.x
        y = olho.exterior.y

        dimensao = olho.exterior.dimensao

        exterior = deslocar_regiao(olho.exterior, x, y)

        abertura = deslocar_regiao(olho.abertura, x, y)

        interior = deslocar_regiao(olho.interior, x, y)

        geometria_global = GeometriaGradiente(
            largura=dimensao_matriz,
            altura=dimensao_matriz,
            origem_x=geometria.origem_x - x,
            origem_y=geometria.origem_y - y,
        )

        with Image.new(
            "RGBA",
            (dimensao, dimensao),
            (0, 0, 0, 0),
        ) as camada:
            aplicar_regiao(
                camada=camada,
                regiao=exterior,
                preenchimento=preenchimentos.exterior,
                geometria_global=geometria_global,
                abertura=abertura,
            )

            aplicar_regiao(
                camada=camada,
                regiao=interior,
                preenchimento=preenchimentos.interior,
                geometria_global=geometria_global,
            )

            imagem.alpha_composite(
                camada,
                dest=(x, y),
            )
