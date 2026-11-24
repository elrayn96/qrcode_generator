# Concorrência, cache e quotas

Go usa goroutines HTTP e worker pool limitado para controlar pressão sobre Python. Fila buffered, context com prazo total, select para cancelamento, WaitGroup no encerramento. Resposta síncrona; não existe fila persistente de trabalhos. Fila cheia devolve 503; limite de frequência/quota devolve 429 e Retry-After quando determinável.

## Política inicial proposta (ajustável após testes)

2 workers Go, fila de 8, prazo total 15 s, 2 processos Python quando recursos permitirem. Token Bucket por aplicação e por IP anónimo; capacidade e taxa configuráveis. Não assumir que mais goroutines aumentam capacidade CPU. Cache em memória limitada, TTL proposto 60 s, RWMutex e invalidação na alteração/revogação. Não guardar conteúdos QR.

Quota diária UTC por aplicação, reserva atómica antes de execução; pedidos aceites consomem quota mesmo se cancelados para impedir abuso. Rejeições anteriores à admissão não consomem quota. Separar contadores de utilização de quota. Firestore mantém quota persistente; reservas em blocos são optimização posterior, exigem análise de falhas. No modo simulado, reinício pode perder quota. MVP assume um gateway; múltiplas réplicas exigem coordenação distribuída.

## Aceitação

Sem data races; nunca ultrapassar número de operações admitidas; fila limitada; cancelamento não bloqueia workers; revogação local imediata; quota consistente sob concorrência. Medir p50/p95, throughput, CPU, RAM e rejeições.
