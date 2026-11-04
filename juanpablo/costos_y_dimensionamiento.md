# Costos y dimensionamiento — BoletaYa SAS

**Responsable:** Juan Pablo · **Consulta de precios:** 3-nov-2026 · **Moneda de control:** COP · **TRM académica:** COP 4.000/USD.

## 1. Criterio de cálculo

Se separan (a) valores reproducibles del modelo de Jacobo, (b) precios públicos consultados y (c) conceptos pendientes de cotización. No se asigna un precio ficticio a hardware, enlaces, cola virtual ni licencias cuyo importe no esté publicado o cuya configuración no esté cerrada.

Los presupuestos de control son **COP 280.000.000 para el año 1** y **COP 130.000.000 por año para los años 2–5**. La reserva de 10 % se muestra aparte. El IVA se aplica solo cuando la condición comercial lo exige; no se suma dos veces a precios publicados con IVA incluido.

## 2. Parámetros heredados

| Parámetro | Valor |
|---|---:|
| TRM | 4.000 COP/USD |
| IVA | 19 % |
| PUE | 1,8 |
| Energía | 900 COP/kWh |
| Administración/DBA | 120.000 COP/h |
| DBA por preventa | 6 h |
| Preventas grandes/año | 25 |
| Reserva | 10 % |
| Presupuesto año 1 | 280.000.000 COP |
| Presupuesto anual años 2–5 | 130.000.000 COP |

## 3. Arquitectura presupuestada

- **Escenario A:** ruta crítica en AWS: CloudFront → cola virtual → API/aplicación → DynamoDB on-demand, caché, S3/Athena y región alterna. Bogotá conserva administración y tareas de gestión.
- **Escenario B:** aplicación, caché local y solución de estadio en Bogotá; DynamoDB y estado de la cola virtual siguen en AWS. Enlace principal Direct Connect en Equinix BG1 + VPN y enlace redundante. Aplicación en espera en AWS.
- DynamoDB no se presupuesta como software instalable on-premise: es un servicio administrado de AWS. B es híbrido y depende de aprobación del profesor (P-1).

## 4. Capa de datos: cifras de Jacobo

La salida de `jacobo/calculos/modelo_capacidad.py` indica para `us-east-1`:

| Año | Throughput | Almacenamiento | PITR | Exportaciones | S3 | Total USD/año |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 83 | 144 | 115 | 6 | 0 | **348** |
| 2 | 99 | 312 | 250 | 8 | 0 | **670** |
| 3 | 120 | 407 | 326 | 11 | 9 | **874** |
| 4 | 147 | 532 | 426 | 14 | 21 | **1.140** |
| 5 | 183 | 695 | 556 | 18 | 36 | **1.489** |

La alternativa `sa-east-1` del mismo modelo es USD 523 en año 1 y USD 2.242 en año 5. El modelo recomienda on-demand + caché/CDN, no provisionar fijo al pico. Las cifras de la tabla son el modelo de Jacobo, no una cotización de la calculadora.

### 4.1 Réplica us-east-2

Las escrituras replicadas se cobran por región de réplica. La documentación oficial indica que cada región con réplica incurre en rWRU y que la replicación de Global Tables no tiene cargo separado de transferencia interregional. Con 123,4 M rWRU en año 1 y 277,7 M en año 5, usando USD 0,625 por millón como tarifa de referencia de us-east-1/us-east-2:

- Año 1: 123,4 × 0,625 = **USD 77,13** = **COP 308.500**.
- Año 5: 277,7 × 0,625 = **USD 173,56** = **COP 694.240**.

Además de las escrituras, se agrega el almacenamiento de la réplica (USD 144 en año 1; USD 695 en año 5) y PITR activado manualmente en us-east-2 (USD 115 en año 1; USD 556 en año 5), con las cifras del modelo de Jacobo. La réplica de almacenamiento y PITR suma USD 259 en año 1 y USD 1.251 en año 5.

Se usa la cota superior de WRU de Jacobo; no se descuenta el posible ajuste por transacciones/GSI hasta que el equipo confirme el conteo exacto. Las escrituras GSI se facturan como unidades locales adicionales según la documentación de Global Tables. No se suma una transferencia entre regiones por la replicación propia de Global Tables.

### 4.2 Warm throughput

Jacobo fija como objetivo de precalentamiento aproximado 6.000 WRU/s para `bya_seats`, `bya_orders` y sus GSI; 3.000 para `bya_counters`; 1.500 para `bya_tickets`. El mensaje de equipo propone 10.000 unidades incrementales a USD 0,00065/unidad como cálculo de referencia: USD 6,50 por región. Como la documentación confirma que el warm throughput se aplica automáticamente a las réplicas de una tabla global, pero el equipo no ha confirmado si el cargo se liquida una o dos veces, se conserva el supuesto prudente de **USD 13 (COP 52.000) como cargo único total** y se etiqueta como estimación pendiente de validar en Pricing Calculator. No es un cargo anual recurrente.

