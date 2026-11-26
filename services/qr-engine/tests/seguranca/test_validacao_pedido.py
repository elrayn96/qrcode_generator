import pytest
from pydantic import ValidationError
from src.schemas.pedido import PedidoRenderizacao
from src.schemas.personalizacao import Logotipo


@pytest.mark.parametrize(
    "dados",
    [
        {"content": "ntizoconnect", "admin": True},
        {"content": "ntizoconnect", "role": "admin"},
        {"content": "ntizoconnect", "quota": -1},
        {
            "content": "ntizoconnect",
            "output": {"workers": 999},
        },
        {
            "content": "ntizoconnect",
            "style": {"unknown": True},
        },
    ],
)
def test_campos_desconhecidos(dados):
    with pytest.raises(ValidationError):
        PedidoRenderizacao.model_validate(dados)


@pytest.mark.parametrize(
    "dados",
    [
        {"content": None},
        {"content": "ntizoconnect", "output": None},
        {"content": "ntizoconnect", "options": None},
        {"content": "ntizoconnect", "style": None},
        {
            "content": "ntizoconnect",
            "style": {"modules": None},
        },
    ],
)
def test_valores_nulos(dados):
    with pytest.raises(ValidationError):
        PedidoRenderizacao.model_validate(dados)


def test_booleano_nao_aceite_como_inteiro():
    with pytest.raises(ValidationError):
        PedidoRenderizacao.model_validate(
            {
                "content": "ntizoconnect",
                "output": {"size": True},
            }
        )


def test_string_nao_aceite_como_booleano():
    with pytest.raises(ValidationError):
        PedidoRenderizacao.model_validate(
            {
                "content": "ntizoconnect",
                "style": {
                    "background": {
                        "transparent": "true",
                    },
                },
            }
        )


def test_conteudo_nao_exposto_na_representacao():
    pedido = PedidoRenderizacao(
        content="password-secreta-exemplo",
    )

    assert "password-secreta-exemplo" not in repr(pedido)


def test_logotipo_nao_exposto_na_representacao():
    logo = Logotipo(
        mediaType="image/png",
        base64="YWJj",
    )

    assert "YWJj" not in repr(logo)


def test_erro_nao_expoe_valor_original():
    segredo = "password-secreta-exemplo"

    with pytest.raises(ValidationError) as erro:
        PedidoRenderizacao.model_validate(
            {
                "content": "ntizoconnect",
                "output": {"size": segredo},
            }
        )

    assert segredo not in str(erro.value)
