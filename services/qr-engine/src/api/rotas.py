from fastapi import APIRouter, Request

from src.core.excecoes import ErroServicoIndisponivel

router = APIRouter()


@router.get("/healthz", operation_id="engineHealth")
def verificar_saude():
    return {
        "status": "ok",
        "service": "qr-engine",
    }


@router.get("/readyz", operation_id="engineReady")
def verificar_prontidao(request: Request):
    if not request.app.state.pronto:
        raise ErroServicoIndisponivel()

    return {
        "status": "ok",
        "service": "qr-engine",
    }
