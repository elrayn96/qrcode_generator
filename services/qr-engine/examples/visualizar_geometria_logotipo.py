from pathlib import Path

from PIL import Image, ImageDraw
from src.motor.matriz import gerar_matriz
from src.renderizacao.geometria import calcular_geometria
from src.renderizacao.logotipos import calcular_geometria_logotipo
from src.schemas.personalizacao import Logotipo


def main():
    matriz = gerar_matriz("ntizoconnect", "H")
    g = calcular_geometria(matriz.dimensao, 512)
    logo = Logotipo(mediaType="image/png", base64="AAAA", scale=0.1, padding=1)
    destino = Path("geometria-logotipos")
    destino.mkdir(exist_ok=True)
    for nome, tamanho in [
        ("quadrado", (100, 100)),
        ("horizontal", (200, 100)),
        ("vertical", (100, 200)),
    ]:
        r = calcular_geometria_logotipo(matriz, g, logo, tamanho)
        with Image.new("RGB", (512, 512), "white") as imagem:
            draw = ImageDraw.Draw(imagem)
            for linha, valores in enumerate(matriz.modulos):
                for coluna, valor in enumerate(valores):
                    if valor:
                        x, y, xf, yf = g.caixa_modulo(linha, coluna)
                        draw.rectangle((x, y, xf - 1, yf - 1), fill="black")
            x, y, xf, yf = r.caixa_protecao
            draw.rectangle((x, y, xf - 1, yf - 1), fill="white", outline="orange")
            x, y, xf, yf = r.caixa_imagem
            draw.rectangle((x, y, xf - 1, yf - 1), fill="royalblue")
            imagem.save(destino / f"{nome}.png")


if __name__ == "__main__":
    main()
