# Respuesta de Miguel a David: conciliar D-2 (RPO 0 al perder la región)

**Autor:** Miguel · **Para:** David · **Fecha:** 2026-10-30
**Responde a:** tu pregunta "¿cuadramos la decisión D-2?" y a `david/respuesta_a_jacobo.md` §5.
Los runbooks, la tabla de RTO y las fuentes están en `recuperacion_licenciamiento_carta.md`.

---

## 1. Postura

**Acepto D-2** (una sola región escribe; tras perder la región, modo seguro con conciliación contra la pasarela antes de reabrir), **con dos condiciones**. Sin ellas, el RPO 0 de pagos no se sostiene ante el jurado.

La razón de fondo está verificada en la documentación de AWS: las tablas globales con consistencia fuerte (MRSC) tienen RPO 0 pero **no admiten transacciones ni TTL**, y las de consistencia eventual (MREC) tienen RPO igual al retraso de replicación, "normalmente unos segundos" ([tablas globales](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html)). Como la compra usa `TransactWriteItems`, no hay otra salida que MREC.

## 2. Condición 1: cómo se sabe qué sillas compró un pago aprobado

La lista de sillas de la compra (`sil`) vive en el ítem `ORDER`. Si ese ítem no alcanzó a replicarse en el último segundo antes de la falla, la pasarela solo tiene la llave `<oid>#<nn>` y el monto. Con eso no se puede marcar las sillas como vendidas ni reembolsar con certeza.

Dos opciones:

| Opción | Qué es | Costo | Riesgo |
|---|---|---|---|
| A. Metadato en el cobro | Enviar a la pasarela el evento y las sillas como dato de referencia del cobro | Casi nulo | Depende de que la pasarela elegida lo permita |
| B. Libro de pagos en MRSC | Tabla pequeña (orden, sillas, monto, estado) escrita con `PutItem` condicional, sin transacción, antes de cobrar. MRSC exige exactamente tres regiones: dos réplicas y un testigo ([AWS](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/V2globaltables_HowItWorks.html)) | Escritura sincrónica entre regiones en el camino del pago, testigo, y el precio lo calcula Juan Pablo | Latencia no medida |

**Propuesta:** A como mecanismo principal y B como plan B si la pasarela no permite metadatos ni listar transacciones por fechas. Hay que elegir la pasarela y confirmarlo.

## 3. Condición 2: la conciliación de desastre no puede partir de `gsi_pendientes`

Tu reconciliador normal (cada minuto, pagos con más de 5 minutos) usa `gsi_pendientes`. Tras perder la región, ese índice en la réplica puede no tener las entradas de los últimos segundos, que son justo las que importan.

Por eso propongo dos modos:

- **Modo normal:** tu reconciliador, sin cambios.
- **Modo desastre:** parte de la lista de transacciones aprobadas de la pasarela por ventana de tiempo (desde unos minutos antes de la hora T de la falla) y busca cada una en la réplica con lectura fuerte. Pasos 4 y 5 del runbook 2b.

**Decidido el 3-nov-2026 (Miguel, Jacobo y David): se usa el listado por rango de fechas.** Falta confirmar que la pasarela concreta lo ofrezca.

## 4. Riesgo adicional: la región original que vuelve

AWS indica que, cuando una región se recupera, las replicaciones pendientes se reintentan y no hace falta ninguna acción ([diseño de tablas globales](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-global-table-design.html)). Los conflictos se resuelven por "última escritura gana" y no quedan en CloudWatch ni CloudTrail.

Mi lectura, que necesito que confirmes porque es tu escenario 4: la región original **no recibe tráfico ni escrituras** al volver, y sus ítems pendientes se comparan contra la pasarela antes de dejarlos converger. El regreso a us-east-1 se hace fuera de una preventa.

## 5. Lo que necesito de ti

1. **Que tu `alta_disponibilidad.md` coincida con la tabla de pasos del RTO** (congelar, cambiar tráfico, aplicación lista, conciliar, verificar contadores, reabrir): total de 4 a 8 minutos (4 a 11 en secuencia) tras el congelamiento de sillas en duda. Casi todos los tiempos son supuestos, y si tú tienes cifras publicadas, las cambio.
2. **Que confirmes el criterio de declaración** de la falla y quién lo declara.
3. **El RPO de los escaneos del estadio** (`estadio.md`), que en mi tabla figura como pendiente tuyo.
4. **Decidir con Jacobo** si se agrega el libro de pagos (opción B).

## 6. Lo que ya ajusté para coincidir con tu diseño

- El runbook 3 (pago sin registro) usa tu tabla de qué dice la pasarela y qué dice la base, y tus tiempos: el caso se resuelve solo en unos 6 minutos (5 de espera más 1 de ciclo del reconciliador).
- La confirmación del runbook 2b reutiliza tu confirmación idempotente. No se inventa otro camino.
- No toco tus claves ni tus condiciones.

## 7. Pregunta para el profesor (P-4)

Propongo enviarla así: *"En el Escenario con DynamoDB, 'pérdida total del sitio' ¿equivale a pérdida de una zona, de una región o del data center? Con transacciones, RPO 0 entre regiones no es alcanzable (las tablas con consistencia fuerte no las admiten). ¿Se acepta RPO 0 de pagos por conciliación con la pasarela como cumplimiento del requisito?"*
