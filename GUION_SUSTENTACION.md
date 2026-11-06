# Guion de sustentación — quién hizo qué

**Orden:** el mismo de siempre. **Presentadores:** se le quitan a Jacobo las diapositivas 11 y 15; la 11 pasa a Samuel y la 15 a Miguel. Este guion cambia **lo que se dice**: en cada diapositiva se nombra a quién le pertenece ese sector del proyecto. Así el jurado ve que cada uno tiene un área y que todos la conocemos.
**Tiempo:** todos hablan **más o menos lo mismo, unos 4 minutos cada uno** (≈ 500 palabras). Jacobo tiene menos diapositivas, pero más largas (≈ 2 min cada una); Miguel tiene más, pero más cortas (≈ 1 min). Las cifras son las finales de `SUSTENTACION.md`.

## Reparto de diapositivas

| Integrante | Presenta | Diapositivas | Palabras habladas | Tiempo aprox. |
|---|---|---|---|---|
| Jacobo | 2, 5 y parte de la 20 | 2 | ≈ 500 | ≈ 4 min |
| David | 4, 7, 13, 18 y parte de la 20 | 4 | ≈ 545 | ≈ 4 min |
| Miguel | 3, 9, 12, **15**, 17 y parte de la 20 | 5 | ≈ 545 | ≈ 4 min |
| Juan Pablo | 6, 10, 14, 19 y parte de la 20 | 4 | ≈ 495 | ≈ 4 min |
| Samuel | 1, 8, **11**, 16 y parte de la 20 | 4 | ≈ 515 | ≈ 4 min |

Con pausas, señalando la pantalla y los pases de palabra, el total queda en unos 25–28 minutos: sobra margen dentro de los 30.

Jacobo presenta menos diapositivas, pero habla lo mismo que los demás porque las suyas son las más técnicas. En las preguntas de datos, capacidad y arquitectura responde él primero.

## Los cinco sectores

| Integrante | Sector | Diapositivas de su sector |
|---|---|---|
| **Jacobo** | Modelo de datos, capacidad y arquitectura | 2, 3, 4, 5, 6, 9, 10, 11 |
| **David** | Concurrencia, alta disponibilidad, pagos y estadio | 7, 8, 12, 14 |
| **Miguel** | Recuperación, respaldos, licenciamiento y runbooks | 12, 13, 16 |
| **Juan Pablo** | Costos, escenario B, sensibilidad y TCO | 10, 17, 18, 19 |
| **Samuel** | Seguridad, cumplimiento legal y comparación final (comodín del grupo) | 15, 19 |

---

## 1. Portada — presenta **Samuel**
**Sector: todo el grupo**

> "Buenos días. Somos el grupo 5 y les presentamos BoletaYa SAS: una base de datos en DynamoDB, sobre AWS, que pasa de 100 a 3.000 ventas por minuto sin vender dos veces la misma silla ni perder un pago.
> Nos repartimos el proyecto en cinco sectores. **Jacobo** diseñó el modelo de datos, la capacidad y la arquitectura. **David** se encargó de la concurrencia, la alta disponibilidad, los pagos y el estadio. **Miguel** hizo la recuperación ante desastres, los respaldos y el licenciamiento. **Juan Pablo** construyó la hoja de costos y el escenario híbrido. Y yo, **Samuel**, cubrí seguridad y cumplimiento legal, y apoyé a todos como comodín.
> Cada uno va a presentar también partes de los demás, porque todos conocemos el proyecto completo. Arranca Jacobo con el problema."

## 2. El problema en números — presenta **Jacobo**
**Sector: Jacobo (capacidad y volumetría)**

