# Resumen para la sustentación — parte de Jacobo (datos, capacidad y arquitectura)

**Para estudiar con:** [`modelo_datos.md`](modelo_datos.md) · [`capacidad_y_volumetria.md`](capacidad_y_volumetria.md) · [`arquitectura.md`](arquitectura.md). Cada respuesta indica **dónde está la demostración**. Las cifras son las del script `calculos/modelo_capacidad.py`.

---

## 1. Mi parte en lenguaje claro (2 minutos)

**El problema.** BoletaYa pasa de vender casi nada a vender 50 boletas por segundo cuando abre una preventa, sin vender dos veces la misma silla y sin perder un pago. Mi trabajo es que la base **aguante ese pico**, que **no se cuelgue por culpa de unas pocas sillas o contadores muy disputados**, y dibujar **dónde vive cada pieza**.

**La base.** DynamoDB es una base **administrada por AWS**: no tiene servidores que dimensionar; se mide en **unidades de lectura y escritura** (RCU/WCU). Eso cambia el enfoque: no se calcula CPU ni IOPS, se calcula cuántas unidades consume cada operación.

**Cómo está organizada.** Ocho tablas, cada una para un tipo de dato. La silla es **un ítem** que dice si está disponible, bloqueada o vendida y **cuándo vence el bloqueo**. Las sillas se agrupan por fila para que ninguna partición reciba todo el tráfico. Cuando alguien compra, **una sola transacción** cambia las sillas, la orden, el contador y las boletas: o ocurre todo o no ocurre nada.

**El pico.** 60.000 boletas en 20 minutos son 24.000 órdenes, 20 por segundo. Cada orden cuesta unas 55 a 85 unidades de escritura (según los conflictos que haya), así que el pico "normal" es ≈ 1.700 unidades/s y una ráfaga de cinco veces ≈ 8.400. Eso es manejable para DynamoDB. **Lo que no es manejable** es que 250.000 personas miren el mapa de sillas contra la base: serían 25.000 consultas por segundo, 17 veces la cuota de una tabla. Por eso el mapa se sirve desde una **copia aproximada en CDN**, y la **base solo se usa para comprar**.

**La región.** Elegí **us-east-1**: desde Bogotá está a ≈ 77 ms frente a ≈ 112 ms de São Paulo (medición de un tercero) y es 33 % más barata.

**El escenario B.** DynamoDB **no se puede instalar en el data center**. Propongo una variante híbrida y dejé la pregunta al profesor.

---

## 2. Decisiones técnicas y su justificación

| Decisión | Por qué | Qué se sacrifica | Dónde se demuestra |
|---|---|---|---|
| **8 tablas, no una** | Calor, retención, permisos y clase de tabla distintos; transacciones sí funcionan entre tablas | Más objetos que operar; sin `JOIN` | `modelo_datos` §2 |
| **PK de sillas = evento#localidad#fila** | ≈ 900 claves por estadio; con la clave por evento o por localidad se superan 1.000 escrituras/s por partición | Leer una localidad completa exige una consulta por fila (lo hace un solo constructor) | `modelo_datos` §4.1 |
| **Sillas sin GSI** | Un GSI por localidad sería otro punto caliente y frenaría la tabla base | La disponibilidad por localidad sale de instantáneas | `modelo_datos` §3.2, §4 |
| **Contador fragmentado (N = 8) dentro de la transacción** | Exacto y atómico con la venta; reparte el choque | Leer el total = leer N ítems | `modelo_datos` §5 |
| **Bloqueo en la silla (`lx`, `lo`); vencido = disponible en la condición** | El TTL borra días después; no sirve para lógica | Condición más larga | `modelo_datos` §7.1 |
| **Mapa por CDN, compra por base** | 5,7×–139,9× la cuota de la tabla si fuera directo | El mapa va 3–6 s atrasado (estimado) | `capacidad` §6 |
| **On-demand + pre-calentamiento** | ≈ 10× más barato que el provisionado programado y ≈ 760× que el fijo; sin adivinar capacidad | Si se excede 2× el pico previo en 30 min sin pre-calentar, puede haber *throttling* | `capacidad` §7 |
| **us-east-1 + us-east-2 (réplica MREC en espera)** | Menor latencia medida y menor precio; MRSC existe pero no sirve para transacciones | Datos fuera de Colombia (validar con Samuel) | `arquitectura` §1 |
| **Una sola región escribe** | "Última escritura gana" de MREC podría vender la misma silla dos veces | La conmutación entre regiones exige modo seguro | `arquitectura` §4.1 |
| **Historial por Streams** | Barato e idempotente por `(silla, versión)` | Puede atrasarse; el stream guarda solo 24 h | `modelo_datos` §3.6 |

