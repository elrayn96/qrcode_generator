from pathlib import Path
from statistics import median
from time import perf_counter

from examples.visualizar_logotipos_png import criar_logotipo
from src.schemas.pedido import PedidoRenderizacao
from src.servicos.renderizacao import renderizar


def main():
    destino = Path("validacao-fase4")
    destino.mkdir(exist_ok=True)
    logo = criar_logotipo().model_dump(exclude_none=True)
    for formato in ("png", "svg"):
        for tamanho in (256, 512, 1024, 2048):
            for nome, estilo in (
                ("base", {}),
                ("moldura", {"frame": {"label": "Leia o QR", "position": "bottom"}}),
                ("completo", {"logo": logo, "frame": {"label": "Leia o QR", "position": "top"}}),
                ("transparente", {"logo": logo, "background": {"transparent": True}}),
            ):
                pedido = PedidoRenderizacao.model_validate(
                    {
                        "content": "ntizoconnect",
                        "output": {"format": formato, "size": tamanho},
                        "options": {"errorCorrection": "H"},
                        "style": estilo,
                    }
                )
                renderizar(pedido)
                tempos = []
                for _ in range(3):
                    inicio = perf_counter()
                    resultado = renderizar(pedido)
                    tempos.append((perf_counter() - inicio) * 1000)
                (destino / f"{tamanho}-{nome}.{formato}").write_bytes(resultado.dados)
                print(f"{formato},{tamanho},{nome},{median(tempos):.3f},{len(resultado.dados)}")


if __name__ == "__main__":
    main()
