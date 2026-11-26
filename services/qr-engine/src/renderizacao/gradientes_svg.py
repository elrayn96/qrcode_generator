from xml.etree.ElementTree import Element, SubElement

from src.renderizacao.gradientes import (
    RGBA,
    GeometriaGradiente,
    Gradiente,
)

Preenchimento = RGBA | Gradiente


def formatar_numero(valor: float) -> str:
    resultado = f"{valor:.10f}".rstrip("0").rstrip(".")

    if resultado in ("", "-0"):
        return "0"

    return resultado


def converter_hex(cor: RGBA) -> str:
    vermelho, verde, azul, _ = cor

    return f"#{vermelho:02X}{verde:02X}{azul:02X}"


def atributos_cor_solida(
    cor: RGBA,
) -> dict[str, str]:
    atributos = {
        "fill": converter_hex(cor),
    }

    alfa = cor[3]

    if alfa != 255:
        atributos["fill-opacity"] = formatar_numero(alfa / 255)

    return atributos


def atributos_ponto_cor(
    posicao: float,
    cor: RGBA,
) -> dict[str, str]:
    atributos = {
        "offset": formatar_numero(posicao),
        "stop-color": converter_hex(cor),
    }

    alfa = cor[3]

    if alfa != 255:
        atributos["stop-opacity"] = formatar_numero(alfa / 255)

    return atributos


class RegistoGradientesSVG:
    def __init__(self, raiz: Element) -> None:
        self._raiz = raiz

        self._defs: Element | None = None

        self._registos: dict[
            tuple[Gradiente, GeometriaGradiente],
            str,
        ] = {}

        self._contador = 0

    @property
    def quantidade(self) -> int:
        return len(self._registos)

    def _obter_defs(self) -> Element:
        if self._defs is not None:
            return self._defs

        existente = self._raiz.find("defs")

        if existente is not None:
            self._defs = existente
        else:
            self._defs = Element("defs")

            self._raiz.insert(
                0,
                self._defs,
            )

        return self._defs

    def _gerar_identificador(self) -> str:
        existentes = {
            elemento.get("id") for elemento in self._raiz.iter() if elemento.get("id") is not None
        }

        while True:
            self._contador += 1

            identificador = f"gqr-gradient-{self._contador}"

            if identificador not in existentes:
                return identificador

    def _adicionar_pontos(
        self,
        elemento: Element,
        gradiente: Gradiente,
    ) -> None:
        for ponto in gradiente.pontos:
            SubElement(
                elemento,
                "stop",
                atributos_ponto_cor(
                    ponto.posicao,
                    ponto.cor,
                ),
            )

    def _criar_linear(
        self,
        identificador: str,
        gradiente: Gradiente,
        geometria: GeometriaGradiente,
    ) -> Element:
        x1, y1, x2, y2 = geometria.extremos_lineares(gradiente.angulo)

        elemento = SubElement(
            self._obter_defs(),
            "linearGradient",
            {
                "id": identificador,
                "gradientUnits": "userSpaceOnUse",
                "spreadMethod": "pad",
                "color-interpolation": "sRGB",
                "x1": formatar_numero(x1),
                "y1": formatar_numero(y1),
                "x2": formatar_numero(x2),
                "y2": formatar_numero(y2),
            },
        )

        self._adicionar_pontos(
            elemento,
            gradiente,
        )

        return elemento

    def _criar_radial(
        self,
        identificador: str,
        gradiente: Gradiente,
        geometria: GeometriaGradiente,
    ) -> Element:
        centro_x, centro_y = geometria.centro

        elemento = SubElement(
            self._obter_defs(),
            "radialGradient",
            {
                "id": identificador,
                "gradientUnits": "userSpaceOnUse",
                "spreadMethod": "pad",
                "color-interpolation": "sRGB",
                "cx": formatar_numero(centro_x),
                "cy": formatar_numero(centro_y),
                "fx": formatar_numero(centro_x),
                "fy": formatar_numero(centro_y),
                "r": formatar_numero(geometria.raio),
            },
        )

        self._adicionar_pontos(
            elemento,
            gradiente,
        )

        return elemento

    def registar(
        self,
        gradiente: Gradiente,
        geometria: GeometriaGradiente,
    ) -> str:
        chave = (
            gradiente,
            geometria,
        )

        existente = self._registos.get(chave)

        if existente is not None:
            return existente

        identificador = self._gerar_identificador()

        if gradiente.tipo == "linear":
            self._criar_linear(
                identificador,
                gradiente,
                geometria,
            )
        else:
            self._criar_radial(
                identificador,
                gradiente,
                geometria,
            )

        self._registos[chave] = identificador

        return identificador

    def atributos_preenchimento(
        self,
        preenchimento: Preenchimento,
        geometria: GeometriaGradiente,
    ) -> dict[str, str]:
        if isinstance(preenchimento, Gradiente):
            identificador = self.registar(
                preenchimento,
                geometria,
            )

            return {
                "fill": f"url(#{identificador})",
            }

        return atributos_cor_solida(preenchimento)
