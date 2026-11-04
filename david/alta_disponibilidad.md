# Conmutación y alta disponibilidad

**Autor:** David · **Fecha:** 2026-11-03, actualizado el 2026-11-04 con las respuestas del profesor (`respuestas_profesor.md`) · **Rúbrica:** Estudio de conmutación y alta disponibilidad (3 puntos)
**Insumos:** `jacobo/arquitectura.md` §4.1, `miguel/recuperacion_licenciamiento_carta.md` (tabla de RTO y runbooks), `miguel/respuesta_a_david.md`. Referencias `[R-xx]` en `jacobo/referencias.md` (citas de Jacobo que no abrí yo); `[D-xx]` al final de este documento (páginas que abrí yo el 2026-11-03).

> **Cambio del 2026-11-04 (respuestas 3 y 6 del profesor):** ya no se cierra toda la venta al perder la región. Se **congelan solo las sillas en duda** (§5.0), se reabre, y la conciliación termina después con esas sillas congeladas. El RTO termina en la reapertura y baja a **4 a 11 minutos** desde la declaración (§3.3).

> **Idea central:** la base no tiene un "servidor principal" que conmutar. Dentro de la región DynamoDB replica en 3 zonas y no hay nada que hacer. Lo que sí se conmuta, y es lo que cuesta tiempo, es **el tráfico y la aplicación** hacia otra región, y ahí el RPO 0 de los **pagos** se logra con un **proceso** (conciliar contra la pasarela), no con la réplica.

---

## 1. Resumen

| Falla | RPO de la base | RPO de pagos | RTO | Mecanismo | Fuente |
|---|---|---|---|---|---|
| Servidor de aplicación | 0 | 0 | Lo que tarde el escalado | El estado vive en la base; la confirmación es idempotente | `concurrencia.md` §5 |
| Zona de disponibilidad (para el profesor es la falla del "servidor principal", no del sitio) | 0 | 0 | Sin conmutación de la base; la aplicación corre en varias zonas | Replicación en 3 zonas, SLA 99,99 % | [D-11, D-12] |
| Región completa (= pérdida del sitio en la nube) | El atraso de replicación: típicamente ≤ 1 s, sin SLA (§3.1) | 0, con las sillas en duda congeladas hasta conciliar | **4 a 11 min desde la declaración** hasta aceptar compras (§3.3); detección y declaración aparte, 2 a 5 min | Réplica en us-east-2 + congelamiento de sillas en duda + conciliación contra la pasarela | [D-07, D-08] |
| Data center de Bogotá (= pérdida del sitio en el Escenario B) | 0 (la base no está allí) | 0 | 3 a 11 min (Miguel) | Aplicación en espera en AWS; runbook 2c | `miguel/` runbook 2c |

## 2. Cómo funciona la alta disponibilidad elegida

### 2.1 Dentro de la región: replicación en 3 zonas

AWS dice que DynamoDB "replica automáticamente tus datos en tres zonas de disponibilidad para dar alta durabilidad y un SLA de disponibilidad de 99,99 %" [D-11] (traducción mía). La escritura se confirma cuando está replicada, por eso **un fallo de zona no pierde datos** (RPO 0) y **no hay conmutación que gestionar**: no hay versiones ni ventanas de mantenimiento [D-11].

### 2.2 Entre regiones: tabla global MREC con una sola región que escribe

| Decisión | Elección | Por qué |
|---|---|---|
| Tipo de tabla global | **MREC** (consistencia eventual entre regiones) | La compra usa `TransactWriteItems`. MRSC (RPO 0 entre regiones) "no soporta operaciones de transacción y devolverá un error si se invocan", tampoco TTL, y exige exactamente tres regiones [D-07] |
| Modo de escritura | **Una sola región escribe** (*write to one Region*): us-east-1 activa, us-east-2 en espera | AWS describe este modo como el que exige "un mecanismo para enrutar las escrituras a la región activa" [D-09]. Evita que dos regiones escriban la misma silla (ver abajo) |
| Regiones | us-east-1 principal, us-east-2 alterna | Decisión D-3 de Jacobo; MRSC no existe en sa-east-1 [R-17] |

