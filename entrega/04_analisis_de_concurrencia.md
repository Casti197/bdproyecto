# Anexo de concurrencia: cuatro escenarios sin doble venta

**Autor:** David · **Fecha:** 2026-10-29 · **Rúbrica:** Anexo de concurrencia (3 puntos)
**Estado:** escenarios 1 y 2 completos (semana 1); escenarios 3 y 4 en borrador para la semana 2.
Pseudocódigo completo de las transacciones: `david/concurrencia.md` §3–§5. Claves: `jacobo/modelo_datos.md` §3.2. Referencias `[R-xx]` en `jacobo/referencias.md`; `[D-xx]` en `david/concurrencia.md` §9.

Notación: silla `E1234#S07#R12 / S024`, abreviada **S024**. `t` en segundos; los estados de la silla son `A` (disponible), `L` (bloqueada), `S` (vendida).

---

## Escenario 1: dos clientes piden la misma silla en el mismo milisegundo

**Respuesta corta:** solo una transacción gana. DynamoDB las ejecuta como si una terminara antes de que empiece la otra; la segunda se cancela por conflicto o encuentra la silla ya bloqueada, y en ambos casos no se escribe nada [R-04].

**Transacción de cada cliente (fase 1):**

```text
TransactWriteItems  ClientRequestToken = H(oid, "LOCK")
  Update bya_seats  E1234#S07#R12 / S024
    IF  attribute_exists(pk) AND ( st='A' OR (st='L' AND lx < :vencido_antes_de) )
    SET st='L', lx=:lx, lo=:oid   ADD v :uno
  Put    bya_orders  ORD#<oid> / ORDER   (st='PENDING', ...)   IF attribute_not_exists(pk)
  Update bya_counters LIM#E1234#U<uid> / P   SET n = if_not_exists(n,:cero) + :k   IF attribute_not_exists(n) OR n <= :max_menos_k
```

**Línea de tiempo.** Ana (orden `O-ANA`) y Beto (orden `O-BETO`), S024 en `A`, `v = 0`.

| t | Sesión de Ana | Sesión de Beto | S024 |
|---|---|---|---|
| 0,000 | Envía su transacción | Envía su transacción | `A`, v=0 |
| 0,003 | DynamoDB evalúa su condición: `st='A'` se cumple. Escribe `L`, `lo=O-ANA`, `lx=480` | Su transacción toca el mismo ítem mientras la de Ana está en curso | `L` (O-ANA), v=1 |
| 0,005 | Recibe éxito; ve su temporizador de 8 min | Recibe `TransactionCanceledException`, motivo `TransactionConflict` en la acción de S024 [R-04, D-02] | `L` (O-ANA) |
| 0,040 | Pasa a pagar | Espera aleatoria (*backoff*) y reintenta con el **mismo** token | `L` (O-ANA) |
| 0,045 | — | La condición se evalúa ahora contra `st='L'` con `lx` en el futuro: **no se cumple** | `L` (O-ANA) |
| 0,047 | — | Recibe `ConditionalCheckFailed` en S024. La API responde 409 "silla no disponible" y no reintenta | `L` (O-ANA) |

**Variante:** si Beto llega cuando la transacción de Ana ya terminó, salta directo a la fila 0,045. El resultado no cambia.

**Por qué no hay doble venta:**

1. El aislamiento entre transacciones, y entre transacciones y escrituras sueltas, es **serializable** [R-04]. No existe un orden de ejecución en el que ambas condiciones se cumplan, porque la primera que escribe cambia `st` a `L`.
2. La transacción de Beto es **todo o nada**: su orden `O-BETO` no se crea y su cupo `LIM#` no se descuenta [R-04, D-02].
3. Si Ana pedía 3 sillas y solo S024 estaba en disputa, igual se cancela **toda** su transacción si pierde; nunca queda con 2 de 3 sillas bloqueadas. `CancellationReasons` dice cuál silla falló, en el orden de las acciones [D-02], y la API se lo muestra al cliente.

---

## Escenario 2: el bloqueo vence mientras el cliente paga

**Respuesta corta:** si nadie tomó la silla, la compra se confirma aunque `lx` haya pasado. Si otro la tomó después del vencimiento, la confirmación falla por condición, la orden pasa a `FULFILL_FAIL` y el pago se reembolsa. En ningún caso dos órdenes terminan con la misma silla.

**Transacción de confirmación (fase 3), parte que decide:**

