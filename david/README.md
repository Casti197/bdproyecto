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
| [`pruebas/`](pruebas/) | Prueba de las transacciones en un simulador (moto): 46 casos, resultado en `resultado.txt`; verificador de invariantes para el simulacro | Listo |
| [`respuestas_profesor.md`](respuestas_profesor.md) | Las 7 respuestas del profesor (2026-11-04) y a quién le toca cada una | Registrado |
| [`pasarelas.md`](pasarelas.md) | Comparación de pasarelas para D-11; elegida Mercado Pago | Decidido |
| [`estadio.md`](estadio.md) | Nodo por puerta como autoridad, doble ingreso entre puertas, fallas, sincronización con DynamoDB, equipo para Juan Pablo | Listo (borrador para revisión) |

## Pendientes

**Míos (David)**
* Hecho el 2026-11-04: respuestas 3, 5, 6 y 7 del profesor aplicadas a mis documentos.
* Entregar a Miguel el verificador de `pruebas/` para su simulacro de conmutación.

**De otros**
* Jacobo: aplicar las correcciones de `respuesta_a_jacobo.md` §3; activar Streams en `bya_tickets` y guardar la puerta por localidad en `bya_catalog` (`estadio.md` §4). **Hecho el 2026-11-03** (`jacobo/respuesta_a_revisiones.md`); el pre-calentamiento de réplicas es automático.
* Miguel: **hecho el 2026-11-03** (runbook 2b de 10 pasos, RTO de 7 a 13 min, o de 7 a 16 sin traslape).
* Samuel: confirmar la devolución del cupo al expirar un bloqueo (`:max` = 10 ya acordado).
* Juan Pablo: costear el equipo de `estadio.md` §9, las réplicas, Ubuntu Pro o el cambio de versión de Ubuntu y una migración de PostgreSQL hacia 2030 (§9.1, con precios).

* Juan Pablo: mostrar el Escenario B con la opción 1 (torniquetes propios) y la 2 (usar los del estadio) de `estadio.md` §9.2; corregir el signo del "Saldo" del Resumen; cobrar Ubuntu Pro solo el último año.

* Jacobo: sección de máximo 2 páginas sobre por qué DynamoDB no va *on premise* y si hay alternativa compatible (respuesta 1); Escenario A todo en AWS (respuesta 2); AWS en Colombia y latencia desde Bogotá (respuesta 4).
* Miguel: runbook 2b y tabla de RTO con el congelamiento de sillas en duda (`alta_disponibilidad.md` §3.3 y §5.0); carta del estadio de 40 min a 4 h (respuesta 7).
* Samuel: análisis de transferencia internacional de la Ley 1581 (respuesta 4).
* Juan Pablo: comparar A (todo en AWS) contra B en latencia, conectividad, egress y costos (respuesta 2).

**Entre varios**
* Miguel, Jacobo y David: D-11 **decidida: Mercado Pago** (2026-11-03). Falta comprobar en el sandbox `metadata` y `X-Idempotency-Key` (`pasarelas.md` §2).
* Grupo: decidir los riesgos E-R1 y E-R2 de `estadio.md` §8 y la opción de equipo de puerta de §9.2 (la pregunta 45 sigue sin respuesta).
