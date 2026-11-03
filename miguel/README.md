# Parte de Miguel — BoletaYa SAS (Grupo 5, DynamoDB en AWS)

**Autor:** Miguel Medina · **Fecha:** 2026-10-30
Cubre: 5.5 Recuperación, 5.3 Versiones y licenciamiento, sitio alterno del Escenario B, plan de 72 horas de la carta de evento, y revisión cruzada de Jacobo.

## Qué leer según quién seas

| Tú eres | Lee | Por qué |
|---|---|---|
| Todos | `recuperacion_licenciamiento_carta.md` | Documento principal: respaldo, RPO/RTO por componente, 3 runbooks, plan de pruebas, licenciamiento, Escenario B, carta de 72 horas, fuentes |
| David | `respuesta_a_david.md` | Respuesta sobre D-2 (RPO 0 al perder la región): acepto con 2 condiciones |
| Jacobo | `revision_de_jacobo.md` | Revisión cruzada: 7 hallazgos, el principal sobre CloudFront y `POST` |
| Juan Pablo | `lista_componentes_para_juan_pablo.md` | Componentes de respaldo y recuperación a costear, con volúmenes por tabla y año; sin precios |
| Samuel | `fichas_decision_miguel.md` | Fichas R-1 y R-2 para el registro de decisiones |
| Chat del grupo | `mensaje_para_el_grupo.md` | Mensaje corto con lo que necesito de cada uno |

## Resultado en una línea

Tres capas: DynamoDB replica en 3 zonas (falla de zona, RPO 0); PITR de 35 días y AWS Backup con copia inmutable en otra región y cuenta (errores humanos, corrupción, ransomware); región alterna us-east-2 con modo seguro y conciliación contra la pasarela (pérdida de región). RTO desde la declaración de la falla: **7 a 13 minutos** si se pierde la región (7 a 16 sin traslape de pasos), **3 a 11** si se pierde el data center de Bogotá.

## Qué está verificado y qué no

**Verificado en documentación oficial de AWS** (20 páginas, en la sección Fuentes del documento principal): límites de PITR, restauración, AWS Backup, Vault Lock, Object Lock, replicación S3 con RTC, tablas globales (MREC y MRSC), failover de CloudFront, políticas de fin de vida de SDK y runtimes de Lambda.

**Reproducido:** el script de capacidad de Jacobo da exactamente su `salida_modelo.md`. Los volúmenes por tabla de la lista para Juan Pablo suman sus totales.

**Supuestos, no datos** (están marcados así en el documento):
- Los tiempos de cada paso de los runbooks. AWS no publica tiempos de restauración ni de conmutación de una región.
- Que la pasarela de pagos permita enviar metadatos en el cobro. El listado de transacciones por rango de fechas **ya se decidió usar** (3-nov-2026, Miguel, Jacobo y David), pero falta confirmarlo con la pasarela concreta, que no está elegida.
- Que AWS Backup no consuma capacidad de las tablas (la documentación consultada no lo dice; por eso hay reglas de congelamiento y horario).
- Si AWS Backup factura incrementalmente los puntos de DynamoDB (la lista de Juan Pablo da una cota superior).
- Las horas de DBA (68 al año) y de actualización (104 en 5 años): son estimaciones mías.
- Fechas de fin de vida de Valkey: AWS no las publica.

**No probado:** nada se ejecutó en AWS real (el proyecto es de diseño). Las restauraciones y simulacros están descritos en el plan de pruebas, no hechos.

## Pendientes abiertos

| Quién | Qué |
|---|---|
| David | Confirmar D-2 con las dos condiciones; alinear `alta_disponibilidad.md` con la tabla de RTO; RPO de los escaneos del estadio |
| Jacobo | Corregir la conmutación de CloudFront en `arquitectura.md` y el diagrama del B; guardar la cola virtual en AWS; decidir el libro de pagos en MRSC; fijar el pre-calentamiento |
| Juan Pablo | Costear la lista; avisar si el año 1 no cabe en COP 280.000.000 |
| Samuel | Plazo legal de retención; confirmar que los respaldos no guardan números de tarjeta |
| Profesor (P-1, P-4) | Qué significa Escenario B con DynamoDB; qué es "pérdida total del sitio" |
| Miguel, David, Jacobo | Fijar la pasarela: listado por fechas decidido; faltan llave de idempotencia y metadatos en el cobro |

## Cifras de costo que entrego

- DBA: 68 horas al año × COP 120.000 = **COP 8.160.000 al año** (al TCO, no al año 1).
- Actualizaciones: 2 migraciones de runtime × 40 h + 1 SDK mayor × 24 h = 104 h → **COP 12.480.000 en 5 años**; más una migración de PostgreSQL del estadio (24 h, **COP 2.880.000**) y Ubuntu Pro de 14 equipos (precio sin verificar).
- Parámetros usados: TRM 4.000, IVA 19 %, administración COP 120.000/hora.
