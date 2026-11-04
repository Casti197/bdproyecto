# Pruebas de sandbox de Mercado Pago (D-11)

**Para qué:** confirmar lo que el modo desastre necesita de Mercado Pago (`pasarelas.md` §2, `alta_disponibilidad.md` §5.0). Hay que correrlo **en un computador del grupo**: el entorno donde se escribió el script no tiene salida a la API de Mercado Pago.

El script `sandbox_mercadopago.py` se probó contra un servidor que imita la API (13 de 13 casos). **Contra Mercado Pago real todavía no se ha corrido.**

## Qué comprueba

| # | Prueba | Si falla… |
|---|---|---|
| 1 | `metadata` guarda y devuelve las 10 sillas | Se activa el libro de pagos de Jacobo (`bya_ledger`) o se reembolsa en desastre |
| 2 | La misma `X-Idempotency-Key` devuelve el mismo pago | Hay que revisar `concurrencia.md` §4: el reintento podría cobrar dos veces |
| 3 | Otra llave crea otro pago | La llave no estaría funcionando como se espera |
| 4 | La búsqueda por fechas encuentra los pagos y trae `metadata` | No se puede armar la lista de sillas en duda: la venta quedaría cerrada en desastre |
| 5 | Nombres reales de los estados (aprobado, pendiente, rechazado) | Se ajusta la regla de congelar y liberar |
| 6 | Largo que acepta `external_reference` (informativa) | Solo sirve para la idea de guardar ahí las sillas |

## Pasos

1. **Python 3.** En PowerShell: `python --version`. Si no está: `winget install Python.Python.3.12`.
2. **Aplicación de prueba.** Entrar a [Mercado Pago Developers Colombia](https://www.mercadopago.com.co/developers/es) → *Tus integraciones* → crear una aplicación de pagos en línea (Checkout API).
3. **Cuentas de prueba.** En la aplicación → *Cuentas de prueba* → crear una **Vendedor** y una **Comprador**, las dos de **Colombia** (deben ser del mismo país). Anotar el email del comprador.
4. **Credenciales de prueba.** *Credenciales* de la aplicación: el **Access Token** y la **Public Key** de prueba. Si no aparecen credenciales `TEST-`, iniciar sesión con la cuenta Vendedor de prueba y usar las credenciales de una aplicación creada con ella.
5. **Correr** desde la carpeta `david\pruebas`:

   ```powershell
   $env:MP_ACCESS_TOKEN = "<access token de prueba>"
   $env:MP_PUBLIC_KEY   = "<public key de prueba>"
   $env:MP_PAYER_EMAIL  = "<email de la cuenta Comprador de prueba>"
   python sandbox_mercadopago.py
   ```

6. **Compartir** `resultados_sandbox.json`, que queda en la misma carpeta. No subir las credenciales al repositorio.

## Seguridad

* **Freno incluido:** si la credencial no empieza por `TEST-` ni pertenece a un usuario con la etiqueta `test_user`, el script se detiene sin hacer nada. Así no se puede cobrar con una cuenta real por error.
* Usa la tarjeta de prueba Mastercard de Colombia (5254 1336 7440 3564, CVV 123, vencimiento 11/30) con los titulares APRO (aprobado), CONT (pendiente) y OTHE (rechazado), y el documento 123456789, como indica Mercado Pago.
* Crea unos 9 pagos de prueba de COP 50.000. No mueven dinero real.

## Dudas que quedan abiertas en la documentación

* El endpoint `/v1/card_tokens` que usa el script para tokenizar la tarjeta en el servidor no aparece en la referencia de pagos. Si responde con error, la tarjeta se tokeniza desde una página con el SDK de JavaScript de Mercado Pago. Avisen si pasa.
* La página de cuentas de prueba no explica cómo se obtienen las credenciales; el paso 4 cubre las dos formas habituales.
