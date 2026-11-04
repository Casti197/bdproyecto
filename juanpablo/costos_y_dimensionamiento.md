# Costos y dimensionamiento — BoletaYa SAS

**Responsable:** Juan Pablo · **Precios consultados:** 3–4 nov 2026 · **Moneda:** COP · **TRM académica:** COP 4.000/USD.

## Criterio

La hoja [`costos_boletaya_final.xlsx`](costos_boletaya.xlsx) es el modelo numérico autoritativo. Tiene precios o tarifas de referencia, fuente y fecha por línea; incluye capturas para hardware y servicios principales en `entrega/evidencias/`. Los precios públicos consultados no son cotizaciones vinculantes. Antes de comprar hay que confirmar existencia, compatibilidad, IVA, instalación y garantía.

El total incorpora el estadio en ambos escenarios, precios del hardware, API Gateway/Lambda, ElastiCache, cola virtual propia, seguridad/monitoreo, enlaces y el ledger de recuperación D-2b. La hoja separa gasto de caja de administración incluida en TCO. Reserva: 10 % del presupuesto del año 1, disponible una sola vez; F-16 decide usarla solo para B.

## Totales modelados (COP)

| Escenario | Año 1 | Año 2 | Año 3 | Año 4 | Año 5 | Caja 5 años | TCO 5 años |
|---|---:|---:|---:|---:|---:|---:|---:|
| A — AWS + estadio local | 193.985.458 | 58.664.181 | 64.021.797 | 70.950.069 | 86.079.042 | 473.700.546 | 619.860.546 |
| B — híbrido + estadio local | 291.130.117 | 89.661.939 | 95.049.331 | 102.016.313 | 121.955.608 | 699.813.308 | 874.773.308 |

Presupuesto: COP 280 M en año 1 y COP 130 M/año en años 2–5. A deja COP 86.015.000 aprox. el año 1 y permanece bajo presupuesto cada año. B supera el tope base del año 1 en COP 11.130.117; F-16 aplica la reserva autorizada de COP 28 M y deja COP 16.869.883 de margen sobre el tope ampliado. B queda bajo el tope anual en años 2–5, con COP 8.044.392 de margen en año 5.

## Supuestos que explican la diferencia

- **Estadio:** ≈ COP 159,8 M en año 1 para ambos escenarios. Incluye 2 servidores, nodos de puerta con repuestos, 12 terminales portátiles, UPS, lectores QR Wiegand, switches, routers, gabinete, energía y datos móviles. F-14 usa los torniquetes existentes; F-23 reduce terminales portátiles de 24 a 12; F-24 agrega desde el año 2 un fondo anual de reposición del 10 % del hardware, porque el precio consultado trae garantía limitada.
- **A:** ≈ COP 34,2 M de nube en año 1; incluye aplicación/cola, caché principal y de espera, respaldo, CloudFront, DynamoDB y réplica. A deja caché de espera en us-east-2.
- **B:** añade dos servidores en Bogotá, energía con PUE 1,8, dos enlaces y VPN; F-25 elimina la caché de espera en us-east-2. El año 1 necesita la reserva. Si cae el sitio local, el estado de cola se reconstruye y se readmite por sorteo, como documenta el runbook 2c.
- **TCO:** agrega horas DBA, mantenimiento, pruebas, migración y actualizaciones; no confundir TCO con gasto de caja del escenario.

## Fuentes y conceptos pendientes

Las URLs, tarifas, supuestos y fechas por rubro están en `Precios`; las capturas están en `entrega/evidencias/`. La hoja `Pendientes` deja cuatro validaciones abiertas:

1. Si el jurado exige la AWS Pricing Calculator, exportar un estimado con los mismos parámetros y valores de `Precios`.
2. Confirmar con AWS Backup el tratamiento de copias entre cuentas/regiones; se modela la tarifa publicada para DynamoDB.
3. Obtener cotización comercial del hardware con garantía. El modelo usa precios publicados de tienda, no una oferta de compra.
4. Ingresar el valor promedio por orden para la comisión de Mercado Pago; se excluye del presupuesto de infraestructura por F-19.

Además, David y el estadio deben comprobar en sitio la compatibilidad entre los torniquetes existentes y los lectores/controladores elegidos. La cola virtual es propia (F-15); validar el costo modelado con calculadora y el desempeño con prueba de carga.

## Recomendación

Recomendar A: menor gasto modelado a cinco años (COP 473,7 M frente a COP 699,8 M), menor latencia estimada por compra y menos dependencia del enlace Bogotá–AWS. Las latencias y recuperaciones son estimaciones de diseño, no mediciones de producción. Revisar cifras al recibir cotizaciones y tras validar los precios y supuestos; la carta concreta del evento no fue asignada.