---

## 3. Preguntas difíciles del jurado y respuestas con fundamento

**P1. ¿Por qué esa clave de partición y cómo evitas el cuello de botella en el pico?**
Cada partición entrega como máximo **1.000 escrituras/s y 3.000 lecturas/s** [R-12]. En el pico de planificación ×5 las sillas reciben **≈ 2.214 WRU/s**; con la clave por evento (una partición) se supera el límite, y con la clave por localidad una localidad popular recibe ≈ 885 WRU/s, sin margen. Con **evento#localidad#fila** hay ≈ 900 claves y la carga media por clave es ≈ 2,5 WRU/s. El caso peor es **una sola silla** (techo ≈ 500 transacciones/s): lo contengo con la cola virtual, una pista negativa en caché, límites por usuario, *backoff* con *jitter* y pre-calentamiento. *(modelo §4)*

**P2. ¿Cómo mantienes el contador exacto sin que miles de compras choquen?**
El contador se actualiza **dentro de la misma transacción** que marca la silla vendida: o se vende y se cuenta, o ninguna de las dos. Para repartir el choque lo **fragmento en N = 8** ítems; el fragmento de una venta es `hash(orden) mod N`, así un reintento cae en el mismo. El total exacto es la suma de los fragmentos (lectura fuerte). **Ojo:** con el límite del enunciado, un contador único **no excede el límite físico** (100 órdenes/s × 2 WRU = 200 WRU/s < 1.000); el riesgo real es la **cancelación por choque de transacciones**, que **no medí** (no se pueden hacer pruebas) y por eso fragmento de todos modos. Distingo **exactitud** (siempre) de **frescura** (la suma de N ítems no es un instante único salvo con `TransactGetItems`). *(modelo §5)*

**P3. ¿Por qué on-demand o provisionado, y cuánto cuesta cada opción al año?**
Año 1, solo throughput: **on-demand USD 83 (us-east-1) – 124 (sa-east-1)**; **provisionado con escalado programado USD 880 – 1.319**; **provisionado fijo al pico USD 63.176 – 94.764**. El provisionado solo gana si usas más del **28,9 %** de lo provisionado; aquí el uso medio de una capacidad fija al pico es **0,037 %**. Y el auto scaling **no es instantáneo**: dispara tras 2 minutos y tarda varios mientras rechaza lo que excede [R-20]. Recomiendo on-demand **con pre-calentamiento** [R-13, R-18]; el plan B es provisionado programado. *(capacidad §7)*

**P4. ¿Qué consultas van a la base principal y cuáles no?**
A la base: bloqueo, confirmación, estado definitivo de silla, boleta, escaneo válido, contador exacto. **No** a la base: el mapa de 250.000 personas (CDN + instantáneas), la posición en la cola (objeto cacheable), el catálogo (caché), el histórico (S3 + Athena). *(arquitectura §6)*

**P5. ¿Por qué no una tabla única?**
La guía oficial dice "tan pocas tablas como sea posible" **salvo** patrones de acceso muy distintos [R-05]; aquí hay retención, calor y permisos distintos (backup todo-o-nada, cifrado compartido, Streams mezclados [R-06]). Uso tabla única **solo donde hay un agregado** (orden + pagos + factura). *(modelo §2)*

**P6. ¿Qué pasa si dos clientes piden la misma silla en el mismo milisegundo?**
Las dos transacciones apuntan al **mismo ítem** con la condición `st='A' OR (st='L' AND lx < now-skew)`. DynamoDB las trata como serializables [R-04]: una gana; la otra recibe `ConditionalCheckFailed` o `TransactionConflict` y **toda su transacción se cancela** (ninguna otra silla queda bloqueada). *(modelo §7; el anexo es de David)*

**P7. ¿El 30 % con rechazo significa un solo intento extra?**
No necesariamente. Intentos = 1 + 0,30 × k. Con k = 1 da **1,3** (la cifra oficial), con k = 3 da 1,9. Impacto: **+4 %** en escrituras. Lo que sí pesa es el conflicto de sillas: de 2 a 8 bloqueos fallidos por exitoso el pico sube **78 %**. *(capacidad §5.4)*

