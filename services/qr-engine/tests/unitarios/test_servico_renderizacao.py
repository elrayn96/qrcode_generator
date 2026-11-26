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
            "content": "https://ntizoconnect.me",
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
            "content": "https://ntizoconnect.me",
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


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize("exterior", ["square", "rounded", "dots"])
@pytest.mark.parametrize("interior", ["square", "rounded", "dots"])
def test_personalizacao_olhos(
    formato,
    exterior,
    interior,
):
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "https://ntizoconnect.me",
            "output": {
                "format": formato,
                "size": 512,
            },
            "style": {
                "eyes": {
                    "outer": {
                        "shape": exterior,
                        "color": "#4C1D95",
                    },
                    "inner": {
                        "shape": interior,
                        "color": "#7C3AED",
                    },
                },
            },
        }
    )

    resultado = renderizar(pedido)

    assert resultado.extensao == formato
    assert resultado.tamanho_bytes > 0
    assert resultado.largura == 512


def test_olhos_herdam_cor_modulos():
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "example",
            "output": {"format": "svg"},
            "style": {
                "modules": {
                    "color": "#7C3AED",
                },
                "eyes": {
                    "outer": {
                        "shape": "rounded",
                    },
                    "inner": {
                        "shape": "dots",
                    },
                },
            },
        }
    )

    resultado = renderizar(pedido)

    from xml.etree.ElementTree import fromstring

    raiz = fromstring(resultado.dados)

    ns = "http://www.w3.org/2000/svg"

    grupo = raiz.find(f"{{{ns}}}g[@id='qr-eyes']")

    assert grupo is not None

    assert all(elemento.attrib["fill"] == "#7C3AED" for elemento in grupo)