**Qué significa MREC para nuestra regla de oro** (todo textual de [D-07], traducción mía):

1. **Transacciones.** "Son solo atómicas dentro de la región donde se invocó la operación" y no se replican como unidad: en otra réplica "solo algunas de las escrituras de una transacción podrían verse". Una réplica puede mostrar una compra **a medias**.
2. **Escrituras condicionales.** "Evalúan la condición contra la versión del ítem en la región". Si dos regiones escribieran, cada una vería su propia versión y **ambas podrían vender la misma silla**.
3. **Conflictos.** Gana "la última escritura" por ítem, según una marca de tiempo interna, y esos conflictos no quedan en CloudWatch ni CloudTrail [D-07, D-08].
4. **Lecturas fuertes.** Devuelven lo último "si el ítem se actualizó por última vez en la región donde ocurre la lectura, pero pueden devolver datos viejos si se actualizó en otra región" [D-07].

De los puntos 1 y 2 sale la regla: **solo una región escribe**. De los puntos 1 y 4 sale la necesidad de la conciliación: tras perder la región, lo que la réplica muestra **no es de fiar** para las últimas ventas.

**SLA.** El de 99,999 % exige que **todas** las tablas de la región sean globales y que se intente la conmutación en un problema regional; si no, aplica el de 99,99 % [D-12]. Con ambas cifras se cumple el mínimo del enunciado (Miguel hace la misma observación).

## 3. Cuánto tarda la conmutación

### 3.1 Qué publica AWS (y qué no)

| Dato | Valor publicado | Fuente |
|---|---|---|
| Conmutación de la **base** | "No hay conmutaciones complicadas o demoradas ni tiempo de inactividad de la base al conmutar una aplicación entre regiones" (la base ya está en las dos) | [D-11] |
| Retraso de replicación MREC | "Típicamente dentro de un segundo o menos"; el RPO es igual al retraso, "usualmente unos segundos"; **no hay SLA** sobre esa latencia | [D-07, D-08] |
| Replicación bajo carga | Capital One midió ≈ 1 s en operación normal y que "bajo carga fuerte la latencia aumentó" (sin cifra) | [D-14] |
| Cambio de tráfico con DNS | TTL de 60 s es típico; no todo el software respeta el TTL ni los cachés intermedios | [D-09] |
| Cambio de tráfico, extremo a extremo | Con ARC: "segundos a pocos minutos, según la propagación del TTL de DNS". Solo con DNS: "varios minutos" | [D-10] |
| Revisión de salud de Route 53 | Cada 10 o cada 30 s; el tiempo total depende del umbral de fallos y **AWS no da una fórmula** | [D-13] |
| RTO absoluto de la conmutación de una región de DynamoDB | **AWS no publica una cifra** | [D-08, D-10] |

**Atraso de replicación que asumimos (condición a del profesor).** Típicamente 1 s o menos [D-07]; Capital One midió ≈ 1 s y vio que crece bajo carga [D-14]; AWS no da SLA [D-08]. Diseñamos para **hasta 60 s**: una alarma salta si `ReplicationLatency` pasa de 60 s durante la preventa, y en ese caso el coordinador sabe que la ventana de §5.0 debe crecer en lo mismo. **La seguridad no depende de esa cifra**: las sillas en duda salen de la pasarela, no de la réplica, y la ventana se fija como 8 minutos de bloqueo + 2 de margen + el último atraso medido.

**Consecuencia honesta:** el único dato con número es el de enrutamiento (segundos a minutos). Todo el resto del RTO (congelar, levantar la aplicación, conciliar) son **tiempos de nuestro propio procedimiento**, y solo un simulacro los confirma.

### 3.2 Criterio para declarar la falla

El enunciado mide el RTO "desde que se declara la falla" (hallazgo H-2 de Miguel), así que el criterio debe estar acordado **antes** de la preventa. Propuesta, basada en lo que AWS recomienda [D-10]:

