# Preguntas para el profesor (versión ampliada, sin suposiciones)

**Fecha:** 2026-11-03 · Las P-1 a P-8 son las ya registradas en `jacobo/entrega_para_el_equipo.md`; desde la P-9 son nuevas. Cada pregunta dice **qué decisión cambia la respuesta**, para priorizar. Las marcadas **(★)** bloquean diseño; si solo se puede enviar un mensaje, enviar estas.

## A. Interpretación del enunciado y alcance

| # | Pregunta | Qué cambia |
|---|---|---|
| P-1 ★ | DynamoDB solo existe como servicio de AWS y no se instala en un data center. En el Escenario B, ¿se acepta la variante híbrida (aplicación, caché y servidor de estadio en Bogotá; base en AWS), o debe interpretarse de otra forma? | Arquitectura y costos del Escenario B |
| P-2 | La preventa es de 60.000 boletas y los estadios tienen 45.000 sillas. ¿Son varias fechas, un festival o un error de redacción? ¿Se modela el peor caso en un solo evento? | Capacidad, particiones, cola virtual |
| P-3 ★ | En el Escenario A, ¿la aplicación debe vivir físicamente en el data center de Bogotá, o puede estar en la nube junto a la base? | Latencia, costos, quién conmuta |
| P-9 | ¿Se entregan los dos escenarios (A y B) completos y comparados, o se elige uno? ¿Cómo se pondera cada uno en la nota? | Esfuerzo y estructura de la entrega |
| P-10 | ¿Hay un formato, plantilla o extensión máxima obligatoria para cada entregable (informe, anexo, presentación)? | Forma de los documentos |
| P-11 | ¿La sustentación es individual por parte o grupal? ¿Cuánto dura y qué se debe mostrar en vivo (demo, consola de AWS, solo documentos)? | Preparación |
| P-12 | ¿Se espera una implementación funcional (tablas creadas, código ejecutándose) o basta el diseño y el pseudocódigo? | Si hay que construir algo real |
| P-13 | ¿Se puede usar una cuenta de AWS real para pruebas y mediciones? ¿Quién asume el costo? ¿Las evidencias medidas valen más que las citadas de la documentación? | Evidencia de la rúbrica |
| P-14 | ¿Cuáles son los criterios exactos de cada punto de la rúbrica? ¿Hay un ejemplo de entrega con puntaje máximo? | Prioridades |
| P-15 | ¿Las referencias deben ser solo documentación oficial de AWS o se aceptan blogs, casos de estudio y artículos académicos? ¿Hay formato de citación? | Cómo citar |

## B. Concurrencia y consistencia (rúbrica 5.2 y anexo)

| # | Pregunta | Qué cambia |
|---|---|---|
| P-16 ★ | ¿Qué se considera "doble venta"? ¿Basta con que dos órdenes no terminen con la misma silla, o también se prohíbe que dos usuarios vean la misma silla como "bloqueada" a la vez por un instante? | Nivel de consistencia exigido |
| P-17 | ¿El tiempo de bloqueo de una silla (nosotros usamos 8 minutos) lo fija el enunciado o es decisión del grupo? ¿Hay un máximo de espera de pago? | Parámetros de la transacción |
| P-18 | ¿Cuántas sillas puede comprar un usuario por evento? Usamos 10. ¿Lo define el enunciado o la empresa? ¿Se cuenta por usuario, por tarjeta, por documento o por dispositivo? | Antibots y límites |
| P-19 | Si el pago se aprueba después de vencer el bloqueo y otro usuario tomó la silla, proponemos reembolsar. ¿Se acepta, o debe reubicarse al cliente en otra silla equivalente? ¿En cuánto tiempo debe devolverse el dinero? | Reglas de negocio de la confirmación |
| P-20 | ¿Se puede vender por encima del aforo (sobreventa deliberada) o está prohibido en todo caso? | Modelo de inventario |
| P-21 | ¿Las sillas se escogen una a una (mapa) o la plataforma asigna "mejor disponible"? ¿Hay localidades sin numeración (general)? | Modelo de datos y contención |
| P-22 | ¿El pago se hace dentro de nuestra plataforma o en un sitio de la pasarela? ¿Hay una pasarela impuesta (por ejemplo PSE, Wompi, PayU, Stripe)? ¿Se puede suponer una? | RPO 0 de pagos, idempotencia |
| P-23 | ¿Se debe soportar compra por varios canales a la vez (web, app, taquilla física)? ¿Cómo se coordinan con la misma base? | Alcance de la concurrencia |
| P-24 | ¿Qué latencia máxima es aceptable en la compra (p. ej. p95 en ms) y en la sala de espera? ¿Hay un objetivo de disponibilidad por servicio, no solo global? | Dimensionamiento |
| P-25 | ¿Cómo se debe tratar el consumo de capacidad: bajo demanda o aprovisionada? ¿El enunciado fija un límite de costo? | Capacidad y presupuesto |
| P-5 | ¿Se acepta un producto comercial de cola virtual como componente auxiliar (costeado), dado que el de AWS está discontinuado? | Contención en picos |
| P-26 | ¿Se acepta que parte del control antibots (captcha, verificación de dispositivo) sea de terceros? | Antibots |
| P-27 | ¿El anexo de concurrencia debe estar en pseudocódigo, en código real de un lenguaje concreto o en SQL/PartiQL? ¿Se exigen las líneas de tiempo como diagramas? | Formato del anexo |
| P-28 | ¿Los cuatro escenarios del anexo están definidos por el enunciado (cuáles son) o los elige el grupo? | Contenido del anexo |
| P-29 | ¿Se acepta la lectura fuerte y las transacciones de DynamoDB, que consumen el doble de capacidad, o hay que optimizar para menos costo con consistencia eventual? | Costo vs. garantía |

