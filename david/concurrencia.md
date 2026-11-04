# Concurrencia y consistencia (5.2): cómo se evita la doble venta

**Autor:** David · **Fecha:** 2026-10-29 · **Rúbrica:** Concurrencia y consistencia (10 puntos)
**Modelo usado:** el de Jacobo (`jacobo/modelo_datos.md` §3 y §7). Referencias `[R-xx]` en `jacobo/referencias.md`; `[D-xx]` al final de este documento.

> **Regla de oro:** una silla solo pasa a vendida dentro de una transacción cuya condición nombra a la orden dueña del bloqueo. Bloquear también es una escritura condicional, y DynamoDB serializa las transacciones entre sí y con las escrituras sueltas [R-04]. Por eso no pueden existir dos dueños de la misma silla al mismo tiempo, y no hay doble venta.

---

## 0. Qué es doble venta (respuesta 5 del profesor, 2026-11-04)

| Regla del profesor | Cómo la cumple el diseño | Dónde |
|---|---|---|
| Prohibido que una silla termine con dos boletas válidas o dos órdenes pagadas | La silla pasa a `S` solo en la transacción que exige `st = 'L' AND lo = :oid`; la boleta usa `attribute_not_exists` con un `tid` determinista; si la silla ya es de otro, la orden queda `FULFILL_FAIL` y se reembolsa, **nunca** `PAID` | §5; anexo, escenarios 1 y 2b |
| Prohibido que dos usuarios tengan a la vez un bloqueo activo sobre la misma silla; el de 8 minutos es exclusivo | Solo se bloquea una silla `A` o una `L` vencida hace más de `:skew` (`lx < now − 2 s`). Mientras el bloqueo esté vigente, nadie más lo toma. Con relojes sincronizados por NTP con menos de 2 s de diferencia, los bloqueos no se traslapan. En desastre, un bloqueo que no llegó a la réplica no puede terminar en compra (anexo, escenario 4b) | §3; pruebas: ":skew protege al dueño" |
| Se permite que el mapa muestre un estado con atraso, si la validación final es contra la base | El mapa sale de instantáneas en la CDN (Jacobo) y de `Query`/GSI, que pueden ir atrasados. **Ninguna decisión de venta se toma con ellos**: solo con las condiciones de la transacción | §5, "Aislamiento" |

**Supuesto que queda explícito:** la exclusividad del bloqueo depende de que los relojes de los servidores difieran en menos de `:skew` = 2 s. Es lo que justifica ese margen (`respuesta_a_jacobo.md`).

## 1. Resumen

| Riesgo | Mecanismo | Garantía |
|---|---|---|
| Dos clientes por la misma silla | `TransactWriteItems` con `ConditionExpression` sobre `st` y `lx` | Una sola transacción gana; la otra se cancela entera [R-04] |
| Bloqueo de 8 minutos | `lx` (vence) y `lo` (orden dueña) en la silla; lo vencido se trata como libre **dentro de la condición** | No depende de ningún proceso que "libere"; el TTL solo limpia [R-08] |
| Pago aprobado sin registro | Intento de pago registrado **antes** de cobrar; llave idempotente ante la pasarela; webhook → SQS → confirmación idempotente; reconciliador sobre `gsi_pendientes` | Todo pago aprobado termina en orden `PAID` o en reembolso |
| Orden pagada sin pago | La confirmación exige `PAY#nn` en `INITIATED`/`UNKNOWN` dentro de la misma transacción | Imposible por construcción |
| Contención en el pico | Cancelación por conflicto (no espera) + reintento con *backoff* y *jitter*; cola virtual; pista negativa | Sin *deadlocks* clásicos |
| Bots | Límite por usuario `LIM#` dentro de la transacción de bloqueo | No se pueden retener más de `:max` sillas por usuario y evento |

## 2. Parámetros fijados

