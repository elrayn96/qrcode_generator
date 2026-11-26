import pytest
from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.estilos import resolver_estilo
from src.renderizacao.gradientes import Gradiente
from src.schemas.pedido import PedidoRenderizacao


def criar_pedido(**estilo):
    return PedidoRenderizacao.model_validate(
        {
            "content": "https://ntizoconnect.me",
            "style": estilo,
        }
    )


def criar_gradiente(tipo="linear"):
    return {
        "type": tipo,
        "stops": [
            {
                "position": 0.0,
                "color": "#6D28D9",
            },
            {
                "position": 1.0,
                "color": "#172554",
            },
        ],
    }


def test_estilo_padrao():
    estilo = resolver_estilo(criar_pedido())

    assert estilo.forma == "square"
    assert estilo.modulos.valor == (0, 0, 0, 255)
    assert estilo.modulos.ambito == "global"
    assert estilo.fundo.preenchimento.valor == (255, 255, 255, 255)
    assert estilo.olhos is None
    assert estilo.preenchimentos_olhos is None


def test_modulos_com_cor_personalizada():
    estilo = resolver_estilo(
        criar_pedido(
            modules={
                "shape": "rounded",
                "color": "#6D28D9",
            }
        )
    )

    assert estilo.forma == "rounded"
    assert estilo.modulos.valor == (109, 40, 217, 255)


@pytest.mark.parametrize("tipo", ["linear", "radial"])
def test_gradiente_dos_modulos(tipo):
    estilo = resolver_estilo(
        criar_pedido(
            modules={
                "gradient": criar_gradiente(tipo),
            }
        )
    )

    assert isinstance(estilo.modulos.valor, Gradiente)
    assert estilo.modulos.valor.tipo == tipo
    assert estilo.modulos.ambito == "global"
    assert estilo.modulos.opaco


def test_heranca_do_gradiente_nos_olhos():
    estilo = resolver_estilo(
        criar_pedido(
            modules={
                "gradient": criar_gradiente(),
            },
            eyes={
                "outer": {"shape": "rounded"},
                "inner": {"shape": "dots"},
            },
        )
    )

    olhos = estilo.preenchimentos_olhos

    assert olhos is not None
    assert olhos.exterior is estilo.modulos
    assert olhos.interior is estilo.modulos

    assert estilo.olhos is not None
    assert estilo.olhos.forma_exterior == "rounded"
    assert estilo.olhos.forma_interior == "dots"


def test_gradiente_local_do_olho():
    estilo = resolver_estilo(
        criar_pedido(
            modules={"color": "#000000"},
            eyes={
                "outer": {
                    "gradient": criar_gradiente("radial"),
                },
            },
        )
    )

    olhos = estilo.preenchimentos_olhos

    assert olhos is not None
    assert isinstance(olhos.exterior.valor, Gradiente)
    assert olhos.exterior.ambito == "local"
    assert olhos.interior is estilo.modulos


def test_cor_independente_dos_olhos():
    estilo = resolver_estilo(
        criar_pedido(
            eyes={
                "outer": {"color": "#6D28D9"},
                "inner": {"color": "#172554"},
            }
        )
    )

    olhos = estilo.preenchimentos_olhos

    assert olhos is not None
    assert olhos.exterior.valor == (109, 40, 217, 255)
    assert olhos.interior.valor == (23, 37, 84, 255)


def test_prioridade_da_transparencia():
    estilo = resolver_estilo(
        criar_pedido(
            background={
                "transparent": True,
                "color": "#FFFFFF",
                "gradient": criar_gradiente(),
            }
        )
    )

    assert estilo.fundo.tipo == "transparent"
    assert estilo.fundo.preenchimento.valor == (0, 0, 0, 0)


def test_prioridade_do_gradiente_no_fundo():
    estilo = resolver_estilo(
        criar_pedido(
            background={
                "transparent": False,
                "color": "#FFFFFF",
                "gradient": criar_gradiente(),
            }
        )
    )

    assert estilo.fundo.tipo == "gradient"
    assert isinstance(
        estilo.fundo.preenchimento.valor,
        Gradiente,
    )


def test_rejeitar_modulos_semitransparentes():
    with pytest.raises(ErroDadosInvalidos):
        resolver_estilo(criar_pedido(modules={"color": "#00000080"}))


@pytest.mark.parametrize("regiao", ["outer", "inner"])
def test_rejeitar_olhos_semitransparentes(regiao):
    with pytest.raises(ErroDadosInvalidos):
        resolver_estilo(
            criar_pedido(
                eyes={
                    regiao: {"color": "#00000080"},
                }
            )
        )


def test_rejeitar_gradiente_semitransparente():
    gradiente = criar_gradiente()
    gradiente["stops"][0]["color"] = "#00000080"

    with pytest.raises(ErroDadosInvalidos):
        resolver_estilo(
            criar_pedido(
                modules={"gradient": gradiente},
            )
        )


def test_permitir_fundo_semitransparente():
    estilo = resolver_estilo(criar_pedido(background={"color": "#FFFFFF80"}))

    assert estilo.fundo.preenchimento.valor == (255, 255, 255, 128)
    assert not estilo.fundo.opaco


def test_rejeitar_pontos_desordenados():
    gradiente = criar_gradiente()
    gradiente["stops"].reverse()

    with pytest.raises(ErroDadosInvalidos):
        resolver_estilo(
            criar_pedido(
                modules={"gradient": gradiente},
            )
        )


def test_olhos_herdados_nao_requerem_renderizacao_independente():
    estilo = resolver_estilo(
        criar_pedido(
            modules={
                "gradient": criar_gradiente(),
            },
            eyes={
                "outer": {"shape": "square"},
                "inner": {"shape": "square"},
            },
        )
    )

    assert not estilo.requer_olhos_independentes


def test_olhos_arredondados_requerem_renderizacao_independente():
    estilo = resolver_estilo(
        criar_pedido(
            eyes={
                "outer": {"shape": "rounded"},
            },
        )
    )

    assert estilo.requer_olhos_independentes


def test_olhos_com_gradiente_local_requerem_renderizacao_independente():
    estilo = resolver_estilo(
        criar_pedido(
            modules={
                "gradient": criar_gradiente(),
            },
            eyes={
                "outer": {
                    "gradient": criar_gradiente(),
                },
            },
        )
    )

    assert estilo.requer_olhos_independentes


def test_ausencia_de_olhos_personalizados():
    estilo = resolver_estilo(criar_pedido())

    assert not estilo.requer_olhos_independentes
