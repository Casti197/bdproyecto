Actualización 4-nov (Miguel): apliqué las respuestas del profesor a miguel/ (carta de recuperación, README, fichas). Pull y listo.

Lo que cambió en mi parte:
- Runbook 2b: ya no se cierra toda la venta. Al declarar, se congelan las sillas en duda (pagos de Mercado Pago de los últimos T−W min), se reabre y la conciliación termina después. Usa la tabla de RTO de alta_disponibilidad.md §3.3: 4 a 8 min (4 a 11 en secuencia), cumple los 15.
- Detección y criterio de declaración aparte (2 a 5 min): alarma compuesta + Route 53 (30 s, 3 fallos) + confirmación humana.
- Estadio: 4 horas aislado, con el RPO/RTO del ingreso de David (estadio.md §6.1) y cierre de reembolsos 2 h antes.
- Escenario A es todo en AWS: no hay runbook 2c ni aplicación en Bogotá; el 2c es solo del B.

Lo que le toca a cada uno (de respuestas_profesor.md):
- Jacobo: sección de 2 páginas sobre DynamoDB on premise y alternativa compatible; arquitectura de A todo en AWS; qué tiene AWS en Colombia y la latencia desde Bogotá.
- Samuel: análisis de transferencia internacional (Ley 1581).
- Juan Pablo: comparar A contra B (latencia, conectividad, egress y costos) y mostrar B con torniquetes propios y con los del estadio. La lista de lo mío está en miguel/lista_componentes_para_juan_pablo.md.
- David o Jacobo: probar en el sandbox de Mercado Pago que metadata guarda las sillas y que la idempotencia devuelve el mismo pago.
