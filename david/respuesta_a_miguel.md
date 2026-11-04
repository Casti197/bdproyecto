# Respuesta de David a Miguel (modo desastre D-2)

> **Aviso (2026-11-04):** tras las respuestas 3 y 6 del profesor, ya no se cierra toda la venta hasta conciliar. Se congelan solo las sillas en duda y se reabre antes (`alta_disponibilidad.md` §3.3 y §5.0). Lo demás de este documento sigue vigente.

**Fecha:** 2026-11-03 · Detalle técnico en [`alta_disponibilidad.md`](alta_disponibilidad.md) §3 a §6.

## Qué acepto
1. **Condición 1 (sillas de un pago aprobado):** sí, con metadatos en el cobro (evento, usuario, sillas). Sin ellos el pago se reembolsa.
2. **Condición 2 (no usar `gsi_pendientes`):** sí. Con D-2b, congelar desde `bya_ledger` por ventana `T − W`; consultar el estado de cada pago por `gid`.
3. **Región original al volver:** no recibe tráfico ni escrituras; se concilia otra vez tras la convergencia (§6).

## Qué cambia en tu runbook 2b
| Tema | Cambio |
|---|---|
| Paso 4 | La confirmación normal **no sirve** (la orden o la silla pueden faltar). Usa `confirmarDesastre` (§5.2): lee, decide y escribe solo lo que falta |
| "Si está `PAID`, no hacer nada" | Una réplica puede mostrar una compra a medias (las transacciones no se replican como unidad [D-07]). Las órdenes `PAID` de la ventana **también** pasan por `confirmarDesastre`, que no hace nada si está completa |
| Contadores | De "verificar" a **reconstruir** contando sillas `S` (§5.4) |
| Orden de pasos | Tráfico a us-east-2 primero con admisión cerrada; reapertura al final (§3.3) |
| Pagos tardíos | Los aprobados después de reabrir cuyo origen es anterior a la declaración usan `confirmarDesastre` (§5.5) |

## Observaciones
* Cambiar el tráfico en 1 a 3 min es el paso más optimista: AWS dice "varios minutos" solo con DNS y "segundos a pocos minutos" con ARC [D-10]. Vale si está preparado y con TTL de 60 s.
* Declaración: alarma compuesta (`SystemErrors`, `ReplicationLatency`, 5xx) más confirmación humana (§3.2). La detección queda fuera del RTO pero se reporta.
* Las réplicas necesitan pre-calentamiento; se lo pido a Jacobo y a Juan Pablo.
* Mercado Pago elegida; sandbox verificó metadata/idempotencia y mostró fallo de listado por fechas; D-2b usa el ledger y consulta pagos por `gid`.
