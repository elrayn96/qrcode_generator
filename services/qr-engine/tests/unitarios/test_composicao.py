import pytest
from PIL import Image
from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.composicao import (
    RESOLUCAO_PALETA,
    aplicar_preenchimento,
    criar_paleta,
    criar_preenchimento,
    obter_indice,
)
from src.renderizacao.gradientes import (
    GeometriaGradiente,
    Gradiente,
    PontoCor,
    calcular_cor,
)

PRETO = (0, 0, 0, 255)
BRANCO = (255, 255, 255, 255)
TRANSPARENTE = (0, 0, 0, 0)
ROXO = (124, 58, 237, 255)


def criar_gradiente(tipo="linear", angulo=0):
    return Gradiente(
        tipo=tipo,
        angulo=angulo,
        pontos=(
            PontoCor(0, PRETO),
            PontoCor(1, BRANCO),
        ),
    )


def test_paleta_gradiente():
    paleta = criar_paleta(criar_gradiente())

    assert len(paleta) == RESOLUCAO_PALETA
    assert paleta[0] == PRETO
    assert paleta[-1] == BRANCO


@pytest.mark.parametrize(
    ("posicao", "indice"),
    [
        (-1, 0),
        (0, 0),
        (1, RESOLUCAO_PALETA - 1),
        (2, RESOLUCAO_PALETA - 1),
    ],
)
def test_limites_indice(posicao, indice):
    assert obter_indice(posicao) == indice


def test_preenchimento_solido():
    with criar_preenchimento(100, 100, ROXO) as imagem:
        assert imagem.mode == "RGBA"
        assert imagem.size == (100, 100)
        assert imagem.getpixel((50, 50)) == ROXO


@pytest.mark.parametrize("tipo", ["linear", "radial"])
def test_dimensoes_gradiente(tipo):
    with criar_preenchimento(
        128,
        256,
        criar_gradiente(tipo),
    ) as imagem:
        assert imagem.size == (128, 256)
        assert imagem.mode == "RGBA"


def test_gradiente_horizontal():
    with criar_preenchimento(
        128,
        128,
        criar_gradiente(angulo=0),
    ) as imagem:
        esquerda = imagem.getpixel((0, 64))
        direita = imagem.getpixel((127, 64))

        assert esquerda[0] <= 2
        assert direita[0] >= 253


def test_gradiente_vertical():
    with criar_preenchimento(
        128,
        128,
        criar_gradiente(angulo=90),
    ) as imagem:
        topo = imagem.getpixel((64, 0))
        base = imagem.getpixel((64, 127))

        assert topo[0] <= 2
        assert base[0] >= 253


def test_gradiente_radial():
    with criar_preenchimento(
        101,
        101,
        criar_gradiente("radial"),
    ) as imagem:
        centro = imagem.getpixel((50, 50))
        canto = imagem.getpixel((0, 0))

        assert centro == PRETO
        assert canto[0] >= 252


@pytest.mark.parametrize("angulo", [0, 45, 90, 180, 270, 360])
def test_consistencia_matematica_linear(angulo):
    gradiente = criar_gradiente(angulo=angulo)

    geometria = GeometriaGradiente(64, 64)

    with criar_preenchimento(64, 64, gradiente, geometria) as imagem:
        for x, y in (
            (0, 0),
            (20, 30),
            (32, 32),
            (63, 63),
        ):
            esperado = calcular_cor(
                gradiente,
                geometria,
                x + 0.5,
                y + 0.5,
            )

            resultado = imagem.getpixel((x, y))

            assert all(
                abs(a - b) <= 1
                for a, b in zip(
                    resultado,
                    esperado,
                    strict=True,
                )
            )


def test_mascara_totalmente_opaca():
    with (
        Image.new("RGBA", (32, 32), BRANCO) as imagem,
        Image.new("L", (32, 32), 255) as mascara,
    ):
        aplicar_preenchimento(imagem, mascara, ROXO)

        assert imagem.getpixel((16, 16)) == ROXO


def test_mascara_totalmente_transparente():
    with (
        Image.new("RGBA", (32, 32), BRANCO) as imagem,
        Image.new("L", (32, 32), 0) as mascara,
    ):
        aplicar_preenchimento(imagem, mascara, ROXO)

        assert imagem.getpixel((16, 16)) == BRANCO


def test_preservar_transparencia():
    with (
        Image.new("RGBA", (32, 32), TRANSPARENTE) as imagem,
        Image.new("L", (32, 32), 0) as mascara,
    ):
        mascara.paste(
            255,
            (8, 8, 24, 24),
        )

        aplicar_preenchimento(imagem, mascara, ROXO)

        assert imagem.getpixel((16, 16)) == ROXO
        assert imagem.getpixel((0, 0))[3] == 0


def test_composicao_alfa():
    with (
        Image.new("RGBA", (16, 16), TRANSPARENTE) as imagem,
        Image.new("L", (16, 16), 128) as mascara,
    ):
        aplicar_preenchimento(
            imagem,
            mascara,
            (124, 58, 237, 128),
        )

        assert imagem.getpixel((8, 8)) == (124, 58, 237, 64)


def test_mascara_gradiente():
    with (
        Image.new("RGBA", (64, 64), TRANSPARENTE) as imagem,
        Image.new("L", (64, 64), 0) as mascara,
    ):
        mascara.paste(
            255,
            (8, 8, 56, 56),
        )

        aplicar_preenchimento(
            imagem,
            mascara,
            criar_gradiente(),
        )

        assert imagem.getpixel((0, 0))[3] == 0
        assert imagem.getpixel((32, 32))[3] == 255


@pytest.mark.parametrize(
    ("largura", "altura"),
    [
        (0, 128),
        (128, 0),
        (-1, 128),
        (2049, 128),
        (128, 2049),
    ],
)
def test_rejeitar_dimensoes_invalidas(largura, altura):
    with pytest.raises(ErroDadosInvalidos):
        criar_preenchimento(
            largura,
            altura,
            ROXO,
        )


def test_rejeitar_mascara_incompativel():
    with (
        Image.new("RGBA", (32, 32)) as imagem,
        Image.new("L", (16, 16)) as mascara,
        pytest.raises(ErroDadosInvalidos),
    ):
        aplicar_preenchimento(imagem, mascara, ROXO)


def test_rejeitar_modo_mascara_invalido():
    with (
        Image.new("RGBA", (32, 32)) as imagem,
        Image.new("RGB", (32, 32)) as mascara,
        pytest.raises(ErroDadosInvalidos),
    ):
        aplicar_preenchimento(imagem, mascara, ROXO)


def test_rejeitar_modo_imagem_invalido():
    with (
        Image.new("RGB", (32, 32)) as imagem,
        Image.new("L", (32, 32)) as mascara,
        pytest.raises(ErroDadosInvalidos),
    ):
        aplicar_preenchimento(imagem, mascara, ROXO)
