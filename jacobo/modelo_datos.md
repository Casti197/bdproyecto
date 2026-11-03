# Modelo de datos en DynamoDB — BoletaYa SAS

**Autor:** Jacobo · **Estado:** modelo **aprobado por David** (claves soportan los 4 escenarios) · **Redacción:** 2026-10-29 · **Revisión:** 2026-11-03 (correcciones de David y Miguel; ver [`respuesta_a_revisiones.md`](respuesta_a_revisiones.md))
**Motor / nube:** Amazon DynamoDB en AWS (servicio administrado, sin versiones ni ediciones)
**Cifras de capacidad:** se calculan en [`capacidad_y_volumetria.md`](capacidad_y_volumetria.md) con [`calculos/modelo_capacidad.py`](calculos/modelo_capacidad.py). Las fuentes están en [`referencias.md`](referencias.md) con la clave `[R-xx]`.

> **Convenciones.** `DATO` = viene del enunciado oficial. `SUPUESTO A-xx` = lo define este grupo y se lista en el README. `[R-xx]` = fuente oficial consultada el 2026-10-29. Lo que no pude verificar está marcado **PENDIENTE**.

---

## 0. Resumen de decisiones

| # | Decisión | Una línea de justificación |
|---|---|---|
| D1 | **8 tablas especializadas** (no una sola, no una por entidad) | Cada tabla tiene patrón de acceso, retención, calor y permisos distintos; las transacciones de DynamoDB funcionan entre tablas de la misma cuenta y región [R-04]. |
| D2 | **Sillas sin GSI**, particionadas por `evento#localidad#fila` | Un GSI por localidad sería una partición caliente que, además, frena las escrituras de la tabla base [R-03]. |
| D3 | **Contador por localidad fragmentado (N=8 por defecto)**, actualizado **dentro de la misma transacción** que marca la silla como vendida | Exacto y atómico con la venta; el fragmento lo fija `hash(orderId) mod N`, así un reintento cae en el mismo fragmento. |
| D4 | **El bloqueo de 8 min vive en la silla** (`lx` = vence en, `lo` = dueño); la condición trata un bloqueo vencido como disponible | El TTL solo limpia y puede tardar días [R-08]; nunca decide. |
| D5 | **Historial de sillas derivado por DynamoDB Streams** con clave determinista `(silla, versión)` | Escritura idempotente: un reintento de Lambda sobreescribe el mismo ítem. |
| D6 | **Mapa de sillas = instantánea aproximada** (S3/CloudFront); la confirmación es siempre la transacción en DynamoDB | La caché nunca es la fuente para decir "disponible". |
| D7 | **Histórico**: TTL a los 2 años + exportación incremental diaria a S3 + Athena | Las exportaciones no consumen RCU ni afectan la tabla [R-09]. |
| D8 | **Libro de pagos en MRSC: opcional** (plan B de la decisión D-2, §3.9) | Solo si la pasarela no permite guardar las sillas como metadato del cobro. |

---

## 1. Patrones de acceso

Frecuencias del **año 1** (derivadas en `capacidad_y_volumetria.md`): preventa promedio = 20 órdenes/s, 50 boletas/s; "×5" = ráfaga instantánea razonada (el enunciado no da la distribución dentro de los 20 min, ver limitación L-1); operación normal = 0,056 órdenes/s.

| ID | Patrón | Entidad / tabla | PK | SK | Índice | Consistencia | Frecuencia estimada | Destino |
|---|---|---|---|---|---|---|---|---|
| AP-01 | Consultar un evento y sus localidades | `bya_catalog` | `EVT#<eid>` | `META` / `SEC#<sid>` (Query sin condición de SK) | — | Eventual | Lectura masiva; solo fallos de caché llegan a la base (TTL de CDN 60 s) | **CDN/caché** primero; DynamoDB como fuente |
| AP-02 | Sillas disponibles de una localidad | `bya_seats` | `E<eid>#S<sid>#R<fila>` | `S<nro>` | — (Query por fila, ~900 filas en un estadio de 45.000) | Eventual (constructor de mapa) | 450 RRU/s por evento activo (refresco cada 2 s); los usuarios leen la **instantánea**, no la tabla | **Instantánea** (S3 + CloudFront + ElastiCache); DynamoDB solo la alimenta |
| AP-03 | Estado de una silla | `bya_seats` | igual | igual | — | **Fuerte** (`ConsistentRead`) | ≈ (1 + f) × 2,5 lecturas por orden; f = bloqueos fallidos por exitoso | DynamoDB |
| AP-04 | Bloquear varias sillas en una compra | `bya_seats` + `bya_orders` + `bya_counters` | igual | igual | — | **Transacción** `TransactWriteItems` (serializable) | Promedio 20 exitosos/s (60 intentos/s con f=2); ×5 = 300 intentos/s | DynamoDB (nunca caché) |
| AP-05 | Registrar una orden | `bya_orders` | `ORD#<oid>` | `ORDER` | `gsi_usuario`, `gsi_evento_orden` (se alimentan solos) | Transacción (dentro de AP-04 y de la confirmación) | = órdenes: 20/s promedio | DynamoDB |
| AP-06 | Registrar intentos de pago | `bya_orders` | `ORD#<oid>` | `PAY#<nn>` | `gsi_pendientes` (dispersa) | Fuerte (`PutItem` condicional) | 26 intentos/s (1,3 por orden), ×5 = 130/s | DynamoDB |
| AP-07 | Órdenes de un usuario | `bya_orders` | `USR#<uid>` (en el GSI) | `<creada>#<oid>` | **`gsi_usuario`** | Eventual (los GSI no ofrecen lectura fuerte [R-03]) | Supuesto: ≈ 1 por orden + visitas; < 5/s | DynamoDB |
| AP-08 | Boletas de una orden | `bya_orders` → `bya_tickets` | `ORD#<oid>` / `TKT#<tid>` | `ORDER` / `T` | — (la orden guarda la lista de `tid`; `BatchGetItem` ≤ 100) | Fuerte | 1 por orden + consultas del cliente | DynamoDB |
| AP-09 | Validar boleta por QR | `bya_tickets` | `TKT#<tid>` | `T` | — | **Fuerte** + `UpdateItem` condicional (`st = VALID`) | 45.000 boletas / 90 min = 8,3 boletas/s; 10 lecturas/s (1,2 por boleta) | DynamoDB; **servidor local** si no hay internet |
| AP-10 | Registrar un escaneo | `bya_tickets` | `TKT#<tid>` | `SCAN#<ts>#<puerta>` | — | Transacción con AP-09 | 10/s promedio; ×3 al abrir puertas (supuesto) | DynamoDB; cola local → sincronización |
| AP-11 | Contador exacto de boletas por localidad | `bya_counters` | `CNT#E<eid>#S<sid>` | `SH#<00..N-1>` | — | **Fuerte**: `BatchGetItem` de N fragmentos (o `TransactGetItems` para instantánea serializable) | Tablero de organizador: ≤ 20 localidades × 1/s = 20 lecturas/s (×8 o ×16 RRU) | DynamoDB (el número exacto no sale de caché) |
| AP-12 | Historial de una silla | `bya_seat_history` | `E<eid>#S<sid>#R<fila>#<nro>` | `V#<versión 8 dígitos>` | — | Eventual | Auditoría/soporte: baja | DynamoDB |
| AP-13 | Ventas de un evento (reembolsos por cancelación) | `bya_orders` | `EVT#<eid>#<n>` (n = 0..7) | `<creada>#<oid>` | **`gsi_evento_orden`** (8 consultas en paralelo, filtro `st = PAID`) | Eventual + verificación fuerte de cada orden antes de reembolsar | Rara (cancelaciones); una pasada completa | DynamoDB → SQS de reembolsos |
| AP-14 | Registrar y consultar auditorías | `bya_audit` | `ENT#<tipo>#<id>` | `<ts>#<ulid>` | `gsi_actor` (**dispersa**, solo acciones humanas) | Escritura: transacción si es cambio administrativo; lectura eventual | 1,9/s promedio (5 M/mes) + 2 por orden en pico | DynamoDB (reciente) / **Athena** (consulta amplia) |
| AP-15 | Datos históricos archivados | S3 (exportación) | — | — | Tabla externa de Athena | — | Reclamos y auditorías: esporádico | **Athena** |
| AP-16 | Buscar usuario por correo (ingreso) | `bya_users` | `EM#<sha256(correo)>` (en el GSI) | `USR#<uid>` | `gsi_email` | Eventual | Proporcional a inicios de sesión | DynamoDB |
| AP-17 | Pagos y facturas pendientes (conciliación) | `bya_orders` | `PEND#<tipo>#<n>` (en el GSI) | `<creada>#<oid>#<ref>` | **`gsi_pendientes`** (dispersa) | Eventual; la decisión se confirma leyendo el ítem con lectura fuerte | Periódica (cada 1–5 min) | DynamoDB → SQS |
| AP-18 | Boletas de un evento (copia para el estadio) | `bya_tickets` | `EVT#<eid>#<n>` (en el GSI) | `TKT#<tid>` | **`gsi_evento_boleta`** (8 consultas en paralelo) | Eventual | Una vez antes de cada evento | DynamoDB → servidor local |
| AP-19 | Eventos de un organizador | `bya_catalog` | `ORG#<oid>` (en el GSI) | `<inicio>#EVT#<eid>` | `gsi_organizador` | Eventual | Baja | DynamoDB |
| AP-20 | Límite de compra por usuario (antibots) | `bya_counters` | `LIM#E<eid>#U<uid>` | `P` | — | Transacción (dentro de AP-04) | = intentos de bloqueo | DynamoDB |

