# Registro de decisiones (anexo A de la propuesta)

**Versión de entrega del 2026-11-04.** Las fichas F-01 a F-15 consolidan decisiones tomadas en las carpetas de cada integrante; F-16 a F-25 se cerraron al integrar la propuesta (`entrega/01_propuesta_escrita.pdf`) y la hoja de costos (`entrega/02_hoja_de_costos.xlsx`).
**Mínimo exigido:** 8 fichas con contexto, alternativas, criterio, elección y sacrificio. Aquí hay **25 fichas**; las decisiones están tomadas y las verificaciones de compra, costos o terceros que siguen pendientes se indican en cada ficha.
**Regla de esta carpeta:** no se copió ni se cambió nada de las carpetas de los demás. Cada ficha dice de dónde sale.

| # | Decisión | Dueño | Estado |
|---|---|---|---|
| F-01 | Escenario B híbrido (DynamoDB no va *on premise*) | Jacobo | Cerrada (profesor, resp. 1) |
| F-02 | Región principal us-east-1, alterna us-east-2 | Jacobo | Cerrada, sujeta a Ley 1581 (Samuel) |
| F-03 | Ocho tablas especializadas en vez de tabla única | Jacobo | Cerrada (D-1) |
| F-04 | Clave de sillas por evento, localidad y fila, sin GSI | Jacobo | Cerrada |
| F-05 | Contador exacto fragmentado dentro de la transacción | Jacobo, David | Cerrada (D-5) |
| F-06 | Control optimista: escritura condicional + transacción; el TTL no libera | David | Cerrada (D-9) |
| F-07 | Capacidad on-demand con pre-calentamiento | Jacobo, Juan Pablo | Cerrada (D-4) |
| F-08 | Mapa de sillas por CDN; la base solo para comprar | Jacobo | Cerrada |
| F-09 | Una sola región escribe; RPO 0 de pagos por conciliación | David, Miguel | Cerrada (D-2, R-1; profesor resp. 3) |
| F-10 | `bya_ledger` como fuente de las sillas en duda | David, Jacobo | Cerrada (D-2b) |
| F-11 | Pasarela de pagos: Mercado Pago | David, Miguel, Jacobo | Cerrada (D-11) |
| F-12 | Respaldo inmutable en otra región y otra cuenta | Miguel | Cerrada en diseño; costo abierto (R-2) |
| F-13 | Estadio: un nodo por puerta como autoridad | David | Cerrada |
| F-14 | Equipo de puerta: usar los torniquetes del estadio | David, Juan Pablo | Cerrada |
| F-15 | Cola virtual propia sobre AWS | Jacobo, Juan Pablo | Decidida; estimación y prueba de carga pendientes de validar |
| F-16 | Reserva del 10 %: solo B la usa | Juan Pablo | Cerrada |
| F-17 | AWS Backup semanal y mensual (PITR cubre los 35 días) | Miguel, Juan Pablo | Cerrada |
| F-18 | Escenario B: VPN sobre dos enlaces dedicados en vez de Direct Connect | Jacobo, Juan Pablo | Cerrada |
| F-19 | Comisión de la pasarela fuera del presupuesto de infraestructura | Juan Pablo | Cerrada |
| F-20 | PCI: tokenización reduce alcance; SAQ sujeto al adquirente | Samuel | Diseño definido; SAQ por confirmar |
| F-21 | Retención por clase: firmeza tributaria o 10 años mercantiles | Samuel, Miguel | Diseño definido; matriz por validar |
| F-22 | Recomendación final: Escenario A | Grupo | Cerrada |
| F-23 | 12 terminales portátiles en vez de 24 | David, Juan Pablo | Cerrada |
| F-24 | Fondo de reposición del hardware del estadio | Juan Pablo | Cerrada |
| F-25 | B sin caché en espera en us-east-2 | Jacobo, Miguel | Cerrada |

---

## F-01. Escenario B híbrido