AWS no publica un plazo fijo de finalización: depende del tamaño y del valor solicitado. Ejecutar con al menos 24 h de anticipación es una recomendación operativa conservadora, no un SLA.

## 5. Respaldos y recuperación (datos de Miguel)

Los tamaños de respaldo provienen de `miguel/lista_componentes_para_juan_pablo.md`. Se incluyen:

- PITR 35 días en las ocho tablas en `us-east-1` y PITR activado manualmente en `us-east-2` (no se replica automáticamente la configuración PITR).
- AWS Backup diario 35 días para siete tablas; mensual 13 meses para tablas críticas. Opción horaria (24 puntos/día) solo para comparar, no como base aprobada.
- Copias a `us-east-2` y a cuenta separada; Vault Lock en modo cumplimiento tras prueba de gobernanza; llave KMS independiente (compartida con Samuel).
- Exportación incremental diaria a S3, versionado/Object Lock y S3 RTC; Athena para archivo frío.
- Cuatro pruebas de restauración al año; almacenamiento temporal de tablas restauradas por un día.

Tarifas publicadas por AWS DynamoDB: PITR USD 0,20/GB-mes; backup on-demand USD 0,10/GB-mes; restore USD 0,15/GB. AWS Backup factura almacenamiento, transferencias entre regiones y restauraciones. La hoja `Respaldo` cuantifica las 35 copias diarias y 13 mensuales como cota superior suponiendo que cada punto fuese completo; el precio exacto de AWS Backup para DynamoDB y el efecto de incrementalidad deben verificarse en la calculadora antes de incorporar el importe al costo base. El costo real de puntos incrementales depende del consumo facturable; no multiplicar mecánicamente 35 veces el tamaño de la tabla sin validar incrementalidad y retención en la calculadora. La hoja deja los volúmenes y tarifas separados para evitar sobrecostear por duplicación.

## 6. Capa de aplicación, cola, CDN y observabilidad

- CloudFront: el modelo de Jacobo usa la zona **South America** y 3 KB por consulta. Para 25 preventas/año, el escenario moderado da aproximadamente USD 632/año; alto USD 1.898; extremo USD 6.325. Es una estimación heredada del modelo, dependiente de 10 M/30 M/100 M solicitudes por preventa; debe confirmarse con el precio exacto por solicitudes y GB en la calculadora.
- Cola virtual: no confundir SQS (cola de mensajes interna) con la sala de espera de 250.000 usuarios. La sala requiere control de admisión, tokens/orden y estado persistente. Comparar construcción propia con proveedor comercial. No hay proveedor ni cotización elegidos: importe **PENDIENTE**.
- Streams/Lambda/KMS/CloudWatch/CloudTrail: requieren métricas de lecturas, invocaciones, duración, logs ingeridos/almacenados, claves y solicitudes. La lectura del trigger Lambda no se cobra como lector adicional de Streams; otros lectores sí. Samuel debe confirmar KMS/CloudTrail.
- Route 53: incluir zona hospedada, health checks y consultas DNS según la configuración final.

## 7. Conectividad

AWS confirma que Equinix BG1 Bogotá es ubicación de Direct Connect y que existen conexiones dedicadas 1 Gbps y 10 Gbps. El precio AWS de puerto dedicado es USD 0,30/h para 1 Gbps, pero el puerto, cross-connect, circuito local, instalación y transporte deben cotizarse con Equinix/partner. El servicio de AWS no representa el costo total de conectividad. VPN Site-to-Site se costea por túnel-hora y transferencia de datos según región; el proveedor de internet de respaldo también requiere cotización.

**No se asigna un costo de Direct Connect BG1 inventado.** En el Excel se deja una celda para la tarifa del partner y se calcula automáticamente el puerto AWS cuando se seleccione capacidad.

## 8. CAPEX del estadio (David §9)

David define 2 servidores centrales, 15 mini PC de puerta (12 activos + 3 repuestos), 48 torniquetes/lectores QR fijos, 24 lectores portátiles, 12 switches PoE, 2 switches de núcleo, 14 UPS, 1 router dual-WAN, un plan 4G/5G y un lote de rack/cableado/instalación.

Referencia comercial verificable para un servidor 1U que cumple 8 núcleos y 32 GB: Dell PowerEdge R360, precio publicado COP 32.308.000; ficha comercial indica 8 núcleos, 32 GB ECC, SSD configurables en RAID y doble fuente. El IVA y la garantía exacta del vendedor deben confirmarse en cotización. CAPEX preliminar de dos unidades: COP 64.616.000 antes de cualquier IVA adicional no incluido en el precio. No se presume que el precio incluya soporte de 5 años: exigir cotización escrita.

