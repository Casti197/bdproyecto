# Pruebas de las transacciones

`prueba_concurrencia.py` ejecuta las transacciones de `concurrencia.md` y `alta_disponibilidad.md` §5 con las claves de Jacobo, contra **moto** (simulador de AWS en Python). `resultado.txt` es la salida de la última ejecución: **50 de 50 pasan** (2026-11-04).

```
pip install "moto[dynamodb]==5.1.0" boto3
python3 prueba_concurrencia.py
```

## Qué demuestra
* Las condiciones son válidas para la API y deciden lo que dice el diseño: escenario 1 (misma silla), todo o nada con varias sillas, `:skew` en el límite del vencimiento, escenarios 2a y 2b, confirmación repetida, máximo de 10 por usuario, los cuatro casos del modo desastre , el congelamiento de sillas en duda con la venta reabierta (respuesta 3b del profesor) y la lista de sillas en duda sacada del libro de pagos (D-2b).
* Las dos condiciones con aritmética de `modelo_datos.md` §7.1 no se pueden interpretar (en AWS dan `ValidationException` [D-01]).
* `verificar_invariantes()` detecta sillas con boletas de dos órdenes, pagos aprobados sin orden y órdenes `PAID` incompletas. Sirve para revisar el estado al final del simulacro de Miguel.

## Verificador para el simulacro de Miguel

`verificar_simulacro.py` es el mismo verificador, separado para correrlo **contra las tablas reales** al terminar el simulacro de conmutación (runbook 2b). Solo lee. Revisa 6 reglas: silla con boletas de dos órdenes; silla vendida sin dueño; pago aprobado sin orden; orden pagada incompleta; sillas que siguen congeladas por el incidente; intentos del libro sin resolver. Sale con código 1 si hay alguna violación y deja el detalle en `verificacion_simulacro.json`.

```
pip install boto3
python verificar_simulacro.py --region us-east-2 --evento 1234 --incidente INC-1
```

Se probó contra el simulador: con datos limpios no reporta violaciones, y con errores metidos a propósito detecta la silla con dos boletas y el pago aprobado sin orden.

## Qué no demuestra
* Concurrencia real: moto ejecuta una transacción a la vez y no es seguro con hilos. Tampoco produce `TransactionConflict` ni mide latencia.
* `ClientRequestToken`: moto lo ignora. Por eso se prueba la segunda defensa (`concurrencia.md` §3), que no depende del token.
* La replicación entre regiones.

## Hallazgo
Sin el token, reintentar un bloqueo que sí se aplicó devolvía "silla ocupada" al propio dueño. Se corrigió en `concurrencia.md` §3 y en el anexo, escenario 3b.