**Regla de oro del modelo:** ninguna decisión de venta, de ingreso o de reembolso se toma leyendo un GSI ni la caché. Los GSI son eventualmente consistentes y se actualizan de forma asíncrona ("en una fracción de segundo… en algunos fallos, más") [R-03].

---

## 2. ¿Una tabla o varias? Comparación

La documentación oficial recomienda "mantener tan pocas tablas como sea posible", y reconoce la excepción de **conjuntos de datos con patrones de acceso muy distintos** y de series de tiempo de alto volumen [R-05]. El diseño de tabla única tiene ventajas reales (localidad de datos, una consulta para varias entidades, tráfico más suave) y desventajas reales (copias de seguridad "todo o nada", cifrado compartido, Streams con todos los cambios, clase Standard-IA menos útil con datos mezclados) [R-06].

| Criterio | Tabla única | **8 tablas especializadas (elegida)** | Una tabla por entidad (≈ 10) |
|---|---|---|---|
| **Transacciones** (bloqueo y confirmación tocan sillas + orden + contador + boletas) | Funcionan | Funcionan: una transacción puede abarcar varias tablas de la misma cuenta y región [R-04] | Funcionan |
| **Calor de las sillas** | Las sillas y todo lo demás comparten límites de capacidad y de GSI | Las sillas quedan aisladas, **sin GSI**, con su propio `warm throughput` | Igual que la elegida |
| **GSI y contrapresión** | Un GSI caliente frena escrituras de *cualquier* entidad | El GSI de órdenes solo frena órdenes | Igual |
| **Retención y TTL distintos** (órdenes 2 años; escaneos 1 año; sillas 90 días tras el evento) | Un mismo atributo TTL sirve a todos los tipos; difícil auditar | TTL y política por tabla | Igual |
| **Respaldo / restauración** (Miguel) | Todo o nada | Tablas críticas (`bya_orders`, `bya_tickets`, `bya_seats`) con PITR y copias dedicadas; las demás con menos | Igual |
| **Streams** | Todos los cambios pasan por el mismo flujo | Un flujo por tabla con su propia Lambda (solo `bya_seats` alimenta historial y mapa) | Igual |
| **Mínimo privilegio** (Samuel) | Una política por rol con condiciones de clave complejas | Políticas por tabla: el rol de soporte no ve `bya_orders` completo | Igual |
| **Clase de tabla** (Standard-IA para historial/auditoría/escaneos) | Se pierde el ahorro por mezclar datos fríos y calientes [R-06] | Aplicable tabla por tabla | Igual |
| **Operación** (alarmas, capacidad) | Menos objetos | 8 conjuntos de alarmas | Más objetos |
| **Consultas conjuntas** (orden + pagos + factura) | Una consulta | Se resuelve con la **colección de ítems de la orden** (`ORD#<oid>` con `ORDER`, `PAY#n`, `INV`) en una sola tabla | Varias lecturas y uniones en la aplicación |

**Conclusión.** No uso tabla única por defecto. Uso **single-table solo donde hay un agregado coherente** (la orden con sus pagos y su referencia de factura; el catálogo con sus localidades; la boleta con sus escaneos) y separo lo que difiere en calor, retención o riesgo. Lo que se sacrifica: no hay `JOIN` entre tablas (DynamoDB no lo ofrece [R-01]); la aplicación resuelve con `BatchGetItem` o con listas de IDs guardadas en el ítem padre.

---

## 3. Las 8 tablas

Atributos con nombres cortos para reducir bytes: **el nombre del atributo cuenta en el tamaño del ítem** (límite 400 KB; el tamaño de un ítem es la suma de nombres y valores) [R-07]. Tiempos en **segundos de época** (tipo Number) para que el TTL pueda usarlos [R-08].

### 3.1 `bya_catalog` — eventos y localidades

| Elemento | Valor |
|---|---|
| **PK / SK** | `pk = EVT#<eid>` · `sk = META` \| `SEC#<sid>` |
| Atributos de `META` | `tit` (título), `org` (organizador), `ini` (inicio, epoch), `est` (estado: DRAFT/ON_SALE/CLOSED/CANCELLED), `ven` (recinto), `gs1pk`, `gs1sk` |
| Atributos de `SEC#` | `nom`, `cap` (capacidad), `pre` (precio en centavos COP), `fil` (número de filas), `nsh` (**fragmentos del contador**, por defecto 8), `pue` (**puerta de acceso asignada**, la usa el servidor del estadio: `david/estadio.md` §4), `est` |
| **GSI `gsi_organizador`** | PK `ORG#<org>` · SK `<ini>#EVT#<eid>` · proyección `INCLUDE (tit, est)` |
| Calor | Bajo (lectura masiva servida por CDN). Cambios de precio o cupo = escritura transaccional con **auditoría** en la misma transacción (ver §6.3). |

Ejemplo (evento + localidad):

```json
{ "pk": "EVT#1234", "sk": "META", "tit": "Concierto X - Estadio Y", "org": "ORG#77",
  "ini": 1793059200, "est": "ON_SALE", "ven": "VEN#12", "gs1pk": "ORG#77", "gs1sk": "1793059200#EVT#1234" }
{ "pk": "EVT#1234", "sk": "SEC#07", "nom": "Oriental Baja", "cap": 2250, "pre": 18000000,
  "fil": 45, "nsh": 8, "pue": "P3", "est": "ON_SALE" }
```

Consulta AP-01 (una sola llamada trae el evento y todas sus localidades):

```json
{ "TableName": "bya_catalog", "KeyConditionExpression": "pk = :p", "ExpressionAttributeValues": { ":p": {"S": "EVT#1234"} } }
```

### 3.2 `bya_seats` — estado de cada silla (tabla caliente)