> "Mi sector fue el modelo de datos, la capacidad y la arquitectura, y empieza por entender cuánta carga tiene que aguantar la base.
> El 80 % del año BoletaYa vende unas 8.000 boletas al día. Eso es casi nada: unos 3,5 WRU por segundo, algo que cualquier tabla atiende sin esfuerzo.
> El problema son las preventas. Hay unas 25 al año, y en cada una se venden 60.000 boletas en 20 minutos. Son 24.000 órdenes, unas 20 por segundo, y cada orden consume entre 55 y 85 unidades de escritura según cuántos choques haya. Al mismo tiempo, 250.000 personas esperan en la cola mirando el mapa de sillas.
> Para diseñar tomé el pico multiplicado por cinco, porque las compras no llegan parejas sino en ráfagas, y le sumé un margen del 25 %. De ahí sale el pico de diseño de 10.546 WRU por segundo que van a ver más adelante.
> La exigencia del cliente es doble: cero sillas vendidas dos veces y cero pagos perdidos, incluso si algo falla. Y el presupuesto no alcanza para pagar la capacidad del pico los 365 días.
> Todo lo que van a ver sale de esa tensión: diseñar para el pico sin pagarlo todo el año. Miguel les muestra los dos escenarios."

## 3. Dos escenarios — presenta **Miguel**
**Sector: Jacobo (arquitectura) y Juan Pablo (escenario B)**

> "La arquitectura de los dos escenarios la diseñó **Jacobo**, y la variante híbrida, **Juan Pablo**.
> DynamoDB no se instala en un data center: DynamoDB Local es solo para desarrollo, y Outposts y Local Zones no lo ejecutan. Por eso la base vive en AWS en los dos escenarios.
> En el **escenario A**, todo está en AWS: aplicación, cola, caché y base en us-east-1, con us-east-2 en espera. En el **escenario B**, la aplicación y la caché están en Bogotá y llegan a la base por dos enlaces dedicados con VPN. En ambos, el estadio funciona local.
> David les explica cómo organizó Jacobo los datos."

## 4. Ocho tablas, no una — presenta **David**
**Sector: Jacobo (modelo de datos)**

> "Este modelo es de **Jacobo**. Él separó los datos en ocho tablas, una por cada tipo de dato. La más caliente es `bya_seats`: guarda el estado de cada silla y su bloqueo de 8 minutos, y no tiene índices secundarios. `bya_orders` guarda la orden junto con sus intentos de pago y su factura, porque forman un solo agregado. `bya_counters` lleva el contador exacto, y `bya_tickets` las boletas y los escaneos. Aparte están el catálogo, los usuarios, el historial y la auditoría.
> ¿Por qué no una sola tabla? Porque cada tipo de dato tiene una retención, una carga, unos permisos y un respaldo distintos, y en DynamoDB todo eso se configura por tabla. Además, las transacciones sí funcionan entre tablas.
> Jacobo les explica la clave de las sillas."

## 5. Sillas sin cuello de botella — presenta **Jacobo**
**Sector: Jacobo (modelo de datos)**

> "La clave de partición de las sillas fue la decisión más importante de mi sector, porque de ella depende que la base aguante el pico.
> En DynamoDB los datos se reparten en particiones según la clave, y cada partición aguanta como máximo 1.000 escrituras por segundo. No importa cuánta capacidad tenga la tabla: si todo cae en la misma partición, esa partición se satura. En el pico multiplicado por cinco, las sillas reciben unas 2.214 WRU por segundo.
> Probé tres claves. Si la clave fuera el evento, todo caería en una sola partición y no aguantaría. Si fuera la localidad, una localidad popular como oriental general recibiría unas 885 WRU por segundo, sin margen. Por eso elegí **evento, localidad y fila**: son unas 900 claves y cada una recibe unas 2,5 WRU por segundo, muy lejos del límite.
> El costo de esa decisión es que, para leer una localidad completa, hay que consultar fila por fila. Eso lo hace un solo proceso, el que construye el mapa, así que no pesa.
> El caso extremo es una sola silla muy disputada. Eso lo contienen la cola virtual, el límite de 10 sillas por usuario y los reintentos con *backoff*.
> Juan Pablo sigue con el contador."

## 6. El contador exacto — presenta **Juan Pablo**
**Sector: Jacobo (modelo de datos)**

