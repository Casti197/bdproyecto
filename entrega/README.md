# Entrega final — BoletaYa SAS (DynamoDB en AWS)

Versión integrada del 2026-11-04. Recomendación: **Escenario A (todo en AWS, estadio local)**.

| Entregable del enunciado (§7) | Archivo | Estado |
|---|---|---|
| Propuesta escrita (PDF, ≤ 25 págs.) | [`propuesta_boletaya.pdf`](propuesta_boletaya.pdf) (12 páginas; fuente en `fuentes_pdf/propuesta.md`) | Lista |
| Hoja de costos | [`costos_boletaya_final.xlsx`](costos_boletaya_final.xlsx) | Lista; 5 rubros del estadio sin precio (hoja `Pendientes`) |
| Registro de decisiones (≥ 8 fichas) | [`registro_decisiones.md`](registro_decisiones.md) (22 fichas) y en [`anexos_boletaya.pdf`](anexos_boletaya.pdf) | Lista |
| Análisis de concurrencia | `david/anexo_concurrencia.md`, también en `anexos_boletaya.pdf` | Lista |
| Estudio de conmutación | `david/alta_disponibilidad.md`, también en `anexos_boletaya.pdf` | Lista |
| Memorando de la carta de evento | — | La carta no ha llegado |
| Presentación (≤ 20 diapositivas) | Deck de 20 diapositivas en claude.ai (se descarga como PowerPoint o PDF); guion en `integracion/presentacion_guion.md` | Lista |

## Qué se agregó al integrar

* Secciones que faltaban: seguridad y cumplimiento (5.6), norma tributaria citada, Ley 1581, DynamoDB *on premise* y alternativa compatible, comparación A contra B y recomendación (5.8).
* Hoja de costos nueva a partir de la de Juan Pablo: estadio en A y en B, cómputo de la aplicación, cola, seguridad y monitoreo, saldo con el signo correcto, torniquetes del estadio, VPN con precio público en B, sensibilidades y TCO.
* Fichas F-16 a F-22 del registro.
* Único cambio en una carpeta ajena: el paso 4 del runbook 2b de Miguel ahora toma las sillas en duda de `bya_ledger` (D-2b), para que el anexo F coincida con la propuesta.

## Lo que falta

1. Cotizar los 5 rubros del estadio: 48 lectores QR Wiegand, 24 portátiles, 14 UPS, núcleo/router/rack y plan 4G (Juan Pablo). A tiene COP 174,4 M de margen para ellos; B solo 66,7 M.
2. Capturas o exportación de la AWS Pricing Calculator (Juan Pablo).
3. La carta de evento, cuando llegue (Miguel coordina; 72 horas).
4. Samuel debe leer y poder defender §8 de la propuesta (seguridad), que redactó el integrador con los insumos de Jacobo.
5. Compartir el deck con el grupo desde su menú Compartir y ensayar la sustentación.
