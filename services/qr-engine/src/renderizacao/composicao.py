from math import hypot

from PIL import Image, ImageChops

from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.gradientes import (
    RGBA,
    GeometriaGradiente,
    Gradiente,
    obter_cor,
)

Preenchimento = RGBA | Gradiente

DIMENSAO_MAXIMA = 2048
RESOLUCAO_PALETA = 4096


def validar_dimensoes(
    largura: int,
    altura: int,
) -> None:
    if not (1 <= largura <= DIMENSAO_MAXIMA and 1 <= altura <= DIMENSAO_MAXIMA):
        raise ErroDadosInvalidos()


def criar_paleta(
    gradiente: Gradiente,
) -> tuple[RGBA, ...]:
    return tuple(
        obter_cor(
            gradiente,
            indice / (RESOLUCAO_PALETA - 1),
        )
        for indice in range(RESOLUCAO_PALETA)
    )


def obter_indice(posicao: float) -> int:
    return max(
        0,
        min(
            RESOLUCAO_PALETA - 1,
            round(posicao * (RESOLUCAO_PALETA - 1)),
        ),
    )


def criar_gradiente_linear(
    largura: int,
    altura: int,
    gradiente: Gradiente,
    geometria: GeometriaGradiente,
) -> Image.Image:
    paleta = criar_paleta(gradiente)

    x1, y1, x2, y2 = geometria.extremos_lineares(gradiente.angulo)

    dx = x2 - x1
    dy = y2 - y1

    denominador = dx**2 + dy**2

    passo_x = dx / denominador
    passo_y = dy / denominador

    inicio = ((0.5 - x1) * dx + (0.5 - y1) * dy) / denominador

    dados = bytearray(largura * altura * 4)

    deslocamento = 0

    for y in range(altura):
        posicao = inicio + y * passo_y

        for x in range(largura):
            cor = paleta[obter_indice(posicao + x * passo_x)]

            dados[deslocamento] = cor[0]
            dados[deslocamento + 1] = cor[1]
            dados[deslocamento + 2] = cor[2]
            dados[deslocamento + 3] = cor[3]

            deslocamento += 4

    return Image.frombytes(
        "RGBA",
        (largura, altura),
        bytes(dados),
    )


def criar_gradiente_radial(
    largura: int,
    altura: int,
    gradiente: Gradiente,
    geometria: GeometriaGradiente,
) -> Image.Image:
    paleta = criar_paleta(gradiente)

    cx, cy = geometria.centro
    raio = geometria.raio

    distancias_x = tuple(x + 0.5 - cx for x in range(largura))

    dados = bytearray(largura * altura * 4)

    deslocamento = 0

    for y in range(altura):
        dy = y + 0.5 - cy

        for dx in distancias_x:
            posicao = hypot(dx, dy) / raio

            cor = paleta[obter_indice(posicao)]

            dados[deslocamento] = cor[0]
            dados[deslocamento + 1] = cor[1]
            dados[deslocamento + 2] = cor[2]
            dados[deslocamento + 3] = cor[3]

            deslocamento += 4

    return Image.frombytes(
        "RGBA",
        (largura, altura),
        bytes(dados),
    )


def criar_preenchimento(
    largura: int,
    altura: int,
    preenchimento: Preenchimento,
    geometria: GeometriaGradiente | None = None,
) -> Image.Image:
    validar_dimensoes(largura, altura)

    if not isinstance(preenchimento, Gradiente):
        return Image.new(
            "RGBA",
            (largura, altura),
            preenchimento,
        )

    geometria = geometria or GeometriaGradiente(
        largura=largura,
        altura=altura,
    )

    gerador = criar_gradiente_linear if preenchimento.tipo == "linear" else criar_gradiente_radial

    return gerador(
        largura,
        altura,
        preenchimento,
        geometria,
    )


def aplicar_preenchimento(
    imagem: Image.Image,
    mascara: Image.Image,
    preenchimento: Preenchimento,
    geometria: GeometriaGradiente | None = None,
) -> None:
    if imagem.mode != "RGBA":
        raise ErroDadosInvalidos()

    if mascara.mode != "L":
        raise ErroDadosInvalidos()

    if imagem.size != mascara.size:
        raise ErroDadosInvalidos()

    largura, altura = imagem.size

    with criar_preenchimento(
        largura,
        altura,
        preenchimento,
        geometria,
    ) as camada:
        with (
            camada.getchannel("A") as alfa,
            ImageChops.multiply(
                alfa,
                mascara,
            ) as alfa_final,
        ):
            camada.putalpha(alfa_final)

        imagem.alpha_composite(camada)