| Parámetro | Valor |
|---|---|
| Duración del bloqueo | 480 s (8 min) |
| `:skew` (margen de relojes) | 2 s, con servidores sincronizados por NTP |
| Máximo de sillas por orden | 10 |
| Reintentos ante `TransactionConflict` | 3, espera aleatoria entre 0 y `min(1000, 50 × 2^intento)` ms, mismo `ClientRequestToken` |
| `ClientRequestToken` | `H(oid, "LOCK")` para el bloqueo y `H(oid, "CONFIRM")` para la confirmación; válido 10 min tras completarse la primera llamada [R-04, D-02] |
| Límite por usuario (`:max`) | 10 sillas por usuario y evento (acordado con Samuel) |

## 3. Fase 1: bloqueo de sillas

Una sola `TransactWriteItems` bloquea todas las sillas, crea la orden y descuenta el cupo del usuario. Si cualquier condición falla, DynamoDB cancela todo y no queda ninguna silla bloqueada a medias [R-04, D-02].

```text
funcion bloquear(uid, eid, sillas[], oid):          # oid lo genera el cliente: es la llave de idempotencia
    now           = epoch_segundos()
    :lx           = now + 480
    :vencido_antes_de = now - :skew                  # la resta se hace aquí: las condiciones no admiten aritmética [D-01]
    :k            = len(sillas)                      # 1..10
    :max_menos_k  = :max - :k

    acciones = []
    para cada s en sillas:
        acciones += Update bya_seats  Key(pk = "E"+eid+"#S"+s.loc+"#R"+s.fila, sk = "S"+s.nro)
            Condition: attribute_exists(pk)
                       AND ( st = 'A'
                             OR (st = 'L' AND lx < :vencido_antes_de) )      # vencido = disponible
            Update:    SET st = 'L', lx = :lx, lo = :oid  ADD v :uno

    acciones += Put bya_orders  ORD#<oid> / ORDER
            Item:      st = 'PENDING', uid, eid, sil, tot, lx = :lx, ttl = :lx + 86400, ...
            Condition: attribute_not_exists(pk)                              # la orden no se crea dos veces

    acciones += Update bya_counters  LIM#E<eid>#U<uid> / P
            Condition: attribute_not_exists(n) OR n <= :max_menos_k
            Update:    SET n = if_not_exists(n, :cero) + :k

    intentar:
        TransactWriteItems(acciones, ClientRequestToken = H(oid, "LOCK"))
        devolver {oid, lx}                                                  # el cliente ve 8 minutos
    capturar TransactionCanceledException e:
        motivos = e.CancellationReasons                                     # uno por acción, en orden [D-02]
        si motivo del Put de ORDER == ConditionalCheckFailed:
            orden = GetItem(ORD#<oid> / ORDER, ConsistentRead = true)
            si orden existe y orden.uid == uid: devolver {oid, orden.lx}    # un intento anterior ya se aplicó
        si algún motivo de silla == ConditionalCheckFailed: devolver 409 + sillas que fallaron
        si motivo del límite == ConditionalCheckFailed:     devolver 429 "superaste el máximo"
        si algún motivo == TransactionConflict:            reintentar(backoff)   # el SDK no lo hace [R-04]
```

Decisiones de esta fase:

* **La expiración vive en la condición.** Una silla `L` con `lx` vencido hace más de `:skew` segundos vale como `A` en el mismo instante en que DynamoDB evalúa la escritura. No hay proceso de liberación que pueda fallar o atrasarse.
* **El TTL no interviene.** DynamoDB borra los vencidos "típicamente en pocos días" y siguen siendo legibles hasta entonces [R-08]. Además la silla nunca se borra, solo cambia de estado. El `ttl` de `bya_seats` es limpieza a los 90 días del evento.
* **El `:skew` protege al dueño.** Si el reloj de otro servidor va adelantado, no puede "robar" un bloqueo justo antes de que venza.
* **La orden y el cupo van en la misma transacción.** No puede existir una silla bloqueada sin orden, ni una orden sin descontar cupo.
* **Segunda defensa de idempotencia, sin depender del token.** Si la respuesta se perdió y el reintento llega cuando el `ClientRequestToken` ya no protege, las sillas fallan por condición (ya son de esta orden) y el `Put` de la orden también. Como el `oid` es único y la transacción es atómica, que la orden exista prueba que el intento anterior bloqueó todo. Sin esta regla, el cliente recibiría "silla ocupada" por sus propias sillas. Lo encontró la prueba de `pruebas/prueba_concurrencia.py`.

