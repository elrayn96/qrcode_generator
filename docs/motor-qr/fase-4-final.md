# Encerramento do motor QR

Base: commit `4a942cd7e41076cbb9bf24def7423b1ddddc0f7f`.

## Logótipos

PNG e JPEG normalizados, escala 5–20%, padding 0–4 módulos, correcção H
obrigatória no serviço. Colisões com padrões funcionais são rejeitadas.
A leitura em fundo transparente depende da superfície de apresentação.

## Molduras

A resolução solicitada refere-se ao QR interior, incluindo a margem original.
A moldura acrescenta padding em pixels (8 por omissão), e uma faixa de
etiqueta quando solicitada. Posição inferior por omissão. Fundo preto e texto
branco por omissão. A etiqueta usa a fonte interna do Pillow, é raster em
ambos os formatos e rejeita texto que não cabe ou caracteres de controlo.
A cobertura de glifos Unicode não é garantida. O SVG mantém o QR vectorial.

## HTTP interno

`POST /internal/v1/render` recebe JSON UTF-8 até 1 MiB e devolve PNG ou SVG.
O serviço usa o tratamento de erros existente e não guarda as imagens.
O endpoint não tem autenticação própria: manter em loopback/rede privada.
Timeouts, quotas e controlo de concorrência dedicado ficam para integração.

## Evidência de aceitação

Pendente: Ruff, Pytest, cobertura, CI, benchmark e descodificação manual.
Não declarar a fase concluída antes de registar os resultados reais.
