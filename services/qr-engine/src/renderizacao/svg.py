from xml.etree.ElementTree import Element, SubElement, tostring

from src.motor.matriz import MatrizQR
from src.renderizacao.cores import (
    BRANCO,
    PRETO,
    CorRGBA,
)
from src.renderizacao.geometria import (
    GeometriaQR,
    calcular_geometria,
)
from src.renderizacao.resultado import ResultadoRenderizacao

SVG_NS = "http://www.w3.org/2000/svg"


def atributos_cor(cor: CorRGBA) -> dict[str, str]:
    atributos = {"fill": cor.como_hex()}

    if cor.alfa != 255:
        atributos["fill-opacity"] = f"{cor.opacidade:.8f}".rstrip("0").rstrip(".")

    return atributos


def construir_caminho(
    matriz: MatrizQR,
    geometria: GeometriaQR,
) -> str:
    segmentos = []

    for linha, valores in enumerate(matriz.modulos):
        coluna = 0

        while coluna < matriz.dimensao:
            if valores[coluna] == 0:
                coluna += 1
                continue

            inicio = coluna

            while coluna < matriz.dimensao and valores[coluna] == 1:
                coluna += 1

            x = geometria.origem_x + inicio * geometria.escala

            y = geometria.origem_y + linha * geometria.escala

            largura = (coluna - inicio) * geometria.escala

            altura = geometria.escala

            segmentos.append(f"M{x} {y}h{largura}v{altura}h{-largura}z")

    return "".join(segmentos)


def renderizar_svg(
    matriz: MatrizQR,
    tamanho: int = 512,
    margem: int = 4,
    cor_modulos: CorRGBA = PRETO,
    cor_fundo: CorRGBA = BRANCO,
) -> ResultadoRenderizacao:
    geometria = calcular_geometria(
        dimensao_matriz=matriz.dimensao,
        dimensao_imagem=tamanho,
        margem=margem,
    )

    raiz = Element(
        "svg",
        {
            "xmlns": SVG_NS,
            "width": str(tamanho),
            "height": str(tamanho),
            "viewBox": f"0 0 {tamanho} {tamanho}",
            "shape-rendering": "crispEdges",
        },
    )

    if cor_fundo.alfa > 0:
        SubElement(
            raiz,
            "rect",
            {
                "x": "0",
                "y": "0",
                "width": str(tamanho),
                "height": str(tamanho),
                **atributos_cor(cor_fundo),
            },
        )

    caminho = construir_caminho(
        matriz,
        geometria,
    )

    SubElement(
        raiz,
        "path",
        {
            "d": caminho,
            **atributos_cor(cor_modulos),
        },
    )

    dados = tostring(
        raiz,
        encoding="utf-8",
        xml_declaration=True,
    )

    return ResultadoRenderizacao(
        dados=dados,
        media_type="image/svg+xml",
        largura=tamanho,
        altura=tamanho,
    )
