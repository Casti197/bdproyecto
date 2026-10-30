# Fichas de decisión de Miguel (para el registro de Samuel)

**Autor:** Miguel · **Para:** Samuel · **Fecha:** 2026-10-30
Las mismas fichas que están en `recuperacion_licenciamiento_carta.md`, en un archivo aparte para pegar en el registro. El detalle y las fuentes están en ese documento.

---

## Ficha R-1: cómo lograr RPO 0 de pagos si se pierde la región

| Campo | Contenido |
|---|---|
| Contexto | El enunciado exige RPO 0 para pagos. La compra usa transacciones, y las tablas globales con consistencia fuerte entre regiones (MRSC) no las admiten |
| Alternativas | (a) Tablas globales con consistencia eventual (MREC) y conciliación contra la pasarela. (b) MRSC para toda la compra: imposible por las transacciones. (c) MREC más un libro de pagos en MRSC. (d) Aceptar un RPO mayor que 0 |
| Criterio | RPO 0 del dinero, sin romper la atomicidad de la compra, a costo razonable |
| Elección | (a), con las sillas enviadas como metadato del cobro; (c) como plan B si la pasarela no permite metadatos ni listar transacciones por fechas |
| Sacrificio | La base queda con RPO de segundos; el RTO incluye de 3 a 5 minutos de conciliación; la recuperación depende de capacidades de la pasarela que aún no se han confirmado |
| Responsable | Miguel, con David (D-2) |
| Estado | Propuesta; falta la confirmación de David y elegir la pasarela |

## Ficha R-2: respaldo inmutable

| Campo | Contenido |
|---|---|
| Contexto | PITR protege de errores, pero no de quien tenga acceso a la cuenta y borre tablas y respaldos. El enunciado pide una copia inmutable o desconectada |
| Alternativas | (a) Solo PITR. (b) PITR más AWS Backup en la misma cuenta y región. (c) PITR más AWS Backup con copia a otra región y cuenta, en una bóveda con Vault Lock |
| Criterio | Sobrevivir al borrado malicioso o por error de la cuenta principal, con un costo que quepa en el tope del año 1 |
| Elección | (c), con Vault Lock probado antes en modo gobernanza |
| Sacrificio | Costo de almacenamiento comprometido hasta que venza la retención; el modo cumplimiento es irreversible; la copia diaria deja hasta 24 h de datos en riesgo ante una cuenta comprometida; hay que operar dos cuentas y dos regiones |
| Responsable | Miguel; costo de Juan Pablo; legal de Samuel |
| Estado | Propuesta; falta que Juan Pablo confirme que cabe en el presupuesto |
