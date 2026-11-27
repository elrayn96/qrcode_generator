from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.api.rotas import router
from src.api.tratamento_erros import registar_tratamento_erros
from src.core.config import carregar_configuracao


@asynccontextmanager
async def ciclo_vida(app: FastAPI) -> AsyncIterator[None]:
    app.state.pronto = True
    try:
        yield
    finally:
        app.state.pronto = False


def criar_aplicacao() -> FastAPI:
    config = carregar_configuracao()
    desenvolvimento = config.ambiente != "production"
    aplicacao = FastAPI(
        title="GQR API interna",
        version="0.1.0",
        description="Motor interno de geração de códigos QR.",
        lifespan=ciclo_vida,
        docs_url="/docs" if desenvolvimento else None,
        redoc_url="/redoc" if desenvolvimento else None,
        openapi_url="/openapi.json" if desenvolvimento else None,
    )
    aplicacao.state.config = config
    aplicacao.state.pronto = False
    aplicacao.include_router(router)
    registar_tratamento_erros(aplicacao)
    return aplicacao


app = criar_aplicacao()

if __name__ == "__main__":
    config = carregar_configuracao()
    uvicorn.run(
        "src.main:app",
        host=config.host,
        port=config.porta,
        workers=config.workers,
        log_level=config.nivel_log.lower(),
        access_log=False,
    )
