# Capacidad, volumetría y manejo del pico — BoletaYa SAS (DynamoDB)

**Autor:** Jacobo · **Fecha:** 2026-10-29 · **Criterio de rúbrica:** Capacidad y manejo del pico (15 %).
**Reproducibilidad:** todas las cifras salen de [`calculos/modelo_capacidad.py`](calculos/modelo_capacidad.py) (salida completa en [`calculos/salida_modelo.md`](calculos/salida_modelo.md)). Las tablas de este documento reproducen esa salida con formato en español (punto de miles, coma decimal). Las fuentes `[R-xx]` están en [`referencias.md`](referencias.md).

> **Etiquetas.** `DATO` = enunciado oficial. `A-xx` = supuesto del grupo (lista en el README). **PENDIENTE** = no verificado.
> **Unidades.** DynamoDB usa unidades binarias: 1 KB = 1.024 B, 1 GB = 1.024 MB [R-07, R-14]. Aquí GiB = 2³⁰ B. El enunciado dice "KB"; tomo 1 KB = 1.024 B (diferencia de 2,4 %).

---

## 0. Lo que hay que saber en 60 segundos

1. **La operación normal es irrelevante para el tamaño de la base**: 8.000 boletas/día son **0,056 órdenes/s** y **≈ 3,5 WRU/s** en promedio (año 1). Una tabla on-demand nueva sostiene 4.000 escrituras/s [R-13].
2. **Todo el dimensionamiento lo manda la preventa**: 60.000 boletas / 20 min = **50 boletas/s = 20 órdenes/s**. Cada orden completada genera ≈ **55 WRU** en el mejor caso y **≈ 84 WRU** en el escenario de planificación → **≈ 1.690 WRU/s** promedio y **≈ 8.440 WRU/s** en una ráfaga ×5.
3. **Las lecturas del mapa de sillas no pueden ir a la base**: 250.000 personas consultando cada 10 s son **25.000 solicitudes/s**; leídas directo de DynamoDB serían **≈ 688.000 RRU/s = 17 veces** la cuota por defecto de una tabla (40.000) [R-14]. Con instantáneas en CDN, la base ve **≈ 450 RRU/s**.
4. **Recomendación:** DynamoDB **on-demand** + **pre-calentamiento** (`warm throughput`) de las tablas y GSI calientes + **cola virtual** + **instantáneas del mapa en CDN**. Cuesta **≈ USD 83–124 al año en throughput** (año 1) frente a **≈ USD 880–1.320** del provisionado con escalado programado y **≈ USD 63.000–95.000** del provisionado fijo al pico.
5. **El costo de DynamoDB es pequeño frente al presupuesto** (capa de datos completa ≈ USD 350–525 en el año 1; ≈ USD 1.490–2.240 en el año 5). El presupuesto lo van a consumir los componentes auxiliares (CDN, cola, caché, conectividad, estadio), no la base.

---

## 1. Contradicciones e inconsistencias del enunciado (y cómo las resuelvo)

| # | Dónde | Qué dice | Conflicto | Resolución |
|---|---|---|---|---|
| C-1 | §3 Carga: "hasta 60.000 boletas" en la preventa vs. Volumetría: "45.000 en estadio" | 60.000 > 45.000 sillas del estadio | Un solo evento de estadio no puede vender 60.000 boletas | Interpreto la preventa como un **lanzamiento** que puede abarcar **varias fechas/eventos** o un festival. El modelo funciona igual si toda la carga cae sobre un evento (peor caso). **Pregunta P-2 al profesor.** |
| C-2 | Contexto: "8.000 boletas/día" y "25 preventas de 60.000" vs. Volumetría: "4.000.000 boletas año 1" | 8.000 × 365 + 25 × 60.000 = **4.420.000** ≠ 4.000.000 (+10,5 %) | Los tres datos no cuadran entre sí | Para **almacenamiento** uso la **tabla oficial** (4.000.000). Para **carga** uso 8.000/día y 60.000/preventa (más exigente). La diferencia no cambia ninguna conclusión. |
| C-3 | §1 Contexto: "pasar de **100 ventas por minuto** a 3.000" vs. §3: 8.000 boletas en 16 h = **8,3 boletas/min** | 100/min ≈ 96.000 boletas/día | 12× más que 8.000/día | Uso §3 ("todo cálculo de capacidad parte de esta sección"). Sensibilidad: 100 órdenes/min = 104 WRU/s, todavía muy por debajo de 4.000 WRU/s. |
| C-4 | §5.1 pide "traducción a CPU, memoria e IOPS" | DynamoDB es **sin servidor**: no hay CPU, memoria ni IOPS que dimensionar; la unidad de capacidad es RCU/WCU (o RRU/WRU) [R-01, R-13] | El enunciado está pensado para motores con servidores | **Tradujo a RCU/WCU**, como indican `jacobo.md` y las instrucciones. La CPU/memoria que sí hay que dimensionar es la de la capa de aplicación (fuera de mi alcance). |
| C-5 | `jacobo.md`: "estimar índices (GSI), **compresión y espacio libre**" | DynamoDB no expone compresión ni espacio libre al cliente: factura el tamaño **calculado** del ítem (nombres + valores) [R-07] | Esos conceptos no existen en el servicio | **Compresión: no aplicada** (ratio 1:1). **Espacio libre: no aplica.** Documentado en §3.4. |
| C-6 | Volumetría: "Usuario registrado 2.500.000 (volumen año 1)" | ¿Son usuarios **nuevos** o **acumulados**? | Ambiguo | A-05: **acumulados** (existencias) porque el crecimiento "+40 % anual" se da sobre usuarios registrados. |
| C-7 | "Intento de pago: 1,3 por orden" y "30 % de las órdenes tiene **al menos** un rechazo" | 1,3 = 1 + 0,30 × 1 solo si cada orden afectada tiene **exactamente 1** rechazo | "Al menos un" admite más | Caso base k = 1 (cuadra con 1,3); sensibilidad k = 2, 3 en §5.4. |

---

## 2. Reglas de capacidad de DynamoDB (con fuente) y ejemplos

### 2.1 Unidades

| Concepto | Regla | Fuente |
|---|---|---|
| **Lectura fuerte** | 1 unidad por 4 KB (o fracción) | [R-02, R-07] |
| **Lectura eventualmente consistente** | ½ unidad por 4 KB | [R-02] |
| **Lectura transaccional** | 2 unidades por 4 KB | [R-02] |
| **Escritura** | 1 unidad por 1 KB (o fracción) | [R-02] |
| **Escritura transaccional** | 2 unidades por 1 KB: una para preparar y otra para confirmar. **Se consume aunque la transacción se cancele** | [R-02, R-04] |
| Redondeo de lecturas | El tamaño del ítem se redondea **hacia arriba al siguiente múltiplo de 4 KB** (3.500 B cuesta lo mismo que 4 KB) | [R-02] |
| Redondeo de escrituras | Hacia arriba al siguiente 1 KB (500 B = 1 WRU) | [R-02] |
| `Query` | Suma el tamaño de **todos** los ítems devueltos y redondea una sola vez a 4 KB (10 ítems de 40,8 KB → 44 KB) | [R-02] |
| `BatchGetItem` / `BatchWriteItem` | Cada ítem se redondea **por separado** y luego se suma (1,5 KB + 6,5 KB = 4 + 8 = 12 KB) | [R-02] |
| `UpdateItem` | Cobra el **mayor** entre el tamaño del ítem antes y después, aunque se cambie un solo atributo | [R-02] |
| Escritura condicional que **falla** | Consume igual la capacidad de escritura | [R-02] |
| Lectura de un ítem inexistente | Consume capacidad igual | [R-02] |
| GSI: lectura | Solo **eventual** (½ unidad por 4 KB); `GetItem` y `BatchGetItem` **no** se pueden usar en un GSI | [R-03] |
| GSI: escritura | Cada escritura de tabla que afecte al índice consume escritura **del índice**: alta = 1; cambio del valor de la clave del índice = **2** (borra y crea); cambio solo de atributos proyectados = 1; si el ítem no está ni estaba en el índice (índice disperso) = 0. Si el GSI no tiene capacidad suficiente, **se frena la tabla base** | [R-03] |
| Tamaño de ítem | Máx. 400 KB; **el nombre del atributo cuenta** | [R-07] |
| Almacenamiento de un GSI | Clave primaria de la tabla + clave del índice + atributos proyectados + **100 B de sobrecarga por ítem** | [R-03] |
| Almacenamiento de la tabla | Tamaño crudo + "sobrecarga por ítem que depende de las funciones habilitadas" (**no publica cifra**) | [R-36] |