* **Alarma compuesta** de CloudWatch con `SystemErrors` de DynamoDB, `ReplicationLatency` y el porcentaje de errores 5xx de la API. AWS da como ejemplo una alarma que se activa cuando los 5xx "superan 5 % durante tres periodos consecutivos de 1 minuto" [D-10].
* **Confirmación humana:** el coordinador del incidente y el DBA de guardia revisan el estado de AWS (AWS Health) y **declaran**. Es una decisión manual a propósito: declarar congela sillas y mueve todo el tráfico de región.
* **Revisión de salud de Route 53** contra el punto de compra de us-east-1: cada 30 s y falla tras 3 revisiones seguidas, que son los valores por defecto (umbral entre 1 y 10; intervalo de 10 o 30 s) [D-22]. Con eso la detección automática tarda unos **90 s**; con el intervalo rápido de 10 s, unos 30 s, con costo adicional [D-13].
* Se anotan la hora **T** de la última escritura visible y la última `ReplicationLatency` (paso 1 del runbook 2b).

**Tiempo de detección y declaración, reportado aparte del RTO (respuesta 6 del profesor):**

| Etapa | Tiempo | Fuente |
|---|---|---|
| Route 53 marca la falla (3 revisiones × 30 s) | ≈ 1,5 min | [D-22] |
| La alarma compuesta de CloudWatch se activa (3 periodos de 1 min) | ≈ 3 min, en paralelo | [D-10] |
| El coordinador y el DBA confirman en AWS Health y declaran | 0 a 2 min | Supuesto |
| **Detección y declaración** | **≈ 2 a 5 min** | Se mide en el simulacro |

**Criterio de declaración:** alarma compuesta activa **y** Route 53 en falla **y** confirmación humana. Es manual a propósito: congelar y conmutar no se hace por un falso positivo.

### 3.3 RTO nuevo: la conciliación sale del camino crítico

El profesor dice que el RTO termina "hasta que la plataforma acepta compras otra vez con datos correctos", y que "la conciliación de pagos pendientes puede terminar después, siempre que esas sillas sigan congeladas" (respuesta 6). Eso saca la conciliación y la reconstrucción de contadores del RTO.

| Paso | Minutos | Fuente u observación |
|---|---|---|
| 1. Cerrar la admisión y no enrutar a us-east-1 | 1 a 2 | Miguel |
| 2. Cambiar el tráfico a us-east-2 (la gente ve la sala de espera) | 1 a 3 | "Segundos a pocos minutos" con ARC, "varios minutos" solo con DNS [D-10]; vale con TTL de 60 s y el cambio preparado |
| 3. Aplicación en us-east-2 lista (en paralelo con el paso 2) | 0 a 3 | Miguel; réplica pre-calentada automáticamente [D-18] |
| 4. **Congelar las sillas en duda** (§5.0) | 1 a 2 | Supuesto: una búsqueda en Mercado Pago y unos pocos miles de escrituras |
| 5. Reabrir por tramos | 1 | Miguel |
| **RTO (pasos 2 y 3 en paralelo)** | **4 a 8** | Suma de mínimos y máximos |
| **RTO (todo en secuencia)** | **4 a 11** | Peor caso |
| Después del RTO: conciliar (§5.1–5.3) y reconstruir contadores (§5.4) | 4 a 7 | No cuenta en el RTO: las sillas en duda siguen congeladas |

**Cumplimiento de la condición c del profesor:** el peor caso estimado (11 min) queda **por debajo de 15**, con 4 minutos de margen. Si el simulacro midiera más de 15, la diferencia se cierra con lo que más pesa: automatizar el cambio de tráfico con Application Recovery Controller en vez de DNS manual [D-10], cuyo costo debe cotizar Juan Pablo. Ningún tiempo de esta tabla está medido.

**Total desde la falla**, para informarlo completo: 2 a 5 min de detección y declaración más 4 a 11 de RTO, es decir **6 a 16 minutos**.

