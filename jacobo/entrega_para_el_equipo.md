# Entrega para el equipo — interfaces de Jacobo con David, Juan Pablo, Miguel y Samuel

**Autor:** Jacobo · **Fecha:** 2026-10-29 · No sustituye el trabajo de nadie: da lo necesario para que cada quien integre su parte **sin rediseñar claves ni recalcular volúmenes**. Archivos de origen de cada compañero: no modificados.
Documentos de apoyo: [`modelo_datos.md`](modelo_datos.md) (claves y transacción) · [`capacidad_y_volumetria.md`](capacidad_y_volumetria.md) (cifras) · [`arquitectura.md`](arquitectura.md) (región, escenarios) · [`referencias.md`](referencias.md) `[R-xx]`.

---

## 0. Quién necesita qué (y para cuándo)

| Para | Qué recibe | Qué necesito de vuelta |
|---|---|---|
| **David** | Modelo con PK/SK/GSI, estructura de la transacción de compra (§7 del modelo), atributos del bloqueo y de la idempotencia, límites de las transacciones, hallazgo sobre RPO 0 entre regiones | Que **valide las claves** contra sus 4 escenarios (§1.3), confirme `:skew`, máximo de sillas/orden y el *backoff* |
| **Juan Pablo** | Volumetría 1–5, almacenamiento, RCU/WCU, costo por preventa, opciones on-demand/provisionado, componentes auxiliares, **qué está calculado, qué es supuesto y qué falta** | Precios unitarios de su catálogo para **contrastar** los míos; confirmar los pendientes de §2.3 |
| **Miguel** | Inventario de entidades, datos críticos, historiales/auditorías, lo archivable, retención propuesta, requisitos de recuperación del modelo | Lista de lo que se respalda y con qué frecuencia; que concilie su RPO 0 con la decisión D-2 |
| **Samuel** | Patrones para reembolsos por cancelación, datos a proteger, datos de auditoría, aspectos de arquitectura que afectan el cumplimiento | Plazo legal de conservación (para fijar TTL/exportación) y validación de la región |

Cronograma de `jacobo.md`: día 3 = borrador de patrones y claves (**este documento y `modelo_datos.md` lo cubren**) · viernes semana 1 = modelo congelado · semana 2 = volumetría y RCU/WCU (**ya entregada aquí**) y diagramas.

---

## 1. Para David — concurrencia, consistencia y alta disponibilidad

### 1.1 Modelo definitivo (propuesta para congelar)

| Tabla | PK | SK | GSI | Rol en tu transacción |
|---|---|---|---|---|
| `bya_seats` | `E<eid>#S<sid>#R<fila>` | `S<nro>` | **ninguno** | La silla: `st` (A/L/S), `lx`, `lo`, `so`, `tk`, `v` |
| `bya_orders` | `ORD#<oid>` | `ORDER` · `PAY#<nn>` · `INV#1` | `gsi_usuario`, `gsi_evento_orden`, `gsi_pendientes` (dispersa) | La orden, los intentos de pago y la referencia de factura |
| `bya_counters` | `CNT#E<eid>#S<sid>` · `LIM#E<eid>#U<uid>` | `SH#<00..N-1>` · `P` | — | Contador fragmentado y límite antibot |
| `bya_tickets` | `TKT#<tid>` | `T` · `SCAN#<ts>#<puerta>` | `gsi_evento_boleta` | Boleta y escaneos |
| `bya_catalog`, `bya_users`, `bya_seat_history`, `bya_audit` | ver `modelo_datos.md` §3 | | | Fuera de la transacción de compra |

### 1.2 Lo que necesitas, punto por punto