### 2.2 Ejemplos numéricos con los ítems de BoletaYa

| Operación | Cálculo | Resultado |
|---|---|---|
| `GetItem` de una silla (100 B) | ⌈100 B / 4 KB⌉ = 1 | **1 RRU** fuerte · **0,5** eventual · **2** transaccional |
| `Query` de una fila de 50 sillas | 50 × 100 B = 5.000 B = 4,88 KiB → ⌈4,88 / 4⌉ = 2 | **2 RRU** fuerte · **1 RRU** eventual |
| `GetItem` de `ORDER` (2 KB) | ⌈2 / 4⌉ = 1 | **1 RRU** fuerte · 0,5 eventual |
| `BatchGetItem` de 3 boletas (1 KB c/u) | 3 × ⌈1/4⌉ = 3 | **3 RRU** fuertes |
| `UpdateItem` de una silla (A→L) | ⌈100 B / 1 KB⌉ = 1 | **1 WRU** · **2** si va dentro de una transacción |
| `PutItem` de `ORDER` (2 KB) | ⌈2 / 1⌉ = 2 | **2 WRU** · **4** transaccional |
| `PutItem` de `PAY#nn` (1,5 KB) | ⌈1,5 / 1⌉ = 2 | **2 WRU** · **4** transaccional |
| Referencia de factura (500 B) | 1 | **1 WRU** · 2 transaccional |
| Una transacción de bloqueo con 2,5 sillas | 2,5 × 2 (sillas) + 4 (orden) + 2 (límite) | **11 WRU** |
| La misma transacción **cancelada** por conflicto | Mismo cálculo [R-04] | **11 WRU** (no es gratis fallar) |
| Orden nueva en `gsi_usuario` + `gsi_evento_orden` | 2 índices × 1 | **+2 WRU** |
| Lectura exacta de un contador con N = 8 | 8 ítems pequeños | **8 RRU** (`BatchGetItem` fuerte) · **16** (`TransactGetItems`) |

### 2.3 Límites relevantes y su implicación de diseño

| Límite | Valor | Implicación | Fuente |
|---|---|---|---|
| Por **partición** | 3.000 lecturas/s y 1.000 escrituras/s | No concentrar un evento en una clave (modelo §4) | [R-12] |
| Por **ítem** (vive en una partición) | ≈ 1.000 WRU/s ≈ 500 transacciones/s sobre el mismo ítem | Contadores fragmentados; sillas calientes | [R-12, R-19] |
| Tabla on-demand **nueva** | 4.000 escrituras/s y 12.000 lecturas/s sostenibles; acepta de inmediato hasta **2× el pico previo**; superar 2× en 30 min puede dar *throttling* | Pre-calentar antes de cada preventa grande | [R-13] |
| Cuota por tabla (on-demand) | 40.000 RRU y 40.000 WRU/s (ajustable) | Suficiente; ver T6 | [R-13, R-14] |
| Provisionado | Se puede subir "tan seguido como haga falta" pero **no muy rápido**; bajar: 4 al inicio del día + 1 por hora (máx. 27/día) | Escalado programado con anticipación | [R-14] |
| Auto scaling | Dispara tras **2 minutos consecutivos** sobre el objetivo y tarda **"varios minutos"**; lo que supere la capacidad previa **se rechaza** mientras tanto | No sirve para picos escalonados | [R-20] |
| *Burst capacity* | Hasta 300 s de capacidad sin usar | Amortigua picos cortos, no un evento de 20 min | [R-19] |
| Transacción | ≤ 100 ítems, ≤ 4 MB, misma región y cuenta | Máx. 10 sillas/orden (A-09) | [R-04, R-07] |
| `Query` / `Scan` | 1 MB por página | Lectura de tickets de un evento: 9–10 páginas | [R-07] |
| `BatchGetItem` / `BatchWriteItem` | 100 ítems/16 MB · 25 ítems/16 MB | Lecturas por lote | [R-07] |
| GSI por tabla | 20 (defecto) | Se usan 1–3 por tabla | [R-14] |
| Streams | Retención 24 h; ≤ 2 lectores por *shard* | Consumidores idempotentes + alarma de edad | [R-11, R-07] |
| Exportación incremental | Ventana de 15 min a 24 h | Exportación diaria | [R-14] |
| Cambio provisionado → on-demand | 4 veces en 24 h (la inversa, sin límite) | Cambiar de modo no es una palanca para cada preventa | [R-13] |

---

## 3. Volumetría de los años 1 a 5

### 3.1 Supuestos y tasas (cada entidad con su propia regla)

| Entidad | Regla de crecimiento | Tasa | Justificación | Origen |
|---|---|---|---|---|
| Usuarios (existencias) | Uₙ = 2.500.000 × 1,40ⁿ⁻¹ | **40 %** | `DATO`: usuarios registrados +40 % anual | Enunciado |
| Boletas | Bₙ = 4.000.000 × 1,30ⁿ⁻¹ | **30 %** | `DATO`: boletas vendidas +30 % anual | Enunciado |
| Órdenes | Oₙ = 1.600.000 × 1,30ⁿ⁻¹ | 30 % | 2,5 boletas por orden (constante): Bₙ / 2,5 | Derivado de `DATO` (4.000.000 / 2,5 = 1.600.000 ✔) |
| Intentos de pago | Pₙ = 1,3 × Oₙ | 30 % | Ratio `DATO` constante | Derivado |
| Referencias de factura | Fₙ = 1,0 × Oₙ | 30 % | 1 por orden `DATO` | Derivado |
| Escaneos | Sₙ = 1,2 × Bₙ | 30 % | 1,2 por boleta `DATO` | Derivado |
| **Eventos** | Eₙ = 1.800 × 1,30ⁿ⁻¹ | 30 % | **A-01.** El enunciado no define su crecimiento. Si los eventos fueran constantes, la ocupación pasaría de 74,1 % a **96,3 % (año 2), 125,2 % (año 3) y 211,6 % (año 5)**: imposible. Crecer como las boletas mantiene la ocupación en **74,1 %** | **Supuesto** (impacto: sillas e historial) |
| Sillas | SILₙ = Eₙ × 3.000 | 30 % | `DATO`: 3.000 sillas por evento en promedio (incluye estadios de 45.000) | Derivado de A-01 |
| Historial de sillas | Hₙ = 4 × SILₙ | 30 % | `DATO`: 4 cambios por silla en promedio | Derivado |
| **Auditoría** | Aₙ = 60.000.000 × 1,30ⁿ⁻¹ | 30 % | **A-02.** `DATO` da 5 M/mes sin crecimiento; asumo que acompaña la actividad (boletas) | **Supuesto** |