## 4. Por qué ninguna orden confirmada se pierde (RPO 0)

| Pregunta del jurado | Respuesta |
|---|---|
| ¿Se pierde una orden si cae un servidor? | No. La orden y el pago están en la base y la confirmación es idempotente (`concurrencia.md` §5–§6) |
| ¿Y si cae una zona? | No. Se confirma tras replicar en 3 zonas [D-11] |
| ¿Y si cae una región? | La **base** puede perder los últimos segundos (RPO = retraso de replicación [D-07]). Pero el **dinero** no se pierde: la pasarela guarda cada cobro, las sillas de esos cobros se congelan antes de reabrir y se concilian después |
| ¿Puede entonces venderse dos veces una silla? | No. Toda silla que pudo venderse en us-east-1 sin llegar a la réplica tiene un cobro en la pasarela, y esa silla queda congelada hasta conciliarla. Además, solo escribe una región |
| ¿Pueden dos personas tener la misma silla bloqueada a la vez? | No. Un bloqueo que no llegó a la réplica queda anulado: su orden no existe en us-east-2, así que ese cliente no puede pagar con él y debe volver a elegir. Si ya había empezado a pagar, su cobro está en la pasarela y la silla queda congelada (§5.0) |

La afirmación "RPO 0 de pagos" depende de **tres capacidades de la pasarela**. El 2026-11-03 Miguel, Jacobo y David eligieron **Mercado Pago** (D-11, `pasarelas.md`), que documenta las tres: llave de idempotencia obligatoria (`X-Idempotency-Key`), campo `metadata` en el pago (evento, usuario y sillas) y búsqueda de pagos por rango de fechas (`/v1/payments/search`). **Falta comprobar en el sandbox** que `metadata` guarda y devuelve un objeto propio y que repetir con la misma llave devuelve el mismo pago. Si `metadata` no sirve, las sillas de un pago no se pueden reconstruir: se reembolsa o se activa el libro de pagos de Jacobo (`bya_ledger`). Es la condición 1 y 2 de Miguel, y las acepto.

## 5. Modo desastre: confirmar un pago cuando la orden o la silla se perdieron

Este es el paso 4 del runbook 2b de Miguel. **No sirve la confirmación normal** (`concurrencia.md` §5), por tres razones que salen de §2.2:

| Por qué falla la normal | Consecuencia |
|---|---|
| Lee `orden.sil` de `ORDER`, que puede no existir en la réplica | No sabe qué sillas confirmar |
| Exige `st='L' AND lo=:oid` | En la réplica la silla puede estar `A` (el bloqueo no alcanzó a replicarse) y la condición falla |
| Cuenta con que la compra se aplicó completa o nada | Una réplica puede mostrar una compra **a medias** [D-07]: `ORDER` en `PAID` y la silla todavía en `L` |

### 5.0 Congelar las sillas en duda (respuesta 3b del profesor)

**Qué silla está en duda.** Una silla solo puede estar vendida en us-east-1 sin que la réplica lo sepa si su pago existe en la pasarela: para vender, la compra pasa siempre por un cobro (`concurrencia.md` §4). Por eso:

> **Sillas en duda** = las sillas del `metadata` de **todo pago de Mercado Pago creado desde `T − W`**, en cualquier estado salvo rechazado o cancelado (los nombres exactos de estado se confirman en el sandbox). `W` = 8 min de bloqueo + 2 min de margen + el último `ReplicationLatency` medido.

Un pago creado antes de `T − W` corresponde a un bloqueo que ya venció en us-east-1. Si se aprueba después, se trata como en el escenario 2b del anexo: si la silla sigue libre se confirma; si otro la tomó, se reembolsa. Es lo mismo que pasaría sin desastre.

**Cómo se congela, sin estado nuevo.** Cada silla en duda se bloquea a nombre del incidente, con un vencimiento lejano. La condición normal de bloqueo (`st = 'A' OR (st = 'L' AND lx < :vencido_antes_de)`) ya rechaza esa silla para cualquier otro cliente:

```text
funcion congelarSillasEnDuda(T, W, incidente):
    pagos = MercadoPago GET /v1/payments/search  range=date_created  begin_date=T-W  end_date=NOW
    si la búsqueda falla: NO reabrir; seguir con las ventas cerradas y reintentar        # respaldo seguro
    para cada pago p que no esté rechazado ni cancelado:
        para cada silla s de p.metadata.sillas:
            Update bya_seats Key de s
                IF  st <> 'S'                                   # una vendida ya no se puede comprar
                SET st = 'L', lo = :conc, lx = :lejos ADD v :uno   # :conc = "CONC#<incidente>", :lejos = T + 1 día
    registrar en el incidente cuántas sillas quedaron congeladas
```

* Si el `Update` falla porque la silla está `S`, ya está protegida: no hace falta congelarla.
* Pisar un bloqueo `L` de la misma orden no hace daño: `confirmarDesastre` acepta las sillas congeladas por el incidente (§5.2).
* El mapa mostrará esas sillas como no disponibles. El profesor acepta que el mapa vaya con atraso mientras la validación final sea contra la base (respuesta 5).
* El límite de 10 sillas por usuario (`LIM#`) puede estar desactualizado en la réplica al reabrir. Eso no causa doble venta y se recalcula al final de la conciliación (§5.4).

**Cuándo se libera una silla congelada.** Según el estado final de su pago:

| Estado del pago | Qué se hace con sus sillas |
|---|---|
| Aprobado | `confirmarDesastre` las vende a esa orden (§5.2) |
| Rechazado o cancelado | Se liberan |
| Todavía en proceso (por ejemplo, un pago que tarda en confirmarse) | **Siguen congeladas** hasta que la pasarela dé el estado final. El webhook o el reconciliador decide entonces: aprobado, se confirma; rechazado, se liberan |

Liberar es esta escritura, que solo toca sillas que siguen a nombre del incidente:

```text
Update bya_seats Key de s  IF st = 'L' AND lo = :conc  SET st = 'A'  REMOVE lx, lo  ADD v :uno
```

### 5.1 Datos de partida y precondiciones

* **Entrada:** **los mismos pagos que se usaron para congelar** (§5.0): todo pago de Mercado Pago creado desde `T − W`, no solo los últimos 5 minutos. Conciliar una ventana más corta que la del congelamiento dejaría sillas congeladas sin revisar, y al liberarlas se podría perder una compra pagada. Cada pago trae `oid`, `nn`, `gtx`, `uid`, `eid`, `sillas[]`, `monto` y `aprobado_en` en su `metadata`. Los aprobados pasan por `confirmarDesastre`; los que siguen en proceso esperan (ver abajo).
* **Precondiciones:** las sillas en duda ya están congeladas (§5.0); la aplicación en us-east-2 apunta a la réplica local; nadie escribe en us-east-1. Las ventas pueden estar **abiertas**: ninguna otra compra puede tocar una silla congelada.
* **Orden de proceso:** por `aprobado_en` ascendente. Si dos cobros aprobados reclaman la misma silla, gana el primero y el otro se reembolsa. Nunca hay doble venta; en el caso raro puede que la silla vaya a quien no la tenía en us-east-1, y por eso el criterio es explícito.

### 5.2 Pseudocódigo