| Campo | Contenido |
|---|---|
| Contexto | El enunciado pide un Escenario B con la base en el data center de Bogotá. DynamoDB es un servicio administrado de AWS: DynamoDB Local es solo para desarrollo y pruebas, y Outposts no lo ejecuta localmente |
| Alternativas | (a) DynamoDB Local en producción. (b) Un motor *on premise* compatible con la API de DynamoDB. (c) Híbrido: aplicación, caché y estadio en Bogotá; base en AWS por Direct Connect y VPN |
| Criterio | Usar el motor asignado sin inventar una configuración que no existe; que la verdad transaccional quede en el motor asignado |
| Elección | (c). El profesor la aceptó el 2026-11-04 y pidió una sección de máximo 2 páginas que explique por qué no se puede *on premise* y evalúe (b) sin diseñarla |
| Sacrificio | B depende del enlace Bogotá–AWS: si cae, no se vende. Añade Direct Connect, VPN redundante y una aplicación en espera en AWS. Cada compra suma unos 353 ms de ida y vuelta frente a unos 22 ms en A |
| Fuente | `jacobo/arquitectura.md` §3; `jacobo/resumen_sustentacion.md` P10 y P18; `david/respuestas_profesor.md` resp. 1 |
| Pendiente | Sección de 2 páginas (Jacobo) |

## F-02. Región us-east-1 con alterna us-east-2

| Campo | Contenido |
|---|---|
| Contexto | No se ha confirmado que AWS tenga una región con DynamoDB en Colombia (verificación pedida por el profesor). Hay que elegir dónde vive la base |
| Alternativas | (a) sa-east-1 (São Paulo). (b) us-east-1 (Virginia) con us-east-2 (Ohio) como alterna. (c) Otra región norteamericana |
| Criterio | Latencia desde Bogotá, precio, disponibilidad de funciones (MRSC) y viabilidad legal |
| Elección | (b). Ping medido por un tercero desde Bogotá: 77,1 ms a Washington frente a 112,2 ms a São Paulo. DynamoDB cuesta un 50 % más en São Paulo, que además no tiene MRSC |
| Sacrificio | Los datos personales quedan fuera de Colombia y exigen el análisis de transferencia internacional de la Ley 1581. La latencia es un ping de un tercero, no una medición contra AWS |
| Fuente | `jacobo/arquitectura.md` §1; `jacobo/calculos/evidencia/latencia_wondernetwork_bogota_2026-10-29.txt` |
| Pendiente | Ley 1581 (Samuel); infraestructura de AWS en Colombia y latencia (Jacobo); plan B sa-east-1 si se rechaza |

## F-03. Ocho tablas en vez de una

| Campo | Contenido |
|---|---|
| Contexto | La guía de DynamoDB recomienda "tan pocas tablas como sea posible", salvo cuando los patrones de acceso son muy distintos |
| Alternativas | (a) Tabla única. (b) Ocho tablas especializadas (`bya_seats`, `bya_orders`, `bya_counters`, `bya_tickets`, `bya_catalog`, `bya_users`, `bya_seat_history`, `bya_audit`) |
| Criterio | Retención, carga, permisos y respaldo distintos por tipo de dato; las transacciones sí funcionan entre tablas |
| Elección | (b), con tabla única solo donde hay un agregado (orden + pagos + factura en `bya_orders`) |
| Sacrificio | Más objetos que operar y configurar (PITR, Streams, alarmas por tabla); sin `JOIN` |
| Fuente | `jacobo/modelo_datos.md` §2; aprobada por David (D-1) |

## F-04. Clave de sillas por evento, localidad y fila

| Campo | Contenido |
|---|---|
| Contexto | En el pico casi toda la escritura cae en las sillas de un evento. Una partición acepta como máximo 1.000 escrituras por segundo |
| Alternativas | (a) Clave por evento. (b) Clave por localidad. (c) Clave por evento, localidad y fila. (d) Cualquiera de ellas más un GSI por localidad |
| Criterio | Que ninguna partición se acerque a 1.000 WRU/s en el pico de planificación ×5 (≈ 2.214 WRU/s sobre las sillas) |
| Elección | (c), sin GSI: unas 900 claves por estadio y unos 2,5 WRU/s por clave en promedio |
| Sacrificio | Leer una localidad completa exige una consulta por fila; la disponibilidad por localidad sale de instantáneas, no de un índice |
| Fuente | `jacobo/modelo_datos.md` §3.2 y §4.1; `jacobo/resumen_sustentacion.md` P1 |

## F-05. Contador exacto fragmentado dentro de la transacción

