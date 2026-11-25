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
from src.renderizacao.olhos import (
    EstiloOlhos,
    RegiaoOlho,
    calcular_geometria_olhos,
    pertence_a_olho,
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
    excluir_olhos: bool = False,
) -> str:
    segmentos = []

    for linha, valores in enumerate(matriz.modulos):
        coluna = 0
        _linha, _valores = linha, valores
        _dimensao_matriz = matriz.dimensao

        def desenhavel(
            c: int, _linha=_linha, _dimensao_matriz=_dimensao_matriz, _valores=_valores
        ) -> bool:
            return _valores[c] != 0 and not (
                excluir_olhos
                and pertence_a_olho(
                    _linha,
                    c,
                    _dimensao_matriz,
                )
            )

        while coluna < matriz.dimensao:
            if not desenhavel(coluna):
                coluna += 1
                continue

            inicio = coluna

            while coluna < matriz.dimensao and desenhavel(coluna):
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
    excluir_olhos: bool = False,
) -> None:
    funcionais = []
    dados = []

    for modulo in iterar_modulos_escuros(
        matriz,
        geometria,
        forma,
        excluir_olhos=excluir_olhos,
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
    olhos: EstiloOlhos | None = None,
) -> ResultadoRenderizacao:
    geometria = calcular_geometria(
        dimensao_matriz=matriz.dimensao,
        dimensao_imagem=tamanho,
        margem=margem,
    )

    personalizacao_curva = forma != "square" or (
        olhos is not None and (olhos.forma_exterior != "square" or olhos.forma_interior != "square")
    )

    if personalizacao_curva and geometria.escala < ESCALA_MINIMA_PERSONALIZACAO:
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
                "d": construir_caminho(
                    matriz,
                    geometria,
                    excluir_olhos=olhos is not None,
                ),
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
            excluir_olhos=olhos is not None,
        )

    if olhos is not None:
        desenhar_olhos_svg(
            raiz,
            geometria,
            olhos,
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


def construir_caminho_regiao(
    regiao: RegiaoOlho,
) -> str:
    x = regiao.x
    y = regiao.y
    d = regiao.dimensao
    r = regiao.raio

    if r == 0:
        return f"M{x} {y}h{d}v{d}h{-d}z"

    p = formatar_numero

    return (
        f"M{p(x + r)} {p(y)}"
        f"H{p(x + d - r)}"
        f"A{p(r)} {p(r)} 0 0 1 "
        f"{p(x + d)} {p(y + r)}"
        f"V{p(y + d - r)}"
        f"A{p(r)} {p(r)} 0 0 1 "
        f"{p(x + d - r)} {p(y + d)}"
        f"H{p(x + r)}"
        f"A{p(r)} {p(r)} 0 0 1 "
        f"{p(x)} {p(y + d - r)}"
        f"V{p(y + r)}"
        f"A{p(r)} {p(r)} 0 0 1 "
        f"{p(x + r)} {p(y)}z"
    )


def desenhar_olhos_svg(
    raiz: Element,
    geometria: GeometriaQR,
    estilo: EstiloOlhos,
) -> None:
    grupo = SubElement(
        raiz,
        "g",
        {"id": "qr-eyes"},
    )

    for olho in calcular_geometria_olhos(
        geometria,
        estilo,
    ):
        exterior = construir_caminho_regiao(olho.exterior)

        abertura = construir_caminho_regiao(olho.abertura)

        interior = construir_caminho_regiao(olho.interior)

        SubElement(
            grupo,
            "path",
            {
                "d": exterior + abertura,
                "fill-rule": "evenodd",
                **atributos_cor(estilo.cor_exterior),
            },
        )

        SubElement(
            grupo,
            "path",
            {
                "d": interior,
                **atributos_cor(estilo.cor_interior),
            },
        )