> "El contador también lo diseñó **Jacobo**, y lo presento yo porque el costo de cada orden depende de él.
> Cuando alguien compra, una sola transacción hace todo: marca la silla como vendida, pone la orden como pagada, emite las boletas y suma en el contador. O pasa todo, o no pasa nada.
> Para que miles de compras no choquen en un mismo ítem, el contador se divide en **8 fragmentos**. Cada orden va al fragmento `hash(orden) mod 8`, así que un reintento cae siempre en el mismo. El total es la suma de los ocho con lectura fuerte.
> Hay que distinguir dos cosas: el contador es **exacto siempre**, pero la suma de ocho ítems no es un instante único.
> Ahora David les muestra por qué nunca se vende dos veces la misma silla."

## 7. Cero doble venta — presenta **David**
**Sector: David (concurrencia)**

> "Este es mi sector: la concurrencia. Ana y Beto piden la silla S24 en el mismo milisegundo. Los dos mandan una transacción con la misma condición: bloquear la silla solo si está disponible o si su bloqueo ya venció.
> DynamoDB serializa las transacciones, así que gana una. Ana bloquea la silla por 8 minutos. Beto recibe `ConditionalCheckFailed`, y **toda** su transacción se cancela: su orden no existe y su cupo no se descuenta.
> Escribí 50 casos de prueba y los 50 pasan en un simulador local, moto. La garantía viene de AWS; el simulador comprueba que las condiciones están bien escritas.
> El detalle está en el anexo de concurrencia. Samuel les cuenta qué pasa con los pagos."

## 8. Bloqueo de 8 minutos y pagos a medias — presenta **Samuel**
**Sector: David (concurrencia y pasarela de pagos)**

> "Esto lo diseñó **David**, y yo revisé la parte de privacidad de los datos que viajan a Mercado Pago.
> Primero: ¿quién libera la silla a los 8 minutos? **No es el TTL**, porque el TTL borra en días. La silla se libera en la condición del siguiente bloqueo, que la toma como disponible si ya venció.
> Segundo: si el pago se aprueba y la base falla, no se pierde nada. El intento de pago se escribe **antes** de cobrar, y un reconciliador lo confirma cada minuto.
> Tercero: si hay un reintento o un webhook duplicado, no se cobra dos veces. Cada intento lleva una llave de idempotencia, y lo probamos en el sandbox: la primera vez responde 201 y la segunda 200, con el mismo pago.
> Miguel sigue con el mapa."

## 9. El mapa no toca la base — presenta **Miguel**
**Sector: Jacobo (capacidad)**

> "Este cálculo es de **Jacobo**. Si las 250.000 personas de la cola leyeran el mapa de la base cada 10 segundos, serían 687.500 RRU por segundo: **17,2 veces** la cuota de lectura de una tabla.
> Por eso el mapa sale de instantáneas en CloudFront. Un solo constructor lee la base, unas 450 RRU por segundo, y publica la copia. El mapa puede ir unos segundos atrasado, pero nunca decide una silla: la compra siempre se valida con la transacción, y el profesor confirmó que eso es aceptable.
> Juan Pablo les explica cómo pagamos la capacidad."

## 10. Capacidad sin pagar el pico todo el año — presenta **Juan Pablo**
**Sector: Jacobo (capacidad) y Juan Pablo (costos)**

> "La capacidad la calculó **Jacobo**, y yo la convertí en costos. El pico de diseño es de 10.546 WRU por segundo.
> Comparamos tres opciones para el año 1. La capacidad **provisionada fija al pico** costaría USD 63.176, y en promedio se usaría el 0,037 % de lo que se paga. La **provisionada con escalado programado** costaría USD 880. La **on-demand con pre-calentamiento** cuesta USD 83, y es la que elegimos.
> El auto scaling reactivo no sirve aquí: tarda más de 2 minutos en reaccionar y, mientras tanto, rechaza tráfico. Por eso pedimos el pre-calentamiento 24 horas antes de cada preventa.
> Samuel les cuenta por qué estamos en Virginia."

## 11. Región y latencia — presenta **Samuel**
**Sector: Jacobo (arquitectura) y Samuel (transferencia de datos)**

