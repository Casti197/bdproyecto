## T1. Cantidad de registros por anio (formulas en capacidad_y_volumetria.md)

| Entidad | Tam./registro (B) | Anio 1 | Anio 2 | Anio 3 | Anio 4 | Anio 5 |
|---|---:|---:|---:|---:|---:|---:|
| usuarios | 1536 | 2.500.000 | 3.500.000 | 4.900.000 | 6.860.000 | 9.604.000 |
| eventos | 4096 | 1.800 | 2.340 | 3.042 | 3.955 | 5.141 |
| sillas | 100 | 5.400.000 | 7.020.000 | 9.126.000 | 11.865.000 | 15.423.000 |
| historial | 150 | 21.600.000 | 28.080.000 | 36.504.000 | 47.460.000 | 61.692.000 |
| ordenes | 2048 | 1.600.000 | 2.080.000 | 2.704.000 | 3.515.200 | 4.569.760 |
| pagos | 1536 | 2.080.000 | 2.704.000 | 3.515.200 | 4.569.760 | 5.940.688 |
| boletas | 1024 | 4.000.000 | 5.200.000 | 6.760.000 | 8.788.000 | 11.424.400 |
| escaneos | 250 | 4.800.000 | 6.240.000 | 8.112.000 | 10.545.600 | 13.709.280 |
| cufe | 500 | 1.600.000 | 2.080.000 | 2.704.000 | 3.515.200 | 4.569.760 |
| auditoria | 300 | 60.000.000 | 78.000.000 | 101.400.000 | 131.820.000 | 171.366.000 |

**Ocupacion implicita (boletas / sillas)** con eventos creciendo a 30 % vs. eventos constantes:

| Anio | Boletas | Sillas (eventos +30 %) | Ocupacion | Sillas (eventos constantes) | Ocupacion |
|---|---:|---:|---:|---:|---:|
| 1 | 4.000.000 | 5.400.000 | 74.1 % | 5.400.000 | 74.1 % |
| 2 | 5.200.000 | 7.020.000 | 74.1 % | 5.400.000 | 96.3 % |
| 3 | 6.760.000 | 9.126.000 | 74.1 % | 5.400.000 | 125.2 % |
| 4 | 8.788.000 | 11.865.000 | 74.1 % | 5.400.000 | 162.7 % |
| 5 | 11.424.400 | 15.423.000 | 74.1 % | 5.400.000 | 211.6 % |

## T2. Almacenamiento (GiB) - flujo anual crudo, en linea facturado, indices y archivado en S3

| Anio | Crudo del anio (flujo) | En linea: crudo | En linea: facturado (crudo+sobrecarga) | Indices GSI | Total en linea (tablas+GSI) | Archivado acumulado S3 (crudo) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 35,6 | 35,6 | 45,2 | 2,8 | 48,0 | 0,0 |
| 2 | 46,6 | 77,0 | 98,0 | 6,0 | 104,0 | 1,6 |
| 3 | 61,1 | 100,6 | 127,9 | 7,9 | 135,8 | 34,1 |
| 4 | 80,1 | 131,4 | 167,1 | 10,3 | 177,4 | 76,3 |
| 5 | 105,1 | 171,9 | 218,2 | 13,6 | 231,8 | 131,2 |

**Desglose por entidad en el anio 5 (GiB):**

| Entidad | Crudo anual | En linea crudo | En linea facturado | GSI de la entidad | Archivado S3 |
|---|---:|---:|---:|---:|---:|
| usuarios | 13,74 | 13,74 | 14,63 | 1,65 | 0,00 |
| eventos | 0,02 | 0,03 | 0,04 | 0,00 | 0,03 |
| sillas | 1,44 | 1,44 | 2,87 | 0,00 | 3,11 |
| historial | 8,62 | 15,25 | 25,41 | 0,00 | 12,04 |
| ordenes | 8,72 | 15,42 | 16,17 | 3,86 | 12,18 |
| pagos | 8,50 | 15,04 | 16,01 | 0,00 | 11,87 |
| boletas | 10,90 | 19,28 | 21,16 | 5,08 | 15,22 |
| escaneos | 3,19 | 3,19 | 4,47 | 0,00 | 6,91 |
| cufe | 2,13 | 3,76 | 4,52 | 0,00 | 2,97 |
| auditoria | 47,88 | 84,71 | 112,95 | 2,96 | 66,89 |

