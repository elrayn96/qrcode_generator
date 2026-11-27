from contextlib import ExitStack
from io import BytesIO

from PIL import Image, ImageDraw

from src.motor.matriz import MatrizQR
from src.renderizacao.composicao import aplicar_preenchimento
from src.renderizacao.cores import BRANCO, PRETO, CorRGBA
from src.renderizacao.estilos import (
    EstiloRenderizacao,
    criar_estilo_convencional,
    validar_escala,
)
from src.renderizacao.formas import (
    calcular_forma,
)
from src.renderizacao.fundo import (
    renderizar_fundo_png,
)
from src.renderizacao.geometria import (
    GeometriaQR,
    calcular_geometria,
)
from src.renderizacao.gradientes import (
    GeometriaGradiente,
    Gradiente,
)
from src.renderizacao.logotipos import calcular_geometria_logotipo
from src.renderizacao.logotipos_png import (
    guardar_fundo_logotipo,
    renderizar_logotipo_png,
)
from src.renderizacao.modulos import (
    ModuloVisual,
    iterar_modulos_escuros,
)
from src.renderizacao.olhos import EstiloOlhos
from src.renderizacao.olhos_png import renderizar_olhos_png
from src.renderizacao.resultado import ResultadoRenderizacao
from src.schemas.personalizacao import Forma, Logotipo
from src.seguranca.logotipos import carregar_logotipo


def desenhar_modulo(
    desenho: ImageDraw.ImageDraw,
    modulo: ModuloVisual,
    cor: CorRGBA | int,
) -> None:
    geometria = calcular_forma(
        modulo.x,
        modulo.y,
        modulo.escala,
        modulo.forma,
    )

    caixa = (
        round(geometria.x),
        round(geometria.y),
        round(geometria.x + geometria.largura) - 1,
        round(geometria.y + geometria.altura) - 1,
    )

    preenchimento = cor.como_tuplo() if isinstance(cor, CorRGBA) else cor

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


def criar_mascara_modulos(
    matriz: MatrizQR,
    geometria: GeometriaQR,
    estilo: EstiloRenderizacao,
) -> Image.Image:
    tamanho = geometria.dimensao_imagem

    mascara = Image.new(
        "L",
        (tamanho, tamanho),
        0,
    )

    desenho = ImageDraw.Draw(mascara)

    for modulo in iterar_modulos_escuros(
        matriz,
        geometria,
        estilo.forma,
        excluir_olhos=estilo.requer_olhos_independentes,
    ):
        desenhar_modulo(
            desenho=desenho,
            modulo=modulo,
            cor=255,
        )

    return mascara


def desenhar_modulos_png(
    imagem: Image.Image,
    matriz: MatrizQR,
    geometria: GeometriaQR,
    estilo: EstiloRenderizacao,
) -> None:
    preenchimento = estilo.modulos.valor

    # Caminho optimizado para cores sólidas.
    if not isinstance(preenchimento, Gradiente):
        desenho = ImageDraw.Draw(imagem)

        cor = CorRGBA(*preenchimento)

        for modulo in iterar_modulos_escuros(
            matriz,
            geometria,
            estilo.forma,
            excluir_olhos=estilo.requer_olhos_independentes,
        ):
            desenhar_modulo(
                desenho,
                modulo,
                cor,
            )

        return

    dimensao = geometria.dimensao_matriz * geometria.escala

    geometria_gradiente = GeometriaGradiente(
        largura=dimensao,
        altura=dimensao,
        origem_x=geometria.origem_x,
        origem_y=geometria.origem_y,
    )

    with criar_mascara_modulos(
        matriz,
        geometria,
        estilo,
    ) as mascara:
        aplicar_preenchimento(
            imagem=imagem,
            mascara=mascara,
            preenchimento=preenchimento,
            geometria=geometria_gradiente,
        )


def renderizar_png(
    matriz: MatrizQR,
    tamanho: int = 512,
    margem: int = 4,
    cor_modulos: CorRGBA = PRETO,
    cor_fundo: CorRGBA = BRANCO,
    forma: Forma = "square",
    olhos: EstiloOlhos | None = None,
    *,
    estilo: EstiloRenderizacao | None = None,
    logotipo: Logotipo | None = None,
) -> ResultadoRenderizacao:
    estilo = estilo or criar_estilo_convencional(
        cor_modulos,
        cor_fundo,
        forma,
        olhos,
    )

    geometria = calcular_geometria(
        dimensao_matriz=matriz.dimensao,
        dimensao_imagem=tamanho,
        margem=margem,
    )

    validar_escala(
        geometria,
        estilo,
    )

    with ExitStack() as recursos:
        imagem_logotipo = None
        geometria_logotipo = None
        fundo_logotipo = None

        if logotipo is not None:
            imagem_logotipo = recursos.enter_context(
                carregar_logotipo(logotipo),
            )

            geometria_logotipo = calcular_geometria_logotipo(
                matriz,
                geometria,
                logotipo,
                imagem_logotipo.size,
            )

        imagem = recursos.enter_context(
            renderizar_fundo_png(
                largura=tamanho,
                altura=tamanho,
                estilo=estilo.fundo,
            ),
        )

        if geometria_logotipo is not None:
            fundo_logotipo = recursos.enter_context(
                guardar_fundo_logotipo(
                    imagem,
                    geometria_logotipo,
                ),
            )

        desenhar_modulos_png(
            imagem,
            matriz,
            geometria,
            estilo,
        )

        if (
            estilo.requer_olhos_independentes
            and estilo.olhos is not None
            and estilo.preenchimentos_olhos is not None
        ):
            renderizar_olhos_png(
                imagem=imagem,
                geometria=geometria,
                estilo=estilo.olhos,
                preenchimentos=estilo.preenchimentos_olhos,
            )

        if (
            imagem_logotipo is not None
            and geometria_logotipo is not None
            and fundo_logotipo is not None
        ):
            renderizar_logotipo_png(
                imagem=imagem,
                logotipo=imagem_logotipo,
                fundo=fundo_logotipo,
                geometria=geometria_logotipo,
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
