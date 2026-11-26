# GQR — QR Engine

Motor Python de geração e renderização de códigos QR do Gen QR.

## Tecnologias

Python, FastAPI, Uvicorn, Segno, Pillow, Pydantic, ElementTree, Pytest e Ruff.

## Funcionalidades

- Matrizes QR convencionais, Unicode e correcção de erros L, M, Q e H.
- PNG e SVG, resoluções de 128 a 2048 px e margens de 4 a 32 módulos.
- Módulos quadrados, arredondados e circulares.
- Personalização independente dos olhos, cores e gradientes lineares e radiais.
- Fundos sólidos, translúcidos, transparentes e com gradientes.
- Preservação geométrica dos padrões funcionais e composição regional optimizada.

## Estrutura

```text
src/
├── api/
├── core/
├── motor/
├── renderizacao/
├── schemas/
├── seguranca/
├── servicos/
└── main.py
tests/
├── integracao/
├── seguranca/
└── unitarios/
```

## Ambiente e execução

Na pasta do serviço, em PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt -c requirements-lock.txt
python -m pip check
python -m src.main
```

Endereço predefinido: `http://127.0.0.1:8001`.

| Método | Endpoint | Finalidade |
|---|---|---|
| GET | `/healthz` | Saúde |
| GET | `/readyz` | Prontidão |

A renderização está disponível na camada de serviços Python. O endpoint HTTP de renderização permanece pendente.

## Exemplo

```python
from pathlib import Path
from src.schemas.pedido import PedidoRenderizacao
from src.servicos.renderizacao import renderizar

pedido = PedidoRenderizacao.model_validate({
    "content": "https://example.com",
    "output": {"format": "png", "size": 512, "margin": 4},
    "options": {"errorCorrection": "H"},
    "style": {"modules": {"shape": "rounded", "gradient": {
        "type": "linear", "angle": 45, "stops": [
            {"position": 0.0, "color": "#6D28D9"},
            {"position": 1.0, "color": "#172554"},
        ],
    }}},
})
Path("qr-exemplo.png").write_bytes(renderizar(pedido).dados)
```

## Validação

```powershell
python -m ruff check src tests
python -m ruff format --check src tests
python -m pytest -q
python -m pytest --cov=src --cov-report=term-missing
```

Referência de 26/11/2026: 903 testes aprovados, cobertura global de 97,45% e redução de 79,11% no tempo mediano do PNG completo a 2048 px.

## Documentação

- [Arquitectura de renderização](../../docs/motor-qr/renderizacao.md)
- [Desempenho](../../docs/motor-qr/desempenho.md)
- [Validação](../../docs/motor-qr/validacao.md)
- [Contratos](../../packages/api-contracts/README.md)
- [Roadmap](../../docs/roadmap.md)

## Pendências

Logótipos, molduras, legendas, endpoint interno, descodificação automatizada independente e integração com o gateway.