```text
funcion confirmarDesastre(cobro):                    # cobro viene de la pasarela
    ahora = epoch_segundos()
    :vencido_antes_de = ahora - :skew                # las condiciones no admiten aritmética [D-01]

    repetir hasta 3 veces:                           # un choque con otra escritura obliga a replanificar
        # 1. LEER (fuerte, en la réplica local). Las lecturas por lote no necesitan ser transaccionales.
        orden   = GetItem(ORD#oid / ORDER)
        pago    = GetItem(ORD#oid / PAY#nn)
        sillas  = BatchGetItem fuerte de cada silla de cobro.sillas
        tickets = BatchGetItem fuerte de TKT#UUIDv5(oid, silla)
        inv     = GetItem(ORD#oid / INV#1)

        # 2. DECIDIR si todas las sillas son nuestras o están libres
        para cada silla s:
            mia   = (s.st == 'S' y s.so == oid)
            libre = (s.st == 'A')
                 o (s.st == 'L' y (s.lo == oid o s.lo == :conc o s.lx < :vencido_antes_de))
            si no (mia o libre): conflicto = verdadero

        si conflicto:
            # alguien más tiene la silla (S de otra orden o bloqueo vigente de otra)
            planificar ORDER -> 'FULFILL_FAIL' (Put si falta; Update IF st <> 'PAID' si existe)
            planificar PAY   -> 'APPROVED' (Put si falta; Update IF st IN (INITIATED, UNKNOWN))
            ejecutar; encolar reembolso con llave refund#oid; devolver REEMBOLSO

        # 3. PLANIFICAR solo lo que falta (cada acción afirma lo que se leyó)
        acciones = []
        para cada silla s que no es 'mia':
            acciones += Update bya_seats  Key de s
                IF  (st = 'A')
                 OR (st = 'L' AND (lo = :oid OR lo = :conc OR lx < :vencido_antes_de))
                 OR (st = 'S' AND so = :oid)                     # por si otra ejecución ya la tomó
                SET st = 'S', so = :oid, tk = :tid  REMOVE lx, lo  ADD v :uno
        para cada ticket ausente:
            acciones += Put bya_tickets TKT#tid / T (st='VALID', ...)  IF attribute_not_exists(pk)
        si orden ausente:   acciones += Put    ORDER (st='PAID', sil=cobro.sillas, tot=cobro.monto,
                                                      uid, eid, ttl=:ttl_largo)  IF attribute_not_exists(pk)
        si orden != 'PAID': acciones += Update ORDER SET st='PAID', sil=cobro.sillas, ttl=:ttl_largo
                                                      IF st IN (:pending, :expired)
        si pago ausente:    acciones += Put    PAY#nn (st='APPROVED', gtx, idem=oid#nn, amt)  IF attribute_not_exists(pk)
        si pago != 'APPROVED': acciones += Update PAY#nn SET st='APPROVED', gtx REMOVE g3pk, g3sk
                                                      IF st IN (:initiated, :unknown)
        si inv ausente:     acciones += Put    INV#1 (st='PENDING', g3pk=PEND#INV#n)  IF attribute_not_exists(pk)
        # NO se toca el contador de la localidad ni LIM#: se reconstruyen al final (§5.4)

        si acciones vacío: devolver YA_COMPLETA
        intentar:
            TransactWriteItems(acciones, ClientRequestToken = H(oid, "CONFIRM-D"))
            devolver CONFIRMADA
        capturar TransactionCanceledException:
            continuar                                            # releer y replanificar
    devolver ERROR_REVISAR_A_MANO                                # alerta; no se reembolsa a ciegas
```

### 5.3 Por qué esto es seguro

* **No hay doble venta.** Una silla pasa a `S` solo si está libre, vencida, ya es de esta orden o ya es vendida a esta orden. Si es de otra orden, el cobro va a reembolso. Aunque las ventas estén abiertas, ninguna compra nueva puede tomar una silla congelada, y solo escribe una región [D-07].
* **Es idempotente.** Se puede ejecutar dos veces (o por el webhook y por el reconciliador a la vez): el segundo plan solo encuentra lo que falta, y la condición `st = 'S' AND so = :oid` hace que repetir la silla no falle.
* **Cubre "PAID" a medias.** Miguel indica "si está `PAID`, no hacer nada". Con transacciones que no se replican como unidad [D-07], una orden en `PAID` puede tener la silla en `L` o la boleta sin crear. Por eso **también las órdenes `PAID` de la ventana pasan por `confirmarDesastre`**, que no hace nada si todo está completo (`YA_COMPLETA`) y repara si no.
* **Las boletas no se pisan.** Cada acción de boleta es `attribute_not_exists`: si la boleta ya estaba (incluso `USED`), no se toca.
* **Si no se pueden conocer las sillas** (sin metadatos): se reembolsa. Se pierde la venta, no el dinero ni la integridad.