**Nota sobre las preventas.** Las 25 preventas grandes **no crecen en sillas** `DATO`: 60.000 boletas cada una en todos los años. Solo crece la cola (+25 %). Por tanto el **pico de escritura es constante** en el tiempo (el 30 % de crecimiento de boletas lo absorbe la operación normal y los eventos medianos), mientras el **pico de lectura del mapa** sí crece (§6). Como las 25 preventas aportan 1.500.000 boletas fijas, el crecimiento implícito de la operación normal es **mayor** que 30 %; para el dimensionamiento uso 8.000 × 1,3ⁿ⁻¹ boletas/día (conservador y simple; la diferencia es inmaterial porque la carga normal es ≈ 0,1 % de la del pico).

**Redondeo:** cada cantidad se calcula con decimales y se redondea **al entero más cercano**. Unidad: registros. Los tamaños son `DATO` crudos (sin índices ni sobrecarga).

### 3.2 Cantidad de registros

| Entidad | Tamaño crudo | Año 1 | Año 2 | Año 3 | Año 4 | Año 5 | Fórmula |
|---|---:|---:|---:|---:|---:|---:|---|
| Usuarios | 1,5 KB | 2.500.000 | 3.500.000 | 4.900.000 | 6.860.000 | 9.604.000 | 2.500.000 × 1,40ⁿ⁻¹ |
| Eventos | 4 KB | 1.800 | 2.340 | 3.042 | 3.955 | 5.141 | 1.800 × 1,30ⁿ⁻¹ |
| Sillas | 100 B | 5.400.000 | 7.020.000 | 9.126.000 | 11.865.000 | 15.423.000 | Eventos × 3.000 |
| Historial de sillas | 150 B | 21.600.000 | 28.080.000 | 36.504.000 | 47.460.000 | 61.692.000 | Sillas × 4 |
| Órdenes | 2 KB | 1.600.000 | 2.080.000 | 2.704.000 | 3.515.200 | 4.569.760 | 1.600.000 × 1,30ⁿ⁻¹ |
| Intentos de pago | 1,5 KB | 2.080.000 | 2.704.000 | 3.515.200 | 4.569.760 | 5.940.688 | Órdenes × 1,3 |
| Boletas | 1 KB | 4.000.000 | 5.200.000 | 6.760.000 | 8.788.000 | 11.424.400 | 4.000.000 × 1,30ⁿ⁻¹ |
| Escaneos | 250 B | 4.800.000 | 6.240.000 | 8.112.000 | 10.545.600 | 13.709.280 | Boletas × 1,2 |
| Ref. factura (CUFE) | 500 B | 1.600.000 | 2.080.000 | 2.704.000 | 3.515.200 | 4.569.760 | Órdenes × 1 |
| Auditoría | 300 B | 60.000.000 | 78.000.000 | 101.400.000 | 131.820.000 | 171.366.000 | 5.000.000 × 12 × 1,30ⁿ⁻¹ |

### 3.3 Datos crudos por año (GiB; usuarios = existencias)

| Entidad | Año 1 | Año 2 | Año 3 | Año 4 | Año 5 | Fórmula |
|---|---:|---:|---:|---:|---:|---|
| Usuarios | 3,58 | 5,01 | 7,01 | 9,81 | 13,74 | registros × 1.536 B / 2³⁰ |
| Eventos | 0,01 | 0,01 | 0,01 | 0,02 | 0,02 | × 4.096 B |
| Sillas | 0,50 | 0,65 | 0,85 | 1,11 | 1,44 | × 100 B |
| Historial | 3,02 | 3,92 | 5,10 | 6,63 | 8,62 | × 150 B |
| Órdenes | 3,05 | 3,97 | 5,16 | 6,70 | 8,72 | × 2.048 B |
| Intentos de pago | 2,98 | 3,87 | 5,03 | 6,54 | 8,50 | × 1.536 B |
| Boletas | 3,81 | 4,96 | 6,45 | 8,38 | 10,90 | × 1.024 B |
| Escaneos | 1,12 | 1,45 | 1,89 | 2,46 | 3,19 | × 250 B |
| Ref. factura | 0,75 | 0,97 | 1,26 | 1,64 | 2,13 | × 500 B |
| Auditoría | 16,76 | 21,79 | 28,33 | 36,83 | 47,88 | × 300 B |
| **Total flujo del año** | **35,6** | **46,6** | **61,1** | **80,1** | **105,1** | |

> Todos los tamaños "KB" del enunciado se toman como múltiplos de 1.024 B (1,5 KB = 1.536 B).

### 3.4 Tamaño facturado, índices, espacio libre y archivo en S3 (cinco conceptos distintos)

**(1) Cantidad de registros** — §3.2.
**(2) Datos crudos** — §3.3 (`DATO` del enunciado).
**(3) Tamaño facturado por DynamoDB (en línea)** = crudo + sobrecarga por ítem. **A-03:** uso **100 B por ítem de tabla**: la documentación vigente de precios dice que existe "una sobrecarga por ítem que depende de las funciones habilitadas" y **no da la cifra** [R-36]; 100 B es el valor documentado para los ítems de GSI [R-03] y el que históricamente se citaba para tablas (**no verificado en documentación actual → PENDIENTE; sensibilidad: ±100 B por ítem mueve el total ≈ ±10 %**).
**(4) Tamaño de índices (GSI)** = (claves de la tabla + clave del índice + atributos proyectados + **100 B**) × ítems indexados [R-03]. Índices diseñados y su tamaño por entrada: `gsi_email` 85 + 100 B · `gsi_org_fecha` 170 + 100 · `gsi_usuario` 152 + 100 · `gsi_evento_orden` 160 + 100 · `gsi_evento_boleta` 170 + 100 · `gsi_actor` 110 + 100 (**dispersa: solo acciones humanas, A-07 = 5 %**) · `gsi_pendientes` (dispersa; en estado estable casi vacía). Las **sillas no tienen GSI**.
**(5) Datos históricos archivados en S3** = lo que sale de línea (retención en línea **A-04**, sujeta a validación legal): órdenes, pagos, boletas, referencias de factura, historial y auditoría **2 años** `DATO` para órdenes/pagos/boletas; escaneos **1 año**; sillas: se cuentan en línea **todo el año** (conservador; el TTL a 90 días tras el evento ahorra más); usuarios: siempre en línea. Se archivan en bruto (supuesto: el JSON comprimido de la exportación ≈ bytes crudos; **no cuantifico compresión**).

**Compresión y espacio libre (C-5):** DynamoDB factura el tamaño calculado del ítem; **no hay compresión ni espacio libre que estimar**. Se puede comprimir un atributo grande del lado del cliente, pero con ítems de ≤ 2 KB no vale la pena.

#### Espacio total facturado **en línea** (tabla + sus GSI), GiB