> "La región la eligió **Jacobo**, y yo revisé si era legal tener los datos allá. Jacobo eligió **us-east-1**, en Virginia: desde Bogotá tiene unos 77 ms de latencia, contra unos 112 de São Paulo. Además, en São Paulo DynamoDB cuesta un 50 % más y no tiene MRSC, que necesitamos para el libro de pagos.
> La latencia la midió un tercero, no nosotros contra AWS; eso lo dejamos claro.
> ¿Se pueden tener los datos en Estados Unidos? Sí. Revisé la Ley 1581: Estados Unidos está en la lista de países adecuados de la SIC, así que la transferencia es lícita con aviso y autorización del titular.
> La alterna es us-east-2. Miguel les explica qué pasa si cae la región principal."

## 12. Si cae una región — presenta **Miguel**
**Sector: David (alta disponibilidad) y Miguel (runbooks)**

> "El estudio de conmutación es de **David**, y yo escribí los runbooks y el simulacro.
> Solo una región escribe: con dos regiones escribiendo gana la última escritura, y se podría vender una silla dos veces. Si cae us-east-1, se cierra la admisión, se pasa el tráfico a us-east-2, se congelan **solo** las sillas con un pago en duda según `bya_ledger` y se reabre la venta por tramos.
> El RTO estimado es de **4 a 11 minutos**, con meta de menos de 15, y el RPO de los pagos es 0 gracias al libro y a la conciliación. El RTO es estimado: se mide en el simulacro. David sigue con los respaldos."

## 13. Respaldos que no frenan la preventa — presenta **David**
**Sector: Miguel (recuperación y respaldos)**

> "Esta parte es de **Miguel**. Son tres capas de respaldo, y ninguna frena la preventa.
> La primera son las **tres zonas** de la región: si cae una zona, no se pierde nada y no hay que conmutar. La segunda es **PITR** de 35 días: ante un error humano o datos corruptos, se puede volver a cualquier segundo hasta 5 minutos antes del presente. La tercera es una **bóveda inmutable** con AWS Backup semanal y mensual, Vault Lock, en otra cuenta y otra región, para el caso de ransomware o borrado malicioso.
> Además, no se hacen cambios desde 24 horas antes hasta 3 horas después de cada preventa.
> Juan Pablo les cuenta qué pasa en el estadio."

## 14. El estadio sin internet — presenta **Juan Pablo**
**Sector: David (estadio)**

> "El diseño del estadio es de **David**, y yo le puse precio a cada equipo. La regla es simple: una puerta, un nodo, una sola autoridad.
> Cada localidad entra por una puerta. El nodo de esa puerta marca la boleta como usada **antes** de abrir el torniquete, así que dos lectores no pueden aceptar la misma boleta dos veces.
> Sin internet, el estadio sigue funcionando hasta **4 horas** igual que siempre. Cuando vuelve la conexión, los escaneos suben con una transacción idempotente.
> Usamos los torniquetes del propio estadio, con 48 lectores QR.
> Miguel les presenta la parte de Samuel: seguridad."

## 15. Seguridad y cumplimiento — presenta **Miguel**
**Sector: Samuel (seguridad y cumplimiento)**

> "Este sector es de **Samuel**. La tarjeta nunca llega a nuestra base: Mercado Pago la tokeniza en el navegador y solo guardamos el id y el token. Eso reduce el alcance de PCI DSS; el adquirente confirma qué cuestionario aplica.
> Hay un rol por función, todo se cifra con KMS y cada cambio de precio o cupo queda auditado en la misma transacción. En lo legal, Samuel definió la retención: 2 años en línea y hasta 10 en S3 con Object Lock.
> Ahora Samuel les presenta mi parte: las licencias."

## 16. Versiones y licencias — presenta **Samuel**
**Sector: Miguel (licenciamiento)**

