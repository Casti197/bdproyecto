# Gestión de Cupos y Expiración de Bloqueos

Se confirma la regla de negocio para la gestión del límite de compra:
* Todo usuario tiene un límite máximo de **10 boletas por evento**. 
* Al iniciar el proceso de pago, el cupo correspondiente se descuenta temporalmente del usuario y las sillas pasan a estado `bloqueada` por una ventana estricta de 8 minutos. 
* Si el pago es rechazado o el tiempo expira sin confirmación, un proceso automatizado (ej. AWS EventBridge + Lambda o control por TTL con validación) libera las sillas a estado `disponible` y **devuelve inmediatamente el cupo al usuario**. Esto garantiza que el usuario pueda volver a intentar la compra sin que el sistema le bloquee injustamente su límite permitido de 10 boletas.