| Campo | Contenido |
|---|---|
| Contexto | Los organizadores exigen un contador exacto por localidad, actualizado con cada venta, y en preventa miles de compras tocan las mismas pocas localidades |
| Alternativas | (a) Un contador único dentro de la transacción. (b) Contador derivado con Streams. (c) Contador fragmentado (N = 8) dentro de la transacción |
| Criterio | Exacto con cada venta (no solo al converger) y con el menor riesgo de choque entre transacciones |
| Elección | (c): se vende y se cuenta en la misma transacción; el total es la suma de 8 fragmentos con lectura fuerte |
| Sacrificio | Leer el total cuesta 8 lecturas. La frescura no es un instante único salvo con `TransactGetItems`. La frecuencia real de conflictos no está medida |
| Fuente | `jacobo/modelo_datos.md` §5; `jacobo/resumen_sustentacion.md` P2 |

## F-06. Control optimista con escritura condicional y transacción

| Campo | Contenido |
|---|---|
| Contexto | Regla de oro: una silla nunca se vende dos veces. DynamoDB no tiene niveles de aislamiento SQL ni bloqueos que esperen |
| Alternativas | (a) Bloqueo pesimista en una tabla aparte. (b) Escritura condicional sobre el ítem de la silla dentro de `TransactWriteItems` (todo o nada), con el bloqueo de 8 minutos como atributo (`lx`, `lo`). (c) Liberar sillas vencidas con TTL |
| Criterio | Cero doble venta demostrable y sin depender de procesos que tardan |
| Elección | (b). La silla vencida se trata como disponible dentro de la condición; el TTL solo limpia. Parámetros: máximo 10 sillas por orden, `:skew` = 2 s, *backoff* con *jitter* y máximo 3 reintentos |
| Sacrificio | Las transacciones cuestan el doble de capacidad, también al cancelarse; un choque cancela la transacción completa y el cliente reintenta |
| Fuente | `david/concurrencia.md` §2–§5; `david/anexo_concurrencia.md`; prueba en simulador: 50 de 50 casos pasan (`david/pruebas/resultado.txt`) |

## F-07. Capacidad on-demand con pre-calentamiento

| Campo | Contenido |
|---|---|
| Contexto | El presupuesto no alcanza para pagar todo el año la capacidad de la preventa |
| Alternativas (throughput del año 1, USD) | (a) On-demand: 83 (us-east-1) a 124 (sa-east-1). (b) Provisionado con escalado programado: 880 a 1.319. (c) Provisionado fijo al pico: 63.176 a 94.764. (d) Auto scaling reactivo |
| Criterio | Costo anual y capacidad de absorber un salto súbito sin rechazar compras |
| Elección | (a) con pre-calentamiento (*warm throughput*) antes de cada preventa; (b) como plan B. (d) se descarta: dispara tras 2 minutos y tarda varios más |
| Sacrificio | Si el tráfico supera el doble del pico previo en 30 minutos sin pre-calentar, puede haber *throttling*. El monto exacto del pre-calentamiento no está verificado (Juan Pablo supone USD 13 como cargo único) |
| Fuente | `jacobo/capacidad_y_volumetria.md` §7; `jacobo/resumen_sustentacion.md` P3 y P12; `juanpablo/costos_y_dimensionamiento.md` §4.2 |

## F-08. Mapa de sillas por CDN

| Campo | Contenido |
|---|---|
| Contexto | 250.000 personas en la cola consultan el mapa. Sondeando cada 10 s serían 25.000 consultas por segundo, 17,2 veces la cuota de una tabla |
| Alternativas | (a) Leer el mapa de la base. (b) Caché con DAX o ElastiCache. (c) Instantáneas en CloudFront regeneradas cada 2 s desde la base |
| Criterio | Que la consulta masiva no toque la base principal y que ninguna venta dependa de la copia |
| Elección | (c). La base ve unos 450 RRU/s del constructor de instantáneas. La compra siempre se valida con la transacción |
| Sacrificio | El mapa puede ir unos segundos atrasado (el profesor lo acepta si la validación final es contra la base). CloudFront cuesta USD 25, 76 o 253 por preventa (moderado, alto, extremo) |
| Fuente | `jacobo/capacidad_y_volumetria.md` §6; `david/concurrencia.md` §0 |

## F-09. Una sola región escribe; RPO 0 de pagos por conciliación