**P8. ¿Por qué us-east-1 y no São Paulo?**
Datos: ping medido desde Bogotá a São Paulo **112,2 ms** vs. Washington **77,1 ms**; DynamoDB cuesta **50 % más** en São Paulo; y São Paulo **no tiene MRSC**. **Límites:** es un ping de un tercero, no contra AWS, y hay que validar Ley 1581 con Samuel; si exigieran Latinoamérica, `sa-east-1` es el plan B. *(arquitectura §1)*

**P9. ¿RPO 0? ¿Qué pasa si cae la región?**
Dentro de la región **sí hay RPO 0** (tres zonas) [R-01]. Entre regiones **no con transacciones**: MRSC (RPO 0) no admite transacciones ni TTL, y MREC es asíncrono (RPO = retraso, unos segundos) [R-17]. Por eso **una sola región escribe** y, tras un desastre, entramos en **modo seguro**: conciliar con la pasarela (que es la fuente de verdad del dinero) y marcar vendidas las sillas de pagos aprobados antes de reabrir. *(arquitectura §4.1; decisión D-2)*

**P10. ¿Cómo instalan DynamoDB en el data center (Escenario B)?**
**No se puede**: es un servicio administrado, DynamoDB local es solo para desarrollo y pruebas [R-33] y Outposts no lo ejecuta localmente (inferencia) [R-34]. Propongo la variante híbrida: aplicación, caché y estadio en Bogotá; base en AWS por Direct Connect. **Está pendiente de confirmación del profesor (P-1).** *(arquitectura §3)*

**P21. En el Escenario B, ¿CloudFront conmuta solo a AWS si cae el data center?**
No para la compra. CloudFront solo conmuta de origen cuando la solicitud es `GET`, `HEAD` u `OPTIONS`, **no** `POST` ni `PUT` [R-40], y bloquear, pagar y confirmar son escrituras. La venta se conmuta **por DNS o cambiando el origen a mano**; CloudFront sí conmuta solo las consultas `GET`. Además el **estado de la cola virtual está en AWS**, para que al caer el DC no se pierda el lugar de 250.000 personas. *(arquitectura §3.4)*

**P22. ¿Por qué `lx < :vencido_antes_de` y no `lx < now - skew`?**
Una `ConditionExpression` no admite aritmética (solo el `SET` de una `UpdateExpression` suma y resta); la aplicación calcula `now − skew` y lo pasa como valor. Lo detectó David al revisar el modelo. *(modelo §7.1; `respuesta_a_revisiones.md`)*

**P23. Si restauran una tabla con PITR, ¿queda lista?**
No. La restauración crea una tabla nueva **sin** Streams, TTL, IAM, alarmas, etiquetas, escalado, protección contra borrado ni PITR [R-41]; sin Streams no hay mapa ni historial. Hay una lista de reaplicación en el modelo §6.4. Y solo se puede restaurar hasta cinco minutos antes de la hora actual [R-42].

**P11. ¿250.000 personas golpean la base?**
No. Consultando cada 10 s serían 25.000 req/s = 687.500 RRU/s = **17,2×** la cuota por tabla. El mapa sale de **instantáneas** (≈ 3 KB, TTL 2 s) y la base solo ve ≈ **450 RRU/s** del constructor. *(capacidad §6)*

**P12. ¿El auto scaling responde al instante?**
No. Dispara tras **2 minutos consecutivos** de exceso y tarda **varios minutos** en aplicarse; mientras, lo que exceda se rechaza [R-20]. Sirve para crecimiento gradual. Un salto súbito se resuelve con **pre-calentamiento o capacidad programada**, no con auto scaling reactivo.

**P13. Si la caché dice "libre" y no lo está…**
La caché **nunca** confirma. Una silla que la caché marca "libre" igual se intenta con la transacción y falla si no lo está; si marca "vendida", se rechaza sin tocar la base (error a favor de no vender). El usuario se entera por el `409` con las sillas fallidas y por el siguiente sondeo.

**P14. ¿Por qué no decidir con un GSI?**
Los GSI son **eventualmente consistentes** y se actualizan después [R-03]; una decisión de venta con un GSI podría ver datos viejos. Se usan solo para encontrar candidatos y se **verifica con lectura fuerte** del ítem.

**P15. ¿El TTL libera la silla a los 8 minutos?**
No. El TTL borra "típicamente en pocos días" y los ítems vencidos siguen siendo legibles [R-08]. La liberación se evalúa **en la condición** (`lx < now`); el TTL solo limpia.

