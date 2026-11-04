# Sustentación — BoletaYa SAS con DynamoDB en AWS

**Formato:** 30 minutos de presentación (20 diapositivas, ≈ 1,5 min cada una) + 10 minutos de preguntas.
**Regla del grupo:** el jurado puede preguntarle **a cualquiera** por **cualquier** decisión. Cada uno debe poder defender las 25 fichas (`entrega/03_registro_de_decisiones.md`), no solo su parte.
**Cifras válidas:** las de este archivo, que coinciden con `entrega/01_propuesta_escrita.pdf` y `entrega/02_hoja_de_costos.xlsx`. Si algún borrador viejo dice 194,0 M, 291,1 M, 473,7 M o 699,8 M, **está desactualizado**: no usarlo.

---

## 1. Qué hay en la entrega (para señalarlo si lo piden)

| # | Entregable | Archivo |
|---|---|---|
| 1 | Propuesta escrita (≤ 25 págs.) | `entrega/01_propuesta_escrita.pdf` (13 págs.) |
| 2 | Hoja de costos | `entrega/02_hoja_de_costos.xlsx` + `entrega/02_hoja_de_costos_evidencias/` (26 capturas) |
| 3 | Registro de decisiones (≥ 8 fichas) | `entrega/03_registro_de_decisiones.md` (25 fichas, F-01 a F-25) |
| 4 | Análisis de concurrencia | `entrega/04_analisis_de_concurrencia.md` |
| 5 | Estudio de conmutación | `entrega/05_estudio_de_conmutacion.md` |
| 6 | Memorando de carta de evento | No aplica: no hubo carta de evento |
| 7 | Presentación (≤ 20 diapositivas) | `entrega/07_presentacion.pdf` |

Pruebas ejecutables: `david/pruebas/` (50 de 50 pasan contra el simulador moto; sandbox de Mercado Pago).

---

## 2. Quién presenta qué

| # | Diapositiva | Presenta | Frase que no puede faltar |
|---|---|---|---|
| 1 | BoletaYa con DynamoDB en AWS | Samuel | Pasamos de 100 a 3.000 ventas por minuto sin doble venta ni pagos perdidos |
| 2 | El problema en números | Jacobo | 24.000 órdenes en 20 minutos y 250.000 personas mirando el mapa |
| 3 | Dos escenarios | Miguel | DynamoDB no se instala en el data center; B es híbrido |
| 4 | Ocho tablas, no una | David | Cada tipo de dato tiene su retención, su carga y sus permisos |
| 5 | Sillas sin cuello de botella | Jacobo | Clave por fila: ≈ 900 claves, ≈ 2,5 WRU/s por clave, lejos de 1.000 |
| 6 | El contador exacto | Juan Pablo | Se vende y se cuenta en la misma transacción, en 8 fragmentos |
| 7 | Cero doble venta | David | Transacción todo o nada con condición sobre cada silla |
| 8 | Bloqueo de 8 minutos y pagos a medias | Samuel | El TTL solo limpia; el vencimiento se decide en la condición. Pago con llave de idempotencia |
| 9 | El mapa no toca la base | Miguel | Directo serían 17,2× la cuota; con CDN, ≈ 450 RRU/s |
| 10 | Capacidad sin pagar el pico todo el año | Juan Pablo | On-demand USD 83/año contra USD 63.176 del provisionado fijo |
| 11 | Región y latencia | Jacobo | us-east-1: ≈ 77 ms desde Bogotá contra ≈ 112 ms de São Paulo, y más barata |
| 12 | Si cae una región | Miguel | Una sola región escribe; RPO 0 de pagos por conciliación; RTO 4–11 min |
| 13 | Respaldos que no frenan la preventa | David | PITR + AWS Backup + copia inmutable en otra cuenta y región |
| 14 | El estadio sin internet | Juan Pablo | Un nodo por puerta es la autoridad: 4 horas aislado sin doble ingreso |
| 15 | Seguridad y cumplimiento | Jacobo | La tarjeta nunca toca BoletaYa (token); Ley 1581; retención por norma |
| 16 | Versiones y licencias | Samuel | DynamoDB no tiene versión ni licencia; lo que la rodea sí, y está costeado |
| 17 | Costos por escenario | Miguel | A 191,1 M año 1; B 289,6 M, solo cabe usando la reserva |
| 18 | Sensibilidad y TCO | David | Con doble preventa y doble cola, B no cabe en el año 5 |
| 19 | A contra B | Juan Pablo | B no compra nada a cambio de su costo |
| 20 | Recomendación | Todos | Escenario A; cada uno dice una razón |

