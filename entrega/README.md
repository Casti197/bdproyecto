# Entrega final — BoletaYa SAS (DynamoDB en AWS)

Versión integrada del 2026-11-04. Recomendación: **Escenario A (todo en AWS, estadio local)**.

| Entregable del enunciado (§7) | Archivo | Estado |
|---|---|---|
| Propuesta escrita (PDF, ≤ 25 págs.) | [`propuesta_boletaya.pdf`](propuesta_boletaya.pdf) (12 páginas; fuente en `fuentes_pdf/propuesta.md`) | Lista |
| Hoja de costos | [`costos_boletaya_final.xlsx`](costos_boletaya_final.xlsx) y capturas en [`evidencias/`](evidencias/) | Lista: todas las líneas con precio, fuente y fecha |
| Registro de decisiones (≥ 8 fichas) | [`registro_decisiones.md`](registro_decisiones.md) (25 fichas) y en [`anexos_boletaya.pdf`](anexos_boletaya.pdf) | Lista |
| Análisis de concurrencia | `david/anexo_concurrencia.md`, también en `anexos_boletaya.pdf` | Lista |
| Estudio de conmutación | `david/alta_disponibilidad.md`, también en `anexos_boletaya.pdf` | Lista |
| Memorando de la carta de evento | — | No se asignó carta al grupo |
| Presentación (≤ 20 diapositivas) | Deck de 20 diapositivas en claude.ai (se descarga como PowerPoint o PDF); guion en `integracion/presentacion_guion.md` | Lista |

## Qué se agregó al integrar

* Secciones que faltaban: seguridad y cumplimiento (5.6), norma tributaria citada, Ley 1581, DynamoDB *on premise* y alternativa compatible, comparación A contra B y recomendación (5.8).
* Hoja de costos nueva a partir de la de Juan Pablo: estadio en A y en B, cómputo de la aplicación, cola, seguridad y monitoreo, saldo con el signo correcto, torniquetes del estadio, VPN con precio público en B, sensibilidades y TCO.
* Fichas F-16 a F-22 del registro.
* Único cambio en una carpeta ajena: el paso 4 del runbook 2b de Miguel ahora toma las sillas en duda de `bya_ledger` (D-2b), para que el anexo F coincida con la propuesta.

## Resultado

| COP millones | Año 1 (tope 280) | Peor año 2–5 (tope 130) | Caja 5 años | TCO 5 años |
|---|---|---|---|---|
| A | 194,0 | 86,1 | 473,7 | 619,9 |
| B | 291,1 (usa la reserva del 10 %) | 122,0 | 699,8 | 874,8 |

## Lo que queda para el grupo

1. Leer la propuesta completa, en especial lo que cada uno no escribió: el jurado puede preguntarle a cualquiera.
2. Compartir el deck desde su menú Compartir y ensayar la sustentación.
3. Si el jurado exige la AWS Pricing Calculator, exportar un estimado con los mismos valores de la hoja `Precios`.