| Elemento | Valor |
|---|---|
| **PK / SK** | `pk = E<eid>#S<sid>#R<fila>` · `sk = S<nro>` (p. ej. `E1234#S07#R12` / `S023`) |
| Atributos | `st` = `A` (disponible) \| `L` (bloqueada) \| `S` (vendida) · `lx` = bloqueo vence en (epoch s) · `lo` = dueño del bloqueo (`oid`) · `so` = orden que la vendió · `tk` = `tid` de la boleta · `v` = versión (entero, +1 en cada cambio) · `ttl` = limpieza (evento + 90 días) |
| **GSI** | **Ninguno** (decisión D2) |
| **Streams** | Sí, `NEW_AND_OLD_IMAGES` → historial (D5) y actualización del mapa (§6 de arquitectura) |
| Calor | El más alto. Reparto por fila (≈ 900 claves de partición en un estadio de 45.000 sillas, ≈ 50 sillas por fila); ver §4 |

Una silla disponible pesa ≈ 55 B y una vendida ≈ 100 B con los nombres cortos, consistente con los 100 B `DATO` del enunciado. Para zonas sin numeración ("general"), se crean **filas virtuales de ≤ 50 cupos** (`R<bloque>`), de modo que el modelo sea el mismo (**SUPUESTO A-08**).

Ejemplos:

```json
{ "pk": "E1234#S07#R12", "sk": "S023", "st": "A", "v": 0 }
{ "pk": "E1234#S07#R12", "sk": "S024", "st": "L", "lx": 1793000480, "lo": "01JC3...ORD", "v": 1 }
{ "pk": "E1234#S07#R12", "sk": "S025", "st": "S", "so": "01JC3...ORD", "tk": "01JC3...TKT", "v": 2 }
```

Consulta AP-02 (una fila; la repite el constructor del mapa, no los usuarios):

```json
{ "TableName": "bya_seats", "KeyConditionExpression": "pk = :p", "ExpressionAttributeValues": { ":p": {"S": "E1234#S07#R12"} } }
```

Costo: ≈ 50 sillas × 100 B = 5 KB → 2 unidades de 4 KB → **1 RRU** con lectura eventual (2 × 0,5). Estadio completo: 900 filas ≈ 900 RRU por refresco.

### 3.3 `bya_counters` — contadores por localidad y límites por usuario

| Elemento | Valor |
|---|---|
| **PK / SK (contador)** | `pk = CNT#E<eid>#S<sid>` · `sk = SH#<00..N-1>` |
| Atributos | `sold` (Number, boletas vendidas en el fragmento), `ts` (última actualización) |
| **PK / SK (límite antibot)** | `pk = LIM#E<eid>#U<uid>` · `sk = P` · atributos `n` (boletas retenidas + compradas), `ttl` |
| Fragmento de una venta | `sh = hash(oid) mod N` (**sufijo calculado**: un reintento de la misma orden cae siempre en el mismo fragmento) [R-10] |
| **GSI** | Ninguno |
| Calor | Alto pero repartido: ver §5 |

```json
{ "pk": "CNT#E1234#S07", "sk": "SH#03", "sold": 211, "ts": 1793000500 }
{ "pk": "LIM#E1234#U01JA...", "sk": "P", "n": 4, "ttl": 1793600000 }
```

### 3.4 `bya_orders` — la orden y todo lo que cuelga de ella

| Elemento | Valor |
|---|---|
| **PK / SK** | `pk = ORD#<oid>` (ULID generado por el cliente/BFF; **es la llave de idempotencia de la compra**) · `sk` = `ORDER` \| `PAY#<nn>` \| `INV#1` |
| `ORDER` (≈ 2 KB `DATO`) | `uid`, `eid`, `st` (PENDING/PAID/EXPIRED/CANCELLED/FULFILL_FAIL/REFUNDING/REFUNDED), `lx` (vence el bloqueo), `sil` (lista de sillas con precio), `tot`, `tkt` (lista de `tid`), `cre`, `idem` (token de cliente), `ttl` (mientras `PENDING` = `lx` + 1 día; **al pagar se reemplaza** por el valor largo de retención), `g1pk`/`g1sk`, `g2pk`/`g2sk` |
| `PAY#nn` (≈ 1,5 KB `DATO`) | `n`, `idem` = `<oid>#<nn>` (llave de idempotencia ante la pasarela), `gtk` (**token** de la pasarela; **nunca** tarjeta), `gtx` (id de transacción de la pasarela), `st` (INITIATED/APPROVED/DECLINED/UNKNOWN), `cod`, `amt`, `cre`, `upd`, `g3pk`/`g3sk` (solo mientras esté pendiente) |
| `INV#1` (≈ 500 B `DATO`) | `st` (PENDING/ISSUED/REJECTED), `cufe`, `prov` (referencia del proveedor tecnológico), `cre`, `upd`, `g3pk`/`g3sk` (solo mientras esté pendiente) |
| **GSI `gsi_usuario`** | PK `g1pk = USR#<uid>` · SK `g1sk = <cre>#<oid>` · `INCLUDE (st, tot, eid)` (solo ítems `ORDER`) |
| **GSI `gsi_evento_orden`** | PK `g2pk = EVT#<eid>#<n>` con `n = hash(oid) mod 8` · SK `g2sk = <cre>#<oid>` · `INCLUDE (st, tot, uid)` (solo ítems `ORDER`) |
| **GSI `gsi_pendientes`** (dispersa) | PK `g3pk = PEND#<PAY\|INV>#<n>` con `n = hash(oid) mod 4` · SK `g3sk = <cre>#<oid>#<ref>` · `KEYS_ONLY` — solo existe mientras el pago o la factura estén sin resolver |
| TTL | **Un solo atributo TTL por tabla: `ttl`** (DynamoDB admite uno por tabla). `PAY` e `INV`: creación + 2 años + 60 días de gracia (A-04, **sujeto a validación legal**). `ORDER`: mientras `PENDING` = `lx` + 1 día (limpia abandonadas); al pagar, la transacción de confirmación lo **cambia** al valor largo |

Ejemplo (colección de la orden):

```json
{ "pk": "ORD#01JC3A", "sk": "ORDER", "uid": "01JA9X", "eid": "1234", "st": "PAID", "lx": 1793000480,
  "sil": [{"k":"E1234#S07#R12|S024","p":18000000},{"k":"E1234#S07#R12|S025","p":18000000}], "tot": 36000000,
  "tkt": ["01JC3B","01JC3C"], "cre": 1793000000, "idem": "c0ffee...", "g1pk": "USR#01JA9X", "g1sk": "1793000000#01JC3A",
  "g2pk": "EVT#1234#5", "g2sk": "1793000000#01JC3A", "ttl": 1856000000 }
{ "pk": "ORD#01JC3A", "sk": "PAY#01", "n": 1, "idem": "01JC3A#01", "gtk": "tok_9f...", "gtx": "gw-778", "st": "APPROVED", "amt": 36000000, "cre": 1793000100, "upd": 1793000102, "ttl": 1856000000 }
{ "pk": "ORD#01JC3A", "sk": "INV#1", "st": "PENDING", "cre": 1793000102, "g3pk": "PEND#INV#2", "g3sk": "1793000102#01JC3A#INV", "ttl": 1856000000 }
```

Consultas:

```json
// AP-07: órdenes del usuario, más recientes primero
{ "TableName": "bya_orders", "IndexName": "gsi_usuario", "KeyConditionExpression": "g1pk = :u", "ScanIndexForward": false, "Limit": 20, "ExpressionAttributeValues": { ":u": {"S": "USR#01JA9X"} } }
// AP-13: ventas de un evento cancelado (repetir para n = 0..7 en paralelo)
{ "TableName": "bya_orders", "IndexName": "gsi_evento_orden", "KeyConditionExpression": "g2pk = :e", "FilterExpression": "st = :p", "ExpressionAttributeValues": { ":e": {"S": "EVT#1234#5"}, ":p": {"S": "PAID"} } }
// AP-17: pagos sin resolver hace más de 5 minutos (cada fragmento)
{ "TableName": "bya_orders", "IndexName": "gsi_pendientes", "KeyConditionExpression": "g3pk = :k AND g3sk < :t", "ExpressionAttributeValues": { ":k": {"S": "PEND#PAY#1"}, ":t": {"S": "1793000200"} } }
```

