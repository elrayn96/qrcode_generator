from dataclasses import dataclass

from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.cores import PRETO, converter_cor
from src.renderizacao.fundo import EstiloFundo
from src.renderizacao.gradientes import Gradiente, PontoCor
from src.renderizacao.olhos import EstiloOlhos
from src.renderizacao.preenchimentos import (
    AmbitoPreenchimento,
    PreenchimentosOlhos,
    PreenchimentoVisual,
)
from src.schemas.pedido import PedidoRenderizacao
from src.schemas.personalizacao import (
    Forma,
    Modulos,
)
from src.schemas.personalizacao import (
    Gradiente as ModeloGradiente,
)


@dataclass(frozen=True, slots=True)
class EstiloRenderizacao:
    forma: Forma
    modulos: PreenchimentoVisual
    fundo: EstiloFundo
    olhos: EstiloOlhos | None = None
    preenchimentos_olhos: PreenchimentosOlhos | None = None

    def __post_init__(self) -> None:
        if not self.modulos.opaco:
            raise ErroDadosInvalidos()

        if (self.olhos is None) != (self.preenchimentos_olhos is None):
            raise ErroDadosInvalidos()

    @property
    def requer_olhos_independentes(self) -> bool:
        if self.olhos is None or self.preenchimentos_olhos is None:
            return False

        if self.olhos.forma_exterior != "square" or self.olhos.forma_interior != "square":
            return True

        return (
            self.preenchimentos_olhos.exterior != self.modulos
            or self.preenchimentos_olhos.interior != self.modulos
        )


def converter_gradiente(
    modelo: ModeloGradiente,
) -> Gradiente:
    pontos = tuple(
        PontoCor(
            posicao=ponto.position,
            cor=converter_cor(ponto.color).como_tuplo(),
        )
        for ponto in modelo.stops
    )

    return Gradiente(
        tipo=modelo.type,
        pontos=pontos,
        angulo=modelo.angle or 0,
    )


def resolver_preenchimento(
    modelo: Modulos | None,
    herdado: PreenchimentoVisual,
    ambito: AmbitoPreenchimento,
) -> PreenchimentoVisual:
    if modelo is None:
        return herdado

    if modelo.gradient is not None:
        return PreenchimentoVisual(
            valor=converter_gradiente(modelo.gradient),
            ambito=ambito,
        )

    if modelo.color is not None:
        return PreenchimentoVisual(
            valor=converter_cor(modelo.color).como_tuplo(),
            ambito=ambito,
        )

    return herdado


def resolver_fundo(
    pedido: PedidoRenderizacao,
) -> EstiloFundo:
    fundo = pedido.style.background

    if fundo is None:
        return EstiloFundo()

    if fundo.transparent is True:
        return EstiloFundo(transparente=True)

    if fundo.gradient is not None:
        return EstiloFundo(
            gradiente=converter_gradiente(
                fundo.gradient,
            ),
        )

    if fundo.color is not None:
        return EstiloFundo(
            cor=converter_cor(fundo.color).como_tuplo(),
        )

    return EstiloFundo()


def resolver_estilo_olhos(
    pedido: PedidoRenderizacao,
    modulos: PreenchimentoVisual,
) -> tuple[
    EstiloOlhos | None,
    PreenchimentosOlhos | None,
]:
    olhos = pedido.style.eyes

    if olhos is None:
        return None, None

    exterior = resolver_preenchimento(
        modelo=olhos.outer,
        herdado=modulos,
        ambito="local",
    )

    interior = resolver_preenchimento(
        modelo=olhos.inner,
        herdado=modulos,
        ambito="local",
    )

    forma_exterior: Forma = "square"
    forma_interior: Forma = "square"

    if olhos.outer is not None:
        forma_exterior = olhos.outer.shape or "square"

    if olhos.inner is not None:
        forma_interior = olhos.inner.shape or "square"

    preenchimentos = PreenchimentosOlhos(
        exterior=exterior,
        interior=interior,
    )

    estilo = EstiloOlhos(
        forma_exterior=forma_exterior,
        forma_interior=forma_interior,
        cor_exterior=PRETO,
        cor_interior=PRETO,
    )

    return estilo, preenchimentos


def resolver_estilo(
    pedido: PedidoRenderizacao,
) -> EstiloRenderizacao:
    modelo = pedido.style.modules

    preenchimento_padrao = PreenchimentoVisual(
        valor=PRETO.como_tuplo(),
        ambito="global",
    )

    modulos = resolver_preenchimento(
        modelo=modelo,
        herdado=preenchimento_padrao,
        ambito="global",
    )

    forma: Forma = "square"

    if modelo is not None:
        forma = modelo.shape or "square"

    olhos, preenchimentos_olhos = resolver_estilo_olhos(
        pedido,
        modulos,
    )

    return EstiloRenderizacao(
        forma=forma,
        modulos=modulos,
        fundo=resolver_fundo(pedido),
        olhos=olhos,
        preenchimentos_olhos=preenchimentos_olhos,
    )