## T3. Operacion normal (8.000 boletas/dia, 16 h) - anio 1 y anio 5

| Metrica | Anio 1 | Anio 5 | Formula |
|---|---:|---:|---|
| Boletas por dia | 8.000 | 22.849 | 8.000 x 1,3^(n-1) |
| Boletas por hora | 500,0 | 1.428,1 | dia / 16 |
| Boletas por minuto | 8,33 | 23,80 | hora / 60 |
| Ordenes por dia | 3.200 | 9.140 | boletas / 2,5 |
| Ordenes por hora | 200,0 | 571,2 | ordenes dia / 16 |
| Ordenes por minuto | 3,33 | 9,52 | hora / 60 |
| Ordenes por segundo | 0,0556 | 0,1587 | hora / 3600 |
| WRU por orden (camino feliz + 30 % abandono) | 62,4 | 62,4 | T4 (escenario Minimo con abandono 30 %) |
| WRU por segundo promedio | 3,47 | 9,90 | ordenes/s x WRU/orden |
| WRU por dia | 199.589 | 570.045 | ordenes dia x WRU/orden |
| RRU por orden | 11,75 | 11,75 | T4b |
| RRU por segundo promedio | 0,65 | 1,86 | ordenes/s x RRU/orden |

Sensibilidad a la frase 'unos 100 ventas por minuto' del contexto del enunciado: 100 ordenes/min = 1,67 ordenes/s -> 104,0 WRU/s (todavia << 4.000 WRU/s de una tabla nueva on-demand).

## T4. WRU por orden completada, por escenario (desglose por tabla)

| Escenario | sillas | ordenes | limites | contadores | boletas | historial | auditoria | gsi_ordenes | gsi_pendientes | gsi_boletas | **Total WRU/orden** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Minimo | 10,00 | 18,20 | 2,00 | 2,00 | 5,00 | 5,00 | 2,00 | 4,00 | 4,60 | 2,50 | **55,30** |
| Planificacion | 22,14 | 27,91 | 6,86 | 2,00 | 5,00 | 6,07 | 2,43 | 4,86 | 4,60 | 2,50 | **84,37** |
| Estres | 55,00 | 56,60 | 20,00 | 2,00 | 10,00 | 7,50 | 6,00 | 12,00 | 8,80 | 5,00 | **182,90** |

**T4b. RRU por orden:**

| Escenario | RRU/orden |
|---|---:|
| Minimo | 11,75 |
| Planificacion | 14,25 |
| Estres | 21,75 |

## T5. Preventa grande - tasas

| Concepto | Valor | Formula |
|---|---:|---|
| Boletas por minuto (promedio) | 3.000 | 60.000 / 20 |
| Boletas por segundo (promedio) | 50,0 | 60.000 / 1.200 |
| Ordenes en la preventa | 24.000 | 60.000 / 2,5 |
| Ordenes por segundo (promedio) | 20,0 | 24.000 / 1.200 |
| Intentos de pago por orden si el 30 % tiene 1 rechazo | 1,30 | 1 + 0,30 x k |
| Intentos de pago por orden si el 30 % tiene 2 rechazos | 1,60 | 1 + 0,30 x k |
| Intentos de pago por orden si el 30 % tiene 3 rechazos | 1,90 | 1 + 0,30 x k |
| Intentos de pago totales (k=1) | 31.200 | 24.000 x 1,3 |
| Intentos de pago por segundo (k=1) | 26,0 | /1.200 |
| Intentos ADICIONALES (rechazados), k=1 | 7.200 | 24.000 x 0,30 |

**T5b. Escrituras de la preventa (WRU) por escenario y factor de rafaga:**

