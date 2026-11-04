# Sensibilidad y TCO a cinco años

## 1. Base heredada

Jacobo calcula 25 preventas grandes/año, 60.000 boletas por preventa, 24.000 órdenes y 250.000 personas en cola en año 1. La cola crece ×1,25 por año hasta 610.352 en año 5. DynamoDB on-demand (us-east-1) cuesta USD 83/año de throughput en año 1 y USD 183 en año 5; capa de datos completa USD 348 y USD 1.489 respectivamente.

## 2. Doble de preventas

Si las preventas pasan de 25 a 50/año, las unidades de escritura atribuibles a preventa y los costes variables asociados aproximadamente se duplican. No se duplica automáticamente el almacenamiento histórico, PITR ni costes fijos: se recalculan con la política de retención, crecimiento de tablas y volumen de exportación. Para la réplica, la cota superior de escritura replicada sube de USD 77 a USD 154 en año 1 y de USD 174 a USD 347 en año 5, si el volumen anual de WRU crece en igual proporción (validar el script, pues el tráfico normal permanece).

## 3. Doble de personas en cola

La cola pasa de 250.000 a 500.000 personas en año 1 y de 610.352 a 1.220.704 en año 5. El modelo de Jacobo estima CloudFront por preventa:

| Caso | Solicitudes/preventa | USD/preventa | USD/año (25) | USD/año con 50 preventas |
|---|---:|---:|---:|---:|
| Moderado | 10 M | 25,3 | 632,5 | 1.265 |
| Alto | 30 M | 75,9 | 1.897,5 | 3.795 |
| Extremo | 100 M | 253,0 | 6.325 | 12.650 |

Para doble de usuarios concurrentes, si frecuencia de consulta y payload no cambian, las solicitudes y el egreso pueden duplicarse; CloudFront pasa aproximadamente al doble. La base DynamoDB no se duplica necesariamente: Jacobo diseñó instantáneas CDN y dejó carga residual de 450 RRU/s. Si TTL, tasa de refresco o payload cambian, recalcular.

## 4. TCO de administración

| Concepto | Horas | COP/h | COP |
|---|---:|---:|---:|
| DBA por preventas (25 × 6 h) | 150/año | 120.000 | 18.000.000/año |
| Pruebas, simulacros y mantenimiento respaldo (Miguel) | 68/año | 120.000 | 8.160.000/año |
| Actualizaciones runtime/SDK (104 h en cinco años) | 104 total | 120.000 | 12.480.000 total |
| Migración PostgreSQL estadio | 24 total | 120.000 | 2.880.000 total |
| Ubuntu Pro (2 servidores + 12 nodos activos) | 1.300 USD/año | TRM 4.000 | 5.200.000/año; confirmar clase workstation y soporte |
| Mercado Pago Checkout Pro | 600.000 órdenes/año (24.000 × 25) | 3,29 % + COP 800 por cobro + IVA (referencia) | Fórmula depende del valor promedio de la orden; se completa en Excel al ingresar ese dato |

La mano de obra de administración se incluye en el TCO pero se muestra separada del presupuesto de caja del año 1 según el plan individual. Ubuntu Pro y la comisión de Mercado Pago sí se incluyen como costos operativos; la comisión permanece pendiente del valor promedio por orden y de confirmar la tarifa de la cuenta. No sumar dos veces las 6 h/preventa y las 68 h de Miguel: son actividades distintas según su lista.

## 5. CAPEX vs OPEX

- **CAPEX:** servidores, nodos, torniquetes, lectores, switches, UPS, router, rack/cableado/instalación.
- **OPEX:** AWS, Direct Connect/partner, VPN, circuitos, datos móviles, cola virtual, soporte/garantía, energía, Ubuntu Pro, operación y administración.
- La hoja `Costos_Anuales` calcula valores conocidos y mantiene campos de precio por cotizar. Los subtotales parciales no se consideran TCO completo.

## 6. Conclusión de presupuesto

A 3-nov-2026 no se puede declarar que A ni B cumplen los topes porque faltan cotizaciones críticas. La capa de datos es pequeña frente al presupuesto, pero el hardware completo del estadio, la cola virtual, Direct Connect/circuitos, respaldo inmutable y aplicación en espera no están cerrados. La recomendación es no aprobar CAPEX ni cerrar el escenario hasta obtener esas cotizaciones.

## 7. Solicitud de adición presupuestal (solo si se usa la reserva)

**Borrador para el registro de decisiones:**

> Se solicita autorizar el uso de la reserva del 10 % del presupuesto del proyecto para cubrir variaciones verificadas de precios de hardware, conectividad y servicios cloud indispensables para mantener los RPO/RTO y la operación de BoletaYa. La reserva no se usa para ampliar alcance; cada uso deberá estar soportado por cotización vigente, comparación de alternativas y aprobación del responsable financiero. El gasto adicional se registrará por componente, escenario, fecha y evidencia. La solicitud se activa únicamente cuando el costo consolidado y cotizado supere el presupuesto base, sin exceder el techo autorizado por el comité.
