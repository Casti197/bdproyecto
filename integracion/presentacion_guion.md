# Presentación — guion integrado de 20 diapositivas

**Estado:** guion final; la preparación de la sustentación está en [`SUSTENTACION.md`](../SUSTENTACION.md). Sustentación: 30 minutos + 10 de preguntas, unos **1,5 minutos por diapositiva**.
**Quién presenta:** se propone que cada quien presente lo que no es suyo en al menos una diapositiva, porque el jurado puede preguntarle a cualquiera.

| # | Título | Mensaje (una frase) | Contenido | Fuente | Presenta (propuesta) |
|---|---|---|---|---|---|
| 1 | BoletaYa con DynamoDB en AWS | Diseñamos la base para pasar de 100 a 3.000 ventas por minuto sin doble venta ni pagos perdidos | Grupo, motor y nube asignados | Enunciado | Samuel |
| 2 | El problema en números | El pico manda: 24.000 órdenes en 20 minutos y 250.000 personas mirando el mapa | Carga normal frente a preventa | `jacobo/capacidad_y_volumetria.md` | Jacobo |
| 3 | Dos escenarios | A todo en AWS; B híbrido, porque DynamoDB no se instala *on premise* | Diagrama simple de A y B | `jacobo/arquitectura.md`; resp. 1 y 2 del profesor | Miguel |
| 4 | Ocho tablas, no una | Cada tipo de dato tiene su retención, su carga y sus permisos | Lista de tablas y la clave de sillas | `jacobo/modelo_datos.md` §2–§4; F-03, F-04 | David |
| 5 | Sillas sin cuello de botella | Ninguna partición pasa de 1.000 escrituras/s gracias a la clave por fila | ≈ 900 claves; ≈ 2,5 WRU/s por clave | `jacobo/resumen_sustentacion.md` P1 | Jacobo |
| 6 | El contador exacto | Se vende y se cuenta en la misma transacción, repartido en 8 fragmentos | Esquema del contador | F-05 | Juan Pablo |
| 7 | Cero doble venta | Una transacción todo o nada con condición sobre cada silla | Línea de tiempo: dos clientes, la misma silla | `david/anexo_concurrencia.md` escenario 1 | David |
| 8 | Bloqueo de 8 minutos y pagos a medias | La silla vencida se libera en la condición; el pago se reintenta sin cobrar dos veces | Escenarios 2 y 3 del anexo; idempotencia | `david/concurrencia.md` §4–§6 | Samuel |
| 9 | El mapa no toca la base | 17,2 veces la cuota de una tabla si fuera directo; con CDN, ≈ 450 RRU/s | Antes y después | F-08 | Miguel |
| 10 | Capacidad sin pagar el pico todo el año | On-demand + pre-calentamiento: USD 83 frente a 63.176 del provisionado fijo | Barras de las tres opciones (año 1) | F-07 | Juan Pablo |
| 11 | Región y latencia | us-east-1: ≈ 77 ms desde Bogotá frente a ≈ 112 ms de São Paulo | Mapa y tabla | F-02 | Jacobo |
| 12 | Si cae una región | Una sola región escribe; se congelan solo las sillas en duda y se reabre en 4 a 11 minutos (estimado) | Pasos del RTO | `david/alta_disponibilidad.md` §3.3; F-09, F-10 | Miguel |
| 13 | Respaldos que no frenan la preventa | PITR, AWS Backup y copia inmutable en otra cuenta | Tres capas de recuperación | `miguel/recuperacion_licenciamiento_carta.md` §5.5; F-12 | David |
| 14 | El estadio sin internet | Una puerta, un nodo, una autoridad: 4 horas aislado sin doble ingreso | Diagrama de puerta | `david/estadio.md`; F-13 | Juan Pablo |
| 15 | Seguridad y cumplimiento | Roles/KMS, PCI con token sujeto al flujo real, Ley 1581 y retención tributaria; quedan validación contractual y jurídica | — | Samuel | Jacobo |
| 16 | Versiones y licencias | DynamoDB no tiene versión ni licencia; lo que rodea a la base sí, y está costeado | Tabla de fin de soporte | `miguel/recuperacion_licenciamiento_carta.md` §5.3 | Samuel |
| 17 | Costos por escenario | A COP 191,1 M; B COP 289,6 M en año 1; B solo cabe usando la reserva del 10 % | Barras frente al tope | Juan Pablo | Miguel |
| 18 | Sensibilidad y TCO | Sensibilidad a doble de preventas/cola y TCO a 5 años, separados del subtotal de caja | Tabla | `juanpablo/sensibilidad_y_tco.md` | David |
| 19 | A contra B | Comparación en latencia estimada, conectividad, costo incompleto, riesgo, RPO/RTO y crecimiento | Tabla comparativa | Samuel | Juan Pablo |
| 20 | Recomendación | A recomendado: 469,7 M de caja a 5 años frente a 697,1 M; B consume la reserva en el año 1 | Una frase y tres razones | Samuel | Todos |

**Diapositiva de reserva (no cuenta en las 20, para preguntas):** contradicciones del enunciado (`jacobo/README.md` §5) y lo que no se pudo verificar (`jacobo/README.md` §6).
