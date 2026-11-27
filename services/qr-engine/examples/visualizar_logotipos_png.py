from base64 import b64encode
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw
from src.motor.matriz import gerar_matriz
from src.renderizacao.estilos import EstiloRenderizacao
from src.renderizacao.fundo import EstiloFundo
from src.renderizacao.gradientes import Gradiente, PontoCor
from src.renderizacao.png import renderizar_png
from src.renderizacao.preenchimentos import PreenchimentoVisual
from src.schemas.personalizacao import Logotipo


def criar_logotipo(
    tamanho=(200, 200),
    formato="PNG",
):
    largura, altura = tamanho

    with Image.new("RGBA", tamanho) as imagem, BytesIO() as memoria:
        desenho = ImageDraw.Draw(imagem)

        desenho.rounded_rectangle(
            (0, 0, largura - 1, altura - 1),
            radius=min(tamanho) // 5,
            fill=(37, 99, 235, 255),
        )

        centro_x = largura // 2
        centro_y = altura // 2
        raio = min(tamanho) // 4

        desenho.ellipse(
            (
                centro_x - raio,
                centro_y - raio,
                centro_x + raio,
                centro_y + raio,
            ),
            fill="white",
        )

        desenho.ellipse(
            (
                centro_x - raio // 2,
                centro_y - raio // 2,
                centro_x + raio // 2,
                centro_y + raio // 2,
            ),
            fill=(37, 99, 235, 255),
        )

        if formato == "JPEG":
            with Image.new("RGB", tamanho, "white") as rgb:
                rgb.paste(imagem, (0, 0), imagem)
                rgb.save(memoria, format="JPEG")
        else:
            imagem.save(memoria, format="PNG")

        dados = b64encode(
            memoria.getvalue(),
        ).decode("ascii")

    return Logotipo(
        mediaType="image/jpeg" if formato == "JPEG" else "image/png",
        base64=dados,
        scale=0.15,
        padding=1,
    )


def main():
    matriz = gerar_matriz("ntizoconnect.com", "H")

    destino = Path("demonstracao-logotipos-png")
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

    casos = [
        (
            "01-convencional",
            criar_logotipo(),
            EstiloRenderizacao(
                forma="square",
                modulos=preto,
                fundo=EstiloFundo(),
            ),
        ),
        (
            "02-horizontal",
            criar_logotipo((300, 150)),
            EstiloRenderizacao(
                forma="square",
                modulos=preto,
                fundo=EstiloFundo(),
            ),
        ),
        (
            "03-vertical",
            criar_logotipo((150, 300)),
            EstiloRenderizacao(
                forma="square",
                modulos=preto,
                fundo=EstiloFundo(),
            ),
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
            EstiloRenderizacao(
                forma="square",
                modulos=preto,
                fundo=EstiloFundo(),
            ),
        ),
    ]

    for nome, logo, estilo in casos:
        resultado = renderizar_png(
            matriz,
            tamanho=512,
            estilo=estilo,
            logotipo=logo,
        )

        ficheiro = destino / f"{nome}.png"

        ficheiro.write_bytes(
            resultado.dados,
        )

        print(f"Gerado: {ficheiro}")


if __name__ == "__main__":
    main()
