# Registro de decisiones (anexo de la propuesta)

**Estado:** registro integrado 2026-11-04. Incluye decisiones de diseño tomadas y recomendaciones del equipo; las aprobaciones externas/cotizaciones pendientes se señalan explícitamente.
**Mínimo exigido:** 8 fichas con contexto, alternativas, criterio, elección y sacrificio. Hay 19 fichas; las decisiones presupuestales son propuestas del equipo, no aceptación de proveedor o del cliente.
Las fichas enlazan a sus fuentes; las propuestas presupuestales no sustituyen aprobación del cliente o contratos.

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
| F-14 | Equipo de puerta del estadio (torniquetes) | David, Juan Pablo | Propuesta del grupo: opción 2; compatibilidad por verificar |
| F-15 | Cola virtual: construir o comprar | Jacobo, Juan Pablo | Propuesta: comprar con SLA/precio aceptable; proveedor pendiente |
| F-16 | Uso de la reserva del 10 % | Juan Pablo | **Abierta** (solo si hace falta) |
| F-17 | Retención y transferencia de datos | Samuel | Propuesta cerrada, requiere validación jurídica/contractual antes de producción |
| F-18 | Escenario recomendado | Grupo | Propuesta: A; costo total pendiente de cotizaciones |
| F-19 | Torniquetes y cola virtual | Grupo | Opción 2 de estadio; comprar cola virtual si SLA y cotización caben; sin proveedor contratado |

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
| Estado | Sección en `jacobo/arquitectura.md` §2.5 (máximo 2 páginas de texto) |

## F-02. Región us-east-1 con alterna us-east-2

| Campo | Contenido |
|---|---|
| Contexto | No se ha confirmado que AWS tenga una región con DynamoDB en Colombia (verificación pedida por el profesor). Hay que elegir dónde vive la base |
| Alternativas | (a) sa-east-1 (São Paulo). (b) us-east-1 (Virginia) con us-east-2 (Ohio) como alterna. (c) Otra región norteamericana |
| Criterio | Latencia desde Bogotá, precio, disponibilidad de funciones (MRSC) y viabilidad legal |
| Elección | (b). Ping medido por un tercero desde Bogotá: 77,1 ms a Washington frente a 112,2 ms a São Paulo. DynamoDB cuesta un 50 % más en São Paulo, que además no tiene MRSC |
| Sacrificio | Los datos personales quedan fuera de Colombia y exigen el análisis de transferencia internacional de la Ley 1581. La latencia es un ping de un tercero, no una medición contra AWS |
| Fuente | `jacobo/arquitectura.md` §1; `jacobo/calculos/evidencia/latencia_wondernetwork_bogota_2026-10-29.txt` |
| Pendiente | Validación jurídica/contractual del tratamiento; revisión de región alternativa si cambia norma o requisito |

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
| Estado | Propuesta en `integracion/propuesta_borrador.md` §8; validación contractual pendiente |

## F-10. `bya_ledger` como fuente de las sillas en duda (D-2b)

| Campo | Contenido |
|---|---|
| Contexto | El plan era sacar la lista de sillas en duda de la búsqueda por fechas de Mercado Pago. En el sandbox esa búsqueda devolvió 0 resultados, incluso 14 minutos después |
| Alternativas | (a) Confiar en la búsqueda por fechas en producción sin haberla visto funcionar. (b) Libro de pagos `bya_ledger` en MRSC, escrito antes de cobrar. (c) Reembolsar todo pago de desastre sin sillas conocidas |
| Criterio | No descubrir en pleno desastre que la fuente de la lista no sirve |
| Elección | (b), aprobada por el grupo el 2026-11-04. Cada pago se consulta luego en Mercado Pago por su `id` |
| Sacrificio | Una escritura sincrónica entre regiones en el camino del pago (latencia sin medir); tabla MRSC en tres regiones con unas 24.000 escrituras por preventa grande (costo por calcular) |
| Fuente | `david/pasarelas.md` §7; `david/alta_disponibilidad.md` §5.0 |
| Estado | Diseño `bya_ledger` y runbook actualizado; prueba de latencia entre regiones/costo siguen pendientes |

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

## F-14. Equipo de puerta del estadio — ABIERTA

| Campo | Contenido |
|---|---|
| Contexto | Con 48 torniquetes propios (COP 216,1 M, solo el cuerpo), el Escenario B suma COP 336,6 M en el año 1 frente a un tope de 280 M, y todavía faltan cotizaciones |
| Alternativas | (1) 48 torniquetes propios. (2) Lectores QR que abren los torniquetes que ya tiene el estadio. (3) Alquilar torniquetes por evento. (4) Carriles con lector portátil y vallas. (5) Comprar 24 torniquetes |
| Criterio | Caber en el presupuesto sin cambiar la regla contra el doble ingreso (la autoridad es el nodo, no el torniquete) |
| Propuesta de David | (2) como base, (4) como respaldo en estadios sin torniquetes compatibles, (1) solo si el cliente exige equipo propio |
| Sacrificio | (2) depende de integrar equipos ajenos y de cada estadio; (4) no tiene barrera física y exige más personal |
| Fuente | `david/estadio.md` §9.2 |
| Estado | Opción 2 propuesta, sujeto a inventario y compatibilidad física del estadio |

## F-15. Cola virtual: construir o comprar — ABIERTA

