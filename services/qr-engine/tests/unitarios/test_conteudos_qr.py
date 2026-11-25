import pytest
from src.motor.matriz import gerar_matriz


@pytest.mark.parametrize(
    "conteudo",
    [
        pytest.param(
            "https://example.com",
            id="url",
        ),
        pytest.param(
            "Bem-vindo ao Gen QR!",
            id="text",
        ),
        pytest.param(
            "WIFI:T:WPA;S:MinhaRede;P:senha-exemplo;;",
            id="wifi",
        ),
        pytest.param(
            "BEGIN:VCARD\r\nVERSION:3.0\r\nFN:Contacto Exemplo\r\nTEL:+258840000000\r\nEND:VCARD",
            id="vcard",
        ),
        pytest.param(
            "mailto:contacto@example.com?subject=Ola",
            id="email",
        ),
        pytest.param(
            "SMSTO:+258840000000:Ola",
            id="sms",
        ),
        pytest.param(
            "tel:+258840000000",
            id="phone",
        ),
        pytest.param(
            "geo:-25.9653,32.5892",
            id="geo",
        ),
    ],
)
def test_geracao_tipos_conteudo(conteudo):
    matriz = gerar_matriz(conteudo)

    assert 1 <= matriz.versao <= 40
    assert matriz.dimensao >= 21
    assert matriz.modulos_escuros > 0
    assert matriz.modulos_claros > 0
