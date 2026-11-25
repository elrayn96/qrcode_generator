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


@pytest.mark.parametrize(
    "forma",
    ["square", "rounded", "dots"],
)
@pytest.mark.parametrize(
    "formato",
    ["png", "svg"],
)
def test_renderizacao_formas(forma, formato):
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "https://example.com",
            "output": {
                "format": formato,
                "size": 512,
            },
            "style": {
                "modules": {
                    "shape": forma,
                    "color": "#7C3AED",
                },
            },
        }
    )

    resultado = renderizar(pedido)

    assert resultado.extensao == formato
    assert resultado.tamanho_bytes > 0
    assert resultado.largura == 512


@pytest.mark.parametrize(
    "formato",
    ["png", "svg"],
)
def test_forma_padrao_preservada(formato):
    padrao = PedidoRenderizacao.model_validate(
        {
            "content": "example",
            "output": {"format": formato},
        }
    )

    explicito = PedidoRenderizacao.model_validate(
        {
            "content": "example",
            "output": {"format": formato},
            "style": {
                "modules": {
                    "shape": "square",
                }
            },
        }
    )

    assert renderizar(padrao).dados == renderizar(explicito).dados


def test_gradiente_ainda_nao_suportado():
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "example",
            "style": {
                "modules": {
                    "gradient": {
                        "type": "linear",
                        "stops": [
                            {
                                "position": 0.0,
                                "color": "#000000",
                            },
                            {
                                "position": 1.0,
                                "color": "#7C3AED",
                            },
                        ],
                    },
                },
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
