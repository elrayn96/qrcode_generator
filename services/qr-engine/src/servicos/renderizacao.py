from src.core.excecoes import ErroDadosInvalidos
from src.motor.matriz import gerar_matriz
from src.renderizacao.estilos import resolver_estilo
from src.renderizacao.molduras_png import aplicar_moldura_png
from src.renderizacao.molduras_svg import aplicar_moldura_svg
from src.renderizacao.png import renderizar_png
from src.renderizacao.resultado import ResultadoRenderizacao
from src.renderizacao.svg import renderizar_svg
from src.schemas.pedido import PedidoRenderizacao


def validar_estilo_suportado(pedido: PedidoRenderizacao) -> None:
    if pedido.style.logo is not None and pedido.options.errorCorrection != "H":
        raise ErroDadosInvalidos()


def renderizar(pedido: PedidoRenderizacao) -> ResultadoRenderizacao:
    validar_estilo_suportado(pedido)
    estilo = resolver_estilo(pedido)
    matriz = gerar_matriz(
        conteudo=pedido.content,
        correcao_erros=pedido.options.errorCorrection,
    )
    svg = pedido.output.format == "svg"
    renderizador = renderizar_svg if svg else renderizar_png
    resultado = renderizador(
        matriz=matriz,
        tamanho=pedido.output.size,
        margem=pedido.output.margin,
        estilo=estilo,
        logotipo=pedido.style.logo,
    )
    if pedido.style.frame is not None:
        aplicar = aplicar_moldura_svg if svg else aplicar_moldura_png
        return aplicar(resultado, pedido.style.frame)
    return resultado
