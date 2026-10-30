# Componentes de respaldo y recuperación para costear

**Autor:** Miguel · **Para:** Juan Pablo (copia: Jacobo, Samuel) · **Fecha:** 2026-10-30
Lo que respalda y cuándo está en `recuperacion_licenciamiento_carta.md` (sección "5.5 Estrategia de respaldo"). Este archivo es solo la lista para tu hoja, con las cantidades que ya puedo calcular.

**Regla que seguí:** no puse ningún precio. Los de AWS cambian y cada línea necesita enlace, fecha de consulta y captura de la Pricing Calculator, así que eso lo haces tú. Donde no sé una cantidad lo digo.

---

## 1. Volúmenes que uso (de Jacobo)

Tomados de `calculos/modelo_capacidad.py` de Jacobo (lo ejecuté y da lo mismo que su `salida_modelo.md`). Tabla + índices (GSI), en GiB, fin de cada año.

| Tabla | Año 1 | Año 2 | Año 3 | Año 4 | Año 5 |
|---|---|---|---|---|---|
| `bya_seats` | 1,01 | 1,31 | 1,70 | 2,21 | 2,87 |
| `bya_orders` | 8,02 | 18,47 | 24,00 | 31,21 | 40,56 |
| `bya_tickets` | 6,75 | 13,97 | 18,17 | 23,63 | 30,71 |
| `bya_counters` | ≈0 | ≈0 | ≈0 | ≈0 | ≈0 |
| `bya_users` | 4,24 | 5,94 | 8,31 | 11,63 | 16,29 |
| `bya_catalog` | 0,01 | 0,02 | 0,02 | 0,03 | 0,04 |
| `bya_seat_history` | 5,03 | 11,57 | 15,04 | 19,55 | 25,41 |
| `bya_audit` | 22,94 | 52,76 | 68,59 | 89,16 | 115,91 |
| **Críticas** (seats + orders + tickets) | 15,78 | 33,75 | 43,87 | 57,05 | 74,14 |
| **Total** (8 tablas) | 48,00 | 104,04 | 135,83 | 177,42 | 231,79 |
| **Tablas con AWS Backup** (total sin `bya_seat_history`) | 42,97 | 92,47 | 120,79 | 157,87 | 206,38 |
| Archivo S3 acumulado (cifra de Jacobo) | 0 | 1,6 | 34,1 | 76,3 | 131,2 |

Dos advertencias:

- Jacobo (R-36) anota que PITR y AWS Backup facturan el tamaño de la tabla sin índices. Estas cifras incluyen los índices, así que sobreestiman unos 6 %. Es un error del lado seguro.
- Usa el mismo año de referencia que Jacobo. Si él cambia volúmenes, recalcula con su script, no con esta tabla.

## 2. Lista de componentes

Para cada uno: qué es, de qué cantidad depende y qué falta saber. "Precio" siempre es tuyo.

### 2.1 Respaldo dentro de la región

| # | Componente | Cantidad | Nota |
|---|---|---|---|
| R1 | **PITR** en las 8 tablas de us-east-1, 35 días | Tamaño de tabla de cada año (fila "Total") | `bya_seat_history` lo necesita aunque no tenga AWS Backup, porque la exportación a S3 exige PITR |
| R2 | **PITR** en las réplicas de us-east-2 | Igual que R1 | AWS no replica PITR entre réplicas de una tabla global: se activa a mano en us-east-2 y se cobra aparte |
| R3 | **AWS Backup diario**, retención 35 días, 7 tablas (todas menos `bya_seat_history`) | Fila "Tablas con AWS Backup" | Cota superior si cada punto se cobrara completo: 35 × tamaño (1.504 GiB en el año 1 y 7.223 GiB en el año 5). **No he podido verificar si AWS Backup cobra los puntos de DynamoDB de forma incremental**: confírmalo en su página de precios. Si es incremental, el costo real es mucho menor |
| R4 | **AWS Backup mensual**, retención 13 meses, tablas críticas | Fila "Críticas" | Cota superior: 13 × tamaño (205 GiB en el año 1 y 964 GiB en el año 5) |
| R5 | Opción: **AWS Backup horario** en lugar de diario, solo para las críticas | 24 puntos por día | Está en la decisión pendiente de la ficha R-2: baja el riesgo de una cuenta comprometida de 24 h a 1 h. Costea las dos versiones |

### 2.2 Copia fuera de la región y de la cuenta (inmutable)

| # | Componente | Cantidad | Nota |
|---|---|---|---|
| C1 | **Copia entre regiones** de los respaldos a us-east-2 | Volumen de R3 y R4 que se copia | Cobra transferencia entre regiones además del almacenamiento |
| C2 | **Copia a la cuenta de respaldo** (otra cuenta) | Igual que C1 | Es la que protege si la cuenta principal se compromete |
| C3 | **Almacenamiento bajo Vault Lock** (modo cumplimiento tras probar en gobernanza) | Lo que dure la retención | Compromete el costo: no se puede borrar antes. Incluye todos los puntos, incluidos los mensuales de 13 meses |
| C4 | **Llave KMS independiente** para los respaldos | 1 llave + solicitudes | AWS permite cifrar los respaldos con una llave distinta a la de la tabla. Esta línea es compartida con Samuel (seguridad) |

### 2.3 Exportaciones y archivo en S3

