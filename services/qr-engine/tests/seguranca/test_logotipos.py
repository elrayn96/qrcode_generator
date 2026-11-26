from base64 import b64encode
from io import BytesIO

import pytest
from PIL import Image, PngImagePlugin
from src.core.excecoes import (
    ErroDadosInvalidos,
    ErroFormatoNaoSuportado,
    ErroPedidoExcessivo,
)
from src.schemas.personalizacao import Logotipo
from src.seguranca.logotipos import carregar_logotipo, descodificar_logotipo


def criar_logo(dados: bytes, media_type: str = "image/png") -> Logotipo:
    return Logotipo.model_validate(
        {"mediaType": media_type, "base64": b64encode(dados).decode("ascii")}
    )


def criar_imagem(formato="PNG", tamanho=(32, 16), modo="RGB") -> bytes:
    with Image.new(modo, tamanho) as imagem, BytesIO() as memoria:
        imagem.save(memoria, format=formato)
        return memoria.getvalue()


@pytest.mark.parametrize("formato,media_type", [("PNG", "image/png"), ("JPEG", "image/jpeg")])
def test_normaliza_imagem(formato, media_type):
    with carregar_logotipo(criar_logo(criar_imagem(formato), media_type)) as imagem:
        assert imagem.mode == "RGBA"
        assert imagem.size == (32, 16)
        assert imagem.info == {}
        assert imagem.getpixel((0, 0)) == (0, 0, 0, 255)


def test_preserva_alfa_remove_metadados():
    metadados = PngImagePlugin.PngInfo()
    metadados.add_text("Comment", "privado")
    with Image.new("RGBA", (8, 8), (12, 34, 56, 100)) as original, BytesIO() as memoria:
        original.save(memoria, format="PNG", pnginfo=metadados)
        dados = memoria.getvalue()
    with carregar_logotipo(criar_logo(dados)) as imagem:
        assert imagem.getpixel((0, 0)) == (12, 34, 56, 100)
        assert imagem.info == {}


@pytest.mark.parametrize("valor", ["A", "AAA", "AB==", "AAAA="])
def test_rejeita_base64_invalido(valor):
    logo = Logotipo(mediaType="image/png", base64=valor)
    with pytest.raises(ErroDadosInvalidos):
        descodificar_logotipo(logo)


def test_limite_binario():
    assert len(descodificar_logotipo(criar_logo(b"a" * (512 * 1024)))) == 512 * 1024
    with pytest.raises(ErroPedidoExcessivo):
        descodificar_logotipo(criar_logo(b"a" * (512 * 1024 + 1)))


@pytest.mark.parametrize("formato", ["JPEG", "GIF", "BMP"])
def test_rejeita_formato_incompativel(formato):
    with pytest.raises(ErroFormatoNaoSuportado):
        carregar_logotipo(criar_logo(criar_imagem(formato)))


@pytest.mark.parametrize("dados", [b"<svg/>", b"not an image"])
def test_rejeita_dados_nao_imagem(dados):
    with pytest.raises(ErroFormatoNaoSuportado):
        carregar_logotipo(criar_logo(dados))


@pytest.mark.parametrize("tamanho", [(2049, 1), (1, 2049), (2049, 2049)])
def test_rejeita_dimensoes(tamanho):
    with pytest.raises(ErroDadosInvalidos):
        carregar_logotipo(criar_logo(criar_imagem(tamanho=tamanho)))


def test_aceita_dimensao_limite():
    with carregar_logotipo(criar_logo(criar_imagem(tamanho=(2048, 2048)))) as imagem:
        assert imagem.size == (2048, 2048)


def test_rejeita_png_truncado():
    dados = criar_imagem()[:-16]
    with pytest.raises(ErroDadosInvalidos):
        carregar_logotipo(criar_logo(dados))


def test_rejeita_png_animado():
    with (
        Image.new("RGBA", (8, 8), "red") as primeira,
        Image.new("RGBA", (8, 8), "blue") as segunda,
        BytesIO() as memoria,
    ):
        primeira.save(memoria, format="PNG", save_all=True, append_images=[segunda])
        dados = memoria.getvalue()
    with pytest.raises(ErroDadosInvalidos):
        carregar_logotipo(criar_logo(dados))
