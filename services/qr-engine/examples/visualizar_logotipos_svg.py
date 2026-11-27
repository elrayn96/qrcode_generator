from pathlib import Path

from examples.visualizar_logotipos_png import criar_logotipo
from src.motor.matriz import gerar_matriz
from src.renderizacao.estilos import EstiloRenderizacao
from src.renderizacao.fundo import EstiloFundo
from src.renderizacao.gradientes import Gradiente, PontoCor
from src.renderizacao.png import renderizar_png
from src.renderizacao.preenchimentos import PreenchimentoVisual
from src.renderizacao.svg import renderizar_svg


def main():
    matriz = gerar_matriz("ntizoconnect.com", "H")

    destino = Path("demonstracao-logotipos-svg")
    destino.mkdir(exist_ok=True)

    preto = PreenchimentoVisual(
        (0, 0, 0, 255),
    )

    gradiente = Gradiente(
        tipo="linear",
        angulo=45,
        pontos=(
            PontoCor(
                posicao=0.0,
                cor=(109, 40, 217, 255),
            ),
            PontoCor(
                posicao=1.0,
                cor=(23, 37, 84, 255),
            ),
        ),
    )

    convencional = EstiloRenderizacao(
        forma="square",
        modulos=preto,
        fundo=EstiloFundo(),
    )

    casos = [
        (
            "01-convencional",
            criar_logotipo(),
            convencional,
        ),
        (
            "02-horizontal",
            criar_logotipo((300, 150)),
            convencional,
        ),
        (
            "03-vertical",
            criar_logotipo((150, 300)),
            convencional,
        ),
        (
            "04-fundo-colorido",
            criar_logotipo(),
            EstiloRenderizacao(
                forma="rounded",
                modulos=preto,
                fundo=EstiloFundo(
                    cor=(235, 225, 250, 255),
                ),
            ),
        ),
        (
            "05-fundo-transparente",
            criar_logotipo(),
            EstiloRenderizacao(
                forma="square",
                modulos=preto,
                fundo=EstiloFundo(
                    transparente=True,
                ),
            ),
        ),
        (
            "06-gradiente",
            criar_logotipo(),
            EstiloRenderizacao(
                forma="rounded",
                modulos=PreenchimentoVisual(gradiente),
                fundo=EstiloFundo(),
            ),
        ),
        (
            "07-logotipo-jpeg",
            criar_logotipo(formato="JPEG"),
            convencional,
        ),
    ]

    for nome, logo, estilo in casos:
        svg = renderizar_svg(
            matriz,
            tamanho=512,
            estilo=estilo,
            logotipo=logo,
        )

        png = renderizar_png(
            matriz,
            tamanho=512,
            estilo=estilo,
            logotipo=logo,
        )

        (destino / f"{nome}.svg").write_bytes(
            svg.dados,
        )

        (destino / f"{nome}.png").write_bytes(
            png.dados,
        )

        print(
            f"{nome}: SVG={len(svg.dados)} bytes | PNG={len(png.dados)} bytes",
        )


if __name__ == "__main__":
    main()
