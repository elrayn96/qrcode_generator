from io import BytesIO

import pytest
from PIL import Image
from src.motor.matriz import gerar_matriz
from src.renderizacao.cores import (
    TRANSPARENTE,
    converter_cor,
)
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.png import renderizar_png


def test_assinatura_png():
    matriz = gerar_matriz("example")

    resultado = renderizar_png(matriz)

    assert resultado.dados.startswith(b"\x89PNG\r\n\x1a\n")

    assert resultado.media_type == "image/png"


@pytest.mark.parametrize("tamanho", [128, 512, 1024, 2048])
def test_dimensao_png(tamanho):
    matriz = gerar_matriz("example")

    resultado = renderizar_png(
        matriz,
        tamanho=tamanho,
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        assert imagem.size == (tamanho, tamanho)
        assert imagem.format == "PNG"

        imagem.verify()


def test_cor_modulo():
    matriz = gerar_matriz("example")

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    resultado = renderizar_png(
        matriz,
        cor_modulos=converter_cor("#7C3AED"),
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        pixel = imagem.getpixel((geometria.origem_x, geometria.origem_y))

    assert pixel == (124, 58, 237, 255)


def test_fundo_transparente():
    resultado = renderizar_png(
        gerar_matriz("example"),
        cor_fundo=TRANSPARENTE,
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        assert imagem.mode == "RGBA"
        assert imagem.getpixel((0, 0))[3] == 0


def test_apenas_duas_cores():
    resultado = renderizar_png(gerar_matriz("example"))

    with Image.open(BytesIO(resultado.dados)) as imagem:
        cores = set(imagem.getdata())

    assert cores == {
        (0, 0, 0, 255),
        (255, 255, 255, 255),
    }


def test_correspondencia_integral_matriz_png():
    matriz = gerar_matriz("example")

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    resultado = renderizar_png(matriz)

    with Image.open(BytesIO(resultado.dados)) as imagem:
        for linha, valores in enumerate(matriz.modulos):
            for coluna, valor in enumerate(valores):
                caixa = geometria.caixa_modulo(
                    linha,
                    coluna,
                )

                esperado = (0, 0, 0, 255) if valor == 1 else (255, 255, 255, 255)

                with imagem.crop(caixa) as modulo:
                    assert set(modulo.getdata()) == {esperado}


def test_png_deterministico():
    matriz = gerar_matriz("example")

    primeira = renderizar_png(matriz)
    segunda = renderizar_png(matriz)

    assert primeira.dados == segunda.dados