```text
TransactWriteItems  ClientRequestToken = H(oid, "CONFIRM")
  Update bya_seats   S024             IF st='L' AND lo=:oid          SET st='S', so=:oid, tk=:tid  ADD v :uno
  Put    bya_tickets TKT#<tid> / T    IF attribute_not_exists(pk)
  Update bya_orders  ORD#<oid>/ORDER  IF st='PENDING'                SET st='PAID', ...
  Update bya_orders  ORD#<oid>/PAY#01 IF st IN (:initiated,:unknown) SET st='APPROVED', gtx=:gtx  REMOVE g3pk, g3sk
  Update bya_counters CNT#E1234#S07 / SH#<hash(oid) mod 8>           ADD sold :uno
  Put    bya_orders  ORD#<oid>/INV#1  IF attribute_not_exists(pk)
```

### 2a. Venció, pero nadie la tomó (se confirma)

| t | Sesión de Ana | Otros | S024 |
|---|---|---|---|
| 0 | Bloqueo con éxito, `lx = 480` | — | `L` (O-ANA) |
| 60 | Registra `PAY#01` en `INITIATED`; abre la pasarela | — | `L` (O-ANA) |
| 481 | Sigue en la pasarela | Nadie pidió S024 | `L` (O-ANA), vencida |
| 495 | La pasarela aprueba; se ejecuta la confirmación | — | `L` (O-ANA) |
| 495 | `st='L' AND lo='O-ANA'` **se cumple**: no se exige que `lx` siga vigente | — | `S` (O-ANA) |

### 2b. Venció y otro la tomó (reembolso)

| t | Sesión de Ana | Sesión de Beto | S024 |
|---|---|---|---|
| 0 | Bloqueo con éxito, `lx = 480` | — | `L` (O-ANA) |
| 60 | Registra `PAY#01` en `INITIATED`; abre la pasarela | — | `L` (O-ANA) |
| 483 | Sigue en la pasarela | Pide S024. `lx = 480 < now − skew = 481`: la condición de bloqueo **se cumple** | `L` (O-BETO) |
| 495 | La pasarela aprueba; se ejecuta la confirmación | Pagando | `L` (O-BETO) |
| 495 | `lo='O-ANA'` **no se cumple**: `ConditionalCheckFailed`. Se cancela **toda** la transacción: ni boleta, ni `PAID`, ni contador | — | `L` (O-BETO) |
| 496 | Orden → `FULFILL_FAIL`; `PAY#01` → `APPROVED` (queda en `gsi_pendientes`); reembolso a SQS; aviso a Ana | — | `L` (O-BETO) |
| 530 | — | Confirma con normalidad | `S` (O-BETO) |

**Por qué no hay doble venta ni dinero perdido:**

1. La silla solo pasa a `S` en una transacción cuya condición nombra al dueño actual (`lo`). Para que Beto sea dueño, su propio bloqueo tuvo que escribir `lo='O-BETO'`, y esa escritura es serializable con la confirmación de Ana [R-04].
2. El vencimiento se evalúa **dentro de la condición** de Beto, no con TTL. El TTL puede tardar días y no se usa para la lógica [R-08].
3. El dinero de Ana no se pierde: el pago queda `APPROVED` con la orden en `FULFILL_FAIL`, y `gsi_pendientes` lo mantiene visible para el reconciliador hasta que el reembolso termina.
4. Para que 2b sea raro, la sesión de la pasarela vence antes que el bloqueo (7 de los 8 minutos).

---

## Escenario 3: falla a mitad de la compra

**Respuesta corta:** una falla puede dejar la compra *sin terminar*, nunca *a medias*. Las dos transacciones (bloqueo y confirmación) son todo o nada [R-04]; el cobro, que no es transaccional, se protege con un registro previo (`PAY#nn`), una llave de idempotencia con la pasarela y un reconciliador. En ningún caso se cobra sin que quede rastro, ni se vende una silla dos veces.

| Punto de falla | Qué queda en la base | Quién lo resuelve | Mecanismo |
|---|---|---|---|
| 3a. Durante la transacción de bloqueo o confirmación | Nada o todo | DynamoDB | Atomicidad [R-04] |
| 3b. Respuesta perdida (*timeout*) | No se sabe si se aplicó | El servidor | Reintento con el mismo `ClientRequestToken` (10 min); luego lectura fuerte |
| 3c. Servidor cae tras cobrar, antes de confirmar | `PAY#01` `INITIATED`, orden `PENDING` | Webhook, SQS o reconciliador | Confirmación idempotente; DLQ [D-04] |
| 3d. La pasarela no responde | `PAY#01` `UNKNOWN` | Reconciliador | Consulta con la llave `<oid>#<nn>` |

### 3a. Falla durante la transacción

Si el servidor cae, o una de las condiciones falla, DynamoDB cancela toda la transacción y no deja efectos parciales; si se cancela, `CancellationReasons` dice cuál acción falló, en el mismo orden de las acciones [D-02]. La atomicidad vale frente a operaciones individuales; las lecturas con `Query` o `Scan` son *read committed* y pueden ver el estado antes o después, pero nunca la mitad de la transacción [R-04].

