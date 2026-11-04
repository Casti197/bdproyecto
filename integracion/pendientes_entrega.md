# Entrega BoletaYa — estado integrado al 4 de noviembre de 2026

## Entregables

| Entregable | Estado | Archivo autoritativo |
|---|---|---|
| Propuesta escrita, máximo 25 páginas | Lista: 10 páginas | `entrega/propuesta_boletaya.pdf` (fuente `entrega/fuentes_pdf/propuesta.md`) |
| Hoja de costos | Modelo consolidado con precios públicos, capturas y supuestos; no son cotizaciones vinculantes | `entrega/costos_boletaya_final.xlsx` y `entrega/evidencias/` |
| Registro de decisiones | 25 fichas | `entrega/registro_decisiones.md` (también en anexos) |
| Concurrencia y conmutación | Listos como anexos | `david/anexo_concurrencia.md`, `david/alta_disponibilidad.md` |
| Carta del evento | No se asignó carta al grupo; no se inventan condiciones | Miguel prepara el memorando cuando llegue una carta concreta |
| Presentación | Deck externo de 20 diapositivas; guion sincronizado | `integracion/presentacion_guion.md` |

## Decisiones integradas

- Recomendar A: aplicación y DynamoDB en AWS; el estadio permanece local en A y B.
- F-14: usar torniquetes del estadio y lectores QR Wiegand; validar compatibilidad en sitio.
- F-15: construir la cola virtual sobre AWS; validar estimación y desempeño con calculadora y prueba de carga.
- F-16: la reserva de 10 % se usa solo para B en año 1.
- F-23: 12 terminales portátiles, una por puerta; F-24: fondo de reposición; F-25: B sin caché en espera en us-east-2.
- F-10/D-2b: runbook 2b usa `bya_ledger` MRSC por minuto y consulta Mercado Pago por `gid`; la búsqueda por fecha falló en sandbox.
- Seguridad definida en diseño; el SAQ PCI, contrato y matriz de retención requieren revisión antes de producción.

## Costos modelados (COP)

| Escenario | Año 1 caja | Año 5 caja | Total caja 5 años | TCO 5 años |
|---|---:|---:|---:|---:|
| A | 193.985.458 | 86.079.042 | 473.700.546 | 619.860.546 |
| B | 291.130.117 | 121.955.608 | 699.813.308 | 874.773.308 |

A queda bajo el tope de COP 280 M en año 1. B supera el tope base en COP 11,13 M y requiere la reserva única de 10 % autorizada; para años 2–5 se mantiene bajo el tope anual de COP 130 M. Las cifras son modelos basados en precios públicos y supuestos, no cotizaciones vinculantes.

## Pendientes reales

1. **David + estadio:** probar compatibilidad de torniquetes/controladores con los lectores escogidos; verificar capacidad, disponibilidad, stock e instalación.
2. **Juan Pablo:** validar garantías y precios finales con proveedores; revisar los valores de AWS Pricing Calculator, AWS Backup y enlaces. Las capturas guardadas son precios consultados, no ofertas comerciales.
3. **Samuel + asesor:** confirmar SAQ PCI, matriz documental de retención, aviso y contrato de transmisión a AWS. EE. UU. figura en la Circular SIC consultada, pero el contrato y la responsabilidad demostrada siguen aplicando.
4. **Miguel:** redactar respuesta cuando se reciba una carta concreta del evento; aún no fue asignada.
5. **Todos:** leer la propuesta completa, compartir el deck externo y ensayar. Latencia desde Bogotá y RTO siguen como estimaciones, no mediciones de producción.
