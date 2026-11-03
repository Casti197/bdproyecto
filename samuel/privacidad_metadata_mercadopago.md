# Privacidad de Datos en Metadata de Mercado Pago

Para cumplir con el principio de minimización de datos y evitar riesgos de fuga de información personal (*Data Leakage*), se establece una restricción estricta sobre el *payload* (metadata) enviado a la API de Mercado Pago para procesar el cobro:
* **Solo viajarán identificadores únicos (UUIDs/IDs):** `id_orden`, `id_usuario`, `id_evento` y un arreglo con los `id_silla`.
* **Queda estrictamente prohibido** incluir nombres, apellidos, números de documento de identidad (cédulas), correos electrónicos o teléfonos en los campos de metadata de la pasarela. La conciliación ante reclamos se hará cruzando el `id_orden` interno con el token devuelto por Mercado Pago, manteniendo la información personal de los compradores aislada y protegida dentro de la base de datos de BoletaYa.
