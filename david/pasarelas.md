# Pasarelas de pago: comparación para la decisión D-11

> **Decisión (2026-11-03):** Miguel, Jacobo y David aceptan **Mercado Pago**.
>
> **Sandbox (2026-11-04, §7):** `metadata` e idempotencia **confirmadas**. La **búsqueda por fechas no devolvió nada** en el sandbox, ni siquiera 14 minutos después, y la aplicación no tiene credenciales `APP_USR` para repetir la prueba, así que no está confirmada. Sin ella no se puede armar la lista de sillas en duda: **D-2b aprobada por el grupo el 2026-11-04:** la lista sale de `bya_ledger`, que se escribe antes de cobrar (`alta_disponibilidad.md` §5.0).

**Autor:** David · **Fecha:** 2026-11-03 · **Para:** Miguel y Jacobo (decisión D-11)
**Qué necesitamos** (`alta_disponibilidad.md` §4, `miguel/` runbook 2b):

1. **Idempotencia:** que reintentar un cobro no cobre dos veces (`concurrencia.md` §4).
2. **Metadatos en el cobro:** guardar evento, usuario y sillas para reconstruir la compra si la región se pierde.
3. **Listar cobros por rango de fechas:** el punto de partida de la conciliación de desastre (ya decidido usarlo el 3-nov).
4. **Webhook firmado** con reintentos (no es requisito, pero reduce el trabajo del reconciliador).

Todo lo de abajo sale de la documentación pública consultada hoy. **No se probó en ningún sandbox** y no comparé tarifas.

## 1. Resultado

| Pasarela | 1. Idempotencia | 2. Metadatos | 3. Listado por fechas | 4. Webhook | Veredicto |
|---|---|---|---|---|---|
| **Mercado Pago** | ✅ Encabezado `X-Idempotency-Key` **obligatorio** [P-01] | 🟡 Los campos `metadata` y `external_reference` aparecen en la respuesta del pago, pero la página no los describe [P-02] | ✅ `GET /v1/payments/search` con `begin_date`, `end_date` y `range=date_created`; también filtra por `external_reference` [P-03] | ✅ Firma `x-signature`; reintenta cada 15 min y sigue después del tercer intento [P-04] | **Cumple las tres**, con la duda de `metadata` |
| **Wompi** | 🟡 No hay llave de idempotencia; la `reference` "debe ser única por transacción" y repetirla da error 422 "Duplicate reference" [P-05]. Sirve para no cobrar dos veces, pero el reintento recibe un error en vez del cobro original | ❌ No hay campo de metadatos; solo `customer_data` (nombre, teléfono, dirección) [P-05] | 🟡 La documentación oficial solo muestra consultar **una** transacción por id [P-05]. Un SDK de terceros lista con `from_date`, `until_date` y llave privada [P-06], pero no está en la página oficial | ✅ Evento `transaction.updated` con firma SHA256; solo 3 reintentos (a los 30 min, 3 h y 24 h) [P-07] | Falla en metadatos; listado sin confirmar |
| **PayU Latam** | 🟡 `referenceCode` es "el identificador de la orden en tu sistema"; la página no dice si debe ser único ni qué pasa al repetirlo [P-08] | 🟡 `extraParameters` existe dentro de la transacción [P-08, P-09] | ❌ La API de consultas solo busca por id de orden, id de transacción o `referenceCode`; no por fechas [P-09] | ✅ `notifyUrl` de confirmación [P-08] | Falla en listado por fechas |
| **ePayco** | ❓ | ❓ (existe un objeto `extras` en las respuestas, según un SDK de terceros [P-10]) | ❓ | ❓ | **No pude abrir su documentación oficial** |
| **Stripe** | — | — | — | — | No está disponible para empresas en Colombia [P-11] |

✅ documentado · 🟡 parcial o sin describir · ❌ no documentado · ❓ sin verificar

## 2. Recomendación (aceptada)

**Mercado Pago como opción principal**, con dos condiciones antes de decidir:

1. **Confirmar en el sandbox que `metadata` guarda y devuelve un objeto propio** (por ejemplo `{"eid": "1234", "uid": "ana", "sillas": ["07|12|24"]}`) y que la búsqueda por fechas lo devuelve. La documentación solo lo muestra en un ejemplo.
2. **Confirmar que el encabezado de idempotencia devuelve el mismo pago** al repetir la llamada (no un error). Usaríamos `<oid>#<nn>` como llave, igual que en `concurrencia.md` §4.

**Si no se cumple la 1:** se activa el libro de pagos de Jacobo (`bya_ledger` en MRSC) o, para un pago de desastre sin sillas conocidas, se reembolsa.

**Wompi** solo vale con el libro de pagos, porque no tiene metadatos. **PayU** no permite iniciar la conciliación desde un listado por fechas, que es lo que decidimos.

## 3. Idea para no depender de los metadatos (sin verificar)

Las sillas de una orden caben en un texto corto: hasta 10 sillas como `07|12|24` son unos 100 caracteres. Si la referencia del cobro (`external_reference` en Mercado Pago, `reference` en Wompi) admite esa longitud, se puede guardar ahí `oid` y las sillas, y la conciliación las lee del listado sin necesitar `metadata`. **Falta verificar el largo máximo de esos campos** en cada pasarela.

## 4. Qué cambia en nuestros documentos según la pasarela

| Si se elige… | `concurrencia.md` §4 | `alta_disponibilidad.md` §5 | Jacobo |
|---|---|---|---|
| Mercado Pago (elegida) | `X-Idempotency-Key = <oid>#<nn>`; `metadata` con eid, uid y sillas; **antes** de cobrar se escribe el intento en `bya_ledger` | La lista de sillas en duda sale de `bya_ledger`; cada pago se consulta por su `id` (la búsqueda por fechas no funcionó en el sandbox) | **Activar `bya_ledger`** (D-2b) con clave listable por minuto |
| Wompi | `reference = <oid>#<nn>`; un 422 "Duplicate reference" se trata como "ya se envió" y se consulta el estado | Sin metadatos: activar `bya_ledger` o reembolsar | Activar `bya_ledger` |

## 5. Pendientes

* **Miguel, Jacobo y David:** crear una cuenta de prueba en Mercado Pago y comprobar los dos puntos de §2 (es poco trabajo y cierra D-11).
* **Juan Pablo:** comparar las comisiones por transacción de Mercado Pago y Wompi para Colombia (no las consulté).
* **Samuel:** revisar qué datos personales viajan en `metadata` (se propone solo identificadores, no nombres ni documentos).

## 7. Resultados del sandbox (2026-11-04)

Corrida `60978573`, con credenciales `TEST-` de una aplicación de **API de Payments**, ejecutada por David con `pruebas/sandbox_mercadopago.py`. Archivo completo: `pruebas/resultados_sandbox.json`. **11 de 13 pasan.**

| Qué necesitábamos | Resultado | Efecto en el diseño |
|---|---|---|
| `metadata` guarda y devuelve las sillas | **Confirmado.** Las 10 sillas, el evento y el usuario vuelven iguales (cambia el orden de las claves, no los valores) | La compra se puede reconstruir desde Mercado Pago (`alta_disponibilidad.md` §5.2) |
| La misma `X-Idempotency-Key` devuelve el mismo pago | **Confirmado.** El pago `1328620210` vuelve igual; la primera vez responde HTTP 201 y la repetición HTTP 200 | `concurrencia.md` §4 queda como está: un reintento no cobra dos veces |
| Otra llave crea otro pago | **Confirmado** | La llave es la que decide |
| Nombres de estados | **Confirmados:** aprobado `approved`; pendiente `in_process` (detalle `pending_contingency`); rechazado `rejected` (detalle `cc_rejected_other_reason`) | La regla de congelar y liberar usa `approved`, `in_process` y `rejected` (`alta_disponibilidad.md` §5.0) |
| Largo de `external_reference` | Acepta 64 y 128 caracteres; con 256 responde HTTP 400, "too much large" | La idea de §3 (guardar ahí las sillas) no hace falta, porque `metadata` funciona |
| **Búsqueda por rango de fechas** | **Falla en el sandbox.** `/v1/payments/search` responde HTTP 200 pero sin resultados, también sin filtros, por estado, por vendedor o por `external_reference`. Solo funciona filtrando por el `id` del pago, y en ese caso sí trae la `metadata` | **No queda confirmado** que en producción se pueda listar por fechas. De esa búsqueda sale la lista de sillas en duda |

