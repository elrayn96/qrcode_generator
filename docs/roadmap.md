# Roadmap

## Marcos gerais

| Marco | Actividades | Dependências | Estado |
|---|---|---|---|
| 1 | Documentação inicial | Decisões confirmadas | Concluído |
| 2A | Bootstrap monorepo e ambientes | 1 | Concluído |
| 2B | Contratos OpenAPI público e interno | 1; paralelo a 2A | Concluído |
| 3A | Motor Python e validação QR | 2A/2B | Em execução |
| 3B | Gateway Go com motor simulado | 2A/2B | Pendente |
| 3C | Firebase e modelo de acesso | 2A/2B | Pendente |
| 3D | Tokens de design e protótipos | 1; paralelo | Pendente |
| 4 | Integração, concorrência e quotas | 3A/3B/3C | Pendente |
| 5A | Website | 2B/3D; mocks até 4 | Pendente |
| 5B | Portal | 2B/3C/3D | Pendente |
| 5C | Android | 2B/3D; mocks até 4 | Pendente |
| 6 | Testes integrados, carga e release | 4/5A/5B/5C | Pendente |

## Progresso detalhado do motor (marco 3A)

- [x] Ambiente, configuração, saúde, prontidão e erros estruturados.
- [x] Schemas, matriz e identificação dos padrões funcionais.
- [x] Geometria, escala, margens e renderização PNG/SVG.
- [x] Cores, formas, olhos, gradientes e fundos.
- [x] Camada de serviços, testes de renderização e segurança.
- [x] Composição raster optimizada, composição regional e simetria radial.
- [x] Avaliação experimental, cobertura e documentação da fase 4.8.7.

| Fase | Actividade | Estado |
|---|---|---|
| 4.9 | Logótipos personalizados | Pendente |
| 4.10 | Molduras e legendas | Pendente |
| 4.11 | Endpoint interno | Pendente |
| 4.12 | Validação integral | Pendente |
| 5 | API Gateway | Pendente |

## Referência de validação

26/11/2026: 903/903 testes, 97,45% de cobertura global, 32/32 ficheiros binariamente idênticos, 10/10 leituras manuais e redução de 79,11% no PNG completo a 2048 px.

## Dívida técnica

- Descodificação automatizada e análise de contraste.
- Harmonização das restrições dos gradientes com os contratos OpenAPI.
- Investigação das duas metas temporais não atingidas e regressões residuais.
- Revisão das lacunas de cobertura e do aviso de depreciação do Starlette.
- Benchmarks reproduzíveis, memória e concorrência.
- Segurança de logótipos e integração HTTP.

## Directrizes

CI acompanha cada etapa, não apenas o fim. Docker e gRPC são experiências posteriores. Alojamento não obrigatório; demonstração local e artefactos de portefólio no final. Não fixar prazos sem disponibilidade do autor.
