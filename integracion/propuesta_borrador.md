# Propuesta escrita — BORRADOR INTEGRADO

**Estado:** borrador de integración del 2026-11-04, armado solo con lo que ya está en el repositorio. **No es el texto final:** es el esqueleto del PDF de máximo 25 páginas (sin anexos), con el contenido de cada frente resumido desde la carpeta de su dueño, las cifras clave y lo que falta. El armado final del PDF es de **Samuel**.
**Cómo usarlo:** cada sección dice de qué archivo sale. Si algo de aquí no coincide con tu carpeta, manda tu carpeta: corrígelo allá y avisa, no aquí.

**Leyenda:** ✅ hay material suficiente · 🟡 hay material con huecos · ❌ falta el material

## Presupuesto de páginas (25 sin anexos)

| Sección | Páginas | Estado |
|---|---|---|
| 0. Resumen ejecutivo y recomendación | 1 | 🟡 falta la recomendación final |
| 1. Contexto, supuestos y contradicciones del enunciado | 1 | ✅ |
| 2. Escenarios A y B (incluye la sección de 2 páginas sobre DynamoDB *on premise*) | 3 | 🟡 |
| 3. Capacidad (5.1) | 3 | ✅ |
| 4. Concurrencia y consistencia (5.2) | 3 | ✅ |
| 5. Versiones y licenciamiento (5.3) | 1,5 | ✅ |
| 6. Arquitectura (5.4) | 3 | 🟡 |
| 7. Recuperación (5.5) | 3 | 🟡 |
| 8. Seguridad y cumplimiento (5.6) | 2 | ❌ |
| 9. Costos (5.7) | 2 | ❌ no se puede cerrar sin cotizaciones |
| 10. Decisión final (5.8) | 1 | ❌ |
| 11. Respuesta a la carta de evento | 1,5 | ❌ aún no llega |
| **Total** | **25** | |

**Anexos (no cuentan en las 25):** A. Registro de decisiones (`integracion/registro_decisiones.md`) · B. Análisis de concurrencia (`david/anexo_concurrencia.md`) · C. Estudio de conmutación (`david/alta_disponibilidad.md`) · D. Modelo de datos completo (`jacobo/modelo_datos.md`) · E. Volumetría y fórmulas (`jacobo/capacidad_y_volumetria.md`) · F. Runbooks (`miguel/recuperacion_licenciamiento_carta.md` §5.5) · G. Referencias (`jacobo/referencias.md` y las de cada carpeta).

---

## 0. Resumen ejecutivo (1 página) 🟡

* **Motor y nube asignados:** Amazon DynamoDB en AWS.
* **Escenario A:** todo en AWS (aplicación y base); el estadio es local. **Escenario B:** híbrido aceptado por el profesor: aplicación, caché y estadio en Bogotá; base en AWS por Direct Connect.
* **El pico manda:** 24.000 órdenes en 20 minutos, unas 20 por segundo. DynamoDB on-demand con pre-calentamiento lo absorbe por unos USD 83 de throughput al año (año 1, us-east-1).
* **Cero doble venta:** escritura condicional dentro de una transacción todo o nada; 50 de 50 casos pasan en un simulador.
* **Pérdida de región:** una sola región escribe; se congelan las sillas en duda y se reabre en 4 a 11 minutos estimados (sin medir); el RPO 0 de pagos sale de la conciliación con Mercado Pago.
* **Lo que falta para recomendar:** el costo total de cada escenario. La capa de datos es barata; lo caro es el equipo del estadio, la cola virtual y la conectividad, todavía sin cotizar.
* **Recomendación:** ❌ pendiente de la sección 10.

## 1. Contexto, supuestos y contradicciones (1 página) ✅

* Supuestos numerados A-01 a A-12: `jacobo/README.md` §4.
* Contradicciones del enunciado y cómo se resolvieron (60.000 boletas frente a 45.000 sillas; 4,42 M frente a 4,0 M boletas; "100 ventas por minuto" frente a 8,3; CPU e IOPS que DynamoDB no expone): `jacobo/README.md` §5 y `jacobo/entrega_para_el_equipo.md` §6.
* Respuestas del profesor del 2026-11-04 que fijan la interpretación: `david/respuestas_profesor.md`.

## 2. Escenarios A y B (3 páginas) 🟡

* Definición de cada escenario según el profesor (resp. 1 y 2): `david/respuestas_profesor.md`.
* **Por qué DynamoDB no va *on premise*** y evaluación de una alternativa compatible con su API (máximo 2 páginas, pedido explícito del profesor): ❌ **la escribe Jacobo**. Insumos ya existentes: `jacobo/resumen_sustentacion.md` P10 y `jacobo/arquitectura.md` §3.
* **Comparación A contra B en latencia por compra, conectividad con Bogotá, egress y costos** (resp. 2): 🟡 la latencia ya está (≈ 353 ms por compra en B frente a ≈ 22 ms en A, `jacobo/resumen_sustentacion.md` P18); faltan egress y costos (Juan Pablo).

