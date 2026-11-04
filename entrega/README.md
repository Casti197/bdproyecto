# Entrega final — BoletaYa SAS (DynamoDB en AWS)

Versión integrada del 2026-11-04. Recomendación: **Escenario A (todo en AWS, estadio local)**.

| Entregable del enunciado (§7) | Archivo | Estado |
|---|---|---|
| Propuesta escrita (PDF, ≤ 25 págs.) | [`propuesta_boletaya.pdf`](propuesta_boletaya.pdf) (10 páginas; fuente en `fuentes_pdf/propuesta.md`) | Lista |
| Hoja de costos | [`costos_boletaya_final.xlsx`](costos_boletaya_final.xlsx) y capturas en [`evidencias/`](evidencias/) | Modelo con fuentes, fechas y estimaciones; confirmar condiciones comerciales |
| Registro de decisiones (≥ 8 fichas) | [`registro_decisiones.md`](registro_decisiones.md) (25 fichas) y en [`anexos_boletaya.pdf`](anexos_boletaya.pdf) | Lista |
| Análisis de concurrencia | `david/anexo_concurrencia.md`, también en `anexos_boletaya.pdf` | Lista |
| Estudio de conmutación | `david/alta_disponibilidad.md`, también en `anexos_boletaya.pdf` | Lista |
| Memorando de la carta de evento | — | No se asignó carta al grupo |
| Presentación (≤ 20 diapositivas) | Deck externo de 20 diapositivas; guion en `integracion/presentacion_guion.md` | Guion listo; revisar, compartir y ensayar |

## Qué se integró

- Seguridad, PCI sujeto a confirmación del SAQ, retención por clase documental, Ley 1581, la limitación de DynamoDB *on premise*, comparación A/B y recomendación.
- Costos de ambos escenarios, incluidos precios de hardware del estadio con evidencia, aplicación, cola, seguridad, monitoreo, saldo, reserva y TCO.
- Fichas F-16 a F-25, incluida la reserva para B, fondo de reposición, 12 terminales portátiles y B sin caché de espera en us-east-2.
- Runbook 2b usa `bya_ledger` para las sillas en duda (D-2b).

## Resultado modelado

| COP millones | Año 1 (tope base 280) | Peor año 2–5 (tope 130) | Caja 5 años | TCO 5 años |
|---|---:|---:|---:|---:|
| A | 194,0 | 86,1 | 473,7 | 619,9 |
| B | 291,1 (usa la reserva del 10 %) | 122,0 | 699,8 | 874,8 |

B excede el tope base del año 1 en COP 11,13 M y requiere la reserva única; el año 5 queda bajo el tope anual por COP 8,04 M. Son cifras de modelo con precios públicos y supuestos, no cotizaciones vinculantes.

## Pendientes para el grupo

1. Validar en sitio la compatibilidad entre torniquetes existentes y lectores/controladores; confirmar stock, instalación, IVA y garantía de los precios consultados.
2. Revisar los supuestos de AWS Pricing Calculator, AWS Backup y conectividad con proveedores.
3. Confirmar con adquirente/asesor el SAQ PCI y revisar matriz de retención y contrato de transmisión a AWS.
4. Miguel redacta el memorando cuando llegue una carta concreta del evento; aún no fue asignada.
5. Compartir el deck externo, revisar las cifras y ensayar la sustentación.