**Tiempos de control:** diapositiva 7 al minuto 10, diapositiva 14 al minuto 21, diapositiva 20 al minuto 29. Si vamos tarde, se recortan las 13 y 16 (se dicen en una frase).

**Cierre (diapositiva 20):** Samuel: costo · Jacobo: latencia · Miguel: riesgo y RTO · Juan Pablo: crecimiento · David: "lo no medido (RTO real, latencia real, conflictos) se valida en el simulacro antes de la preventa más grande".

---

## 3. Hoja de cifras (memorizar)

### Carga y capacidad
| Dato | Valor |
|---|---|
| Pico de preventa | 60.000 boletas en 20 min = **24.000 órdenes** (≈ 20 órdenes/s) |
| Costo por orden | 55–85 WRU según conflictos |
| Escritura pico normal / ráfaga ×5 | ≈ 1.700 WRU/s / ≈ 8.400 WRU/s (planificación hasta **10.546 WRU/s**) |
| Límite por partición | 1.000 WCU/s y 3.000 RCU/s |
| Sillas en pico ×5 | ≈ 2.214 WRU/s repartidas en ≈ 900 claves (≈ 2,5 WRU/s por clave) |
| Mapa si fuera a la base | 25.000 consultas/s = **17,2× la cuota** de una tabla |
| Mapa con CDN | ≈ **450 RRU/s** contra la base |
| Throughput año 1 | On-demand **USD 83** · provisionado programado USD 880 · provisionado fijo **USD 63.176** |
| Punto de equilibrio del provisionado | usar más del 28,9 % de lo provisionado (aquí: 0,037 %) |

### Disponibilidad
| Dato | Valor |
|---|---|
| Regiones | us-east-1 escribe; us-east-2 alterna (tabla global MREC) |
| RPO | **0 para pagos** (conciliación con la pasarela + `bya_ledger` MRSC + congelar sillas en duda) |
| RTO | **4–11 min** desde que se declara el desastre, + 2–5 min de detección (estimado, no medido) |
| Latencia por compra | A ≈ **22 ms** · B ≈ **353 ms** |
| Estadio | 4 horas sin internet; 48 lectores QR Wiegand sobre los torniquetes del estadio; 12 portátiles |
| Bloqueo de silla | 8 minutos |
| Pruebas | **50 de 50** pasan (simulador moto); Mercado Pago sandbox: idempotencia y `metadata` confirmadas |

### Costos (COP, caja)
| | Año 1 | Año 2 | Año 3 | Año 4 | Año 5 | 5 años | TCO 5 años |
|---|---|---|---|---|---|---|---|
| Presupuesto | 280,0 M | 130,0 M | 130,0 M | 130,0 M | 130,0 M | 800,0 M | — |
| **A** | **191,1 M** | 58,4 M | 63,7 M | 70,7 M | 85,8 M | **469,7 M** | **615,9 M** |
| **B** | **289,6 M** | 89,4 M | 94,8 M | 101,7 M | 121,7 M | **697,1 M** | **872,1 M** |

- A sobra 88,9 M en el año 1 y 330,3 M en 5 años.
- B se pasa **9,6 M** en el año 1; con la reserva del 10 % (28 M) le quedan **18,4 M**.
- B cuesta **227,4 M** más que A en 5 años.
- Sensibilidad (doble preventa + doble cola): A queda con 80,5 M (año 1) y 24,8 M (año 5). B queda en −18,0 M en el año 1 (10,0 M con reserva) y en **−11,0 M en el año 5: no cabe**.
- Estadio ≈ 157,0 M en el año 1 en ambos escenarios + fondo de reposición de 15,6 M/año.
- B suma 2 servidores en Bogotá (65,9 M), energía con PUE 1,8 (9,9 M/año), dos enlaces dedicados (26,9 M/año) y VPN (4,2 M/año).
- Supuestos: TRM 4.000, IVA 19 %. Todo precio tiene fuente, fecha y captura. La única excepción es el servidor Dell (sin captura: la página no cargó; precio 32.968.000 tomado del texto, agotado).

---

## 4. Preguntas probables del jurado

Las de datos, capacidad y arquitectura (P1–P23) están respondidas a fondo en `jacobo/resumen_sustentacion.md`; **todos deben leerlo**. Aquí van las respuestas cortas de todas las áreas.

### Modelo y concurrencia
**¿Por qué 8 tablas y no tabla única?** La guía dice "pocas tablas" salvo patrones de acceso muy distintos. Aquí cambian la retención, el calor y los permisos; backup, cifrado y Streams son por tabla. Tabla única solo donde hay un agregado (orden + pagos + factura). *(F-03)*