### 3.5 `bya_tickets` — boletas y escaneos

| Elemento | Valor |
|---|---|
| **PK / SK** | `pk = TKT#<tid>` · `sk = T` (la boleta) \| `SCAN#<ts>#<puerta>` (intentos de ingreso) |
| `T` (≈ 1 KB `DATO`) | `oid`, `eid`, `sid`, `sil` (`E1234#S07#R12\|S024`), `st` (VALID/USED/VOID), `qrh` (huella HMAC del QR), `usa` (cuándo se usó), `pta` (puerta), `ver`, `g4pk`, `g4sk`, `ttl` |
| `SCAN#…` (≈ 250 B `DATO`) | `res` (OK/DUPLICADA/INVALIDA), `pta`, `dis` (dispositivo), `off` (true si vino del servidor local), `ttl` |
| **Streams** | **Sí** (pedido de David para el estadio, `david/estadio.md` §4): vista `NEW_AND_OLD_IMAGES`; Lambda con **filtro de eventos** que solo deja pasar altas de boleta (`sk = T`) y cambios a `VOID`, y los envía a una cola SQS por evento que consulta el servidor central; los escaneos (`USED`, `SCAN#…`) no se reenvían. Retención del *stream*: 24 h [R-11] → el central debe consumir antes; si falla, se rehace con `gsi_evento_boleta` (AP-18) |
| **GSI `gsi_evento_boleta`** | PK `g4pk = EVT#<eid>#<n>` con `n = hash(tid) mod 8` · SK `g4sk = TKT#<tid>` · `INCLUDE (st, sil, qrh)` |
| `tid` | **Determinista**: `UUIDv5(oid, clave de silla)`. Un reintento de la confirmación no puede crear una boleta distinta para la misma silla. |
| QR | `v1.<tid>.<eid>.<hmac>`: lleva `tid`, así la validación en línea es un `GetItem` sin índice. El HMAC permite al servidor local rechazar QR falsos sin internet. |
| TTL | Atributo `ttl`: la boleta (`sk = T`) 2 años + 60 d; los escaneos (`sk = SCAN#…`) **1 año** (A-04). |

Doble uso (AP-09 + AP-10 en una transacción de 2 ítems):

```json
{ "Update": { "TableName": "bya_tickets", "Key": {"pk":{"S":"TKT#01JC3B"},"sk":{"S":"T"}},
    "UpdateExpression": "SET st = :u, usa = :now, pta = :g, ver = ver + :one",
    "ConditionExpression": "st = :v AND eid = :eid",
    "ExpressionAttributeValues": {":u":{"S":"USED"},":v":{"S":"VALID"},":now":{"N":"1793400000"},":g":{"S":"P3"},":eid":{"S":"1234"},":one":{"N":"1"}} } },
{ "Put": { "TableName": "bya_tickets", "Item": {"pk":{"S":"TKT#01JC3B"},"sk":{"S":"SCAN#1793400000#P3"},"res":{"S":"OK"},"pta":{"S":"P3"}} } }
```

### 3.6 `bya_seat_history` — historial de cambios de estado

| Elemento | Valor |
|---|---|
| **PK / SK** | `pk = E<eid>#S<sid>#R<fila>#<nro>` · `sk = V#<v con 8 dígitos>` |
| Atributos (≈ 150 B `DATO`) | `de`, `a` (estado anterior y nuevo), `lo`/`so` (orden), `ts`, `ev` (origen: `LOCK`, `SOLD`, `ADMIN`, `EXPIRED_TAKEOVER`) |
| Escritura | **Función Lambda sobre el stream de `bya_seats`**: para cada registro con `NewImage.v ≠ OldImage.v`, `PutItem` con la clave `(silla, v)`. Si Lambda reintenta, **sobreescribe el mismo ítem** (idempotente). El orden por ítem lo garantiza DynamoDB Streams [R-11]. |
| Clase de tabla | **Standard-IA**: pensada para tablas donde el almacenamiento es el costo dominante (historiales, registros) [R-24]; todos los GSI usan la clase de la tabla |
| TTL | 2 años (A-04) |

Por qué por Streams y no dentro de la transacción: (a) evita duplicar los ítems de la transacción (cada ítem cuesta el doble) y los conflictos; (b) la **fuente de verdad** es el estado de la silla, el historial es derivado. **Costo del sacrificio:** el historial puede quedar atrasado segundos y, si el consumidor falla más de 24 h, **se pierde** el registro del stream [R-11] (mitigación: DLQ en el *event source mapping*, alarma de edad del iterador y reconstrucción desde exportaciones incrementales de `bya_seats`, que traen `OldImage`/`NewImage` [R-09]). Los cambios **administrativos** de sillas se auditan de forma **síncrona** en `bya_audit` dentro de la misma transacción (§6.3).

### 3.7 `bya_audit` — auditoría

| Elemento | Valor |
|---|---|
| **PK / SK** | `pk = ENT#<tipo>#<id>` (p. ej. `ENT#SEC#1234#07`, `ENT#ORD#01JC3A`) · `sk = <ts ISO>#<ulid>` |
| Atributos (≈ 300 B `DATO`) | `act` (acción), `ator` + `tip` (HUMAN/SYSTEM), `ant`/`des` (antes/después, resumidos o con huella), `req` (id de solicitud), `ttl` |
| **GSI `gsi_actor`** (**dispersa**) | PK `g5pk = ACT#<ator>` · SK `g5sk = <ts>#<ulid>` · solo ítems con `tip = HUMAN` (A-07: ≈ 5 %). Los actores de sistema **no** se indexan (serían una clave caliente). |
| Clase de tabla | **Standard-IA** |
| TTL | 2 años en línea (A-04); después, solo en S3 con retención legal (Samuel) |
| Qué no resuelve | La auditoría de **control** (quién cambió una tabla o un rol) viene de CloudTrail; Streams no trae la identidad de la persona (Samuel integra ambas). |

### 3.8 `bya_users` — usuarios

| Elemento | Valor |
|---|---|
| **PK / SK** | `pk = USR#<uid>` · `sk = P` |
| Atributos (≈ 1,5 KB `DATO`) | `em_h` (SHA-256 del correo normalizado), `em_c` (correo cifrado), `tel_c`, `doc_t`/`doc_c` (tipo y cédula cifradas), `nom`, `cre`, `cons` (consentimiento Ley 1581, versión y fecha), `est` |
| **GSI `gsi_email`** | PK `g6pk = EM#<em_h>` · SK `USR#<uid>` · `KEYS_ONLY` |
| Protección (Samuel) | Cifrar los campos sensibles del lado del cliente antes de escribir (la guía de DynamoDB menciona el AWS Database Encryption SDK para cifrado del lado del cliente [R-01]); el correo en claro **no** es clave de índice. |
| TTL | No (supresión por solicitud del titular: proceso de Samuel) |

---

### 3.9 `bya_ledger` — libro de pagos (**OPCIONAL**: plan B de la decisión D-2)

