from src.core.excecoes import ErroDadosInvalidos
from src.motor.matriz import gerar_matriz
from src.renderizacao.cores import (
    BRANCO,
    PRETO,
    TRANSPARENTE,
    CorRGBA,
    converter_cor,
)
from src.renderizacao.png import renderizar_png
from src.renderizacao.resultado import ResultadoRenderizacao
from src.renderizacao.svg import renderizar_svg
from src.schemas.pedido import PedidoRenderizacao
from src.schemas.personalizacao import Forma


def resolver_cores(
    pedido: PedidoRenderizacao,
) -> tuple[CorRGBA, CorRGBA]:
    cor_modulos = PRETO
    cor_fundo = BRANCO

    modulos = pedido.style.modules
    fundo = pedido.style.background

    if modulos is not None and modulos.color is not None:
        cor_modulos = converter_cor(modulos.color)

    if fundo is not None:
        if fundo.transparent is True:
            cor_fundo = TRANSPARENTE

        elif fundo.color is not None:
            cor_fundo = converter_cor(fundo.color)

    return cor_modulos, cor_fundo


def resolver_forma(
    pedido: PedidoRenderizacao,
) -> Forma:
    modulos = pedido.style.modules

    if modulos is None:
        return "square"

    return modulos.shape or "square"


def validar_estilo_suportado(
    pedido: PedidoRenderizacao,
) -> None:
    estilo = pedido.style

    if estilo.modules is not None and estilo.modules.gradient is not None:
        raise ErroDadosInvalidos()

    if estilo.background is not None and estilo.background.gradient is not None:
        raise ErroDadosInvalidos()

    if any(
        componente is not None
        for componente in (
            estilo.eyes,
            estilo.logo,
            estilo.frame,
        )
    ):
        raise ErroDadosInvalidos()


def renderizar(
    pedido: PedidoRenderizacao,
) -> ResultadoRenderizacao:
    validar_estilo_suportado(pedido)

    cor_modulos, cor_fundo = resolver_cores(pedido)
    forma = resolver_forma(pedido)

    if cor_modulos.alfa != 255:
        raise ErroDadosInvalidos()

    matriz = gerar_matriz(
        conteudo=pedido.content,
        correcao_erros=pedido.options.errorCorrection,
    )

    renderizador = renderizar_svg if pedido.output.format == "svg" else renderizar_png

    return renderizador(
        matriz=matriz,
        tamanho=pedido.output.size,
        margem=pedido.output.margin,
        cor_modulos=cor_modulos,
        cor_fundo=cor_fundo,
        forma=forma,
    )