| Entidad | Año 1 | Año 2 | Año 3 | Año 4 | Año 5 | Retención en línea |
|---|---:|---:|---:|---:|---:|---|
| Usuarios | 4,24 | 5,94 | 8,31 | 11,63 | 16,29 | siempre |
| Eventos | 0,01 | 0,02 | 0,02 | 0,03 | 0,04 | 2 años |
| Sillas | 1,01 | 1,31 | 1,70 | 2,21 | 2,87 | año en curso |
| Historial | 5,03 | 11,57 | 15,04 | 19,55 | 25,41 | 2 años |
| Órdenes | 3,96 | 9,12 | 11,85 | 15,41 | 20,03 | 2 años |
| Pagos | 3,17 | 7,29 | 9,48 | 12,32 | 16,01 | 2 años |
| Boletas | 5,19 | 11,94 | 15,53 | 20,19 | 26,24 | 2 años |
| Escaneos | 1,56 | 2,03 | 2,64 | 3,44 | 4,47 | 1 año |
| Ref. factura | 0,89 | 2,06 | 2,67 | 3,48 | 4,52 | 2 años |
| Auditoría | 22,94 | 52,76 | 68,59 | 89,16 | 115,91 | 2 años |

#### Resumen por año (GiB)

| Año | Crudo del año | En línea: crudo | En línea: facturado (crudo + 100 B/ítem) | **Índices GSI** | **Total en línea (tablas + GSI)** | **Archivado acumulado en S3 (crudo)** |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 35,6 | 35,6 | 45,2 | 2,8 | **48,0** | 0,0 |
| 2 | 46,6 | 77,0 | 98,0 | 6,0 | **104,0** | 1,6 |
| 3 | 61,1 | 100,6 | 127,9 | 7,9 | **135,8** | 34,1 |
| 4 | 80,1 | 131,4 | 167,1 | 10,3 | **177,4** | 76,3 |
| 5 | 105,1 | 171,9 | 218,2 | 13,6 | **231,8** | 131,2 |

#### Sobrecarga por índice (GiB, en línea)

| Índice (entidad base) | Año 1 | Año 2 | Año 3 | Año 4 | Año 5 |
|---|---:|---:|---:|---:|---:|
| `gsi_email` (usuarios) | 0,43 | 0,60 | 0,84 | 1,18 | 1,65 |
| `gsi_usuario` (órdenes) | 0,38 | 0,86 | 1,12 | 1,46 | 1,90 |
| `gsi_evento_orden` (órdenes) | 0,39 | 0,89 | 1,16 | 1,51 | 1,96 |
| `gsi_evento_boleta` (boletas) | 1,01 | 2,31 | 3,01 | 3,91 | 5,08 |
| `gsi_actor` (auditoría, 5 %) | 0,59 | 1,35 | 1,75 | 2,28 | 2,96 |
| `gsi_org_fecha` (eventos) | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |

**Lectura.** La auditoría es **la mitad** del espacio (≈ 116 de 232 GiB en el año 5) por 171 M de registros/año: se aloja en **Standard-IA** y se limita a 1–2 años en línea. El almacenamiento total es modesto: **231,8 GiB** al año 5.

### 3.5 Tabla maestra pedida (año 5 como ejemplo; las demás columnas están en §3.2–§3.4)

| Entidad | Tamaño/registro | Cantidad Y1 → Y5 | Crudo Y1 → Y5 (GiB) | Sobrecarga de índices Y5 | Espacio total en línea Y5 | Fórmula | Fuente / supuesto |
|---|---|---|---|---:|---:|---|---|
| Usuarios | 1,5 KB | 2,5 M → 9,6 M | 3,58 → 13,74 | 1,65 | 16,29 | 2,5 M × 1,4ⁿ⁻¹ | `DATO`, A-05 |
| Eventos | 4 KB | 1.800 → 5.141 | 0,01 → 0,02 | ≈ 0 | 0,04 | 1.800 × 1,3ⁿ⁻¹ | A-01 |
| Sillas | 100 B | 5,4 M → 15,4 M | 0,50 → 1,44 | 0 | 2,87 | Eventos × 3.000 | `DATO`, A-01 |
| Historial | 150 B | 21,6 M → 61,7 M | 3,02 → 8,62 | 0 | 25,41 | Sillas × 4 | `DATO`, A-01 |
| Órdenes | 2 KB | 1,6 M → 4,57 M | 3,05 → 8,72 | 3,86 | 20,03 | 1,6 M × 1,3ⁿ⁻¹ | `DATO` |
| Pagos | 1,5 KB | 2,08 M → 5,94 M | 2,98 → 8,50 | 0 (dispersa) | 16,01 | Órdenes × 1,3 | `DATO` |
| Boletas | 1 KB | 4 M → 11,4 M | 3,81 → 10,90 | 5,08 | 26,24 | 4 M × 1,3ⁿ⁻¹ | `DATO` |
| Escaneos | 250 B | 4,8 M → 13,7 M | 1,12 → 3,19 | 0 | 4,47 | Boletas × 1,2 | `DATO` |
| Ref. factura | 500 B | 1,6 M → 4,57 M | 0,75 → 2,13 | 0 (dispersa) | 4,52 | Órdenes × 1 | `DATO` |
| Auditoría | 300 B | 60 M → 171,4 M | 16,76 → 47,88 | 2,96 | 115,91 | 5 M × 12 × 1,3ⁿ⁻¹ | `DATO`, A-02, A-07 |

---

## 4. Carga en operación normal

`DATO`: 8.000 boletas/día en 16 h (7:00–23:00); 2,5 boletas/orden. Tasas **promedio** (la distribución horaria no se da; no se asume pico horario; ver nota).

| Métrica | Año 1 | Año 5 | Fórmula |
|---|---:|---:|---|
| Boletas por día | 8.000 | 22.849 | 8.000 × 1,3ⁿ⁻¹ |
| Boletas por hora | 500,0 | 1.428,1 | día / 16 |
| Boletas por minuto | 8,33 | 23,80 | hora / 60 |
| Órdenes por día | 3.200 | 9.140 | boletas / 2,5 |
| Órdenes por hora | 200,0 | 571,2 | / 16 |
| Órdenes por minuto | 3,33 | 9,52 | / 60 |
| Órdenes por segundo | 0,0556 | 0,1587 | / 3.600 |
| **WRU por orden** (camino feliz + 30 % de órdenes abandonadas) | 62,4 | 62,4 | §5.1 |
| **WRU por segundo (promedio)** | **3,47** | **9,90** | órdenes/s × WRU/orden |
| WRU por día | 199.589 | 570.045 | órdenes/día × WRU/orden |
| **RRU por orden** | 11,75 | 11,75 | §5.3 |
| RRU por segundo | 0,65 | 1,86 | |

**Qué es transaccional y qué auxiliar.**
* **Transaccional (cuesta ×2):** bloqueo de sillas, confirmación (silla → vendida + orden pagada + intento aprobado + contador + boletas + referencia de factura), registro de escaneo válido (§3.5 del modelo).
* **Auxiliar (cuesta ×1, puede reintentarse):** alta y rechazo de intentos de pago, emisión de factura (`INV` → `ISSUED`), **historial de sillas derivado por Streams**, auditoría, índices.

**Notas.** (a) Si la carga normal tuviera un pico horario de, p. ej., 3× el promedio, seguiría en ≈ 10 WRU/s. (b) Sensibilidad C-3: 100 órdenes/min = 1,67 órdenes/s → **104 WRU/s** (3 % de los 4.000 WRU/s iniciales de una tabla on-demand). (c) La operación normal es **tan pequeña** que dimensionar la base para ella es irrelevante: manda el pico.

---

## 5. Preventa grande

