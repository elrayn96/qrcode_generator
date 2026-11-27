from pathlib import Path
from statistics import median
from time import perf_counter

from examples.visualizar_logotipos_png import criar_logotipo
from src.schemas.pedido import PedidoRenderizacao
from src.servicos.renderizacao import renderizar

RESOLUCOES = (256, 512, 1024, 2048)
FORMATOS = ("png", "svg")
REPETICOES = 3


def criar_pedido(
    formato,
    tamanho,
    logotipo=None,
    transparente=False,
):
    estilo = {
        "modules": {
            "shape": "rounded",
            "gradient": {
                "type": "linear",
                "angle": 45,
                "stops": [
                    {
                        "position": 0.0,
                        "color": "#6D28D9",
                    },
                    {
                        "position": 1.0,
                        "color": "#172554",
                    },
                ],
            },
        },
        "eyes": {
            "outer": {
                "shape": "rounded",
                "color": "#172554",
            },
            "inner": {
                "shape": "dots",
                "color": "#6D28D9",
            },
        },
        "background": {
            "transparent": transparente,
        },
    }

    if logotipo is not None:
        estilo["logo"] = logotipo.model_dump(
            exclude_none=True,
        )

    return PedidoRenderizacao.model_validate(
        {
            "content": "ntizoconnect.com",
            "output": {
                "format": formato,
                "size": tamanho,
                "margin": 4,
            },
            "options": {
                "errorCorrection": "H",
            },
            "style": estilo,
        },
    )


def medir(pedido):
    renderizar(pedido)

    tempos = []

    for _ in range(REPETICOES):
        inicio = perf_counter()

        resultado = renderizar(pedido)

        tempos.append(
            (perf_counter() - inicio) * 1000,
        )

    return median(tempos), resultado


def main():
    destino = Path("validacao-final-logotipos")
    destino.mkdir(exist_ok=True)

    logo = criar_logotipo()

    print(
        f"{'Formato':<9}{'Tamanho':>9}{'Sem logo':>14}{'Com logo':>14}{'Dif. ms':>12}{'Dif. %':>10}"
    )

    for formato in FORMATOS:
        for tamanho in RESOLUCOES:
            pedido_base = criar_pedido(
                formato,
                tamanho,
            )

            pedido_logo = criar_pedido(
                formato,
                tamanho,
                logotipo=logo,
            )

            antes, original = medir(pedido_base)
            depois, personalizado = medir(pedido_logo)

            diferenca = depois - antes

            percentual = diferenca / antes * 100 if antes > 0 else 0

            print(
                f"{formato:<9}"
                f"{tamanho:>9}"
                f"{antes:>14.3f}"
                f"{depois:>14.3f}"
                f"{diferenca:>12.3f}"
                f"{percentual:>9.2f}%"
            )

            (destino / f"{tamanho}-sem-logo.{formato}").write_bytes(original.dados)

            (destino / f"{tamanho}-com-logo.{formato}").write_bytes(personalizado.dados)

    for formato in FORMATOS:
        pedido = criar_pedido(
            formato,
            512,
            logotipo=logo,
            transparente=True,
        )

        resultado = renderizar(pedido)

        (destino / f"transparente.{formato}").write_bytes(resultado.dados)

    print()
    print(f"Ficheiros guardados em: {destino.resolve()}")


if __name__ == "__main__":
    main()