**Pasos para cerrar la búsqueda:**
1. ~~Repetir la búsqueda pasados unos minutos, por si el índice tarda.~~ **Hecho.** A las 11:51, unos 14 minutos después de crear los pagos, la búsqueda por fechas y la búsqueda sin filtros siguen devolviendo 0 resultados. Se descarta un retraso del índice.
2. ~~Repetir con las credenciales `APP_USR` del entorno Prueba.~~ **No se pudo:** la aplicación no tiene credenciales `APP_USR`, solo las `TEST-`.
3. **Aprobado por el grupo el 2026-11-04 (D-2b):** activar `bya_ledger` como fuente de la lista de sillas en duda (`alta_disponibilidad.md` §5.0); guardar clave listable por minuto y `gid` al llegar a CHARGED. La búsqueda por fechas no se usa.

## 6. Referencias

Consultadas el 2026-11-03.

| ID | Fuente | Qué respalda |
|---|---|---|
| P-01 | [Mercado Pago Colombia: envío del pago (Payment Brick)](https://mercadopago.com.co/developers/en/docs/checkout-bricks/payment-brick/payment-submission/other-payment-methods) | "Es obligatorio enviar el atributo `X-Idempotency-Key`" |
| P-02 | [Mercado Pago: referencia de la API de pagos](https://www.mercadopago.com/developers/en/reference/payments/_payments_id/put) | `metadata` y `external_reference` en la respuesta del pago (sin descripción) |
| P-03 | [Mercado Pago Colombia: gestión de pagos](https://www.mercadopago.com.co/developers/en/docs/subscriptions/additional-content/payment-management) | `/v1/payments/search` con `begin_date`, `end_date`, `range` y `external_reference` |
| P-04 | [Mercado Pago Colombia: webhooks](https://www.mercadopago.com.co/developers/en/docs/your-integrations/notifications/webhooks) | Firma `x-signature`; espera 22 s; reintentos cada 15 min |
| P-05 | [Wompi Colombia: transacciones](https://docs.wompi.co/en/docs/colombia/transacciones/) | `reference` única, error 422 "Duplicate reference"; `customer_data`; consulta de una transacción por id |
| P-06 | [SDK de terceros @pulgueta/wompi (no oficial)](https://cdn.jsdelivr.net/npm/@pulgueta/wompi@3.2.0/skills/wompi-transactions/SKILL.md) | Listado con `from_date`, `until_date`, `page_size` ≤ 200 y llave privada |
| P-07 | [Wompi Colombia: eventos](https://docs.wompi.co/en/docs/colombia/eventos/) | `transaction.updated`, firma SHA256, 3 reintentos en 24 h |
| P-08 | [PayU Latam: Payments API Colombia](https://developers-payu-latam.github.io/latam/en/docs/integrations/api-integration/payments-api-colombia.html) | `referenceCode`, `extraParameters`, `notifyUrl` |
| P-09 | [PayU Latam: Queries API](https://developers-payu-latam.github.io/latam/en/docs/integrations/api-integration/queries-api.html) | Consultas solo por id de orden, id de transacción o `referenceCode` |
| P-10 | [SDK de terceros epayco_dart (no oficial)](https://pub.dev/documentation/epayco_dart/latest/data_models_api_responses_tc_transaction/TransactionData-class.html) | Objeto `extras` en las respuestas de ePayco |
| P-11 | [Stripe: países disponibles](https://stripe.com/global) | Colombia no aparece en la lista |