### 5.1 Qué escrituras genera **una** compra (el desglose que nadie debe sumar "a ojo")

Se cuenta **por orden completada** en el **camino feliz mínimo** (1 intento aprobado, ningún bloqueo fallido, ninguna orden abandonada) y luego se añaden los efectos de reintentos, conflictos y abandono por separado. Con 2,5 sillas por orden:

| # | Operación | Tipo | Cálculo | WRU |
|---|---|---|---|---:|
| 1 | **Transacción de bloqueo**: 2,5 sillas A→L (100 B) + `ORDER` PENDING (2 KB) + límite antibot | Transacción | 2,5 × 1 × 2 + 2 × 2 + 1 × 2 | **11,0** |
| 2 | Índices por alta de `ORDER` (`gsi_usuario`, `gsi_evento_orden`) | Propagación GSI | 2 × 1 | **2,0** |
| 3 | Intento de pago aprobado: `PutItem PAY#01` (1,5 KB) + entrada en `gsi_pendientes` | No transaccional | 2 + 1 | **3,0** |
| 4 | Rechazos: 0,30 órdenes × k=1 × (Put 2 + índice 1 + Update 2 + borrar índice 1) | No transaccional | 0,30 × 6 | **1,8** |
| 5 | **Transacción de confirmación**: 2,5 sillas L→S + `ORDER`→PAID (2 KB) + `PAY`→APPROVED (1,5 KB) + contador + 2,5 boletas (1 KB) + `INV` PENDING (500 B) | Transacción | 5 + 4 + 4 + 2 + 5 + 2 | **22,0** |
| 6 | Índices de la confirmación: `ORDER.st` en 2 GSI + borrar pago pendiente + alta factura pendiente + 2,5 entradas `gsi_evento_boleta` | Propagación GSI | 2 + 1 + 1 + 2,5 | **6,5** |
| 7 | Emisión de factura: `UpdateItem INV`→ISSUED (500 B) + borrar `gsi_pendientes` | No transaccional | 1 + 1 | **2,0** |
| 8 | **Historial de sillas** (Streams → Lambda): 2 cambios de estado por silla (A→L, L→S), 150 B | No transaccional | 2,5 × 2 × 1 | **5,0** |
| 9 | **Auditoría**: 2 registros por orden (300 B) | No transaccional | 2 × 1 | **2,0** |
| | **Total mínimo por orden completada** | | | **55,3** |

Por tabla: sillas 10 · órdenes 18,2 · límites 2 · contadores 2 · boletas 5 · historial 5 · auditoría 2 · `gsi_ordenes` 4 · `gsi_pendientes` 4,6 · `gsi_boletas` 2,5.

**Supuestos propios de este cálculo.** (S-1) La propagación a GSI de un ítem escrito dentro de una transacción factura **una** escritura por entrada de índice (la documentación consultada no lo detalla; sensibilidad ×2 en §5.4; **PENDIENTE**). (S-2) Un ítem de boleta de "1 KB" cuesta 1 WRU (si por nombres de atributos supera 1.024 B, cuesta 2; sensibilidad §5.4). (S-3) Los historiales se escriben una vez por cambio de estado (no se duplican por reintentos de Lambda porque la clave es determinista). (S-4) Las lecturas de Streams que hace Lambda no consumen RCU de la tabla [R-11]; su precio de lectura de *stream* **queda PENDIENTE** para Juan Pablo.

### 5.2 Tasas de la preventa

| Concepto | Valor | Fórmula |
|---|---:|---|
| Boletas por minuto (promedio) | 3.000 | 60.000 / 20 |
| Boletas por segundo | 50,0 | 60.000 / 1.200 |
| **Órdenes en la preventa** | **24.000** | 60.000 / 2,5 |
| **Órdenes por segundo (promedio de 20 min)** | **20,0** | 24.000 / 1.200 |
| Intentos de pago totales (k = 1) | 31.200 (26/s) | 24.000 × 1,3 |
| Intentos **adicionales** (rechazados) | 7.200 | 24.000 × 0,30 |
| Compradores simultáneos en la fase transaccional (Little: λ × duración de sesión) | 4.800 con sesión de 240 s (2.400–9.600 para 120–480 s) | 20/s × 240 s |

**Tasa promedio vs. tasa máxima instantánea.** El enunciado **no da la distribución dentro de los 20 minutos** (**limitación L-1**). Planteo tres niveles:

* **×1 (promedio):** 20 órdenes/s.
* **×3 (ráfaga sostenida):** las 60.000 boletas en ≈ 6,7 min → 60 órdenes/s.
* **×5 (pico instantáneo razonado):** las 60.000 boletas en **4 min** → **100 órdenes/s = 250 boletas/s**. Es pesimista pero físicamente consistente con la cola: la admisión de compradores la regula la cola virtual; un estadio de 45.000 sillas no se agota en menos de unos minutos con 24.000 órdenes de 2,5.

**Margen recomendado:** +25 % sobre el pico ×5 para dimensionar capacidad provisionada o pre-calentamiento.

### 5.3 Los tres escenarios de dimensionamiento

Parámetros: *k* = rechazos por orden afectada · *f* = transacciones de bloqueo fallidas por exitosa · *b* = fracción de órdenes iniciadas que se abandonan.

| Escenario | k | f | b | Otros | WRU / orden |
|---|---:|---:|---:|---|---:|
| **Mínimo** | 1 | 0 | 0 % | — | **55,3** |
| **Planificación** (base) | 1 | 2 | 30 % | — | **84,4** |
| **Estrés** | 3 | 8 | 50 % | boleta = 2 WRU, índices en transacción ×2, 5 auditorías | **182,9** |

*f* y *b* son **supuestos de planificación (A-10)**: el enunciado no da tasas de conflicto ni de abandono. Un bloqueo fallido cuesta lo mismo que uno exitoso [R-04]; un abandono (el cliente no paga) cuesta el bloqueo, la orden pendiente y el historial A→L; las sillas "vuelven a quedar disponibles" **sin escritura** porque el vencimiento se evalúa en la condición.

**Escrituras de la preventa (WRU) por escenario y factor de ráfaga**

| Escenario | WRU/orden | WRU totales (24.000 órdenes) | WRU/s ×1 | WRU/s ×3 | WRU/s ×5 | +25 % margen |
|---|---:|---:|---:|---:|---:|---:|
| Mínimo | 55,3 | 1.327.200 | 1.106 | 3.318 | 5.530 | 6.912 |
| **Planificación** | **84,4** | **2.024.914** | **1.687** | **5.062** | **8.437** | **10.546** |
| Estrés | 182,9 | 4.389.600 | 3.658 | 10.974 | 18.290 | 22.862 |

**Distribución por tabla en la ráfaga ×5 (WRU/s)** — comparar con **4.000 WRU/s** (capacidad inicial de una tabla on-demand nueva) y 1.000 WRU/s por partición:

| Tabla / índice | Planificación ×5 | Estrés ×5 | ¿Excede 4.000? |
|---|---:|---:|---|
| `bya_seats` (sillas) | 2.214 | **5.500** | Estrés: sí → pre-calentar |
| `bya_orders` (órdenes + pagos + facturas) | 2.791 | **5.660** | Estrés: sí → pre-calentar |
| `bya_counters`: límites antibot | 686 | 2.000 | no |
| `bya_counters`: contador de localidad | 200 | 200 | no |
| `bya_tickets` (boletas) | 500 | 1.000 | no |
| `bya_seat_history` | 607 | 750 | no |
| `bya_audit` | 243 | 600 | no |
| `gsi_ordenes` (2 GSI) | 486 | 1.200 | no |
| `gsi_pendientes` | 460 | 880 | no |
| `gsi_boletas` | 250 | 500 | no |