## 3. Capacidad — 5.1 (3 páginas) ✅

Fuente: `jacobo/capacidad_y_volumetria.md`, `jacobo/calculos/salida_modelo.md`.

| Dato | Valor |
|---|---|
| Operación normal | 0,056 órdenes/s ≈ 3,5 WRU/s |
| Preventa | 24.000 órdenes en 20 min = 20/s; 55,3 WRU por orden (mínimo), 84,4 (planificación), 182,9 (estrés) |
| Pico de escritura | ≈ 1.690 WRU/s promedio; ≈ 8.440 WRU/s en ráfaga ×5; 10.546 con margen del 25 % |
| Mapa de sillas | 250.000 personas = 25.000 consultas/s = 17,2 × la cuota de una tabla; con instantáneas en CDN la base ve ≈ 450 RRU/s |
| Almacenamiento en línea | 48,0 GiB (año 1) a 231,8 GiB (año 5) |
| Opciones de pico, throughput año 1 (USD) | On-demand 83–124 · provisionado programado 880–1.319 · provisionado fijo 63.176–94.764 |

**Qué va a la base y qué no:** a la base, bloquear, confirmar, boletas, escaneos y contador; fuera de ella, el mapa (CDN), la posición en la cola, el catálogo (caché) y el histórico (S3 + Athena). `jacobo/resumen_sustentacion.md` P4.

## 4. Concurrencia y consistencia — 5.2 (3 páginas) ✅

Fuente: `david/concurrencia.md`, `david/anexo_concurrencia.md`, `david/estadio.md`.

* **Qué es doble venta** según el profesor (resp. 5): `david/concurrencia.md` §0.
* **Cómo se evita:** escritura condicional sobre el ítem de la silla dentro de `TransactWriteItems`; transacciones serializables entre sí; el bloqueo de 8 minutos vive en la silla y el TTL solo limpia. Ficha F-06.
* **Pago confirmado sin registro y al revés:** idempotencia (`X-Idempotency-Key = <oid>#<nn>`), estado del intento de pago, reconciliador cada minuto, SQS con cola de fallidos. `david/concurrencia.md` §6.
* **Deadlocks:** no hay bloqueos que esperen; un choque cancela la transacción y se reintenta con *backoff* y *jitter* (máximo 3). `david/concurrencia.md` §7.
* **Antibots:** máximo 10 sillas por usuario y evento, en la misma transacción. `david/concurrencia.md` §8.
* **Estadio sin internet:** un nodo por puerta como autoridad, 4 horas aislado. Ficha F-13.
* **Evidencia:** 50 de 50 casos pasan en un simulador (moto). Aclarar en el texto que es un simulador local, no AWS real.

## 5. Versiones y licenciamiento — 5.3 (1,5 páginas) ✅

Fuente: `miguel/recuperacion_licenciamiento_carta.md` §5.3; `david/estadio.md` §9.1.

* DynamoDB no tiene versión, edición ni licencia por núcleo: escalar o replicar no agrega licencias.
* Lo que sí tiene fin de soporte: SDK de AWS, runtime (Node.js 24 hasta abril de 2028 o Python 3.14 hasta junio de 2029), ElastiCache para Valkey, y en el estadio Ubuntu 26.04 LTS (mayo de 2031) y PostgreSQL 18 (noviembre de 2030).
* Plan de actualización costeado: COP 15.360.000 en 5 años más Ubuntu Pro.
* Hueco: el lenguaje de la aplicación no está decidido (por eso hay dos runtimes).

## 6. Arquitectura — 5.4 (3 páginas) 🟡

Fuente: `jacobo/arquitectura.md` (diagramas Mermaid de A y B), `david/alta_disponibilidad.md` §2.

* Región us-east-1 (≈ 77 ms desde Bogotá) con alterna us-east-2. Ficha F-02.
* Alta disponibilidad: 3 zonas dentro de la región (RPO 0, SLA 99,99 %); MREC hacia us-east-2 con una sola región que escribe.
* La venta se conmuta por DNS o a mano: CloudFront no conmuta `POST`.
* **Hueco:** el diagrama del Escenario A debe reflejar que es todo en AWS (resp. 2 del profesor), y falta la verificación de AWS en Colombia (resp. 4). Ambas son de Jacobo.

## 7. Recuperación — 5.5 (3 páginas) 🟡

Fuente: `miguel/recuperacion_licenciamiento_carta.md` §5.5; `david/alta_disponibilidad.md` §3.

