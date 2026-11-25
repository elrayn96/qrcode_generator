import pytest
from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.cores import PRETO, converter_cor
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.olhos import (
    EstiloOlhos,
    calcular_geometria_olhos,
    pertence_a_olho,
    posicoes_olhos,
)


def criar_estilo(
    exterior="square",
    interior="square",
):
    return EstiloOlhos(
        forma_exterior=exterior,
        forma_interior=interior,
        cor_exterior=PRETO,
        cor_interior=PRETO,
    )


@pytest.mark.parametrize("dimensao", [21, 25, 29, 57, 177])
def test_posicoes_olhos(dimensao):
    assert posicoes_olhos(dimensao) == (
        (0, 0),
        (0, dimensao - 7),
        (dimensao - 7, 0),
    )


@pytest.mark.parametrize("dimensao", [21, 25, 177])
def test_area_total_olhos(dimensao):
    quantidade = sum(
        pertence_a_olho(linha, coluna, dimensao)
        for linha in range(dimensao)
        for coluna in range(dimensao)
    )

    assert quantidade == 3 * 49


@pytest.mark.parametrize(
    ("linha", "coluna"),
    [(7, 0), (0, 7), (7, 7), (20, 20)],
)
def test_preservar_regioes_externas(linha, coluna):
    assert not pertence_a_olho(linha, coluna, 21)


@pytest.mark.parametrize("exterior", ["square", "rounded", "dots"])
@pytest.mark.parametrize("interior", ["square", "rounded", "dots"])
def test_geometria_olhos(exterior, interior):
    geometria = calcular_geometria(21, 512)
    estilo = criar_estilo(exterior, interior)

    olhos = calcular_geometria_olhos(geometria, estilo)

    assert len(olhos) == 3

    for olho in olhos:
        assert olho.exterior.dimensao == 7 * geometria.escala
        assert olho.abertura.dimensao == 5 * geometria.escala
        assert olho.interior.dimensao == 3 * geometria.escala

        assert olho.abertura.x == (olho.exterior.x + geometria.escala)

        assert olho.interior.x == (olho.exterior.x + 2 * geometria.escala)

        assert olho.abertura.y == (olho.exterior.y + geometria.escala)

        assert olho.interior.y == (olho.exterior.y + 2 * geometria.escala)


def test_raio_olho_quadrado():
    geometria = calcular_geometria(21, 512)

    olhos = calcular_geometria_olhos(
        geometria,
        criar_estilo(),
    )

    for olho in olhos:
        assert olho.exterior.raio == 0
        assert olho.interior.raio == 0
        assert olho.abertura.raio == 0


def test_raio_olho_circular():
    geometria = calcular_geometria(21, 512)

    olhos = calcular_geometria_olhos(
        geometria,
        criar_estilo("dots", "dots"),
    )

    for olho in olhos:
        assert olho.exterior.raio == (olho.exterior.dimensao / 2)

        assert olho.interior.raio == (olho.interior.dimensao / 2)


def test_rejeitar_olhos_translucidos():
    with pytest.raises(ErroDadosInvalidos):
        EstiloOlhos(
            forma_exterior="square",
            forma_interior="square",
            cor_exterior=converter_cor("#00000080"),
            cor_interior=PRETO,
        )