### 5.4 Sensibilidad: reintentos de pago y otros supuestos

El **30 % con "al menos un rechazo"** no implica un solo rechazo. Intentos por orden = 1 + 0,30 × *k*:

| Variante | Intentos de pago por orden | WRU / orden | WRU/s ×1 | WRU/s ×5 |
|---|---:|---:|---:|---:|
| **Base** (k = 1, f = 2, b = 30 %) | 1,30 | **84,4** | 1.687 | 8.437 |
| k = 2 rechazos | 1,60 | 86,2 | 1.723 | 8.617 |
| k = 3 rechazos | 1,90 | 88,0 | 1.759 | 8.797 |
| Boleta de 2 KB (2 WRU) | 1,30 | 89,4 | 1.787 | 8.937 |
| Índices en transacción cuentan doble | 1,30 | 94,7 | 1.895 | 9.473 |
| **f = 8** bloqueos fallidos por exitoso | 1,30 | **150,4** | 3.007 | **15.037** |
| Abandono 50 % | 1,30 | 93,8 | 1.876 | 9.380 |
| 5 auditorías por orden | 1,30 | 87,4 | 1.747 | 8.737 |

**Conclusión.** Los **reintentos de pago casi no mueven la aguja** (+4 % al pasar de k = 1 a k = 3). Lo que más pesa es **la contención sobre las sillas** (*f*): de f = 2 a f = 8 el pico sube **78 %**. Por eso el diseño ataca el conflicto antes de la base (cola virtual, pista negativa en caché, límite por usuario).

### 5.5 Lecturas en la preventa (RRU/s)

Por orden: 3 lecturas fuertes de `ORDER` (3 × 1) + 2,5 boletas por `BatchGetItem` (2,5 × 1) + 10 sondeos del estado del pago eventuales (10 × 0,5) + prechequeo eventual de 2,5 sillas por intento (2,5 × 0,5 × (1 + f)) = **11,75** (mínimo) · **14,25** (planificación) · **21,75** (estrés).

| Fuente | RRU/s | Fórmula |
|---|---:|---|
| Órdenes, planificación ×5 | 1.425 | 100 ord/s × 14,25 |
| Órdenes, estrés ×5 | 2.175 | 100 × 21,75 |
| **Constructor del mapa** (estadio 45.000 sillas, 900 filas × 1 RRU, refresco cada 2 s) | **450** | 900 / 2 |
| Constructor del mapa con refresco cada 5 s | 180 | 900 / 5 |
| Tablero de contadores (16 fragmentos × 20 localidades × 1/s, `BatchGetItem` fuerte) | 320 | 16 × 20 × 1 |
| Ídem con `TransactGetItems` | 640 | × 2 |
| **Total lecturas de preventa, planificación ×5** | **≈ 2.200** | 1.425 + 450 + 320 |

Muy por debajo de los **12.000 RRU/s** iniciales de una tabla on-demand [R-13].

---

## 6. Mapa de sillas con 250.000 personas y cola virtual

### 6.1 Crecimiento de la cola

`DATO`: +25 % anual. Qₙ = 250.000 × 1,25ⁿ⁻¹.

| Año | 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| Personas en cola | 250.000 | 312.500 | 390.625 | 488.281 | 610.352 |

### 6.2 Tres escenarios de consulta

No asumo "una consulta por persona": cada persona **sondea** el mapa. Supuestos por escenario (A-11): 250.000 personas simultáneas, duración **20 min** (1.200 s), carga útil de **3 KB** por consulta (resumen de la sala + mapa de bits de la localidad: 2 bits por silla; **todo un estadio de 45.000 sillas = 11 KiB**), consulta directa de una localidad de 2.250 sillas = 220 KiB = 27,5 RRU eventuales.

| Escenario | Intervalo de sondeo | Solicitudes/s | **RRU/s si TODO fuera a DynamoDB** | × cuota 40.000 | Solicitudes en 20 min |
|---|---:|---:|---:|---:|---:|
| Moderada | 30 s | 8.333 | 229.167 | 5,7× | 10.000.000 |
| **Alta** (la que implica el glosario: "25.000 consultas por segundo") | 10 s | **25.000** | 687.500 | **17,2×** | 30.000.000 |
| Extrema | 3 s | 83.333 | 2.291.667 | 57,3× | 100.000.000 |
| Extrema, año 5 (610.352 personas) | 3 s | 203.451 | 5.594.889 | 139,9× | 244.140.625 |

**Conclusión:** servir el mapa desde DynamoDB es **imposible** incluso en el escenario moderado (5,7× la cuota por tabla; y 3.000 RCU/s por partición [R-12]).

### 6.3 Arquitectura de lectura (qué va a la base y qué no)

```
Usuarios (250.000) ── CloudFront (TTL 2 s) ── S3 (instantáneas JSON/bitmap, 21 objetos por evento)
                                                      ▲  (se reescriben cada 1–2 s)
        DynamoDB Streams ► Lambda ► ElastiCache (mapa vivo) ► Publicador ─┘
        (cambios de bya_seats)          ▲
                                        └─ reconstrucción completa cada 30 s desde bya_seats (Query por filas)
```

* **Aproximado para navegar:** instantánea de la localidad (bitmaps) con retraso ≈ 3–6 s (Streams + publicador 1–2 s + TTL de CDN 2 s: **estimación, no medición**).
* **Definitivo para comprar:** únicamente la **transacción** del §7 del modelo. Una silla que la caché marca "libre" se intenta igual; una que marca "vendida" se rechaza sin tocar la base (error a favor de no vender).
* **Invalidación:** (1) por cambio: Streams actualiza el mapa vivo; (2) por reconstrucción periódica contra la base (corrige pérdidas del *stream*); (3) por expiración de CDN. Las instantáneas se **sobrescriben**, no se invalidan una a una.
* **Cómo se avisa al usuario que una silla ya no está:** el `TransactionCanceledException` trae `CancellationReasons` por ítem [R-04]: la API responde 409 con las sillas que fallaron; el cliente las marca y pide elegir otra. El siguiente sondeo corrige el resto.
* **Sondeo adaptativo:** el servidor indica el próximo intervalo (más largo para quienes están lejos en la cola) → recorta el costo 5–10× frente a un sondeo fijo.

Los sondeos de **posición en la cola** (250.000 × cada 10 s) también van a un objeto cacheable ("posición atendida") y no a una API: cada cliente compara su turno localmente; solo quien ya fue admitido llama al API (token de admisión).

### 6.4 Carga residual y costo del mapa por preventa (año 1)

| Escenario | Solicitudes/s | Ancho de banda | GB por preventa | CloudFront solicitudes | CloudFront salida | **USD/preventa** | **USD/año (25)** | RRU/s a DynamoDB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Moderada | 8.333 | 200 Mbps | 30,0 | 22,0 | 3,3 | **25,3** | 632 | 450 |
| Alta | 25.000 | 600 Mbps | 90,0 | 66,0 | 9,9 | **75,9** | 1.898 | 450 |
| Extrema | 83.333 | 2.000 Mbps | 300,0 | 220,0 | 33,0 | **253,0** | 6.325 | 450 |
| Extrema, año 5 | 203.451 | 4.883 Mbps | 732,4 | 537,1 | 80,6 | **617,7** | 15.442 | 450 |

