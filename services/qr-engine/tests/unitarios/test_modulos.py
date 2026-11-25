import pytest
from segno.consts import TYPE_DATA_DARK
from src.motor.matriz import gerar_matriz
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.modulos import (
    determinar_forma,
    iterar_modulos_escuros,
)


@pytest.mark.parametrize(
    "forma",
    ["square", "rounded", "dots"],
)
def test_forma_modulo_dados(forma):
    assert (
        determinar_forma(
            TYPE_DATA_DARK,
            forma,
        )
        == forma
    )


@pytest.mark.parametrize(
    "forma",
    ["square", "rounded", "dots"],
)
def test_padroes_funcionais_preservados(forma):
    matriz = gerar_matriz("https://example.com")

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    modulos = list(
        iterar_modulos_escuros(
            matriz,
            geometria,
            forma,
        )
    )

    funcionais = [modulo for modulo in modulos if modulo.funcional]

    assert funcionais

    assert all(modulo.forma == "square" for modulo in funcionais)


@pytest.mark.parametrize(
    "forma",
    ["square", "rounded", "dots"],
)
def test_personalizacao_modulos_dados(forma):
    matriz = gerar_matriz("example")

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    dados = [
        modulo
        for modulo in iterar_modulos_escuros(
            matriz,
            geometria,
            forma,
        )
        if not modulo.funcional
    ]

    assert dados

    assert all(modulo.forma == forma for modulo in dados)


def test_quantidade_modulos_preservada():
    matriz = gerar_matriz("example")

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    modulos = list(
        iterar_modulos_escuros(
            matriz,
            geometria,
            "dots",
        )
    )

    assert len(modulos) == matriz.modulos_escuros


def test_modulos_claros_nao_desenhados():
    matriz = gerar_matriz("example")

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    for modulo in iterar_modulos_escuros(
        matriz,
        geometria,
    ):
        assert matriz.modulo_escuro(
            modulo.linha,
            modulo.coluna,
        )


def test_coordenadas_modulos():
    matriz = gerar_matriz("example")

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    for modulo in iterar_modulos_escuros(
        matriz,
        geometria,
    ):
        assert modulo.x == (geometria.origem_x + modulo.coluna * geometria.escala)

        assert modulo.y == (geometria.origem_y + modulo.linha * geometria.escala)


def test_matriz_densa_preserva_padroes_funcionais():
    matriz = gerar_matriz("a" * 1000)

    geometria = calcular_geometria(
        matriz.dimensao,
        2048,
    )

    for modulo in iterar_modulos_escuros(
        matriz,
        geometria,
        "dots",
    ):
        tipo = matriz.tipo_modulo(
            modulo.linha,
            modulo.coluna,
        )

        if tipo != TYPE_DATA_DARK:
            assert modulo.forma == "square"
        else:
            assert modulo.forma == "dots"