| Componente | Meta RPO / RTO | Alcanzado (estimado) |
|---|---|---|
| Venta, falla de zona | 0 / 15 min | 0 / sin conmutación |
| Venta, pérdida de región | 0 / 15 min | Pagos 0 con sillas en duda congeladas; RTO 4 a 8 min (4 a 11 en secuencia) desde la declaración; detección 2 a 5 min aparte |
| Venta, pérdida del data center (solo B) | 0 / 15 min | 0 / 3 a 11 min |
| Ingreso al evento | Nunca se detiene | RPO 0 y RTO 0 sin internet; 5 a 10 min si cae el nodo de una puerta |
| Usuarios y catálogo | 15 min / 4 h | Segundos con PITR / minutos a horas |
| Histórico | 24 h / 48 h | Hasta 24 h / horas |

* Respaldo: PITR 35 días, AWS Backup diario y mensual con copia a otra región y otra cuenta, Vault Lock. Ficha F-12.
* Respaldo sin afectar la preventa: según AWS, PITR, respaldos y exportaciones no consumen capacidad; aun así, congelamiento de cambios de 24 h antes a 3 h después de cada preventa y respaldos de madrugada.
* Runbooks 1, 2a, 2b, 2c y 3, y plan de pruebas (68 horas de DBA al año).
* **Hueco:** el paso 4 del runbook 2b todavía dice que las sillas en duda salen de la búsqueda de Mercado Pago; desde D-2b salen de `bya_ledger` (lo actualiza Miguel). Ningún tiempo está medido: decirlo en el texto.

## 8. Seguridad y cumplimiento — 5.6 (2 páginas) ❌

**Dueño: Samuel. No hay carpeta `samuel/` en el repositorio.** Insumos que ya preparó Jacobo para esta sección: `jacobo/entrega_para_el_equipo.md` §4 (datos a proteger, token de la pasarela, auditoría síncrona, Ley 1480, factura electrónica, PCI, región fuera de Colombia).

Lo que esta sección debe contener según la rúbrica:
* Roles y mínimo privilegio: aplicación, DBA, organizadores, soporte, auditores.
* Cifrado en reposo y en tránsito; gestión de llaves (KMS).
* Por qué el diseño queda fuera del alcance de PCI DSS (solo token) y verificación de que ningún log ni respaldo guarda la tarjeta.
* Auditoría antifraude de precios, cupos y sillas; enmascaramiento de datos personales.
* Antibots a nivel de base (ya hay límite por usuario: F-06).
* Ley 1581: transferencia internacional a EE. UU. (condición del profesor para aceptar la región).
* **Plazo de conservación según la norma tributaria, con la norma citada:** no aparece en ningún archivo del repositorio.

## 9. Costos — 5.7 (2 páginas) ❌

Fuente: `juanpablo/costos_boletaya.xlsx`, `juanpablo/costos_y_dimensionamiento.md`, `juanpablo/sensibilidad_y_tco.md`.

Totales parciales que da hoy la hoja (recalculada el 2026-11-04):

| | Año 1 | Año 5 | Estado |
|---|---|---|---|
| Escenario A | COP 5.318.500 | COP 14.184.250 | INCOMPLETO |
| Escenario B | COP 336.639.820 | COP 30.099.110 | INCOMPLETO; **ya supera el tope de 280 M** |

**Por qué no se puede cerrar todavía** (detalle en `integracion/pendientes_entrega.md`):
* Faltan cotizaciones de la cola virtual, Direct Connect y partner, VPN, AWS Backup, el resto del equipo del estadio y la Pricing Calculator.
* **El equipo del estadio solo está cargado en B**, pero el profesor dijo que el estadio es local en los dos escenarios. Si se carga también en A, A sube en el mismo monto.
* No hay líneas de cómputo de la aplicación (API, Lambda o contenedores, ElastiCache: USD 2.215 al año según Jacobo) en ninguno de los dos.
* En B, los torniquetes solos (COP 216,1 M) son casi dos tercios del total: ver ficha F-14.

## 10. Decisión final — 5.8 (1 página) ❌

Falta. Debe comparar A y B en costo, riesgo, RPO/RTO, manejo del pico, facilidad de operación y crecimiento, y recomendar uno (y, si aplica, el año en que conviene cambiar).
Lo que ya se puede decir con lo que hay, para que el grupo lo discuta:
* **Recuperación:** A es más simple (sin runbook 2c y sin depender del enlace Bogotá–AWS). `miguel/recuperacion_licenciamiento_carta.md`, final de la sección del Escenario B.
* **Latencia:** A ≈ 22 ms por compra frente a ≈ 353 ms en B.
* **Costo:** no se puede comparar hasta cerrar las cotizaciones y corregir la ubicación del estadio en la hoja.

## 11. Respuesta a la carta de evento (1,5 páginas) ❌

Llega en la semana 3. Plan de 72 horas: `miguel/recuperacion_licenciamiento_carta.md`, sección "Carta de evento".