### 3b. Respuesta perdida

| t | Servidor | Base | Qué pasa |
|---|---|---|---|
| 0 | Envía `TransactWriteItems` (token `T1`) | Aplica la transacción | — |
| 1 | La respuesta se pierde; el cliente HTTP da *timeout* | Sillas en `L` | El servidor **no sabe** si se aplicó |
| 2 | Reintenta con el **mismo** `T1` | Reconoce el token | Devuelve éxito sin repetir |
| 3 | Si pasaron más de 10 min o cambió algún parámetro | `IdempotentParameterMismatch` o ejecuta de nuevo | Lectura fuerte de `ORDER` y de las sillas |

```text
funcion reintentarBloqueo(oid, plan):
    token = H(oid, "LOCK")                       # mismo token en cada reintento
    repetir hasta 3 veces con espera 50 ms x 2^n + jitter:
        intentar TransactWriteItems(plan, ClientRequestToken = token): devolver OK
        capturar TransactionInProgress, InternalServerError, timeout: continuar
        capturar IdempotentParameterMismatch: leer ORDER (fuerte); decidir segun estado
        capturar TransactionCanceledException e:
            si e.motivo(Put ORDER) == ConditionalCheckFailed y ORDER (fuerte) existe con este uid:
                devolver OK                          # el intento anterior ya se aplicó
            devolver CONFLICTO                       # la silla es de otro; no se reintenta
    leer ORDER (fuerte): si st='PENDING' con sillas en L de oid -> OK; si no -> ERROR
```

El token protege 10 minutos [D-02]; el bloqueo dura 8, así que el reintento cae dentro de la ventana. La confirmación tiene además su propia idempotencia por condiciones (`st='PENDING'`, `attribute_not_exists`), que sigue funcionando después de esos 10 minutos.

### 3c. El servidor cae después de cobrar

| t | Servidor A | Pasarela / webhook | Base |
|---|---|---|---|
| 0 | Escribe `PAY#01 INITIATED` y llama a la pasarela con la llave `<oid>#01` | Procesa el cobro | Orden `PENDING`, sillas `L` |
| 40 | **Cae** antes de confirmar | Aprueba; envía webhook | Igual |
| 41 | — | El webhook llega a un servidor sano que lo encola en SQS | Igual |
| 42 | Servidor B toma el mensaje y ejecuta la confirmación de `concurrencia.md` §5 | — | Orden `PAID`, sillas `S`, boletas |
| 43 | — | Reintento duplicado del webhook | La confirmación encuentra `st<>'PENDING'`: no hace nada (idempotente) |

Si el webhook se pierde, el reconciliador (índice disperso `gsi_pendientes`, cada minuto, pagos de más de 5 minutos) consulta la pasarela con la llave `<oid>#01`, ve el cobro aprobado y confirma. Si el mensaje falla varias veces, va a la DLQ tras `maxReceiveCount` intentos y salta una alarma [D-04].

**Si pasaron más de 8 minutos** y otro tomó la silla, aplica el escenario 2b: reembolso, no doble venta.

### 3d. La pasarela no responde

| t | Servidor | Pasarela | Base |
|---|---|---|---|
| 0 | `PAY#01 INITIATED`; llama | No contesta (*timeout*) | `INITIATED` |
| 10 | Marca `PAY#01` → `UNKNOWN` (no `DECLINED`) | Puede haber cobrado o no | `UNKNOWN`, sillas `L` |
| 60 | Reconciliador consulta con la llave `<oid>#01` | Responde: aprobado, rechazado o inexistente | — |
| 61 | Aprobado: confirma. Rechazado/inexistente: libera las sillas | — | `PAID` o `ABANDONED` |

**Regla:** nunca se libera una silla ni se rechaza una compra mientras el pago esté en `UNKNOWN`: puede haberse cobrado. La llave de idempotencia evita que el reintento cobre dos veces.

**Por qué no hay doble cobro:** (1) la llave `<oid>#nn` se envía a la pasarela en cada intento; (2) `PAY#nn` existe *antes* de llamar; (3) un segundo intento del usuario crea `PAY#02` solo si `PAY#01` está `DECLINED`.

---

## Escenario 4: conmutación (falla de servidor, zona o región)

**Respuesta corta:** servidor y zona no pierden nada y no exigen conmutar la base. La región sí: la base puede perder los últimos segundos (MREC es asíncrona), pero el dinero no: las sillas de todo pago reciente se congelan antes de reabrir y se concilian después con la pasarela. Detalle en [`alta_disponibilidad.md`](../david/alta_disponibilidad.md).

