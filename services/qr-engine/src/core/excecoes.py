class ErroMotor(Exception):
    """Excepção controlada do motor QR."""

    status = 500
    codigo = "INTERNAL_ERROR"
    titulo = "Internal error"


class ErroDadosInvalidos(ErroMotor):
    status = 422
    codigo = "INVALID_DATA"
    titulo = "Invalid request"


class ErroPedidoInvalido(ErroMotor):
    status = 400
    codigo = "INVALID_REQUEST"
    titulo = "Malformed request"


class ErroPedidoExcessivo(ErroMotor):
    status = 413
    codigo = "PAYLOAD_TOO_LARGE"
    titulo = "Payload too large"


class ErroFormatoNaoSuportado(ErroMotor):
    status = 415
    codigo = "UNSUPPORTED_MEDIA_TYPE"
    titulo = "Unsupported media type"


class ErroServicoIndisponivel(ErroMotor):
    status = 503
    codigo = "SERVICE_UNAVAILABLE"
    titulo = "Service unavailable"


class ErroTempoExcedido(ErroMotor):
    status = 504
    codigo = "GATEWAY_TIMEOUT"
    titulo = "Processing timeout"


class ErroCapacidadeQR(ErroDadosInvalidos):
    """Conteúdo superior à capacidade de um código QR."""


class ErroCodificacaoQR(ErroDadosInvalidos):
    """Conteúdo incompatível com a codificação suportada."""


class ErroDimensaoQR(ErroDadosInvalidos):
    """Dimensão insuficiente para representar a matriz QR."""
