from dataclasses import FrozenInstanceError

import pytest
from src.core.config import carregar_configuracao


def test_configuracao_padrao(monkeypatch):
    for nome in (
        "QR_ENGINE_HOST",
        "QR_ENGINE_PORT",
        "QR_ENGINE_WORKERS",
        "APP_ENV",
        "LOG_LEVEL",
    ):
        monkeypatch.delenv(nome, raising=False)

    config = carregar_configuracao()

    assert config.host == "127.0.0.1"
    assert config.porta == 8001
    assert config.workers == 1
    assert config.ambiente == "development"
    assert config.nivel_log == "INFO"


def test_configuracao_personalizada(monkeypatch):
    monkeypatch.setenv("QR_ENGINE_PORT", "9000")
    monkeypatch.setenv("QR_ENGINE_WORKERS", "2")
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    config = carregar_configuracao()

    assert config.porta == 9000
    assert config.workers == 2
    assert config.ambiente == "testing"
    assert config.nivel_log == "DEBUG"


@pytest.mark.parametrize("valor", ["0", "-1", "65536", "abc"])
def test_porta_invalida(monkeypatch, valor):
    monkeypatch.setenv("QR_ENGINE_PORT", valor)

    with pytest.raises(ValueError):
        carregar_configuracao()


@pytest.mark.parametrize("valor", ["0", "-1", "33", "abc"])
def test_workers_invalidos(monkeypatch, valor):
    monkeypatch.setenv("QR_ENGINE_WORKERS", valor)

    with pytest.raises(ValueError):
        carregar_configuracao()


def test_ambiente_invalido(monkeypatch):
    monkeypatch.setenv("APP_ENV", "invalido")

    with pytest.raises(ValueError):
        carregar_configuracao()


def test_nivel_log_invalido(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "invalido")

    with pytest.raises(ValueError):
        carregar_configuracao()


def test_configuracao_imutavel():
    config = carregar_configuracao()

    with pytest.raises(FrozenInstanceError):
        config.porta = 9000
