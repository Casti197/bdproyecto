# Referencias y control de fuentes — parte de Jacobo

**Fecha de consulta: 2026-10-29 (R-01 a R-39) y 2026-11-03 (R-40 a R-42, añadidas tras la revisión de Miguel)** (fecha del sistema de la sesión). Las páginas de documentación de AWS se leyeron con la herramienta de navegación web y se extrajeron los datos que se citan; **no se cita nada que no se haya leído**, salvo donde se indica "solo resultados de búsqueda". Los precios vienen de la **API de lista de precios oficial de AWS** (archivos guardados en [`calculos/evidencia/`](calculos/evidencia/)). No se creó cuenta ni recurso en la nube.

**Clave de confianza:** 🟢 abierta y leída · 🟡 solo resultados de búsqueda (no abierta) · 🔴 no verificado (declarado como pendiente).

## A. Documentación oficial de AWS — DynamoDB

| ID | Título | URL | Tema | Datos concretos que respalda |
|---|---|---|---|---|
| R-01 🟢 | What is Amazon DynamoDB? | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html | Descripción, resiliencia, seguridad | Sin servidor y totalmente administrado; "no tiene versiones (mayor, menor o parche) ni ventanas de mantenimiento"; **sin `JOIN`**; replica los datos **en tres zonas de disponibilidad por defecto**, SLA 99,99 %; PITR de **1 a 35 días** sin usar capacidad ni afectar rendimiento; respaldos bajo demanda y AWS Backup (copia entre cuentas y regiones); cifrado en reposo por defecto (clave propiedad de AWS o KMS); control de acceso a nivel de atributo; cumple PCI DSS entre otros; AWS Database Encryption SDK para cifrado del lado del cliente; capa gratuita de 25 GB; "single-digit millisecond performance" |
| R-02 🟢 | DynamoDB read and write operations | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/read-write-operations.html | Consumo de unidades | Lectura fuerte 1 por 4 KB; eventual ½; transaccional 2; escritura 1 por 1 KB; transaccional 2 (una para preparar, otra para confirmar, **también si se cancela**); redondeo a 4 KB / 1 KB; `Query` suma y redondea una vez; `Batch*` redondea por ítem; `UpdateItem` cobra el mayor de antes/después; escritura condicional fallida consume capacidad |
| R-03 🟢 | Using Global Secondary Indexes in DynamoDB | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html | GSI | Solo lecturas eventuales; `GetItem`/`BatchGetItem` no aplican; actualización asíncrona "en una fracción de segundo… en algunos fallos, más"; un GSI sin capacidad suficiente **frena las escrituras de la tabla**; costo de escritura (alta 1, cambio de clave 2, proyectados 1, sin cambio 0); tamaño del ítem de índice = claves + proyectados + **100 B**; índices dispersos |
| R-04 🟢 | DynamoDB Transactions: how it works | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html | Transacciones | Hasta **100 acciones/ítems y 4 MB**, misma cuenta y región, varias tablas; idempotencia con token válido **10 min**; **serializable** entre transacciones y operaciones individuales; `BatchWriteItem`/`Query`/`Scan` no serializables como unidad; conflictos → `TransactionCanceledException` (**los SDK no reintentan**) con `CancellationReasons`; capacidad **×2** incluso al cancelar; no operan sobre índices; propagación a GSI/Streams gradual y sin orden entre ítems; atómicas solo en la región de escritura |
| R-05 🟢 | NoSQL design for DynamoDB | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html | Número de tablas | "Mantener tan pocas tablas como sea posible"; excepciones: series de tiempo de alto volumen o conjuntos de datos con patrones de acceso muy distintos; diseñar a partir de los patrones de acceso |
| R-06 🟢 | Data modeling foundations in DynamoDB | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/data-modeling-foundations.html | Tabla única vs. varias | Ventajas y desventajas de ambos diseños (respaldos todo-o-nada, cifrado compartido, Streams mezclados, Standard-IA, etc.) |
| R-07 🟢 | Constraints in Amazon DynamoDB | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html | Límites | 1 KB = 1.024 B; ítem máx. **400 KB** y el nombre del atributo cuenta; PK ≤ 2.048 B, SK ≤ 1.024 B; transacción ≤ 100 ítems y 4 MB; `Query`/`Scan` 1 MB por página; `BatchGetItem` 100 ítems/16 MB; `BatchWriteItem` 25 ítems/16 MB; `UpdateTimeToLive` 1 cambio/hora |
| R-08 🟢 | Using time to live (TTL) in DynamoDB | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html | TTL | Número en segundos de época; borrado "típicamente en pocos días" sin consumir WCU; los ítems vencidos siguen siendo legibles hasta su borrado (usar filtro); borrados llegan a Streams como borrados del servicio; en tablas globales el borrado se replica y consume escritura replicada |
| R-09 🟢 | DynamoDB data export to Amazon S3: how it works | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/S3DataExport.HowItWorks.html | Exportación | Requiere PITR; exportación completa e incremental; **no consume RCU ni afecta rendimiento**; formatos DynamoDB JSON e Ion; sin SLA de duración; cobro por tamaño |
| R-10 🟢 | Using write sharding to distribute workloads evenly | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-sharding.html | Sharding | Sufijos aleatorios vs. **calculados**; leer todo exige consultar todos los sufijos y unir |
| R-11 🟢 | Change data capture for DynamoDB Streams | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html | Streams | Retención **24 h**; cada registro aparece **exactamente una vez**; orden por ítem; ≤ 2 lectores por *shard*; sin impacto de rendimiento; Lambda procesa por *shard* |
| R-12 🟢 | Best practices for designing and using partition keys | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html | Particiones | Cada partición: **3.000 lecturas/s y 1.000 escrituras/s** |
| R-13 🟢 | DynamoDB on-demand capacity mode | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-capacity-mode.html | On-demand | Tabla nueva: **4.000 escrituras/s y 12.000 lecturas/s**; acepta de inmediato hasta **2× el pico previo**; superar 2× en 30 min puede dar *throttling*; recomienda pre-calentar o espaciar el crecimiento 30 min; cuota por tabla 40.000; máximo de throughput configurable; provisionado→on-demand 4 veces/24 h |
| R-14 🟢 | Quotas in Amazon DynamoDB | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html | Cuotas | 40.000 RCU/WCU por tabla y 80.000 por cuenta (provisionado); no se puede subir capacidad "muy rápidamente"; bajadas: 4 + 1 por hora (27/día); 20 GSI por tabla; exportación incremental 15 min–24 h; 50 restauraciones/50 TB; MRSC 400 tablas; Streams |
| R-15 🟢 | DynamoDB table export output format | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/S3DataExport.Output.html | Formato de exportación | Incremental: `Metadata.WriteTimestampMicros`, `Keys`, `NewImage`, `OldImage`; manifiestos con `itemCount`; archivos `.json.gz` |
| R-17 🟢 | How DynamoDB global tables work | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html | Tablas globales | **MREC**: asíncrona, "típicamente un segundo o menos", RPO = retraso de replicación, "última escritura gana", transacciones solo atómicas en la región de origen. **MRSC**: RPO 0, exactamente 3 regiones, **sin transacciones ni TTL**, lista de regiones (**sin sa-east-1 ni mx-central-1**); PITR, protección contra borrado y etiquetas **no se sincronizan** entre réplicas; SLA 99,999 % |
| R-18 🟢 | Understanding DynamoDB warm throughput | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/warm-throughput.html | Pre-calentamiento | Valores por defecto gratis; se pueden **subir** (no bajar) para tablas, tablas globales y GSI; "tiempo depende de los valores y del tamaño"; se cobra por el aumento |
| R-19 🟢 | DynamoDB burst and adaptive capacity | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/burst-adaptive-capacity.html | Ráfaga y capacidad adaptativa | Hasta 300 s de capacidad sin usar; capacidad adaptativa aísla ítems calientes sin superar 3.000/1.000 por partición |
| R-20 🟢 | Managing throughput capacity with DynamoDB auto scaling | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/AutoScaling.html | Auto scaling | Dispara tras **2 minutos consecutivos** sobre el objetivo; tarda **varios minutos**; mientras tanto se rechaza lo que excede la capacidad previa; objetivo 20–90 % |
| R-21 🟢 | Scheduled scaling for Application Auto Scaling | https://docs.aws.amazon.com/autoscaling/application/userguide/application-auto-scaling-scheduled-scaling.html | Escalado programado | Acciones programadas que suben el mínimo / bajan el máximo; conviven con las políticas reactivas |
| R-24 🟢 | DynamoDB table classes | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.TableClasses.html | Clases de tabla | Standard-IA para tablas donde el almacenamiento domina; los GSI usan la clase de la tabla; se puede cambiar |
| R-28 🟢 | Amazon DynamoDB endpoints and quotas (AWS General Reference) | https://docs.aws.amazon.com/general/latest/gr/ddb.html | Regiones y cuotas | DynamoDB disponible en `sa-east-1`, `us-east-1`, `us-east-2`, `mx-central-1` y las demás regiones listadas |
| R-40 🟢 | Optimize high availability with CloudFront origin failover | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html | Conmutación de origen | "CloudFront fails over to the secondary origin only when the HTTP method of the viewer request is `GET`, `HEAD`, or `OPTIONS`"; **no conmuta `POST` ni `PUT`**; criterios por código de estado (400, 403, 404, 416, 429, 500, 502, 503, 504); por defecto espera hasta 30 s (3 intentos de 10 s) antes de conmutar; remite a DNS failover de Route 53 |
| R-41 🟢 | Restore a table in DynamoDB | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/pointintimerecovery_restores.html | Restauración | Restaura a una **tabla nueva** sin consumir throughput; se puede excluir GSI; **hay que reaplicar a mano**: políticas de auto scaling, políticas IAM, alarmas y métricas, Contributor Insights, **etiquetas**, **Streams**, **TTL**, protección contra borrado y **PITR**; restauración entre regiones posible |
| R-42 🟢 | Backup and restore for DynamoDB · Point-in-time backups for DynamoDB | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Backup-and-Restore.html · https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Point-in-time-recovery.html | PITR | Puntos de recuperación por segundo hasta 35 días (configurable 1–35); se puede restaurar "desde **cinco minutos antes de la hora actual** hasta el período configurado"; PITR se factura por el tamaño de la tabla y los LSI; el respaldo de una réplica se restaura como tabla **independiente** (no como réplica) |
| R-33 🟢 | Setting up DynamoDB local | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html | DynamoDB local | Versión descargable "para desarrollar y probar" |

