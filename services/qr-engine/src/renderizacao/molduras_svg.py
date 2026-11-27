from base64 import b64encode
from io import BytesIO
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring

from src.renderizacao.molduras import calcular_moldura, cores_moldura, criar_etiqueta
from src.renderizacao.resultado import ResultadoRenderizacao
from src.schemas.personalizacao import Moldura

NS = "http://www.w3.org/2000/svg"


def aplicar_moldura_svg(resultado: ResultadoRenderizacao, moldura: Moldura):
    g = calcular_moldura(resultado.largura, moldura)
    cor, _ = cores_moldura(moldura)
    raiz = Element(
        "svg",
        {
            "xmlns": NS,
            "width": str(g.largura),
            "height": str(g.altura),
            "viewBox": f"0 0 {g.largura} {g.altura}",
        },
    )
    # Quatro faixas disjuntas, sem pintar por baixo do QR transparente.
    n = resultado.largura
    for x, y, w, h in (
        (0, 0, g.largura, g.y),
        (0, g.y + n, g.largura, g.altura - g.y - n),
        (0, g.y, g.x, n),
        (g.x + n, g.y, g.largura - g.x - n, n),
    ):
        if w and h:
            SubElement(
                raiz,
                "rect",
                {
                    "x": str(x),
                    "y": str(y),
                    "width": str(w),
                    "height": str(h),
                    "fill": cor.como_hex(),
                    "fill-opacity": str(cor.opacidade),
                },
            )
    qr = fromstring(resultado.dados)
    # O documento original é gerado internamente; preservar IDs e viewBox.
    for elemento in qr.iter():
        if elemento.tag.startswith(f"{{{NS}}}"):
            elemento.tag = elemento.tag.split("}", 1)[1]
    qr.set("x", str(g.x))
    qr.set("y", str(g.y))
    raiz.append(qr)
    if moldura.label is not None:
        with criar_etiqueta(moldura, g) as etiqueta, BytesIO() as memoria:
            etiqueta.save(memoria, format="PNG")
            dados = b64encode(memoria.getvalue()).decode("ascii")
        SubElement(
            raiz,
            "image",
            {
                "x": "0",
                "y": str(g.faixa_y),
                "width": str(g.largura),
                "height": str(g.faixa_altura),
                "href": f"data:image/png;base64,{dados}",
            },
        )
    return ResultadoRenderizacao(
        tostring(raiz, encoding="utf-8", xml_declaration=True),
        "image/svg+xml",
        g.largura,
        g.altura,
    )
