from xml.etree.ElementTree import Element, SubElement, tostring

from src.core.excecoes import ErroDimensaoQR
from src.motor.matriz import MatrizQR
from src.renderizacao.cores import BRANCO, PRETO, CorRGBA
from src.renderizacao.formas import (
    ESCALA_MINIMA_PERSONALIZACAO,
    calcular_forma,
)
from src.renderizacao.geometria import (
    GeometriaQR,
    calcular_geometria,
)
from src.renderizacao.modulos import (
    ModuloVisual,
    iterar_modulos_escuros,
)
from src.renderizacao.resultado import ResultadoRenderizacao
from src.schemas.personalizacao import Forma

SVG_NS = "http://www.w3.org/2000/svg"


def formatar_numero(valor: float) -> str:
    return f"{valor:.6f}".rstrip("0").rstrip(".")


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


def construir_segmento(
    modulo: ModuloVisual,
) -> str:
    x = modulo.x
    y = modulo.y
    escala = modulo.escala

    return f"M{x} {y}h{escala}v{escala}h{-escala}z"


def desenhar_modulo_svg(
    grupo: Element,
    modulo: ModuloVisual,
) -> None:
    geometria = calcular_forma(
        modulo.x,
        modulo.y,
        modulo.escala,
        modulo.forma,
    )

    if modulo.forma == "dots":
        SubElement(
            grupo,
            "circle",
            {
                "cx": formatar_numero(geometria.x + geometria.largura / 2),
                "cy": formatar_numero(geometria.y + geometria.altura / 2),
                "r": formatar_numero(geometria.raio),
            },
        )

        return

    atributos = {
        "x": formatar_numero(geometria.x),
        "y": formatar_numero(geometria.y),
        "width": formatar_numero(geometria.largura),
        "height": formatar_numero(geometria.altura),
    }

    if modulo.forma == "rounded":
        atributos["rx"] = formatar_numero(geometria.raio)

        atributos["ry"] = atributos["rx"]

    SubElement(
        grupo,
        "rect",
        atributos,
    )


def desenhar_modulos_personalizados(
    raiz: Element,
    matriz: MatrizQR,
    geometria: GeometriaQR,
    forma: Forma,
    cor_modulos: CorRGBA,
) -> None:
    funcionais = []
    dados = []

    for modulo in iterar_modulos_escuros(
        matriz,
        geometria,
        forma,
    ):
        if modulo.funcional:
            funcionais.append(construir_segmento(modulo))
        else:
            dados.append(modulo)

    SubElement(
        raiz,
        "path",
        {
            "d": "".join(funcionais),
            "shape-rendering": "crispEdges",
            **atributos_cor(cor_modulos),
        },
    )

    grupo = SubElement(
        raiz,
        "g",
        atributos_cor(cor_modulos),
    )

    for modulo in dados:
        desenhar_modulo_svg(
            grupo,
            modulo,
        )


def renderizar_svg(
    matriz: MatrizQR,
    tamanho: int = 512,
    margem: int = 4,
    cor_modulos: CorRGBA = PRETO,
    cor_fundo: CorRGBA = BRANCO,
    forma: Forma = "square",
) -> ResultadoRenderizacao:
    geometria = calcular_geometria(
        dimensao_matriz=matriz.dimensao,
        dimensao_imagem=tamanho,
        margem=margem,
    )

    if forma != "square" and geometria.escala < ESCALA_MINIMA_PERSONALIZACAO:
        raise ErroDimensaoQR()

    raiz = Element(
        "svg",
        {
            "xmlns": SVG_NS,
            "width": str(tamanho),
            "height": str(tamanho),
            "viewBox": f"0 0 {tamanho} {tamanho}",
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

    if forma == "square":
        SubElement(
            raiz,
            "path",
            {
                "d": construir_caminho(matriz, geometria),
                "shape-rendering": "crispEdges",
                **atributos_cor(cor_modulos),
            },
        )

    else:
        desenhar_modulos_personalizados(
            raiz,
            matriz,
            geometria,
            forma,
            cor_modulos,
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
