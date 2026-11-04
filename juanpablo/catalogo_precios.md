# Catálogo de precios unitarios y supuestos

**Fecha de consulta:** 3 de noviembre de 2026. **TRM de modelado:** COP 4.000/USD (supuesto del curso, no tasa de mercado).

| Concepto | Unidad | Precio USD | Precio COP | Fuente/criterio | Estado |
|---|---:|---:|---:|---|---|
| DynamoDB WRU / rWRU us-east-1/us-east-2 | millón | 0,625 | 2.500 | Lista de precios de Jacobo (consulta 29-oct) + página oficial DynamoDB | Verificado como referencia del modelo |
| DynamoDB RRU us-east-1 | millón | 0,125 | 500 | Lista de precios de Jacobo (consulta 29-oct) | Verificado como referencia del modelo |
| DynamoDB almacenamiento Standard us-east-1 | GB-mes | 0,25 | 1.000 | AWS DynamoDB pricing | Verificado |
| DynamoDB PITR | GB-mes | 0,20 | 800 | AWS DynamoDB pricing | Verificado |
| Backup on-demand DynamoDB | GB-mes | 0,10 | 400 | AWS DynamoDB pricing | Verificado |
| Restore DynamoDB | GB restaurado | 0,15 | 600 | AWS DynamoDB pricing | Verificado |
| AWS Backup DynamoDB warm storage | GB-mes | 0,10 (referencia) | 400 | AWS Backup pricing / región y storage tier deben elegirse en calculadora | Validar región/tier |
| Direct Connect dedicado 1 Gbps | puerto-hora | 0,30 | 1.200 | AWS Direct Connect pricing; no incluye partner/cross-connect/circuito | Verificado tarifa AWS, costo total pendiente |
| Direct Connect dedicado 10 Gbps | puerto-hora | 2,25 | 9.000 | AWS Direct Connect pricing | Verificado tarifa AWS, costo total pendiente |
| CloudFront South America | GB/solicitud | — | — | Valores de Jacobo: USD 25,3 / preventa moderada, USD 75,9 alta, USD 253 extrema | Estimación heredada, validar calculator |
| SQS estándar | millón solicitudes | — | — | AWS SQS: 1 M gratis/mes; tarifa regional exacta en calculadora | Pendiente de región y uso |
| Lambda | millón invocaciones + GB-s | — | — | AWS Lambda pricing | Pendiente de memoria, duración y frecuencia |
| Streams | 100.000 lecturas | 0,02 (después de cuota) | 80 | AWS DynamoDB pricing: 2,5 M gratis en ejemplo oficial | Verificado como tarifa de ejemplo; volumen falta |
| Ubuntu Pro servidor | máquina-año | 500 | 2.000.000 | Canonical pricing | Verificado |
| Ubuntu Pro workstation | máquina-año | 25 | 100.000 | Canonical pricing | Verificado; confirmar si aplica a nodos |
| Dell PowerEdge R360 8C/32GB/SSD RAID/dual PSU | unidad | — | 32.308.000 | Sigma Tiendas; precio publicado COP, IVA no aclarado | Referencia comercial, cotizar garantía/IVA |
| Lenovo ThinkSystem SR250 V3 8C/32GB/RAID | unidad | — | 19.729.329 + IVA | Lasus; referencia 7DCLA04TLA | Alternativa comercial, revisar discos/fuentes/garantía |
| Mini PC industrial fanless 8GB/128GB o superior | unidad | — | 2.025.856 | 3nStar PC082WV-8-240W10, Klikken; precio publicado con impuesto | Referencia comercial; SSD 240GB, garantía publicada 1 año; no cumple por sí sola soporte 5 años |
| Torniquete peatonal bidireccional AXCSS AX-KATRAX | unidad | — | 3.784.000 + IVA | BioLabels; precio publicado antes de IVA | Solo cuerpo del torniquete; lector QR/PoE y controlador aparte |
| Switch Hikvision 8 puertos PoE + uplinks | unidad | — | 355.045 | Asegúrate Colombia; referencia DS-3E0310P-E/M | Confirmar gigabit/PoE budget y garantía antes de comprar |
| Lector QR fijo PoE / controlador de acceso | unidad | — | — | Debe integrarse con torniquete AX-KATRAX y el nodo local | Cotización pendiente; no confundir lector USB con lector PoE |
| Lector QR portátil Android | unidad | — | — | David requiere 24 | Cotización pendiente |
| Switch PoE 8 puertos | unidad | — | — | David requiere 12 | Cotización pendiente |
| Switch core 24 puertos/fibra | unidad | — | — | David requiere 2; debe tener uplinks SFP/SFP+ compatibles | Cotización pendiente |
| UPS puerta ≥2 h | unidad | — | — | David requiere 12 | Cotización pendiente |
| UPS sala técnica ≥2 h | unidad | — | — | David requiere 2 | Cotización pendiente |
| Router dual WAN fibra + 4G/5G | unidad | — | — | David requiere 1 | Cotización pendiente |
| Direct Connect BG1 partner/cross-connect | mensual | — | — | Equinix BG1 + partner AWS | Cotización pendiente |
| VPN Site-to-Site | túnel-hora | — | — | AWS VPN pricing | Pendiente de número de túneles/horas |
| Cola virtual 250.000 personas | preventa/mes | — | — | Construcción propia o SaaS; no seleccionado | Cotización/estimación técnica pendiente |

| UPS puerta ≥2 h | unidad | — | — | David requiere 12; dimensionar con carga real de 4 torniquetes + nodo + switch | Cotización pendiente; no usar un UPS 1500 VA sin curva de autonomía |
| UPS sala técnica ≥2 h | unidad | — | — | David requiere 2; dimensionar servidores + core + router | Cotización pendiente |
| Lector QR portátil Android | unidad | — | — | David requiere 24; Android + lectura 2D + base Ethernet/Wi-Fi | Cotización pendiente; lectores USB/Bluetooth no son equivalentes |
| Router dual WAN fibra + 4G/5G | unidad | — | — | David requiere 1; failover cableado y módem celular | Cotización pendiente |

## Observaciones

1. Los precios de AWS varían por región y unidad de consumo. La calculadora debe usar región `us-east-1` y réplica `us-east-2` para el diseño recomendado; CloudFront usa zona South America.
2. El precio de servidor Dell se toma como precio público de distribuidor, pero la ficha de venta debe archivarse y solicitarse cotización formal que confirme IVA, soporte y garantía de cinco años.
3. La oferta Lenovo es alternativa con IVA explícito, pero no se presume que incluya el arreglo SSD/RAID exacto solicitado por David.
4. Las tarifas de AWS Backup deben seleccionarse en la calculadora para la región y modalidad real. No extrapolar la tarifa de EBS/EFS a DynamoDB sin verificar la línea específica.
5. El costo de SQS no equivale al costo de la sala de espera web.

## Mercado Pago (D-11)

| Concepto | Supuesto de modelado | Fuente/criterio | Estado |
|---|---:|---|---|
| Checkout Pro, pago con disponibilidad inmediata | 3,29 % + COP 800 por cobro + IVA sobre comisión | Referencia comercial comparativa publicada; la tarifa oficial depende del plazo y de la cuenta | Provisional, confirmar en el simulador de la cuenta |

La hoja calcula `número de órdenes × (valor promedio de orden × tasa + cargo fijo) × (1 + IVA)`. El costo queda vacío hasta ingresar el valor promedio real de la orden. No se debe sumar comisión a reembolsos o pagos fallidos sin validar el contrato.