| Campo | Contenido |
|---|---|
| Contexto | El enunciado exige RPO 0 para pagos. MRSC (RPO 0 entre regiones) no admite transacciones ni TTL; MREC es asíncrono y, si dos regiones escriben, "la última escritura gana" puede vender una silla dos veces |
| Alternativas | (a) MREC con dos regiones escribiendo. (b) MRSC para toda la compra. (c) MREC con una sola región que escribe y conciliación contra la pasarela. (d) Aceptar un RPO mayor que 0 |
| Criterio | RPO 0 del dinero sin romper la atomicidad de la compra ni la regla de oro |
| Elección | (c). Ante la pérdida de región se congelan solo las sillas en duda, se reabre y la conciliación termina después. El profesor lo aceptó con tres condiciones, todas atendidas: atraso de replicación con fuente (típicamente ≤ 1 s, diseño para 60 s con alarma), sillas en duda congeladas y RTO dentro de 15 minutos |
| Sacrificio | La base queda con RPO de segundos ante pérdida de región; el RPO 0 de pagos depende de un proceso, no de la réplica. RTO estimado de 4 a 11 minutos desde la declaración (más 2 a 5 de detección), **sin medir**: solo el simulacro lo confirma. Si pasara de 15, se automatiza el cambio de tráfico con Application Recovery Controller (costo por cotizar) |
| Fuente | `david/alta_disponibilidad.md` §2–§5; `miguel/fichas_decision_miguel.md` R-1; `david/respuestas_profesor.md` resp. 3 y 6 |
| Pendiente | Conformidad de Samuel |

## F-10. `bya_ledger` como fuente de las sillas en duda (D-2b)

| Campo | Contenido |
|---|---|
| Contexto | El plan era sacar la lista de sillas en duda de la búsqueda por fechas de Mercado Pago. En el sandbox esa búsqueda devolvió 0 resultados, incluso 14 minutos después |
| Alternativas | (a) Confiar en la búsqueda por fechas en producción sin haberla visto funcionar. (b) Libro de pagos `bya_ledger` en MRSC, escrito antes de cobrar. (c) Reembolsar todo pago de desastre sin sillas conocidas |
| Criterio | No descubrir en pleno desastre que la fuente de la lista no sirve |
| Elección | (b), aprobada por el grupo el 2026-11-04. Cada pago se consulta luego en Mercado Pago por su `id` |
| Sacrificio | Una escritura sincrónica entre regiones en el camino del pago (latencia sin medir); tabla MRSC en tres regiones con unas 24.000 escrituras por preventa grande (costo por calcular) |
| Fuente | `david/pasarelas.md` §7; `david/alta_disponibilidad.md` §5.0 |
| Pendiente | Clave listable por minuto y medición de latencia (Jacobo); costo (Juan Pablo) |

## F-11. Pasarela de pagos: Mercado Pago

| Campo | Contenido |
|---|---|
| Contexto | La conciliación necesita idempotencia, metadatos en el cobro y una forma de consultar pagos |
| Alternativas | Mercado Pago, Wompi, PayU Latam, ePayco (documentación no accesible), Stripe (no disponible para empresas en Colombia) |
| Criterio | Idempotencia que devuelva el mismo pago, metadatos propios en el cobro, consulta de pagos y webhook firmado |
| Elección | Mercado Pago. En el sandbox (11 de 13 pruebas) se confirmó que `metadata` guarda y devuelve las sillas y que la misma `X-Idempotency-Key` devuelve el mismo pago |
| Sacrificio | La búsqueda por fechas no funcionó en el sandbox (de ahí F-10). Comisión de referencia 3,29 % + COP 800 por cobro + IVA, sin confirmar en la cuenta |
| Fuente | `david/pasarelas.md` §1, §2 y §7; `david/pruebas/resultados_sandbox.json` |

## F-12. Respaldo inmutable en otra región y otra cuenta

