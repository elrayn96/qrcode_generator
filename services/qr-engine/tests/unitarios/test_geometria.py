import pytest
from src.core.excecoes import ErroDimensaoQR
from src.renderizacao.geometria import calcular_geometria


def test_geometria_padrao():
    geometria = calcular_geometria(21, 512, 4)

    assert geometria.escala == 17
    assert geometria.dimensao_qr == 357
    assert geometria.margem_pixels == 68
    assert geometria.origem_x == 77
    assert geometria.origem_y == 77


@pytest.mark.parametrize("tamanho", [128, 256, 512, 1024, 2048])
def test_dimensoes_imagem(tamanho):
    geometria = calcular_geometria(21, tamanho)

    assert geometria.dimensao_imagem == tamanho
    assert geometria.escala >= 1


@pytest.mark.parametrize("margem", [4, 8, 16, 32])
def test_margem_minima_preservada(margem):
    geometria = calcular_geometria(21, 512, margem)

    margem_esquerda = geometria.origem_x

    margem_direita = geometria.dimensao_imagem - geometria.origem_x - geometria.dimensao_qr

    assert margem_esquerda >= geometria.margem_pixels
    assert margem_direita >= geometria.margem_pixels

    assert abs(margem_esquerda - margem_direita) <= 1


def test_dimensao_insuficiente():
    with pytest.raises(ErroDimensaoQR):
        calcular_geometria(177, 128, 4)


@pytest.mark.parametrize("margem", [0, 3, 33])
def test_margem_invalida(margem):
    with pytest.raises(ErroDimensaoQR):
        calcular_geometria(21, 512, margem)


@pytest.mark.parametrize("dimensao", [20, 22, 178])
def test_dimensao_matriz_invalida(dimensao):
    with pytest.raises(ErroDimensaoQR):
        calcular_geometria(dimensao, 512)


def test_coordenadas_primeiro_modulo():
    geometria = calcular_geometria(21, 512)

    assert geometria.caixa_modulo(0, 0) == (77, 77, 94, 94)


def test_modulos_nao_sobrepostos():
    geometria = calcular_geometria(21, 512)

    primeira = geometria.caixa_modulo(0, 0)
    segunda = geometria.caixa_modulo(0, 1)

    assert primeira[2] == segunda[0]


@pytest.mark.parametrize(
    ("linha", "coluna"),
    [(-1, 0), (0, -1), (21, 0), (0, 21)],
)
def test_coordenadas_invalidas(linha, coluna):
    geometria = calcular_geometria(21, 512)

    with pytest.raises(IndexError):
        geometria.caixa_modulo(linha, coluna)