**¿Por qué esa clave de partición?** Con `E<evento>#S<localidad>#R<fila>` hay ≈ 900 claves. Con la clave por evento se pasa de 1.000 WRU/s en una partición, y con la clave por localidad una localidad popular queda sin margen. *(F-04)*

**Dos personas, la misma silla, el mismo milisegundo.** Las dos transacciones tocan el mismo ítem con la condición "disponible o bloqueo vencido". DynamoDB las serializa: una gana; la otra recibe `ConditionalCheckFailed` o `TransactionConflict` y **toda** su transacción se cancela. Está probado en `david/pruebas/` (escenario 1). *(F-06; entregable 4)*

**¿El TTL libera la silla a los 8 minutos?** **No.** El TTL puede tardar días: solo limpia. El vencimiento se decide en la `ConditionExpression`, que compara `lx` con un valor que calcula la aplicación (`:vencido_antes_de`), porque DynamoDB no admite aritmética en la condición. Eso también está probado.

**¿Cómo no se cobra dos veces?** Mercado Pago recibe `X-Idempotency-Key` = id del intento y en `metadata` van solo identificadores. El reintento con la misma llave devuelve el mismo pago (confirmado en sandbox). Si se pierde la respuesta del bloqueo, el reintento se reconoce como "ya aplicado". *(F-11)*

**¿Contador exacto?** Se actualiza dentro de la misma `TransactWriteItems` que vende la silla, en 8 fragmentos (`hash(orden) mod 8`). El total es la suma de los fragmentos. *(F-05)*

### Capacidad y costo de la base
**¿On-demand o provisionado?** On-demand con *warm throughput* antes de cada preventa. El auto scaling tarda minutos y rechaza tráfico mientras sube; el provisionado fijo cuesta ≈ 760×. Plan B: provisionado programado. *(F-07)*

**¿250.000 personas golpean la base?** No. El mapa sale de instantáneas en CloudFront (3–6 s de atraso). La base solo atiende bloquear, confirmar y validar. La cola virtual regula la entrada. *(F-08, F-15)*

### Recuperación
**¿RPO 0 si cae la región?** La réplica MREC es asíncrona, así que puede perder segundos de sillas. Lo que no se pierde son los **pagos**: el libro `bya_ledger` (MRSC, escritura síncrona en varias regiones) registra cada intento **antes** de cobrar. Al conmutar se congelan solo las sillas en duda, se concilia con la pasarela y se reabre la venta. *(F-09, F-10; entregable 5)*

**¿Por qué no escriben las dos regiones?** Con MREC gana la última escritura, y eso podría vender la misma silla dos veces. MRSC no admite transacciones. *(F-09)*

**¿De dónde sale el RTO de 4–11 min?** De los pasos del runbook (declarar, promover us-east-2, congelar sillas en duda, verificar, reabrir), cada uno con su tiempo estimado. **No está medido**: se mide en el simulacro, con `david/pruebas/verificar_simulacro.py`.

**¿Y si borran una tabla o meten ransomware?** Hay tres capas: PITR (35 días), AWS Backup semanal y mensual, y una copia inmutable en otra cuenta y otra región. Una tabla restaurada con PITR **no** queda lista sola: hay que reconfigurar Streams, TTL, autoescalado, réplicas y alarmas. *(F-12, F-17)*

### Estadio
**¿Qué pasa si se cae internet en el estadio?** Cada puerta tiene un nodo que es la autoridad de sus boletas, con la lista precargada. Así no hay doble ingreso por la misma puerta y aguanta 4 horas aislado. Al volver la conexión, sincroniza. *(F-13)*

**¿Por qué no compraron torniquetes?** Se usan los del estadio, con 48 lectores QR Wiegand, y 12 terminales portátiles en vez de 24. Hay un fondo de reposición de 15,6 M/año. *(F-14, F-23, F-24)*

### Seguridad y cumplimiento
**¿Están en PCI DSS?** La tarjeta va del navegador a Mercado Pago, que devuelve un token. BoletaYa solo guarda `id` y token, sin cuerpos en los logs. Eso **reduce** el alcance, pero no decimos "fuera de PCI": el adquirente confirma el SAQ. *(F-20)*

**Datos personales fuera de Colombia.** El art. 26 de la Ley 1581 prohíbe transferir a países sin nivel adecuado de protección, pero la Circular Única de la SIC (Título V, Cap. 3) incluye a EE. UU. en la lista de países adecuados; detalle en `samuel/analisis_ley_1581.md`. En B la base **también** vive en AWS, así que ese punto no distingue A de B.

