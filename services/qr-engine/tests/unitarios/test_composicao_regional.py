from unittest.mock import patch

import pytest
from PIL import Image, ImageChops
from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.composicao import (
    aplicar_preenchimento,
    criar_gradiente_radial_centrado,
    criar_preenchimento,
    criar_preenchimento_regional,
)
from src.renderizacao.gradientes import (
    GeometriaGradiente,
    Gradiente,
    PontoCor,
)

TRANSPARENTE = (0, 0, 0, 0)
BRANCO = (255, 255, 255, 255)
ROXO = (109, 40, 217, 128)

CAIXAS = [
    (0, 0, 64, 64),
    (8, 8, 56, 56),
    (0, 0, 16, 16),
    (48, 48, 64, 64),
    (7, 13, 38, 47),
    (30, 30, 31, 31),
]


def criar_gradiente(tipo, angulo=0):
    return Gradiente(
        tipo=tipo,
        angulo=angulo,
        pontos=(
            PontoCor(0.0, (23, 37, 84, 255)),
            PontoCor(0.4, (67, 56, 202, 192)),
            PontoCor(0.7, (109, 40, 217, 128)),
            PontoCor(1.0, (196, 181, 253, 0)),
        ),
    )


PREENCHIMENTOS = [
    ROXO,
    criar_gradiente("linear", 0),
    criar_gradiente("linear", 45),
    criar_gradiente("linear", 90),
    criar_gradiente("linear", 180),
    criar_gradiente("linear", 270),
    criar_gradiente("radial"),
]


def aplicar_referencia(
    imagem,
    mascara,
    preenchimento,
    geometria=None,
):
    # Composição integral anterior.
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


@pytest.mark.parametrize(
    "preenchimento",
    PREENCHIMENTOS,
)
@pytest.mark.parametrize("caixa", CAIXAS)
def test_regiao_equivalente_recorte(
    preenchimento,
    caixa,
):
    with (
        criar_preenchimento(
            64,
            64,
            preenchimento,
        ) as completa,
        completa.crop(caixa) as esperado,
        criar_preenchimento_regional(
            64,
            64,
            preenchimento,
            caixa,
        ) as regional,
    ):
        assert regional.size == esperado.size
        assert regional.mode == "RGBA"

        assert regional.tobytes() == esperado.tobytes()


@pytest.mark.parametrize(
    "tipo",
    ["linear", "radial"],
)
@pytest.mark.parametrize(
    ("origem_x", "origem_y"),
    [
        (0, 0),
        (-25, -18),
        (10, 14),
        (0.25, 0.75),
    ],
)
def test_regiao_geometria_deslocada(
    tipo,
    origem_x,
    origem_y,
):
    gradiente = criar_gradiente(tipo, 45)

    geometria = GeometriaGradiente(
        largura=128,
        altura=96,
        origem_x=origem_x,
        origem_y=origem_y,
    )

    caixa = (7, 13, 38, 47)

    with (
        criar_preenchimento(
            64,
            64,
            gradiente,
            geometria,
        ) as completa,
        completa.crop(caixa) as esperado,
        criar_preenchimento_regional(
            64,
            64,
            gradiente,
            caixa,
            geometria,
        ) as regional,
    ):
        assert regional.tobytes() == esperado.tobytes()


@pytest.mark.parametrize(
    "preenchimento",
    PREENCHIMENTOS,
)
@pytest.mark.parametrize(
    "fundo",
    [BRANCO, TRANSPARENTE, (25, 50, 75, 128)],
)
def test_composicao_regional_equivalente(
    preenchimento,
    fundo,
):
    with (
        Image.new("RGBA", (64, 64), fundo) as original,
        original.copy() as optimizada,
        Image.new("L", (64, 64), 0) as mascara,
    ):
        mascara.paste(
            255,
            (10, 12, 50, 52),
        )

        mascara.paste(
            128,
            (20, 20, 40, 40),
        )

        mascara.paste(
            0,
            (25, 25, 30, 30),
        )

        aplicar_referencia(
            original,
            mascara,
            preenchimento,
        )

        aplicar_preenchimento(
            optimizada,
            mascara,
            preenchimento,
        )

        assert original.tobytes() == optimizada.tobytes()


@pytest.mark.parametrize(
    "preenchimento",
    PREENCHIMENTOS,
)
def test_mascara_vazia_sem_renderizacao(
    preenchimento,
):
    with (
        Image.new(
            "RGBA",
            (64, 64),
            BRANCO,
        ) as imagem,
        Image.new(
            "L",
            (64, 64),
            0,
        ) as mascara,
    ):
        antes = imagem.tobytes()

        with (
            patch("src.renderizacao.composicao.criar_preenchimento") as integral,
            patch("src.renderizacao.composicao.criar_preenchimento_regional") as regional,
        ):
            aplicar_preenchimento(
                imagem,
                mascara,
                preenchimento,
            )

            integral.assert_not_called()
            regional.assert_not_called()

        assert imagem.tobytes() == antes


