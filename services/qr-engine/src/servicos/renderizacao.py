from src.core.excecoes import ErroDadosInvalidos
from src.motor.matriz import gerar_matriz
from src.renderizacao.estilos import resolver_estilo
from src.renderizacao.png import renderizar_png
from src.renderizacao.resultado import ResultadoRenderizacao
from src.renderizacao.svg import renderizar_svg
from src.schemas.pedido import PedidoRenderizacao


def validar_estilo_suportado(
    pedido: PedidoRenderizacao,
) -> None:
    estilo = pedido.style

    if estilo.logo is not None or estilo.frame is not None:
        raise ErroDadosInvalidos()


def renderizar(
    pedido: PedidoRenderizacao,
) -> ResultadoRenderizacao:
    validar_estilo_suportado(pedido)

    estilo = resolver_estilo(pedido)

    matriz = gerar_matriz(
        conteudo=pedido.content,
        correcao_erros=pedido.options.errorCorrection,
    )

    renderizador = renderizar_svg if pedido.output.format == "svg" else renderizar_png

    return renderizador(
        matriz=matriz,
        tamanho=pedido.output.size,
        margem=pedido.output.margin,
        estilo=estilo,
    )
