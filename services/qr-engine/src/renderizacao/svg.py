from xml.etree.ElementTree import Element, SubElement, tostring

from src.motor.matriz import MatrizQR
from src.renderizacao.cores import BRANCO, PRETO, CorRGBA
from src.renderizacao.estilos import (
    EstiloRenderizacao,
    criar_estilo_convencional,
    validar_escala,
)
from src.renderizacao.formas import calcular_forma
from src.renderizacao.fundo import renderizar_fundo_svg
from src.renderizacao.geometria import (
    GeometriaQR,
    calcular_geometria,
)
from src.renderizacao.gradientes import GeometriaGradiente
from src.renderizacao.gradientes_svg import (
    RegistoGradientesSVG,
    formatar_numero,
)
from src.renderizacao.modulos import (
    ModuloVisual,
    iterar_modulos_escuros,
)
from src.renderizacao.olhos import (
    EstiloOlhos,
    pertence_a_olho,
)
from src.renderizacao.olhos_svg import renderizar_olhos_svg
from src.renderizacao.resultado import ResultadoRenderizacao
from src.schemas.personalizacao import Forma

SVG_NS = "http://www.w3.org/2000/svg"


def construir_caminho(
    matriz: MatrizQR,
    geometria: GeometriaQR,
    excluir_olhos: bool = False,
) -> str:
    segmentos = []

    for linha, valores in enumerate(matriz.modulos):
        coluna = 0

        def desenhavel(
            c: int,
            _linha=linha,
            _valores=valores,
            _dimensao=matriz.dimensao,
        ) -> bool:
            return _valores[c] != 0 and not (
                excluir_olhos
                and pertence_a_olho(
                    _linha,
                    c,
                    _dimensao,
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
                "r": formatar_numero(
                    geometria.raio,
                ),
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
        atributos["rx"] = formatar_numero(
            geometria.raio,
        )

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
    atributos_preenchimento: dict[str, str],
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
            funcionais.append(
                construir_segmento(modulo),
            )
        else:
            dados.append(modulo)

    SubElement(
        raiz,
        "path",
        {
            "d": "".join(funcionais),
            "shape-rendering": "crispEdges",
            **atributos_preenchimento,
        },
    )

    grupo = SubElement(
        raiz,
        "g",
        atributos_preenchimento.copy(),
    )

    for modulo in dados:
        desenhar_modulo_svg(
            grupo,
            modulo,
        )


def desenhar_modulos_svg(
    raiz: Element,
    matriz: MatrizQR,
    geometria: GeometriaQR,
    estilo: EstiloRenderizacao,
    registo: RegistoGradientesSVG,
    excluir_olhos: bool,
) -> None:
    dimensao = geometria.dimensao_matriz * geometria.escala

    geometria_gradiente = GeometriaGradiente(
        largura=dimensao,
        altura=dimensao,
        origem_x=geometria.origem_x,
        origem_y=geometria.origem_y,
    )

    atributos = registo.atributos_preenchimento(
        preenchimento=estilo.modulos.valor,
        geometria=geometria_gradiente,
    )

    if estilo.forma == "square":
        SubElement(
            raiz,
            "path",
            {
                "d": construir_caminho(
                    matriz,
                    geometria,
                    excluir_olhos=excluir_olhos,
                ),
                "shape-rendering": "crispEdges",
                **atributos,
            },
        )

        return

    desenhar_modulos_personalizados(
        raiz=raiz,
        matriz=matriz,
        geometria=geometria,
        forma=estilo.forma,
        atributos_preenchimento=atributos,
        excluir_olhos=excluir_olhos,
    )


def renderizar_svg(
    matriz: MatrizQR,
    tamanho: int = 512,
    margem: int = 4,
    cor_modulos: CorRGBA = PRETO,
    cor_fundo: CorRGBA = BRANCO,
    forma: Forma = "square",
    olhos: EstiloOlhos | None = None,
    *,
    estilo: EstiloRenderizacao | None = None,
) -> ResultadoRenderizacao:
    chamada_convencional = estilo is None

    estilo = estilo or criar_estilo_convencional(
        cor_modulos,
        cor_fundo,
        forma,
        olhos,
    )

    geometria = calcular_geometria(
        dimensao_matriz=matriz.dimensao,
        dimensao_imagem=tamanho,
        margem=margem,
    )

    validar_escala(
        geometria,
        estilo,
    )

    raiz = Element(
        "svg",
        {
            "xmlns": SVG_NS,
            "width": str(tamanho),
            "height": str(tamanho),
            "viewBox": f"0 0 {tamanho} {tamanho}",
        },
    )

    registo = RegistoGradientesSVG(raiz)

    renderizar_fundo_svg(
        raiz=raiz,
        largura=tamanho,
        altura=tamanho,
        estilo=estilo.fundo,
        registo=registo,
    )

    # Preserva a estrutura das chamadas antigas.
    excluir_olhos = olhos is not None if chamada_convencional else estilo.requer_olhos_independentes

    desenhar_modulos_svg(
        raiz=raiz,
        matriz=matriz,
        geometria=geometria,
        estilo=estilo,
        registo=registo,
        excluir_olhos=excluir_olhos,
    )

    if excluir_olhos and estilo.olhos is not None and estilo.preenchimentos_olhos is not None:
        renderizar_olhos_svg(
            raiz=raiz,
            geometria=geometria,
            estilo=estilo.olhos,
            preenchimentos=estilo.preenchimentos_olhos,
            registo=registo,
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
