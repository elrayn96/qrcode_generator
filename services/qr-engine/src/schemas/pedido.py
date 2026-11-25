from pydantic import Field

from src.schemas.personalizacao import (
    ModeloEstrito,
    Opcoes,
    Personalizacao,
    Saida,
)


class PedidoRenderizacao(ModeloEstrito):
    """Pedido de renderização recebido do API Gateway."""

    content: str = Field(
        min_length=1,
        max_length=4096,
        repr=False,
    )

    output: Saida = Field(default_factory=Saida)

    options: Opcoes = Field(default_factory=Opcoes)

    style: Personalizacao = Field(
        default_factory=Personalizacao,
    )