| # | Componente | Cantidad | Nota |
|---|---|---|---|
| S1 | **Exportación incremental diaria** de `bya_seats`, `bya_orders`, `bya_tickets`, `bya_audit`, `bya_seat_history` y completa de `bya_catalog` | Datos exportados por día | La exportación no consume RCU pero **sí se cobra por GB exportado**: verifica la unidad en la página de precios |
| S2 | **Almacenamiento S3** con versionado y Object Lock (modo cumplimiento) | Fila "Archivo S3 acumulado" (de Jacobo) más las exportaciones | El plazo legal lo fija Samuel; hasta que lo dé, el costo de retención de S3 es un supuesto |
| S3 | **Replicación S3 a us-east-2 con Replication Time Control** | Mismo volumen que S2 | RTC cobra aparte de la replicación normal |
| S4 | **Athena** para consultar archivo frío | Consultas al año | Lo de Jacobo; no lo repito aquí |

### 2.4 Región alterna (pérdida de la región)

| # | Componente | Cantidad | Nota |
|---|---|---|---|
| A1 | **Réplica en us-east-2** (tabla global): almacenamiento | Fila "Total" | Cada tabla global replica a us-east-2 |
| A2 | **Escrituras replicadas** a us-east-2 | Una escritura replicada por cada escritura de la tabla | La replicación a otra región se cobra por unidad de escritura replicada. Depende de las WCU de Jacobo |
| A3 | **Transferencia entre regiones** de la replicación | Volumen de escrituras | Línea separada |
| A4 | **Pre-calentamiento (warm throughput)** de las réplicas | Valor que fije Jacobo | Una sola vez, para todas las réplicas, no se puede reducir después y se cobra al subirlo |
| A5 | **Aplicación en espera** en us-east-2 | Lo que decida Jacobo: tamaño mínimo siempre encendido, o encendido bajo demanda con más RTO | Es lo que define el paso "aplicación lista" del RTO (0 a 3 minutos) |
| A6 | **Route 53**: zona, comprobaciones de salud (cada 10 o 30 s) y conmutación por DNS | 1 zona, pocas comprobaciones | Reemplaza la conmutación de CloudFront para las compras |
| A7 | Opcional, plan B de D-2: **libro de pagos en MRSC** | Una tabla pequeña, tres regiones (dos réplicas y un testigo) | Solo si Jacobo y David lo aprueban. MRSC está disponible en us-east-1 y us-east-2. Cobra el testigo y la escritura sincrónica |

### 2.5 Escenario B (sitio alterno del data center de Bogotá)

| # | Componente | Cantidad | Nota |
|---|---|---|---|
| B1 | **Aplicación y caché en AWS** como sitio alterno cuando cae Bogotá | Misma de A5 | La base ya está en AWS (P-1 de Jacobo), así que no hay réplica de base adicional |
| B2 | **Cola virtual con estado en AWS** (si se acepta mi hallazgo H-4) | Estado de hasta 250.000 personas | Pendiente de decisión de Jacobo |
| B3 | **Enlace redundante** entre Bogotá y AWS | 1 enlace extra | Si el único enlace cae, el sitio de Bogotá queda aislado aunque no se haya caído. Es tuyo (conectividad) |

### 2.6 Pruebas y personal (entran al TCO, no al presupuesto del año 1)

| # | Componente | Cantidad | Costo ya calculado |
|---|---|---|---|
| P1 | **Restauraciones de prueba** (PITR a tabla nueva) | 4 tipos de prueba al año, descritos en mi plan de pruebas | Almacenamiento de las tablas restauradas mientras existan, a precio de DynamoDB. Cantidad: tamaño de las críticas × el tiempo que se conserven (propongo 1 día) |
| P2 | **Horas de DBA** para simulacros, pruebas y mantenimiento de respaldo | 68 horas al año | 68 × COP 120.000 = **COP 8.160.000 al año** |
| P3 | **Plan de actualización de software** (licenciamiento 5.3) | 2 migraciones de runtime × 40 h + 1 SDK mayor × 24 h = 104 h en 5 años | 104 × 120.000 = **COP 12.480.000 en 5 años** |

Las 6 horas de DBA por preventa (25 preventas al año = 150 horas) están en tu parámetro y son aparte de P2; no las duplico.

## 3. Lo que NO estoy costeando y por qué

- **DynamoDB sin licencia:** no hay edición ni licencia por núcleo; DynamoDB es un servicio sin versión que elegir. La línea de licenciamiento es 0 y el trabajo real es P3.
- **Lecturas y escrituras, caché y egress de usuarios:** son de Jacobo y tuyas.
- **CloudTrail y KMS de seguridad en general:** son de Samuel. Solo la llave de respaldo (C4) está aquí.
- **Horas de DBA por incidente real:** no las puse porque no sé cuántos incidentes habrá.

## 4. Qué necesito que me avises

1. Si el costo de AWS Backup (R3, R4) o la copia inmutable (C1 a C3) hace que el año 1 no quepa en los COP 280.000.000. Dime cuánto y bajo la frecuencia o la retención que haga falta (por ejemplo, la mensual a 13 meses solo para `bya_orders` y `bya_tickets`).
2. Si la opción horaria (R5) es viable. Si no lo es, dejo la diaria y el riesgo de 24 h queda documentado en la ficha R-2.
3. Cuáles líneas no tienen precio verificable, para escribirlas como supuesto y no como dato.