## 4. Fase 2: pago

El pago no es transaccional con la base (la pasarela es externa), así que se protege con estados e idempotencia.

```text
funcion pagar(oid, nn, token_tarjeta):
    1. Put bya_orders ORD#<oid> / PAY#<nn>
         Item: st='INITIATED', idem = oid+"#"+nn, g3pk/g3sk (entra a gsi_pendientes)
         Condition: attribute_not_exists(pk)

    2. Put bya_ledger  LED#<minuto>#<fragmento> / <oid>#<nn>       # D-2b: libro de pagos MRSC (clave: propuesta a Jacobo)
         Item: st='INTENT', eid, uid, sil, amt, cre = now
         Condition: attribute_not_exists(pk)
         # se replica a la otra región antes de responder: si cae la región, el intento no se pierde

    3. respuesta = MercadoPago POST /v1/payments                  # pasarela elegida (D-11, pasarelas.md)
         encabezado X-Idempotency-Key = oid+"#"+nn                 # obligatorio; el sandbox confirmó que repetir devuelve el mismo pago
         external_reference = oid+"#"+nn
         metadata = {eid, uid, sillas[]}                           # el sandbox confirmó que se guarda y se devuelve

    4. Update bya_ledger  SET st='CHARGED', gid = respuesta.id  IF st='INTENT'   # con el id se consulta el pago en desastre

    5. según respuesta:
         APROBADO  -> confirmar(oid, nn, gtx)                     # fase 3
         RECHAZADO -> Update PAY#<nn> SET st='DECLINED' REMOVE g3pk, g3sk  IF st='INITIATED'
                      # el bloqueo sigue vigente; el cliente puede intentar con PAY#<nn+1>
         TIMEOUT   -> Update PAY#<nn> SET st='UNKNOWN'  IF st='INITIATED'
                      # lo resuelve el reconciliador (§6)
```

**Por qué el libro va antes del cobro (D-2b, 2026-11-04).** En el sandbox, Mercado Pago no listó pagos por fechas (`pasarelas.md` §7). Si se pierde la región, la lista de sillas en duda sale de `bya_ledger`, que es una tabla MRSC y no pierde datos con la región (`alta_disponibilidad.md` §5.0). Si el `Put` del libro falla, no se cobra. Cuesta una escritura sincrónica entre regiones más por pago, cuya latencia falta medir.

La sesión de la pasarela se configura para vencer **antes** que el bloqueo (por ejemplo a los 7 minutos), así lo normal es que el cobro termine con la silla todavía bloqueada.

## 5. Fase 3: confirmación

```text
funcion confirmar(oid, nn, gtx):
    orden = GetItem(ORD#<oid> / ORDER, ConsistentRead = true)

    acciones = []
    para cada s en orden.sil:
        tid = UUIDv5(oid, s)                                          # determinista: un reintento no crea otra boleta
        acciones += Update bya_seats  Key de s
            Condition: st = 'L' AND lo = :oid        # aunque lx haya vencido: si nadie la tomó, sigue siendo de esta orden
            Update:    SET st = 'S', so = :oid, tk = :tid  ADD v :uno
        acciones += Put bya_tickets  TKT#<tid> / T   (st='VALID', ...)   Condition: attribute_not_exists(pk)

    acciones += Update bya_orders ORD#<oid> / ORDER
            Condition: st = 'PENDING'
            Update:    SET st = 'PAID', tkt = :tids, ttl = :ttl_largo
    acciones += Update bya_orders ORD#<oid> / PAY#<nn>
            Condition: st IN (:initiated, :unknown)
            Update:    SET st = 'APPROVED', gtx = :gtx  REMOVE g3pk, g3sk
    para cada localidad L presente en la orden:                        # un Update por localidad, en su fragmento
        acciones += Update bya_counters CNT#E<eid>#S<L> / SH#<hash(oid) mod nsh>
            Update: ADD sold :n_en_L
    acciones += Put bya_orders ORD#<oid> / INV#1  (st='PENDING', g3pk = PEND#INV#n)   Condition: attribute_not_exists(pk)

    intentar:
        TransactWriteItems(acciones, ClientRequestToken = H(oid, "CONFIRM"))
        devolver PAID
    capturar TransactionCanceledException e:
        si e es por TransactionConflict: reintentar(backoff)
        orden = GetItem(ORD#<oid> / ORDER, ConsistentRead = true)
        si orden.st == 'PAID':      devolver PAID                     # ya se confirmó antes (reintento tardío)
        si falló alguna silla:                                        # otro la tomó después de vencer el bloqueo
            Update ORDER SET st='FULFILL_FAIL'            IF st='PENDING'
            Update PAY#<nn> SET st='APPROVED', gtx=:gtx   IF st IN (:initiated, :unknown)   # queda en gsi_pendientes
            liberar las demás sillas de la orden: Update SET st='A' REMOVE lx, lo  IF st='L' AND lo=:oid
            encolar reembolso (SQS)                                    # escenario 2 del anexo
```

