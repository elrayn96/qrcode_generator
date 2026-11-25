from io import BytesIO

import pytest
from PIL import Image
from src.core.excecoes import ErroDimensaoQR
from src.motor.matriz import gerar_matriz
from src.renderizacao.cores import (
    TRANSPARENTE,
    converter_cor,
)
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.modulos import iterar_modulos_escuros
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


@pytest.mark.parametrize(
    "forma",
    ["square", "rounded", "dots"],
)
def test_renderizar_formas_png(forma):
    resultado = renderizar_png(
        gerar_matriz("example"),
        forma=forma,
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        assert imagem.format == "PNG"
        assert imagem.size == (512, 512)

        imagem.verify()


@pytest.mark.parametrize(
    "forma",
    ["rounded", "dots"],
)
def test_forma_altera_imagem_png(forma):
    matriz = gerar_matriz("example")

    quadrado = renderizar_png(
        matriz,
        forma="square",
    )

    personalizado = renderizar_png(
        matriz,
        forma=forma,
    )

    assert quadrado.dados != personalizado.dados


@pytest.mark.parametrize(
    "forma",
    ["rounded", "dots"],
)
def test_padroes_funcionais_png(forma):
    matriz = gerar_matriz("example")

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    resultado = renderizar_png(
        matriz,
        forma=forma,
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        for modulo in iterar_modulos_escuros(
            matriz,
            geometria,
            forma,
        ):
            if not modulo.funcional:
                continue

            caixa = geometria.caixa_modulo(
                modulo.linha,
                modulo.coluna,
            )

            with imagem.crop(caixa) as regiao:
                assert set(regiao.getdata()) == {(0, 0, 0, 255)}


@pytest.mark.parametrize(
    "forma",
    ["rounded", "dots"],
)
def test_escala_insuficiente_png(forma):
    matriz = gerar_matriz("example")

    with pytest.raises(ErroDimensaoQR):
        renderizar_png(
            matriz,
            tamanho=128,
            margem=32,
            forma=forma,
        )


@pytest.mark.parametrize(
    "forma",
    ["rounded", "dots"],
)
def test_centro_modulos_dados_png(forma):
    matriz = gerar_matriz("example")

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    resultado = renderizar_png(
        matriz,
        forma=forma,
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        for modulo in iterar_modulos_escuros(
            matriz,
            geometria,
            forma,
        ):
            if modulo.funcional:
                continue

            centro = (
                modulo.x + modulo.escala // 2,
                modulo.y + modulo.escala // 2,
            )

            assert imagem.getpixel(centro) == (0, 0, 0, 255)