| Campo | Contenido |
|---|---|
| Contexto | 250.000 personas (610.352 en el año 5) esperan en una sala de espera. El producto de AWS para esto está descontinuado. El estado de la cola vive en AWS para no perder el turno si cae Bogotá |
| Alternativas | (a) Construcción propia sobre servicios de AWS. (b) Producto comercial |
| Criterio | Costo, SLA y que ninguna venta dependa solo de la cola |
| Elección | Sin decidir |
| Sacrificio | — |
| Fuente | `jacobo/entrega_para_el_equipo.md` D-8; `juanpablo/costos_y_dimensionamiento.md` §6 |
| Estado | Opción 2 seleccionada; lectores y compatibilidad física siguen por cotizar/verificar |

## F-16. Reserva del 10 % — ABIERTA

| Campo | Contenido |
|---|---|
| Contexto | El enunciado permite hasta un 10 % adicional sobre el año 1, una sola vez, con una solicitud de adición presupuestal |
| Alternativas | (a) No usarla. (b) Usarla para cubrir variaciones verificadas de precios |
| Criterio | Solo si el total cotizado supera el presupuesto base y no lo supera con la reserva |
| Elección | Sin decidir hasta tener las cotizaciones |
| Fuente | Borrador de solicitud en `juanpablo/sensibilidad_y_tco.md` §7 |

---

## Fichas que todavía no existen y conviene agregar

* **Seguridad (Samuel):** mínimo privilegio y roles, cifrado y llaves (KMS), PCI DSS solo con token, retención legal.
* **Historial por Streams y auditoría administrativa síncrona** (D-10 de Jacobo): está propuesta pero no aprobada formalmente.
* **Sistema operativo del estadio** (Ubuntu 26.04 LTS + Ubuntu Pro o cambio de versión hacia 2031; PostgreSQL 18 con una migración hacia 2030): `david/estadio.md` §9.1 y `miguel/recuperacion_licenciamiento_carta.md` §5.3.
* **Recomendación final** (5.8): qué escenario y, si aplica, en qué año cambiar.


## F-17. Transferencia internacional y conservación

| Campo | Contenido |
|---|---|
| Contexto | Los datos se procesan en AWS us-east-1/us-east-2; el profesor condiciona la aceptación a analizar Ley 1581 y retención tributaria. |
| Alternativas | Mantener región EE. UU. con cumplimiento documentado; migrar a otra jurisdicción adecuada; mantener datos en Colombia cuando exista servicio compatible/disponible. |
| Criterio | Adecuación SIC, contrato responsable-encargado, minimización, seguridad, derechos y evidencia. |
| Elección | Mantener EE. UU. sujeto a contrato y responsabilidad demostrada. Estados Unidos aparece en el numeral 3.2 del Título V de la Circular Única SIC vigente. El flujo AWS se clasifica primero como transmisión internacional si AWS actúa como encargado. |
| Sacrificio | Datos fuera del país y dependencia de controles/contrato AWS; la lista de adecuación no elimina obligaciones. Retener comprobantes tributarios hasta firmeza aplicable; no imponer TTL de 2 años sobre evidencia tributaria. |
| Fuente | Ley 1581/2012 art. 26; Circular Única SIC Título V §3.2; E.T. art. 632; Ley 962/2005 art. 46. `integracion/propuesta_borrador.md` §8.4. |

## F-18. Recomendación A

| Campo | Contenido |
|---|---|
| Contexto | A ubica aplicación/base en AWS; B deja aplicación/caché en Bogotá y base AWS. |
| Alternativas | A o B. |
| Criterio | Latencia estimada de compra, dependencia de enlace, recuperación, complejidad y costo verificable. |
| Elección | Proponer A como arquitectura objetivo; estadio local en ambos. |
| Sacrificio | A requiere operar la aplicación en nube. El costo total A y B aún no es certificable; los costos parcialmente cuantificados favorecen A y la aprobación presupuestal queda pendiente. |
| Fuente | `integracion/propuesta_borrador.md` §10; `juanpablo/costos_boletaya.xlsx` Resumen. |

## F-19. Equipos del estadio y cola virtual

| Campo | Contenido |
|---|---|
| Contexto | Torniquetes propios exceden presupuesto B; la sala de espera soporta hasta 250.000 usuarios y el servicio de AWS antes evaluado está discontinuado. |
| Alternativas | F-14 opción 1: comprar torniquetes; opción 2: usar los del estadio y añadir lectores/controlador compatibles. F-15: construir cola o comprar proveedor especializado. |
| Criterio | No duplicar infraestructura que el estadio ya provee; admitir 250.000 usuarios con orden estable, seguridad, SLA, pruebas y salida/retención documentadas. |
| Elección | Opción 2 para torniquetes, sujeto a inventario y compatibilidad en sitio. Comprar cola virtual a proveedor especializado si SLA/pruebas/cotización caben; mantener diseño de construcción propia como contingencia de evaluación. Ningún proveedor está contratado. |
| Sacrificio | Dependencia de equipos del estadio y del proveedor; costos de lectores y cola siguen pendientes y pueden cambiar el veredicto presupuestal. |
| Fuente | `david/estadio.md` §9.2; `juanpablo/costos_boletaya.xlsx` `Costos_Anuales`; `jacobo/capacidad_y_volumetria.md` §6. |
