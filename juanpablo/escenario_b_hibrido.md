# Escenario B híbrido — equipos, energía y conectividad

## 1. Topología

**Bogotá on-premise:** aplicación, caché local, servidor central del estadio, nodos de puerta, torniquetes/lectores, switches, UPS y router. **AWS:** DynamoDB (us-east-1 + réplica us-east-2), estado de cola virtual, CDN, API/servicios complementarios y aplicación en espera. La conexión principal es Direct Connect por Equinix BG1; VPN y segundo enlace son respaldo.

DynamoDB no se instala localmente. B requiere aceptación del profesor (P-1). Si Bogotá se pierde, la base y el estado de cola siguen en AWS; se conmuta la venta a la aplicación en espera. CloudFront no conmuta solicitudes POST por origin failover, por lo que el procedimiento de venta debe usar DNS/Route 53 o cambio manual según el runbook.

## 2. BOM de David (estadio.md §9)

| Equipo | Cantidad | Especificación mínima | Estado de precio |
|---|---:|---|---|
| Servidor central | 2 | 1U, 8 núcleos, 32 GB, 2 SSD RAID1, fuentes redundantes | Referencia Dell R360 8C/32GB/SSD RAID y dual PSU: COP 32.308.000/unidad; IVA/garantía confirmar |
| Nodo de puerta | 15 | Mini PC industrial fanless, 8GB, SSD 128GB (12 activos + 3 repuesto) | Referencia: 3nStar PC082WV, 8GB/240GB, COP 2.025.856 IVA incluido; garantía publicada 1 año. Cotizar alternativa/soporte que cubra 5 años |
| Torniquete + lector QR fijo PoE | 48 | lector 2D pantalla móvil, Ethernet PoE | Referencia de cuerpo: AXCSS AX-KATRAX COP 3.784.000 + IVA/unidad; lector QR PoE y controlador no incluidos. Integración/garantía por cotizar |
| Lector QR portátil | 24 | Android, lector 2D, base Ethernet o Wi-Fi | Cotización pendiente |
| Switch PoE de puerta | 12 | 8 puertos PoE, 2 uplinks | Referencia Hikvision 8 PoE + 2 uplinks Gigabit desde COP 355.045; puertos PoE 10/100, confirmar que el ancho de banda sea suficiente y cotizar garantía |
| Switch de núcleo | 2 | 24 puertos, enlaces fibra | Cotización pendiente |
| UPS de puerta | 12 | autonomía ≥2 horas | Cotización pendiente; validar carga de 4 torniquetes + nodo + switch |
| UPS sala técnica | 2 | autonomía ≥2 horas | Cotización pendiente |
| Router dual WAN | 1 | fibra + módem 4G/5G | Cotización pendiente |
| Plan de datos 4G/5G | 1 | bajo volumen, unos 45.000 escaneos/evento × 1 KB | Cotización pendiente |
| Rack, cableado e instalación | 1 lote | instalación en estadio | Cotización pendiente |

### Precio de servidor usado como referencia

Sigma Tiendas publica Dell PowerEdge R360 1U con Intel 8 núcleos, 32 GB DDR5 ECC, SSD configurables RAID y doble fuente por **COP 32.308.000**. Para dos unidades: **COP 64.616.000**. La publicación no deja clara la inclusión de IVA ni un soporte de cinco años; ambos deben quedar en cotización. No usar como precio contractual.

Alternativa: Lenovo ThinkSystem SR250 V3 8 núcleos/32GB/RAID a COP 19.729.329 + IVA en Lasus; confirmar la configuración de discos y fuentes redundantes antes de compararlo. La oferta Lenovo resulta más barata, pero no se da por equivalente hasta confirmar discos/PSU/garantía.

## 3. Energía anual del estadio (corregida)

No corresponde aplicar la fórmula de un data center (8.760 h y PUE 1,8) a equipos ubicados en el estadio y encendidos durante eventos. El PUE mide sobrecarga de infraestructura de un centro de datos; aquí se usa directamente la energía de los equipos: `kW × horas energizadas × 900 COP/kWh`.

Supuesto provisional editable: 25 eventos/año × 4 horas energizadas por evento (preparación, ingreso de 90 minutos y cierre) = 100 h/año. Se cuentan 12 nodos de puerta activos; los 3 nodos de repuesto son *cold spares* y permanecen apagados. Con las potencias provisionales del Excel, el consumo estimado es ≈ 2,254 kW y el costo anual ≈ **COP 202.860**, no COP 32,8 millones. El valor es de energía directa (sin multiplicar por PUE). No es medición: reemplazar kW por fichas técnicas/mediciones; incluir pérdidas UPS y motores de torniquetes cuando se conozcan. Si servidores o switches deben quedar encendidos fuera de eventos, aumentar sus horas por separado.

## 4. Direct Connect y VPN

- AWS lista Equinix BG1, Bogotá, como ubicación de Direct Connect; conexiones dedicadas disponibles 1 Gbps y 10 Gbps.
- Tarifa AWS pública de puerto dedicado: USD 0,30/h (1 Gbps) o USD 2,25/h (10 Gbps). 1 Gbps 24×7 durante 8.760 h = USD 2.628/año = COP 10.512.000/año. 10 Gbps = USD 19.710/año = COP 78.840.000/año.
- Estos valores **no incluyen** puerto/servicio del partner, cross-connect Equinix, circuito de fibra desde el DC, instalación, CPE ni soporte. El precio real de acceso a BG1 debe cotizarse con partner AWS.
- VPN Site-to-Site se incluye como respaldo; calcular con número de túneles, horas y datos transferidos según región.
- El segundo enlace redundante es obligatorio para que la pérdida del único circuito no aísle Bogotá. Proveedor y tarifa pendientes.

## 5. Sitio alterno

El sitio alterno no es un segundo centro de datos físico: es la aplicación en espera en AWS (A5/B1 de Miguel), junto con cola virtual con estado en AWS (B2) y enlace redundante (B3). Deben costearse horas de cómputo/almacenamiento de la aplicación en espera, balanceo, DNS/health checks, logs, transferencia y la licencia/operación de la cola. La capacidad de espera debe definirse (mínima siempre encendida o encendido bajo demanda) y asociarse al RTO.

## 6. Soporte de cinco años

David propone Ubuntu 26.04 LTS, cuyo soporte estándar llega a mayo de 2031; si la compra se hace a inicios de 2027, no cubre cinco años completos. Canonical publica Ubuntu Pro a USD 500/servidor-año y USD 25/workstation-año. En el Excel se modelan 2 servidores + 12 nodos activos como workstation = USD 1.300/año (COP 5.200.000/año con TRM académica). Los 3 nodos de repuesto apagados no se incluyen hasta su puesta en servicio. Confirmar con Canonical la clasificación workstation y la cobertura de cinco años; no asumir que la licencia comercial tiene el mismo ciclo que el soporte estándar. PostgreSQL 18 requiere una migración mayor estimada por Miguel en 24 horas: COP 2.880.000 de mano de obra.