## B. SLA, precios y servicios auxiliares

| ID | Título | URL | Tema | Datos que respalda |
|---|---|---|---|---|
| R-22 🟢 | Amazon DynamoDB Service Level Agreement | https://aws.amazon.com/dynamodb/sla/ | SLA | 99,99 % (estándar) y 99,999 % (Global Tables); créditos 10/25/100 %; el SLA global aplica si todas las tablas de la región son globales y se intenta conmutar |
| R-23 🟢 | AWS Price List API — Amazon DynamoDB (versión 20260911124422) | https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonDynamoDB/20260911124422/sa-east-1/index.json (igual con `us-east-1`, `us-east-2`, `mx-central-1`; índice: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonDynamoDB/current/region_index.json) | Precios DynamoDB (USD) | WRU/RRU on-demand, WCU/RCU-hora, GB-mes, PITR, exportación, escritura replicada (ver valores en `capacidad_y_volumetria.md` §7.2 y `arquitectura.md` §1.1). Copia local en `calculos/evidencia/` (fecha de publicación 2026-09-11) |
| R-16 🟢 | AWS Price List API — Athena, S3, ElastiCache, API Gateway, CloudFront | https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonAthena/20260911124408/sa-east-1/index.json · …/AmazonS3/20261015173540/… · …/AmazonElastiCache/20261028192450/… · …/AmazonApiGateway/20261013003044/… · https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonCloudFront/current/index.json (publicada 2026-10-19) | Precios (USD) | Athena USD 9 / 5 por TB (sa/us); S3 Standard 0,0405 / 0,023 por GB-mes; ElastiCache Valkey `cache.m7g.large` 0,18 / 0,1264 por hora; HTTP API 1,59 / 1,00 por millón; CloudFront SA: 2,2 USD/millón de solicitudes HTTPS y 0,11 USD/GB (primeros 10 TB) |
| R-36 🟢 | Amazon DynamoDB on-demand pricing | https://aws.amazon.com/dynamodb/pricing/on-demand/ | Precios, facturación | Sobrecarga de almacenamiento "depende de las funciones habilitadas" (**sin cifra**); cobro **único** de pre-calentamiento; lecturas/escrituras transaccionales 2 unidades; PITR/respaldo sobre tabla y LSI |
| R-31 🟢 | Amazon API Gateway quotas | https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html | Cuotas API | 10.000 req/s por cuenta y región (ráfaga 5.000); **2.500** en México (Central) |
| R-32 🟢 | Use Amazon CloudFront Origin Shield | https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html | CDN | Capa extra de caché que consolida solicitudes al origen; con cargo; ofrecido en us-east-1, sa-east-1, etc. |

