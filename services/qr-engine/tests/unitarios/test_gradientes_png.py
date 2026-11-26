from io import BytesIO

import pytest
from PIL import Image
from src.motor.matriz import gerar_matriz
from src.renderizacao.estilos import resolver_estilo
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.png import renderizar_png
from src.schemas.pedido import PedidoRenderizacao


def criar_gradiente(
    tipo="linear",
    primeira="#6D28D9",
    ultima="#172554",
):
    return {
        "type": tipo,
        "stops": [
            {"position": 0.0, "color": primeira},
            {"position": 1.0, "color": ultima},
        ],
    }


def criar_imagem(**personalizacao):
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "https://ntizoconnect.me",
            "style": personalizacao,
        }
    )

    matriz = gerar_matriz(pedido.content)

    resultado = renderizar_png(
        matriz,
        estilo=resolver_estilo(pedido),
    )

    return resultado, matriz


def test_estilo_padrao_preserva_renderizacao():
    resultado, matriz = criar_imagem()

    convencional = renderizar_png(matriz)

    with (
        Image.open(BytesIO(resultado.dados)) as primeira,
        Image.open(BytesIO(convencional.dados)) as segunda,
    ):
        assert primeira.tobytes() == segunda.tobytes()


@pytest.mark.parametrize("tipo", ["linear", "radial"])
@pytest.mark.parametrize("forma", ["square", "rounded", "dots"])
def test_gradientes_modulos_png(tipo, forma):
    resultado, _ = criar_imagem(
        modules={
            "shape": forma,
            "gradient": criar_gradiente(tipo),
        },
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        assert imagem.mode == "RGBA"
        assert imagem.size == (512, 512)

        cores = set(imagem.getdata())

        assert len(cores) > 2
        assert imagem.getpixel((0, 0)) == (255, 255, 255, 255)


def test_gradiente_preserva_modulos_claros():
    resultado, matriz = criar_imagem(
        modules={
            "gradient": criar_gradiente(),
        }
    )

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        for linha, valores in enumerate(matriz.modulos):
            for coluna, valor in enumerate(valores):
                x = geometria.origem_x + coluna * geometria.escala + geometria.escala // 2

                y = geometria.origem_y + linha * geometria.escala + geometria.escala // 2

                pixel = imagem.getpixel((x, y))

                if valor == 0:
                    assert pixel == (255, 255, 255, 255)
                else:
                    assert pixel != (255, 255, 255, 255)
                    assert pixel[3] == 255


def test_gradiente_com_fundo_transparente():
    resultado, matriz = criar_imagem(
        modules={
            "gradient": criar_gradiente(),
        },
        background={
            "transparent": True,
        },
    )

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        assert imagem.getpixel((0, 0))[3] == 0

        assert imagem.getpixel((geometria.origem_x, geometria.origem_y))[3] == 255


def test_gradiente_no_fundo():
    resultado, _ = criar_imagem(
        background={
            "gradient": criar_gradiente(
                primeira="#FFFFFF",
                ultima="#DBEAFE",
            ),
        }
    )

    with Image.open(BytesIO(resultado.dados)) as imagem:
        esquerda = imagem.getpixel((0, 0))
        direita = imagem.getpixel((511, 0))

        assert esquerda != direita
        assert esquerda[3] == 255
        assert direita[3] == 255


def test_gradiente_herdado_pelos_olhos():
    gradiente = criar_gradiente()

    convencional, _ = criar_imagem(
        modules={"gradient": gradiente},
    )

    personalizado, _ = criar_imagem(
        modules={"gradient": gradiente},
        eyes={
            "outer": {"shape": "square"},
            "inner": {"shape": "square"},
        },
    )

    with (
        Image.open(BytesIO(convencional.dados)) as primeira,
        Image.open(BytesIO(personalizado.dados)) as segunda,
    ):
        assert primeira.tobytes() == segunda.tobytes()


def test_gradientes_independentes_nos_olhos():
    resultado, matriz = criar_imagem(
        modules={"color": "#000000"},
        eyes={
            "outer": {
                "gradient": criar_gradiente(
                    primeira="#7C3AED",
                    ultima="#2563EB",
                ),
            },
            "inner": {
                "color": "#DC2626",
            },
        },
    )

    geometria = calcular_geometria(
        matriz.dimensao,
        512,
    )

    x = geometria.origem_x
    y = geometria.origem_y
    e = geometria.escala

    with Image.open(BytesIO(resultado.dados)) as imagem:
        exterior = imagem.getpixel((x, y))

        interior = imagem.getpixel((x + 3 * e + e // 2, y + 3 * e + e // 2))

        abertura = imagem.getpixel((x + e + e // 2, y + 3 * e + e // 2))

        assert exterior != (0, 0, 0, 255)
        assert interior == (220, 38, 38, 255)
        assert abertura == (255, 255, 255, 255)


def test_gradiente_png_deterministico():
    primeira, _ = criar_imagem(
        modules={"gradient": criar_gradiente()},
    )

    segunda, _ = criar_imagem(
        modules={"gradient": criar_gradiente()},
    )

    assert primeira.dados == segunda.dados
