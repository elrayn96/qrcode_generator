import json
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from src.core.excecoes import (
    ErroDadosInvalidos,
    ErroFormatoNaoSuportado,
    ErroPedidoExcessivo,
    ErroPedidoInvalido,
    ErroServicoIndisponivel,
)
from src.schemas.pedido import PedidoRenderizacao
from src.servicos.renderizacao import renderizar

router = APIRouter()
LIMITE_CORPO = 1024 * 1024


@router.get("/healthz", operation_id="engineHealth")
def verificar_saude():
    return {"status": "ok", "service": "qr-engine"}


@router.get("/readyz", operation_id="engineReady")
def verificar_prontidao(request: Request):
    if not request.app.state.pronto:
        raise ErroServicoIndisponivel()
    return {"status": "ok", "service": "qr-engine"}


def esquema_pedido():
    esquema = PedidoRenderizacao.model_json_schema()
    definicoes = esquema.pop("$defs", {})

    def expandir(valor):
        if isinstance(valor, list):
            return [expandir(item) for item in valor]
        if isinstance(valor, dict):
            if "$ref" in valor:
                return expandir(definicoes[valor["$ref"].rsplit("/", 1)[-1]])
            return {chave: expandir(item) for chave, item in valor.items()}
        return valor

    return expandir(esquema)


@router.post(
    "/internal/v1/render",
    operation_id="render",
    response_class=Response,
    responses={
        200: {
            "content": {
                "image/png": {"schema": {"type": "string", "format": "binary"}},
                "image/svg+xml": {"schema": {"type": "string", "format": "binary"}},
            }
        }
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {"schema": esquema_pedido()},
            },
        }
    },
)
async def renderizar_pedido(request: Request):
    if not request.app.state.pronto:
        raise ErroServicoIndisponivel()
    tipo = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if tipo != "application/json":
        raise ErroFormatoNaoSuportado()
    corpo = bytearray()
    async for bloco in request.stream():
        if len(corpo) + len(bloco) > LIMITE_CORPO:
            raise ErroPedidoExcessivo()
        corpo.extend(bloco)
    try:
        dados = json.loads(corpo.decode("utf-8"))
    except ValueError, RecursionError:
        raise ErroPedidoInvalido() from None
    try:
        pedido = PedidoRenderizacao.model_validate(dados)
    except ValidationError:
        raise ErroDadosInvalidos() from None
    resultado = await run_in_threadpool(renderizar, pedido)
    return Response(
        content=resultado.dados,
        media_type=resultado.media_type,
        headers={
            "Cache-Control": "no-store",
            "X-Request-ID": f"req_{uuid4().hex}",
            "X-Content-Type-Options": "nosniff",
        },
    )