| Campo | Contenido |
|---|---|
| Contexto | PITR protege de errores, pero no de quien tenga acceso a la cuenta y borre tablas y respaldos. El enunciado pide una copia inmutable o desconectada |
| Alternativas | (a) Solo PITR. (b) PITR + AWS Backup en la misma cuenta y región. (c) PITR + AWS Backup con copia a otra región y otra cuenta, en una bóveda con Vault Lock |
| Criterio | Sobrevivir a una cuenta comprometida con un costo que quepa en el presupuesto |
| Elección | (c), con Vault Lock probado antes en modo gobernanza |
| Sacrificio | El modo cumplimiento es irreversible y compromete el costo hasta que vence la retención; la copia diaria deja hasta 24 h en riesgo ante una cuenta comprometida; hay que operar dos cuentas |
| Fuente | `miguel/fichas_decision_miguel.md` R-2; `miguel/recuperacion_licenciamiento_carta.md` §5.5 |
| Pendiente | Costo real de AWS Backup con incrementalidad (Juan Pablo; la hoja `Respaldo` solo tiene la cota superior) |

## F-13. Estadio: un nodo por puerta como autoridad

| Campo | Contenido |
|---|---|
| Contexto | El ingreso no puede detenerse sin internet (hasta 4 horas aislado, según el profesor) y una boleta no puede entrar dos veces |
| Alternativas | (a) Cada lector decide solo con una copia local. (b) Un servidor central único. (c) Cada boleta tiene una puerta dueña y cada puerta un nodo que marca la boleta con un `UPDATE` atómico |
| Criterio | Cero doble ingreso sin depender de internet ni de la conexión entre puertas |
| Elección | (c), con dos servidores centrales en réplica síncrona y sincronización idempotente con DynamoDB al volver la conexión |
| Sacrificio | Asignación fija de puerta (no se puede desviar gente a otra puerta durante el evento). Cambiar un nodo caído exige que una persona confirme que está apagado (5 a 10 min, supuesto). Se cierran los reembolsos 2 h antes de abrir puertas |
| Fuente | `david/estadio.md` §1, §6 y §8 |

## F-14. Equipo de puerta: torniquetes del estadio

| Campo | Contenido |
|---|---|
| Contexto | Con 48 torniquetes propios (COP 216,1 M, solo el cuerpo), el Escenario B suma COP 336,6 M en el año 1 frente a un tope de 280 M, y todavía faltan cotizaciones |
| Alternativas | (1) 48 torniquetes propios. (2) Lectores QR que abren los torniquetes que ya tiene el estadio. (3) Alquilar torniquetes por evento. (4) Carriles con lector portátil y vallas. (5) Comprar 24 torniquetes |
| Criterio | Caber en el presupuesto sin cambiar la regla contra el doble ingreso (la autoridad es el nodo, no el torniquete) |
| Elección | (2) como base, (4) como respaldo en estadios sin torniquetes compatibles, (1) solo si el cliente exige equipo propio. Con (1), B superaba el tope del año 1 (COP 336,6 M) |
| Sacrificio | (2) depende de integrar equipos ajenos y de cada estadio; (4) no tiene barrera física y exige más personal |
| Fuente | `david/estadio.md` §9.2 |
| Pendiente | La pregunta 45 al profesor no tiene respuesta; si el cliente exige equipo propio, A lo absorbe con su margen y B no |

## F-15. Cola virtual propia sobre AWS

| Campo | Contenido |
|---|---|
| Contexto | 250.000 personas (610.352 en el año 5) esperan en una sala de espera. El producto de AWS para esto está descontinuado. El estado de la cola vive en AWS para no perder el turno si cae Bogotá |
| Alternativas | (a) Construcción propia sobre servicios de AWS. (b) Producto comercial |
| Criterio | Costo, SLA y que ninguna venta dependa solo de la cola |
| Elección | (a): tokens de admisión firmados emitidos por Lambda, posición como objeto cacheable en CloudFront y estado en ElastiCache Multi-AZ (patrón de SeatGeek [R-30]). Su costo ya está en las líneas de API, Lambda, ElastiCache y CloudFront |
| Sacrificio | Hay que construirla y probarla (no hay producto de AWS con SLA); un producto comercial no tiene precio público |
| Fuente | `jacobo/entrega_para_el_equipo.md` D-8; `juanpablo/costos_y_dimensionamiento.md` §6 |
| Pendiente | Prueba de carga antes de la primera preventa |

## F-16. Reserva del 10 %: solo B la usa

