from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from src.core.excecoes import (
    ErroDadosInvalidos,
    ErroMotor,
    ErroPedidoInvalido,
)
from src.schemas.erro import Problema


def resposta_problema(
    status: int,
    codigo: str,
    titulo: str,
) -> JSONResponse:
    identificador = f"req_{uuid4().hex}"

    problema = Problema(
        type=f"urn:gqr:error:{codigo.lower().replace('_', '-')}",
        title=titulo,
        status=status,
        code=codigo,
        requestId=identificador,
    )

    cabecalhos = {
        "Cache-Control": "no-store",
        "X-Request-ID": identificador,
    }

    if status == 503:
        cabecalhos["Retry-After"] = "1"

    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        headers=cabecalhos,
        content=problema.model_dump(),
    )


async def tratar_erro_motor(
    request: Request,
    exc: ErroMotor,
) -> JSONResponse:
    return resposta_problema(
        exc.status,
        exc.codigo,
        exc.titulo,
    )


async def tratar_erro_validacao(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    json_invalido = any(erro["type"] == "json_invalid" for erro in exc.errors())

    erro = ErroPedidoInvalido() if json_invalido else ErroDadosInvalidos()

    return resposta_problema(
        erro.status,
        erro.codigo,
        erro.titulo,
    )


async def tratar_erro_http(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    codigos = {
        400: ("INVALID_REQUEST", "Malformed request"),
        404: ("RESOURCE_NOT_FOUND", "Resource not found"),
        405: ("METHOD_NOT_ALLOWED", "Method not allowed"),
        413: ("PAYLOAD_TOO_LARGE", "Payload too large"),
        415: ("UNSUPPORTED_MEDIA_TYPE", "Unsupported media type"),
        422: ("INVALID_DATA", "Invalid request"),
        503: ("SERVICE_UNAVAILABLE", "Service unavailable"),
    }

    codigo, titulo = codigos.get(
        exc.status_code,
        ("HTTP_ERROR", "Request failed"),
    )

    resposta = resposta_problema(
        exc.status_code,
        codigo,
        titulo,
    )

    if exc.status_code == 405 and exc.headers and "Allow" in exc.headers:
        resposta.headers["Allow"] = exc.headers["Allow"]

    return resposta


async def tratar_erro_inesperado(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return resposta_problema(
        500,
        "INTERNAL_ERROR",
        "Internal error",
    )


def registar_tratamento_erros(app: FastAPI) -> None:
    app.add_exception_handler(
        ErroMotor,
        tratar_erro_motor,
    )

    app.add_exception_handler(
        RequestValidationError,
        tratar_erro_validacao,
    )

    app.add_exception_handler(
        HTTPException,
        tratar_erro_http,
    )

    app.add_exception_handler(
        Exception,
        tratar_erro_inesperado,
    )
