# Pruebas de sandbox de Mercado Pago (D-11)

**Para qué:** confirmar lo que el modo desastre necesita de Mercado Pago (`pasarelas.md` §2, `alta_disponibilidad.md` §5.0). Hay que correrlo **en un computador del grupo**: el entorno donde se escribió el script no tiene salida a la API de Mercado Pago.

El script `sandbox_mercadopago.py` se probó contra un servidor que imita la API (13 de 13 casos). **Contra el sandbox de Mercado Pago se corrió el 2026-11-04 (corrida `60978573`): 11 de 13 pasan.** Falla la búsqueda por fechas; ver `pasarelas.md` §7.

## Qué comprueba

| # | Prueba | Si falla… |
|---|---|---|
| 1 | `metadata` guarda y devuelve las 10 sillas | Pasa en sandbox; aun así, D-2b activa `bya_ledger` porque la búsqueda por fecha falló |
| 2 | La misma `X-Idempotency-Key` devuelve el mismo pago | Hay que revisar `concurrencia.md` §4: el reintento podría cobrar dos veces |
| 3 | Otra llave crea otro pago | La llave no estaría funcionando como se espera |
| 4 | La búsqueda por fechas encuentra los pagos y trae `metadata` | Falló en sandbox; la lista sale de `bya_ledger`, pago por `gid` |
| 5 | Nombres reales de los estados (aprobado, pendiente, rechazado) | Se ajusta la regla de congelar y liberar |
| 6 | Largo que acepta `external_reference` (informativa) | Solo sirve para la idea de guardar ahí las sillas |

## Pasos

1. **Python 3.** Descargarlo de [python.org/downloads](https://www.python.org/downloads/) y, en la primera pantalla del instalador, marcar **"Add python.exe to PATH"**. Cerrar y abrir PowerShell, y comprobar con `python --version` (o `py --version`).
2. **Aplicación.** Entrar al [Panel de integración](https://www.mercadopago.com.co/developers/panel/app) con una cuenta de Mercado Pago y elegir **Crear manualmente**. Si el formulario pregunta qué se va a integrar, elegir pagos en línea con **Checkout API** (pago con tarjeta desde nuestra propia página). Al crearla, Mercado Pago genera solas las credenciales de prueba.
3. **Credenciales de prueba.** Dentro de la aplicación, elegir **Prueba** en el selector de entorno de arriba y abrir **Credenciales** (en el menú lateral o en el bloque de Inicio). Copiar la **Public Key** y el **Access Token**. El Access Token de prueba **empieza por `APP_USR`**, igual que el de producción: por eso hay que fijarse en que el selector diga **Prueba**. No activar el ambiente de producción.
4. **Cuenta compradora de prueba.** En la aplicación, **Cuentas de prueba** → crear una de tipo **Comprador**, de **Colombia** (debe ser del mismo país que el vendedor). Anotar su email.
5. **Correr** desde la carpeta `david\pruebas`:

   ```powershell
   cd "D:\Bases de datos\Proyecto final\david\pruebas"
   $env:MP_ACCESS_TOKEN    = "<access token de prueba>"
   $env:MP_PUBLIC_KEY      = "<public key de prueba>"
   $env:MP_PAYER_EMAIL     = "<email de la cuenta Comprador de prueba>"
   $env:MP_CONFIRMO_PRUEBA = "1"
   python sandbox_mercadopago.py
   ```

6. **Compartir** `resultados_sandbox.json`, que queda en la misma carpeta. No subir las credenciales al repositorio.

## Seguridad

* **Doble freno.** El script corre si la credencial empieza por `TEST-`, si su usuario tiene la etiqueta `test_user`, o si se confirma con `MP_CONFIRMO_PRUEBA = "1"` que se copió del entorno Prueba. En el último caso, además, revisa cada token de tarjeta: si Mercado Pago lo marca como real (`live_mode = true`), se detiene.
* Usa la tarjeta de prueba Mastercard de Colombia (5254 1336 7440 3564, CVV 123, vencimiento 11/30) con los titulares APRO (aprobado), CONT (pendiente) y OTHE (rechazado), y el documento 123456789, como indica Mercado Pago. No es una tarjeta real.
* Crea unos 9 pagos de prueba de COP 50.000. No mueven dinero real.

## Dudas que quedan abiertas en la documentación

* El endpoint `/v1/card_tokens` que usa el script para tokenizar la tarjeta en el servidor no aparece en la referencia de pagos. Si responde con error, la tarjeta se tokeniza desde una página con el SDK de JavaScript de Mercado Pago. Avisen si pasa.
* La documentación no detalla los campos del formulario de creación de la aplicación; el paso 2 da la elección esperada. Si aparece algo distinto, anotar qué se eligió.
