from dataclasses import dataclass

import segno
from segno import DataOverflowError

from src.core.excecoes import (
    ErroCapacidadeQR,
    ErroCodificacaoQR,
    ErroDadosInvalidos,
)
from src.schemas.personalizacao import CorrecaoErro


@dataclass(frozen=True, slots=True)
class MatrizQR:
    """Representação imutável de um código QR convencional."""

    modulos: tuple[tuple[int, ...], ...]
    tipos_modulos: tuple[tuple[int, ...], ...]
    versao: int
    correcao_erros: str
    mascara: int

    @property
    def dimensao(self) -> int:
        """Número de módulos por lado."""
        return len(self.modulos)

    @property
    def total_modulos(self) -> int:
        """Número total de módulos da matriz."""
        return self.dimensao**2

    @property
    def modulos_escuros(self) -> int:
        """Número de módulos escuros."""
        return sum(sum(linha) for linha in self.modulos)

    @property
    def modulos_claros(self) -> int:
        """Número de módulos claros."""
        return self.total_modulos - self.modulos_escuros

    def modulo_escuro(self, linha: int, coluna: int) -> bool:
        """Indica se um módulo é escuro."""
        self._validar_coordenadas(linha, coluna)

        return self.modulos[linha][coluna] == 1

    def tipo_modulo(self, linha: int, coluna: int) -> int:
        """Devolve o tipo funcional de um módulo."""
        self._validar_coordenadas(linha, coluna)

        return self.tipos_modulos[linha][coluna]

    def _validar_coordenadas(
        self,
        linha: int,
        coluna: int,
    ) -> None:
        if not (0 <= linha < self.dimensao and 0 <= coluna < self.dimensao):
            raise IndexError("Coordenadas fora da matriz")


def gerar_matriz(
    conteudo: str,
    correcao_erros: CorrecaoErro = "M",
) -> MatrizQR:
    """Gera uma matriz QR convencional através do Segno."""

    if not isinstance(conteudo, str):
        raise ErroDadosInvalidos()

    if not 1 <= len(conteudo) <= 4096:
        raise ErroDadosInvalidos()

    if correcao_erros not in ("L", "M", "Q", "H"):
        raise ErroDadosInvalidos()

    try:
        codigo = segno.make_qr(
            conteudo,
            error=correcao_erros,
            encoding="utf-8",
            eci=True,
            boost_error=False,
        )

    except DataOverflowError:
        raise ErroCapacidadeQR() from None

    except UnicodeError:
        raise ErroCodificacaoQR() from None

    modulos = tuple(tuple(linha) for linha in codigo.matrix)

    tipos_modulos = tuple(
        tuple(linha)
        for linha in codigo.matrix_iter(
            scale=1,
            border=0,
            verbose=True,
        )
    )

    return MatrizQR(
        modulos=modulos,
        tipos_modulos=tipos_modulos,
        versao=int(codigo.version),
        correcao_erros=str(codigo.error),
        mascara=int(codigo.mask),
    )
