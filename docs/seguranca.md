# Segurança e privacidade

## Modelo de confiança
Firebase ID Token autentica programadores; verificar assinatura, emissor, audiência, validade e propriedade dos recursos. Chaves públicas identificam aplicações, não autenticam fortemente a origem. CORS protege interacções de browser, não impede clientes HTTP de falsificar Origin. Chaves privadas são exclusivas de servidores, geradas por CSPRNG, armazenadas como hash seguro (ou HMAC com segredo do servidor), comparadas em tempo constante e nunca registadas em logs.

| Cliente | Acesso |
|---|---|
| Website/Android próprios | Sem login; identificação pública e limites anónimos por IP/aplicação |
| Web externa | qr_pk_, origem exacta autorizada, permissões e quotas |
| Android externa | qr_pk_, identificação declarada; não constitui prova de assinatura |
| Backend externo | qr_sk_, permissões e IP opcional |
| Portal | Firebase ID Token; autorização por propriedade |

Atestação futura, não garantia do MVP. Chaves públicas nunca autorizam administração. Origem ausente em cliente web restrito: rejeitar; validar esquema, host e porta. Não confiar em X-Forwarded-For salvo proxy autorizado. Revogação invalida cache local imediatamente; falha de validação não deve autorizar pedidos.

## Protecções
Limitar corpo, dimensões e pixels de logótipos; rejeitar ficheiros inválidos e SVG enviado pelo utilizador no MVP; não descarregar URLs fornecidos (evita SSRF). Escapar entradas em SVG/HTML. Não incluir conteúdos, tokens ou segredos em logs. HTTPS obrigatório fora de ambiente local isolado. Configuração sensível por variáveis de ambiente, nunca no Git. Mensagens de erro não revelam detalhes internos. Limitar pedidos anónimos mesmo que o identificador público seja copiado.