| Necesidad | Dónde está |
|---|---|
| **Identificar y bloquear varias sillas** | Cada silla es **un ítem** con clave `(pk, sk)` calculable desde `(evento, localidad, fila, número)`; `TransactWriteItems` hasta 100 ítems/4 MB, **máx. 10 sillas por orden** (A-09) [R-04, R-07] |
| **Atributos del bloqueo de 8 minutos** | `lx` (epoch s) y `lo` (orden dueña). Condición del bloqueo: `st='A' OR (st='L' AND lx < :vencido_antes_de)`, con `:vencido_antes_de = now − skew` **calculado en la aplicación** (una `ConditionExpression` no admite aritmética; corrección de David). **El TTL de `bya_seats` solo limpia; nunca interviene** [R-08] |
| **Confirmación aunque el bloqueo haya vencido** | `st='L' AND lo=:oid` (si nadie la tomó sigue siendo de la orden) |
| **Pagos idempotentes** | `PAY#nn.idem = <oid>#<nn>` (clave para la pasarela), `PutItem` con `attribute_not_exists(pk)`, `ClientRequestToken = H(oid,"LOCK"/"CONFIRM")` (válido 10 min tras terminar [R-04]); `ORD#<oid>` con `oid` generado por el cliente |
| **Estado de intentos y conciliación** | `PAY#nn.st` ∈ INITIATED/APPROVED/DECLINED/UNKNOWN; **`gsi_pendientes`** (dispersa) lista los pagos y facturas sin resolver para el reconciliador y SQS |
| **Boletas y doble uso** | `tid = UUIDv5(oid, silla)` (determinista) · `bya_tickets.st` VALID→USED con `UpdateItem` condicional + `SCAN#…` en la misma transacción |
| **Antibots por usuario** | `LIM#E<eid>#U<uid>` con `attribute_not_exists(n) OR n <= :max_menos_k` (`:max_menos_k = max − k`, calculado en la aplicación) dentro del bloqueo |
| **Estado intermedio "pagado sin boleta"** | `ORDER.st = FULFILL_FAIL` + `PAY#.st = APPROVED` → reembolso |

### 1.3 Los 4 escenarios de tu anexo: qué claves los sostienen

| Escenario | Elementos del modelo que usas | Lo que **no** debes asumir |
|---|---|---|
| **1. Dos clientes, misma silla** | El ítem de la silla; condición `st='A' OR (st='L' AND lx < :vencido_antes_de)`; `TransactionCanceledException` con `CancellationReasons` por ítem [R-04]. Transacciones y `UpdateItem` son **serializables** entre sí [R-04] | Que el SDK reintente un `TransactionConflict`: **no lo hace** [R-04] |
| **2. El bloqueo expira mientras paga** | `lx`, `lo`, condición de confirmación `st='L' AND lo=:oid`; si otro la tomó, `FULFILL_FAIL` + reembolso | Que el TTL libere la silla |
| **3. Falla a mitad de la compra** | Transacciones atómicas (todo o nada); `ClientRequestToken`; condiciones de estado (`ORDER.st='PENDING'`); `gsi_pendientes` + SQS | Que el token proteja más de 10 minutos: después protege la **condición** (`st='L' AND lo=:oid` falla porque ya es `S`) |
| **4. Conmutación del servidor** | **Dentro de la región**: 3 zonas, RPO 0, sin modo de conmutación que gestionar [R-01]. **Entre regiones**: ver §1.5 | Que una tabla global entre regiones dé RPO 0 con transacciones |

### 1.4 Limitaciones de las transacciones que condicionan tu diseño

Resumidas en `modelo_datos.md` §7.4: ≤ 100 ítems/4 MB · el mismo ítem una vez por transacción · conflictos → cancelación (sin espera) · capacidad ×2 **y también al cancelar** · serializable con operaciones sueltas pero **no** con `BatchWriteItem` ni `Query` (read-committed) · GSI y Streams llegan después y sin orden entre ítems · atómicas solo en la región de escritura · **MRSC no soporta transacciones ni TTL**.

**Por qué no hay *deadlocks* clásicos (para tu respuesta de sustentación):** DynamoDB no toma bloqueos que se esperen entre sí; una transacción que choca con otra **se cancela** (`TransactionConflict`) y la aplicación reintenta con *backoff*. Lo que reemplaza al *deadlock* es **cancelación + reintento** [R-04].

### 1.5 Hallazgo que afecta tu estudio de conmutación (no lo oculto)

Tu plan dice "por qué ninguna orden confirmada se pierde (RPO 0)". La documentación obliga a **separar**:

