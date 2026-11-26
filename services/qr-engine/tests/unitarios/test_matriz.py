from dataclasses import FrozenInstanceError

import pytest
from segno.consts import (
    TYPE_DATA_DARK,
    TYPE_DATA_LIGHT,
    TYPE_FINDER_PATTERN_DARK,
    TYPE_FINDER_PATTERN_LIGHT,
)
from src.core.excecoes import (
    ErroCapacidadeQR,
    ErroCodificacaoQR,
    ErroDadosInvalidos,
)
from src.motor.matriz import MatrizQR, gerar_matriz


def test_gerar_matriz():
    matriz = gerar_matriz("https://ntizoconnect.me")

    assert isinstance(matriz, MatrizQR)
    assert matriz.dimensao >= 21
    assert matriz.correcao_erros == "M"


def test_dimensao_corresponde_versao():
    matriz = gerar_matriz("https://ntizoconnect.me")

    assert matriz.dimensao == 17 + 4 * matriz.versao


def test_matriz_quadrada():
    matriz = gerar_matriz("example")

    assert all(len(linha) == matriz.dimensao for linha in matriz.modulos)


def test_matriz_binaria():
    matriz = gerar_matriz("example")

    assert all(modulo in (0, 1) for linha in matriz.modulos for modulo in linha)


def test_contagem_modulos():
    matriz = gerar_matriz("example")

    assert matriz.total_modulos == matriz.dimensao**2
    assert matriz.modulos_escuros > 0
    assert matriz.modulos_claros > 0

    assert matriz.modulos_escuros + matriz.modulos_claros == matriz.total_modulos


@pytest.mark.parametrize("nivel", ["L", "M", "Q", "H"])
def test_correcao_erros_respeitada(nivel):
    matriz = gerar_matriz("example", nivel)

    assert matriz.correcao_erros == nivel


def test_versao_automaticamente_selecionada():
    pequena = gerar_matriz("A")
    grande = gerar_matriz("a" * 1000)

    assert grande.versao > pequena.versao


def test_micro_qr_nao_utilizado():
    matriz = gerar_matriz("A")

    assert isinstance(matriz.versao, int)
    assert matriz.versao >= 1
    assert matriz.dimensao >= 21


def test_mascara_valida():
    matriz = gerar_matriz("example")

    assert 0 <= matriz.mascara <= 7


def test_geracao_deterministica():
    primeira = gerar_matriz("https://ntizoconnect.me")
    segunda = gerar_matriz("https://ntizoconnect.me")

    assert primeira == segunda


def test_conteudos_diferentes():
    primeira = gerar_matriz("Conteudo A")
    segunda = gerar_matriz("Conteudo B")

    assert primeira.modulos != segunda.modulos


@pytest.mark.parametrize(
    "conteudo",
    [
        "Olá, Moçambique!",
        "Maputo — Cidade das Acácias",
        "你好世界",
        "مرحبا بالعالم",
        "GQR 🌍",
    ],
)
def test_conteudo_unicode(conteudo):
    matriz = gerar_matriz(conteudo)

    assert matriz.dimensao >= 21


@pytest.mark.parametrize("conteudo", ["", None, 123])
def test_conteudo_invalido(conteudo):
    with pytest.raises(ErroDadosInvalidos):
        gerar_matriz(conteudo)


def test_conteudo_excede_limite_contratual():
    with pytest.raises(ErroDadosInvalidos):
        gerar_matriz("a" * 4097)


def test_conteudo_excede_capacidade_qr():
    with pytest.raises(ErroCapacidadeQR):
        gerar_matriz("a" * 4096, "H")


def test_unicode_invalido():
    with pytest.raises(ErroCodificacaoQR):
        gerar_matriz("\ud800")


def test_correcao_erro_invalida():
    with pytest.raises(ErroDadosInvalidos):
        gerar_matriz("example", "X")


def test_matriz_imutavel():
    matriz = gerar_matriz("example")

    with pytest.raises(FrozenInstanceError):
        matriz.versao = 40


def test_modulos_imutaveis():
    matriz = gerar_matriz("example")

    with pytest.raises(TypeError):
        matriz.modulos[0][0] = 0


def test_tipos_modulos_dimensao():
    matriz = gerar_matriz("example")

    assert len(matriz.tipos_modulos) == matriz.dimensao

    assert all(len(linha) == matriz.dimensao for linha in matriz.tipos_modulos)


def test_identificacao_padroes_localizacao():
    matriz = gerar_matriz("example")

    assert matriz.tipo_modulo(0, 0) == (TYPE_FINDER_PATTERN_DARK)

    assert matriz.tipo_modulo(1, 1) == (TYPE_FINDER_PATTERN_LIGHT)


def test_identificacao_modulos_dados():
    matriz = gerar_matriz("example")

    tipos = {modulo for linha in matriz.tipos_modulos for modulo in linha}

    assert TYPE_DATA_DARK in tipos
    assert TYPE_DATA_LIGHT in tipos


def test_consultar_modulo_escuro():
    matriz = gerar_matriz("example")

    assert matriz.modulo_escuro(0, 0) is True
    assert matriz.modulo_escuro(1, 1) is False


@pytest.mark.parametrize(
    ("linha", "coluna"),
    [
        (-1, 0),
        (0, -1),
        (999, 0),
        (0, 999),
    ],
)
def test_coordenadas_invalidas(linha, coluna):
    matriz = gerar_matriz("example")

    with pytest.raises(IndexError):
        matriz.modulo_escuro(linha, coluna)

    with pytest.raises(IndexError):
        matriz.tipo_modulo(linha, coluna)
