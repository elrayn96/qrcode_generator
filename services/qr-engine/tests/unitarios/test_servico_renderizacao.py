import pytest
from src.core.excecoes import ErroDadosInvalidos
from src.schemas.pedido import PedidoRenderizacao
from src.servicos.renderizacao import renderizar


@pytest.mark.parametrize(
    ("formato", "media_type"),
    [
        ("png", "image/png"),
        ("svg", "image/svg+xml"),
    ],
)
def test_renderizacao_por_formato(formato, media_type):
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "https://example.com",
            "output": {"format": formato},
        }
    )

    resultado = renderizar(pedido)

    assert resultado.media_type == media_type
    assert resultado.extensao == formato
    assert resultado.tamanho_bytes > 0


def test_renderizacao_padrao():
    pedido = PedidoRenderizacao(content="example")

    resultado = renderizar(pedido)

    assert resultado.largura == 512
    assert resultado.altura == 512


def test_renderizacao_personalizada():
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "example",
            "output": {
                "format": "svg",
                "size": 1024,
                "margin": 8,
            },
            "style": {
                "modules": {
                    "color": "#7C3AED",
                },
                "background": {
                    "color": "#FFFFFF",
                },
            },
        }
    )

    resultado = renderizar(pedido)

    assert resultado.largura == 1024
    assert b"#7C3AED" in resultado.dados


def test_rejeitar_forma_ainda_nao_suportada():
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "example",
            "style": {
                "modules": {"shape": "rounded"},
            },
        }
    )

    with pytest.raises(ErroDadosInvalidos):
        renderizar(pedido)


def test_rejeitar_modulos_translucidos():
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "example",
            "style": {
                "modules": {"color": "#00000080"},
            },
        }
    )

    with pytest.raises(ErroDadosInvalidos):
        renderizar(pedido)


def test_resultado_nao_expoe_bytes():
    resultado = renderizar(PedidoRenderizacao(content="example"))

    assert "dados=" not in repr(resultado)
