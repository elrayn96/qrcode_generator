# Plano de testes

| Área | Verificação | Ferramenta |
|---|---|---|
| Python | matriz, exportação, estilo, validação limites | pytest |
| Go | handlers, autorização, cache, quota, filas | testing, httptest, race detector |
| Contratos | pedidos e respostas Go–Python | testes integração OpenAPI |
| QR | descodificar PNG e rasterização SVG, comparar conteúdo | descodificador independente a seleccionar |
| Web | editor, teclado, temas, histórico, erros | browser; automação a seleccionar |
| Android | navegação, estado, tema, acessibilidade | JUnit, Compose UI Testing, lint |
| Segurança | acesso cruzado, chave revogada, inputs maliciosos | testes negativos |
| Carga | saturação, latência, memória, cancelamento | cliente Go de teste |

Usar conteúdos fictícios, mocks Firebase e relógio controlável. Não depender de credenciais reais nos testes PR. Testes de QR incluem URLs directos, Unicode, Wi-Fi, estilos extremos e fundos invertidos. Critério de release: testes críticos aprovados; QR exportado deve descodificar correctamente; interfaces verificadas em claro/escuro e texto ampliado. Metas quantitativas de desempenho serão fixadas após baseline.
