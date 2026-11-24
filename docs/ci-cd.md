# CI/CD - GitHub Actions

Workflows propostos: validacao-python.yml, validacao-go.yml, validacao-web.yml, validacao-android.yml, testes-integracao.yml, analise-seguranca.yml, release.yml. Executar em PR e push conforme necessidade. Filtros por caminhos incluem contratos e componentes partilhados. Um check agregador obrigatório deve concluir mesmo quando componentes não mudam.

Python: instalação fixada, lint e pytest. Go: build, vet, test e race. Web: validação sintáctica e testes escolhidos. Android: Gradle lint, testes e APK debug. Integração: iniciar serviços locais, health check e testes. Cache de pip, Go e Gradle por lockfiles; não guardar segredos em cache. Actions com permissões mínimas, versões fixadas e segredos protegidos. PR externos não recebem credenciais. Release por tag, artefactos e checksums; sem deployment obrigatório.