## C. Región, latencia y conectividad

| ID | Título | URL | Tema | Datos que respalda |
|---|---|---|---|---|
| R-25 🟢 | WonderNetwork — Pings desde Bogotá | https://wondernetwork.com/pings/Bogota | Latencia medida | São Paulo **112,24 ms**; Washington **77,13 ms**; Miami 57,99; Ciudad de México 111,54; Dallas 86,73; Santiago 67,42 (mediciones del 2026-10-29). **Medición de terceros por ICMP a servidores de ese proveedor; no es contra AWS** |
| R-26 🟢 | Amazon CloudFront features | https://aws.amazon.com/cloudfront/features/ | Puntos de presencia | "Colombia: Bogotá" figura entre los PoP |
| R-27 🟢 | AWS Direct Connect locations | https://aws.amazon.com/directconnect/locations/ | Conectividad | **Equinix BG1, Bogotá** (1G/10G/100G; sin SiteLink); acceso a todas las regiones públicas con Direct Connect Gateway o interfaz pública |
| R-39 🟡 | AWS Direct Connect announces 100G expansion in Bogota | https://aws.amazon.com/about-aws/whats-new/2025/09/aws-direct-connect-100g-expansion-bogota | Conectividad | Expansión a 100G en Bogotá (septiembre de 2025) — **solo resultado de búsqueda** |
| R-38 🟡 | AWS Local Zones en Latinoamérica | https://aws.amazon.com/blogs/publicsector/aws-announces-local-zones-latin-america | Local Zone de Bogotá | Anunciada; **no hallé confirmación de disponibilidad** — solo resultados de búsqueda; no se usa en el diseño |
| R-34 🟡 | AWS Outposts user guides | https://docs.aws.amazon.com/pdfs/outposts/latest/userguide/outposts-rack.pdf | Outposts | DynamoDB **no aparece** en las listas de servicios que corren localmente (**inferencia** de resultados de búsqueda; no abierta) |

