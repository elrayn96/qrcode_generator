from dataclasses import dataclass
from unicodedata import category

from PIL import Image, ImageDraw, ImageFont

from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.cores import converter_cor
from src.schemas.personalizacao import Moldura


@dataclass(frozen=True, slots=True)
class GeometriaMoldura:
    largura: int
    altura: int
    x: int
    y: int
    faixa_y: int
    faixa_altura: int


def calcular_moldura(tamanho: int, moldura: Moldura) -> GeometriaMoldura:
    p = moldura.padding if moldura.padding is not None else 8
    faixa = max(24, tamanho // 6) if moldura.label else 0
    topo = moldura.position == "top"
    return GeometriaMoldura(
        tamanho + 2 * p,
        tamanho + 2 * p + faixa,
        p,
        p + (faixa if topo else 0),
        p if topo else p + tamanho,
        faixa,
    )


def cores_moldura(moldura: Moldura):
    return converter_cor(moldura.color or "#000000"), converter_cor(
        moldura.textColor or "#FFFFFF",
    )


def criar_etiqueta(moldura: Moldura, g: GeometriaMoldura) -> Image.Image:
    texto = moldura.label or ""
    if not texto.strip() or any(category(c).startswith("C") for c in texto):
        raise ErroDadosInvalidos()
    _, cor = cores_moldura(moldura)
    imagem = Image.new("RGBA", (g.largura, g.faixa_altura))
    try:
        desenho = ImageDraw.Draw(imagem)
        limite = max(1, g.largura - 8)
        for tamanho in range(max(8, g.faixa_altura // 2), 7, -1):
            fonte = ImageFont.load_default(size=tamanho)
            caixa = desenho.textbbox((0, 0), texto, font=fonte)
            w, h = caixa[2] - caixa[0], caixa[3] - caixa[1]
            if w <= limite and h <= g.faixa_altura - 4:
                desenho.text(
                    ((g.largura - w) // 2 - caixa[0], (g.faixa_altura - h) // 2 - caixa[1]),
                    texto,
                    font=fonte,
                    fill=cor.como_tuplo(),
                )
                return imagem
        raise ErroDadosInvalidos()
    except BaseException:
        imagem.close()
        raise