**¿Cuánto guardan los datos?** 2 años en línea. Después, S3 Object Lock hasta la firmeza tributaria para los soportes fiscales y hasta 10 años para los libros mercantiles (art. 632 E.T., Ley 962 de 2005 arts. 28 y 46). Las supresiones por la Ley 1581 se hacen por seudonimización. *(F-21)*

### Escenario B y recomendación
**¿Cómo instalan DynamoDB en el data center?** No se puede. B es híbrido: la aplicación en Bogotá y la base en AWS, conectadas por VPN sobre dos enlaces dedicados (1 Gbps + 512 Mbps). *(F-01, F-18)*

**¿Por qué VPN y no Direct Connect?** El puerto de Direct Connect (Equinix BG1), el *cross-connect* y el circuito no tienen precio publicado: no se podían costear con fuente. Dos enlaces de proveedores distintos con VPN dan redundancia real con precio de Colombia Compra Eficiente (26,9 M/año). Direct Connect queda como mejora si la latencia medida fuera inaceptable. *(F-18)*

**¿Cómo hicieron caber B?** Quitando la caché en espera de us-east-2 (F-25) y usando la reserva, que solo B necesita (F-16).

**¿Por qué A?** Cuesta 227,4 M menos en 5 años, la compra es ≈ 330 ms más rápida, no depende de un enlace ni de un data center sin planta, y sigue cabiendo con la sensibilidad. *(F-22)*

**¿En qué año conviene cambiar?** En ninguno. Solo se revisaría si una norma exigiera los datos en Colombia o si AWS abriera allí una región con DynamoDB; en ese caso, A se muda a esa región.

**¿La comisión de la pasarela entra en el presupuesto?** No. El enunciado (§4) no la incluye entre los costos; es costo de recaudo (3,29 % + COP 800 por cobro) que se descuenta del ingreso. *(F-19)*

### Honestidad (siempre suma)
**¿Qué no pudieron verificar?**
- El RTO real.
- La latencia real desde Bogotá: la cifra es una medición de un tercero.
- La tasa real de `TransactionConflict`, porque moto ejecuta una transacción a la vez.
- Los precios comerciales finales: usamos precios públicos con captura.
- La validación jurídica y la de PCI.

Todo eso se valida en el simulacro previo a la preventa más grande.

---

## 5. Errores que no podemos cometer

1. Decir que el TTL libera la silla.
2. Decir que DynamoDB "se instala" en el data center.
3. Decir que las dos regiones escriben o que MREC da RPO 0. El RPO 0 es de **pagos** y sale del libro y la conciliación.
4. Decir que el RTO está medido. Es **estimado**.
5. Decir "estamos fuera de PCI". Lo correcto es "alcance reducido por tokenización".
6. Dar cifras viejas: 194,0 / 291,1 / 473,7 / 699,8 / Direct Connect.
7. Decir que el escenario B cabe sin la reserva.
8. Confundir **exactitud** del contador (siempre) con **frescura** (la suma de 8 ítems).
9. Decir que el mapa en vivo sale de la base.
10. Contradecir a un compañero. Si alguien se equivoca, el siguiente dice "complemento:" y corrige con la ficha.

---

## 6. Si el jurado trae una "segunda carta" (cambio sorpresa)

Respuesta en 3 minutos, en este orden:

1. **Repetir el cambio** en una frase, para confirmar que lo entendimos.
2. **Qué ficha toca:** buscar la ficha en el registro (capacidad → F-07; regiones → F-02/F-09; estadio → F-13/F-14; costos → hoja Resumen).
3. **Impacto en números:** cuánto cambia el pico (WRU/s), el costo (año 1 y 5 años) y el RTO. Para costos, la hoja tiene las celdas de supuestos; se cambia el valor y se lee el total.
4. **Decisión:** ¿la recomendación sigue siendo A? Hoy A tiene 88,9 M de holgura en el año 1 y B tiene −9,6 M. Casi cualquier aumento de costo refuerza A.
5. **Qué sacrificamos** y **qué validaríamos**.

Quien conozca mejor el área responde (datos: Jacobo · concurrencia/estadio: David · recuperación: Miguel · costos: Juan Pablo · cumplimiento: Samuel). Los demás no interrumpen.

---

## 7. Lista del día

- [ ] Todos leyeron este archivo, `jacobo/resumen_sustentacion.md` y las 25 fichas.
- [ ] Ensayo cronometrado completo (≤ 29 min).
- [ ] Presentación exportada de nuevo si cambió algo: las diapositivas 17–20 deben decir 191,1 / 289,6 / 469,7 / 697,1.
- [ ] PDF, Excel y anexos abiertos en una pestaña para mostrarlos si los piden.
- [ ] `david/pruebas/resultado.txt` a mano para mostrar los 50/50.