## C. Alta disponibilidad, conmutación y recuperación

| # | Pregunta | Qué cambia |
|---|---|---|
| P-4 ★ | "Pérdida total del sitio": ¿equivale a pérdida de zona, de región o del data center? Con transacciones, RPO 0 entre regiones no es alcanzable con DynamoDB; ¿se acepta RPO 0 de pagos por conciliación con la pasarela, manteniendo las ventas cerradas hasta conciliar? | Toda la sección de HA y recuperación |
| P-30 ★ | El RTO de 15 minutos, ¿se mide desde que ocurre la falla o desde que se declara? ¿Incluye la detección? ¿Y hasta cuándo: hasta aceptar compras otra vez, o hasta tener todo conciliado? | Si el diseño cumple o no |
| P-31 | El RPO 0, ¿aplica a todo dato o solo a pagos y boletas confirmadas? ¿Se tolera perder bloqueos de sillas y órdenes sin pagar? | Alcance real del RPO |
| P-32 | ¿Se acepta que, durante una conmutación regional, se cierren las ventas unos minutos (modo seguro), o el servicio debe seguir vendiendo? | Diseño de conmutación |
| P-33 | ¿Se acepta que el RTO medido sea estimado con documentación de AWS (que no publica una cifra de conmutación regional) o se exige un simulacro medido? | Evidencia |
| P-34 | ¿Se permite alojar una réplica en otra región de AWS (us-east-2)? ¿Hay restricciones de ubicación para los datos? | Topología |
| P-6 ★ | ¿Se acepta alojar datos de compradores en una región fuera de Colombia (EE. UU.) con el análisis de transferencia internacional de Samuel? | Región y cumplimiento |
| P-35 | ¿Qué disponibilidad exige el enunciado: 99,99 %, 99,999 % u otra? ¿Se mide por mes, por año o por preventa? | SLA y tipo de tabla global |
| P-36 | ¿Se exige copia de seguridad (backup) con restauración a un punto en el tiempo, además de la replicación? ¿Con qué retención? | Recuperación ante errores lógicos |
| P-37 | ¿Se considera un error humano o un ataque (borrado de datos, ransomware) dentro de los "desastres" a cubrir, o solo fallas de infraestructura? | Alcance del plan |
| P-38 | ¿Con qué frecuencia deben hacerse los simulacros de recuperación y quién debe aprobar la reapertura tras un desastre? | Operación |
| P-39 | Si la región original vuelve, ¿se espera que se regrese a ella (failback) o se puede quedar en la alterna? | Runbook de retorno |
| P-40 | ¿Se acepta que el reembolso de pagos sin sillas conocidas (porque la pasarela no guardó metadatos) sea la política en desastre? | Pérdida de ventas vs. integridad |

## D. Ingreso al estadio sin internet