| Escenario | WRU/orden | WRU totales preventa | WRU/s promedio (x1) | WRU/s rafaga x3 | WRU/s instantaneo x5 | +25 % margen sobre x5 |
|---|---:|---:|---:|---:|---:|---:|
| Minimo | 55,3 | 1.327.200 | 1.106 | 3.318 | 5.530 | 6.912 |
| Planificacion | 84,4 | 2.024.914 | 1.687 | 5.062 | 8.437 | 10.546 |
| Estres | 182,9 | 4.389.600 | 3.658 | 10.974 | 18.290 | 22.862 |

**T5c. WRU/s por tabla en la rafaga x5, escenario Planificacion y Estres (comparar con 4.000 WRU/s de tabla on-demand nueva; 1.000 WRU/s por particion):**

| Tabla/indice | Planificacion x5 | Estres x5 |
|---|---:|---:|
| sillas | 2.214 | 5.500 |
| ordenes | 2.791 | 5.660 |
| limites | 686 | 2.000 |
| contadores | 200 | 200 |
| boletas | 500 | 1.000 |
| historial | 607 | 750 |
| auditoria | 243 | 600 |
| gsi_ordenes | 486 | 1.200 |
| gsi_pendientes | 460 | 880 |
| gsi_boletas | 250 | 500 |

**T5d. RRU/s en la preventa:**

| Fuente | RRU/s | Formula |
|---|---:|---|
| Ordenes (Planificacion, x5) | 1.425 | ordenes/s x5 x RRU/orden |
| Ordenes (Estres, x5) | 2.175 | ordenes/s x5 x RRU/orden |
| Constructor de mapa (estadio 45.000 sillas, 900 filas x 1 RRU, refresco cada 2 s) | 450 | filas x RRU/fila / intervalo |
| Constructor de mapa (estadio 45.000 sillas, 900 filas x 1 RRU, refresco cada 5 s) | 180 | filas x RRU/fila / intervalo |
| Contadores: BatchGet fuerte de 16 fragmentos x 20 localidades x 1 lectura/s | 320 | 16 x 20 x 1 RRU |
| Contadores: TransactGetItems 16 fragmentos x 20 localidades x 1/s | 640 | x2 (transaccional) |

## T6. Mapa de sillas - 3 escenarios (anio 1) y proyeccion de la cola

| Anio | Personas en cola (250.000 x 1,25^(n-1)) |
|---|---:|
| 1 | 250.000 |
| 2 | 312.500 |
| 3 | 390.625 |
| 4 | 488.281 |
| 5 | 610.352 |

Consulta DIRECTA a la base de una localidad de 2.250 sillas: 220 KiB -> 27.5 RRU (eventual) por solicitud (supera 1 MB? no: 220 KiB < 1 MiB).

| Escenario | Usuarios | Intervalo de consulta | Solicitudes/s | RRU/s si TODO fuera a DynamoDB | x cuota 40.000/tabla | Solicitudes en 20 min |
|---|---:|---:|---:|---:|---:|---:|
| Moderada | 250.000 | 30 s | 8.333 | 229.167 | 5.7x | 10.000.000 |
| Alta | 250.000 | 10 s | 25.000 | 687.500 | 17.2x | 30.000.000 |
| Extrema | 250.000 | 3 s | 83.333 | 2.291.667 | 57.3x | 100.000.000 |
| Extrema, anio 5 | 610.352 | 3 s | 203.451 | 5.594.889 | 139.9x | 244.140.625 |

**T6b. Con arquitectura de lectura (instantaneas en CDN): carga residual en DynamoDB y costo CloudFront por preventa**

Supuestos: carga util por consulta = 3 KB (resumen + mapa de bits de la localidad; 45.000 sillas x 2 bits = 11 KiB todo el estadio); TTL 2 s; 21 objetos (resumen + 20 localidades).

