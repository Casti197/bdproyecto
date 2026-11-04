# Juan Pablo — Costos y dimensionamiento

**Proyecto:** BoletaYa SAS · **Responsable:** Juan Pablo · **Escenario:** A (ruta crítica en AWS) y B (híbrido Bogotá + AWS)

## Entregables

- `costos_y_dimensionamiento.md`: método, costos base y evaluación de presupuesto.
- `catalogo_precios.md`: precios unitarios, fuentes, fecha y estado de verificación.
- `escenario_b_hibrido.md`: hardware del estadio, energía, conectividad y sitio alterno.
- `sensibilidad_y_tco.md`: TCO a cinco años, doble de preventas y doble de cola.
- `fuentes_y_evidencias.md`: enlaces oficiales y comerciales consultados.
- `costos_boletaya.xlsx`: libro editable con parámetros, supuestos, fórmulas, CAPEX/OPEX y pendientes.

## Cómo actualizar

1. Ejecutar `git pull` antes de editar.
2. Actualizar los parámetros amarillos de `costos_boletaya.xlsx` cuando lleguen cotizaciones o cambien los volúmenes de Jacobo.
3. No reemplazar celdas de fórmulas por valores manuales.
4. Cada precio nuevo debe llevar URL, fecha de consulta, región, moneda y condición de IVA.
5. Cuando cambien los volúmenes de Jacobo, volver a ejecutar `jacobo/calculos/modelo_capacidad.py` y actualizar la hoja `Volumenes`.

## Estado de la entrega

Los valores reproducibles del modelo DynamoDB y las tarifas oficiales verificadas se incluyen como base. Hardware de estadio, proveedor de cola virtual, Direct Connect/Equinix, VPN, conectividad redundante, varios periféricos y la captura de AWS Pricing Calculator requieren cotización o ejecución desde la cuenta del equipo. Se dejan marcados como **PENDIENTE**, no se inventan.

