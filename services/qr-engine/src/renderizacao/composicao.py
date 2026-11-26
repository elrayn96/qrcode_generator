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
    *,
    origem_x: int = 0,
    origem_y: int = 0,
) -> Image.Image:
    paleta = criar_paleta_bytes(gradiente)

    x1, y1, x2, y2 = geometria.extremos_lineares(
        gradiente.angulo,
    )

    dx = x2 - x1
    dy = y2 - y1

    denominador = dx**2 + dy**2

    passo_x = dx / denominador
    passo_y = dy / denominador

    inicio = ((0.5 - x1) * dx + (0.5 - y1) * dy) / denominador

    deslocamentos_x = tuple(
        x * passo_x
        for x in range(
            origem_x,
            origem_x + largura,
        )
    )

    posicoes_y = tuple(
        inicio + y * passo_y
        for y in range(
            origem_y,
            origem_y + altura,
        )
    )

    indice = obter_indice

    # Verificar se todas as colunas mantêm
    # o mesmo índice entre a primeira e a
    # última linha.
    if abs(passo_y) <= abs(passo_x):
        primeira = posicoes_y[0]
        ultima = posicoes_y[-1]

        indices = tuple(indice(primeira + deslocamento) for deslocamento in deslocamentos_x)

        if all(
            actual == indice(ultima + deslocamento)
            for actual, deslocamento in zip(
                indices,
                deslocamentos_x,
                strict=True,
            )
        ):
            linha = b"".join(paleta[actual] for actual in indices)

            return Image.frombytes(
                "RGBA",
                (largura, altura),
                linha * altura,
            )

    # Verificar se todas as linhas mantêm
    # o mesmo índice entre o primeiro e o
    # último pixel.
    else:
        primeiro = deslocamentos_x[0]
        ultimo = deslocamentos_x[-1]

        indices = tuple(indice(posicao + primeiro) for posicao in posicoes_y)

        if all(
            actual == indice(posicao + ultimo)
            for actual, posicao in zip(
                indices,
                posicoes_y,
                strict=True,
            )
        ):
            dados = b"".join(paleta[actual] * largura for actual in indices)

            return Image.frombytes(
                "RGBA",
                (largura, altura),
                dados,
            )

    # Caso geral: preservar o cálculo
    # original de cada pixel.
    dados = b"".join(
        b"".join(paleta[indice(posicao + deslocamento)] for deslocamento in deslocamentos_x)
        for posicao in posicoes_y
    )

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
    *,
    origem_x: int = 0,
    origem_y: int = 0,
) -> Image.Image:
    cx, cy = geometria.centro
    raio = geometria.raio

    metade_largura = (largura + 1) // 2
    metade_altura = (altura + 1) // 2

    distancias_x = tuple(
        x + 0.5 - cx
        for x in range(
            origem_x,
            origem_x + metade_largura,
        )
    )

    indice = obter_indice

    linhas = []

    for y in range(
        origem_y,
        origem_y + metade_altura,
    ):
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
    *,
    origem_x: int = 0,
    origem_y: int = 0,
) -> Image.Image:
    paleta = criar_paleta_bytes(gradiente)

    cx, cy = geometria.centro

    centro_regiao_x = origem_x + largura / 2
    centro_regiao_y = origem_y + altura / 2

    # A simetria é válida sempre que o centro
    # da região coincide com o do gradiente.
    if cx == centro_regiao_x and cy == centro_regiao_y:
        return criar_gradiente_radial_centrado(
            largura,
            altura,
            paleta,
            geometria,
            origem_x=origem_x,
            origem_y=origem_y,
        )

    raio = geometria.raio

    distancias_x = tuple(
        x + 0.5 - cx
        for x in range(
            origem_x,
            origem_x + largura,
        )
    )

    indice = obter_indice

    linhas = []

    for y in range(
        origem_y,
        origem_y + altura,
    ):
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


def criar_preenchimento_regional(
    largura: int,
    altura: int,
    preenchimento: Preenchimento,
    caixa: tuple[int, int, int, int],
    geometria: GeometriaGradiente | None = None,
) -> Image.Image:
    validar_dimensoes(largura, altura)

    x0, y0, x1, y1 = caixa

    if not (0 <= x0 < x1 <= largura and 0 <= y0 < y1 <= altura):
        raise ErroDadosInvalidos()

    largura_regiao = x1 - x0
    altura_regiao = y1 - y0

    if not isinstance(preenchimento, Gradiente):
        return Image.new(
            "RGBA",
            (largura_regiao, altura_regiao),
            preenchimento,
        )

    geometria = geometria or GeometriaGradiente(
        largura=largura,
        altura=altura,
    )

    gerador = criar_gradiente_linear if preenchimento.tipo == "linear" else criar_gradiente_radial

    return gerador(
        largura_regiao,
        altura_regiao,
        preenchimento,
        geometria,
        origem_x=x0,
        origem_y=y0,
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

    validar_dimensoes(largura, altura)

    caixa = mascara.getbbox()

    # Uma máscara totalmente vazia não
    # altera nenhum pixel da imagem.
    if caixa is None:
        return

    x0, y0, x1, y1 = caixa

    # Evitar o recorte quando a máscara
    # ocupa toda a imagem.
    if caixa == (0, 0, largura, altura):
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

        return

    # Gerar apenas a região utilizada.
    with (
        mascara.crop(caixa) as mascara_regional,
        criar_preenchimento_regional(
            largura,
            altura,
            preenchimento,
            (x0, y0, x1, y1),
            geometria,
        ) as camada,
    ):
        with (
            camada.getchannel("A") as alfa,
            ImageChops.multiply(
                alfa,
                mascara_regional,
            ) as alfa_final,
        ):
            camada.putalpha(alfa_final)

        imagem.alpha_composite(
            camada,
            dest=(x0, y0),
        )