| Escenario | Solicitudes/s | Ancho de banda (Mbps) | GB por preventa (20 min) | CloudFront solicitudes (USD/preventa, SA) | CloudFront salida (USD/preventa, SA) | Total USD/preventa | Total USD/anio (25) | Lecturas a DynamoDB (RRU/s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Moderada | 8.333 | 200 | 30,0 | 22,0 | 3,3 | 25,3 | 632 | 450 |
| Alta | 25.000 | 600 | 90,0 | 66,0 | 9,9 | 75,9 | 1.898 | 450 |
| Extrema | 83.333 | 2.000 | 300,0 | 220,0 | 33,0 | 253,0 | 6.325 | 450 |
| Extrema anio 5 | 203.451 | 4.883 | 732,4 | 537,1 | 80,6 | 617,7 | 15.442 | 450 |

## T7. Costo anual de DynamoDB (solo throughput) por opcion, region y anio - USD (planificacion)

Normal: abandono 30 %, sin fallos de bloqueo. Preventa: escenario Planificacion con fallos de bloqueo creciendo con la cola (x1,25^(n-1)).


### sa-east-1

| Anio | WRU normal (M) | WRU preventas (M) | RRU totales (M) | A) On-demand USD | B1) Provisionado fijo al pico USD | B2) Programado (base + 75 h de pico) USD | Umbral de uso para que provisionado gane |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 72,8 | 50,6 | 45,4 | 124 | 94.764 | 1.319 | 28.9 % |
| 2 | 94,7 | 53,9 | 49,9 | 149 | 100.769 | 1.371 | 28.9 % |
| 3 | 123,1 | 58,0 | 55,7 | 180 | 108.276 | 1.435 | 28.9 % |
| 4 | 160,1 | 63,2 | 63,2 | 221 | 117.659 | 1.515 | 28.9 % |
| 5 | 208,1 | 69,6 | 73,0 | 274 | 129.389 | 1.616 | 28.9 % |

### us-east-1

| Anio | WRU normal (M) | WRU preventas (M) | RRU totales (M) | A) On-demand USD | B1) Provisionado fijo al pico USD | B2) Programado (base + 75 h de pico) USD | Umbral de uso para que provisionado gane |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 72,8 | 50,6 | 45,4 | 83 | 63.176 | 880 | 28.9 % |
| 2 | 94,7 | 53,9 | 49,9 | 99 | 67.180 | 914 | 28.9 % |
| 3 | 123,1 | 58,0 | 55,7 | 120 | 72.184 | 957 | 28.9 % |
| 4 | 160,1 | 63,2 | 63,2 | 147 | 78.440 | 1.010 | 28.9 % |
| 5 | 208,1 | 69,6 | 73,0 | 183 | 86.259 | 1.077 | 28.9 % |

**Capacidad de pico a provisionar (planificacion x5 + 25 %):**

| Anio | WCU pico | RCU pico | WCU base normal | RCU base normal |
|---|---:|---:|---:|---:|
| 1 | 10.546 | 2.744 | 50 | 50 |
| 2 | 11.234 | 2.822 | 50 | 50 |
| 3 | 12.093 | 2.920 | 50 | 50 |
| 4 | 13.168 | 3.042 | 50 | 50 |
| 5 | 14.510 | 3.194 | 50 | 50 |

## T8. Costo mensual de almacenamiento anio 5 (USD/mes) por clase de tabla

| Entidad | GiB facturado en linea | Standard sa-east-1 | Standard-IA sa-east-1 | Standard us-east-1 | Standard-IA us-east-1 |
|---|---:|---:|---:|---:|---:|
| usuarios | 14,63 | 5,5 | 2,2 | 3,7 | 1,5 |
| eventos | 0,04 | 0,0 | 0,0 | 0,0 | 0,0 |
| sillas | 2,87 | 1,1 | 0,4 | 0,7 | 0,3 |
| historial | 25,41 | 9,5 | 3,8 | 6,4 | 2,5 |
| ordenes | 16,17 | 6,1 | 2,4 | 4,0 | 1,6 |
| pagos | 16,01 | 6,0 | 2,4 | 4,0 | 1,6 |
| boletas | 21,16 | 7,9 | 3,2 | 5,3 | 2,1 |
| escaneos | 4,47 | 1,7 | 0,7 | 1,1 | 0,4 |
| cufe | 4,52 | 1,7 | 0,7 | 1,1 | 0,5 |
| auditoria | 112,95 | 42,4 | 16,9 | 28,2 | 11,3 |

