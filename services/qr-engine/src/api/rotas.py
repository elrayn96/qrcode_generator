from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

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
        return JSONResponse(
            status_code=503,
            media_type="application/problem+json",
            headers={
                "Retry-After": "1",
                "Cache-Control": "no-store",
            },
            content={
                "type": "urn:gqr:error:service-unavailable",
                "title": "Service unavailable",
                "status": 503,
                "code": "SERVICE_UNAVAILABLE",
                "requestId": f"req_{uuid4().hex}",
            },
        )

    return {
        "status": "ok",
        "service": "qr-engine",
    }
