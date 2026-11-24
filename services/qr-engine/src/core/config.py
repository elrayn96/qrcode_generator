import os
from dataclasses import dataclass


def ler_inteiro(
    nome: str,
    padrao: int,
    minimo: int,
    maximo: int,
) -> int:
    """Lê e valida uma variável de ambiente inteira."""
    try:
        valor = int(os.getenv(nome, str(padrao)))
    except ValueError:
        raise ValueError(f"Configuracao invalida: {nome}") from None

    if not minimo <= valor <= maximo:
        raise ValueError(f"Configuracao fora dos limites: {nome}")

    return valor


@dataclass(frozen=True, slots=True)
class Configuracao:
    """Configurações centralizadas do motor QR."""

    host: str = "127.0.0.1"
    porta: int = 8001
    workers: int = 1
    ambiente: str = "development"
    nivel_log: str = "INFO"

    @classmethod
    def carregar(cls) -> Configuracao:
        ambiente = os.getenv("APP_ENV", "development")
        nivel_log = os.getenv("LOG_LEVEL", "INFO").upper()

        if ambiente not in {"development", "testing", "production"}:
            raise ValueError("Configuracao invalida: APP_ENV")

        if nivel_log not in {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }:
            raise ValueError("Configuracao invalida: LOG_LEVEL")

        return cls(
            host=os.getenv("QR_ENGINE_HOST", "127.0.0.1"),
            porta=ler_inteiro("QR_ENGINE_PORT", 8001, 1, 65535),
            workers=ler_inteiro("QR_ENGINE_WORKERS", 1, 1, 32),
            ambiente=ambiente,
            nivel_log=nivel_log,
        )


def carregar_configuracao() -> Configuracao:
    return Configuracao.carregar()
