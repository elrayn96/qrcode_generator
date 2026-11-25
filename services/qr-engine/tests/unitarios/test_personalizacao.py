import pytest
from pydantic import ValidationError
from src.schemas.personalizacao import (
    Fundo,
    Gradiente,
    Logotipo,
    Modulos,
    Moldura,
    Personalizacao,
)


@pytest.mark.parametrize(
    "cor",
    ["#000000", "#FFFFFF", "#7C3AED", "#123456FF"],
)
def test_cores_validas(cor):
    assert Modulos(color=cor).color == cor


@pytest.mark.parametrize(
    "cor",
    ["red", "123456", "#123", "#GGGGGG", "#123456789"],
)
def test_cores_invalidas(cor):
    with pytest.raises(ValidationError):
        Modulos(color=cor)


@pytest.mark.parametrize(
    "forma",
    ["square", "rounded", "dots"],
)
def test_formas_validas(forma):
    assert Modulos(shape=forma).shape == forma


def test_forma_invalida():
    with pytest.raises(ValidationError):
        Modulos(shape="triangle")


def criar_gradiente():
    return {
        "type": "linear",
        "angle": 90,
        "stops": [
            {"position": 0, "color": "#7C3AED"},
            {"position": 1, "color": "#2563EB"},
        ],
    }


def test_gradiente_valido():
    gradiente = Gradiente.model_validate(criar_gradiente())

    assert gradiente.angle == 90
    assert len(gradiente.stops) == 2


@pytest.mark.parametrize("angulo", [-1, 361])
def test_angulo_invalido(angulo):
    dados = criar_gradiente()
    dados["angle"] = angulo

    with pytest.raises(ValidationError):
        Gradiente.model_validate(dados)


@pytest.mark.parametrize("quantidade", [0, 1, 9])
def test_quantidade_pontos_invalida(quantidade):
    dados = criar_gradiente()

    dados["stops"] = [{"position": 0, "color": "#000000"} for _ in range(quantidade)]

    with pytest.raises(ValidationError):
        Gradiente.model_validate(dados)


@pytest.mark.parametrize("posicao", [-0.1, 1.1])
def test_posicao_gradiente_invalida(posicao):
    dados = criar_gradiente()
    dados["stops"][0]["position"] = posicao

    with pytest.raises(ValidationError):
        Gradiente.model_validate(dados)


def test_cor_e_gradiente_simultaneos():
    with pytest.raises(ValidationError):
        Modulos.model_validate(
            {
                "color": "#000000",
                "gradient": criar_gradiente(),
            }
        )


def test_fundo_transparente():
    fundo = Fundo(transparent=True)

    assert fundo.transparent is True


@pytest.mark.parametrize(
    "formato",
    ["image/png", "image/jpeg"],
)
def test_formato_logotipo_valido(formato):
    logo = Logotipo(
        mediaType=formato,
        base64="YWJj",
        scale=0.15,
    )

    assert logo.mediaType == formato


@pytest.mark.parametrize(
    "formato",
    ["image/svg+xml", "application/pdf", "image/gif"],
)
def test_formato_logotipo_invalido(formato):
    with pytest.raises(ValidationError):
        Logotipo(
            mediaType=formato,
            base64="YWJj",
        )


@pytest.mark.parametrize("escala", [0, 0.04, 0.21, 1])
def test_escala_logotipo_invalida(escala):
    with pytest.raises(ValidationError):
        Logotipo(
            mediaType="image/png",
            base64="YWJj",
            scale=escala,
        )


def test_logotipo_base64_invalido():
    with pytest.raises(ValidationError):
        Logotipo(
            mediaType="image/png",
            base64="<script>",
        )


def test_logotipo_excessivo():
    with pytest.raises(ValidationError):
        Logotipo(
            mediaType="image/png",
            base64="A" * 699053,
        )


def test_moldura_valida():
    moldura = Moldura(
        label="SCAN ME",
        position="bottom",
        padding=8,
    )

    assert moldura.label == "SCAN ME"


@pytest.mark.parametrize("texto", ["", "a" * 81])
def test_texto_moldura_invalido(texto):
    with pytest.raises(ValidationError):
        Moldura(label=texto)


def test_personalizacao_vazia():
    personalizacao = Personalizacao()

    assert personalizacao.modules is None
    assert personalizacao.logo is None
