from dataclasses import dataclass, field
from typing import Literal

TipoMedia = Literal[
    "image/png",
    "image/svg+xml",
]


@dataclass(frozen=True, slots=True)
class ResultadoRenderizacao:
    dados: bytes = field(repr=False)
    media_type: TipoMedia
    largura: int
    altura: int

    @property
    def tamanho_bytes(self) -> int:
        return len(self.dados)

    @property
    def extensao(self) -> str:
        if self.media_type == "image/png":
            return "png"

        return "svg"
