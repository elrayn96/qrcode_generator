# API REST v1

Contratos propostos; não implementados. JSON para pedidos, PNG/SVG binário para respostas. Erros JSON com code, message e requestId; mensagens localizadas no cliente. Cabeçalho X-API-Key para aplicações, Authorization: Bearer para administração.

| Método | Caminho | Acesso |
|---|---|---|
| GET | /v1/templates | Público |
| POST | /v1/qr/generate | Aplicação ou anónimo limitado |
| POST | /v1/qr/preview | Igual a geração, resolução limitada |
| GET/POST | /v1/projects | Programador |
| GET/POST | /v1/projects/{id}/applications | Proprietário |
| PATCH | /v1/applications/{id} | Proprietário |
| POST | /v1/applications/{id}/keys | Proprietário |
| DELETE | /v1/keys/{id} | Proprietário |
| GET | /v1/applications/{id}/usage | Proprietário |

Interno Go–Python: POST /internal/v1/render, recebe conteúdo canónico e estilo; GET /healthz. Sem acesso externo. 400 entrada inválida, 401 credencial ausente/inválida quando exigida, 403 sem permissão, 413 corpo excessivo, 422 QR ilegível, 429 limite, 503 saturação, 504 timeout. Especificação OpenAPI detalhada será elaborada em paralelo com bootstrap, antes dos handlers.