## D. Cola virtual y patrones

| ID | Título | URL | Tema | Datos que respalda |
|---|---|---|---|---|
| R-29 🟢 | Virtual Waiting Room on AWS (página de la solución) | https://aws.amazon.com/solutions/implementations/virtual-waiting-room-on-aws/ | Cola virtual | "This AWS Solution is no longer available" (sin fecha de retiro en la página); alternativas: AWS Marketplace o construcción propia con CloudFront Functions. Sus páginas de documentación en `docs.aws.amazon.com/solutions/…` respondieron **404** al consultarlas |
| R-30 🟢 | Build a virtual waiting room with Amazon DynamoDB and AWS Lambda at SeatGeek | https://aws.amazon.com/blogs/architecture/build-a-virtual-waiting-room-with-amazon-dynamodb-and-aws-lambda-at-seatgeek/ | Patrón | Tokens de acceso, modos "sala de espera" y "cola", tablas de contadores/conexiones/cola, WAF/Shield; **sin cifras de escala** |

## E. Datos personales (insumo para Samuel; no es análisis legal)

| ID | Título | URL | Tema | Datos que respalda |
|---|---|---|---|---|
| R-35 🟡 | Colombia Designates U.S. as "Adequate" Data Transfer Nation (Hunton) · Circular Externa 005 de 2017 (BU) · Brasil y otros candidatos a la lista (Asuntos Legales, 2026) | https://www.huntonprivacyblog.com/2017/08/15/colombia-designates-u-s-adequate-data-transfer-nation/ · https://www.bu.com.co/es/insights/noticias/circular-externa-005-del-10082017 · https://www.asuntoslegales.com.co/analisis/sofia-navas-vera-4325984/brasil-ecuador-kenia-panama-y-sudafrica-los-nuevos-candidatos-a-la-lista-de-paises-con-proteccion-adecuada-de-datos-personales-4417427 | Transferencia internacional | EE. UU. incluido en la lista de la SIC en 2017; México figura entre los países listados; Brasil no figuraba y es **candidato** (2026). **Fuentes secundarias de resultados de búsqueda; no abiertas. Verificar el numeral vigente de la Circular Única de la SIC** |