**Para qué existe.** Miguel y David aceptaron D-2 (una sola región escribe; tras perder la región, modo seguro con conciliación contra la pasarela) **con dos condiciones**: (1) tras perder la región, la lista de sillas de un pago aprobado vive en `ORDER.sil`, que puede no haberse replicado en el último segundo, y la pasarela solo conoce `<oid>#<nn>` y el monto; (2) la conciliación de desastre no puede partir de `gsi_pendientes`. La condición (2) se resuelve en el proceso (modo desastre parte de la lista de transacciones aprobadas de la pasarela y lee la réplica con lectura fuerte: `miguel/respuesta_a_david.md` §3). La condición (1) tiene dos opciones:

| Opción | Qué es | Dependencia |
|---|---|---|
| **A (principal)** | Enviar a la pasarela el evento y las sillas como **metadato del cobro** | Que la pasarela elegida lo permita y permita **listar transacciones por rango de fechas** (**PENDIENTE**: elegir pasarela entre Miguel, David y yo) |
| **B (plan B, esta tabla)** | Escribir un **libro mínimo** en una tabla global **MRSC**, antes de cobrar | Costo y latencia (abajo) |

**Diseño de la opción B** (solo si A no es viable):

| Elemento | Valor |
|---|---|
| **PK / SK** | `pk = LED#<oid>` · `sk = P` |
| Atributos | `eid`, `uid`, `sil` (claves de las sillas), `amt`, `nn` (n.º de intento), `st` (INTENT / CHARGED / VOID), `cre` |
| Escritura | `PutItem` **condicional** (`attribute_not_exists(pk)`), **sin transacción**, **antes** de llamar a la pasarela; el paso de INTENT a CHARGED es un `UpdateItem` condicional |
| Consistencia | **MRSC**: la escritura se replica de forma sincrónica a otra región antes de responder, y una lectura fuerte en cualquier réplica devuelve lo último → **RPO 0** para este dato [R-17] |
| Restricciones de MRSC que condicionan | **Exactamente tres regiones** (dos réplicas + un testigo, p. ej. us-east-1, us-east-2 y testigo en una tercera de la lista oficial); **sin transacciones, sin TTL, sin LSI**; solo se crea sobre una tabla **vacía** y no admite agregar réplicas después [R-17] → la limpieza se hace por exportación + borrado de la aplicación |
| Costo en rendimiento | Una escritura **más** en el camino del pago (≈ 24.000 por preventa grande) y su latencia **depende de la distancia entre regiones**; **no la medí** (**PENDIENTE**). Costo en USD: Juan Pablo |
| GSI | Ninguno |

**Decisión que falta (D-2b, grupo):** elegir la pasarela; si no admite metadato ni listado por fechas, se activa esta tabla. Hasta entonces **no se incluye en el costo base**.

---

## 4. Evitar particiones calientes

**Límites que mandan** [R-12, R-19]: cada partición entrega como máximo **3.000 RCU/s y 1.000 WCU/s**; esto aplica también a un único ítem (un ítem vive en una partición). La *adaptive capacity* aísla ítems muy usados, **sin superar** esos máximos. Una tabla on-demand nueva sostiene **4.000 escrituras/s y 12.000 lecturas/s** y acepta de inmediato hasta **el doble de su pico previo**; superar el doble dentro de 30 minutos puede causar *throttling* [R-13].

### 4.1 Alternativas para la clave de partición de `bya_seats`

| Opción | Reparto | Lectura de una localidad | ¿Aguanta el pico? (planificación ×5 = **2.214 WRU/s** en sillas; estrés ×5 = 5.500) | Veredicto |
|---|---|---|---|---|
| a) `pk = evento` | Una sola clave por evento | Una consulta | **No**: 2.214 > 1.000 por partición | ✗ |
| b) `pk = evento#localidad` | ≈ 20 claves | Una consulta por localidad | Si una localidad popular concentrara ~40 % (supuesto) ≈ 885 WRU/s, **sin margen** frente a 1.000 | ✗ |
| c) **`pk = evento#localidad#fila`** | ≈ 900 claves en un estadio | Una consulta por fila (≈ 1 RRU) | Carga media por clave ≈ 2,5 WRU/s; el máximo no se acerca a 1.000 | ✓ **elegida** |
| d) `pk = evento#(hash(silla) mod 64)` | Uniforme | 64 consultas por localidad (*scatter-gather*) [R-10] | Sí | Más uniforme pero pierde localidad; no hace falta |

**Beneficio de (c):** reparto natural, sillas contiguas (compras de 2–3 boletas) en la misma colección de ítems, y la lectura del mapa por fila es barata. **Sacrificio:** leer una localidad completa = una consulta por fila (45–100 consultas) → por eso esa lectura la hace **un solo constructor** que publica instantáneas, no los 250.000 usuarios.

### 4.2 El ítem más caliente de todos: una silla "de primera fila"

Una silla es un ítem: su techo es **1.000 WRU/s = 500 transacciones/s** (2 WRU por ítem en una transacción [R-04]). Cada intento fallido **consume capacidad igual** que uno exitoso [R-04]. Mitigaciones (por capas):

1. **Cola virtual** admite solo C compradores simultáneos (Little: 20 órdenes/s × 240 s = 4.800 en promedio; ×5 = 24.000).
2. **Pista negativa en caché** (`ElastiCache`): si el mapa en vivo ya dice "vendida", la API **no** lanza la transacción. Si la caché dice "disponible", **igual** se lanza (la caché puede equivocarse a favor del rechazo, nunca a favor de la venta).
3. **Límite por usuario** (`bya_counters`, `LIM#…`): una escritura condicional por intento.
4. **Reintentos con *backoff* exponencial y *jitter*** ante `TransactionCanceledException` por `TransactionConflict`: los SDK **no** reintentan esa excepción [R-04].
5. **Pre-calentamiento** (`warm throughput`) de `bya_seats` antes de la preventa [R-18].

### 4.3 Qué se escala y cómo

* **Tablas y GSI se pre-calientan por separado** (la documentación lo permite para tablas, tablas globales y GSI [R-18]). Un GSI con menos capacidad que la tabla base **frena las escrituras de la tabla** [R-03]: se pre-calienta `gsi_usuario`/`gsi_evento_orden`/`gsi_pendientes` al nivel de `bya_orders`.
* **Las réplicas heredan el pre-calentamiento.** Para las tablas globales de la versión actual, la documentación dice que el `warm throughput` que se fija "se aplica automáticamente a todas las réplicas" [R-18]. Por eso la réplica de us-east-2 (hallazgo de David, `alta_disponibilidad.md` §7) se pre-calienta **al mismo nivel** que la principal con la misma operación. **PENDIENTE:** si el cargo único se cobra una vez por región (Juan Pablo) y cuánto tarda.
* Dimensionamiento por tabla en la ráfaga ×5 (planificación / estrés), de la tabla T5c de capacidad: sillas 2.214 / 5.500 · órdenes 2.791 / 5.660 · límites 686 / 2.000 · contadores 200 / 200 · boletas 500 / 1.000.

---

## 5. Contador exacto por localidad (el punto crítico)

**Requisito `DATO`:** "contador exacto, no aproximado, de boletas vendidas por localidad, actualizado con cada venta; miles de compras por minuto actualizan las mismas pocas localidades".

### 5.1 Distinguir dos cosas

* **Exactitud del dato:** el valor almacenado es igual al número de sillas vendidas en esa localidad, sin pérdidas ni duplicados.
* **Frescura de la lectura:** cuánto tarda un lector en ver la última venta.

Una cifra puede ser **exacta y estar desactualizada** (la caché de ayer) o **fresca y no exacta** (suma con un aproximado). Lo que el enunciado exige —"exacto" y "con cada venta"— se cumple **escribiendo el contador en la misma transacción** que la venta y **leyéndolo con lectura fuerte**. Lo que ninguna arquitectura da gratis es leer un solo valor atómico si el contador está fragmentado.

### 5.2 Las tres opciones