Precios de CloudFront, lista oficial (consulta 2026-10-29), zona "South America": **USD 2,20 por millón de solicitudes HTTPS** y **USD 0,11/GB** (primeros 10 TB) [R-16]. **A-06:** Colombia se factura en esa zona (**PENDIENTE de confirmar** en la calculadora). Los precios por volumen bajan en tramos superiores; no los apliqué (conservador).

**Para Juan Pablo (orden de magnitud, año 1):** el escenario "Alta" cuesta ≈ **USD 1.900/año** (≈ COP 7,6 M); el "Extremo del año 5", ≈ **USD 15.400/año** (≈ COP 61,8 M), que es ≈ 48 % del tope anual de COP 130 M: **es la sensibilidad de "doble de personas en la cola" que debe revisar**. El API dinámico (HTTP API) cuesta ≈ USD 1,1–1,8 por preventa; ElastiCache (2 nodos `cache.m7g.large`, 24×7) ≈ USD 2.215 (us-east-1) / USD 3.154 (sa-east-1) al año; la cola virtual comercial o propia queda **PENDIENTE** (el producto "Virtual Waiting Room on AWS" está **discontinuado** [R-29]).

---

## 7. Comparación de opciones de capacidad

### 7.1 Las tres opciones

| | **A. On-demand** | **B. Provisionado** (B1 fijo al pico · B2 escalado programado · B3 auto scaling) | **C. Arquitectura híbrida de lectura** (superposición, no alternativa) |
|---|---|---|---|
| **Idea** | Se paga por solicitud; sin capacidad que administrar | Se fija RCU/WCU por hora; se paga lo provisionado, se use o no | DynamoDB solo transaccional + CDN/caché + cola + analítica en S3/Athena |
| **Comportamiento en un salto súbito** | Absorbe de inmediato hasta **2× el pico previo**; más allá puede dar *throttling* si se supera 2× en 30 min; tabla nueva: 4.000 W / 12.000 R [R-13]. **Pre-calentable** [R-18] | Atiende **solo hasta lo provisionado**; lo que exceda se rechaza. Subir no es instantáneo ("no muy rápido" [R-14]). B3: dispara tras 2 min de exceso y tarda "varios minutos" mientras se rechaza [R-20] | La CDN absorbe los 25.000–203.000 req/s del mapa; la cola limita la concurrencia transaccional |
| **Capacidad de escritura/lectura** | Hasta 40.000/40.000 por tabla (ajustable) [R-14] | Hasta 40.000 por tabla y 80.000 por cuenta (ajustables) [R-14] | n/a |
| **Throttling posible** | Sí si se supera 2× el pico en 30 min sin pre-calentar; mitigable | **Sí si el escalado no llega a tiempo** (B3) o el pico excede lo programado (B2) | Reduce la causa del *throttling*: menos lecturas |
| **Capacidad base necesaria** | Ninguna (escala a cero) [R-13] | B2: base ≈ 50 WCU / 50 RCU **en total** (carga normal ×3) + **10.546 WCU y 2.744 RCU** (suma de tablas e índices) durante ≈ 3 h por preventa (planificación ×5 + 25 %) | Cola + CDN + ElastiCache 24×7 |
| **Riesgo de capacidad insuficiente** | Bajo con pre-calentamiento | **Alto** si la preventa se adelanta o la demanda excede lo programado; las fechas de preventa se conocen, pero un error humano cuesta ventas | Baja, aguas arriba |
| **Costo anual de throughput (año 1)** | **USD 83 (us-east-1) – 124 (sa-east-1)** | B2: **USD 880 – 1.319** · B1: **USD 63.176 – 94.764** | CloudFront: USD 632–6.325; ElastiCache ≈ USD 2.200–3.150 |
| **Costo anual de throughput (año 5)** | USD 183 – 274 | B2: USD 1.077 – 1.616 | CloudFront año 5: hasta USD 15.442 |
| **Operación** | Sin ajustes; opcional **máximo de throughput** para limitar costo ante bots [R-13] | Acciones programadas (Application Auto Scaling): suben el mínimo antes y bajan el máximo después; la política reactiva puede seguir decidiendo dentro de ese rango [R-21] | Más componentes que operar |

**Umbral de equilibrio:** el provisionado resulta más barato que on-demand solo si el uso medio de la capacidad supera **28,9 %** (precio por WCU-hora ÷ (3.600 × precio por WRU) = 0,000975 / (3.600 × 0,9375 × 10⁻⁶) = 0,289; idéntico en us-east-1 con 0,00065 / (3.600 × 0,625 × 10⁻⁶)). Aquí el uso medio de una capacidad fija al pico es **0,037 %** (año 1): el provisionado fijo es **≈ 760 veces** más caro.

### 7.2 Costos anuales por opción, región y año (throughput, USD; planificación, f creciendo ×1,25ⁿ⁻¹)

| Región | Año | On-demand | Provisionado fijo al pico | Provisionado programado |
|---|---:|---:|---:|---:|
| sa-east-1 | 1 | 124 | 94.764 | 1.319 |
| sa-east-1 | 2 | 149 | 100.769 | 1.371 |
| sa-east-1 | 3 | 180 | 108.276 | 1.435 |
| sa-east-1 | 4 | 221 | 117.659 | 1.515 |
| sa-east-1 | 5 | 274 | 129.389 | 1.616 |
| us-east-1 | 1 | 83 | 63.176 | 880 |
| us-east-1 | 2 | 99 | 67.180 | 914 |
| us-east-1 | 3 | 120 | 72.184 | 957 |
| us-east-1 | 4 | 147 | 78.440 | 1.010 |
| us-east-1 | 5 | 183 | 86.259 | 1.077 |

Capacidad de pico a provisionar (planificación ×5 + 25 %): año 1 **10.546 WCU / 2.744 RCU**; año 5 **14.510 WCU / 3.194 RCU**. **Por preventa:** on-demand ≈ **USD 2,14** (sa-east-1) / **1,42** (us-east-1); provisionado programado, sobrecosto de 3 h de pico ≈ **USD 32,3** / **21,5**.

Precios (lista oficial, consulta 2026-10-29, versión 20260911124422) [R-23]: sa-east-1 → **USD 0,9375 por millón de WRU**, **0,1875 por millón de RRU**, **0,000975 por WCU-hora**, **0,000195 por RCU-hora**, **0,375 por GB-mes** · us-east-1 → **0,625 / 0,125 / 0,00065 / 0,00013 / 0,25**. No incluyo los 25 GB gratuitos (el enunciado no usa capa gratuita). **No incluidos / PENDIENTES:** lecturas de Streams, Lambda, KMS, CloudWatch, y el cobro único del pre-calentamiento ("cargo único a la tarifa regional de una RCU/WCU, según el aumento" [R-36]; el monto exacto debe confirmarse en la calculadora).

### 7.3 Recomendación

