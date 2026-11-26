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
INDICE_MAXIMO = RESOLUCAO_PALETA - 1


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
            indice / INDICE_MAXIMO,
        )
        for indice in range(RESOLUCAO_PALETA)
    )


def criar_paleta_bytes(
    gradiente: Gradiente,
) -> tuple[bytes, ...]:
    return tuple(bytes(cor) for cor in criar_paleta(gradiente))


def obter_indice(posicao: float) -> int:
    indice = round(posicao * INDICE_MAXIMO)

    if indice < 0:
        return 0

    if indice > INDICE_MAXIMO:
        return INDICE_MAXIMO

    return indice


def criar_gradiente_linear(
    largura: int,
    altura: int,
    gradiente: Gradiente,
    geometria: GeometriaGradiente,
) -> Image.Image:
    paleta = criar_paleta_bytes(gradiente)

    x1, y1, x2, y2 = geometria.extremos_lineares(gradiente.angulo)

    dx = x2 - x1
    dy = y2 - y1

    denominador = dx**2 + dy**2

    passo_x = dx / denominador
    passo_y = dy / denominador

    inicio = ((0.5 - x1) * dx + (0.5 - y1) * dy) / denominador

    # O deslocamento horizontal é independente
    # da linha que está a ser processada.
    deslocamentos_x = tuple(x * passo_x for x in range(largura))

    indice = obter_indice

    # Gradiente estritamente horizontal:
    # todas as linhas possuem as mesmas cores.
    if passo_y == 0.0:
        linha = b"".join(paleta[indice(inicio + deslocamento)] for deslocamento in deslocamentos_x)

        dados = linha * altura

    # Gradiente estritamente vertical:
    # todos os pixels de cada linha são iguais.
    elif passo_x == 0.0:
        dados = b"".join(paleta[indice(inicio + y * passo_y)] * largura for y in range(altura))

    # Gradiente com orientação arbitrária.
    else:
        linhas = []

        for y in range(altura):
            posicao = inicio + y * passo_y

            linha = b"".join(
                paleta[indice(posicao + deslocamento)] for deslocamento in deslocamentos_x
            )

            linhas.append(linha)

        dados = b"".join(linhas)

    return Image.frombytes(
        "RGBA",
        (largura, altura),
        dados,
    )


def criar_gradiente_radial_centrado(
    largura: int,
    altura: int,
    paleta: tuple[bytes, ...],
    geometria: GeometriaGradiente,
) -> Image.Image:
    cx, cy = geometria.centro
    raio = geometria.raio

    metade_largura = (largura + 1) // 2
    metade_altura = (altura + 1) // 2

    distancias_x = tuple(x + 0.5 - cx for x in range(metade_largura))

    indice = obter_indice

    linhas = []

    for y in range(metade_altura):
        dy = y + 0.5 - cy

        metade = [paleta[indice(hypot(dx, dy) / raio)] for dx in distancias_x]

        reflexo = metade[-2::-1] if largura % 2 else metade[::-1]

        linha = b"".join(metade + reflexo)

        linhas.append(linha)

    if altura % 2:
        linhas += linhas[-2::-1]
    else:
        linhas += linhas[::-1]

    return Image.frombytes(
        "RGBA",
        (largura, altura),
        b"".join(linhas),
    )


def criar_gradiente_radial(
    largura: int,
    altura: int,
    gradiente: Gradiente,
    geometria: GeometriaGradiente,
) -> Image.Image:
    paleta = criar_paleta_bytes(gradiente)

    cx, cy = geometria.centro

    # A reflexão só é válida quando o centro
    # do gradiente coincide com o da imagem.
    if cx == largura / 2 and cy == altura / 2:
        return criar_gradiente_radial_centrado(
            largura,
            altura,
            paleta,
            geometria,
        )

    raio = geometria.raio

    distancias_x = tuple(x + 0.5 - cx for x in range(largura))

    indice = obter_indice

    linhas = []

    for y in range(altura):
        dy = y + 0.5 - cy

        linha = b"".join(paleta[indice(hypot(dx, dy) / raio)] for dx in distancias_x)

        linhas.append(linha)

    return Image.frombytes(
        "RGBA",
        (largura, altura),
        b"".join(linhas),
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