def test_regiao_recebe_limites_mascara():
    gradiente = criar_gradiente("linear", 45)

    with (
        Image.new(
            "RGBA",
            (64, 64),
        ) as imagem,
        Image.new(
            "L",
            (64, 64),
            0,
        ) as mascara,
        patch(
            "src.renderizacao.composicao.criar_preenchimento_regional",
            wraps=criar_preenchimento_regional,
        ) as regional,
    ):
        mascara.paste(
            255,
            (8, 12, 40, 48),
        )

        aplicar_preenchimento(
            imagem,
            mascara,
            gradiente,
        )

        regional.assert_called_once_with(
            64,
            64,
            gradiente,
            (8, 12, 40, 48),
            None,
        )


def test_mascara_integral_sem_recorte():
    gradiente = criar_gradiente("radial")

    with (
        Image.new(
            "RGBA",
            (64, 64),
        ) as imagem,
        Image.new(
            "L",
            (64, 64),
            255,
        ) as mascara,
        patch("src.renderizacao.composicao.criar_preenchimento_regional") as regional,
    ):
        aplicar_preenchimento(
            imagem,
            mascara,
            gradiente,
        )

        regional.assert_not_called()


@pytest.mark.parametrize(
    "caixa",
    [
        (-1, 0, 16, 16),
        (0, -1, 16, 16),
        (0, 0, 65, 64),
        (0, 0, 64, 65),
        (5, 5, 5, 10),
        (5, 5, 10, 5),
        (10, 0, 5, 10),
        (0, 10, 10, 5),
    ],
)
def test_rejeitar_regioes_invalidas(caixa):
    with pytest.raises(ErroDadosInvalidos):
        criar_preenchimento_regional(
            64,
            64,
            ROXO,
            caixa,
        )


@pytest.mark.parametrize(
    "angulo",
    [0, 90, 180, 270, 360],
)
@pytest.mark.parametrize(
    "tamanho",
    [31, 32, 63, 64],
)
def test_gradiente_cardinal_regional(
    angulo,
    tamanho,
):
    gradiente = criar_gradiente(
        "linear",
        angulo,
    )

    caixa = (
        3,
        5,
        tamanho - 3,
        tamanho - 5,
    )

    with (
        criar_preenchimento(
            tamanho,
            tamanho,
            gradiente,
        ) as imagem,
        imagem.crop(caixa) as esperado,
        criar_preenchimento_regional(
            tamanho,
            tamanho,
            gradiente,
            caixa,
        ) as regional,
    ):
        assert regional.tobytes() == esperado.tobytes()


@pytest.mark.parametrize(
    ("largura", "altura", "caixa"),
    [
        (64, 64, (8, 8, 56, 56)),
        (64, 64, (16, 16, 48, 48)),
        (64, 64, (24, 24, 40, 40)),
        (63, 63, (8, 8, 55, 55)),
        (63, 63, (16, 16, 47, 47)),
        (64, 63, (8, 8, 56, 55)),
        (63, 64, (8, 8, 55, 56)),
        (64, 32, (8, 4, 56, 28)),
        (63, 63, (31, 31, 32, 32)),
    ],
)
def test_radial_regional_com_simetria(
    largura,
    altura,
    caixa,
):
    gradiente = criar_gradiente("radial")

    with (
        criar_preenchimento(
            largura,
            altura,
            gradiente,
        ) as completa,
        completa.crop(caixa) as esperado,
        patch(
            "src.renderizacao.composicao.criar_gradiente_radial_centrado",
            wraps=criar_gradiente_radial_centrado,
        ) as centrado,
        criar_preenchimento_regional(
            largura,
            altura,
            gradiente,
            caixa,
        ) as regional,
    ):
        centrado.assert_called_once()

        assert regional.tobytes() == esperado.tobytes()


@pytest.mark.parametrize(
    "caixa",
    [
        (0, 0, 32, 32),
        (8, 10, 56, 56),
        (10, 8, 56, 56),
        (16, 16, 64, 64),
    ],
)
def test_radial_regional_descentrado(
    caixa,
):
    gradiente = criar_gradiente("radial")

    with (
        criar_preenchimento(
            64,
            64,
            gradiente,
        ) as completa,
        completa.crop(caixa) as esperado,
        patch(
            "src.renderizacao.composicao.criar_gradiente_radial_centrado",
        ) as centrado,
        criar_preenchimento_regional(
            64,
            64,
            gradiente,
            caixa,
        ) as regional,
    ):
        centrado.assert_not_called()

        assert regional.tobytes() == esperado.tobytes()


def test_radial_regional_geometria_deslocada_centrada():
    gradiente = criar_gradiente("radial")

    geometria = GeometriaGradiente(
        largura=32,
        altura=32,
        origem_x=8,
        origem_y=12,
    )

    caixa = (8, 12, 40, 44)

    with (
        criar_preenchimento(
            64,
            64,
            gradiente,
            geometria,
        ) as completa,
        completa.crop(caixa) as esperado,
        patch(
            "src.renderizacao.composicao.criar_gradiente_radial_centrado",
            wraps=criar_gradiente_radial_centrado,
        ) as centrado,
        criar_preenchimento_regional(
            64,
            64,
            gradiente,
            caixa,
            geometria,
        ) as regional,
    ):
        centrado.assert_called_once()

        assert regional.tobytes() == esperado.tobytes()