1. **Opción A (on-demand) + C (híbrida de lectura).** Es ≈ 10 veces más barata que el provisionado programado y ≈ 760 veces más barata que el provisionado fijo al pico, no exige adivinar capacidad y resuelve el salto súbito **con pre-calentamiento**, no con fe en el auto scaling.
2. **Pre-calentar** (una sola vez; los valores de `warm throughput` no pueden bajar [R-18]; **en una tabla global se aplican automáticamente a todas las réplicas** [R-18], lo que cubre el hallazgo de David sobre la réplica de us-east-2) `bya_seats`, `bya_orders` y sus GSI a ≥ el pico de **estrés ×5** (≈ 6.000 WRU/s; lecturas ≈ 3.000 RRU/s), `bya_counters` a ≈ 3.000 WRU/s y `bya_tickets` a ≈ 1.500, antes de la primera preventa y antes de cualquier evento mayor al previsto.
3. **Máximo de throughput** por tabla (≈ 2× el pico esperado) como freno de costos frente a abusos [R-13].
4. **Plan B documentado:** si el servicio cambiara su política o el pre-calentamiento no bastara, pasar a **provisionado con acciones programadas** (T-60 min a T+120 min por preventa) sobre las dos tablas más calientes, con 25 % de margen y GSI iguales a la tabla base [R-03, R-21].
5. **No usar auto scaling reactivo como única defensa**: dispara tras 2 min de exceso y tarda varios minutos, durante los cuales se rechaza lo que exceda la capacidad previa [R-20]. Sirve para crecimiento gradual, no para un salto de 100×.

**Cosas que *no* afirmo.** (i) Que el auto scaling responda al instante. (ii) Que on-demand sea inmune al *throttling*: lo es mientras el tráfico no exceda 2× el pico previo en 30 min o el pre-calentamiento lo cubra. (iii) Tiempos de pre-calentamiento: la documentación dice que "depende de los valores y del tamaño de la tabla" [R-18] (**PENDIENTE**: lanzarlo con ≥ 24 h de antelación).

---

## 8. Datos de dimensionamiento para Juan Pablo

### 8.1 Cifras **calculadas** (reproducibles con el script)

| Dato | Año 1 | Año 5 |
|---|---:|---:|
| Preventas grandes al año | 25 | 25 |
| Boletas por preventa | 60.000 | 60.000 |
| Órdenes por preventa | 24.000 | 24.000 |
| Personas en la cola | 250.000 | 610.352 |
| WRU por orden (mín. / plan. / estrés) | 55,3 / 84,4 / 182,9 | = |
| WRU/s promedio de preventa (plan.) / ráfaga ×5 | 1.687 / 8.437 | = |
| RRU/s de preventa (plan. ×5) | ≈ 2.200 | ≈ 2.200 |
| WRU anuales (normal + preventas) | 72,8 M + 50,6 M | 208,1 M + 69,6 M |
| RRU anuales | 45,4 M | 73,0 M |
| Almacenamiento total en línea (tablas + GSI) | 48,0 GiB | 231,8 GiB |
| Archivado en S3 (acumulado) | 0 | 131,2 GiB |
| Solicitudes del mapa por preventa (moderada / alta / extrema) | 10 M / 30 M / 100 M | ×2,44 |
| Costo DynamoDB por preventa (on-demand) | USD 2,14 (sa) / 1,42 (us) | |
| **Capa de datos completa** (throughput + almacenamiento + PITR + exportaciones + S3), USD/año | **348 (us) – 523 (sa)** | **1.489 (us) – 2.242 (sa)** |

Desglose del año 1: sa-east-1 → throughput 124 + almacenamiento 216 + PITR 173 + exportaciones 9 + S3 0 = **523**; us-east-1 → 83 + 144 + 115 + 6 + 0 = **348**. Año 5: sa-east-1 → 274 + 1.043 + 834 + 27 + 64 = **2.242**; us-east-1 → 183 + 695 + 556 + 18 + 36 = **1.489**. (PITR se factura sobre la tabla y los LSI, **no sobre los GSI** [R-36]: incluir los GSI sobreestima ≈ 6 %.)

### 8.2 **Supuestos** que Juan Pablo debe heredar tal cual (o cambiarlos y recalcular el script)

A-01 eventos +30 % · A-02 auditoría +30 % · A-03 sobrecarga 100 B/ítem · A-04 retención en línea · A-05 usuarios acumulados · A-06 CloudFront zona "South America" · A-07 5 % de auditoría humana · A-09 máx. 10 sillas por orden · A-10 f = 2 y b = 30 % · A-11 payload del mapa 3 KB, TTL 2 s · pico instantáneo ×5 · margen 25 %.

### 8.3 **Pendientes** (no los inventé)

* Monto exacto del cobro del pre-calentamiento **y si se cobra por cada región de una tabla global** (Juan Pablo). · Facturación de la propagación a GSI en transacciones (¿×1 o ×2?). · Precio y volumen de lecturas de DynamoDB Streams y de Lambda. · KMS, CloudWatch, CloudTrail (Samuel). · Cola virtual (build vs. buy). · Tarifa de CloudFront para Colombia. · Direct Connect (puerto y datos) y VPN. · Captura/exportación de la **AWS Pricing Calculator** (las cifras aquí vienen de la **lista de precios oficial vía API**, guardada en `calculos/evidencia/`, no de la calculadora web).

### 8.4 Componentes auxiliares que deben costearse

CloudFront (solicitudes + salida) · S3 (instantáneas, exportaciones, histórico) · ElastiCache Valkey Multi-AZ · API Gateway / compute de aplicación · Lambda (Streams, publicador, reconciliación) · SQS + DLQ · Athena + Glue · PITR y AWS Backup (Miguel) · tabla global / réplica de otra región (Miguel y David) · Direct Connect/VPN · cola virtual · WAF/Shield · KMS/CloudTrail/CloudWatch.

---

## 9. Verificación de coherencia (hecha antes de entregar)

| Comprobación | Resultado |
|---|---|
| 1,6 M órdenes × 2,5 = 4,0 M boletas (tabla oficial) | ✔ coincide |
| 24.000 órdenes × 2,5 = 60.000 boletas; 60.000 / 1.200 s = 50/s; 24.000 / 1.200 = 20/s | ✔ |
| Total mínimo por orden = 11 + 2 + 3 + 1,8 + 22 + 6,5 + 2 + 5 + 2 = **55,3** = suma por tabla (10 + 18,2 + 2 + 2 + 5 + 5 + 2 + 4 + 4,6 + 2,5) | ✔ |
| Planificación = 10 + 18,2 + … con f = 2 y b = 30 % (a = 0,4286): sillas 10 + 10 + 2,14 = 22,14; órdenes 18,2 + 8 + 1,71 = 27,91; **84,37** | ✔ |
| Unidades de capacidad ≠ solicitudes: cada fila de §5.1 cuenta unidades (WRU), no llamadas; un `TransactWriteItems` cuenta **una vez** sus ítems ×2, no se suma a las escrituras sueltas | ✔ |
| Contadores: 100 órdenes/s × 2 WRU = 200 WRU/s ≪ 1.000 por ítem | ✔ (no afirmo saturación por rendimiento) |
| Tablas on-demand nuevas (4.000 W/s) vs. necesidades por tabla (§5.3) | ✔ Solo estrés excede en `bya_seats` y `bya_orders` |
| Mapa directo = 5,7×–139,9× la cuota por tabla | ✔ |
| Costos reproducibles con `python3 -I calculos/modelo_capacidad.py` | ✔ |

**Limitaciones que podrían invalidar cifras:** L-1 distribución temporal de la preventa no dada · L-2 frecuencia de conflictos de transacción no medida · L-3 sobrecarga por ítem de la tabla no publicada · L-4 propagación a GSI en transacciones no detallada · L-5 tiempos de pre-calentamiento no publicados. **No presento resultados de pruebas de rendimiento**: no se hicieron (el enunciado prohíbe crear infraestructura).
