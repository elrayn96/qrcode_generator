# Requisitos de segurança

- RS01: verificar identidade e propriedade em todas as operações administrativas.
- RS02: negar privilégios por chaves públicas e nunca confiar em Origin como autenticação.
- RS03: validar tipos, limites e campos desconhecidos nos dois serviços.
- RS04: aplicar quotas transaccionais, fila limitada e timeout.
- RS05: renderizar texto sem HTML activo; gerar SVG sem scripts ou referências externas.
- RS06: verificar formato real e limites de descompressão de imagens.
- RS07: excluir segredos do Git e dos logs; adicionar análise automatizada posteriormente.
- RS08: negar acesso directo ao Firestore e ao motor; validar consultas e permissões.
- RS09: revogar chaves e invalidar cache.
