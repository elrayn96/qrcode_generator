import pytest
from pydantic import ValidationError
from src.schemas.pedido import PedidoRenderizacao


def test_pedido_minimo():
    pedido = PedidoRenderizacao(
        content="https://example.com",
    )

    assert pedido.content == "https://example.com"
    assert pedido.output.format == "png"
    assert pedido.output.size == 512
    assert pedido.output.margin == 4
    assert pedido.options.errorCorrection == "M"


def test_pedido_personalizado():
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "https://example.com",
            "output": {
                "format": "svg",
                "size": 1024,
                "margin": 8,
            },
            "options": {
                "errorCorrection": "H",
            },
            "style": {
                "modules": {
                    "shape": "rounded",
                    "color": "#7C3AED",
                },
            },
        }
    )

    assert pedido.output.format == "svg"
    assert pedido.output.size == 1024
    assert pedido.output.margin == 8
    assert pedido.options.errorCorrection == "H"
    assert pedido.style.modules.shape == "rounded"


@pytest.mark.parametrize(
    "conteudo",
    ["", "a" * 4097, None, 123],
)
def test_conteudo_invalido(conteudo):
    with pytest.raises(ValidationError):
        PedidoRenderizacao.model_validate({"content": conteudo})


@pytest.mark.parametrize("tamanho", [128, 512, 2048])
def test_dimensoes_validas(tamanho):
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "example",
            "output": {"size": tamanho},
        }
    )

    assert pedido.output.size == tamanho


@pytest.mark.parametrize(
    "tamanho",
    [-1, 0, 127, 2049, 999999999, "512", True],
)
def test_dimensoes_invalidas(tamanho):
    with pytest.raises(ValidationError):
        PedidoRenderizacao.model_validate(
            {
                "content": "example",
                "output": {"size": tamanho},
            }
        )


@pytest.mark.parametrize("margem", [-1, 0, 3, 33])
def test_margens_invalidas(margem):
    with pytest.raises(ValidationError):
        PedidoRenderizacao.model_validate(
            {
                "content": "example",
                "output": {"margin": margem},
            }
        )


@pytest.mark.parametrize(
    "formato",
    ["pdf", "jpg", "exe"],
)
def test_formatos_invalidos(formato):
    with pytest.raises(ValidationError):
        PedidoRenderizacao.model_validate(
            {
                "content": "example",
                "output": {"format": formato},
            }
        )


@pytest.mark.parametrize("nivel", ["L", "M", "Q", "H"])
def test_correcao_erros(nivel):
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "example",
            "options": {"errorCorrection": nivel},
        }
    )

    assert pedido.options.errorCorrection == nivel


def test_correcao_erro_invalida():
    with pytest.raises(ValidationError):
        PedidoRenderizacao.model_validate(
            {
                "content": "example",
                "options": {"errorCorrection": "X"},
            }
        )


def test_pedido_sem_conteudo():
    with pytest.raises(ValidationError):
        PedidoRenderizacao.model_validate({})


def test_limite_conteudo():
    pedido = PedidoRenderizacao(
        content="a" * 4096,
    )

    assert len(pedido.content) == 4096