| | **1. Contador único, transaccional** | **2. Fragmentado dentro de la transacción (recomendada)** | **3. Derivado con Streams** |
|---|---|---|---|
| Mecanismo | `Update sold = sold + :n` de un ítem por localidad dentro de la transacción de confirmación | Igual, pero sobre `SH#(hash(oid) mod N)`; el total es la suma de N ítems | Un consumidor del stream de `bya_seats` suma las sillas que pasan a `S` y actualiza el contador |
| **Garantía de exactitud** | Exacto y atómico con la venta | **Exacto y atómico con la venta**: cada fragmento cambia en la misma transacción que la silla | Exacto **al converger**; no atómico con la venta |
| ¿Se actualiza "con cada venta"? | Sí, dentro de la venta | Sí, dentro de la venta | No: con retraso (segundos; el retraso no está garantizado por la documentación) |
| **Contención** | Todas las confirmaciones de la localidad tocan **un** ítem. Una transacción que choca con otra **se cancela** (`TransactionConflict`), no espera [R-04] | Se reparte entre N ítems; la probabilidad de choque cae ~N veces | Ninguna sobre el ítem durante la venta; la contención pasa al consumidor |
| **Límite duro** | 1.000 WRU/s por ítem = 500 transacciones/s | N × 500 transacciones/s | Rendimiento del consumidor y del ítem agregado |
| Fallo a mitad | La transacción es atómica: o se vende y se cuenta, o ninguna | Igual | El stream retiene 24 h; Lambda reintenta; **riesgo de doble conteo** si no hay deduplicación [R-11] |
| Cómo se evita contar dos veces | La venta y el contador son una sola transacción; reintento con el mismo `ClientRequestToken` (10 min) o fallo de condición `st = L AND lo = :oid` | Igual + el fragmento es determinista por `oid` | Marca de procesado `(silla, v)` con escritura condicional en la **misma** transacción que el incremento |
| Lectura exacta | `GetItem` fuerte (1 RRU) | N lecturas: `BatchGetItem` fuerte (N RRU; cada ítem es consistente, no el conjunto) o `TransactGetItems` (2N RRU, instantánea serializable) | `GetItem` fuerte del agregado |
| Costo/complejidad | Mínimo | Bajo: N ítems pequeños, lectura de N ítems | Medio-alto: consumidor idempotente, reproceso |

### 5.3 Qué demuestran los números (y qué no)

* A la carga **del enunciado**, el contador **único no excede el límite físico**: ráfaga ×5 = 100 órdenes/s × 2 WRU = **200 WRU/s** < 1.000 (T10b de capacidad). **No afirmo que N=1 sature por rendimiento.**
* El riesgo real es la **cancelación por choque de transacciones** sobre un mismo ítem, cuya frecuencia **no está documentada** y yo **no la medí** (el enunciado prohíbe montar pruebas). La tabla T10 de capacidad es un **modelo ilustrativo** con el tiempo de retención T como supuesto; sirve para elegir N de forma proporcional, no como resultado experimental.
* Por eso se **fragmenta de todos modos** (N=8 por defecto, guardado en `SEC#`.`nsh` y ajustable por localidad hasta 32 sin rediseñar claves): es barato (8 ítems de ≈ 100 B), conserva la atomicidad y reduce el choque ~8 veces.

### 5.4 Recomendación y conflicto expuesto

**Recomendación:** opción 2 para el contador oficial; opción 3 solo para analítica derivada (tableros históricos, conciliación), nunca como el número exacto del organizador.

**Conflicto exactitud inmediata ↔ escalado horizontal.** Fragmentar convierte "leer el contador" en "sumar N ítems". Con `BatchGetItem` fuerte cada fragmento es el último valor confirmado, pero la **suma** puede no corresponder a un único instante: una venta que se confirma mientras se leen los N ítems puede quedar contada en unos y no en otros (nunca contada dos veces ni parcialmente, porque cada venta toca un solo fragmento). Con `TransactGetItems` la lectura es una **instantánea serializable** [R-04], a costa de 2N RRU y de poder cancelarse si choca con una venta en curso. **Solución justificable:** tablero en vivo con `BatchGetItem` fuerte (exacto respecto a toda venta terminada antes de iniciar la lectura); cierre, liquidación y auditoría con `TransactGetItems` y, además, **conciliación** periódica (contar sillas `S` por consulta de filas vs. suma de fragmentos: debe dar diferencia 0). No afirmo que una sola lectura barata dé a la vez "instante único" y "máxima frescura": hay que elegir el modo por caso de uso.

### 5.5 Recuperación de una actualización fallida

No existe una "actualización del contador" independiente que pueda fallar sola: está **dentro** de `TransactWriteItems`; si cualquier condición falla, **nada** cambia [R-04]. Casos:

1. **Timeout sin respuesta:** el cliente repite con el **mismo** `ClientRequestToken` (válido 10 min tras terminar la primera): si la primera tuvo éxito, devuelve éxito sin cambios [R-04].
2. **Reintento tras 10 min:** la condición `st = 'L' AND lo = :oid` ya no se cumple (la silla es `S`) → falla; la aplicación **lee la orden** (lectura fuerte): si está `PAID`, es éxito. La idempotencia no depende solo de la ventana de 10 min.
3. **Caída del servidor de aplicación:** el estado de la compra vive en `bya_orders` (`PENDING`, `PAY#` pendiente en `gsi_pendientes`); el reconciliador reanuda.

---

## 6. Historial, auditoría, escaneos, TTL y datos fríos

### 6.1 Política de TTL (todo **SUPUESTO A-04, sujeto a validación legal de Samuel y Miguel**)

| Tabla | Atributo | Cuándo expira | Lo que hace el TTL | Lo que **no** hace |
|---|---|---|---|---|
| `bya_seats` | `ttl` | evento + 90 días | Limpia sillas viejas | **No decide** la disponibilidad: la condición usa `lx` |
| `bya_orders` (`ORDER` en `PENDING`) | `ttl` | `lx` + 1 día; al pagar se **reemplaza** por el valor largo | Borra órdenes abandonadas | No libera sillas |
| `bya_orders` (`ORDER/PAY/INV`) | `ttl` | creación + 2 años + 60 d (en `ORDER` pendiente: `lx` + 1 día hasta pagar) | Saca de línea lo ya exportado | No sustituye la retención legal (queda en S3) |
| `bya_tickets` | `ttl` | boleta: 2 años + 60 d · escaneos: 1 año | Idem | — |
| `bya_seat_history`, `bya_audit` | `ttl` | 2 años | Idem | — |
| `bya_counters` (`LIM#`) | `ttl` | fin del evento + 7 d | Limpia límites | — |

**Comportamiento verificado del TTL** [R-08]: borra "típicamente en pocos días" tras expirar, **sin consumir WCU**; los ítems vencidos **siguen apareciendo** en lecturas hasta su borrado (la aplicación filtra con `FilterExpression`); los borrados llegan a Streams como borrados del servicio. En tablas globales, el borrado se replica y **sí** consume escritura replicada en las demás regiones. `UpdateTimeToLive` admite un cambio por tabla por hora.

### 6.2 Exportación histórica a S3 y consulta con Athena

