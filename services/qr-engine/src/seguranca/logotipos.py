from base64 import b64decode, b64encode
from binascii import Error
from io import BytesIO

from PIL import Image, ImageFile, UnidentifiedImageError

from src.core.excecoes import (
    ErroDadosInvalidos,
    ErroFormatoNaoSuportado,
    ErroPedidoExcessivo,
)
from src.schemas.personalizacao import Logotipo

MAX_BYTES_LOGOTIPO = 512 * 1024
MAX_DIMENSAO_LOGOTIPO = 2048
MAX_PIXELS_LOGOTIPO = MAX_DIMENSAO_LOGOTIPO**2
FORMATOS = {"image/png": "PNG", "image/jpeg": "JPEG"}


def descodificar_logotipo(logotipo: Logotipo) -> bytes:
    try:
        dados = b64decode(logotipo.base64, validate=True)
    except Error, ValueError:
        raise ErroDadosInvalidos() from None

    if not dados or b64encode(dados).decode("ascii") != logotipo.base64:
        raise ErroDadosInvalidos()
    if len(dados) > MAX_BYTES_LOGOTIPO:
        raise ErroPedidoExcessivo()
    return dados


def validar_imagem(imagem: Image.Image, formato: str) -> None:
    if imagem.format != formato:
        raise ErroFormatoNaoSuportado()
    largura, altura = imagem.size
    if (
        not 1 <= largura <= MAX_DIMENSAO_LOGOTIPO
        or not 1 <= altura <= MAX_DIMENSAO_LOGOTIPO
        or largura * altura > MAX_PIXELS_LOGOTIPO
    ):
        raise ErroDadosInvalidos()
    if getattr(imagem, "n_frames", 1) != 1 or getattr(imagem, "is_animated", False):
        raise ErroDadosInvalidos()


def carregar_logotipo(logotipo: Logotipo) -> Image.Image:
    """Devolver uma imagem RGBA independente, sem metadados; fechar após utilizar."""
    dados = descodificar_logotipo(logotipo)
    formato = FORMATOS[logotipo.mediaType]
    # A aplicação não deve activar a aceitação global de imagens truncadas.
    if ImageFile.LOAD_TRUNCATED_IMAGES:
        raise ErroDadosInvalidos()
    try:
        with Image.open(BytesIO(dados), formats=("PNG", "JPEG")) as imagem:
            validar_imagem(imagem, formato)
            imagem.verify()
        with Image.open(BytesIO(dados), formats=("PNG", "JPEG")) as imagem:
            validar_imagem(imagem, formato)
            imagem.load()
            with imagem.convert("RGBA") as rgba:
                return Image.frombytes("RGBA", rgba.size, rgba.tobytes())
    except UnidentifiedImageError:
        raise ErroFormatoNaoSuportado() from None
    except OSError, ValueError, SyntaxError, OverflowError, Image.DecompressionBombError:
        raise ErroDadosInvalidos() from None
