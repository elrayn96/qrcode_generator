from io import BytesIO

from PIL import Image

from src.renderizacao.molduras import calcular_moldura, cores_moldura, criar_etiqueta
from src.renderizacao.resultado import ResultadoRenderizacao
from src.schemas.personalizacao import Moldura


def aplicar_moldura_png(resultado: ResultadoRenderizacao, moldura: Moldura):
    g = calcular_moldura(resultado.largura, moldura)
    cor, _ = cores_moldura(moldura)
    with (
        Image.open(BytesIO(resultado.dados)) as original,
        Image.new("RGBA", (g.largura, g.altura), cor.como_tuplo()) as imagem,
        BytesIO() as memoria,
    ):
        # Substituição exacta: não preencher a transparência do QR com a moldura.
        with original.convert("RGBA") as qr:
            imagem.paste(qr, (g.x, g.y))
        if moldura.label is not None:
            with criar_etiqueta(moldura, g) as etiqueta:
                imagem.alpha_composite(etiqueta, (0, g.faixa_y))
        imagem.save(memoria, format="PNG", compress_level=6)
        return ResultadoRenderizacao(memoria.getvalue(), "image/png", g.largura, g.altura)
