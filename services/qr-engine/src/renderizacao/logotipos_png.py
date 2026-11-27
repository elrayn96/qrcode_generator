from PIL import Image

from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.logotipos import GeometriaLogotipo


def guardar_fundo_logotipo(
    imagem: Image.Image,
    geometria: GeometriaLogotipo,
) -> Image.Image:
    """Guardar o fundo original da região de protecção."""
    return imagem.crop(geometria.caixa_protecao)


def renderizar_logotipo_png(
    imagem: Image.Image,
    logotipo: Image.Image,
    fundo: Image.Image,
    geometria: GeometriaLogotipo,
) -> None:
    """Restaurar o fundo e compor o logótipo em RGBA."""
    x, y, xf, yf = geometria.caixa_imagem
    px, py, pxf, pyf = geometria.caixa_protecao

    largura = xf - x
    altura = yf - y

    if imagem.mode != "RGBA" or logotipo.mode != "RGBA" or fundo.mode != "RGBA":
        raise ErroDadosInvalidos()

    if not (0 <= px <= x < xf <= pxf <= imagem.width and 0 <= py <= y < yf <= pyf <= imagem.height):
        raise ErroDadosInvalidos()

    if fundo.size != (pxf - px, pyf - py):
        raise ErroDadosInvalidos()

    with logotipo.resize(
        (largura, altura),
        resample=Image.Resampling.LANCZOS,
    ) as redimensionado:
        imagem.paste(fundo, (px, py))

        imagem.alpha_composite(
            redimensionado,
            dest=(x, y),
        )
