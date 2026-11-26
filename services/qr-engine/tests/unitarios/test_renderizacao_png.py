from io import BytesIO

import pytest
from PIL import Image
from src.core.excecoes import ErroDimensaoQR
from src.motor.matriz import gerar_matriz
from src.renderizacao.cores import (
    PRETO,
    TRANSPARENTE,
    converter_cor,
)
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.modulos import iterar_modulos_escuros
from src.renderizacao.olhos import EstiloOlhos
from src.renderizacao.png import renderizar_png


def test_assinatura_png():
    matriz = gerar_matriz("ntizoconnect")

    resultado = renderizar_png(matriz)

    assert resultado.dados.startswith(b"\x89PNG\r\n\x1a\n")

    assert resultado.media_type == "image/png"


@pytest.mark.parametrize("tamanho", [128, 512, 1024, 2048])
def test_dimensao_png(tamanho):
    matriz = gerar_matriz("ntizoconnect")

    resultado = renderizar_png(
        matriz,
        tamanho=tamanho,
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        assert imagem.size == (tamanho, tamanho)
        assert imagem.format == "PNG"

        imagem.verify()


def test_cor_modulo():
    matriz = gerar_matriz("ntizoconnect")

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
        gerar_matriz("ntizoconnect"),
        cor_fundo=TRANSPARENTE,
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        assert imagem.mode == "RGBA"
        assert imagem.getpixel((0, 0))[3] == 0


def test_apenas_duas_cores():
    resultado = renderizar_png(gerar_matriz("ntizoconnect"))

    with Image.open(BytesIO(resultado.dados)) as imagem:
        cores = set(imagem.getdata())

    assert cores == {
        (0, 0, 0, 255),
        (255, 255, 255, 255),
    }


def test_correspondencia_integral_matriz_png():
    matriz = gerar_matriz("ntizoconnect")

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
    matriz = gerar_matriz("ntizoconnect")

    primeira = renderizar_png(matriz)
    segunda = renderizar_png(matriz)

    assert primeira.dados == segunda.dados


@pytest.mark.parametrize(
    "forma",
    ["square", "rounded", "dots"],
)
def test_renderizar_formas_png(forma):
    resultado = renderizar_png(
        gerar_matriz("ntizoconnect"),
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
    matriz = gerar_matriz("ntizoconnect")

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
    matriz = gerar_matriz("ntizoconnect")

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
    matriz = gerar_matriz("ntizoconnect")

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
    matriz = gerar_matriz("ntizoconnect")

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


@pytest.mark.parametrize("exterior", ["square", "rounded", "dots"])
@pytest.mark.parametrize("interior", ["square", "rounded", "dots"])
def test_formas_olhos_png(exterior, interior):
    estilo = EstiloOlhos(
        forma_exterior=exterior,
        forma_interior=interior,
        cor_exterior=PRETO,
        cor_interior=PRETO,
    )

    resultado = renderizar_png(
        gerar_matriz("ntizoconnect"),
        olhos=estilo,
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        assert imagem.size == (512, 512)
        imagem.verify()


def test_cores_independentes_olhos_png():
    matriz = gerar_matriz("ntizoconnect")

    geometria = calcular_geometria(matriz.dimensao, 512)

    estilo = EstiloOlhos(
        forma_exterior="square",
        forma_interior="dots",
        cor_exterior=converter_cor("#4C1D95"),
        cor_interior=converter_cor("#7C3AED"),
    )

    resultado = renderizar_png(
        matriz,
        olhos=estilo,
    )

    x = geometria.origem_x
    y = geometria.origem_y
    e = geometria.escala

    with Image.open(BytesIO(resultado.dados)) as imagem:
        exterior = imagem.getpixel((x, y))

        interior = imagem.getpixel((x + 3 * e + e // 2, y + 3 * e + e // 2))

    assert exterior == (76, 29, 149, 255)
    assert interior == (124, 58, 237, 255)


def test_abertura_transparente_olhos_png():
    matriz = gerar_matriz("ntizoconnect")

    geometria = calcular_geometria(matriz.dimensao, 512)

    estilo = EstiloOlhos(
        forma_exterior="square",
        forma_interior="square",
        cor_exterior=PRETO,
        cor_interior=PRETO,
    )

    resultado = renderizar_png(
        matriz,
        cor_fundo=TRANSPARENTE,
        olhos=estilo,
    )

    e = geometria.escala

    ponto = (
        geometria.origem_x + e + e // 2,
        geometria.origem_y + 3 * e + e // 2,
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        assert imagem.getpixel(ponto)[3] == 0


def test_olhos_padrao_preservam_imagem_png():
    matriz = gerar_matriz("ntizoconnect")

    convencional = renderizar_png(matriz)

    personalizado = renderizar_png(
        matriz,
        olhos=EstiloOlhos(
            forma_exterior="square",
            forma_interior="square",
            cor_exterior=PRETO,
            cor_interior=PRETO,
        ),
    )

    with (
        Image.open(BytesIO(convencional.dados)) as primeira,
        Image.open(BytesIO(personalizado.dados)) as segunda,
    ):
        assert primeira.tobytes() == segunda.tobytes()