| Falla | RPO | Qué hacer | Fuente |
|---|---|---|---|
| Servidor de aplicación | 0 (el estado vive en la base) | Otro servidor retoma; los reintentos son idempotentes | Escenario 3 |
| Zona de disponibilidad | 0 | Nada: DynamoDB replica en 3 zonas | [R-01], [D-11] |
| Región completa | > 0 en la base (segundos); 0 en pagos por proceso | Cerrar admisión, mover tráfico, congelar sillas en duda, reabrir; conciliar después | [D-07], D-2 |

### 4a. Línea de tiempo: pérdida de la región principal en plena preventa

| t | us-east-1 (activa) | us-east-2 (réplica) | Pasarela | Acción |
|---|---|---|---|---|
| 0 | Opera; las ventas escriben | Recibe replicación (típicamente ≤ 1 s) [D-07] | Cobra | — |
| 100 s | **Falla** | Último dato replicado: T | Sigue cobrando a quien ya estaba pagando | — |
| +1,5 a +5 min | — | — | — | Route 53 (3 revisiones × 30 s) y alarma compuesta; confirmación humana. **Detección, fuera del RTO** [D-22, D-10] |
| 0 (declaración) | — | — | — | **Declaración.** Se registran T y el último `ReplicationLatency` |
| +1 a +2 min | — | Cierra admisión | — | Congelar escrituras |
| +2 a +5 min | — | Recibe el tráfico; aplicación lista en paralelo | — | Cambiar tráfico |
| +3 a +7 min | — | Congela las sillas de todo intento de pago de `bya_ledger` desde `T − W` | Consulta cada pago por su id | **Congelar sillas en duda** |
| +4 a +8 min | — | **Reabre por tramos** | — | **Fin del RTO** |
| Después | — | `confirmarDesastre` por cada pago; libera las congeladas no vendidas; reconstruye contadores | Lista pagos | Conciliar con la venta abierta |

Peor caso, con todo en secuencia: 11 minutos desde la declaración (`alta_disponibilidad.md` §3.3). Los tiempos son **estimados** y solo un simulacro los confirma.

### 4b. Por qué no hay doble venta en el cambio

Dos regiones escribiendo la misma silla podrían venderla dos veces, porque la condición se evalúa contra la versión local y gana la última escritura [D-07]. Por eso escribe **una sola región**. Y como el profesor acepta reabrir antes de terminar la conciliación si las sillas en duda siguen congeladas (respuestas 3b y 6), toda silla que pudo venderse en us-east-1 sin llegar a la réplica queda bloqueada a nombre del incidente. La lista sale del libro de pagos `bya_ledger` (D-2b), que se escribe antes de cobrar y no se pierde con la región:

```text
funcion conmutar(T):
    cerrarAdmision()
    enrutarTrafico(regionAlterna)                 # en paralelo: esperar aplicacionLista()
    W = 8 min + 2 min + ultimo ReplicationLatency
    si no congelarSillasEnDuda(T, W):             # alta_disponibilidad.md §5.0: lee bya_ledger (MRSC)
        mantener la venta cerrada y reintentar     # sin el libro no se sabe qué está en duda
    reabrirGradual()                              # FIN DEL RTO
    para cada intento en bya_ledger(desde = T - W) ordenado por fecha:      # pago pedido por su id
        confirmarDesastre(pago)                   # §5.2; acepta sillas congeladas por el incidente
    liberarCongeladasNoVendidas()
    reconstruirContadores()
```

**Dos bloqueos a la vez sobre la misma silla** (prohibido, respuesta 5) tampoco ocurre. Un bloqueo que no llegó a la réplica queda anulado: su orden no existe en us-east-2, y sin orden no se puede pagar. Si el cliente ya había empezado a pagar, su intento está en el libro y la silla queda congelada.

### 4c. Qué se pierde y qué no

| Elemento | Se puede perder | Cómo se cubre |
|---|---|---|
| Bloqueos de sillas de los últimos segundos | Sí | Las sillas vuelven a `A`; el cliente reintenta |
| Órdenes `PENDING` sin cobrar | Sí | El cliente vuelve a comprar |
| Compras **cobradas** | Segundos de base | Sus sillas quedan congeladas y se reaplican desde la pasarela; sin metadatos, se reembolsan |
| Boletas ya entregadas | Posible | `confirmarDesastre` las recrea con `TKT#UUIDv5(oid, silla)`, el mismo identificador |

---

**Referencias.** [R-xx]: `jacobo/referencias.md`. [D-01] a [D-04]: `concurrencia.md` §9. [D-05], [D-06]: `estadio.md`. [D-07] a [D-14], [D-18] y [D-22]: `alta_disponibilidad.md` §9.