| Campo | Contenido |
|---|---|
| Contexto | El enunciado permite hasta un 10 % adicional sobre el año 1, una sola vez, con una solicitud de adición presupuestal |
| Alternativas | (a) No usarla. (b) Usarla para cubrir variaciones verificadas de precios |
| Criterio | Solo si el total cotizado supera el presupuesto base y no lo supera con la reserva |
| Elección | A no la usa (sobran COP 88,9 M en el año 1). B se pasa COP 9,6 M en el año 1 y la usa con la solicitud de adición presupuestal de `juanpablo/sensibilidad_y_tco.md` §7; le quedan 18,4 M de margen |
| Fuente | Borrador de solicitud en `juanpablo/sensibilidad_y_tco.md` §7 |

---

## F-17. AWS Backup semanal y mensual

| Campo | Contenido |
|---|---|
| Contexto | Miguel propuso copias diarias de AWS Backup con 35 días de retención, además de PITR de 35 días. Sin incrementalidad confirmada, la cota superior crece con cada copia completa |
| Alternativas | (a) Diaria 35 días + mensual 13 meses. (b) Semanal (5) + mensual (13), solo tablas críticas, en bóveda con Vault Lock y copia a otra cuenta y región. (c) Solo PITR |
| Criterio | Cubrir una cuenta comprometida sin duplicar lo que PITR ya da |
| Elección | (b). PITR da cualquier segundo de los últimos 35 días; la copia inmutable es para el caso en que la cuenta se pierda |
| Sacrificio | Ante una cuenta comprometida, la copia inmutable puede tener hasta 7 días de atraso (antes 24 h). Cuesta ≈ COP 3,2 M en el año 1 y 15,2 M en el año 5 |
| Fuente | `entrega/02_hoja_de_costos.xlsx`, línea AWS Backup; `miguel/fichas_decision_miguel.md` R-2 |

## F-18. Escenario B: VPN sobre dos enlaces dedicados

| Campo | Contenido |
|---|---|
| Contexto | La arquitectura de B usaba Direct Connect en Equinix BG1, pero el puerto, el *cross-connect* y el circuito no tienen precio publicado: no se pueden costear con fuente |
| Alternativas | (a) Direct Connect + VPN de respaldo. (b) Dos enlaces dedicados a internet de proveedores distintos (1 Gbps y 512 Mbps) con una VPN Site-to-Site sobre cada uno |
| Criterio | Redundancia real y precio con fuente |
| Elección | (b): COP 26,9 M al año con IVA (precios de la orden de compra 160603 de Colombia Compra Eficiente) + USD 876 al año de VPN |
| Sacrificio | La latencia por internet varía más que por Direct Connect; Direct Connect queda como mejora si la latencia medida fuera inaceptable |
| Fuente | `entrega/01_propuesta_escrita.pdf` §2.3 |

## F-19. Comisión de la pasarela fuera del presupuesto de infraestructura

| Campo | Contenido |
|---|---|
| Contexto | La hoja anterior incluía la comisión de Mercado Pago (3,29 % + COP 800 por cobro), sin valor promedio de orden |
| Alternativas | (a) Incluirla en el presupuesto de la base de datos. (b) Tratarla como costo de recaudo que se descuenta del ingreso |
| Criterio | El enunciado enumera lo que debe incluir el costo (§4) y no menciona comisiones de pago |
| Elección | (b); se reporta aparte cuando haya valor promedio de orden |
| Sacrificio | El costo total del negocio por boleta no queda en esta hoja |

## F-20. PCI DSS: tokenización y alcance reducido

| Campo | Contenido |
|---|---|
| Contexto | Guardar números de tarjeta en cualquier tabla, log o respaldo cuesta −1,0 |
| Alternativas | (a) Formulario propio que envía la tarjeta a la pasarela desde el servidor. (b) Formulario seguro de la pasarela en el navegador, que devuelve un token |
| Criterio | Que la tarjeta nunca toque servidores, base, logs ni respaldos de BoletaYa |
| Elección | (b). La tokenización reduce el alcance: solo se guardan `id` y token; se excluyen cuerpos de logs y `metadata` contiene identificadores. No se declara automáticamente fuera de PCI; el adquirente confirma el SAQ aplicable antes de producción |
| Sacrificio | Menos control sobre la experiencia de pago |
| Fuente | `entrega/01_propuesta_escrita.pdf` §8.3; validar con adquirente/asesor PCI |

## F-21. Retención de órdenes, pagos y boletas