Por qué es seguro:

* **Atomicidad.** Sillas, boletas, orden, pago, contador y factura cambian juntos o no cambia nada [R-04, D-02].
* **Aislamiento.** Entre `TransactWriteItems` y `GetItem`, `PutItem`, `UpdateItem` y `DeleteItem` el aislamiento es serializable: el resultado es el mismo que si cada operación empezara solo cuando la anterior terminó [R-04]. Con `BatchWriteItem` como unidad **no** es serializable, y `Query`/`Scan` son read-committed [R-04]. Por eso las sillas nunca se escriben con batch, y nunca se decide con una `Query` o un GSI.
* **Idempotencia en dos capas.** Dentro de los 10 minutos, repetir con el mismo `ClientRequestToken` devuelve éxito sin cambiar nada [R-04, D-02]. Después de 10 minutos protegen las condiciones: `ORDER.st = 'PENDING'` ya no se cumple, y la aplicación lee la orden y ve `PAID`.
* **Ninguna orden pagada sin pago.** La orden pasa a `PAID` solo en la misma transacción en que el pago pasa a `APPROVED`.

## 6. Pago confirmado sin registro en la base, y al revés

**Caso: la pasarela aprobó y el servidor murió antes de confirmar.** Hay tres caminos que llevan a la misma confirmación idempotente:

1. **El servidor que cobró**, si sigue vivo, llama a `confirmar`.
2. **El webhook de la pasarela.** Solo verifica la firma y publica el aviso en una cola SQS. Un consumidor ejecuta `confirmar`. Si falla, el mensaje reaparece en la cola. Tras `maxReceiveCount` recepciones sin éxito, SQS lo mueve a la **cola de mensajes fallidos**, que tiene una alarma [D-04].
3. **El reconciliador.** Cada minuto consulta los 4 fragmentos de `gsi_pendientes` buscando pagos con más de 5 minutos (patrón AP-17 de Jacobo), y le pregunta a la pasarela el estado de cada uno con su llave `<oid>#<nn>`.

| Pasarela dice | Base dice | Acción del reconciliador |
|---|---|---|
| Aprobado | `PAY` en `INITIATED` o `UNKNOWN`, orden `PENDING` | `confirmar`; si las sillas ya no son de la orden, `FULFILL_FAIL` + reembolso |
| Aprobado | Orden `PAID` | Nada (el índice ya no lo lista) |
| Aprobado | Orden `FULFILL_FAIL` | Verificar que el reembolso esté encolado o hecho |
| Rechazado o sin cobro | `PAY` en `INITIATED` o `UNKNOWN` | `DECLINED` y sale del índice; el bloqueo vence solo |
| Sin cobro | Orden `PAID` | **No puede pasar** (la confirmación exige pago). Si aparece, alerta crítica |

**Caso al revés: la base registró y la pasarela no.** El pago queda `INITIATED` o `UNKNOWN`, nunca `APPROVED`, y la orden nunca pasa a `PAID`. El reconciliador lo marca `DECLINED`.

## 7. Contención en el pico

