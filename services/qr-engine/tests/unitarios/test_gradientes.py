import pytest
from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.gradientes import (
    GeometriaGradiente,
    Gradiente,
    PontoCor,
    calcular_cor,
    calcular_posicao,
    interpolar_cores,
    obter_cor,
)

PRETO = (0, 0, 0, 255)
BRANCO = (255, 255, 255, 255)
VERMELHO = (255, 0, 0, 255)
AZUL = (0, 0, 255, 255)


def criar_gradiente(tipo="linear", angulo=0):
    return Gradiente(
        tipo=tipo,
        angulo=angulo,
        pontos=(
            PontoCor(0, PRETO),
            PontoCor(1, BRANCO),
        ),
    )


@pytest.mark.parametrize(
    ("posicao", "esperado"),
    [
        (0, PRETO),
        (0.5, (128, 128, 128, 255)),
        (1, BRANCO),
        (-1, PRETO),
        (2, BRANCO),
    ],
)
def test_interpolacao(posicao, esperado):
    assert (
        interpolar_cores(
            PRETO,
            BRANCO,
            posicao,
        )
        == esperado
    )


def test_interpolacao_alfa():
    assert interpolar_cores(
        (0, 0, 0, 0),
        PRETO,
        0.5,
    ) == (0, 0, 0, 128)


def test_multiplos_pontos():
    gradiente = Gradiente(
        tipo="linear",
        pontos=(
            PontoCor(0, VERMELHO),
            PontoCor(0.5, PRETO),
            PontoCor(1, AZUL),
        ),
    )

    assert obter_cor(gradiente, 0.25) == (128, 0, 0, 255)

    assert obter_cor(gradiente, 0.5) == PRETO

    assert obter_cor(gradiente, 0.75) == (0, 0, 128, 255)


def test_extender_cores_dos_extremos():
    gradiente = Gradiente(
        tipo="linear",
        pontos=(
            PontoCor(0.2, PRETO),
            PontoCor(0.8, BRANCO),
        ),
    )

    assert obter_cor(gradiente, 0) == PRETO
    assert obter_cor(gradiente, 1) == BRANCO


@pytest.mark.parametrize(
    ("angulo", "inicio", "fim"),
    [
        (0, (0, 50), (100, 50)),
        (90, (50, 0), (50, 100)),
        (180, (100, 50), (0, 50)),
        (270, (50, 100), (50, 0)),
        (360, (0, 50), (100, 50)),
        (45, (0, 0), (100, 100)),
    ],
)
def test_direcao_linear(angulo, inicio, fim):
    geometria = GeometriaGradiente(100, 100)

    gradiente = criar_gradiente(angulo=angulo)

    assert calcular_posicao(
        gradiente,
        geometria,
        *inicio,
    ) == pytest.approx(0)

    assert calcular_posicao(
        gradiente,
        geometria,
        *fim,
    ) == pytest.approx(1)


@pytest.mark.parametrize("angulo", [0, 45, 90, 180, 270, 360])
def test_centro_linear(angulo):
    assert calcular_posicao(
        criar_gradiente(angulo=angulo),
        GeometriaGradiente(100, 100),
        50,
        50,
    ) == pytest.approx(0.5)


def test_gradiente_radial():
    gradiente = criar_gradiente("radial")
    geometria = GeometriaGradiente(100, 100)

    assert calcular_cor(gradiente, geometria, 50, 50) == PRETO

    assert calcular_cor(gradiente, geometria, 0, 0) == BRANCO

    assert calcular_cor(gradiente, geometria, 25, 25) == (128, 128, 128, 255)


def test_geometria_com_deslocamento():
    geometria = GeometriaGradiente(
        largura=100,
        altura=100,
        origem_x=20,
        origem_y=30,
    )

    assert geometria.centro == (70, 80)

    assert (
        calcular_cor(
            criar_gradiente(),
            geometria,
            20,
            80,
        )
        == PRETO
    )


@pytest.mark.parametrize("posicao", [-0.1, 1.1, float("nan")])
def test_rejeitar_posicao_invalida(posicao):
    with pytest.raises(ErroDadosInvalidos):
        PontoCor(posicao, PRETO)


@pytest.mark.parametrize("quantidade", [0, 1, 9])
def test_quantidade_invalida_pontos(quantidade):
    with pytest.raises(ErroDadosInvalidos):
        Gradiente(
            tipo="linear",
            pontos=tuple(PontoCor(0, PRETO) for _ in range(quantidade)),
        )


@pytest.mark.parametrize("posicoes", [(0.5, 0.5), (0.9, 0.1)])
def test_rejeitar_ordem_invalida(posicoes):
    with pytest.raises(ErroDadosInvalidos):
        Gradiente(
            tipo="linear",
            pontos=tuple(PontoCor(posicao, PRETO) for posicao in posicoes),
        )


@pytest.mark.parametrize("angulo", [-1, 361])
def test_angulo_invalido(angulo):
    with pytest.raises(ErroDadosInvalidos):
        criar_gradiente(angulo=angulo)


@pytest.mark.parametrize(
    ("largura", "altura"),
    [(0, 100), (100, 0), (-1, 100)],
)
def test_geometria_invalida(largura, altura):
    with pytest.raises(ErroDadosInvalidos):
        GeometriaGradiente(
            largura,
            altura,
        )