* **Fallo de zona**: RPO 0 (la escritura se confirma tras replicarse en varias zonas; "replica los datos en tres zonas de disponibilidad por defecto") [R-01].
* **Pérdida de región**: **no existe RPO 0 con transacciones**. MRSC (RPO 0) **no admite transacciones** ni TTL y ni siquiera existe en `sa-east-1`; MREC es **asíncrono** (RPO = retraso de replicación, "normalmente unos segundos") y puede mostrar **transacciones parciales** en la réplica y resolver conflictos por "última escritura gana" [R-17].
* **Riesgo para la regla de oro:** si dos regiones escriben, o si se reabre la región alterna sin conciliar, una silla vendida en el último segundo puede **venderse otra vez**.
* **Propuesta (D-2):** una sola región escribe; tras un desastre de región, **modo seguro**: conciliar contra la pasarela (fuente de verdad del dinero), marcar vendidas las sillas de los pagos aprobados y **solo entonces** reabrir. El RPO 0 de **pagos** se sustenta con la conciliación, no con la réplica.

---

## 2. Para Juan Pablo — costos y dimensionamiento

El detalle está en `capacidad_y_volumetria.md` §7–§8. Resumen separado en tres columnas, como pediste ("calculado / supuesto / pendiente").

### 2.1 **Calculado** (reproducible con `python3 -I calculos/modelo_capacidad.py`)

| Dato | Valor |
|---|---|
| Preventas grandes por año | 25 (`DATO`) |
| Órdenes por preventa / por segundo (prom.) | 24.000 / 20 |
| WRU por orden (mín. / planificación / estrés) | 55,3 / 84,4 / 182,9 |
| WRU/s de preventa: promedio / ráfaga ×5 / +25 % | 1.687 / 8.437 / **10.546** (planificación) |
| RRU/s de preventa (planificación ×5) | ≈ 2.200 |
| Capacidad de pico si se provisiona (año 1 → año 5) | 10.546 → 14.510 WCU; 2.744 → 3.194 RCU |
| Almacenamiento en línea tablas + GSI (año 1…5) | 48,0 · 104,0 · 135,8 · 177,4 · 231,8 GiB |
| Archivado en S3 acumulado (año 1…5) | 0 · 1,6 · 34,1 · 76,3 · 131,2 GiB |
| WRU anuales año 1 / año 5 | 123,4 M / 277,7 M |
| RRU anuales año 1 / año 5 | 45,4 M / 73,0 M |
| Costo DynamoDB por preventa (on-demand) | USD 2,14 (sa-east-1) · **1,42 (us-east-1)** |
| Capa de datos completa, USD/año (throughput + almacenamiento + PITR + exportaciones + S3) | año 1: **348 (us) – 523 (sa)** · año 5: **1.489 (us) – 2.242 (sa)** |
| Costo anual por opción de capacidad (año 1, USD) | on-demand 83–124 · provisionado programado 880–1.319 · provisionado fijo 63.176–94.764 |
| Mapa de sillas (CloudFront) por preventa, año 1 | USD 25 (moderada) · **76 (alta)** · 253 (extrema); año 5 extrema: **618** (USD 15.442/año ≈ COP 61,8 M) |
| ElastiCache 2 × `cache.m7g.large`, USD/año | 2.215 (us-east-1) · 3.154 (sa-east-1) |
| API Gateway HTTP API por preventa | USD 1,12 (us) · 1,79 (sa) |

Todos en USD (lista oficial AWS, versión 2026-09-11, consulta 2026-10-29). **Conversión a COP con tu TRM 4.000: es tuya** (el script ya imprime COP para la capa de datos). El IVA del 19 % sobre servicios de nube "facturados en Colombia" **no lo apliqué**: decídelo tú.

### 2.2 **Supuestos** (cámbialos en el script y vuelve a correrlo)

Eventos +30 %/año (A-01) · auditoría +30 % (A-02) · sobrecarga 100 B/ítem (A-03) · retención en línea 2 años, escaneos 1 año (A-04) · usuarios = existencias (A-05) · CloudFront en zona "South America" (A-06) · 5 % de auditoría humana (A-07) · máx. 10 sillas por orden (A-09) · f = 2 bloqueos fallidos por exitoso y 30 % de abandono (A-10) · mapa: 3 KB por consulta, TTL 2 s (A-11) · pico instantáneo ×5, margen 25 % · sin capa gratuita.

