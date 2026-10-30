# Respuesta de David a Jacobo: validación del modelo para concurrencia

**Autor:** David · **Para:** Jacobo · **Fecha:** 2026-10-29
**Responde a:** `jacobo/entrega_para_el_equipo.md` §1, §5 (D-1, D-2, D-5, D-9) y §8 (lista del viernes).
Las referencias `[R-xx]` son las de `jacobo/referencias.md`; las `[D-xx]` son mías y están al final de `david/concurrencia.md`.

---

## 1. Veredicto

**Las claves soportan los 4 escenarios. Apruebo congelar el modelo (D-1)**, con dos correcciones de sintaxis en las condiciones (§3) que no cambian ninguna clave.

| Escenario del anexo | ¿Lo soporta el modelo? | Elementos que uso |
|---|---|---|
| 1. Dos clientes, misma silla | Sí | Un ítem por silla en `bya_seats`; condición sobre `st`, `lx`; `CancellationReasons` por ítem [R-04] |
| 2. Bloqueo que vence mientras paga | Sí | `lx`, `lo`; confirmación con `st='L' AND lo=:oid`; `FULFILL_FAIL` + reembolso |
| 3. Falla a mitad de la compra | Sí | Atomicidad de `TransactWriteItems`; `ClientRequestToken`; `ORDER.st='PENDING'`; `gsi_pendientes` |
| 4. Conmutación del servidor | Sí dentro de la región; entre regiones depende de D-2 (§5) | Réplica en 3 zonas [R-01]; MREC en espera [R-17] |

Adopto tu condición de confirmación `st='L' AND lo=:oid` (sin exigir `lx` vigente). Es mejor que la que yo tenía: si el bloqueo venció pero nadie tomó la silla, la compra se confirma y no hay reembolso innecesario. La seguridad no cambia, porque para que otro tome la silla tiene que haber escrito `lo` con su propia orden.

## 2. Los valores que me pediste (D-9)

| Parámetro | Valor | Justificación |
|---|---|---|
| **`:skew`** | **2 s** | Margen para relojes desfasados entre servidores de aplicación. Una silla bloqueada solo se considera libre cuando `lx` pasó hace más de 2 s. Supone servidores sincronizados por NTP; si no se garantiza, subir a 5 s. Cuesta 2 s de silla ociosa por bloqueo vencido, irrelevante frente a 480 s |
| **Máximo de sillas por orden** | **10** (confirmo A-09) | El bloqueo usa 10 + 2 = 12 ítems y la confirmación ≈ 10 + 10 + 4 = 24, lejos de 100 ítems y 4 MB [R-04, R-07] |
| **Reintentos ante `TransactionConflict`** | *Backoff* exponencial con *jitter* completo: espera aleatoria entre 0 y `min(1000 ms, 50 ms × 2^intento)`; **máximo 3 reintentos**; mismo `ClientRequestToken` en cada reintento | Los SDK **no** reintentan esa excepción [R-04]. Después de 3 reintentos se responde "intenta de nuevo" al cliente; un conflicto repetido indica una silla muy disputada que probablemente ya se vendió |
| Reintentos ante *throttling* y errores 5xx | Los del SDK (con *backoff*) | El SDK los reintenta solo [D-03] |
| `ConditionalCheckFailed` | **Sin reintento** | La silla no está disponible; reintentar no cambia el resultado |

## 3. Dos correcciones de sintaxis (no cambian claves)

DynamoDB **no admite aritmética dentro de una `ConditionExpression`**: solo comparaciones, `BETWEEN`, `IN`, funciones y operadores lógicos. La suma y la resta solo existen en el `SET` de una `UpdateExpression` [D-01]. Dos condiciones de §7.1 de `modelo_datos.md` fallarían con `ValidationException`:

| Dónde | Como está | Corrección |
|---|---|---|
| Bloqueo de la silla | `st='L' AND lx < :now - :skew` | `st='L' AND lx < :vencido_antes_de`, con `:vencido_antes_de = now − skew` calculado en la aplicación |
| Límite por usuario | `attribute_not_exists(n) OR n + :k <= :max` | `attribute_not_exists(n) OR n <= :max_menos_k`, con `:max_menos_k = max − k` calculado en la aplicación |

El `SET n = if_not_exists(n, :cero) + :k` sí es válido y se queda igual. Para `lx` en el `SET`, prefiero pasar `:lx` ya calculado (`now + 480`) para que el mismo valor viaje a la orden y a las sillas.

## 4. Sobre el contador fragmentado (D-5)

**Apruebo N = 8 dentro de la transacción de confirmación.** Un detalle para el pseudocódigo: si una orden tiene sillas de **dos localidades**, la confirmación lleva **un `Update` por localidad** (cada uno en su fragmento `SH#<hash(oid) mod nsh>`). Como son ítems distintos no choca con la regla de "un ítem una sola vez por transacción" [R-04].

## 5. Sobre RPO 0 entre regiones (D-2)

**Estoy de acuerdo con el hallazgo y con la propuesta: una sola región escribe y, tras perder la región, modo seguro con conciliación contra la pasarela antes de reabrir.** Lo desarrollo en mi estudio de alta disponibilidad (semana 2) y en el escenario 4 del anexo. Lo voy a presentar así ante el jurado:

* **Fallo de zona:** RPO 0 real, sin conmutación que gestionar [R-01].
* **Pérdida de región:** RPO 0 **de pagos** por proceso (la pasarela es la fuente de verdad del dinero), no por réplica. Las sillas vendidas en los últimos segundos se reconstruyen desde los pagos aprobados antes de reabrir.

Falta conciliarlo con Miguel (sus runbooks) y llevar la pregunta P-4 al profesor. Lo coordino yo con Miguel.

## 6. Lo que agrego al modelo (sin claves nuevas)

| Agregado | Dónde | Para qué |
|---|---|---|
| Webhook de la pasarela → **SQS** → consumidor que ejecuta la confirmación | Aplicación | Segundo camino para confirmar si el servidor que cobró muere antes de confirmar. Idempotente porque la confirmación lo es |
| **Cola de mensajes fallidos (DLQ)** en esa cola, con alarma | SQS | Ningún aviso de pago se pierde en silencio [D-04] |
| Estado `UNKNOWN` en `PAY#nn` cuando la pasarela no responde | `bya_orders` (ya existe en tu modelo) | El reconciliador lo resuelve consultando la pasarela con la llave `<oid>#<nn>` |

Todo cabe en `gsi_pendientes`; no hace falta otro índice.

## 7. Lista del viernes

- [x] Las claves soportan los 4 escenarios.
- [x] `:skew`, máximo de sillas y reintentos fijados (§2).
- [ ] Jacobo aplica las dos correcciones de §3 en `modelo_datos.md` §7.1.
- [ ] David y Miguel concilian D-2.