Total tablas+GSI anio 5 = 231,8 GiB. PITR (35 dias) factura aprox. el tamano de la tabla: 69,5 USD/mes (sa-east-1) vs 46,4 (us-east-1).

## T9. Little: compradores concurrentes en la fase transaccional

- Sesion de compra 120 s x 20 ordenes/s promedio = 2.400 compradores simultaneos (x5 rafaga: 12.000)
- Sesion de compra 240 s x 20 ordenes/s promedio = 4.800 compradores simultaneos (x5 rafaga: 24.000)
- Sesion de compra 480 s x 20 ordenes/s promedio = 9.600 compradores simultaneos (x5 rafaga: 48.000)

## T10. Contencion del contador por fragmentos (modelo ilustrativo, NO medicion)

lambda = ordenes/s en rafaga sobre una localidad; T = tiempo que una transaccion retiene el item (supuesto; no publicado por AWS). rho = lambda/N x T = probabilidad aproximada de encontrar el item ocupado.

| N fragmentos | lambda por fragmento (100 ord/s) | rho con T=10 ms | rho con T=25 ms | rho con T=50 ms |
|---:|---:|---:|---:|---:|
| 1 | 100.0/s | 1.00 | 2.50 | 5.00 |
| 4 | 25.0/s | 0.25 | 0.62 | 1.25 |
| 8 | 12.5/s | 0.12 | 0.31 | 0.62 |
| 16 | 6.2/s | 0.06 | 0.16 | 0.31 |
| 32 | 3.1/s | 0.03 | 0.08 | 0.16 |

Limite duro por item: 1.000 WRU/s -> 500 transacciones/s sobre un mismo item (2 WRU c/u).

## T11. Comparacion de precios unitarios por region (USD, lista oficial 2026-09-11)

| Concepto | sa-east-1 | us-east-1 | Diferencia sa vs us |
|---|---:|---:|---:|
| 1 M WRU on-demand | 0.9375 | 0.625 | +50 % |
| 1 M RRU on-demand | 0.1875 | 0.125 | +50 % |
| WCU-hora | 0.000975 | 0.00065 | +50 % |
| RCU-hora | 0.000195 | 0.00013 | +50 % |
| GB-mes Standard | 0.375 | 0.25 | +50 % |
| GB-mes PITR | 0.3 | 0.2 | +50 % |
| TB escaneado Athena | 9 | 5 | +80 % |
| Nodo cache.m7g.large Valkey /h | 0.18 | 0.1264 | +42 % |

## T7b. Costo anual total de la capa DynamoDB + archivo (USD, on-demand, Standard) - anio 1..5

Incluye: throughput (T7-A), almacenamiento de fin de anio x 12 meses (conservador), PITR (~tamano de tablas x 12), exportaciones incrementales diarias (2 x flujo anual de tablas con TTL), archivo S3 Standard. NO incluye Streams/Lambda/Athena/KMS/CloudWatch (pendientes, ver documento).

| Region | Anio | Throughput | Almacenamiento | PITR | Exportaciones | S3 archivo | **Total USD/anio** | **Total COP/anio (TRM 4.000)** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| sa-east-1 | 1 | 124 | 216 | 173 | 9 | 0 | **523** | **2.090.211** |
| sa-east-1 | 2 | 149 | 468 | 374 | 12 | 1 | **1.004** | **4.017.468** |
| sa-east-1 | 3 | 180 | 611 | 489 | 16 | 17 | **1.313** | **5.252.092** |
| sa-east-1 | 4 | 221 | 798 | 639 | 21 | 37 | **1.716** | **6.864.048** |
| sa-east-1 | 5 | 274 | 1.043 | 834 | 27 | 64 | **2.242** | **8.969.310** |
| us-east-1 | 1 | 83 | 144 | 115 | 6 | 0 | **348** | **1.393.474** |
| us-east-1 | 2 | 99 | 312 | 250 | 8 | 0 | **670** | **2.678.001** |
| us-east-1 | 3 | 120 | 407 | 326 | 11 | 9 | **874** | **3.494.847** |
| us-east-1 | 4 | 147 | 532 | 426 | 14 | 21 | **1.140** | **4.561.377** |
| us-east-1 | 5 | 183 | 695 | 556 | 18 | 36 | **1.489** | **5.954.345** |