## F. Exportación y Athena

| ID | Título | URL | Datos que respalda |
|---|---|---|---|
| R-37 🟡 | Export Amazon DynamoDB table data to your data lake in Amazon S3 · Analyze Amazon Ion datasets using Amazon Athena | https://aws.amazon.com/blogs/aws/new-export-amazon-dynamodb-table-data-to-data-lake-amazon-s3/ · https://aws.amazon.com/blogs/big-data/analyze-amazon-ion-datasets-using-amazon-athena/ | Las exportaciones en DynamoDB JSON o Ion se consultan con Athena (solo resultados de búsqueda; el DDL del modelo es **ilustrativo y no probado**) |

## G. Archivos de entrada del proyecto (no son fuentes técnicas)

`Proyecto Final Bases de Datos — BoletaYa SAS Grupos.docx` (enunciado oficial) · `Glosario — Proyecto Final Bases de Datos Grupos.docx` · `jacobo.md` · `david.md` · `juanpablo.md` · `miguel.md` · `samuel.md`. No se modificaron.

---

## H. Lo que **no** pude verificar (declarado, no inventado)

| # | Afirmación pendiente | Cómo se trató |
|---|---|---|
| U-1 | Sobrecarga de almacenamiento por ítem de **tabla** (la página de precios no da cifra) | A-03 = 100 B (valor documentado para GSI); sensibilidad ±10 % |
| U-2 | Facturación de la propagación a GSI de escrituras en transacción | S-1 = ×1; sensibilidad ×2 (+12 % WRU/orden) |
| U-3 | Tiempo de duración del pre-calentamiento y monto exacto de su cargo | Pendiente (Juan Pablo); se recomienda lanzarlo con ≥ 24 h |
| U-4 | Frecuencia real de `TransactionConflict` bajo contención y tiempo que una transacción retiene un ítem | Modelo ilustrativo (T10) con supuesto explícito; **no hay pruebas de rendimiento** |
| U-5 | Precio de las lecturas de Streams hechas por Lambda; costo de Lambda, KMS, CloudWatch | Pendiente; no incluido |
| U-6 | Latencia a us-east-2 y por Direct Connect; ping a un *endpoint* de AWS | Pendiente de medir desde Bogotá |
| U-7 | Disponibilidad actual de la Local Zone de Bogotá | No usada |
| U-8 | Compatibilidad exacta del DDL de Athena (SerDe) | Ilustrativo; validar en la consola |
| U-9 | Zona de facturación de CloudFront para Colombia | A-06 = "South America"; pendiente de calculadora |
| U-10 | Tablas de Direct Connect (precio por puerto/datos en Bogotá) | Pendiente (Juan Pablo) |
| U-11 | Que las páginas de documentación de **Virtual Waiting Room** (docs) estén retiradas | Solo se verificó el aviso de la página de la solución |
| U-12 | Estado legal de las listas de países de la SIC | Fuente secundaria; verificar |
| U-13 | Si el cargo único del pre-calentamiento se cobra por cada región de una tabla global; latencia de escritura del libro de pagos MRSC entre us-east-1 y us-east-2 | Pendiente (Juan Pablo; medir) |
| U-14 | Tiempo real de conmutación por DNS de la venta (el tiempo propagado depende del TTL y de los resolvedores; no lo verifiqué) | Pendiente (Miguel, `recuperacion_licenciamiento_carta.md`) |