1. **PITR activado** en las tablas con archivo (requisito de las exportaciones) [R-09].
2. **Exportación incremental diaria** (ventana mínima 15 min, máxima 24 h [R-14]) con vista `NEW_AND_OLD_IMAGES`, formato DynamoDB JSON, prefijo `s3://bya-archivo/<tabla>/dt=AAAA-MM-DD/`. Cada registro trae `Metadata.WriteTimestampMicros`, `Keys`, `NewImage`, `OldImage` [R-15]. No consume RCU ni afecta la tabla [R-09].
3. **Una exportación completa por año** (línea base y verificación: `itemCount` del `manifest-summary.json` vs. conteo esperado).
4. **TTL como último paso:** cada ítem ya fue capturado por las exportaciones diarias de los 2 años previos y los 60 días de gracia dan margen a corregir una exportación fallida. Alarma si falta el `manifest` de un día.
5. **Athena** (catálogo Glue) sobre las carpetas `dt=…` (Athena lee los archivos comprimidos de la exportación en DynamoDB JSON o Ion [R-37]); para obtener "el último estado de cada ítem" se usa `ROW_NUMBER()` por `(pk, sk)` ordenado por `WriteTimestampMicros`.
6. **Copia legal**: bucket S3 con versionado y **Object Lock** (retención sujeta a Samuel/Miguel).

Ejemplo ilustrativo de definición y consulta (**no ejecutado**: el enunciado prohíbe crear recursos; validar en la consola de Athena):

```sql
CREATE EXTERNAL TABLE bya_orders_cdc (
  Metadata struct<WriteTimestampMicros:struct<N:string>>,
  Keys     struct<pk:struct<S:string>, sk:struct<S:string>>,
  NewImage struct<pk:struct<S:string>, sk:struct<S:string>, uid:struct<S:string>,
                  eid:struct<S:string>, st:struct<S:string>, tot:struct<N:string>, cre:struct<N:string>>
) PARTITIONED BY (dt string)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://bya-archivo/bya_orders/';

-- Reclamo: todas las órdenes pagadas de un evento, con su último estado
SELECT * FROM (
  SELECT NewImage.pk.S AS orden, NewImage.st.S AS estado, NewImage.tot.N AS total,
         ROW_NUMBER() OVER (PARTITION BY NewImage.pk.S ORDER BY CAST(Metadata.WriteTimestampMicros.N AS bigint) DESC) AS rn
  FROM bya_orders_cdc WHERE NewImage.eid.S = '1234' AND NewImage.sk.S = 'ORDER'
) WHERE rn = 1 AND estado = 'PAID';
```

Costo de una consulta que recorra **todo** el archivo del año 5 (≈ 131 GiB crudos ≈ 0,13 TB, sin considerar compresión ni poda de particiones): ≈ USD 0,64 con precio de Athena en us-east-1 (USD 5/TB) o USD 1,15 en sa-east-1 (USD 9/TB), de la lista oficial 2026-10-29 [R-16].

### 6.3 Auditoría síncrona de cambios administrativos

Los cambios de **precio, cupo o estado de silla hechos por personas** se hacen con `TransactWriteItems`: `Update` del ítem afectado **+** `Put` en `bya_audit` (`tip = HUMAN`). Así no puede haber cambio sin rastro. Los cambios automáticos de sillas por compra no se auditan aquí: tienen su historia en `bya_seat_history`.

### 6.4 Qué **no** vuelve al restaurar una tabla (para los simulacros de Miguel)

Una restauración (PITR o respaldo) **crea una tabla nueva** [R-42]; puede recuperarse **hasta cinco minutos antes de la hora actual** y hasta el período configurado (1–35 días) [R-42], y la restauración no consume capacidad de la tabla [R-41]. **Pero no copia**, y hay que **reaplicar a mano** [R-41]:

| No se restaura | Efecto en este modelo | Qué se reaplica |
|---|---|---|
| **Streams** | Se pierde el historial de sillas, el mapa vivo y el envío al estadio (`bya_tickets`) | Activar Streams `NEW_AND_OLD_IMAGES` en `bya_seats` y `bya_tickets`; volver a crear los *event source mappings* (Lambda, DLQ) |
| **TTL** | No se limpian sillas, órdenes abandonadas ni escaneos; los vencidos se acumulan | Habilitar TTL con el atributo `ttl` (un cambio por tabla por hora [R-07]) |
| Políticas de **escalado** y capacidad programada | Sin `warm throughput` ni límites | Re-pre-calentar tablas y GSI; reponer el máximo de throughput |
| Políticas **IAM** | Mínimo privilegio roto o inexistente | Reaplicar las políticas por tabla (Samuel) |
| **Alarmas** y Contributor Insights | Sin alertas (edad del iterador de Streams, *throttling*) | Reponer alarmas |
| **Etiquetas** (y las condiciones basadas en ellas) | Fallan permisos por etiqueta | Reponer etiquetas |
| **Protección contra borrado** y **PITR** | La tabla restaurada no queda protegida ni respaldada | Activarlas de inmediato |

Los **GSI se pueden excluir** de la restauración para que sea más rápida y barata, y se crean después [R-41] (todos los de este modelo se reconstruyen desde la tabla). En una tabla global, el respaldo de una réplica se restaura como **tabla independiente**, no como réplica; hay que crear de nuevo la tabla global [R-42].

---

## 7. Interfaz con David: estructura de la transacción de compra

> David diseña y analiza la concurrencia; aquí solo está lo necesario para que las claves **no se rediseñen**. Todo el pseudocódigo usa los nombres de este documento.

### 7.1 Fase 1 — Bloqueo (`TransactWriteItems`, `ClientRequestToken = H(oid,"LOCK")`)

Para cada silla `k` de la compra (máximo **10 sillas por orden**, política de negocio A-09: la transacción permite hasta 100 ítems/4 MB [R-04], el bloqueo usa `n + 2` ítems):

```text
-- La aplicación calcula :lx = now + 480 y :vencido_antes_de = now - skew ANTES de llamar a DynamoDB:
-- una ConditionExpression no admite aritmética (corrección de David, respuesta_a_jacobo.md §3).
Update bya_seats  Key(pk,sk) de la silla
  SET st='L', lx=:lx, lo=:oid, v=v+1
  IF  attribute_exists(pk) AND ( st='A' OR (st='L' AND lx < :vencido_antes_de) )   -- vencido = disponible
Put    bya_orders ORD#<oid>/ORDER  (st='PENDING', lx=:lx, ttl, idem, ...)   IF attribute_not_exists(pk)
Update bya_counters LIM#E<eid>#U<uid>/P  SET n = if_not_exists(n,:cero) + :k
                                         IF  attribute_not_exists(n) OR n <= :max_menos_k   -- :max_menos_k = max - k
```

* **Valores fijados por David:** `:skew` = **2 s** (supone relojes sincronizados por NTP; 5 s si no se garantiza), **máximo 10 sillas por orden** y `:max` = 10 (acordado con Samuel), y ante `TransactionConflict` *backoff* exponencial con *jitter* completo, **máx. 3 reintentos** con el mismo `ClientRequestToken`; `ConditionalCheckFailed` **no** se reintenta.
* El `Put` de la orden con `attribute_not_exists(pk)` evita crear la orden dos veces con el mismo `oid`.
* Los GSI de `bya_orders` se alimentan solos; **las transacciones no operan sobre índices** [R-04].
* Un fallo de condición en cualquier ítem cancela todo; `CancellationReasons` indica **qué silla** falló para avisar al usuario.

### 7.2 Fase 2 — Pago (no transaccional)

```text
Put bya_orders ORD#<oid>/PAY#<nn>  (st='INITIATED', idem='<oid>#<nn>', g3pk/g3sk)  IF attribute_not_exists(pk)
-- llamar a la pasarela con idempotency-key = '<oid>#<nn>'
Update PAY#<nn> SET st='DECLINED' IF st='INITIATED'      (y REMOVE g3pk,g3sk)
```

### 7.3 Fase 3 — Confirmación (`TransactWriteItems`, `ClientRequestToken = H(oid,"CONFIRM")`)