### 5.4 Contadores: de "verificar" a "reconstruir"

Miguel propone verificar que la suma de fragmentos iguale las sillas `S`. Con transacciones a medias el contador puede haberse replicado sin la silla, o al revés, y `confirmarDesastre` no lo toca. Propongo: **al terminar la conciliación**, para cada localidad se cuentan las sillas `S` (consulta por filas, como el constructor del mapa) y se **fijan** los fragmentos (`SH#00` = el total, el resto en 0). Es válido porque el contador es **derivado** de las sillas (Jacobo, `entrega_para_el_equipo.md` §3.1). Como las ventas ya están abiertas, contar y fijar no es atómico: una venta que ocurra entre las dos operaciones puede dejar el contador corrido en unas pocas sillas. **Eso no afecta la doble venta**, porque la decisión de vender nunca usa el contador sino la silla, y el profesor acepta que lo que se muestra vaya con atraso (respuesta 5). El contador se reconstruye otra vez, exacto, cuando la preventa cierra. El límite por usuario `LIM#` se recalcula desde las órdenes, como indica Miguel.

### 5.5 Pagos que llegan después de abrir

Un cliente que ya estaba pagando cuando cayó la región puede ser aprobado **después** de reabrir. Para esos cobros, el consumidor de SQS usa `confirmarDesastre` con el mismo metadato **mientras la hora de creación de la orden sea anterior a la hora de declaración**. Para el resto, la confirmación normal.

## 6. Cuando vuelve la región original

Miguel pregunta si su lectura es correcta: la región original **no recibe tráfico ni escrituras** al volver y se concilia otra vez contra la pasarela. **La confirmo, con un matiz.**

* AWS dice que al volver "todas las replicaciones salientes y entrantes pendientes se reintentarán" y que "no se requiere ninguna acción especial" [D-08]. Eso es lo que necesitamos: **dejar que converja**, no intervenir a mano.
* El matiz es el criterio de "última escritura gana" [D-07]: las escrituras de la conciliación en us-east-2 son **posteriores** a las pendientes de us-east-1, así que normalmente ganan. Pero si us-east-1 tenía una versión más reciente de algún ítem que nunca llegó a replicarse, ese ítem podría volver con un estado distinto del que decidió la conciliación. Como estos conflictos no se registran [D-08], **se concilia otra vez contra la pasarela** después de la convergencia y antes de cualquier regreso a us-east-1, y el regreso se hace fuera de una preventa (Miguel).

## 7. Costo en rendimiento

| Mecanismo | Efecto en la latencia de la compra | Costo adicional |
|---|---|---|
| Replicación en 3 zonas | Ninguno medible; ya está incluido en el "milisegundo de un dígito" del servicio [D-11] | Ninguno |
| MREC (elegido) | Ninguno en la escritura: la replicación es asíncrona [D-07] | Escrituras replicadas (USD 0,625 por millón en us-east-1, cifra de Jacobo, `entrega_para_el_equipo.md` §2.4) |
| MRSC (descartado) | Subiría la latencia de escritura (cruza regiones), según Jacobo (`arquitectura.md` §4.1) | No se puede usar con transacciones |
| Conciliación en modo desastre | No afecta la preventa normal | Horas de DBA; el enunciado asigna 6 horas por preventa (Miguel) |
| Pre-calentamiento de la réplica | — | Ninguno extra: se aplica solo a todas las réplicas (abajo) |

**Pre-calentamiento de la réplica: resuelto por Jacobo.** Mi temor era que la réplica de us-east-2, que solo recibe tráfico de replicación, no soportara la carga de pico al conmutar. Jacobo encontró que en las tablas globales los valores de *warm throughput* "se aplicarán automáticamente a todas las réplicas" [R-18, D-18] (traducción mía). Basta con pre-calentar la tabla global al nivel del pico (≈ 10.546 WCU, cifra de Jacobo). Queda para Juan Pablo saber si el cargo del pre-calentamiento se cobra por región.

