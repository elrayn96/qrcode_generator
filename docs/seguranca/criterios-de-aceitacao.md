# Critérios de aceitação de segurança

Testes a implementar durante o desenvolvimento.

| ID | Cenário | Resultado esperado |
|---|---|---|
| TS01 | Utilizador consulta recurso alheio | 404 |
| TS02 | Chave pública acede à administração | 401 |
| TS03 | Dimensão negativa ou campo desconhecido | 422 |
| TS04 | Cinco pedidos concorrentes com quota restante 1 | Apenas um admitido |
| TS05 | Nome contém HTML | Texto inerte |
| TS06 | SVG ou ficheiro falso como logótipo | Rejeitado |
| TS07 | Pedido contém segredo | Ausente nos logs |
| TS08 | Chave revogada | 401 após revogação |
| TS09 | Fila cheia | 503 sem consumo de quota |
| TS10 | Chave inválida | 401 sem acesso anónimo |
