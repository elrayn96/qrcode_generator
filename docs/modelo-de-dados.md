# Modelo de dados

| Colecção | Campos principais |
|---|---|
| developers | uid, displayName, email, createdAt |
| projects | id, ownerId, name, status, createdAt |
| applications | id, projectId, type, name, allowedOrigins, allowedIPs, permissions, status, revision |
| api_keys | id, applicationId, kind, publicId, secretHash, status, createdAt, expiresAt |
| usage | applicationId, period, admitted, completed, failed, rejected |

IDs gerados pelo servidor; datas UTC; referências validadas. Projectos pertencem a um programador; aplicações pertencem a um projecto; cada aplicação pode ter várias chaves. Operações administrativas passam pelo Go, que verifica propriedade. Firestore nega acesso directo a clientes por omissão; Admin SDK ignora regras e requer IAM restrito. Contadores de quota usam transacções ou reservas atómicas.

## Local
Web: IndexedDB para histórico; preferências locais. Android: armazenamento privado, com tecnologia concreta a escolher (Room/DataStore propostos). Registo: id, tipo, conteúdo, estilo, data e referência ao ficheiro local. Permitir eliminação individual e total. Conteúdos sensíveis (Wi-Fi) não entram no histórico por omissão; evitar backups não intencionais. Nenhum conteúdo QR, logótipo ou imagem gerada no Firestore.
