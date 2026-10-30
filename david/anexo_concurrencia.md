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

## Escenario 3: falla a mitad de la compra (borrador, semana 2)

Casos a desarrollar, cada uno con su línea de tiempo:

| Punto de falla | Qué queda en la base | Quién lo resuelve | Mecanismo |
|---|---|---|---|
| Durante la transacción de bloqueo o confirmación | Nada o todo; nunca la mitad | DynamoDB | Atomicidad [R-04] |
| Respuesta perdida (*timeout*) | No se sabe si se aplicó | El cliente | Reintento con el mismo `ClientRequestToken` dentro de 10 min [R-04]; después, lectura fuerte de la orden |
| Servidor cae tras cobrar y antes de confirmar | `PAY#01` en `INITIATED`, orden `PENDING` | Webhook → SQS, o reconciliador | Confirmación idempotente; DLQ [D-04] |
| La pasarela no responde | `PAY#01` en `UNKNOWN` | Reconciliador | Consulta a la pasarela con la llave `<oid>#<nn>` |

## Escenario 4: conmutación del servidor (borrador, semana 2)

| Falla | RPO | Qué hacer | Fuente |
|---|---|---|---|
| Servidor de aplicación | 0 (el estado vive en la base) | Otro servidor retoma; los reintentos son idempotentes | — |
| Zona de disponibilidad | 0 | Nada: DynamoDB replica en 3 zonas, sin conmutación que gestionar | [R-01] |
| Región completa | > 0 en la base (MREC asíncrona) | Modo seguro: conciliar con la pasarela y marcar vendidas las sillas de pagos aprobados **antes** de reabrir; una sola región escribe | [R-17], decisión D-2 |

Pendiente: tiempos de conmutación publicados, RTO de 15 min y conciliación con los runbooks de Miguel.
