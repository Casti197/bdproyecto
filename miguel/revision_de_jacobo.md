# Revisión cruzada de Miguel al trabajo de Jacobo

**Autor:** Miguel · **Fecha:** 2026-10-30 · **Alcance:** `README.md`, `modelo_datos.md`, `capacidad_y_volumetria.md`, `arquitectura.md`, `entrega_para_el_equipo.md` y `calculos/`.
Criterio: lo que afecta recuperación, licenciamiento y coherencia entre documentos. No revisé a fondo precios ni la lógica de concurrencia (es de David).

---

## 1. Qué comprobé y está bien

| Comprobación | Resultado |
|---|---|
| Ejecuté `python3 -I calculos/modelo_capacidad.py` y comparé con `salida_modelo.md` | **Idéntica, 0 diferencias** |
| Las 8 tablas del modelo, sumadas por tabla (tabla + GSI), reproducen sus totales en línea de 48,0 · 104,0 · 135,8 · 177,4 · 231,8 GiB | Coincide |
| 8.000 × 365 + 25 × 60.000 = 4.420.000, +10,5 % sobre los 4.000.000 de la tabla oficial (C-2) | Correcto |
| MRSC no existe en `sa-east-1` ni `mx-central-1`; sí en `us-east-1` y `us-east-2`; exige tres regiones | Confirmado en la [documentación](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html) |
| PITR, protección contra borrado y etiquetas no se sincronizan entre réplicas | Confirmado en la misma página |
| TTL no es compatible con MRSC | Confirmado |
| Las exportaciones no consumen RCU y requieren PITR | Confirmado en la [guía de DR](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamodbDisasterRecoveryStrategy.html) |
| Declaras como pendiente lo que no pudiste verificar (L-1 a L-5, §8.3) | Bien hecho, y es lo que el jurado valora |

## 2. Hallazgos

### H-1 (alta): la conmutación de origen de CloudFront no funciona para la compra

**Dónde:** `arquitectura.md` §3.4 (riesgo 4), diagrama del Escenario B (flecha `CDN -.-> APPS`, "si cae el data center: conmutación de origen") y §8 (A-R5, "origen de CloudFront conmutable"). También `entrega_para_el_equipo.md` §3.4 punto 6.

**Problema:** CloudFront solo conmuta al origen secundario cuando la solicitud es `GET`, `HEAD` u `OPTIONS`. No conmuta con `POST` ni `PUT` ([documentación](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html)). La compra es de escritura.

**Corrección propuesta:** la conmutación de la venta se hace por DNS (Route 53) o cambiando el origen a mano. CloudFront puede seguir conmutando el mapa y la posición en la cola, que son `GET`. Ya está en el runbook 2c.

### H-2 (media): el RTO no incluye la detección

**Dónde:** `arquitectura.md` §4.1, punto 4 ("el RTO de 15 minutos debe sumar: detección + decisión + conmutación + conciliación").

**Problema:** el enunciado (§3) dice que el RTO "se mide desde que se declara la falla". Detección y decisión quedan fuera del cálculo.

**Corrección propuesta:** reportar el RTO desde la declaración y el tiempo de detección por separado. En mi documento: 4 a 8 minutos desde la declaración (4 a 11 en secuencia), después de las respuestas del profesor del 4 de noviembre.

### H-3 (media): dos huecos en D-2

**Dónde:** `entrega_para_el_equipo.md` D-2 y `arquitectura.md` §4.1.

**Problema:** (1) la lista de sillas de un pago aprobado vive en `ORDER`, y puede no haberse replicado; (2) la conciliación de desastre no puede partir de `gsi_pendientes`, porque en la réplica pueden faltar las entradas de los últimos segundos.

**Corrección propuesta:** metadato del cobro en la pasarela, o un libro de pagos pequeño en MRSC sin transacciones. Detalle en `respuesta_a_david.md`. Tu modelo (§7.4) descarta MRSC en general, y eso es correcto para la compra; para una tabla de libro de pagos sin transacciones se puede evaluar.

### H-4 (media): el estado de la cola virtual en el Escenario B

**Dónde:** diagrama del Escenario B (`COLAB` dentro de "Data center de Bogotá").

**Problema:** si la cola vive en Bogotá, al caer el data center 250.000 personas pierden su lugar. Es una falla de recuperación aunque la base esté intacta.

**Corrección propuesta:** guardar el estado de la cola en AWS (por ejemplo, ElastiCache o DynamoDB), o aceptar y documentar la pérdida.

### H-5 (baja): PITR no restaura "a cualquier segundo" hasta el presente

**Dónde:** `entrega_para_el_equipo.md` §3.2 ("restauración a cualquier segundo de los últimos 1–35 días").

**Problema:** AWS indica que se puede restaurar a cualquier punto desde cinco minutos antes de la hora actual hasta el periodo configurado ([Backup and restore](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Backup-and-Restore.html)). Es decir, el último punto restaurable está unos 5 minutos atrás.

**Corrección propuesta:** añadir "hasta unos 5 minutos antes de la hora actual".

### H-6 (baja): la restauración no devuelve todo

**Dónde:** `modelo_datos.md` (Streams, TTL, políticas) y `entrega_para_el_equipo.md` §3.4.

**Problema:** al restaurar una tabla, AWS no copia las políticas de escalado, las políticas IAM, las alarmas, las etiquetas, la configuración de Streams, el TTL, la protección contra borrado ni PITR ([documentación](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/pointintimerecovery_restores.html)). Tu modelo depende de Streams (mapa, historial) y de TTL en casi todas las tablas, así que una tabla restaurada queda funcionando a medias.

**Corrección propuesta:** añadir al modelo una lista de configuración que se reaplica tras restaurar. La tengo en el plan de pruebas de mi documento.

### H-7 (baja): una afirmación sin verificar

**Dónde:** `entrega_para_el_equipo.md` §3.2, "50 restauraciones concurrentes / 50 TB [R-14]".

**Problema:** no la pude confirmar en las páginas que abrí. No dudo de ella, pero cítala solo si la abres.

## 3. Lo que me pedías

| Tu pedido | Mi respuesta |
|---|---|
| Lista de lo que se respalda y con qué frecuencia | `recuperacion_licenciamiento_carta.md`, sección "5.5 Estrategia de respaldo" |
| Que concilie mi RPO 0 con D-2 | Aceptado con dos condiciones: `respuesta_a_david.md` |
| Clasificación de `bya_audit` (§3.1, "pendiente de acordar") | Propongo clasificarla como **Usuarios, catálogo y analítica** (RPO 15 min, RTO 4 h). PITR da RPO de segundos y la exportación diaria con Object Lock conserva la evidencia. Para los cambios administrativos que se escriben dentro de la transacción, el RPO ya es el de la tabla que cambia |
| Historial de sillas: 15 min / 4 h (propuesto) | De acuerdo |
| `bya_counters`: reconstruible contando sillas `S` | De acuerdo. Los límites `LIM#` se recalculan desde las órdenes |

## 4. Lo que no revisé

Precios de CloudFront, Direct Connect, ElastiCache y Athena; las condiciones de las transacciones (revisión de David); el diseño de la cola virtual; el detalle de las referencias `[R-xx]` que no aparecen en las páginas que abrí.