No se encontraron precios públicos comparables con especificación exacta para torniquete/lector PoE, UPS de autonomía 2 h, switches PoE/núcleo, router, cableado y 4G/5G. Se dejan pendientes de cotización. No cerrar el CAPEX total del estadio hasta tenerlos.

## 9. Energía del data center

Para cargas alojadas en un data center se usa **kW IT × 8.760 h/año × PUE 1,8 × COP 900/kWh**. La potencia real debe salir de fichas técnicas y medición. Esta fórmula no se aplica a los equipos del estadio: allí se usa el horario real de eventos, sin PUE, como se detalla en `escenario_b_hibrido.md` §3.

## 10. Administración y TCO

- DBA por preventa: 25 × 6 h × COP 120.000 = **COP 18.000.000/año**.
- Pruebas/simulacros/mantenimiento de respaldo (Miguel): 68 h × COP 120.000 = **COP 8.160.000/año**.
- Actualizaciones de runtime/SDK en cinco años: 104 h × COP 120.000 = **COP 12.480.000**.
- Migración PostgreSQL del estadio: 24 h × COP 120.000 = **COP 2.880.000**.
- Ubuntu Pro: precio oficial USD 500/servidor/año y USD 25/workstation/año. Alternativa estimada para dos servidores + doce nodos como workstation: USD 1.300 por un año (COP 5.200.000). Clasificación de los nodos y año de contratación requieren confirmación; no incluir 14 licencias de servidor automáticamente.

Ubuntu Pro se incorpora también al TCO y al OPEX del Escenario B: COP 5.200.000/año como supuesto para 2 servidores y 12 nodos activos. La comisión de Mercado Pago se incorpora como costo variable anual y en el TCO; el Excel la deja sin valor calculado hasta ingresar el valor promedio por orden.

Las horas de administración se incluyen en el TCO, pero se muestran aparte del gasto cloud/CAPEX y del control presupuestal de caja del año 1, conforme al plan individual.

## 11. Verificación presupuestal

**Conclusión a 3-nov-2026: no es responsable certificar todavía que A y B caben en COP 280 M / COP 130 M.** Sí se puede afirmar que la capa de datos calculada por Jacobo es baja (USD 348/año para us-east-1 en año 1, más unos USD 77 de escrituras replicadas), pero faltan cotizaciones que pueden dominar el total: cola virtual, Direct Connect/partner y circuito, hardware completo del estadio, conectividad redundante, CloudFront definitivo, respaldos/copia inmutable y sitio alterno.

La hoja presenta **un total parcial independiente para A y otro para B**. Cada uno suma los rubros comunes y los exclusivos del escenario, excluye filas de sensibilidad y horas TCO, y lo compara con el presupuesto. Los rubros aún sin precio quedan vacíos: no presentar el saldo aparente como prueba de cumplimiento hasta cerrar cotizaciones.

## 12. Decisiones y pendientes que deben cerrarse

**Pasarela elegida (D-11): Mercado Pago.** La decisión fue tomada por Miguel, Jacobo y David el 3-nov-2026. La integración usa `X-Idempotency-Key`, `metadata` con evento/usuario/sillas y búsqueda de pagos por rango de fechas. Siguen pendientes las pruebas de sandbox de `metadata` y de repetición idempotente. Si `metadata` no conserva y devuelve el objeto, activar `bya_ledger` según `david/pasarelas.md`.

1. Profesor: P-1, aceptación de Escenario B híbrido con DynamoDB en AWS.
2. Profesor: P-3, ubicación física obligatoria de aplicación en A.
3. Profesor: P-8, formato exigido de captura/exportación de AWS Pricing Calculator.
4. Proveedor: precio de sala de espera para 250.000 usuarios, SLA, ráfaga y retención.
5. Equinix/partner: puerto BG1, cross-connect, circuito, instalación y redundancia.
6. **Asistente:** investigar y consolidar precios/cotizaciones de los equipos del estadio a partir de `david/estadio.md` §9. Juan Pablo valida compatibilidad técnica; David confirma las especificaciones que ya definió.
7. Samuel: retención legal, KMS/CloudTrail y clase de Ubuntu Pro de los nodos.
8. **Juan Pablo:** confirmar en la cuenta/simulador de Mercado Pago la comisión del Checkout elegido y el plazo de disponibilidad; ingresar además el valor promedio de orden para completar el costo. El Excel usa provisionalmente 3,29 % + COP 800 por cobro + IVA (disponibilidad inmediata), como referencia secundaria, no como tarifa contractual.
9. Miguel, Jacobo y David: completar las pruebas de sandbox de Mercado Pago (metadata e idempotencia).
