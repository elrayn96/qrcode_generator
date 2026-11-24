# Roadmap

| Marco | Actividades | Dependências |
|---|---|---|
| 1 | Documentação inicial | Decisões confirmadas |
| 2A | Bootstrap monorepo e ambientes | 1 |
| 2B | Contratos OpenAPI público e interno | 1; paralelo a 2A |
| 3A | Motor Python e validação QR | 2A/2B |
| 3B | Gateway Go com motor simulado | 2A/2B |
| 3C | Firebase e modelo de acesso | 2A/2B |
| 3D | Tokens de design e protótipos | 1; paralelo |
| 4 | Integração, concorrência e quotas | 3A/3B/3C |
| 5A | Website | 2B/3D; mocks até 4 |
| 5B | Portal | 2B/3C/3D |
| 5C | Android | 2B/3D; mocks até 4 |
| 6 | Testes integrados, carga e release | 4/5A/5B/5C |

CI acompanha cada etapa, não apenas o fim. Docker e gRPC são experiências posteriores. Alojamento não obrigatório; demonstração local e artefactos de portefólio no final. Não fixar prazos sem disponibilidade do autor.
