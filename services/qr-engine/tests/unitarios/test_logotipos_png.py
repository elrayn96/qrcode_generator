from base64 import b64encode
from io import BytesIO

import pytest
from PIL import Image
from src.core.excecoes import ErroDadosInvalidos
from src.motor.matriz import gerar_matriz
from src.renderizacao.estilos import EstiloRenderizacao
from src.renderizacao.fundo import EstiloFundo
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.logotipos import (
    GeometriaLogotipo,
    calcular_geometria_logotipo,
)
from src.renderizacao.logotipos_png import (
    guardar_fundo_logotipo,
    renderizar_logotipo_png,
)
from src.renderizacao.png import renderizar_png
from src.renderizacao.preenchimentos import PreenchimentoVisual
from src.schemas.personalizacao import Logotipo


def criar_logo(
    formato="PNG",
    cor=(255, 0, 0, 255),
    tamanho=(40, 20),
    **opcoes,
):
    with Image.new("RGBA", tamanho, cor) as imagem, BytesIO() as memoria:
        if formato == "JPEG":
            with imagem.convert("RGB") as rgb:
                rgb.save(memoria, format="JPEG")
        else:
            imagem.save(memoria, format="PNG")

        dados = b64encode(
            memoria.getvalue(),
        ).decode("ascii")

    return Logotipo(
        mediaType="image/jpeg" if formato == "JPEG" else "image/png",
        base64=dados,
        scale=0.1,
        **opcoes,
    )


@pytest.fixture
def matriz():
    return gerar_matriz("ntizoconnect", "H")


@pytest.mark.parametrize(
    "formato",
    ["PNG", "JPEG"],
)
def test_renderiza_logotipo(matriz, formato):
    logo = criar_logo(formato)

    resultado = renderizar_png(
        matriz,
        logotipo=logo,
    )

    assert resultado.media_type == "image/png"
    assert resultado.largura == 512
    assert resultado.altura == 512

    g = calcular_geometria(matriz.dimensao, 512)

    r = calcular_geometria_logotipo(
        matriz,
        g,
        logo,
        (40, 20),
    )

    x, y, xf, yf = r.caixa_imagem

    with Image.open(BytesIO(resultado.dados)) as imagem:
        vermelho, verde, azul, alfa = imagem.getpixel(
            ((x + xf) // 2, (y + yf) // 2),
        )

        assert vermelho >= 250
        assert verde <= 5
        assert azul <= 5
        assert alfa == 255


@pytest.mark.parametrize(
    "cor",
    [
        (255, 255, 255, 255),
        (100, 150, 200, 255),
        (100, 150, 200, 128),
        (0, 0, 0, 0),
    ],
)
def test_preserva_fundo(matriz, cor):
    estilo = EstiloRenderizacao(
        forma="square",
        modulos=PreenchimentoVisual(
            (0, 0, 0, 255),
        ),
        fundo=EstiloFundo(cor=cor),
    )

    logo = criar_logo(
        cor=(255, 0, 0, 0),
        padding=1,
    )

    resultado = renderizar_png(
        matriz,
        estilo=estilo,
        logotipo=logo,
    )

    g = calcular_geometria(matriz.dimensao, 512)

    r = calcular_geometria_logotipo(
        matriz,
        g,
        logo,
        (40, 20),
    )

    with (
        Image.open(BytesIO(resultado.dados)) as imagem,
        imagem.crop(r.caixa_protecao) as regiao,
    ):
        assert set(regiao.getdata()) == {cor}


def test_composicao_alfa():
    geometria = GeometriaLogotipo(
        caixa_imagem=(4, 4, 8, 8),
        caixa_protecao=(2, 2, 10, 10),
    )

    with (
        Image.new("RGBA", (12, 12), "white") as imagem,
        Image.new("RGBA", (4, 4), (255, 0, 0, 128)) as logo,
        guardar_fundo_logotipo(imagem, geometria) as fundo,
    ):
        imagem.paste(
            (0, 0, 0, 255),
            geometria.caixa_protecao,
        )

        renderizar_logotipo_png(
            imagem,
            logo,
            fundo,
            geometria,
        )

        assert imagem.getpixel((5, 5)) == (255, 127, 127, 255)
        assert imagem.getpixel((2, 2)) == (255, 255, 255, 255)


def test_preserva_exterior(matriz):
    logo = criar_logo(padding=1)

    original = renderizar_png(matriz)

    personalizado = renderizar_png(
        matriz,
        logotipo=logo,
    )

    g = calcular_geometria(matriz.dimensao, 512)

    r = calcular_geometria_logotipo(
        matriz,
        g,
        logo,
        (40, 20),
    )

    x, y, xf, yf = r.caixa_protecao

    caixas = [
        (0, 0, 512, y),
        (0, yf, 512, 512),
        (0, y, x, yf),
        (xf, y, 512, yf),
    ]

    with (
        Image.open(BytesIO(original.dados)) as antes,
        Image.open(BytesIO(personalizado.dados)) as depois,
    ):
        for caixa in caixas:
            with (
                antes.crop(caixa) as a,
                depois.crop(caixa) as b,
            ):
                assert a.tobytes() == b.tobytes()


def test_sem_logotipo(matriz):
    assert (
        renderizar_png(matriz).dados
        == renderizar_png(
            matriz,
            logotipo=None,
        ).dados
    )


@pytest.mark.parametrize(
    "modo",
    ["RGB", "L"],
)
def test_rejeita_modo_invalido(modo):
    geometria = GeometriaLogotipo(
        caixa_imagem=(4, 4, 8, 8),
        caixa_protecao=(2, 2, 10, 10),
    )

    with (
        Image.new(modo, (12, 12)) as imagem,
        Image.new("RGBA", (4, 4)) as logo,
        Image.new("RGBA", (8, 8)) as fundo,
        pytest.raises(ErroDadosInvalidos),
    ):
        renderizar_logotipo_png(
            imagem,
            logo,
            fundo,
            geometria,
        )


def test_rejeita_fundo_incompativel():
    geometria = GeometriaLogotipo(
        caixa_imagem=(4, 4, 8, 8),
        caixa_protecao=(2, 2, 10, 10),
    )

    with (
        Image.new("RGBA", (12, 12)) as imagem,
        Image.new("RGBA", (4, 4)) as logo,
        Image.new("RGBA", (2, 2)) as fundo,
        pytest.raises(ErroDadosInvalidos),
    ):
        renderizar_logotipo_png(
            imagem,
            logo,
            fundo,
            geometria,
        )


def test_rejeita_geometria_invalida():
    geometria = GeometriaLogotipo(
        caixa_imagem=(4, 4, 8, 8),
        caixa_protecao=(-1, -1, 10, 10),
    )

    with (
        Image.new("RGBA", (12, 12)) as imagem,
        Image.new("RGBA", (4, 4)) as logo,
        Image.new("RGBA", (11, 11)) as fundo,
        pytest.raises(ErroDadosInvalidos),
    ):
        renderizar_logotipo_png(
            imagem,
            logo,
            fundo,
            geometria,
        )


def test_rejeita_logotipo_invalido(matriz):
    logo = Logotipo(
        mediaType="image/png",
        base64="AB==",
    )

    with pytest.raises(ErroDadosInvalidos):
        renderizar_png(
            matriz,
            logotipo=logo,
        )