> "El licenciamiento lo trabajó **Miguel**. DynamoDB no tiene versión ni licencia: es un servicio administrado. Lo que sí tiene versión es lo que lo rodea, y eso está costeado.
> Node.js 24 tiene soporte hasta abril de 2028, así que costeamos dos migraciones. El SDK de AWS necesita una migración mayor. Ubuntu 26.04 tiene soporte hasta 2031. PostgreSQL 18, en el estadio, tiene soporte hasta 2030.
> Escalar en preventa o tener réplicas no agrega licencias. El costo está en las escrituras replicadas, y ya está en la hoja.
> Con eso pasamos a la plata. Miguel les presenta los costos de Juan Pablo."

## 17. Costos por escenario — presenta **Miguel**
**Sector: Juan Pablo (costos)**

> "La hoja de costos es de **Juan Pablo**; cada precio tiene fuente, fecha y captura.
> El **escenario A** cuesta 191,1 millones el año 1, contra un tope de 280: le sobran 88,9. En cinco años son 469,7 millones de 800.
> El **escenario B** cuesta 289,6 millones el año 1: se pasa 9,6 y solo cabe con la reserva del 10 %. Suma dos servidores en Bogotá, energía, dos enlaces y la VPN, y aun así hubo que quitarle la caché en espera de us-east-2.
> El estadio cuesta unos 157 millones en los dos. David les muestra qué pasa si el negocio crece."

## 18. Sensibilidad y TCO — presenta **David**
**Sector: Juan Pablo (sensibilidad y TCO)**

> "El análisis de sensibilidad también es de **Juan Pablo**. Probó qué pasa si se duplican las preventas y si se duplica la gente en la cola.
> Con los dos cambios a la vez, al escenario **A** todavía le sobran 80,5 millones el año 1 y 24,8 el año 5. El escenario **B** queda con 10 millones el año 1, y solo usando la reserva, y en el año 5 queda en **−11 millones: ya no cabe**.
> Lo que más crece con la cola es el mapa en CloudFront y el WAF. DynamoDB casi no cambia, porque la cola regula las compras.
> Sumando las horas de administración, el costo total a 5 años es de 615,9 millones para A y 872,1 para B.
> Juan Pablo los compara."

## 19. A contra B — presenta **Juan Pablo**
**Sector: Juan Pablo (costos y escenario B), con Samuel (comparación)**

> "Esta comparación la armé con **Samuel**. B no compra nada a cambio de lo que cuesta.
> En **costo**, A cuesta 469,7 millones en cinco años y B 697,1. En **latencia**, una compra en A tarda unos 22 ms y en B unos 353, porque cada transacción cruza el enlace. En **riesgo**, A depende de AWS; B también, y además del enlace y del data center. El **RPO y el RTO** son iguales, pero B suma un runbook más. En **operación**, A usa servicios administrados y B suma servidores, energía, enlaces y parches. En **crecimiento**, A cabe con la sensibilidad y B no.
> Los datos en Colombia son un empate, porque en B la base también vive en AWS.
> Cerramos todos."

## 20. Recomendación — presentan **todos**
**Sector: cada uno da la razón de su sector**

> **Samuel:** "Recomendamos el escenario A, todo en AWS."
> **Juan Pablo (costos):** "Ahorra 227,4 millones en cinco años y no toca la reserva."
> **Jacobo (arquitectura):** "Desde la arquitectura, A es más simple: la aplicación y la base están en la misma región, así que cada compra es unos 330 ms más rápida. Y la base aguanta el pico de preventa con on-demand, sin pagarlo todo el año."
> **Miguel (recuperación):** "La venta no depende de un enlace ni de un data center sin planta, y se recupera en 4 a 11 minutos."
> **David (concurrencia):** "En los dos escenarios hay cero dobles ventas y cero pagos perdidos. Lo que no pudimos medir, que son el RTO real, la latencia real y los conflictos, se valida en un simulacro antes de la preventa más grande."
> **Jacobo:** "No hay ningún año en que convenga cambiar. Solo lo revisaríamos si una norma exigiera los datos en Colombia o si AWS abriera allí una región con DynamoDB."
> **Samuel:** "Gracias; quedamos atentos a sus preguntas."

---

## En las preguntas
Responde primero el **dueño del sector** (tabla de arriba); si complementa otro, empieza con "complemento:". Respuestas cortas y fichas en `SUSTENTACION.md` §4.
