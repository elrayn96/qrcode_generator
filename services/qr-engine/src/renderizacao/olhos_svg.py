from xml.etree.ElementTree import Element, SubElement

from src.renderizacao.geometria import GeometriaQR
from src.renderizacao.gradientes import (
    GeometriaGradiente,
)
from src.renderizacao.gradientes_svg import (
    RegistoGradientesSVG,
    formatar_numero,
)
from src.renderizacao.olhos import (
    EstiloOlhos,
    RegiaoOlho,
    calcular_geometria_olhos,
)
from src.renderizacao.preenchimentos import (
    PreenchimentosOlhos,
    PreenchimentoVisual,
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


def resolver_atributos(
    registo: RegistoGradientesSVG,
    regiao: RegiaoOlho,
    preenchimento: PreenchimentoVisual,
    geometria_global: GeometriaGradiente,
) -> dict[str, str]:
    geometria_local = GeometriaGradiente(
        largura=regiao.dimensao,
        altura=regiao.dimensao,
        origem_x=regiao.x,
        origem_y=regiao.y,
    )

    geometria = preenchimento.resolver_geometria(
        local=geometria_local,
        global_=geometria_global,
    )

    return registo.atributos_preenchimento(
        preenchimento.valor,
        geometria,
    )


def renderizar_olhos_svg(
    raiz: Element,
    geometria: GeometriaQR,
    estilo: EstiloOlhos,
    preenchimentos: PreenchimentosOlhos,
    registo: RegistoGradientesSVG,
) -> None:
    dimensao_matriz = geometria.dimensao_matriz * geometria.escala

    geometria_global = GeometriaGradiente(
        largura=dimensao_matriz,
        altura=dimensao_matriz,
        origem_x=geometria.origem_x,
        origem_y=geometria.origem_y,
    )

    grupo = SubElement(
        raiz,
        "g",
        {"id": "qr-eyes"},
    )

    for olho in calcular_geometria_olhos(
        geometria,
        estilo,
    ):
        atributos_exterior = resolver_atributos(
            registo,
            olho.exterior,
            preenchimentos.exterior,
            geometria_global,
        )

        atributos_interior = resolver_atributos(
            registo,
            olho.interior,
            preenchimentos.interior,
            geometria_global,
        )

        caminho_exterior = construir_caminho_regiao(olho.exterior) + construir_caminho_regiao(
            olho.abertura
        )

        SubElement(
            grupo,
            "path",
            {
                "d": caminho_exterior,
                "fill-rule": "evenodd",
                **atributos_exterior,
            },
        )

        SubElement(
            grupo,
            "path",
            {
                "d": construir_caminho_regiao(olho.interior),
                **atributos_interior,
            },
        )
