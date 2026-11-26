import pytest
from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.gradientes import (
    GeometriaGradiente,
    Gradiente,
    PontoCor,
)
from src.renderizacao.preenchimentos import (
    PreenchimentosOlhos,
    PreenchimentoVisual,
)

PRETO = (0, 0, 0, 255)
ROXO = (124, 58, 237, 255)


def criar_gradiente(alfa=255):
    return Gradiente(
        tipo="linear",
        pontos=(
            PontoCor(0, PRETO),
            PontoCor(1, (124, 58, 237, alfa)),
        ),
    )


def test_preenchimento_solido_opaco():
    assert PreenchimentoVisual(PRETO).opaco


def test_preenchimento_solido_translucido():
    assert not PreenchimentoVisual((0, 0, 0, 128)).opaco


def test_gradiente_opaco():
    assert PreenchimentoVisual(criar_gradiente()).opaco


def test_gradiente_translucido():
    assert not PreenchimentoVisual(criar_gradiente(128)).opaco


def test_geometria_local():
    local = GeometriaGradiente(100, 100)
    global_ = GeometriaGradiente(512, 512)

    preenchimento = PreenchimentoVisual(
        criar_gradiente(),
        ambito="local",
    )

    assert preenchimento.resolver_geometria(local, global_) == local


def test_geometria_global():
    local = GeometriaGradiente(100, 100)
    global_ = GeometriaGradiente(512, 512)

    preenchimento = PreenchimentoVisual(
        criar_gradiente(),
        ambito="global",
    )

    assert preenchimento.resolver_geometria(local, global_) == global_


@pytest.mark.parametrize(
    "valor",
    [
        (0, 0, 0),
        (-1, 0, 0, 255),
        (256, 0, 0, 255),
        (True, 0, 0, 255),
        (0, 0, 0, 256),
        "#FFFFFF",
    ],
)
def test_rejeitar_preenchimento_invalido(valor):
    with pytest.raises(ErroDadosInvalidos):
        PreenchimentoVisual(valor)


def test_rejeitar_ambito_invalido():
    with pytest.raises(ErroDadosInvalidos):
        PreenchimentoVisual(
            PRETO,
            ambito="invalid",
        )


def test_olhos_com_preenchimentos_distintos():
    exterior = PreenchimentoVisual(PRETO)

    interior = PreenchimentoVisual(criar_gradiente())

    olhos = PreenchimentosOlhos(
        exterior=exterior,
        interior=interior,
    )

    assert olhos.exterior == exterior
    assert olhos.interior == interior


@pytest.mark.parametrize("regiao", ["exterior", "interior"])
@pytest.mark.parametrize(
    "valor",
    [
        (0, 0, 0, 128),
        criar_gradiente(128),
    ],
)
def test_rejeitar_olhos_translucidos(regiao, valor):
    atributos = {
        "exterior": PreenchimentoVisual(PRETO),
        "interior": PreenchimentoVisual(ROXO),
    }

    atributos[regiao] = PreenchimentoVisual(valor)

    with pytest.raises(ErroDadosInvalidos):
        PreenchimentosOlhos(**atributos)