### 2.3 **Pendientes** (no inventé ninguna cifra)

1. Monto del **pre-calentamiento** (`warm throughput`): la página de precios dice "cargo único a la tarifa regional de una RCU/WCU, según el aumento" [R-36]; confirmarlo en la calculadora.
2. Si la propagación a GSI de escrituras en transacción cuenta ×1 o ×2 (sensibilidad: +12 % en WRU/orden).
3. Streams (lecturas), Lambda, KMS, CloudWatch, CloudTrail, WAF/Shield.
4. **Cola virtual** (el producto de AWS está discontinuado [R-29]).
5. **Direct Connect** (puerto en Equinix BG1, datos) y VPN.
6. Tarifa real de CloudFront para Colombia.
7. **Captura/exportación de la AWS Pricing Calculator** (exigida por el enunciado): yo usé la **API de lista de precios**, guardada en `calculos/evidencia/`; no sustituye la captura que debes hacer.
8. Costo de PITR en el diseño final de Miguel (yo estimé ≈ el tamaño de las tablas; PITR no factura los GSI [R-36]).

### 2.4 Elementos que generan costos adicionales (para que no queden "omitidos", −0,5)

Salida de datos (*egress*) hacia el DC de Bogotá y hacia usuarios (CloudFront) · réplicas entre regiones (escritura replicada: USD 0,625/M WRU en us-east-1) · copias de respaldo entre regiones (Miguel) · exportaciones diarias a S3 · almacenamiento de S3 (instantáneas, histórico) · Athena por TB escaneado · aplicación en espera en la región alterna · **escalado en cada preventa** (con on-demand: incluido en WRU; con provisionado: ≈ USD 22–32 por preventa) · garantía y soporte de hardware (solo B) · energía del DC (solo B) · IP públicas fijas.

### 2.5 Sensibilidades que pides (doble de preventas, doble de cola)

* **Doble de preventas (50/año):** WRU de preventa ×2 ⇒ +50,6 M WRU ⇒ **+USD 32–47** (us/sa) en throughput en el año 1; mapa: CloudFront ×2.
* **Doble de personas en la cola:** el throughput de DynamoDB **casi no cambia** (la admisión regula las compras); sí se duplica el mapa: "Alta" pasa de USD 76 a ≈ 152 por preventa (≈ USD 3.800/año). Un aumento de f por la mayor contención sube los WRU (f = 8: +78 % de pico).
* **Escenario B** (hardware, energía, enlace): tuyo.

---

## 3. Para Miguel — recuperación, respaldos y licenciamiento

### 3.1 Inventario de entidades y su criticidad

| Entidad | Tabla | Clase de componente del enunciado | RPO / RTO exigidos | Naturaleza | ¿Archivable? |
|---|---|---|---|---|---|
| Silla (estado) | `bya_seats` | **Venta** | **0** / 15 min (preventa), 1 h (normal) | **Crítica** (verdad transaccional) | Sí (final) tras 90 días del evento |
| Orden, pago, factura-ref | `bya_orders` | **Venta** | 0 / 15 min – 1 h | **Crítica** | Sí a los 2 años (TTL tras exportar) |
| Boleta, escaneo | `bya_tickets` | **Venta** + **Ingreso** | Venta: 0; escaneos ya hechos: **0**; ingreso: continuidad local inmediata | **Crítica** | Boleta 2 años; escaneos 1 año |
| Contadores y límites | `bya_counters` | **Venta** | 0 | **Crítica** (el contador es derivado de las ventas y reconstruible contando sillas `S`) | No (los `LIM#` caducan) |
| Usuarios | `bya_users` | Usuarios, catálogo y analítica | 15 min / 4 h | Crítica para operar, datos personales | No (supresión por solicitud) |
| Catálogo | `bya_catalog` | Usuarios, catálogo y analítica | 15 min / 4 h | Media | Sí a los 2 años |
| Historial de sillas | `bya_seat_history` | Derivada | 15 min / 4 h (propuesto) | Reconstruible desde exportaciones de `bya_seats` | Sí a los 2 años |
| Auditoría | `bya_audit` | **Usuarios, catálogo y analítica** (clasificación propuesta por Miguel y aceptada) | 15 min / 4 h | **Evidencia legal**; inmutable en S3 | Sí a los 2 años |
| Histórico > 2 años | S3 | Histórico | 24 h / 48 h | Evidencia | Es el archivo |

