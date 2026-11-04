# Fuentes y evidencias — consultadas 3-nov-2026

## AWS — documentación y precios

- [Amazon DynamoDB pricing](https://aws.amazon.com/dynamodb/pricing/) — WRU/RRU, almacenamiento, PITR, backup, restore, exportación y Streams.
- [DynamoDB Global Tables billing](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/global-tables-billing.html) — rWRU/rWCU por región, GSI y transferencia de replicación.
- [DynamoDB warm throughput](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/warm-throughput.html) — definición, aumento proactivo y dependencia del tamaño/valor.
- [AWS Backup pricing](https://aws.amazon.com/backup/pricing/) — almacenamiento, transferencia entre regiones y restauraciones.
- [DynamoDB billing best practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-understanding-billing.html) — métricas de AWS Backup DynamoDB.
- [AWS Direct Connect pricing](https://aws.amazon.com/directconnect/pricing/) — horas de puerto y transferencia.
- [AWS Direct Connect locations](https://aws.amazon.com/directconnect/locations/) — Equinix BG1 Bogotá.
- [AWS Direct Connect partners](https://aws.amazon.com/directconnect/partners/) — socios disponibles por ubicación.
- [AWS anunció Direct Connect Bogotá](https://aws.amazon.com/about-aws/whats-new/2023/05/aws-direct-connect-bogota-colombia/) — disponibilidad de BG1.
- [Amazon SQS pricing](https://aws.amazon.com/sqs/pricing/) — solicitudes de cola de mensajes.
- [Amazon CloudFront FAQs](https://aws.amazon.com/cloudfront/faqs/) — categorías de cobro de CloudFront; seleccionar South America en la calculadora.

## Mercado Pago — D-11 y comisión

- [Mercado Pago Colombia: costos de cobros](https://vendedores.mercadolibre.com.co/nota/como-calcular-tus-costos-al-usar-mercado-pago) — la comisión se aplica sobre cobros aprobados y varía según el medio de pago y el plazo de disponibilidad; se añade IVA. Consultado 3-nov-2026.
- [Mercado Pago Colombia: Link de Pago y comisiones](https://vendedores.mercadolibre.com.co/nota/todo-lo-que-necesitas-saber-para-cobrar-con-link-de-pago) — porcentaje más IVA y plazo de liberación. Consultado 3-nov-2026.
- [Mercado Pago Developers Colombia](https://www.mercadopago.com.co/developers/es/docs/getting-started) — Checkout Pro y Checkout API disponibles en Colombia.
- [Comparativa de tarifas Colombia 2026](https://zeroazul.com/blog/pasarelas-de-pago-colombia-comparativa) — referencia secundaria de 3,29 % + IVA para disponibilidad inmediata y COP 800 + IVA en Checkout Pro; validar contra simulador/cuenta antes de presupuesto contractual.

## Hardware / licencias

- [Sigma Tiendas — Dell PowerEdge R360 8C/32GB/960GB SSD](https://sigmatiendas.com/es-co/products/servidor-dell-poweredge-r360-1-x-intel-3ghz-32gb-ram-960gb-ssd-2-x-480gb-ssd-configuration-serie-ata-600-12gb-s-sas-controlador) — precio COP 32.308.000 publicado; verificar IVA, inventario y garantía de 5 años.
- [Lasus — Lenovo ThinkSystem SR250 V3 8C/32GB/RAID](https://lasus.com.co/es/thinksystem-sr250-v3-xeon-6353p-8c-65w-27ghz-32gb-2rx8-pc5-5600-raid-545-8i-0-1-10-8x25-hs-bp-kit-x350-x40-2x800wp) — COP 19.729.329 + IVA; confirmar configuración final.
- [Canonical Ubuntu Pro pricing](https://ubuntu.com/pricing/pro) — USD 500/server-year y USD 25/workstation-year.
- [Klikken — 3nStar PC082WV industrial fanless](https://klikken.com.co/tecnologia/computadores-y-movilidad/computadores/pc-industrial-fanless-3nstar-pc082w-celeron-j6412-8gb-ram-240gb-ssd-windows-10-iot/) — COP 2.025.856 con impuesto, 8GB/240GB; garantía publicada 1 año.
- [BioLabels — AXCSS AX-KATRAX](https://www.biolabels.com.co/product-page/torniquete-tipo-pedestal-bidireccional-para-control-de-acceso-ax-katrx-axcss) — COP 3.784.000 antes de IVA; cuerpo del torniquete, integración de lector QR aparte.
- [Asegúrate Colombia — switches PoE](https://aseguratecolombia.com/productos) — referencia de switch PoE 8 puertos DS-3E0310P-E/M a COP 355.045; verificar ancho de banda y PoE budget.
- [Equinix BG1](https://www.equinix.com/data-centers/americas-colocation/colombia-colocation/bogota-data-centers/bg1) — datos del centro de datos; solicitar cotización de cross-connect/colo.

## Fuentes internas del repositorio

- `jacobo/capacidad_y_volumetria.md` §7–§8 y `jacobo/calculos/salida_modelo.md` — volúmenes, WRU/RRU, CloudFront, crecimiento y capa de datos.
- `jacobo/calculos/evidencia/aws_pricelist_dynamodb_*.json` — API de lista oficial de precios consultada 2026-10-29.
- `miguel/lista_componentes_para_juan_pablo.md` — respaldos, retenciones, copias, restauraciones, DBA y Ubuntu Pro.
- `david/estadio.md` §9 — cantidades y especificación de hardware del estadio.

## Captura de AWS Pricing Calculator

**Pendiente de ejecución con la cuenta del equipo.** La lista de precios vía API no reemplaza la captura/exportación exigida por el enunciado. Crear una estimación por región/servicio, guardar el PDF o captura y adjuntarla en esta carpeta. No afirmar que ya existe.