| Campo | Contenido |
|---|---|
| Contexto | El enunciado pide 2 años en línea y luego el plazo de la norma tributaria |
| Alternativas | (a) Término de firmeza de la declaración de renta (art. 632 E.T. y art. 46 Ley 962 de 2005). (b) 10 años de la regla comercial (art. 28 Ley 962 de 2005, art. 60 C. Co.) |
| Criterio | Cumplir la obligación más larga que aplica a una SAS comerciante |
| Elección | Plazo por clase: soportes tributarios hasta la firmeza de la declaración (art. 46 Ley 962, modificado por art. 304 Ley 1819); libros y papeles mercantiles 10 años (art. 28 Ley 962). Diseño: 2 años en línea y S3 Object Lock hasta 10 años para soportes aplicables; validar matriz con asesor tributario |
| Sacrificio | Almacenamiento en S3 después del año 5 (bajo); no se puede borrar antes ni con permisos de administrador, salvo las supresiones de datos personales, que se manejan por seudonimización |
| Fuente | Estatuto Tributario art. 632; Ley 962 de 2005 arts. 28 y 46; Ley 1819 de 2016 art. 304 |

## F-22. Recomendación final: Escenario A

| Campo | Contenido |
|---|---|
| Contexto | Hay que recomendar un escenario y decir si conviene cambiar en algún año |
| Alternativas | A (todo en AWS + estadio local) o B (aplicación en Bogotá + base en AWS + estadio local) |
| Criterio | Costo, riesgo, RPO/RTO, pico, operación y crecimiento |
| Elección | A: COP 469,7 M de caja en 5 años frente a 697,1 M; latencia ≈ 22 ms frente a ≈ 353 ms; sin depender del enlace Bogotá–AWS; sigue cabiendo con doble preventa y doble cola, y B no en el año 5 |
| Sacrificio | Toda la operación depende de AWS; los datos quedan fuera de Colombia (también en B) |
| Cuándo cambiar | No hay un año en que B resulte mejor. Se revisaría si una norma exigiera los datos en Colombia o si AWS abriera una región en Colombia con DynamoDB (A se mudaría a esa región) |

## F-23. 12 terminales portátiles en vez de 24

| Campo | Contenido |
|---|---|
| Contexto | El diseño del estadio pedía 2 lectores portátiles por puerta; la referencia disponible (Zebra TC21, COP 1.973.336) haría que 24 unidades costaran 47,4 M |
| Alternativas | (a) 24 portátiles. (b) 12, uno por puerta. (c) Terminales genéricos importados (≈ COP 730.000, sin soporte local) |
| Criterio | Cubrir accesibilidad y un carril caído por puerta con soporte de marca |
| Elección | (b): COP 23,7 M |
| Sacrificio | Si caen dos carriles de una misma puerta a la vez, solo uno se cubre con portátil; la gente pasa por los otros carriles de esa puerta |

## F-24. Fondo de reposición del hardware del estadio

| Campo | Contenido |
|---|---|
| Contexto | El enunciado pide garantía y soporte por 5 años o su renovación; los precios de tienda traen 1 año de garantía y no hay cotización de soporte extendido |
| Alternativas | (a) Suponer soporte de 5 años sin precio. (b) Reservar cada año un porcentaje del hardware para reponer equipos. (c) Cotizar soporte del fabricante (no disponible hoy) |
| Criterio | No omitir un costo que podría cambiar la conclusión (−0,5) |
| Elección | (b): 10 % anual del hardware del estadio desde el año 2 (COP 15,6 M/año), más los 3 nodos de repuesto ya incluidos |
| Sacrificio | Es un supuesto del grupo, no una cotización; con una cotización real del fabricante se reemplaza |

## F-25. Escenario B sin caché en espera en us-east-2

| Campo | Contenido |
|---|---|
| Contexto | Con todo costeado, B costaba ≈ COP 300,1 M en el año 1 y ≈ COP 132,2 M en el año 5: no cabía ni con la reserva en el año 5 |
| Alternativas | (a) Declarar B no viable. (b) Quitar la caché en espera de us-east-2 (−10,5 M/año) y usar la reserva en el año 1 |
| Criterio | Presentar dos escenarios viables, con el sacrificio dicho |
| Elección | (b): B queda en 289,6 M (año 1, con reserva) y 121,7 M (año 5) |
| Sacrificio | Si se pierde la región, B pierde el estado de la cola virtual y readmite a los compradores por sorteo (runbook 2c de Miguel ya lo prevé); A conserva la cola |
