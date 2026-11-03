# BoletaYa — Parte de Miguel: Recuperación, licenciamiento y carta de evento

Oct 30, 2026 · @Miguel Medina

## Resumen

La recuperación de BoletaYa tiene tres capas: la replicación en 3 zonas que ya hace DynamoDB (fallo de zona), PITR y AWS Backup (errores humanos, corrupción, ransomware) y una región alterna con modo seguro (pérdida de región). Este documento cubre 5.5, 5.3, el sitio alterno del Escenario B y el plan de la carta de evento. Los datos de AWS se verificaron en la documentación oficial (fuentes al final). Los cálculos de capacidad son de Jacobo (se reprodujo su script y coincide con su salida) y las transacciones, de David. Los tiempos de los pasos de recuperación son estimaciones con supuestos marcados, porque AWS no los publica.

| Supuesto heredado | De quién | Efecto en mi parte |
| --- | --- | --- |
| 8 tablas; críticas: `bya_seats`, `bya_orders`, `bya_tickets`, `bya_counters` | Jacobo | Frecuencia y retención de respaldo por tabla |
| Región principal us-east-1, alterna us-east-2; una sola región escribe | Jacobo, David (D-2, D-3) | Define el runbook de pérdida de región |
| Retención en línea de 2 años; el plazo legal posterior lo fija Samuel | Jacobo (A-04) | Ciclo de vida y bloqueo de objetos en S3 |
| Confirmación idempotente (token + condiciones) y reconciliador sobre `gsi_pendientes` | David | Runbook del pago sin registro |
| Escenario B híbrido: la base sigue en AWS | Jacobo (P-1) | Qué significa "falla el data center de Bogotá" |

Decisiones abiertas que afectan este documento:

- **D-2:** RPO 0 de pagos ante pérdida de región por conciliación con la pasarela, no por réplica. Tiene dos huecos que se tratan en la sección de RPO 0.
- **P-4:** qué significa "pérdida total del sitio" (zona, región o data center). Pregunta pendiente para el profesor.
- **P-1 y P-3:** cómo se interpreta el Escenario B con DynamoDB y dónde vive la aplicación en el Escenario A.

## 5.5 Estrategia de respaldo

Las cuatro tablas críticas llevan PITR de 35 días, una copia diaria de AWS Backup en otra región y otra cuenta, y una bóveda con Vault Lock. PITR cubre errores humanos y corrupción con granularidad de un segundo. La copia inmutable cubre el caso en que alguien con acceso borre las tablas y los respaldos de la cuenta principal.

| Tabla | PITR | AWS Backup (propuesta) | Copia fuera de la región | Exportación a S3 |
| --- | --- | --- | --- | --- |
| `bya_seats`, `bya_orders`, `bya_tickets` | 35 días | Diaria, retención 35 días; mensual, 13 meses | us-east-2, cuenta de respaldo, bóveda con Vault Lock | Incremental diaria (plan de Jacobo) |
| `bya_counters` | 35 días | Diaria, 35 días | us-east-2, bóveda con Vault Lock | No: se reconstruye contando sillas `S` |
| `bya_users`, `bya_catalog` | 35 días | Diaria, 35 días | us-east-2 | Solo `bya_catalog` |
| `bya_audit` | 35 días | Diaria, 35 días | us-east-2, bóveda con Vault Lock | Incremental diaria a S3 con Object Lock |
| `bya_seat_history` | 35 días (requisito de la exportación) | No: se reconstruye desde exportaciones | No | Incremental diaria |

Lo que dice la documentación y sostiene el diseño:

- **PITR** conserva hasta 35 días de puntos de recuperación con granularidad de un segundo, configurable entre 1 y 35 días [\[AWS, PITR\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Point-in-time-recovery.html). Se puede restaurar a cualquier punto desde cinco minutos antes de la hora actual [\[AWS, Backup and restore\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Backup-and-Restore.html). Por eso PITR no da RPO 0: el RPO es de segundos a minutos.
- **AWS Backup** programa, copia y gestiona el ciclo de vida de los respaldos de DynamoDB, y copia a otra región o cuenta [\[AWS, DynamoDB con AWS Backup\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/backuprestore_HowItWorksAWS.html). Los respaldos programados admiten frecuencia horaria, diaria, semanal o mensual [\[AWS, estrategia de DR\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamodbDisasterRecoveryStrategy.html).
- **Vault Lock en modo cumplimiento** no puede ser alterado ni borrado por ningún usuario ni por AWS cuando termina el periodo de gracia, que dura 3 días como mínimo [\[AWS, Vault Lock\]](https://docs.aws.amazon.com/aws-backup/latest/devguide/vault-lock.html). Es irreversible: se prueba antes en modo gobernanza, no se usan puntos con retención "siempre" y el costo de lo guardado queda comprometido hasta que venza la retención.
- **PITR y la protección contra borrado no se sincronizan entre réplicas** de una tabla global [\[AWS, tablas globales\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html). Hay que activarlos a mano en us-east-2.

Para el archivo legal en S3: Object Lock exige versionado. En modo cumplimiento nadie puede borrar ni acortar la retención, ni siquiera la cuenta raíz, y la única forma de borrar antes del plazo es eliminar la cuenta de AWS [\[AWS, Object Lock\]](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html). El bucket se replica a us-east-2 con Replication Time Control, que replica el 99,9 % de los objetos en 15 minutos [\[AWS, RTC\]](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication-time-control.html).

Decisión pendiente de costo: la copia inmutable es diaria en esta propuesta. Una copia horaria baja el RPO ante una cuenta comprometida a 1 hora, y Juan Pablo debe costear la diferencia.

## 5.5 Cómo respaldar sin afectar la preventa

En DynamoDB no hace falta una ventana de respaldo ni un respaldo desde una réplica: AWS afirma que los respaldos no afectan el rendimiento. Aun así, la preventa tiene reglas propias, porque una frase de la documentación no es una prueba y aquí no se pueden hacer pruebas.

| Operación | Impacto según la documentación | Fuente |
| --- | --- | --- |
| Respaldo bajo demanda | Tablas de unos megabytes a cientos de terabytes, "sin impacto en el rendimiento y la disponibilidad" | [Backup and restore](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Backup-and-Restore.html) |
| PITR | "No afecta el rendimiento ni las latencias de la API" | [Backup and restore](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Backup-and-Restore.html) |
| Exportación a S3 | No consume RCU y no afecta el rendimiento ni la disponibilidad | [Estrategia de DR](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamodbDisasterRecoveryStrategy.html) |
| Restauración | No consume capacidad aprovisionada de la tabla; siempre crea una tabla nueva | [Restaurar una tabla](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/pointintimerecovery_restores.html) |

Lo que la documentación consultada **no** dice: si los trabajos de AWS Backup consumen RCU o WCU de la tabla. Por eso:

1. **Congelamiento de cambios** desde 24 horas antes hasta 3 horas después de cada preventa: sin cambios en planes de respaldo, sin simulacros y sin restauraciones de prueba en la cuenta de producción.
2. **Los trabajos de respaldo corren de madrugada** (1:00 a. m. a 5:00 a. m., hora de Bogotá), fuera del horario de venta de 7:00 a. m. a 11:00 p. m. del enunciado. No es un requisito del servicio, es un margen.
3. **Nunca se respalda con `Scan`.** Todo respaldo usa PITR, AWS Backup o exportación.
4. **Alarma de capacidad** sobre las tablas calientes que se revisa en el simulacro previo a la preventa más grande: si un trabajo de respaldo coincidiera con aumento de *throttling*, se pausa.

La restauración tampoco es un mecanismo para recuperar la venta en 15 minutos: AWS dice que su duración "varía según múltiples factores y no siempre está correlacionada con el tamaño de la tabla", y no publica tiempos ni SLA [\[AWS, restaurar\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/pointintimerecovery_restores.html). Para el RTO de la venta se usa la réplica de otra región; la restauración se reserva para errores lógicos.

## 5.5 RPO 0 para pagos

El RPO 0 es real solo dentro de la región. Si se pierde la región, la base tiene un RPO de unos segundos, y el RPO 0 de los pagos se sostiene por proceso, con la pasarela como fuente de verdad del dinero. Esa decisión (D-2) es defendible, pero tiene dos huecos que hay que cerrar antes de presentarla.

| Falla | RPO de la base | RPO de pagos | Mecanismo |
| --- | --- | --- | --- |
| Servidor de aplicación | 0 | 0 | El estado vive en la base; la confirmación es idempotente (David) |
| Zona de disponibilidad | 0 | 0 | DynamoDB replica en 3 zonas por defecto, con SLA de 99,99 % [\[AWS, introducción\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html) |
| Región completa | Igual al retraso de replicación, "normalmente unos segundos" [\[AWS, tablas globales\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html) | 0 solo si se cierran los huecos de abajo | Réplica MREC en us-east-2 + conciliación contra la pasarela antes de reabrir |

**Por qué no se usa MRSC (RPO 0 entre regiones) para la compra.** MRSC no admite transacciones ni TTL, y exige exactamente tres regiones (tres réplicas, o dos réplicas y un testigo) [\[AWS, tablas globales\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html). La compra depende de `TransactWriteItems`, así que MREC es lo que queda para sillas, órdenes y boletas.

**Hueco 1: las sillas de un pago aprobado.** La lista de sillas vive en el ítem `ORDER`. Si ese ítem no alcanzó a replicarse, la pasarela solo conoce la llave `<oid>#<nn>` y el monto, y no se puede saber qué sillas marcar como vendidas. Dos opciones:

1. **Metadato en el cobro:** enviar a la pasarela el evento y las sillas como dato de referencia del cobro. Cuesta casi nada, pero depende de que la pasarela elegida lo permita.
2. **Libro de pagos en MRSC:** una tabla pequeña (orden, sillas, monto, estado) escrita con `PutItem` condicional, sin transacción, antes de cobrar. Da RPO 0 entre regiones para esa tabla. Cuesta una escritura sincrónica entre regiones en el camino del pago (latencia sin medir), un tercer sitio como testigo y su precio, que debe calcular Juan Pablo.

**Hueco 2: la conciliación de desastre no puede partir de `gsi_pendientes`.** Ese índice en la réplica puede no tener las entradas de los últimos segundos. La conciliación debe partir de la lista de transacciones de la pasarela por ventana de tiempo, desde unos minutos antes de la falla.

**Riesgo adicional: la región caída que vuelve.** AWS indica que, cuando una región se recupera, las replicaciones pendientes se reintentan y no hace falta ninguna acción para sincronizar [\[AWS, diseño de tablas globales\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-global-table-design.html). Los conflictos se resuelven por "última escritura gana" y no quedan registrados en CloudWatch ni CloudTrail. Mi lectura, que debe confirmar David: si la región original vuelve, no puede recibir tráfico ni escrituras, y sus ítems pendientes se comparan contra la pasarela antes de dejarlos converger.

**Qué debe confirmarse con la pasarela elegida** (el grupo no ha fijado cuál es):

- Si acepta llave de idempotencia por cobro.
- Si permite listar transacciones por rango de fechas.
- Si permite adjuntar metadatos al cobro.

**Nota sobre el SLA.** El SLA de 99,999 % de las tablas globales exige que todas las tablas de la región sean globales y que se intente la conmutación [\[AWS, SLA\]](https://aws.amazon.com/dynamodb/sla/). Con solo algunas tablas replicadas aplica el SLA estándar de 99,99 %, que coincide con el mínimo del enunciado para la preventa.

## 5.5 RPO y RTO alcanzados por componente

La venta en preventa cumple RPO y RTO ante fallo de zona sin hacer nada. Ante pérdida de región el RTO estimado queda entre 7 y 13 minutos si la aplicación en espera se levanta mientras cambia el DNS, y entre 7 y 16 si todo va en secuencia, frente a un límite de 15; esa cifra sale de supuestos que solo un simulacro puede confirmar. AWS no publica tiempos para la mayoría de estos pasos.

| Componente (enunciado) | Meta RPO / RTO | Alcanzado | Sustento |
| --- | --- | --- | --- |
| Venta en preventa, fallo de zona | 0 / 15 min | 0 / sin conmutación | Replicación en 3 zonas, SLA 99,99 % [\[AWS\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html) |
| Venta en preventa, pérdida de región | 0 / 15 min | Base: segundos. Pagos: 0 si se cierran los huecos de D-2. RTO: 7 a 13 min (7 a 16 sin traslape) | Réplica MREC; tabla de pasos abajo |
| Venta en operación normal | 0 / 1 h | Igual que la preventa, con 46 minutos más de margen | Mismo mecanismo |
| Ingreso al evento | Nunca se detiene; 0 en escaneos hechos | **Pendiente de David** (`estadio.md`, semana 2) | El servidor local es de David |
| Usuarios y catálogo | 15 min / 4 h | RPO de segundos con PITR; RTO de minutos a horas | PITR: RPO segundos, RTO "minutos" en la tabla y "minutos a horas" en el texto [\[AWS, DR\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamodbDisasterRecoveryStrategy.html) |
| Analítica | 15 min / 4 h | Las tablas cumplen; la copia en S3 es diaria y se regenera de ellas | Exportación incremental diaria (Jacobo) |
| Histórico (más de 2 años) | 24 h / 48 h | RPO de hasta 24 h por la exportación diaria; RTO de horas, porque el bucket replicado ya existe y solo se recrea la tabla de Athena en us-east-2 | Replicación de S3 con Replication Time Control: 99,9 % de los objetos en 15 minutos (exige versionado) |

**RTO de la venta ante pérdida de región, por pasos.** El enunciado mide el RTO desde que se declara la falla, así que la detección y la decisión no cuentan. Casi todos los tiempos son supuestos de diseño a validar en el simulacro.

| Paso | Minutos | Origen |
| --- | --- | --- |
| 1. Congelar escrituras en la región original | 1 a 2 | Supuesto: interruptor ya preparado |
| 2. Cambiar el tráfico a us-east-2 | 1 a 3 | Route 53 revisa cada 10 o 30 s [\[AWS\]](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-determining-health-of-endpoints.html); TTL de 60 s es decisión nuestra |
| 3. Aplicación en us-east-2 con capacidad de pico | 0 a 3 | Supuesto: aplicación en espera encendida |
| 4. Conciliar contra la pasarela y marcar sillas vendidas | 3 a 5 | Cálculo: con 5 s de retraso, 100 órdenes al ritmo promedio (20 por segundo) o 500 en ráfaga ×5 |
| 5. Reconstruir contadores: contar sillas `S` por localidad y fijar los fragmentos | 1 a 2 | Supuesto. Va **después** del paso 4, porque David lo define como cierre de la conciliación (`david/alta_disponibilidad.md` §5.4) |
| 6. Reapertura gradual por la cola virtual | 1 | Supuesto |
| **Total, pasos en secuencia** | **7 a 16** | Suma de mínimos y de máximos |
| **Total, si la aplicación en espera (paso 3) se levanta mientras cambia el DNS (paso 2)** | **7 a 13** | Supuesto de traslape que solo el simulacro confirma |

Dos hallazgos para el resto del equipo:

- **CloudFront no conmuta `POST`.** Su conmutación de origen solo actúa con `GET`, `HEAD` u `OPTIONS` [\[AWS, CloudFront\]](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html). La compra es de escritura, así que la conmutación de la venta debe hacerse por DNS (Route 53) o cambiando el origen a mano. Esto corrige `arquitectura.md` de Jacobo (§3.4, riesgo 4 y diagrama del Escenario B).
- **El límite de 15 minutos tiene poco margen.** Sin traslape de pasos el extremo alto (16 min) lo supera. Con el traslape del paso 3 el extremo alto es 13 min y solo se cumple si los pasos 1, 2 y 5 están automatizados. Con cualquier paso manual o lento se pasa. Si el simulacro confirma 16, la alternativa es reabrir por localidades a medida que cada una queda conciliada y con contadores reconstruidos; hay que decidirlo con David.

## 5.5 Runbooks

Son tres, escritos para que los ejecute el DBA de guardia (el enunciado asigna 6 horas de DBA a cada preventa) con el coordinador del incidente. DynamoDB no tiene "servidor principal" que pueda caer, así que el primer runbook cubre sus equivalentes: la capa de aplicación, la caché y la degradación de la tabla.

### Runbook 1: caída del servidor principal en plena preventa

Disparador: alarma de errores 5xx de la API, de `ThrottledRequests` o de `SystemErrors` en las tablas calientes, o caída de la caché.

1. **Acotar la falla.** En el tablero, ver cuál de las tres ramas es: aplicación, caché (ElastiCache) o DynamoDB.
2. **Frenar la entrada.** Pausar la admisión de la cola virtual. Nadie pierde su turno y se reduce la carga mientras se arregla.
3. **Si cae la aplicación:** verificar que el escalado la reemplace y que la capacidad vuelva al nivel de pico. No reiniciar la cola virtual.
4. **Si cae la caché:** la venta sigue, porque la caché nunca decide una silla (David). Sube la carga de transacciones inútiles, así que se admite menos gente y el mapa se reconstruye desde `bya_seats` con `Query` por filas.
5. **Si hay *throttling* en DynamoDB:** revisar si el tráfico superó el doble del pico previo en 30 minutos [\[AWS, modo bajo demanda\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-capacity-mode.html) y mantener la admisión reducida hasta que baje.
6. **Pagos en vuelo.** Dejar que el webhook, SQS y la confirmación idempotente los procesen. Verificar que la cola de mensajes fallidos esté vacía.
7. **Reanudar** la admisión por tramos cuando los 5xx estén en su nivel normal durante 5 minutos, la cola de fallidos vacía y el reconciliador sin pagos pendientes de más de 5 minutos.

No hacer: editar sillas a mano en `bya_seats`, reintentar una confirmación sin su `ClientRequestToken` ni restaurar PITR (no es el caso).

### Runbook 2: pérdida total del sitio

P-4 está pendiente: el runbook distingue tres significados de "sitio".

**2a. Pierde una zona.** No hay pasos: DynamoDB replica en 3 zonas [\[AWS\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html). El DBA verifica que la aplicación y la caché sigan en las zonas sanas.

**2b. Pierde la región (modo seguro).** Los tiempos son los de la tabla de RTO. Pasos acordados con David (`david/respuesta_a_miguel.md` y `david/alta_disponibilidad.md` §3 a §6).

1. **Declarar.** El coordinador y el DBA declaran la falla con un criterio acordado antes de la preventa: alarma compuesta (`SystemErrors`, `ReplicationLatency` y 5xx de la API) más confirmación humana. Se anota la hora **T** de la última escritura visible y la última `ReplicationLatency`.
2. **Cerrar la admisión y congelar escrituras** en us-east-1. Con la región caída puede no ser posible escribir la política que niega escritura al rol de la aplicación; en ese caso el congelamiento real es cerrar la admisión y no enrutar tráfico a us-east-1.
3. **Cambiar el tráfico a us-east-2 con la admisión cerrada.** La gente ve la sala de espera desde la región sana. Es el paso más optimista de la tabla: AWS dice "varios minutos" con solo DNS y "segundos a pocos minutos" con Application Recovery Controller, y vale solo si el cambio está preparado y el TTL es de 60 s.
4. **Levantar la aplicación en us-east-2** apuntando a la réplica local, sin abrir ventas y con la réplica pre-calentada.
5. **Conciliar con `confirmarDesastre`.** Listar las transacciones aprobadas de la pasarela desde `T − 5 min`, en orden de `aprobado_en`. Para **cada** una, incluso si su orden aparece `PAID`, ejecutar `confirmarDesastre` (`david/alta_disponibilidad.md` §5.2): lee con lectura fuerte, decide y escribe solo lo que falta, y no hace nada si la compra está completa. La confirmación normal **no sirve** aquí, porque la orden o la silla pueden faltar y una réplica puede mostrar una compra a medias. Si dos cobros reclaman la misma silla, gana el primero y el otro se reembolsa. Si el cobro no trae sus sillas (la pasarela no guardó metadatos), se reembolsa.
6. **Reconstruir contadores:** al terminar la conciliación, contar las sillas `S` por localidad y fijar los fragmentos (`SH#00` con el total, el resto en 0). El límite por usuario `LIM#` se recalcula desde las órdenes.
7. **Abrir la admisión por tramos** por la cola virtual.
8. **Pagos tardíos.** Los cobros aprobados después de reabrir cuya orden se creó antes de la declaración también usan `confirmarDesastre`; el resto, la confirmación normal.
9. **Cuando vuelva la región original:** no recibe tráfico ni escrituras. Sus escrituras pendientes se replican solas y los conflictos no quedan registrados [\[AWS\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-global-table-design.html), así que tras la convergencia se concilia otra vez contra la pasarela. El regreso a us-east-1 se hace fuera de una preventa.
10. **Cerrar el incidente** midiendo el RTO real y actualizando este runbook.

**2c. Pierde el data center de Bogotá (Escenario B).** La base no está allí, solo la aplicación, la caché y la cola virtual.

1. Declarar y activar la aplicación en espera en AWS.
2. Cambiar el origen por DNS. La conmutación de CloudFront no sirve para `POST` [\[AWS\]](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html).
3. **Reconstruir la cola virtual.** Si su estado vive en Bogotá, los compradores pierden su lugar. Conviene guardar ese estado en AWS (pendiente con Jacobo).
4. El servidor del estadio sigue operando solo y sincroniza contra la API en AWS.

### Runbook 3: pago confirmado por la pasarela que no quedó registrado

Disparador: la cola de mensajes fallidos, el reconciliador (revisa cada minuto los pagos con más de 5 minutos, según David) o un reclamo del cliente. El caso se resuelve solo en unos 6 minutos si el reconciliador está sano.

1. Buscar el pago por `<oid>#<nn>` y preguntarle a la pasarela su estado con esa llave.
2. **Aprobado, orden `PENDING`, pago `INITIATED` o `UNKNOWN`:** ejecutar la confirmación idempotente. Si las sillas ya no son de la orden, la orden pasa a `FULFILL_FAIL` y se encola el reembolso.
3. **Aprobado y la orden no existe** (pérdida de región): aplicar el paso 5 del runbook 2b (`confirmarDesastre`).
4. **Aprobado, orden `PAID`:** no hacer nada.
5. **Rechazado o sin cobro:** marcar `DECLINED`; la silla se libera sola al vencer el bloqueo.
6. **Verificar** que quede la orden `PAID`, las boletas `VALID`, la referencia de factura creada y el contador actualizado.
7. **Reembolsos** con llave idempotente `refund#<oid>` y aviso al cliente por soporte.
8. Una orden `PAID` sin cobro en la pasarela no puede existir: si aparece, alerta crítica.

## 5.5 Plan de pruebas de recuperación

Se planean cuatro tipos de prueba, y ninguna se ejecuta durante el curso. La que mide el RTO real de la venta es el simulacro de conmutación regional antes de la preventa más grande, porque el RTO estimado de 7 a 13 minutos (7 a 16 sin traslape) no puede afirmarse sin él.

| Prueba | Cuándo | Qué se verifica | Criterio de éxito | Horas de DBA (estimación) |
| --- | --- | --- | --- | --- |
| Simulacro de conmutación regional (runbook 2b) | 30 días antes de la preventa más grande, y una vez más en el año | Tiempo de cada paso, conciliación con la pasarela, réplica con capacidad de pico | RTO medido de 15 min o menos; 0 sillas con dos dueños; 0 pagos aprobados sin orden ni reembolso | 12 (2 personas, 6 h) |
| Restauración completa anual | Una vez al año, fuera de temporada de preventas | Restaurar las 4 tablas críticas desde la copia inmutable en us-east-2 a tablas nuevas | Conteo de ítems igual al esperado; contador reconstruido con diferencia 0; tiempo real anotado | 8 |
| Restauración PITR a un punto | Trimestral | Restaurar `bya_orders` a un punto de las últimas 24 h a una tabla nueva | Se restaura y se reaplican los ajustes que no se restauran | 3 |
| Runbook 3 (pago sin registro) en preproducción | Mensual | Reconciliador, cola de fallidos y reembolso idempotente con pagos de prueba | Todo pago de prueba termina `PAID` o reembolsado en 6 min o menos | 2 |

Al restaurar una tabla, AWS no copia las políticas de escalado, las políticas IAM, las alarmas, las etiquetas, la configuración de Streams, el TTL, la protección contra borrado ni la configuración de PITR [\[AWS, restaurar\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/pointintimerecovery_restores.html). Cada prueba de restauración incluye una lista de verificación para volver a aplicarlos. Sin Streams, por ejemplo, el mapa de sillas y el historial no se actualizan.

Costo para Juan Pablo: las horas de la tabla, a COP 120.000 por hora, suman 68 horas al año (COP 8.160.000, cálculo debajo), que entran al TCO a 5 años y no al presupuesto del año 1. Más el cobro de AWS por restaurar a una tabla nueva y por la transferencia saliente si se restaura entre regiones [\[AWS, PITR\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Point-in-time-recovery.html).

```latex
2 \times 12 + 8 + 4 \times 3 + 12 \times 2 = 68 \text{ horas} \;\Rightarrow\; 68 \times 120.000 = \text{COP } 8.160.000 \text{ al año}
```

## 5.3 Versiones y licenciamiento

DynamoDB no tiene versión del motor, edición ni licencia por núcleo que elegir: es un servicio administrado que se cobra por unidades de lectura y escritura y por GB almacenados (precios en el trabajo de Jacobo). Esa ausencia no se cita con una frase de AWS: se deduce de que ni la documentación ni la lista de precios ofrecen ese parámetro. Lo que sí tiene versión y fecha de fin de soporte es lo que lo rodea, y ahí está el riesgo de la penalización de −0,5.

| Elemento | Política o fecha de fin de soporte | Fuente | Plan |
| --- | --- | --- | --- |
| SDK de AWS en la aplicación | Versión mayor en soporte completo al menos 24 meses, luego 12 meses de mantenimiento (solo fallas críticas y seguridad), con aviso público al menos 6 meses antes | [Política de mantenimiento de SDK](https://docs.aws.amazon.com/sdkref/latest/guide/maint-policy.html) | Fijar la versión mayor vigente y revisar cada 6 meses; migrar en una ventana sin preventas |
| Runtime de la aplicación, si corre en Lambda: Node.js 24 | Obsolescencia el 30 de abril de 2028 | [Runtimes de Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) | Una migración de runtime en 2028 y otra antes de 2031 |
| Runtime alternativo: Python 3.14 | Obsolescencia el 30 de junio de 2029 | [Runtimes de Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) | Igual, con una migración en 2029 |
| ElastiCache para Valkey | Soporte estándar por versión mayor; el soporte extendido, de pago, dura hasta 3 años después [\[AWS\]](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/extended-support.html) | ElastiCache, soporte extendido | Desplegar la 9.1 (la más reciente que lista la guía) y revisar el calendario de fin de vida cada 6 meses |
| Servicios administrados (SQS, S3, CloudFront, API Gateway, Streams) | Sin versión ni licencia | Precios de Jacobo | Ninguno |

Lo que la tabla deja abierto:

- **El lenguaje de la aplicación no está decidido.** Por eso van dos runtimes. Ningún runtime de la tabla dura los 5 años: cualquiera exige al menos una migración. Asumo que el año 1 es 2027; si no, las fechas se desplazan.
- **Las fechas de fin de vida de las versiones de Valkey** no están publicadas. La guía de ElastiCache solo da fechas para Redis OSS (versiones 4 y 5: soporte estándar hasta el 31 de enero de 2026 y extendido hasta el 31 de enero de 2029; versión 6: 31 de enero de 2027 y 31 de enero de 2030) y lista la 9.1 como la versión más reciente de Valkey. Sin fecha, la revisión semestral es el control y el soporte extendido queda como costo posible no presupuestado.
- **Licencia de Valkey:** es código abierto y ElastiCache lo cobra por hora de nodo (precio en el trabajo de Jacobo). El tipo de licencia es un dato de memoria sin verificar.

**Qué pasa con la licencia al escalar y con las réplicas.** Nada: no hay licencia por núcleo, así que escalar en la preventa o tener una réplica en us-east-2 no agrega licencias. El costo está en las escrituras facturadas, incluida la escritura replicada de la tabla global, que calcula Juan Pablo.

**Plan de actualización costeado** (horas de mi estimación, a COP 120.000 por hora; entran al TCO a 5 años, no al presupuesto del año 1):

| Actualización | Veces en 5 años | Horas cada una | COP |
| --- | --- | --- | --- |
| Migración de runtime | 2 | 40 | 9.600.000 |
| Migración de versión mayor del SDK | 1 | 24 | 2.880.000 |
| **Total** |  |  | **12.480.000** |

**Escenario B y estadio.** Los servidores de Bogotá y el servidor del estadio sí tienen sistema operativo y fecha de fin de soporte. La regla es elegir uno con soporte de al menos 5 años desde la compra o costear su actualización. David propuso las versiones en `david/estadio.md` §9.1 y revisé las fechas el 3 de noviembre de 2026:

| Elemento | Fin del soporte estándar | ¿Cubre 5 años desde una compra a inicios de 2027? | Fuente |
| --- | --- | --- | --- |
| Ubuntu 26.04 LTS (servidor central y nodos de puerta) | Mayo de 2031; seguridad ampliada (Ubuntu Pro) hasta mayo de 2036 | No del todo (≈ 4,4 años) | [Canonical, fin de soporte](https://ubuntu.com/releaseendoflife) |
| Ubuntu 24.04 LTS (alternativa) | Mayo de 2029; ampliada hasta mayo de 2034 | No (≈ 2,4 años); no se recomienda para equipo nuevo | Canonical, misma página |
| PostgreSQL 18 (base local del estadio) | 14 de noviembre de 2030 | No (≈ 3,9 años) | [Política de versiones de PostgreSQL](https://www.postgresql.org/support/versioning/); la fecha la confirmé en una página secundaria ([endoflife.ai](https://endoflife.ai/postgresql/18)) porque no pude abrir la oficial |

Consecuencias para el costo a 5 años:

- **Ubuntu Pro** para 14 equipos (12 nodos de puerta y 2 servidores centrales, con el supuesto de 12 puertas de David), o un cambio de versión del sistema operativo hacia 2031. **No verifiqué el precio de Ubuntu Pro**: Juan Pablo lo consulta en la página oficial de Canonical antes de cifrarlo.
- **Una migración a una versión mayor de PostgreSQL hacia 2030**, que no estaba en mi plan. Estimo 24 horas de DBA (ensayo previo en un evento sin público incluido), a COP 120.000 por hora: **COP 2.880.000**. Es una estimación mía, sin fuente.
- **Lectores y torniquetes:** su firmware y soporte dependen del fabricante, que no está elegido. Queda como requisito de compra: soporte y repuestos del fabricante por 5 años como mínimo, por escrito.

El plan de actualización queda entonces en COP 12.480.000 (software de la aplicación) más COP 2.880.000 (PostgreSQL del estadio) = **COP 15.360.000 en 5 años**, más Ubuntu Pro por cifrar.

## Escenario B: sitio alterno y falla del data center de Bogotá

En el Escenario B híbrido de Jacobo la base sigue en AWS, así que perder el data center de Bogotá no pierde datos: pierde la aplicación, la caché local y la cola virtual. El sitio alterno de la aplicación es una aplicación en espera en AWS, y el sitio alterno de los datos es us-east-2. No hace falta un segundo data center físico.

| Falla | Qué se pierde | Qué sigue funcionando | Respuesta |
| --- | --- | --- | --- |
| Cae el enlace Bogotá–AWS | Toda lectura y escritura a la base: no se puede vender | Cola y mapa por CloudFront; el estadio | Segundo camino por VPN en otro proveedor y, si falla también, runbook 2c |
| Cae el data center (energía, rack, aire) | Aplicación, caché, cola virtual | Datos en AWS; webhook de la pasarela hacia SQS; estadio | Runbook 2c |
| Cae internet en el estadio | Sincronización con AWS | Ingreso con el servidor local | Diseño de David |
| Cae la región de AWS | Base en us-east-1 | La aplicación de Bogotá queda sin base | Runbook 2b, con la aplicación de Bogotá apuntando a us-east-2 |

**RTO de la falla del data center: 3 a 11 minutos**, con supuestos del mismo tipo que los del runbook 2b (DNS de 1 a 3 minutos, aplicación en espera de 0 a 3, cola virtual de 2 a 5). No hay conciliación con la pasarela porque los datos no se perdieron. Los pagos en vuelo no se pierden: el webhook publica en SQS, que vive en AWS, y la aplicación en espera consume lo acumulado.

Tres puntos que la propuesta de Jacobo deja abiertos:

- **Conmutación de CloudFront.** No sirve para `POST` [\[AWS\]](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html). El origen de la venta se cambia por DNS o a mano.
- **Estado de la cola virtual.** Si vive en Bogotá, 250.000 personas pierden su lugar al caer el data center. Debe guardarse en AWS.
- **Energía.** El enunciado describe rack, UPS, aire acondicionado y conectividad, sin planta eléctrica. El UPS cubre minutos, así que un corte largo equivale a perder el data center.

Desde recuperación, el Escenario A es más simple: la venta no depende de Bogotá. B solo es aceptable con enlace redundante, cola virtual en AWS y aplicación en espera, y esos tres componentes los costea Juan Pablo.

## Carta de evento: plan de las 72 horas

El memorando de máximo 2 páginas se entrega a la hora 64 y no a la 72, para dejar 8 horas de colchón. El contenido del enunciado es fijo: impacto en cada escenario, qué cambia y cuánto cuesta, si el presupuesto alcanza y cómo cambia la recomendación.

| Horas | Qué pasa | Quién |
| --- | --- | --- |
| 0 a 2 | Lectura conjunta de la carta y clasificación: qué áreas toca (preguntas abajo) | Todos; Miguel modera |
| 2 a 24 | Análisis por área, máximo media página de borrador cada uno, con cifra y fuente | Cada responsable |
| 24 a 36 | Integración en un solo borrador de 2 páginas | Miguel |
| 30 a 40 | Cálculo del costo del cambio y verificación del tope del presupuesto | Juan Pablo |
| 36 a 48 | Revisión cruzada del borrador (cada quien revisa a su pareja) | Parejas A y B |
| 48 a 60 | Ajuste de la recomendación y del registro de decisiones | Samuel |
| 60 a 64 | Versión final en PDF, verificación de fuentes y entrega | Miguel y Samuel |
| 64 a 72 | Colchón | Todos |

**Reparto por área**

| Área que pide el enunciado | Responsable | Pregunta clave |
| --- | --- | --- |
| Consistencia y concurrencia | David | ¿Puede la carta producir doble venta o un pago perdido? |
| Capacidad y modelo de datos | Jacobo | ¿Cambian las unidades de lectura y escritura, las claves o el pico? |
| Costo y presupuesto | Juan Pablo | ¿Sigue cabiendo en COP 280 M el año 1 y COP 130 M los años 2 a 5? |
| Seguridad y cumplimiento | Samuel | ¿Qué dato o norma se afecta? |
| RPO, RTO y runbooks | Miguel | ¿Cambia algún RPO o RTO y qué paso del runbook se modifica? |

**Estructura del memorando (2 páginas)**

1. La carta en tres líneas.
2. Impacto por escenario, en una tabla con las filas costo, RPO y RTO, consistencia, seguridad y capacidad, y las columnas A y B.
3. Qué cambia en el diseño y cuánto cuesta, con fuente por cifra.
4. Si el presupuesto alcanza y, si no, qué se recorta.
5. Si cambia la recomendación y por qué.

**Respuesta oral de 3 minutos para una segunda carta**

- 20 segundos: qué dice la carta, con las palabras del grupo.
- 60 segundos: impacto en A y en B, con una cifra.
- 60 segundos: qué cambia y cuánto cuesta.
- 20 segundos: si cambia la recomendación.
- 20 segundos: colchón para una pregunta del jurado.

En el ensayo de la semana 5 cada integrante responde una carta inventada en 3 minutos, con cronómetro, y el resto actúa de jurado.

## Fichas de decisión (para el registro de Samuel)

**Ficha R-1: cómo lograr RPO 0 de pagos si se pierde la región**

| Campo | Contenido |
| --- | --- |
| Contexto | El enunciado exige RPO 0 para pagos. La compra usa transacciones, y las tablas globales con consistencia fuerte entre regiones (MRSC) no las admiten |
| Alternativas | (a) MREC con conciliación contra la pasarela. (b) MRSC para toda la compra: imposible por las transacciones. (c) MREC más un libro de pagos en MRSC. (d) Aceptar un RPO mayor que 0 |
| Criterio | RPO 0 del dinero, sin romper la atomicidad de la compra, a costo razonable |
| Elección | (a), con las sillas enviadas como metadato del cobro; (c) como plan B si la pasarela no permite metadatos ni listar transacciones por fechas |
| Sacrificio | La base queda con RPO de segundos; el RTO incluye de 3 a 5 minutos de conciliación; la recuperación depende de capacidades de la pasarela que aún no se han confirmado |

**Ficha R-2: respaldo inmutable**

| Campo | Contenido |
| --- | --- |
| Contexto | PITR protege de errores, pero no de quien tenga acceso a la cuenta y borre tablas y respaldos. El enunciado pide una copia inmutable o desconectada |
| Alternativas | (a) Solo PITR. (b) PITR más AWS Backup en la misma cuenta y región. (c) PITR más AWS Backup con copia a otra región y cuenta, en una bóveda con Vault Lock |
| Criterio | Sobrevivir al borrado malicioso o por error de la cuenta principal, con un costo que quepa en el tope del año 1 |
| Elección | (c), con Vault Lock probado antes en modo gobernanza |
| Sacrificio | Costo de almacenamiento comprometido hasta que venza la retención; el modo cumplimiento es irreversible; la copia diaria deja hasta 24 h de datos en riesgo ante una cuenta comprometida; hay que operar dos cuentas y dos regiones |

## Pendientes y qué necesito de los demás

| Persona | Qué falta |
| --- | --- |
| David | D-2 ya aceptado por él con mis dos condiciones (`david/respuesta_a_miguel.md`). Falta: que corrija su total de RTO en `alta_disponibilidad.md` (mi tabla ahora da 7 a 13, o 7 a 16 sin traslape, porque reconstruir contadores va después de conciliar), y que declare el RPO/RTO del ingreso al estadio, que su `estadio.md` no cifra |
| Jacobo | Corregir en `arquitectura.md` la conmutación de CloudFront (no sirve para `POST`). Guardar el estado de la cola virtual en AWS. Decidir si se agrega el libro de pagos en MRSC. Fijar el pre-calentamiento una sola vez: se aplica solo a todas las réplicas, no se puede reducir después y se cobra al subirlo |
| Juan Pablo | Costear AWS Backup (diario u horario), copias a us-east-2 y a la cuenta de respaldo, almacenamiento bajo Vault Lock, restauraciones de prueba, el testigo de MRSC si se usa, la aplicación en espera y el enlace redundante del Escenario B. Incluir en el TCO 68 horas de DBA al año (COP 8.160.000) y 15.360.000 en actualizaciones a 5 años (12.480.000 de la aplicación y 2.880.000 de PostgreSQL del estadio), más Ubuntu Pro de 14 equipos, que no tiene precio verificado |
| Samuel | Plazo legal de retención y regla de Object Lock en S3. Los respaldos y la réplica de us-east-2 son otra transferencia de datos personales. Verificar que ningún respaldo contenga números de tarjeta (−1,0). AWS permite cifrar los respaldos con una llave KMS distinta a la de la tabla [\[AWS\]](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/backuprestore_HowItWorksAWS.html) |
| Profesor | P-4 (qué es "pérdida total del sitio") y P-1 (Escenario B con DynamoDB) |
| Yo | Elegir la pasarela con David y Jacobo. AWS no publica tiempos de restauración ni fechas de fin de vida de Valkey, así que esos dos datos se miden en los simulacros o se vigilan, no se citan |

## Fuentes

Páginas abiertas y leídas el 2026-10-30:

- [Point-in-time backups for DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Point-in-time-recovery.html)
- [Restore a table in DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/pointintimerecovery_restores.html)
- [Backup and restore for DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Backup-and-Restore.html)
- [Using AWS Backup with DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/backuprestore_HowItWorksAWS.html)
- [AWS Backup Vault Lock](https://docs.aws.amazon.com/aws-backup/latest/devguide/vault-lock.html)
- [How DynamoDB global tables work](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html)
- [Using DynamoDB global tables](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-global-table-design.html)
- [Choosing your disaster recovery strategy for DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamodbDisasterRecoveryStrategy.html)
- [What is Amazon DynamoDB?](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
- [DynamoDB on-demand capacity mode](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-capacity-mode.html)
- [Amazon DynamoDB SLA](https://aws.amazon.com/dynamodb/sla/)
- [Route 53: cómo se determina la salud de un endpoint](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-determining-health-of-endpoints.html)
- [CloudFront origin failover](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html)
- [Política de mantenimiento de los SDK de AWS](https://docs.aws.amazon.com/sdkref/latest/guide/maint-policy.html)
- [Runtimes de Lambda](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)
- [ElastiCache Extended Support](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/extended-support.html)

* [Understanding DynamoDB warm throughput](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/warm-throughput.html)
* [Locking objects with Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)
* [S3 Replication Time Control](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication-time-control.html)
* [Engine versions and upgrading in ElastiCache](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/engine-versions.html)

Del resto del grupo, sin abrir por mi cuenta: el modelo, las cifras y las referencias `[R-xx]` de Jacobo, y las referencias `[D-xx]` de David. Las citas de AWS que traduje al español son traducciones mías del texto en inglés.
