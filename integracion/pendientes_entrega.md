# Estado de entrega — 4 de noviembre de 2026

Este archivo separa entregables terminados de dependencias externas que aún impiden certificar costos o cerrar la respuesta del evento. Los huecos sin precio siguen identificados como tales; las estimaciones están rotuladas.

## Cerrado en el repositorio

- [x] Pull de `main` integrado: PR de `integracion/`, correcciones de David y cambios de los responsables ya presentes en el remoto.
- [x] David: verificador entregado en `david/pruebas/verificar_simulacro.py`; pruebas registradas 50/50 en `david/pruebas/resultado.txt`.
- [x] Miguel: Runbook 2b usa `bya_ledger` como fuente de sillas en duda; carta considera cuatro horas aislado; Escenario A no depende de aplicación en Bogotá.
- [x] Jacobo: dos páginas de DynamoDB on premise/API compatible, Escenario A todo en AWS para la ruta de compra, estadio local en A y B, Local Zone/ausencia de DynamoDB regional colombiana y latencia con límites de medición.
- [x] Seguridad y cumplimiento: roles/mínimo privilegio, cifrado/KMS, tokenización, PCI sujeto a alcance del adquirente, auditoría, antibots, Ley 1581 y conservación tributaria añadidos a §8 de la propuesta.
- [x] Recomendación registrada: A; torniquetes F-14 opción 2; cola virtual propuesta como compra condicionada a SLA y precio.
- [x] Costos: estadio común cargado a ambos escenarios, torniquetes propios fuera del subtotal (opción 2), aplicación/API/Lambda/ElastiCache y unidades del ledger MRSC agregados; saldo corregido a presupuesto menos subtotal.

## Dependencias pendientes, declaradas

1. Cotizaciones de lectores/controlador QR, switches core, UPS, router/enlaces del estadio, Direct Connect/cross-connect/partner, VPN/enlace alterno, cola virtual y soporte/licencias. Responsable: equipo de compras; validar con Juan Pablo.
2. Validar throughput, egress, backup inmutable, comisión de pago, métricas Lambda y precios finales en AWS Pricing Calculator. Las cifras del Excel de API/Lambda/ElastiCache son estimaciones; no cotización. Responsable: Juan Pablo.
3. Inventario y prueba de compatibilidad de torniquetes existentes en el estadio. Responsable: David + estadio.
4. Evaluación contractual de transmisión a AWS, anexo de tratamiento, subencargados, residencia/transferencia y política de retención aprobada por asesor tributario. El análisis académico cita la norma; no sustituye concepto legal del responsable. Responsable: Samuel.
5. La carta concreta del evento no ha sido recibida; completar la respuesta de 72 horas cuando llegue, sin inventar requisitos. Responsable: Miguel.
6. La presentación tiene guion de 20 diapositivas (`integracion/presentacion_guion.md`); grupo debe repartir voces y ensayar.

## Subtotales de caja modelados (COP, no costo total)

| Escenario | Año 1 | Año 5 | Saldo parcial año 1 vs. tope |
|---|---:|---:|---:|
| A | 113.583.280 | 23.184.650 | 166.416.720 |
| B, F-14 opción 2 | 129.363.740 | 38.965.110 | 150.636.260 |

La hoja mantiene estado **INCOMPLETO** porque hay filas requeridas sin precio. No usar estos saldos como aprobación presupuestal. El subtotal incluye supuestos valorados, no egress medido, cotizaciones de proveedores ni costos variables completos de pagos.

## Decisiones del grupo

- F-14: opción 2, usar torniquetes del estadio si se verifica compatibilidad; adquirir lectores/controlador faltantes.
- F-15: comprar cola virtual a proveedor con SLA, ensayo de carga y precio aceptables; si no hay oferta que cumpla, reevaluar construcción propia. No se inventa precio ni se afirma contratación.
- Recomendar A por menor latencia estimada y menor dependencia de conectividad híbrida; revisar tras recibir cotizaciones.