```text
Update bya_seats    cada silla   SET st='S', so=:oid, tk=:tid, v=v+1   IF st='L' AND lo=:oid          -- aunque haya vencido, si nadie la tomó sigue siendo suya
Update bya_orders   ORDER        SET st='PAID', tkt=:tids, ttl=:ttl_largo   IF st='PENDING'
Update bya_orders   PAY#<nn>     SET st='APPROVED', gtx=:gtx REMOVE g3pk,g3sk   IF st IN ('INITIATED','UNKNOWN')
Update bya_counters CNT#E<eid>#S<sid>/SH#<hash(oid) mod nsh>   ADD sold :n_en_esa_localidad
Put    bya_tickets  TKT#<tid>/T  (st='VALID', ...)  IF attribute_not_exists(pk)      -- una por silla; tid = UUIDv5(oid, silla)
Put    bya_orders   ORD#<oid>/INV#1 (st='PENDING', g3pk=PEND#INV#n)  IF attribute_not_exists(pk)
```

Con 2,5 sillas: 2,5 + 1 + 1 + 1 + 2,5 + 1 = **9 ítems** (límite 100). Si la orden tiene sillas de **dos localidades**, la confirmación lleva **un `Update` de contador por localidad**, cada uno en su fragmento `SH#<hash(oid) mod nsh>` (ítems distintos: no viola "un ítem una vez por transacción" [R-04]). Si la condición de una silla falla porque otro la tomó **después** de vencer el bloqueo, la aplicación pasa la orden a `FULFILL_FAIL` y encola **reembolso** (la pasarela ya cobró): ese es el escenario 2 del anexo de David.

### 7.4 Limitaciones de las transacciones que afectan el diseño de David [R-04]

| Limitación | Consecuencia para el modelo |
|---|---|
| ≤ 100 ítems, ≤ 4 MB, misma cuenta y región | Tope de sillas por orden (A-09: 10) |
| No se puede apuntar dos veces al mismo ítem | Si dos sillas se agrupan en un ítem, un solo `Update` por ítem; con el modelo actual (1 ítem por silla) no ocurre |
| Choque con otra transacción → `TransactionCanceledException` (**los SDK no reintentan**) | *Backoff* con *jitter* en la aplicación |
| La capacidad se consume **doble** y también cuando se cancela | Incluido en el dimensionamiento (el escenario de planificación cuenta f = 2 bloqueos fallidos por exitoso) |
| Serializable con `GetItem`/`PutItem`/`UpdateItem`; **no** con `BatchWriteItem` como unidad; `Query`/`Scan` = read-committed | Leer el estado definitivo con `GetItem` fuerte o `TransactGetItems`; nunca con `Query` para decidir |
| GSI y Streams se propagan **después**, con orden no garantizado entre ítems de la misma transacción | Consumidores idempotentes por `(clave, v)`; nunca decidir con GSI |
| Atómica solo en la región de escritura; **no hay transacciones entre regiones** y las **tablas globales MRSC no soportan transacciones** [R-17] | **Una sola región escribe** (activa-pasiva). Con MREC una réplica puede ver transacciones parciales y resuelve conflictos con "última escritura gana": peligroso si dos regiones escriben la misma silla |
| TTL no soportado en MRSC [R-17] | Otra razón para no usar MRSC en estas tablas |

---

## 8. Validación del modelo

### 8.1 ¿Las claves soportan cada patrón?

| Patrón | ¿Operación por clave (sin `Scan`)? | Comprobación |
|---|---|---|
| AP-01…AP-20 | Sí | Todos usan `GetItem`, `Query` por PK (+ condición de SK), `BatchGetItem` o `Query` en un GSI. **Ningún `Scan`.** |
| AP-04 | Sí | `Update` por clave de silla; `Put` por clave de orden; `Update` por clave de límite |
| AP-13 | Sí | Query en 8 fragmentos de `gsi_evento_orden`; el filtro `st` no reduce RRU pero el volumen por evento es acotado (≈ 24.000 órdenes en una preventa grande) |
| AP-18 | Sí | 8 fragmentos de `gsi_evento_boleta` (≈ 45.000 boletas ≈ 9 MB → 9–10 páginas de 1 MB [R-07]) |

### 8.2 ¿Soporta lo que David necesita?

| Necesidad de David | Elemento del modelo |
|---|---|
| Bloquear varias sillas de forma atómica | `TransactWriteItems` sobre `bya_seats` (§7.1) |
| Bloqueo de 8 min con vencimiento tratado como disponible | `lx`, `lo`, condición `st='A' OR (st='L' AND lx < now - skew)` |
| TTL solo limpia | `ttl` de `bya_seats` no interviene en condiciones |
| Pago idempotente | `PAY#nn.idem`, `PutItem` condicional, `ClientRequestToken` |
| Conciliación con la pasarela | `gsi_pendientes` (dispersa) |
| Doble uso de boleta | `bya_tickets.st` + `UpdateItem` condicional |
| Antibots con escrituras condicionales | `bya_counters` `LIM#…` |
| Estado intermedio "pagado sin boleta" | `ORDER.st = FULFILL_FAIL` y `PAY#.st = APPROVED` |

### 8.3 Riesgos de diseño que podrían invalidar la propuesta

| # | Riesgo | Efecto | Mitigación / estado |
|---|---|---|---|
| R1 | La tabla oficial deja la boleta en **1 KB**; con nombres de atributo y QR, si supera 1.024 B cuesta **2 WRU** en vez de 1 | +5 WRU por orden en el camino feliz | Sensibilidad ya incluida en el escenario de estrés (`ticket_wu = 2`) |
| R2 | **Frecuencia de `TransactionConflict` sobre una silla caliente** no medida | Latencia y reintentos en la apertura | Cola virtual + pista negativa + *backoff*; **PENDIENTE** de validar en simulacro (no se puede ejecutar en el curso) |
| R3 | Cómo se factura la propagación a GSI de ítems escritos en transacción | Si se duplica, `gsi_*` suben ×2 | Sensibilidad `idx_tx_factor = 2` en el escenario de estrés; **PENDIENTE** de confirmar en la calculadora de precios |
| R4 | Retraso del historial y del mapa por Streams | Información derivada atrasada | Aceptado y comunicado; conciliación periódica |
| R5 | **Pérdida de región con RPO > 0** (réplicas MREC asíncronas; MRSC sin transacciones) | Riesgo de **doble venta tras una conmutación entre regiones** | D-2 aceptada por David y Miguel **con dos condiciones** (de dónde sale la lista de sillas de un pago aprobado, y que la conciliación de desastre no parta de `gsi_pendientes`): ver §3.9 y `arquitectura.md` §4.1 |
| R6 | `lx` depende de relojes de la aplicación | Un servidor adelantado podría "robar" un bloqueo | `:skew` = 2 s y sincronización por NTP (David) |
| R7 | Una tabla **restaurada** no recupera Streams, TTL, IAM, alarmas, etiquetas, escalado, protección contra borrado ni PITR | Mapa, historial, limpieza y auditoría quedan "a medias" tras un simulacro o desastre | Lista de reaplicación obligatoria (§6.4) |

---

## 9. Ventajas y desventajas del diseño (para la sustentación)

**Ventajas.** (1) Cero `Scan` y cero `JOIN`. (2) Las sillas, lo más caliente, no tienen GSI y están repartidas en ≈ 900 claves. (3) La venta, la boleta, el contador y la silla cambian en **una** transacción. (4) Todo el historial se reconstruye desde exportaciones. (5) Las claves no cambian si David cambia las condiciones.

**Desventajas.** (1) Más tablas que operar (8). (2) El historial y el mapa dependen de Streams (retención 24 h). (3) El contador exacto exige leer N ítems. (4) La dependencia de `gsi_*` eventualmente consistentes obliga a leer con lectura fuerte antes de actuar. (5) La conmutación entre regiones no puede ofrecer RPO 0 con transacciones (se compensa con conciliación contra la pasarela).
