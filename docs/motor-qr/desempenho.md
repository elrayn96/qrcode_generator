# Desempenho e optimização do motor QR

## Objectivo e metodologia

Reduzir o custo da renderização PNG preservando os resultados originais. A implementação inicial atribuía individualmente os canais RGBA e gerava camadas integrais mesmo quando apenas uma região era necessária.

As avaliações isoladas abrangeram 16, 60 e 12 configurações, respectivamente, com 160, 360 e 180 medições temporais. A avaliação integral utilizou quatro estilos, PNG/SVG e quatro resoluções, totalizando 32 configurações, com três medições após aquecimento. Utilizou-se a mediana, sem incluir HTTP, filas ou concorrência. Ambiente: Windows 10 19045, AMD64, Python 3.15.2, Intel Family 6 Model 60 Stepping 3. Conteúdo: `ntizoconnect`.

## Estratégias

- Paleta de 4096 entradas em bytes RGBA, pré-cálculo de coordenadas e concatenação por linhas.
- Reutilização de linhas ou cores quando a igualdade dos índices extremos permite.
- Simetria radial com tratamento de dimensões pares e ímpares.
- Composição regional com preservação da geometria e simetria quando os centros coincidem.

Para largura W e altura H, o cálculo geral avalia O(W × H) posições. Os percursos cardinais reutilizáveis avaliam O(W) ou O(H) índices; a simetria radial reduz aproximadamente a um quarto as avaliações. A composição regional limita o cálculo à caixa delimitadora. A materialização raster integral permanece O(W × H); uma imagem RGBA de 2048 × 2048 ocupa 16 MiB sem compressão.

## Avaliações isoladas

As 16 configurações da primeira optimização, as 60 da composição regional e as 12 da correcção radial mantiveram equivalência dos pixels. A primeira optimização acelerou todas as configurações; a composição regional apresentou regressões radiais, posteriormente mitigadas. A correcção radial acelerou as 12 configurações face à versão regional anterior, com duas regressões residuais face à primeira optimização.

## Resultados integrais

Tempos medianos em ms; redução negativa indica regressão. Pico residente máximo em MiB, medido separadamente em processos isolados.

| Estilo | Formato | px | Antes | Depois | Redução (%) | Pico (MiB) |
|---|---|---:|---:|---:|---:|---:|
| convencional | png | 256 | 10.381 | 23.416 | -125.566 | 42.117 |
| convencional | png | 512 | 26.214 | 40.855 | -55.852 | 42.621 |
| convencional | png | 1024 | 97.679 | 24.419 | 75.001 | 45.695 |
| convencional | png | 2048 | 97.153 | 107.734 | -10.891 | 57.695 |
| convencional | svg | 256 | 11.519 | 10.832 | 5.964 | 40.504 |
| convencional | svg | 512 | 8.692 | 16.074 | -84.929 | 40.406 |
| convencional | svg | 1024 | 10.5 | 23.533 | -124.124 | 40.434 |
| convencional | svg | 2048 | 10.071 | 10.604 | -5.292 | 40.5 |
| formas | png | 256 | 21.311 | 27.186 | -27.568 | 42.016 |
| formas | png | 512 | 37.058 | 70.184 | -89.39 | 42.891 |
| formas | png | 1024 | 62.574 | 136.456 | -118.071 | 45.906 |
| formas | png | 2048 | 103.15 | 108.39 | -5.08 | 58.047 |
| formas | svg | 256 | 9.45 | 10.357 | -9.598 | 40.566 |
| formas | svg | 512 | 10.865 | 15.31 | -40.911 | 40.52 |
| formas | svg | 1024 | 10.931 | 13.285 | -21.535 | 40.562 |
| formas | svg | 2048 | 9.475 | 15.067 | -59.018 | 40.434 |
| gradiente | png | 256 | 80.07 | 43.609 | 45.536 | 42.492 |
| gradiente | png | 512 | 277.627 | 77.066 | 72.241 | 44.145 |
| gradiente | png | 1024 | 1018.959 | 301.332 | 70.427 | 54.297 |
| gradiente | png | 2048 | 3886.756 | 1179.198 | 69.661 | 95.629 |
| gradiente | svg | 256 | 10.711 | 11.497 | -7.338 | 40.543 |
| gradiente | svg | 512 | 10.398 | 14.297 | -37.498 | 40.613 |
| gradiente | svg | 1024 | 11.127 | 13.639 | -22.576 | 40.703 |
| gradiente | svg | 2048 | 11.552 | 11.192 | 3.116 | 40.574 |
| completa | png | 256 | 193.391 | 87.596 | 54.705 | 42.953 |
| completa | png | 512 | 585.345 | 195.352 | 66.626 | 44.305 |
| completa | png | 1024 | 2196.744 | 620.199 | 71.767 | 54.664 |
| completa | png | 2048 | 8671.357 | 1811.807 | 79.106 | 95.691 |
| completa | svg | 256 | 19.222 | 10.862 | 43.492 | 40.57 |
| completa | svg | 512 | 17.385 | 8.62 | 50.417 | 40.57 |
| completa | svg | 1024 | 16.036 | 12.093 | 24.588 | 40.754 |
| completa | svg | 2048 | 16.417 | 11.707 | 28.69 | 40.543 |

## Metas experimentais

| Estilo PNG | px | Meta (ms) | Resultado (ms) | Estado |
|---|---:|---:|---:|---|
| Gradiente | 512 | 100 | 77,066 | Atingida |
| Gradiente | 1024 | 300 | 301,332 | Não atingida |
| Gradiente | 2048 | 1000 | 1179,198 | Não atingida |
| Completa | 512 | 250 | 195,352 | Atingida |
| Completa | 1024 | 750 | 620,199 | Atingida |
| Completa | 2048 | 2000 | 1811,807 | Atingida |

Quatro de seis metas atingidas. O PNG completo a 2048 px passou de 8,671 s para 1,812 s (4,786 vezes; redução de 79,11%). As metas são referências de engenharia, não limites contratuais.

## Equivalência e memória

As 32 configurações apresentaram ficheiros binariamente idênticos. O maior pico residente observado foi 95,691 MiB. Não existe medição anterior à optimização para quantificar a redução de memória. Os resultados não estabelecem um limite garantido para outros pedidos ou carga concorrente.

## Limitações e evolução

A comparação integral ocorreu em momentos distintos. As regressões nos casos convencionais, formas e SVG não podem ser atribuídas exclusivamente ao código. Foi utilizado um único conteúdo e três repetições por configuração integral. Não foram medidos percentis em carga, latência HTTP ou filas. Investigar gradientes diagonais, metas residuais, concorrência, recursos e impacto de logótipos e molduras em etapas posteriores.

## Referência

26 de Novembro de 2026. Implementação remota de referência: `b90ba38dce5d73c9a7d22fc39801b9b6e4d786bb`.
