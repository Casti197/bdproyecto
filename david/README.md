# BoletaYa SAS — Parte de David: concurrencia, consistencia y alta disponibilidad

**Responsable:** David · **Pareja:** Jacobo · **Inicio:** 2026-10-29 · **Última actualización:** 2026-11-04 (respuestas del profesor)
**Rúbrica que cubre:** Concurrencia y consistencia (10), Anexo de concurrencia (3), Conmutación y alta disponibilidad (3), Ingreso al estadio sin internet (2).
**Modelo de datos:** el de Jacobo ([`../jacobo/`](../jacobo/)). No se rediseñan claves.

## Archivos

| Archivo | Contenido | Estado |
|---|---|---|
| [`concurrencia.md`](concurrencia.md) | Definición de doble venta del profesor (§0); transacciones de bloqueo, pago (Mercado Pago) y confirmación; segunda defensa de idempotencia; pagos sin registro; contención; antibots | Listo (actualizado 2026-11-04) |
| [`anexo_concurrencia.md`](anexo_concurrencia.md) | Los 4 escenarios con pseudocódigo y línea de tiempo; el 4 con el congelamiento de sillas en duda | Listo (actualizado 2026-11-04) |
| [`alta_disponibilidad.md`](alta_disponibilidad.md) | Replicación en 3 zonas, MREC con una sola región que escribe, atraso de replicación asumido, detección y criterio de declaración, **congelamiento de sillas en duda** (§5.0), confirmación en modo desastre, RTO de **4 a 11 min** desde la declaración | Listo (borrador para revisión) |
| [`estadio.md`](estadio.md) | Nodo por puerta como autoridad; aislamiento de 4 horas; punto de acceso sin red (§6.2); RPO/RTO del ingreso (§6.1); sincronización con DynamoDB; equipo (§9), soporte de 5 años (§9.1) y opciones de torniquetes ante el sobrecosto del Escenario B (§9.2) | Listo (borrador para revisión) |
| [`pruebas/`](pruebas/) | Prueba de las transacciones en un simulador (moto): 50 casos, todos pasan (`resultado.txt`); verificador de invariantes para el simulacro de Miguel; prueba de sandbox de Mercado Pago (`SANDBOX.md`, `resultados_sandbox.json`: 11 de 13) | Listo; búsqueda por fechas sin confirmar |
| [`pasarelas.md`](pasarelas.md) | Comparación de pasarelas para D-11 y resultados del sandbox (§7) | Decidido: Mercado Pago; búsqueda por fechas sin confirmar |
| [`respuestas_profesor.md`](respuestas_profesor.md) | Las 7 respuestas del profesor (2026-11-04) y a quién le toca cada una | Registrado |
| [`preguntas_para_el_cliente.md`](preguntas_para_el_cliente.md) | 64 preguntas en lenguaje de negocio para el profesor (cliente) | Enviadas; 7 respondidas el 2026-11-04 |
| [`preguntas_para_el_profesor.md`](preguntas_para_el_profesor.md) | Versión técnica, numeración P-1 a P-67 | Enviadas; 7 respondidas el 2026-11-04 |
| [`respuesta_a_jacobo.md`](respuesta_a_jacobo.md) | Validación de claves, `:skew`, máximo de sillas, reintentos, dos correcciones de sintaxis, postura sobre D-2 | Aplicada por Jacobo (2026-11-03) |
| [`respuesta_a_miguel.md`](respuesta_a_miguel.md) | Condiciones de D-2 aceptadas y cambios al runbook 2b | Aplicada por Miguel; **la parte de cerrar la venta quedó reemplazada** por `alta_disponibilidad.md` §5.0 |

## Pendientes

**Míos (David)**
* Sandbox de Mercado Pago (2026-11-04): `metadata` e idempotencia confirmadas. **La búsqueda por fechas no funciona**: sigue en 0 resultados 14 minutos después, y la aplicación no tiene credenciales `APP_USR` para repetirla (`pasarelas.md` §7). El grupo aprobó **D-2b** el 2026-11-04: la lista de sillas en duda sale de `bya_ledger`. Ya aplicado en `concurrencia.md` §4, `alta_disponibilidad.md` §4–§5, `anexo_concurrencia.md` 4a–4b y `pasarelas.md`.
* Entregar a Miguel el verificador de `pruebas/` para su simulacro de conmutación.
* Preparar la sustentación de mis cuatro partes.

**Jacobo**
* Sección de máximo 2 páginas: por qué DynamoDB no va *on premise* y si hay una alternativa compatible con su API (respuesta 1).
* Escenario A todo en AWS (respuesta 2).
* Qué infraestructura tiene AWS hoy en Colombia, si hay DynamoDB y la latencia desde Bogotá (respuesta 4).
* D-2b aprobada: activar `bya_ledger` con una clave que se pueda listar por minuto (propuesta: `LED#<minuto>#<fragmento>`, `alta_disponibilidad.md` §5.0), guardar el `id` del pago (`gid`) al pasar a `CHARGED`, y medir la latencia de la escritura entre regiones.

**Miguel**
* Runbook 2b, paso 4: las sillas en duda salen de `bya_ledger`, no de la búsqueda de Mercado Pago (D-2b). Pasos 6 y 7: misma ventana `T − W` y liberar solo con estado final.
* Runbook 2b y tabla de RTO con el congelamiento de sillas en duda; detección y criterio de declaración (`alta_disponibilidad.md` §3.2, §3.3 y §5.0).
* Carta del estadio: de 40 minutos a 4 horas aislado (respuesta 7).
* Runbooks del Escenario A sin aplicación en Bogotá (respuesta 2).

**Samuel**
* Análisis de transferencia internacional de la Ley 1581 (respuesta 4).
* Conformidad con D-2: una sola región escribe y RPO 0 de pagos por conciliación.
* Confirmar la devolución del cupo al expirar un bloqueo (`:max` = 10 ya acordado).

**Juan Pablo**
* Comparar A (todo en AWS) contra B en latencia, conectividad, egress y costos (respuesta 2).
* Costear `bya_ledger` (D-2b): tabla MRSC en tres regiones, unas 24.000 escrituras por preventa grande.
* Mostrar el Escenario B con torniquetes propios y con los del estadio (`estadio.md` §9.2).
* Corregir el signo del "Saldo" del Resumen y cobrar Ubuntu Pro solo el último año (`estadio.md` §9.1).

**Entre varios**
* Grupo: decidir la opción de torniquetes (`estadio.md` §9.2); la pregunta 45 al profesor sigue sin respuesta, así que la decisión va al registro de decisiones.
* Grupo: aprobar los riesgos E-R1 y E-R2 (`estadio.md` §8).

## Hecho

* 2026-11-03 · Jacobo aplicó las correcciones de sintaxis, Streams en `bya_tickets`, la puerta por localidad en `bya_catalog` y el libro de pagos opcional (`jacobo/respuesta_a_revisiones.md`). El pre-calentamiento de réplicas es automático.
* 2026-11-03 · Miguel aplicó `respuesta_a_miguel.md` (runbook 2b) y el licenciamiento del estadio.
* 2026-11-03 · Pasarela decidida: Mercado Pago (D-11).
* 2026-11-04 · Juan Pablo subió costos y dimensionamiento con las correcciones (`juanpablo/`).
* 2026-11-04 · Respuestas 3, 5, 6 y 7 del profesor aplicadas a esta carpeta.
* 2026-11-04 · Sandbox de Mercado Pago (11 de 13) y D-2b aprobada por el grupo: `bya_ledger` es la fuente de las sillas en duda.