**P16. ¿Qué supuestos hiciste en la volumetría y cuánto pesan?**
Los eventos crecen 30 % (si fueran constantes la ocupación pasaría de 74 % a 212 % en el año 5), la auditoría crece 30 %, la sobrecarga por ítem es 100 B (sensibilidad ±10 %) y la retención en línea es de 2 años. **Los volúmenes iniciales son los oficiales.** Cada supuesto está numerado (A-01…A-12) y se puede cambiar en el script. *(capacidad §3.1)*

**P17. ¿Cuánto cuesta una preventa?**
**Base de datos:** ≈ **USD 2,14** (sa-east-1) o **1,42** (us-east-1) on-demand. **Mapa en CDN:** USD 25 / 76 / 253 (moderada / alta / extrema). El costo de DynamoDB es ínfimo; el costo relevante son los auxiliares. *(capacidad §7.2, §6.4)*

**P18. ¿Qué pasa con la latencia en el escenario B?**
Cada viaje a la base cruza el enlace: **≈ 77 ms** (us-east-1). Con ≈ 4,3 viajes por compra son **≈ 353 ms** frente a **≈ 22 ms** si la aplicación está junto a la base. Son décimas de segundo frente a 480 s de bloqueo, pero el costo real es **la dependencia del enlace**: si cae, no se vende. *(arquitectura §5)*

**P19. ¿Qué no pudieron verificar?**
Sobrecarga por ítem de tabla (la página de precios no da cifra), la facturación de GSI en transacciones, el cobro y duración del pre-calentamiento, la frecuencia de conflictos de transacción (no se hicieron pruebas) y la latencia a us-east-2/Direct Connect. Está todo en `referencias.md` §H.

**P20. ¿Qué garantiza DynamoDB y qué garantiza la aplicación?**
DynamoDB garantiza: atomicidad y serializabilidad de la transacción, durabilidad en tres zonas, una sola aparición de cada registro de Streams, idempotencia del token por 10 minutos. **La aplicación** garantiza: que las condiciones sean correctas (nunca vender una silla ya vendida), la idempotencia de los pagos, la conciliación con la pasarela, la derivación idempotente del historial y la reconstrucción del mapa. *(modelo §7)*

---

## 4. Errores de diseño que debo evitar (y decir en voz alta que evité)

1. **Decir que el auto scaling responde al instante** → No: 2 min + varios min.
2. **Decir "RPO 0 con tablas globales"** → Solo MRSC lo da y no admite transacciones.
3. **Afirmar que un contador único satura por rendimiento** → Con la carga del enunciado no; el riesgo es el choque de transacciones (no medido).
4. **Llamar "exacto" al contador derivado de Streams** → Es exacto al converger, no con cada venta.
5. **Usar la caché o un GSI para confirmar una silla** → Nunca: lectura fuerte / transacción.
6. **Confundir tamaño de ítem con unidades de capacidad** → Redondeo a 1 KB / 4 KB; transacciones ×2; fallar cuesta.
7. **Traducir a CPU o IOPS** → DynamoDB no los expone: RCU/WCU.
8. **Sumar escrituras "a ojo"** → Cada compra se desglosa por operación (55,3 WRU mínimo; 84,4 planificación).
9. **Presentar estimaciones de latencia como tiempo de transacción** → Son ping de un tercero; no son el tiempo total.
10. **Inventar benchmarks o precios** → Todo precio tiene fuente (lista oficial AWS, consulta 2026-10-29).
11. **Poner el TTL en la lógica de bloqueo** → Solo limpia.
12. **Dos regiones escribiendo** → "Última escritura gana" puede vender una silla dos veces.
13. **Dibujar DynamoDB on premise** → No existe; B es híbrido y la pregunta está abierta.
14. **Ocultar contradicciones del enunciado** → 60.000 vs 45.000 sillas; 4,42 M vs 4,0 M boletas; 100 vs 8,3 ventas/min.
15. **Guardar datos de tarjeta** → Solo token (`gtk`); −1,0.

---

## 5. Preguntas que **yo** haría a mis compañeros en el ensayo

* **David:** ¿qué condición exacta aplicas en la confirmación si el bloqueo venció y nadie tomó la silla? ¿Qué margen `:skew` usas? ¿Cómo evitas el doble ingreso entre puertas sin internet?
* **Juan Pablo:** ¿incluiste pre-calentamiento, Streams, KMS, Direct Connect y la cola virtual? ¿Qué pasa con tu conclusión si la cola se duplica (CloudFront año 5: USD 15.442/año)?
* **Miguel:** ¿cómo defiendes RPO 0 de pagos ante pérdida de región si MRSC no admite transacciones?
* **Samuel:** ¿qué plazo legal fijaste y qué dices de la transferencia internacional a EE. UU.?