### 3.2 Hechos del servicio que pesan en tus runbooks (con fuente)

* **PITR:** restauración a cualquier segundo del período configurado (**1–35 días**), **hasta cinco minutos antes de la hora actual** [R-42] (el último punto restaurable no es "ahora"; corrección H-5 de Miguel); las copias continuas y las restauraciones **no usan capacidad aprovisionada ni afectan rendimiento o disponibilidad** [R-01]. Esto responde "cómo respaldar sin ponerlo lento".
* **Respaldos bajo demanda** y **AWS Backup** con copia entre cuentas y regiones y paso a almacenamiento frío [R-01]; **bóveda inmutable (Vault Lock)** y simulacros: tuyos.
* **PITR, protección contra borrado y etiquetas NO se sincronizan entre réplicas de una tabla global** [R-17]: hay que configurarlas **en cada región**.
* **TTL:** el borrado se **replica** a las demás regiones y **consume** escritura replicada allí [R-08, R-17].
* **Exportación a S3** requiere PITR, no consume RCU, y no hay SLA de duración [R-09]. Hay límite de **50 restauraciones concurrentes / 50 TB** [R-14] (sección "Backup and restore" de esa página de cuotas; la leí, la cita es correcta; H-7).
* **Una restauración crea una tabla nueva y no devuelve Streams, TTL, IAM, alarmas, etiquetas, escalado, protección contra borrado ni PITR** [R-41]: la lista de lo que hay que reaplicar está en `modelo_datos.md` §6.4 (H-6). Los GSI pueden excluirse y reconstruirse.
* **DynamoDB no tiene versiones, ediciones ni licencia por núcleo** [R-01] (tu punto 5.3): "no hay mantenimiento ni ventanas".

### 3.3 Retención propuesta (**SUPUESTO A-04, sujeta a validación legal de Samuel**)

Órdenes/pagos/boletas/referencias de factura: **2 años en línea** (`DATO`) y luego S3 con retención legal. Escaneos: 1 año en línea. Sillas: evento + 90 días. Historial y auditoría: 2 años en línea. **El plazo legal posterior lo fija Samuel**; el diseño lo soporta con S3 versionado + Object Lock y exportaciones diarias.

### 3.4 Requisitos de recuperación que salen del modelo

1. **Reconstruir el contador:** contar sillas `S` por consulta de filas y compararlo con la suma de fragmentos (diferencia 0).
2. **Reconstruir el historial y el mapa:** desde Streams (24 h) o, más atrás, desde las exportaciones incrementales (traen `OldImage`/`NewImage` y `WriteTimestampMicros` [R-15]).
3. **GSI:** son derivados de la tabla; el respaldo cubre la tabla.
4. **Pago confirmado sin registro:** `gsi_pendientes` + reconciliación con la pasarela (David).
5. **Pérdida de región:** ver D-2: RPO 0 de pagos por **conciliación**, no por réplica. **Tu runbook "pérdida total del sitio" debe distinguir** fallo de zona (sin acción), pérdida de región (modo seguro) y pérdida del DC de Bogotá (escenario B: conmutar la **venta** a la aplicación en AWS **por DNS o a mano**: el *origin failover* de CloudFront no conmuta `POST` [R-40]).
6. **Escenario B, "qué pasa si falla el DC de Bogotá":** los datos **no** están en el DC; lo que se pierde es la aplicación y la caché local (**la cola virtual guarda su estado en AWS**, H-4): se conmuta a la aplicación en espera en AWS. El RTO se informa **desde la declaración** de la falla; detección y decisión aparte (H-2). RTO **PENDIENTE** (el cálculo es tuyo).

