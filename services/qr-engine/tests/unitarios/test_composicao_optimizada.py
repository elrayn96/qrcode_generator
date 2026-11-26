from math import hypot

import pytest
from src.renderizacao.composicao import (
    RESOLUCAO_PALETA,
    criar_paleta,
    criar_paleta_bytes,
    criar_preenchimento,
)
from src.renderizacao.gradientes import (
    GeometriaGradiente,
    Gradiente,
    PontoCor,
)


def criar_gradiente(tipo, angulo=0):
    return Gradiente(
        tipo=tipo,
        angulo=angulo,
        pontos=(
            PontoCor(0.0, (23, 37, 84, 255)),
            PontoCor(0.3, (67, 56, 202, 128)),
            PontoCor(0.7, (109, 40, 217, 192)),
            PontoCor(1.0, (196, 181, 253, 0)),
        ),
    )


def criar_referencia(
    largura,
    altura,
    gradiente,
    geometria,
):
    # Algoritmo anterior, mantido como referência
    # independente da implementação optimizada.

    paleta = criar_paleta(gradiente)

    def obter_indice_original(posicao):
        return max(
            0,
            min(
                RESOLUCAO_PALETA - 1,
                round(posicao * (RESOLUCAO_PALETA - 1)),
            ),
        )

    dados = bytearray()

    if gradiente.tipo == "linear":
        x1, y1, x2, y2 = geometria.extremos_lineares(gradiente.angulo)

        dx = x2 - x1
        dy = y2 - y1

        denominador = dx**2 + dy**2

        passo_x = dx / denominador
        passo_y = dy / denominador

        inicio = ((0.5 - x1) * dx + (0.5 - y1) * dy) / denominador

        for y in range(altura):
            posicao = inicio + y * passo_y

            for x in range(largura):
                indice = obter_indice_original(posicao + x * passo_x)

                dados.extend(paleta[indice])

    else:
        cx, cy = geometria.centro
        raio = geometria.raio

        for y in range(altura):
            dy = y + 0.5 - cy

            for x in range(largura):
                dx = x + 0.5 - cx

                posicao = hypot(dx, dy) / raio

                indice = obter_indice_original(posicao)

                dados.extend(paleta[indice])

    return bytes(dados)


@pytest.mark.parametrize("tipo", ["linear", "radial"])
def test_paleta_bytes(tipo):
    gradiente = criar_gradiente(tipo)

    original = criar_paleta(gradiente)
    optimizada = criar_paleta_bytes(gradiente)

    assert len(original) == len(optimizada)

    assert optimizada == tuple(bytes(cor) for cor in original)

    assert all(len(cor) == 4 for cor in optimizada)


@pytest.mark.parametrize(
    "angulo",
    [0, 1, 30, 45, 60, 90, 135, 180, 270, 359, 360],
)
@pytest.mark.parametrize(
    ("largura", "altura"),
    [
        (32, 32),
        (31, 31),
        (64, 33),
        (1, 1),
        (1, 16),
        (16, 1),
    ],
)
def test_linear_equivalente(
    angulo,
    largura,
    altura,
):
    gradiente = criar_gradiente(
        "linear",
        angulo,
    )

    geometria = GeometriaGradiente(
        largura,
        altura,
    )

    esperado = criar_referencia(
        largura,
        altura,
        gradiente,
        geometria,
    )

    with criar_preenchimento(
        largura,
        altura,
        gradiente,
        geometria,
    ) as imagem:
        assert imagem.tobytes() == esperado


@pytest.mark.parametrize(
    ("largura", "altura"),
    [
        (32, 32),
        (31, 31),
        (32, 31),
        (31, 32),
        (64, 33),
        (33, 64),
        (1, 1),
        (1, 16),
        (16, 1),
        (1, 17),
        (17, 1),
    ],
)
def test_radial_centrado_equivalente(
    largura,
    altura,
):
    gradiente = criar_gradiente("radial")

    geometria = GeometriaGradiente(
        largura,
        altura,
    )

    esperado = criar_referencia(
        largura,
        altura,
        gradiente,
        geometria,
    )

    with criar_preenchimento(
        largura,
        altura,
        gradiente,
        geometria,
    ) as imagem:
        assert imagem.tobytes() == esperado


@pytest.mark.parametrize(
    "tipo",
    ["linear", "radial"],
)
@pytest.mark.parametrize(
    ("origem_x", "origem_y"),
    [
        (10, 20),
        (-10, -20),
        (0, -50),
        (0.25, 0.75),
    ],
)
def test_geometria_deslocada(
    tipo,
    origem_x,
    origem_y,
):
    gradiente = criar_gradiente(
        tipo,
        45,
    )

    geometria = GeometriaGradiente(
        largura=128,
        altura=128,
        origem_x=origem_x,
        origem_y=origem_y,
    )

    esperado = criar_referencia(
        32,
        32,
        gradiente,
        geometria,
    )

    with criar_preenchimento(
        32,
        32,
        gradiente,
        geometria,
    ) as imagem:
        assert imagem.tobytes() == esperado


@pytest.mark.parametrize(
    ("largura", "altura"),
    [
        (32, 32),
        (31, 31),
        (32, 31),
        (31, 32),
    ],
)
def test_simetria_radial(largura, altura):
    gradiente = criar_gradiente("radial")

    with criar_preenchimento(
        largura,
        altura,
        gradiente,
    ) as imagem:
        for y in range(altura):
            for x in range(largura):
                cor = imagem.getpixel((x, y))

                assert cor == imagem.getpixel((largura - 1 - x, y))

                assert cor == imagem.getpixel((x, altura - 1 - y))
