import pytest
from src.renderizacao.formas import calcular_forma


def test_forma_quadrada():
    forma = calcular_forma(10, 20, 20, "square")

    assert forma.x == 10
    assert forma.y == 20
    assert forma.largura == 20
    assert forma.altura == 20
    assert forma.raio == 0


def test_forma_arredondada():
    forma = calcular_forma(10, 20, 20, "rounded")

    assert forma.x == 10
    assert forma.y == 20
    assert forma.largura == 20
    assert forma.altura == 20
    assert forma.raio == pytest.approx(4)


def test_forma_circular():
    forma = calcular_forma(10, 20, 20, "dots")

    assert forma.x == pytest.approx(11)
    assert forma.y == pytest.approx(21)
    assert forma.largura == pytest.approx(18)
    assert forma.altura == pytest.approx(18)
    assert forma.raio == pytest.approx(9)


@pytest.mark.parametrize(
    "forma",
    ["square", "rounded", "dots"],
)
@pytest.mark.parametrize(
    "escala",
    [1, 4, 10, 17, 40],
)
def test_forma_dentro_da_celula(forma, escala):
    geometria = calcular_forma(
        10,
        10,
        escala,
        forma,
    )

    assert geometria.x >= 10
    assert geometria.y >= 10

    assert geometria.x + geometria.largura <= 10 + escala + 1e-9

    assert geometria.y + geometria.altura <= 10 + escala + 1e-9


@pytest.mark.parametrize("escala", [0, -1])
def test_escala_invalida(escala):
    with pytest.raises(ValueError):
        calcular_forma(0, 0, escala, "square")


def test_forma_invalida():
    with pytest.raises(ValueError):
        calcular_forma(0, 0, 10, "triangle")
