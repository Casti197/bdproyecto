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
| [`preguntas_para_el_cliente.md`](preguntas_para_el_cliente.md) | 64 preguntas en lenguaje de negocio para el profesor (cliente) | Listo |
| [`preguntas_para_el_profesor.md`](preguntas_para_el_profesor.md) | Versión técnica, numeración P-1 a P-67 | Listo |
| [`pruebas/`](pruebas/) | Prueba de las transacciones en un simulador (moto): 37 casos, resultado en `resultado.txt`; verificador de invariantes para el simulacro | Listo |
| [`estadio.md`](estadio.md) | Nodo por puerta como autoridad, doble ingreso entre puertas, fallas, sincronización con DynamoDB, equipo para Juan Pablo | Listo (borrador para revisión) |

## Pendientes

**Míos (David)**
* Esperar las respuestas del profesor (preguntas ya enviadas) y ajustar los documentos.
* Entregar a Miguel el verificador de `pruebas/` para su simulacro de conmutación.

**De otros**
* Jacobo: aplicar las correcciones de `respuesta_a_jacobo.md` §3; activar Streams en `bya_tickets` y guardar la puerta por localidad en `bya_catalog` (`estadio.md` §4); pre-calentar las réplicas (`alta_disponibilidad.md` §7).
* Miguel: aplicar `respuesta_a_miguel.md` al runbook 2b.
* Samuel: confirmar la devolución del cupo al expirar un bloqueo (`:max` = 10 ya acordado).
* Juan Pablo: costear el equipo de `estadio.md` §9, las réplicas, Ubuntu Pro o el cambio de versión de Ubuntu y una migración de PostgreSQL hacia 2030 (§9.1, con precios).

**Entre varios**
* Miguel, Jacobo y David: elegir la pasarela de pagos (llave de idempotencia, metadatos en el cobro, listado por fechas).
* Grupo: decidir los riesgos E-R1 y E-R2 de `estadio.md` §8.