| # | Pregunta | Qué cambia |
|---|---|---|
| P-41 ★ | ¿"Sin internet" significa que el estadio pierde el enlace con AWS, o también que se cae su red interna? ¿Por cuánto tiempo hay que operar aislado (minutos, horas, todo el evento)? | Autonomía del nodo |
| P-42 | ¿Se debe impedir el doble ingreso entre puertas distintas aun sin internet? Nuestra propuesta asigna una puerta por boleta; ¿es aceptable restringir cada boleta a una puerta? | Restricción de negocio |
| P-43 | Si no es aceptable limitar a una puerta, ¿se tolera una ventana de doble ingreso (con reconciliación posterior) en modo aislado? ¿Cuánto? | E-R1, E-R2 |
| P-44 | ¿Cuántas puertas, torniquetes y asistentes por hora hay que suponer por estadio? Usamos 12 puertas y 4 torniquetes por puerta como supuesto. | Equipo y costo |
| P-45 | ¿Qué debe leer el torniquete: QR, NFC, código de barras? ¿El QR puede ser estático firmado (HMAC) o debe cambiar cada pocos segundos? | Antifraude |
| P-46 | ¿El ingreso debe validarse contra una lista local, o se permite un servidor local en el estadio con base propia (PostgreSQL)? | Arquitectura local |
| P-47 | ¿Se exige que el equipo local tenga energía de respaldo (UPS, planta)? ¿Por cuánto tiempo? | Costo |
| P-48 | ¿Cuánto debe tardar la validación en un torniquete? ¿Qué se hace con las boletas inválidas o duplicadas: bloquear, avisar, escalar a un supervisor? | Flujo operativo |
| P-49 | ¿Se acepta el ingreso manual (supervisor autoriza con documento) como contingencia? ¿Cómo se registra? | Contingencia |
| P-50 | ¿Los equipos del estadio deben tener soporte del fabricante y sistema operativo vigente por un mínimo de años? Miguel propone al menos 5. | Licenciamiento y ciclo de vida |
| P-51 | ¿El costo del equipo del estadio entra en el costo por preventa, en el costo anual o como inversión inicial? | Cálculo de Juan Pablo |

## E. Seguridad, cumplimiento y datos personales

| # | Pregunta | Qué cambia |
|---|---|---|
| P-52 | ¿Qué normas hay que considerar: Ley 1581 de 2012 de datos personales, PCI DSS para pagos, otra? ¿El análisis legal es parte de la nota o solo un anexo? | Alcance de Samuel |
| P-53 | ¿Se almacenan datos de tarjeta en nuestra plataforma o solo tokens de la pasarela? | PCI DSS |
| P-54 | ¿Cuánto tiempo deben conservarse órdenes, pagos, boletas y facturas? (hay que decidir TTL y archivo) | Retención y costo |
| P-55 | ¿Se requiere facturación electrónica ante la DIAN? ¿Con qué proveedor? (el modelo tiene un registro de factura por orden) | Modelo de datos |
| P-56 | ¿Qué debe registrarse en auditoría y por cuánto tiempo (accesos, cambios de precios, reembolsos)? | Almacenamiento y costo |
| P-57 | ¿Se debe poder borrar los datos de un usuario si lo pide (derecho de supresión) aunque haya boletas o facturas asociadas? | Modelo y legal |

## F. Capacidad, volumetría y costos

| # | Pregunta | Qué cambia |
|---|---|---|
| P-7 | El enunciado pide "volumen por nivel de almacenamiento": ¿cuenta como niveles Standard / Standard-IA / S3 de archivo? | Volumetría |
| P-8 | ¿Se exige la captura de la AWS Pricing Calculator aun cuando los precios vengan de la API oficial de precios? | Evidencia de costos |
| P-58 | ¿Qué horizonte se usa para costos: por preventa, mensual o anual? ¿Cuántas preventas al año? | Costos |
| P-59 | ¿Se usa una tasa de cambio fija COP/USD, o la del día? ¿Se incluyen impuestos (IVA)? | Costos |
| P-60 | ¿Las licencias de software (base, antivirus, sistema operativo) entran en el costo, y de qué fecha de precios? | Licenciamiento |
| P-61 | ¿Se espera comparar con otra base (SQL Server, PostgreSQL) para justificar DynamoDB, o la elección ya está impuesta? | Justificación |
| P-62 | El enunciado habla de "horas de DBA por preventa" (6): ¿es un dato fijo, o lo estimamos? ¿Cuál es el costo por hora? | Costos |

## G. Trabajo en equipo y entrega

| # | Pregunta | Qué cambia |
|---|---|---|
| P-63 | ¿Se permite usar GitHub (repositorio) y herramientas de IA para redactar? ¿Debe declararse? | Integridad académica |
| P-64 | El repositorio es público: ¿es aceptable, o debe ser privado y compartido solo con el profesor? | Privacidad |
| P-65 | ¿La nota de cada parte es individual? ¿Cómo se evalúa la coherencia entre las partes de los integrantes (p. ej. David–Jacobo)? | Coordinación |
| P-66 | ¿Hay fecha y hora de entrega de borradores y de entrega final? ¿Se puede entregar una versión corregida tras la retroalimentación? | Calendario |
| P-67 | ¿Hay una sesión de preguntas intermedia para validar decisiones (D-2: una sola región escribe; conciliación de pagos) antes de la entrega? | Reducir riesgo |

## Cómo enviarlas
* **Mensaje corto (si solo se puede uno):** P-1, P-3, P-4, P-6, P-16, P-30, P-41. Son las que bloquean diseño.
* **Segunda tanda (alcance y rúbrica):** P-2, P-9 a P-15, P-22, P-35.
* **Resto:** se pueden resolver con supuestos explícitos si el profesor no responde; cada supuesto debe quedar escrito en el documento.
