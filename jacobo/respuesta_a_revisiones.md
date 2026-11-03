# Respuesta de Jacobo a las revisiones de David y Miguel

**Autor:** Jacobo · **Fecha:** 2026-11-03
**Responde a:** `david/respuesta_a_jacobo.md` (2026-10-29), `miguel/revision_de_jacobo.md` (2026-10-30), `miguel/respuesta_a_david.md` §2–§3 y los pendientes asignados a Jacobo en `david/README.md` y `miguel/README.md`.
Solo cambié archivos de `jacobo/`. Las fuentes nuevas son R-40, R-41 y R-42 (consultadas el 2026-11-03; **las abrí y leí**).

---

## 1. David

| Punto | Decisión | Dónde quedó |
|---|---|---|
| Veredicto: las claves soportan los 4 escenarios; congelar el modelo (D-1) | **Aceptado. El modelo queda congelado** | `entrega_para_el_equipo.md` D-1 |
| Condición de confirmación `st='L' AND lo=:oid` sin exigir `lx` vigente | Ya era la mía; sin cambio | `modelo_datos.md` §7.3 |
| **Corrección 1:** la `ConditionExpression` no admite aritmética (`lx < :now - :skew`) | **Aplicada**: `lx < :vencido_antes_de`, con `now − skew` calculado en la aplicación; `SET lx = :lx` ya calculado | `modelo_datos.md` §7.1; `entrega_para_el_equipo.md` §1.2 y §1.3 |
| **Corrección 2:** `n + :k <= :max` | **Aplicada**: `attribute_not_exists(n) OR n <= :max_menos_k` | `modelo_datos.md` §7.1; `entrega_para_el_equipo.md` §1.2 |
| `:skew` = 2 s; 10 sillas por orden; *backoff* con *jitter*, máx. 3 reintentos; `ConditionalCheckFailed` sin reintento | **Incorporados como valores fijados** (D-9 cerrada) | `modelo_datos.md` §7.1; D-9 |
| Dos localidades en una orden: un `Update` de contador por localidad | **Aceptado** (ítems distintos, no viola la regla de "un ítem una vez") | `modelo_datos.md` §7.3 |
| Webhook de la pasarela → SQS → DLQ; estado `UNKNOWN` | Sin cambio de claves: `UNKNOWN` y `gsi_pendientes` ya existen | — |
| **Pedido a Jacobo:** activar Streams en `bya_tickets` | **Hecho**: vista `NEW_AND_OLD_IMAGES`, Lambda con filtro (altas de boleta y paso a `VOID`), cola SQS por evento, retención de 24 h y plan de reconstrucción por `gsi_evento_boleta` | `modelo_datos.md` §3.5 |
| **Pedido a Jacobo:** guardar la puerta por localidad en `bya_catalog` | **Hecho**: atributo `pue` en `SEC#<sid>` | `modelo_datos.md` §3.1 |
| **Pedido a Jacobo:** pre-calentar las réplicas | **Resuelto con la documentación:** el `warm throughput` de una tabla global **se aplica automáticamente a todas las réplicas** [R-18]; se pre-calienta al mismo nivel. **Pendiente:** si el cargo único se cobra por región, y su duración (Juan Pablo) | `modelo_datos.md` §4.3; `capacidad_y_volumetria.md` §7.3 y §8.3; `arquitectura.md` §4.1 punto 6 |
| D-2 (una sola región escribe) | **De acuerdo; aceptada por David** y por Miguel con dos condiciones (§2 abajo) | `entrega_para_el_equipo.md` D-2 |

## 2. Miguel — los 7 hallazgos

