import re
from dataclasses import dataclass

from src.core.excecoes import ErroDadosInvalidos

PADRAO_COR = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?")


@dataclass(frozen=True, slots=True)
class CorRGBA:
    vermelho: int
    verde: int
    azul: int
    alfa: int = 255

    def como_tuplo(self) -> tuple[int, int, int, int]:
        return (
            self.vermelho,
            self.verde,
            self.azul,
            self.alfa,
        )

    def como_hex(self) -> str:
        return f"#{self.vermelho:02X}{self.verde:02X}{self.azul:02X}"

    @property
    def opacidade(self) -> float:
        return self.alfa / 255


def converter_cor(valor: str) -> CorRGBA:
    if not isinstance(valor, str) or PADRAO_COR.fullmatch(valor) is None:
        raise ErroDadosInvalidos()

    hexadecimal = valor[1:]

    if len(hexadecimal) == 6:
        hexadecimal += "FF"

    return CorRGBA(
        vermelho=int(hexadecimal[0:2], 16),
        verde=int(hexadecimal[2:4], 16),
        azul=int(hexadecimal[4:6], 16),
        alfa=int(hexadecimal[6:8], 16),
    )


PRETO = converter_cor("#000000")
BRANCO = converter_cor("#FFFFFF")
TRANSPARENTE = converter_cor("#00000000")