---

## 4. Para Samuel — seguridad, cumplimiento y consolidación

### 4.1 Reembolsos por evento cancelado (Ley 1480): cómo se localizan órdenes y boletas

1. **AP-13**: `Query` en `gsi_evento_orden` sobre los **8 fragmentos** `EVT#<eid>#0..7` (en paralelo), filtro `st = PAID`: devuelve todas las órdenes pagadas del evento.
2. Por cada orden: lectura **fuerte** de `ORD#<oid>/ORDER` (estado real; el GSI es eventual) y de su `PAY#nn` aprobado (token `gtk` y `gtx` para el reembolso).
3. **Boletas:** la orden guarda la lista `tkt`; `BatchGetItem` en `bya_tickets`; alternativa por evento: `gsi_evento_boleta`.
4. Estados: `PAID → REFUNDING → REFUNDED` con `UpdateItem` condicional; **idempotencia del reembolso** con clave `refund#<oid>` ante la pasarela.
5. Volumen y costo: una preventa de 24.000 órdenes ≈ 3,8 MB de índice ≈ 470 RRU eventuales (3,84 MB / 8 KB); trivial. Para un evento cancelado **ya archivado** (> 2 años): Athena sobre S3 (§6.2 del modelo).
6. Los pagos con tarjeta no se "reembolsan" desde la base: se encola a la pasarela vía SQS.

### 4.2 Información que debe protegerse

| Dato | Dónde | Cómo lo trata el modelo | Tu decisión |
|---|---|---|---|
| Cédula, correo, teléfono | `bya_users` | Cifrados en el cliente (campos `*_c`); el correo no es clave de índice (se usa su SHA-256) | Llaves, roles, enmascaramiento |
| **Token de la pasarela** (`gtk`, `gtx`) | `bya_orders` `PAY#` | **Solo el token; ningún número de tarjeta en ninguna tabla** | Verificar que **ningún log ni respaldo** la contenga (−1,0) y la lectura del token por rol |
| Clave HMAC del QR | Fuera de la base (gestor de secretos/KMS) | Solo `qrh` (huella) en `bya_tickets` | Rotación y custodia |
| Auditoría | `bya_audit` + S3 con Object Lock | Ver §4.3 | Retención y roles de auditor |

DynamoDB cifra **todos los datos en reposo por defecto** (clave propiedad de AWS, o administrada por el cliente con KMS) y ofrece **control de acceso a nivel de atributo** con IAM [R-01]: soporta el mínimo privilegio por tabla (soporte sin acceso a `bya_orders` completo).

### 4.3 Datos necesarios para auditar cambios

* **Cambios administrativos (precio, cupo, silla):** `bya_audit` **síncrono** en la misma transacción que el cambio (`TransactWriteItems`: `Update` + `Put` de auditoría): **imposible cambiar sin rastro**; actor (`ator`, `tip=HUMAN`), antes/después, `req`.
* **Cambios automáticos de sillas:** `bya_seat_history` (versión `v` + estado anterior/nuevo).
* **Qué NO da Streams:** la **identidad de la persona** (los registros del *stream* no la traen); por eso la auditoría humana la escribe la aplicación. **CloudTrail** cubre cambios de **control** (tablas, roles). Tú integras ambas.
* Auditoría **de sistema** (≈ 5 M/mes): no se indexa por actor; se consulta por entidad o con Athena.

### 4.4 Aspectos de arquitectura que afectan el cumplimiento

