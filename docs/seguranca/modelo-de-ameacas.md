# Modelo de ameaças

Fronteiras: clientes → Gateway → motor; Gateway → Firebase.

| STRIDE | Ameaça | Controlo |
|---|---|---|
| S | Identidade falsa | Token verificado |
| T | Alteração de parâmetros | Validação estrita |
| R | Repúdio | ID de pedido e auditoria sem conteúdo |
| I | Fuga de dados | Sem persistência ou logs de conteúdo |
| D | Saturação | Limites e fila |
| E | Escalada | Propriedade e permissões no servidor |
