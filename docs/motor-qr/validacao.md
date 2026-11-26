# Validação e qualidade do motor QR

## Organização

Os testes encontram-se em `tests/unitarios/`, `tests/integracao/` e `tests/seguranca/`, além do teste de ambiente.

## Cobertura funcional

- Unitários: configuração, schemas, matriz, cores, geometria, formas, módulos, olhos, gradientes, composição, máscaras, fundos, PNG/SVG e orquestração.
- Integração: conteúdo, níveis de correcção, dimensões, margens, personalização combinada, determinismo, isolamento, herança, consistência geométrica e saúde/prontidão.
- Segurança: validação estrita, rejeição de propriedades desconhecidas e nulos indevidos, ausência de conteúdo original nas representações verificadas, estrutura SVG sem injecção de elementos executáveis ou referências externas nos gradientes, rejeição de posições inválidas e de preenchimentos translúcidos nos módulos e olhos.

A segurança estrutural do SVG não garante a segurança do conteúdo descodificado. Autenticação, quotas, limites HTTP e concorrência dependem de etapas posteriores.

## Resultados de 26/11/2026

| Indicador | Resultado |
|---|---:|
| Testes aprovados | 903/903 |
| Falhas, erros e ignorados | 0 |
| Tempo da execução com cobertura | 20,063 s |
| Instruções | 1075/1092 (98,44%) |
| Ramos | 262/280 (93,57%) |
| Global | 1337/1372 (97,45%) |
| Composição | 100% |
| Equivalência binária | 32/32 |

## Lacunas de instruções

| Ficheiro | Linhas |
|---|---|
| `api/tratamento_erros.py` | 99 |
| `main.py` | 48, 50 |
| `renderizacao/estilos.py` | 40, 120 |
| `renderizacao/geometria.py` | 52, 58 |
| `renderizacao/gradientes.py` | 21, 26, 37, 60, 112, 131 |
| `renderizacao/olhos.py` | 22, 25, 96 |
| `servicos/renderizacao.py` | 16 |

Existem 17 instruções e 18 ramos não cobertos. A cobertura não demonstra ausência de defeitos.

## Descodificação manual

| Estilo | Resolução | PNG | SVG |
|---|---:|---|---|
| Convencional | 512 | Aprovado | Aprovado |
| Formas | 512 | Aprovado | Aprovado |
| Gradiente | 512 | Aprovado | Aprovado |
| Completa | 512 | Aprovado | Aprovado |
| Completa | 2048 | Aprovado | Aprovado |

As dez leituras foram confirmadas pelo autor, com conteúdo `ntizoconnect`. Não constituem validação universal nem substituem um descodificador automatizado independente.

## Reprodução e CI

Na pasta `services/qr-engine`:

```powershell
python -m pip check
python -m ruff check src tests
python -m ruff format --check src tests
python -m pytest -q
python -m pytest --cov=src --cov-report=term-missing
python -m pytest --junitxml=testes.xml --cov=src --cov-report=json:cobertura.json
```

A CI verifica dependências, análise estática, formatação e testes. Os benchmarks temporais não são critérios obrigatórios da CI. Os relatórios XML e JSON são artefactos regeneráveis.

## Pendências

Descodificação automatizada, contraste, segurança e legibilidade com logótipos, molduras, validação contratual HTTP, integração com gateway e testes concorrentes. Permanece um aviso de depreciação de HTTPX no TestClient do Starlette.

Referência: `b90ba38dce5d73c9a7d22fc39801b9b6e4d786bb`.
