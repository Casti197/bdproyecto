# BoletaYa SAS — Parte de Jacobo: datos, capacidad y arquitectura (DynamoDB en AWS)

**Responsable:** Jacobo · **Pareja:** David · **Motor / nube asignados:** Amazon DynamoDB / AWS · **Fecha:** 2026-10-29 · **Revisión:** 2026-11-03 (tras las revisiones de David y Miguel)
**Rúbrica que cubre:** Capacidad y manejo del pico (15 %), Arquitectura (10 %), y la base del modelo de datos de la que dependen Concurrencia, Recuperación, Costos y Seguridad.

> No se creó, compró, instaló ni probó ninguna infraestructura (regla del enunciado). **No hay resultados de pruebas de rendimiento.** Todo número viene de un script reproducible o de una fuente oficial con fecha de consulta; lo que no pude verificar está declarado como **pendiente**.

---

## 1. Resumen ejecutivo

1. **El pico lo manda todo.** La operación normal (8.000 boletas/día) son 0,056 órdenes/s ≈ 3,5 WRU/s. La preventa (60.000 boletas en 20 min) son 24.000 órdenes, **20/s**, y cada orden cuesta **55,3 WRU** en el mínimo y **84,4** en el escenario de planificación (**182,9** en estrés): **≈ 1.690 WRU/s** promedio y **≈ 8.440 WRU/s** en una ráfaga ×5.
2. **El mapa de sillas no puede salir de la base.** 250.000 personas sondeando cada 10 s son 25.000 req/s = 687.500 RRU/s = **17,2×** la cuota de una tabla. Con instantáneas en CDN, la base ve ≈ 450 RRU/s.
3. **Modelo:** **8 tablas** especializadas (no una sola): `bya_seats` (sin GSI, partición por evento#localidad#fila), `bya_orders` (orden + pagos + factura), `bya_counters`, `bya_tickets`, `bya_catalog`, `bya_users`, `bya_seat_history`, `bya_audit`.
4. **Contador exacto:** fragmentado (N = 8) **dentro de la misma transacción** que marca la silla vendida: exacto y atómico con cada venta. Exactitud ≠ frescura (distinción explicada).
5. **Capacidad:** **on-demand + pre-calentamiento** (año 1: USD 83–124 de throughput al año; provisionado programado USD 880–1.319; provisionado fijo USD 63.176–94.764). La capa de datos completa cuesta ≈ USD 348–523 en el año 1 y ≈ 1.489–2.242 en el año 5.
6. **Región:** **us-east-1** (≈ 77 ms desde Bogotá vs ≈ 112 ms de São Paulo, medición de un tercero; −33 % de precio); alterna **us-east-2**.
7. **Hallazgo crítico:** **RPO 0 ante pérdida de región no es alcanzable con transacciones** (MRSC no soporta transacciones ni TTL; MREC es asíncrono). Propuesta: una sola región escribe y conciliación con la pasarela. **Afecta a David, Miguel y Samuel.**
8. **Escenario B:** DynamoDB **no se instala en el data center**. Variante híbrida (aplicación, caché y estadio en Bogotá; base **y estado de la cola virtual** en AWS por Direct Connect) **pendiente de confirmación del profesor**. La venta se conmuta por DNS o a mano: **CloudFront no conmuta `POST`**.
9. **Revisión cruzada (2026-11-03):** David aprobó el modelo (D-1) y fijó `:skew` = 2 s, 10 sillas y reintentos; corregí dos condiciones que usaban aritmética (no permitida en una `ConditionExpression`). Miguel aceptó D-2 con dos condiciones (sillas del pago como metadato del cobro o libro de pagos MRSC; conciliación de desastre desde la pasarela). Detalle en `respuesta_a_revisiones.md`.

## 2. Decisiones principales

| # | Decisión | Documento |
|---|---|---|
| D1 | 8 tablas especializadas; sin GSI en sillas | `modelo_datos.md` §2–§4 |
| D2 | Contador fragmentado en la transacción de venta | `modelo_datos.md` §5 |
| D3 | Bloqueo de 8 min en la silla; el TTL solo limpia | `modelo_datos.md` §3.2, §7 |
| D4 | Mapa por CDN/instantáneas; transacción para comprar | `capacidad_y_volumetria.md` §6 |
| D5 | On-demand + pre-calentamiento + máximo de throughput | `capacidad_y_volumetria.md` §7 |
| D6 | `us-east-1` + `us-east-2` (réplica MREC en espera, una región escribe) | `arquitectura.md` §1, §4.1 |
| D7 | Historial por Streams; auditoría administrativa síncrona | `modelo_datos.md` §3.6, §6.3 |
| D8 | Escenarios: A (ruta crítica en AWS) y B (híbrido literal; cola con estado en AWS) | `arquitectura.md` §2–§3 |
| D9 | Libro de pagos MRSC **opcional** (plan B de D-2); decisión depende de la pasarela (D-11) | `modelo_datos.md` §3.9 |

## 3. Índice de entregables

| Archivo | Contenido |
|---|---|
| [`README.md`](README.md) | Este resumen, supuestos y pendientes |
| [`modelo_datos.md`](modelo_datos.md) | 20 patrones de acceso, una tabla vs varias, 8 tablas (PK, SK, GSI, ejemplos, consultas), particiones calientes, contador exacto (3 opciones), historial, auditoría, TTL, exportación a S3 + Athena, transacción para David, validación |
| [`capacidad_y_volumetria.md`](capacidad_y_volumetria.md) | Volumetría años 1–5 con fórmulas, almacenamiento (crudo, facturado, índices, S3), carga normal, preventa, RCU/WCU con ejemplos, sensibilidades, mapa de sillas y cola, on-demand vs provisionado vs híbrida, datos para Juan Pablo |
| [`arquitectura.md`](arquitectura.md) | Región y latencia, Escenario A y B con diagramas Mermaid, recorrido de una compra, alta disponibilidad, conectividad, estadio |
| [`entrega_para_el_equipo.md`](entrega_para_el_equipo.md) | Interfaces con David, Juan Pablo, Miguel y Samuel; decisiones a aprobar; contradicciones; preguntas al profesor |
| [`respuesta_a_revisiones.md`](respuesta_a_revisiones.md) | Qué acepté y cambié tras las revisiones de David y Miguel (2 correcciones de sintaxis, 7 hallazgos, pedidos a Jacobo) y qué sigue abierto |
| [`referencias.md`](referencias.md) | 42 fuentes con URL, tema, datos concretos y fecha de consulta; lista de lo no verificado |
| [`resumen_sustentacion.md`](resumen_sustentacion.md) | Explicación en lenguaje claro, preguntas difíciles y errores a evitar |
| [`calculos/`](calculos/) | `modelo_capacidad.py` (reproduce todas las cifras), `salida_modelo.md` (su salida), `evidencia/` (listas de precios oficiales y extracto de latencia) |

**Reproducir las cifras:** `python3 -I jacobo/calculos/modelo_capacidad.py`

## 4. Supuestos (los míos; ninguno se presenta como dato del profesor)

| ID | Supuesto | Impacto |
|---|---|---|
| A-01 | Los eventos crecen **30 %**/año (como las boletas). Si fueran constantes, la ocupación pasaría a 96 % (año 2), 125 % (año 3) y 212 % (año 5) | Sillas e historial |
| A-02 | La auditoría crece 30 %/año (el enunciado da 5 M/mes sin crecimiento) | Mitad del almacenamiento |
| A-03 | Sobrecarga de almacenamiento: 100 B por ítem de tabla (AWS ya no publica la cifra; 100 B es el valor documentado de los GSI) | ±10 % del almacenamiento |
| A-04 | Retención en línea: órdenes/pagos/boletas/facturas/historial/auditoría 2 años; escaneos 1 año; sillas hasta 90 días tras el evento. **Sujeta a validación legal** | Almacenamiento y archivo |
| A-05 | "Usuarios 2,5 M" son existencias acumuladas | Tamaño de usuarios |
| A-06 | CloudFront factura Colombia en la zona "South America" | Costo del mapa |
| A-07 | 5 % de los registros de auditoría son acciones humanas (índice disperso por actor) | Índice de auditoría |
| A-08 | Zonas sin numeración se modelan con filas virtuales de ≤ 50 cupos | Claves de sillas |
| A-09 | Máx. 10 sillas por orden | Transacción (≤ 100 ítems) |
| A-10 | Planificación: 2 bloqueos fallidos por exitoso y 30 % de órdenes abandonadas; estrés: 8 y 50 % | Pico de escritura |
| A-11 | Mapa: sondeo cada 3/10/30 s, 20 min, 3 KB por consulta, TTL 2 s | Costo del mapa |
| A-12 | Acceso a DynamoDB dentro de la región ≈ 5 ms por llamada | Latencia de compra |
| — | Pico instantáneo ×5 (las 60.000 boletas en 4 min) y margen +25 % (el enunciado no da la distribución dentro de los 20 min) | Dimensionamiento |

## 5. Contradicciones del enunciado detectadas

| # | Contradicción | Resolución |
|---|---|---|
| C-1 | 60.000 boletas por preventa > 45.000 sillas de un estadio | Lanzamiento de varias fechas o festival; el modelo cubre el peor caso (P-2) |
| C-2 | 8.000/día × 365 + 25 × 60.000 = 4,42 M ≠ 4,0 M de la tabla | Almacenamiento con 4,0 M; carga con 8.000 y 60.000 |
| C-3 | "100 ventas por minuto" vs. 8,3 boletas/min | Se usa §3; sensibilidad incluida |
| C-4 / C-5 | Pide CPU/IOPS y "compresión y espacio libre"; DynamoDB no los tiene | RCU/WCU; compresión 1:1; sin espacio libre |
| C-6 / C-7 | ¿Usuarios nuevos o acumulados? ¿"Al menos un rechazo" = un rechazo? | A-05; k = 1 en base y sensibilidad k = 2, 3 |
| X-1…X-9 | Ver `entrega_para_el_equipo.md` §6 (RPO 0 entre regiones, réplicas de lectura, escenarios A/B, auditoría con Streams) | Propuestas allí |

## 6. Pendientes y preguntas abiertas

**Para el grupo:** D-11 elegir la pasarela de pagos (de ella depende D-2, opción A o B).

**Para el profesor:** P-1 (escenario B con DynamoDB), P-2 (60.000 vs 45.000), P-3 (¿la aplicación en el DC en A?), P-4 ("pérdida total del sitio" y RPO 0 con transacciones), P-5 (cola virtual comercial), P-6 (región fuera de Colombia), P-7 ("niveles de almacenamiento"), P-8 (captura de la calculadora). Detalle en `entrega_para_el_equipo.md` §7.

**No verificado** (ver `referencias.md` §H): sobrecarga por ítem de tabla; facturación de GSI en transacciones; monto y duración del pre-calentamiento; frecuencia de conflictos de transacción; precio de lecturas de Streams y de Lambda/KMS/CloudWatch; latencia a us-east-2 y por Direct Connect; tarifa de CloudFront para Colombia; costo de la cola virtual; Direct Connect.

## 7. Riesgos que podrían invalidar la propuesta

1. **Región fuera de Colombia** y datos personales (Ley 1581): si no se acepta, `sa-east-1` (+35 ms, +50 % DynamoDB, sin MRSC).
2. **RPO 0 entre regiones con transacciones**: no existe en DynamoDB; la propuesta usa conciliación.
3. **Conflictos de transacción en sillas calientes** (no medidos).
4. **Costo del mapa en el año 5 con cola duplicada** (hasta USD 15.442/año ≈ 48 % del tope anual).
5. **Escenario B** depende de un enlace único hacia la base.
6. El producto de **cola virtual de AWS está discontinuado**; costo de la alternativa desconocido.

## 8. Verificación de coherencia realizada

(Revisión 2026-11-03: los 3 diagramas Mermaid se volvieron a renderizar tras los cambios; las referencias `[R-xx]` siguen coincidiendo con `referencias.md`.)

Fórmulas y unidades recomputadas con el script; 1,6 M × 2,5 = 4,0 M; 24.000 × 2,5 = 60.000; desglose por operación = suma por tabla (55,3 y 84,4); las claves soportan los 20 patrones sin `Scan`; los diagramas coinciden con los componentes explicados; cada precio lleva fuente, moneda (USD) y fecha (2026-10-29); las referencias `[R-xx]` existen en `referencias.md`.
