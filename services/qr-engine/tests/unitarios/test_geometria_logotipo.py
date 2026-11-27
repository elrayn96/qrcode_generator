from dataclasses import replace

import pytest
from segno.consts import TYPE_DATA_DARK, TYPE_DATA_LIGHT, TYPE_FINDER_PATTERN_LIGHT
from src.core.excecoes import ErroDadosInvalidos
from src.motor.matriz import gerar_matriz
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.logotipos import calcular_geometria_logotipo
from src.schemas.personalizacao import Logotipo


def logo(**opcoes):
    return Logotipo(mediaType="image/png", base64="AAAA", **opcoes)


@pytest.fixture
def contexto():
    matriz = gerar_matriz("ntizoconnect", "H")
    return matriz, calcular_geometria(matriz.dimensao, 512)


@pytest.mark.parametrize("tamanho", [(100, 100), (200, 100), (100, 200)])
def test_proporcao_centro(contexto, tamanho):
    matriz, g = contexto
    resultado = calcular_geometria_logotipo(matriz, g, logo(scale=0.1, padding=0), tamanho)
    x, y, xf, yf = resultado.caixa_imagem
    assert max(xf - x, yf - y) == int(g.dimensao_qr * 0.1)
    assert abs((xf - x) * tamanho[1] - (yf - y) * tamanho[0]) < max(tamanho)
    assert abs(x + xf - 2 * g.origem_x - g.dimensao_qr) <= 1
    assert abs(y + yf - 2 * g.origem_y - g.dimensao_qr) <= 1
    assert resultado.caixa_protecao == resultado.caixa_imagem


def test_padding_e_defaults(contexto):
    matriz, g = contexto
    r = calcular_geometria_logotipo(matriz, g, logo(), (100, 100))
    assert r == calcular_geometria_logotipo(matriz, g, logo(scale=0.15, padding=1), (100, 100))
    x, y, xf, yf = r.caixa_imagem
    assert r.caixa_protecao == (x - g.escala, y - g.escala, xf + g.escala, yf + g.escala)


@pytest.mark.parametrize("tipo", [TYPE_DATA_LIGHT, TYPE_DATA_DARK, TYPE_FINDER_PATTERN_LIGHT])
def test_classificacao_modulo(contexto, tipo):
    matriz, g = contexto
    centro = matriz.dimensao // 2
    tipos = [list(linha) for linha in matriz.tipos_modulos]
    tipos[centro][centro] = tipo
    matriz = replace(matriz, tipos_modulos=tuple(map(tuple, tipos)))
    if tipo == TYPE_FINDER_PATTERN_LIGHT:
        with pytest.raises(ErroDadosInvalidos):
            calcular_geometria_logotipo(matriz, g, logo(padding=0), (100, 100))
    else:
        calcular_geometria_logotipo(matriz, g, logo(padding=0), (100, 100))


@pytest.mark.parametrize("tamanho", [(0, 1), (1, 0), (-1, 2)])
def test_dimensoes_invalidas(contexto, tamanho):
    matriz, g = contexto
    with pytest.raises(ErroDadosInvalidos):
        calcular_geometria_logotipo(matriz, g, logo(), tamanho)


def test_padding_colide(contexto):
    matriz, g = contexto
    with pytest.raises(ErroDadosInvalidos):
        calcular_geometria_logotipo(matriz, g, logo(scale=0.2, padding=4), (100, 100))


def test_matriz_incompativel(contexto):
    matriz, _ = contexto
    # print("len modulos:", len(matriz.modulos))
    # print("dimensao matriz:", matriz.dimensao)
    # print("dimensao geometria:", _.dimensao_matriz)
    # print("len primeira linha:", len(matriz.modulos[0]))
    with pytest.raises(ErroDadosInvalidos):
        calcular_geometria_logotipo(matriz, calcular_geometria(24, 512), logo(), (100, 100))
