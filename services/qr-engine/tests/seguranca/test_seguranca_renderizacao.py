from re import fullmatch
from xml.etree.ElementTree import fromstring

import pytest
from src.core.excecoes import ErroDadosInvalidos
from src.schemas.pedido import PedidoRenderizacao
from src.servicos.renderizacao import renderizar

NS = "http://www.w3.org/2000/svg"

CONTEUDOS_HOSTIS = [
    "<script>alert(1)</script>",
    '<img src=x onerror="alert(1)">',
    '"><svg onload="alert(1)">',
    "<!DOCTYPE svg SYSTEM 'https://example.com/evil.dtd'>",
    "javascript:alert(1)",
    '<foreignObject><iframe src="https://example.com"/></foreignObject>',
]

ELEMENTOS_PERMITIDOS = {
    "svg",
    "defs",
    "linearGradient",
    "radialGradient",
    "stop",
    "rect",
    "circle",
    "path",
    "g",
}


@pytest.mark.parametrize("conteudo", CONTEUDOS_HOSTIS)
def test_conteudo_nao_injectado_svg(conteudo):
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": conteudo,
            "output": {
                "format": "svg",
            },
        }
    )

    resultado = renderizar(pedido)

    assert conteudo.encode("utf-8") not in resultado.dados
    assert b"<!DOCTYPE" not in resultado.dados
    assert b"<!ENTITY" not in resultado.dados

    raiz = fromstring(resultado.dados)

    for elemento in raiz.iter():
        assert elemento.tag.startswith(f"{{{NS}}}")

        nome = elemento.tag.split("}")[-1]

        assert nome in ELEMENTOS_PERMITIDOS

        for atributo in elemento.attrib:
            nome = atributo.split("}")[-1].lower()

            assert not nome.startswith("on")
            assert nome != "href"


def test_gradientes_sem_referencias_externas():
    gradiente = {
        "type": "linear",
        "angle": 45,
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

    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "ntizoconnect",
            "output": {
                "format": "svg",
            },
            "style": {
                "modules": {
                    "gradient": gradiente,
                    "shape": "rounded",
                },
                "eyes": {
                    "outer": {
                        "gradient": gradiente,
                        "shape": "rounded",
                    },
                },
            },
        }
    )

    raiz = fromstring(renderizar(pedido).dados)

    ids = [elemento.attrib["id"] for elemento in raiz.iter() if "id" in elemento.attrib]

    assert len(ids) == len(set(ids))

    referencias = []

    for elemento in raiz.iter():
        for atributo, valor in elemento.attrib.items():
            nome = atributo.split("}")[-1].lower()

            assert not nome.startswith("on")
            assert nome != "href"

            if "url(" in valor:
                referencia = fullmatch(
                    r"url\(#([A-Za-z0-9_-]+)\)",
                    valor,
                )

                assert referencia is not None

                identificador = referencia.group(1)

                assert identificador in ids

                referencias.append(identificador)

    assert referencias


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize(
    "posicoes",
    [
        [0.0, 0.0],
        [1.0, 0.0],
        [0.0, 0.5, 0.4],
    ],
)
def test_ordem_invalida_gradiente(formato, posicoes):
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "ntizoconnect",
            "output": {
                "format": formato,
            },
            "style": {
                "modules": {
                    "gradient": {
                        "type": "linear",
                        "stops": [
                            {
                                "position": posicao,
                                "color": "#6D28D9",
                            }
                            for posicao in posicoes
                        ],
                    },
                },
            },
        }
    )

    with pytest.raises(ErroDadosInvalidos):
        renderizar(pedido)


@pytest.mark.parametrize("formato", ["png", "svg"])
def test_conteudo_ausente_representacao_textual(formato):
    conteudo = "GQR-CONTEUDO-CONFIDENCIAL-TESTE"

    pedido = PedidoRenderizacao.model_validate(
        {
            "content": conteudo,
            "output": {
                "format": formato,
            },
        }
    )

    resultado = renderizar(pedido)

    assert conteudo not in repr(pedido)
    assert conteudo not in repr(resultado)
    assert conteudo.encode("utf-8") not in resultado.dados


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize(
    "componente",
    ["modules", "outer", "inner"],
)
def test_rejeitar_gradientes_translucidos(
    formato,
    componente,
):
    gradiente = {
        "gradient": {
            "type": "linear",
            "stops": [
                {
                    "position": 0.0,
                    "color": "#00000080",
                },
                {
                    "position": 1.0,
                    "color": "#172554",
                },
            ],
        },
    }

    estilo = (
        {"modules": gradiente} if componente == "modules" else {"eyes": {componente: gradiente}}
    )

    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "ntizoconnect",
            "output": {
                "format": formato,
            },
            "style": estilo,
        }
    )

    with pytest.raises(ErroDadosInvalidos):
        renderizar(pedido)