1. **Región fuera de Colombia** (recomendada `us-east-1`; alterna `us-east-2`): análisis de **transferencia internacional**. Insumo (fuente **secundaria**): EE. UU. figura en la lista de la Circular Externa 005 de 2017 de la SIC; Brasil **no** figuraba y es candidato en 2026 [R-35]. **Verifica el numeral vigente en la Circular Única.**
2. **Réplica y respaldos en otra región** = otra transferencia del mismo dato personal.
3. **TTL vs. retención legal:** el TTL borra de línea, **no** de S3; el plazo legal posterior (norma tributaria, **la busca Samuel**) se aplica en S3 (Object Lock + ciclo de vida). Mientras exista el ítem vencido pendiente de borrado, sigue siendo legible (hasta días) [R-08].
4. **Derecho de supresión (Ley 1581) vs. conservación de órdenes:** `bya_orders` guarda `uid`, no datos personales en claro; la supresión del perfil en `bya_users` no rompe las órdenes (seudonimización).
5. **Factura electrónica:** `INV#1` se crea **en la misma transacción** que el pago (`PENDING`); `gsi_pendientes` permite demostrar que **no queda una orden pagada sin factura** (todo `PAID` sin `INV.st = ISSUED` es detectable).
6. **PCI DSS:** el diseño almacena solo el token; AWS declara que DynamoDB cumple, entre otros, PCI DSS [R-01], pero que **el alcance del cliente** depende de que no se almacene tarjeta (tu argumento).
7. **Antibots:** el límite por usuario (`LIM#`) está en el modelo; el resto (detección de patrones) es tuyo y de David.

---

## 5. Decisiones que deben aprobarse entre todos

| # | Decisión | Propuesta | Quién decide / afecta |
|---|---|---|---|
| **D-1** | Congelar el modelo de 8 tablas y las claves | **APROBADA por David** (2026-10-29) | Todos |
| **D-2** | **Una sola región escribe; RPO 0 de pagos ante pérdida de región por conciliación con la pasarela** (no por réplica); MRSC descartado **para la compra** | **Aceptada por David y Miguel con 2 condiciones**: (1) sillas del pago aprobado como metadato del cobro, o libro de pagos en MRSC (`modelo_datos.md` §3.9); (2) conciliación de desastre desde la lista de la pasarela, no desde `gsi_pendientes`. Falta Samuel y elegir pasarela | **David + Miguel + Samuel** (afecta runbooks, sustentación y registro de decisiones) |
| **D-3** | Región principal `us-east-1`, alterna `us-east-2`; plan B `sa-east-1` | Aprobar sujeto a la validación legal | Samuel (legal), Juan Pablo (costos), David/Miguel (replicación) |
| **D-4** | Capacidad: **on-demand + pre-calentamiento + máximo de throughput**; plan B provisionado programado | Aprobar | Juan Pablo |
| **D-5** | Contador exacto fragmentado dentro de la transacción (N = 8) | Aprobar | David |
| **D-6** | Retención en línea (A-04) y TTL con exportación previa | Validar el plazo legal | Samuel, Miguel |
| **D-7** | Interpretación de los escenarios: A = ruta crítica en AWS; B = híbrido con aplicación en Bogotá | Confirmar con el profesor (P-1, P-3) | Todos |
| **D-8** | Cola virtual: construcción propia vs. producto comercial | Costear ambas | Juan Pablo |
| **D-9** | Máximo 10 sillas por orden; `:skew` de relojes; política de reintentos | **Fijados por David**: 10 sillas, `:skew` = 2 s, *backoff* con *jitter* y máx. 3 reintentos | Cerrada |
| **D-11** | **Elegir la pasarela de pagos** (llave de idempotencia, metadato en el cobro, listado por fechas) | Elegir entre Miguel, David y Jacobo; de ella depende la opción A o B de D-2 | Miguel, David, Jacobo |
| **D-10** | Historial por Streams (idempotente) y auditoría administrativa síncrona | Aprobar | David, Samuel |

---

## 6. Contradicciones y huecos entre documentos (con resolución propuesta)

