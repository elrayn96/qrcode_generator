from dataclasses import dataclass
from typing import Literal

from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.gradientes import (
    RGBA,
    GeometriaGradiente,
    Gradiente,
)

TipoPreenchimento = RGBA | Gradiente
AmbitoPreenchimento = Literal["local", "global"]


@dataclass(frozen=True, slots=True)
class PreenchimentoVisual:
    valor: TipoPreenchimento
    ambito: AmbitoPreenchimento = "local"

    def __post_init__(self) -> None:
        if self.ambito not in ("local", "global"):
            raise ErroDadosInvalidos()

        if isinstance(self.valor, Gradiente):
            return

        if not isinstance(self.valor, tuple):
            raise ErroDadosInvalidos()

        if len(self.valor) != 4:
            raise ErroDadosInvalidos()

        if any(type(canal) is not int or not 0 <= canal <= 255 for canal in self.valor):
            raise ErroDadosInvalidos()

    @property
    def opaco(self) -> bool:
        if isinstance(self.valor, Gradiente):
            return all(ponto.cor[3] == 255 for ponto in self.valor.pontos)

        return self.valor[3] == 255

    def resolver_geometria(
        self,
        local: GeometriaGradiente,
        global_: GeometriaGradiente,
    ) -> GeometriaGradiente:
        if self.ambito == "global":
            return global_

        return local


@dataclass(frozen=True, slots=True)
class PreenchimentosOlhos:
    exterior: PreenchimentoVisual
    interior: PreenchimentoVisual

    def __post_init__(self) -> None:
        if not self.exterior.opaco:
            raise ErroDadosInvalidos()

        if not self.interior.opaco:
            raise ErroDadosInvalidos()
