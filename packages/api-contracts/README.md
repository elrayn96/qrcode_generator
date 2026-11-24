# Contratos GQR

Especificações propostas OpenAPI 3.1. API pública no Go; geração privada no Python.

## Regras de execução

- O Gateway valida o pedido e converte os dados em conteúdo canónico; o motor valida novamente e renderiza.
- Pré-visualização: máximo 512 px; pedidos maiores devolvem 422.
- Chave ausente: acesso anónimo limitado apenas à geração e pré-visualização; chave inválida nunca recua para acesso anónimo.
- Chaves públicas identificam aplicações Web/Android; chaves privadas são exclusivas do backend. O tipo da aplicação determina o tipo da chave.
- Operações administrativas exigem token Firebase válido e propriedade do recurso; devolver 404 a terceiros.
- Limites provisórios: 30 pedidos/minuto por aplicação, 10 por IP anónimo, 1000/dia por aplicação, timeout 15 s.
- Reservar capacidade na fila antes da transacção de quota; libertar reserva se a transacção falhar. Pedidos admitidos consomem quota mesmo se cancelados.
- Limitar corpo a 1 MiB, logótipo descodificado a 512 KiB e 4 milhões de píxeis; PNG/JPEG reais apenas.
- Validar capacidade real do QR, margem de quatro módulos e compatibilidade do estilo; rejeitar combinações inválidas.
- Não registar conteúdos, credenciais ou imagens; não efectuar pedidos a URLs fornecidos.
- Acesso interno apenas por loopback no MVP; não expor a porta do motor.
- Erros RFC 9457 com códigos estáveis; nunca devolver valores sensíveis.
- Eliminação administrativa desactiva recursos e revoga as chaves associadas; invalidar cache.

## Validação

Na raiz: `npx --yes @redocly/cli@1.34.3 lint`. Os exemplos são ilustrativos.