## 8. Pendientes

* **Pasarela:** elegida Mercado Pago (2026-11-03). Falta la prueba de sandbox de `pasarelas.md` §2 (Miguel, Jacobo, David).
* **Jacobo:** ya diseñó el libro de pagos en MRSC (`bya_ledger`, opcional) por si la pasarela no permite metadatos; se activa según la pasarela que se elija.
* **Miguel:** hecho el 2026-11-03 (runbook 2b de 10 pasos).
* **Profesor:** P-4 respondida el 2026-11-04: región en la nube, data center en Bogotá.
* **Miguel:** pasar el runbook 2b al congelamiento de sillas en duda (§5.0) y a la tabla de RTO de §3.3.
* **Simulacro:** ningún tiempo de este documento se ha medido; el plan de pruebas es de Miguel.

## 9. Referencias propias

Consultadas el 2026-11-03. Las citas en español son traducciones mías.

| ID | Fuente | Qué respalda |
|---|---|---|
| D-07 | [How DynamoDB global tables work](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html) | Transacciones solo atómicas en la región de origen y visibles a medias en réplicas; escrituras condicionales contra la versión local; "última escritura gana"; lecturas fuertes posiblemente viejas; retraso típico ≤ 1 s y RPO de unos segundos; MRSC sin transacciones ni TTL y con tres regiones |
| D-08 | [Best practices for global table design](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-global-table-design.html) | Al volver una región se reintentan las replicaciones pendientes sin acción especial; `ReplicationLatency` sin SLA; conflictos no registrados en CloudWatch ni CloudTrail; MREC con RPO y RTO "medidos en segundos"; sin cifra de conmutación |
| D-09 | [Routing strategies in DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-global-table-design.prescriptive-guidance.request-routing.html) | Modo *write to one Region*; TTL de DNS de 60 s típico y sus límites |
| D-10 | [Best practices for DynamoDB global tables, Part 2: failover strategies](https://aws.amazon.com/blogs/database/best-practices-for-amazon-dynamodb-global-tables-part-2-failover-strategies/) | RTO con ARC "segundos a pocos minutos" y con DNS "varios minutos"; alarma compuesta con `SystemErrors` y `ReplicationLatency`; ejemplo de 5xx > 5 % durante tres minutos; aumentar capacidad en la región destino; operaciones idempotentes y escrituras condicionales; pruebas con AWS Fault Injection Service |
| D-11 | [What is Amazon DynamoDB?](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html) | Replicación en 3 zonas y SLA 99,99 %; sin conmutaciones complicadas ni demoradas entre regiones; sin ventanas de mantenimiento |
| D-12 | [Amazon DynamoDB SLA](https://aws.amazon.com/dynamodb/sla/) | 99,99 % estándar y 99,999 % para tablas globales; condiciones del segundo |
| D-13 | [How Route 53 determines the health of endpoints](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-determining-health-of-endpoints.html) | Revisión cada 10 o 30 s; sin fórmula del tiempo total |
| D-14 | [Capital One: Moving to DynamoDB to increase application resiliency](https://www.capitalone.com/tech/software-engineering/comparing-dynamodb-and-aurora-global-database-and-aurora-multi-master/) | Caso publicado: replicación ≈ 1 s en operación normal, mayor bajo carga; sin tiempo de conmutación absoluto |
| D-18 | [Understanding DynamoDB warm throughput](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/warm-throughput.html) | En tablas globales, el *warm throughput* se aplica automáticamente a todas las réplicas; la duración del pre-calentamiento depende de los valores y del tamaño de la tabla |
| D-22 | [Route 53 API: HealthCheckConfig](https://docs.aws.amazon.com/Route53/latest/APIReference/API_HealthCheckConfig.html) | `FailureThreshold` entre 1 y 10, por defecto 3; `RequestInterval` de 10 o 30 s, por defecto 30 |
