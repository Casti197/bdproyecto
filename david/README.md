# BoletaYa SAS — Parte de David: concurrencia, consistencia y alta disponibilidad

**Responsable:** David · **Pareja:** Jacobo · **Fecha:** 2026-10-29
**Rúbrica que cubre:** Concurrencia y consistencia (10), Anexo de concurrencia (3), Conmutación y alta disponibilidad (3), Ingreso al estadio sin internet (2).
**Modelo de datos:** el de Jacobo (`../Proyecto-BoletaYa-Jacobo/jacobo/`). No se rediseñan claves.

## Archivos

| Archivo | Contenido | Estado |
|---|---|---|
| [`respuesta_a_jacobo.md`](respuesta_a_jacobo.md) | Validación de claves, `:skew`, máximo de sillas, reintentos, dos correcciones de sintaxis, postura sobre D-2 | Listo (semana 1) |
| [`concurrencia.md`](concurrencia.md) | Transacciones de bloqueo, pago y confirmación; pagos sin registro; contención; antibots; referencias D-xx | Listo (semana 1) |
| [`anexo_concurrencia.md`](anexo_concurrencia.md) | Los 4 escenarios con pseudocódigo y línea de tiempo | Los 4 listos |
| [`alta_disponibilidad.md`](alta_disponibilidad.md) | Replicación, MREC/MRSC, tiempos de conmutación, RPO 0 por zona y por región, confirmación en modo desastre | Listo (borrador para revisión) |
| [`respuesta_a_miguel.md`](respuesta_a_miguel.md) | Condiciones de D-2 aceptadas y cambios al runbook 2b | Listo |
| [`estadio.md`](estadio.md) | Nodo por puerta como autoridad, doble ingreso entre puertas, fallas, sincronización con DynamoDB, equipo para Juan Pablo | Listo (borrador para revisión) |

## Pendientes

* Jacobo: aplicar las correcciones de `respuesta_a_jacobo.md` §3.
* Miguel: aplicar `respuesta_a_miguel.md` al runbook 2b.
* Jacobo y Juan Pablo: pre-calentar y costear las réplicas (`alta_disponibilidad.md` §7).
* Miguel, Jacobo, David: elegir pasarela (idempotencia, metadatos, listado por fechas).
* Samuel: confirmar la devolución del cupo al expirar un bloqueo (`:max` = 10 ya acordado).
* Profesor: P-4 ("pérdida total del sitio").
* Jacobo: activar Streams en `bya_tickets` y guardar la puerta asignada por localidad en `bya_catalog` (`estadio.md` §4).
* Juan Pablo: costear el equipo de `estadio.md` §9.
* Grupo: decidir los riesgos E-R1 y E-R2 de `estadio.md` §8.
