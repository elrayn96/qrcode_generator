from io import BytesIO
from xml.etree.ElementTree import fromstring

import pytest
from PIL import Image
from src.core.excecoes import ErroDadosInvalidos
from src.renderizacao.molduras import calcular_moldura
from src.schemas.pedido import PedidoRenderizacao
from src.schemas.personalizacao import Moldura
from src.servicos.renderizacao import renderizar


@pytest.mark.parametrize("posicao", ["top", "bottom"])
@pytest.mark.parametrize("padding", [0, 8, 16])
def test_geometria(posicao, padding):
    g = calcular_moldura(512, Moldura(label="SCAN", position=posicao, padding=padding))
    assert g.largura == 512 + 2 * padding
    assert g.altura == g.largura + 85
    assert g.y == padding + (85 if posicao == "top" else 0)


@pytest.mark.parametrize("formato", ["png", "svg"])
@pytest.mark.parametrize("posicao", ["top", "bottom"])
@pytest.mark.parametrize("transparente", [True, False])
def test_integracao(formato, posicao, transparente):
    dados = {
        "content": "ntizoconnect",
        "output": {"format": formato},
        "style": {"background": {"transparent": transparente}},
    }
    original = renderizar(PedidoRenderizacao.model_validate(dados))
    moldura = Moldura(label="SCAN ME", position=posicao)
    dados["style"]["frame"] = moldura.model_dump(exclude_none=True)
    resultado = renderizar(PedidoRenderizacao.model_validate(dados))
    g = calcular_moldura(512, moldura)
    assert (resultado.largura, resultado.altura) == (g.largura, g.altura)
    if formato == "png":
        with (
            Image.open(BytesIO(original.dados)) as a,
            Image.open(BytesIO(resultado.dados)) as b,
            b.crop((g.x, g.y, g.x + 512, g.y + 512)) as recorte,
        ):
            assert recorte.tobytes() == a.tobytes()
    else:
        raiz = fromstring(resultado.dados)
        ns = {"s": "http://www.w3.org/2000/svg"}
        qr = raiz.find("s:svg", ns)
        assert qr is not None
        assert qr.attrib["x"] == str(g.x)
        assert qr.attrib["y"] == str(g.y)
        assert raiz.find("s:image", ns).attrib["href"].startswith("data:image/png;base64,")


@pytest.mark.parametrize("formato", ["png", "svg"])
def test_rejeita_etiqueta_controle(formato):
    pedido = PedidoRenderizacao.model_validate(
        {
            "content": "abc",
            "output": {"format": formato},
            "style": {"frame": {"label": "a\nb"}},
        }
    )
    with pytest.raises(ErroDadosInvalidos):
        renderizar(pedido)