## T10b. Cuantos fragmentos de contador hacen falta (limite duro 1.000 WRU/s por item; 2 WRU por transaccion)

| Escenario (rafaga x5, todas las ventas en UNA localidad) | WRU/s sobre el contador (2 WRU x ordenes/s) | Fragmentos minimos con 50 % de holgura | Con N=1 |
|---|---:|---:|---|
| x1 promedio | 40 | 1 | cabe el limite de 1.000 WRU/s |
| x3 | 120 | 1 | cabe el limite de 1.000 WRU/s |
| x5 instantaneo | 200 | 1 | cabe el limite de 1.000 WRU/s |
| x5 y 3 reintentos de confirmacion por orden | 600 | 2 | cabe el limite de 1.000 WRU/s |

## T12. Componentes auxiliares - cantidades y orden de magnitud (anio 1)

- Llamadas dinamicas al API por preventa: ordenes x 20 + intentos de bloqueo fallidos x 3 + 2 llamadas de admision por persona en cola = 1.124.000 (supuesto de 20 llamadas por orden: bloqueo, pago x1,3, confirmacion, sondeos). Pico x5: 2.000 req/s (cuota por defecto de API Gateway: 10.000 req/s por cuenta y region).
- API Gateway HTTP API en sa-east-1: 1,79 USD por preventa; 45 USD/anio por las 25 preventas (primeros 300 M solicitudes/mes) + trafico normal.
- ElastiCache Valkey 2 nodos cache.m7g.large 24x7 en sa-east-1: 3.154 USD/anio (precio de nodo; no incluye SyncDurability ni copias).
- API Gateway HTTP API en us-east-1: 1,12 USD por preventa; 28 USD/anio por las 25 preventas (primeros 300 M solicitudes/mes) + trafico normal.
- ElastiCache Valkey 2 nodos cache.m7g.large 24x7 en us-east-1: 2.215 USD/anio (precio de nodo; no incluye SyncDurability ni copias).
- Publicacion de instantaneas a S3: 21 objetos x (1.200 s / 2 s) = 12600 PUT por preventa por evento activo.

## T2b. Datos crudos del anio (GiB) por entidad y anio (flujo anual; usuarios = existencias)

| Entidad | Anio 1 | Anio 2 | Anio 3 | Anio 4 | Anio 5 |
|---|---:|---:|---:|---:|---:|
| usuarios | 3,58 | 5,01 | 7,01 | 9,81 | 13,74 |
| eventos | 0,01 | 0,01 | 0,01 | 0,02 | 0,02 |
| sillas | 0,50 | 0,65 | 0,85 | 1,11 | 1,44 |
| historial | 3,02 | 3,92 | 5,10 | 6,63 | 8,62 |
| ordenes | 3,05 | 3,97 | 5,16 | 6,70 | 8,72 |
| pagos | 2,98 | 3,87 | 5,03 | 6,54 | 8,50 |
| boletas | 3,81 | 4,96 | 6,45 | 8,38 | 10,90 |
| escaneos | 1,12 | 1,45 | 1,89 | 2,46 | 3,19 |
| cufe | 0,75 | 0,97 | 1,26 | 1,64 | 2,13 |
| auditoria | 16,76 | 21,79 | 28,33 | 36,83 | 47,88 |

**T2c. Sobrecarga de indices GSI en linea por anio (GiB) y por indice, y espacio total facturado en linea por entidad (tabla + sus GSI)**