| # | Documentos | Conflicto | Propuesta |
|---|---|---|---|
| X-1 | Enunciado §3 (RPO 0, RTO 15 min, "pérdida total del sitio") vs. documentación de DynamoDB | RPO 0 entre regiones no es compatible con transacciones | D-2 + P-4 |
| X-2 | `david.md` ("por qué ninguna orden confirmada se pierde, RPO 0") y `miguel.md` ("cómo se logra RPO 0 para pagos") | Se asume un mecanismo único de RPO 0 | Separar zona (RPO 0 real) de región (conciliación) |
| X-3 | Enunciado §5.4 y glosario ("réplica síncrona/asíncrona", "réplica de lectura para el mapa") vs. DynamoDB | El servicio gestiona la replicación entre zonas; no hay réplicas de lectura que configurar | Mapa por CDN/instantáneas; MREC solo para DR |
| X-4 | `jacobo.md` ("estimar compresión y espacio libre") y enunciado §5.1 ("CPU, memoria, IOPS") | No existen en DynamoDB | Se traduce a RCU/WCU; compresión 1:1; sin espacio libre (C-4, C-5) |
| X-5 | Enunciado: 60.000 boletas/preventa vs. estadio de 45.000; 8.000/día + 25 × 60.000 ≠ 4 M; "100 ventas/min" vs. 8,3 | Datos inconsistentes | C-1…C-3 de `capacidad_y_volumetria.md` |
| X-6 | Enunciado: "la aplicación vivirá en el data center" vs. escenario A (todo en la nube) | A y B podrían coincidir | P-3 |
| X-7 | `juanpablo.md` (B: hardware y energía; A: nube) vs. diseño: DynamoDB no corre on premise | El costo de B es "híbrido", no "base on premise" | P-1 |
| X-8 | `samuel.md` ("auditoría con CloudTrail y Streams") | Streams no trae la identidad del actor | La auditoría humana la escribe la app (§4.3) |
| X-9 | Enunciado: "Silla … 100 bytes" vs. diseño real | Con nombres de atributo una silla vendida ≈ 100 B (ver modelo §3.2): coincide; si crece, el costo de escritura sigue siendo 1 WRU hasta 1 KB | Sin acción |

---

## 7. Preguntas pendientes para el profesor

| # | Pregunta |
|---|---|
| **P-1** | DynamoDB solo existe como servicio de AWS. ¿Se acepta como Escenario B la **variante híbrida** (aplicación, caché local y estadio en Bogotá; base en AWS por Direct Connect/VPN), o cómo debe interpretarse B? (pendiente en `jacobo.md` y `juanpablo.md`) |
| **P-2** | Una preventa de **60.000 boletas** frente a estadios de **45.000** sillas: ¿es un lanzamiento de varias fechas/eventos o un festival? ¿Se modela en un solo evento (peor caso)? |
| **P-3** | En el Escenario A, ¿la **aplicación debe vivir físicamente en el data center** de Bogotá (como dice el enunciado) o puede desplegarse en la nube junto a la base? |
| **P-4** | "Pérdida total del sitio": ¿equivale a **pérdida de zona, de región o del data center**? Con transacciones, RPO 0 entre regiones no es alcanzable con DynamoDB; ¿se acepta RPO 0 **de pagos por conciliación** con la pasarela? |
| **P-5** | ¿Se acepta un **producto comercial de cola virtual** como componente auxiliar (costeado), dado que el de AWS está discontinuado? |
| **P-6** | ¿Se acepta alojar datos de compradores en una región **fuera de Colombia** (EE. UU.) con el análisis de transferencia internacional de Samuel? |
| **P-7** | El enunciado pide "volumen por **nivel de almacenamiento**": ¿cuenta como niveles Standard / Standard-IA / S3 archivo? |
| **P-8** | ¿Se exige la **captura de la AWS Pricing Calculator** aun cuando los precios vengan de la API de lista de precios oficial? |

---

## 8. Lista de verificación para el viernes de la semana 1 (estado al 2026-11-03)

- [x] David confirma que las claves soportan sus 4 escenarios (`david/respuesta_a_jacobo.md`; dos correcciones de sintaxis **aplicadas** en `modelo_datos.md` §7.1).
- [ ] Juan Pablo contrasta mis cifras con su catálogo de precios y resuelve §2.3.
- [x] Miguel entrega su lista de componentes de respaldo y concilia D-2 (con 2 condiciones; ver D-2). Sus 7 hallazgos están atendidos en [`respuesta_a_revisiones.md`](respuesta_a_revisiones.md).
- [ ] Samuel entrega el plazo legal y la validación de la región.
- [ ] Todos: leer `modelo_datos.md` §5 (contador exacto) y §7 (transacción) y `arquitectura.md` §4.1 (RPO 0), que son las preguntas más probables del jurado.
