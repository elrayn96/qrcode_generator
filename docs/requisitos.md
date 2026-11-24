# Especificação de requisitos - GQR

Estado: baseline proposta para revisão | v0.1

## Objectivo e âmbito

Gerar códigos QR estáticos gratuitamente, sem redireccionamento proprietário, através de website, Android e API REST. O portal permite gerir integrações externas. O alojamento público não constitui condição de conclusão.

## Requisitos funcionais

| ID | Requisito | Critério de aceitação |
|---|---|---|
| RF01 | Codificar URL, texto, Wi-Fi, contacto vCard, email, SMS, telefone e localização | Descodificação reproduz o conteúdo esperado; URL aponta directamente ao destino |
| RF02 | Personalizar módulos, olhos, fundo, cores, gradientes e logótipo | Pré-visualização reflecte opções; padrões funcionais preservados |
| RF03 | Exportar PNG e SVG | Ficheiros abrem e são legíveis por descodificador independente |
| RF04 | Modelos reutilizáveis | Aplicar modelo não modifica o conteúdo |
| RF05 | Histórico local | Consultar, voltar a editar e apagar sem conta; disponível offline |
| RF06 | Temas claro, escuro e automático | Preferência persiste; não altera o QR automaticamente |
| RF07 | Portal com login Google | Token válido permite gerir apenas recursos próprios |
| RF08 | Registar aplicações e gerir chaves | Criar, listar, rodar e revogar; segredo só apresentado na criação |
| RF09 | Restringir origens/IP e permissões | Pedidos incompatíveis são rejeitados conforme tipo de cliente |
| RF10 | Consultar utilização | Portal mostra contagens agregadas e quotas |
| RF11 | Gerar por API versionada | Cliente externo autorizado recebe imagem ou erro estruturado |
| RF12 | Selector de cores | HEX, RGB, HSV e selecção por arrasto reflectem pré-visualização |

## Requisitos não funcionais

RNF01: interface em português com catálogos de tradução, sem textos fixos nos componentes. RNF02: acessibilidade WCAG 2.2 AA como referência web; escala de texto Android e TalkBack. RNF03: nenhuma persistência de conteúdo QR no servidor, incluindo logs. RNF04: limites de tamanho, tempo, fila e concorrência configuráveis. RNF05: instalação reproduzível e desenvolvimento offline após preparação, excepto serviços remotos. RNF06: testes automatizados e CI GitHub Actions. RNF07: serviço Python não exposto externamente. RNF08: sem cobrança pelo uso do produto; quotas para proteger recursos.

## Fora do MVP

QR dinâmico, redireccionamento, sincronização de histórico, SDK próprio, gRPC, alojamento público obrigatório, Docker e atestação completa. Leitura QR pelo utilizador e exportação PDF ficam para avaliação posterior.