| Indice (entidad base) | Bytes por entrada (sin sobrecarga) + 100 | Anio 1 | Anio 2 | Anio 3 | Anio 4 | Anio 5 |
|---|---:|---:|---:|---:|---:|---:|
| gsi_email (usuarios) | 85 + 100 | 0,43 | 0,60 | 0,84 | 1,18 | 1,65 |
| gsi_org_fecha (eventos) | 170 + 100 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| gsi_usuario (ordenes) | 152 + 100 | 0,38 | 0,86 | 1,12 | 1,46 | 1,90 |
| gsi_evento (ordenes) | 160 + 100 | 0,39 | 0,89 | 1,16 | 1,51 | 1,96 |
| gsi_evento_boleta (boletas) | 170 + 100 | 1,01 | 2,31 | 3,01 | 3,91 | 5,08 |
| gsi_actor (auditoria) | 110 + 100 | 0,59 | 1,35 | 1,75 | 2,28 | 2,96 |

**T2d. Espacio total facturado en linea (tabla + GSI) por entidad y anio (GiB)**

| Entidad | Anio 1 | Anio 2 | Anio 3 | Anio 4 | Anio 5 |
|---|---:|---:|---:|---:|---:|
| usuarios | 4,24 | 5,94 | 8,31 | 11,63 | 16,29 |
| eventos | 0,01 | 0,02 | 0,02 | 0,03 | 0,04 |
| sillas | 1,01 | 1,31 | 1,70 | 2,21 | 2,87 |
| historial | 5,03 | 11,57 | 15,04 | 19,55 | 25,41 |
| ordenes | 3,96 | 9,12 | 11,85 | 15,41 | 20,03 |
| pagos | 3,17 | 7,29 | 9,48 | 12,32 | 16,01 |
| boletas | 5,19 | 11,94 | 15,53 | 20,19 | 26,24 |
| escaneos | 1,56 | 2,03 | 2,64 | 3,44 | 4,47 |
| cufe | 0,89 | 2,06 | 2,67 | 3,48 | 4,52 |
| auditoria | 22,94 | 52,76 | 68,59 | 89,16 | 115,91 |

## T5e. Sensibilidad del WRU por orden (planificacion como base)

| Variante | WRU/orden | WRU/s promedio (20 ord/s) | WRU/s x5 | Intentos de pago por orden |
|---|---:|---:|---:|---:|
| Base (k=1, f=2, abandono 30 %) | 84,4 | 1.687 | 8.437 | 1,30 |
| k=2 rechazos por orden afectada | 86,2 | 1.723 | 8.617 | 1,60 |
| k=3 rechazos por orden afectada | 88,0 | 1.759 | 8.797 | 1,90 |
| Boleta de 2 KB (2 WRU en vez de 1) | 89,4 | 1.787 | 8.937 | 1,30 |
| Indices en transaccion cuentan doble | 94,7 | 1.895 | 9.473 | 1,30 |
| f=8 bloqueos fallidos por exitoso | 150,4 | 3.007 | 15.037 | 1,30 |
| Abandono 50 % | 93,8 | 1.876 | 9.380 | 1,30 |
| 5 auditorias por orden | 87,4 | 1.747 | 8.737 | 1,30 |

## T7c. Costo de DynamoDB por preventa (throughput, anio 1, escenario Planificacion, on-demand)

| Concepto | Unidades | sa-east-1 USD | us-east-1 USD |
|---|---:|---:|---:|
| Escrituras (WRU) | 2.024.914 | 1,90 | 1,27 |
| Lecturas (RRU): ordenes + constructor de mapa + tablero | 1.266.000 | 0,24 | 0,16 |
| **Total por preventa** | | **2,14** | **1,42** |

Provisionado programado: sobrecosto de 3 h de capacidad de pico por preventa en sa-east-1: 32,28 USD (WCU 10.546 / RCU 2.744 menos la base de 50/50).

Provisionado programado: sobrecosto de 3 h de capacidad de pico por preventa en us-east-1: 21,52 USD (WCU 10.546 / RCU 2.744 menos la base de 50/50).

Utilizacion media si se provisionara fijo al pico todo el anio (anio 1): 0,037 % (umbral de equilibrio 28,9 %).
