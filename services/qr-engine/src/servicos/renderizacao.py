from src.core.excecoes import ErroDadosInvalidos
from src.motor.matriz import gerar_matriz
from src.renderizacao.cores import (
    BRANCO,
    PRETO,
    TRANSPARENTE,
    CorRGBA,
    converter_cor,
)
from src.renderizacao.olhos import EstiloOlhos
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
    olhos = resolver_olhos(pedido, cor_modulos)

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
        olhos=olhos,
    )


def resolver_olhos(
    pedido: PedidoRenderizacao,
    cor_modulos: CorRGBA,
) -> EstiloOlhos | None:
    olhos = pedido.style.eyes

    if olhos is None:
        return None

    forma_exterior = "square"
    forma_interior = "square"

    cor_exterior = cor_modulos
    cor_interior = cor_modulos

    if olhos.outer is not None:
        forma_exterior = olhos.outer.shape or "square"

        if olhos.outer.color is not None:
            cor_exterior = converter_cor(olhos.outer.color)

    if olhos.inner is not None:
        forma_interior = olhos.inner.shape or "square"

        if olhos.inner.color is not None:
            cor_interior = converter_cor(olhos.inner.color)

    return EstiloOlhos(
        forma_exterior=forma_exterior,
        forma_interior=forma_interior,
        cor_exterior=cor_exterior,
        cor_interior=cor_interior,
    )