**Por qué no hay *deadlocks* clásicos.** Un *deadlock* necesita que dos transacciones retengan bloqueos y cada una espere a la otra. En DynamoDB una transacción que choca con otra en curso sobre el mismo ítem **no espera**: se cancela con `TransactionCanceledException` y motivo `TransactionConflict` [R-04, D-02]. Sin espera no puede formarse el ciclo. Lo que reemplaza al *deadlock* es la **cancelación por conflicto**, que la aplicación resuelve con reintentos.

| Error | Significado | Respuesta |
|---|---|---|
| `ConditionalCheckFailed` (en `CancellationReasons`) | La silla no está disponible o se superó el cupo | No reintentar; informar al cliente |
| `TransactionConflict` | Otra transacción tocaba el mismo ítem | *Backoff* con *jitter*, máx. 3, mismo token |
| `TransactionInProgressException` | Sigue en curso una transacción con el mismo token | Reintentar con el mismo token |
| `ProvisionedThroughputExceededException`, *throttling* | Se superó la capacidad de la tabla o la partición | El SDK reintenta con *backoff* [D-03] |
| `InternalServerError`, 503 | Falla temporal | Reintentar con el mismo token [D-03] |

Cómo se reduce la contención (en capas, todas del diseño de Jacobo):

1. **Cola virtual** que limita cuántos compradores llegan a la transacción al mismo tiempo.
2. **Pista negativa en caché.** Si el mapa dice "vendida", la API no lanza la transacción. Si dice "disponible", la lanza igual: la caché puede equivocarse a favor del rechazo, nunca a favor de la venta.
3. **Partición por fila** (`E#S#R`): unas 900 claves por estadio, lejos de los 1.000 WCU/s por partición [R-12].
4. **Contador fragmentado** en 8 ítems para que las confirmaciones de una localidad no choquen entre sí.
5. **Pre-calentamiento** de `bya_seats` y de los GSI de `bya_orders` antes de la preventa [R-18].

Costo de la contención: cada transacción consume el doble de capacidad, **también cuando se cancela** [R-02]. El dimensionamiento de Jacobo ya cuenta 2 bloqueos fallidos por cada exitoso.

## 8. Antibots a nivel de datos

El ítem `LIM#E<eid>#U<uid>` cuenta las sillas retenidas y compradas por usuario y evento, y se actualiza **dentro** de la transacción de bloqueo con la condición `n <= :max_menos_k`. Un bot con una sola cuenta no puede retener más de `:max` sillas aunque lance mil solicitudes en paralelo, porque las escrituras sobre ese ítem son serializables.

`:max` = 10 sillas por usuario y evento, valor acordado con Samuel. Es el mismo número que el máximo por orden (A-09), así que un usuario puede agotar su cupo en una sola compra de 10 sillas, o en varias más pequeñas.

Pendientes con Samuel:

* **Devolver el cupo** cuando un bloqueo vence sin pagar. Propuesta: el reconciliador, al expirar una orden `PENDING`, hace `ADD n :menos_k` en `LIM#` y pasa la orden a `EXPIRED` en la misma transacción (condición `ORDER.st = 'PENDING'`).
* La detección de patrones de bots (varias cuentas, mismo dispositivo) es de Samuel; aquí solo se garantiza el límite por cuenta.

## 9. Referencias propias

| ID | Fuente | Qué respalda |
|---|---|---|
| D-01 | [Condition and filter expressions, operators, and functions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.OperatorsAndFunctions.html) y [Using update expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.Modifying.html) | La gramática de las condiciones solo admite comparaciones, `BETWEEN`, `IN`, funciones y operadores lógicos; `+` y `-` existen solo en `SET`; `if_not_exists` solo en `SET` |
| D-02 | [TransactWriteItems, API Reference](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TransactWriteItems.html) | Todo o nada; hasta 100 acciones; ninguna acción repetida sobre el mismo ítem; causas de cancelación; `CancellationReasons` en el orden de las acciones; token de 10 min e `IdempotentParameterMismatch` |
| D-03 | [Error handling with DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Programming.Errors.html) | Qué errores son reintentables; *throttling*; *backoff* exponencial |
| D-04 | [Using dead-letter queues in Amazon SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) | Política de *redrive* y `maxReceiveCount` |

Consultadas el 2026-10-29.