| # | Gravedad | Veredicto | Qué hice | Dónde |
|---|---|---|---|---|
| **H-1** | Alta | **Correcto; lo verifiqué.** La documentación dice que CloudFront solo conmuta si el método es `GET`, `HEAD` u `OPTIONS` y que **no conmuta `POST` ni `PUT`** [R-40]. Mi texto y el diagrama del B afirmaban lo contrario para la compra | Corregí el riesgo (4) de §3.4, el diagrama B (la flecha ahora dice "cambio manual o por DNS del origen dinámico — un POST no conmuta solo"), A-R5 y `entrega_para_el_equipo.md` §3.4. La venta conmuta por DNS o a mano; CloudFront puede conmutar solo lo que es `GET` | `arquitectura.md` §3.3–§3.4, §8; `entrega_para_el_equipo.md` §3.4 |
| **H-2** | Media | **Correcto.** El enunciado mide el RTO "desde que se declara la falla" | El RTO se reporta **desde la declaración**; detección y decisión aparte. Cito tu estimación de 6–14 min como **estimada con supuestos** | `arquitectura.md` §4.1 punto 4 |
| **H-3** | Media | **Aceptado, con una decisión abierta.** (1) La lista de sillas de un pago aprobado puede no haberse replicado; (2) la conciliación de desastre no puede partir de `gsi_pendientes` | (2) quedó en el proceso (modo desastre parte de la lista de la pasarela). (1) Diseñé la **opción B (libro de pagos en MRSC)** como tabla **opcional** `bya_ledger` y dejé la **A (metadato en el cobro)** como principal. Nota: mi modelo descarta MRSC **para la compra** (transacciones), no para una tabla sin transacciones como el libro | `modelo_datos.md` §3.9; `arquitectura.md` §4.1 punto 5; D-2, D-11 |
| **H-4** | Media | **Correcto.** Una cola en Bogotá pierde el lugar de 250.000 personas al caer el DC | **Moví el estado de la cola a AWS** (ElastiCache Multi-AZ) en el diagrama y el texto del B; si se perdiera, readmisión por sorteo | `arquitectura.md` §3.3–§3.4, A-R8 |
| **H-5** | Baja | **Correcto; lo verifiqué:** se puede restaurar "desde cinco minutos antes de la hora actual" [R-42] | Corregí "a cualquier segundo" | `entrega_para_el_equipo.md` §3.2 |
| **H-6** | Baja | **Correcto; lo verifiqué:** una tabla restaurada **no** recupera Streams, TTL, IAM, alarmas, etiquetas, escalado, protección contra borrado ni PITR [R-41] | Nueva subsección con la **lista de reaplicación** y su efecto en este modelo; riesgo R7 | `modelo_datos.md` §6.4 y §8.3 |
| **H-7** | Baja | **La cita es correcta.** "50 restauraciones concurrentes / 50 TB" sí está en la sección *Backup and restore* de la página de cuotas que abrí el 2026-10-29 [R-14] | Dejé la cita y añadí en qué sección está | `entrega_para_el_equipo.md` §3.2 |

**Otros acuerdos con Miguel.** La clasificación de `bya_audit` como "Usuarios, catálogo y analítica" (15 min / 4 h) **queda aceptada** (`entrega_para_el_equipo.md` §3.1). Historial de sillas 15 min / 4 h: de acuerdo. `bya_counters` reconstruible contando sillas `S`: de acuerdo.

## 3. Lo que sigue abierto (no lo cierro yo)

| # | Pendiente | Quién |
|---|---|---|
| D-11 | **Elegir la pasarela de pagos**: llave de idempotencia, metadato en el cobro, listado por rango de fechas. De ella depende que D-2 use la opción A o la B (`bya_ledger`) | Miguel, David y Jacobo |
| D-2 | Falta la conformidad de **Samuel** y la pregunta P-4 al profesor | David (la envía), Samuel |
| — | Cargo del pre-calentamiento en réplicas y latencia de escritura del libro MRSC (us-east-1 ↔ us-east-2) | Juan Pablo / medir |
| — | Costo del libro de pagos (testigo MRSC + escritura sincrónica) **no** está en el costo base | Juan Pablo |
| — | Tiempo real de la conmutación de la venta por DNS (U-14) | Miguel |

## 4. Efecto en las cifras

**Ninguna cifra de volumetría, WRU/RCU ni costo cambió**: los cambios son de sintaxis de condiciones, atributos nuevos de bajo volumen (`pue`), Streams en `bya_tickets` (no tiene impacto de rendimiento en la tabla [R-11]; el precio de las lecturas del *stream* sigue **pendiente**, U-5) y texto de arquitectura. El libro de pagos, si se activa, añade ≈ 24.000 escrituras por preventa grande; **no está en el modelo de capacidad** (`calculos/modelo_capacidad.py` no se modificó).
