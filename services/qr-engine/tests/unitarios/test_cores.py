import pytest
from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.cores import converter_cor


@pytest.mark.parametrize(
    ("hexadecimal", "esperado"),
    [
        ("#000000", (0, 0, 0, 255)),
        ("#FFFFFF", (255, 255, 255, 255)),
        ("#7C3AED", (124, 58, 237, 255)),
        ("#FF000080", (255, 0, 0, 128)),
        ("#00000000", (0, 0, 0, 0)),
        ("#ffffff", (255, 255, 255, 255)),
    ],
)
def test_converter_cor(hexadecimal, esperado):
    cor = converter_cor(hexadecimal)

    assert cor.como_tuplo() == esperado


@pytest.mark.parametrize(
    "valor",
    [
        "",
        "red",
        "#123",
        "#GGGGGG",
        "#1234567",
        None,
        123,
    ],
)
def test_cor_invalida(valor):
    with pytest.raises(ErroDadosInvalidos):
        converter_cor(valor)


def test_opacidade():
    cor = converter_cor("#FFFFFF80")

    assert cor.opacidade == pytest.approx(128 / 255)


def test_hexadecimal_normalizado():
    cor = converter_cor("#7c3aed80")

    assert cor.como_hex() == "#7C3AED"
