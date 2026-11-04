# Entrega final — BoletaYa SAS (DynamoDB en AWS)

Versión integrada del 2026-11-04. Recomendación: **Escenario A (todo en AWS, estadio local)**.

| Entregable del enunciado (§7) | Archivo | Estado |
|---|---|---|
| Propuesta escrita (PDF, ≤ 25 págs.) | [`propuesta_boletaya.pdf`](propuesta_boletaya.pdf) (12 páginas; fuente en `fuentes_pdf/propuesta.md`) | Lista |
| Hoja de costos | [`costos_boletaya_final.xlsx`](costos_boletaya_final.xlsx) y capturas en [`evidencias/`](evidencias/) | Lista: cada precio con fuente, fecha y captura (salvo el servidor Dell, agotado, con URL y fecha) |
| Registro de decisiones (≥ 8 fichas) | [`registro_decisiones.md`](registro_decisiones.md) (25 fichas) y en [`anexos_boletaya.pdf`](anexos_boletaya.pdf) | Lista |
| Análisis de concurrencia | `david/anexo_concurrencia.md`, también en `anexos_boletaya.pdf` | Lista |
| Estudio de conmutación | `david/alta_disponibilidad.md`, también en `anexos_boletaya.pdf` | Lista |
| Memorando de la carta de evento | — | No se asignó carta al grupo |
| Presentación (≤ 20 diapositivas) | Deck de 20 diapositivas en claude.ai (se descarga como PowerPoint o PDF); guion en `integracion/presentacion_guion.md` | Lista |

## Qué se integró

- Seguridad, PCI sujeto a confirmación del SAQ, retención por clase documental, Ley 1581, la limitación de DynamoDB *on premise*, comparación A/B y recomendación.
- Costos de ambos escenarios, incluidos precios de hardware del estadio con evidencia, aplicación, cola, seguridad, monitoreo, saldo, reserva y TCO.
- Fichas F-16 a F-25, incluida la reserva para B, fondo de reposición, 12 terminales portátiles y B sin caché de espera en us-east-2.
- Runbook 2b usa `bya_ledger` para las sillas en duda (D-2b).

## Resultado modelado

| COP millones | Año 1 (tope base 280) | Peor año 2–5 (tope 130) | Caja 5 años | TCO 5 años |
|---|---:|---:|---:|---:|
| A | 191,1 | 85,8 | 469,7 | 615,9 |
| B | 289,6 (usa la reserva del 10 %) | 121,7 | 697,1 | 872,1 |

B excede el tope base del año 1 en COP 9,59 M y requiere la reserva única; el año 5 queda bajo el tope anual por COP 8,33 M. Son cifras de modelo con precios públicos y supuestos, no cotizaciones vinculantes.

## Pendientes

Ninguno para la entrega. Lo que queda antes de una implementación real (cotización formal y compatibilidad de los torniquetes en sitio, SAQ PCI con el adquirente, contrato de transmisión con AWS, validación de la matriz de retención con un asesor tributario) está declarado como supuesto en la propuesta y no es un entregable del curso. No se asignó carta de evento.
