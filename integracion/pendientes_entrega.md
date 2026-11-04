# Qué falta para entregar — por entregable y por persona

**Fecha:** 2026-11-04 · Revisión hecha leyendo el repositorio; la hoja de costos se recalculó con LibreOffice para ver los totales (el archivo subido no trae los valores calculados guardados).

## 1. Estado por entregable (sección 7 del enunciado)

| Entregable | Estado | Qué falta | Dueño |
|---|---|---|---|
| Propuesta escrita (PDF, ≤ 25 págs.) | 🟡 Esqueleto en `integracion/propuesta_borrador.md` | Seguridad, costos, decisión final, carta; redactar y diagramar | Samuel (armado); cada dueño su sección |
| Hoja de costos | 🟡 `juanpablo/costos_boletaya.xlsx` | Cotizaciones; correcciones de §3 | Juan Pablo |
| Registro de decisiones (≥ 8 fichas) | 🟡 16 fichas en `integracion/registro_decisiones.md` | Fichas de seguridad y recomendación; revisión de Samuel | Samuel |
| Análisis de concurrencia | ✅ `david/anexo_concurrencia.md` | — | David |
| Estudio de conmutación | ✅ `david/alta_disponibilidad.md` (borrador para revisión) | Revisión cruzada | David |
| Memorando de la carta | ⏳ No ha llegado | Plan listo | Miguel coordina |
| Presentación (≤ 20 diapositivas) | 🟡 Guion en `integracion/presentacion_guion.md` | Armar cuando cierren costos y recomendación | Samuel + quien esté libre |
| Sustentación | 🟡 `jacobo/resumen_sustentacion.md` | Ensayo del grupo | Todos |

## 2. Pendientes por persona

**Samuel (no hay carpeta `samuel/` en el repositorio)**
- [ ] Seguridad y cumplimiento (5.6), con los insumos de `jacobo/entrega_para_el_equipo.md` §4.
- [ ] Plazo de conservación según la norma tributaria, **con la norma citada** (no aparece en ningún archivo).
- [ ] Ley 1581: transferencia internacional a EE. UU. (condición del profesor, resp. 4).
- [ ] Conformidad con D-2 (F-09) y con el límite antibot.
- [ ] Revisar y cerrar `integracion/registro_decisiones.md`; agregar sus fichas.
- [ ] Comparación final y recomendación (5.8); armado del PDF.

**Jacobo**
- [ ] Sección de máximo 2 páginas: DynamoDB *on premise* y alternativa compatible con su API (resp. 1).
- [ ] Escenario A todo en AWS en `arquitectura.md` (resp. 2).
- [ ] AWS en Colombia, disponibilidad de DynamoDB y latencia (resp. 4).
- [ ] `bya_ledger` con clave listable por minuto, `gid` al pasar a `CHARGED` y latencia entre regiones (D-2b).

**Miguel**
- [ ] Runbook 2b, paso 4: la lista de sillas en duda sale de `bya_ledger`, no de la búsqueda de Mercado Pago (D-2b).
- [ ] Actualizar su README: todavía dice que Mercado Pago no se probó en el sandbox.
- [ ] Carta del estadio: de 40 minutos a 4 horas (resp. 7); runbooks del Escenario A sin aplicación en Bogotá (resp. 2).

**Juan Pablo**
- [ ] Correcciones de la hoja (§3).
- [ ] Cotizaciones: cola virtual, Direct Connect y partner en Equinix BG1, VPN y segundo enlace, AWS Backup en la calculadora, equipo del estadio, Pricing Calculator.
- [ ] Costear `bya_ledger` (MRSC en tres regiones, ≈ 24.000 escrituras por preventa grande).
- [ ] Comparar A y B en egress y costos (resp. 2); mostrar B con torniquetes propios y con los del estadio.
- [ ] Actualizar `costos_y_dimensionamiento.md` §12: las pruebas de sandbox ya se hicieron.
- [ ] El pendiente "Equipos estadio" de la hoja tiene como responsable a "Asistente": necesita un dueño del grupo.

**David**
- [ ] `respuestas_profesor.md` dice "46 de 46 pruebas"; `pruebas/resultado.txt` y su README dicen 50 de 50.
- [ ] Entregar a Miguel el verificador de invariantes para el simulacro.

**Grupo**
- [ ] Decidir el equipo de puerta del estadio (F-14) y la cola virtual (F-15).
- [ ] Aprobar los riesgos E-R1 y E-R2 del estadio.

## 3. Hallazgos en la hoja de costos (para Juan Pablo)

Totales que da la hoja recalculada:

| | Año 1 | Año 2 | Año 5 |
|---|---|---|---|
| Total A | COP 5.318.500 | 7.829.500 | 14.184.250 |
| Total B | COP 336.639.820 | 23.744.360 | 30.099.110 |

1. **El equipo del estadio está solo en B** (filas 8 a 14 y 25 de `Costos_Anuales`, escenario "B"). El profesor dijo que el estadio es local **en los dos** escenarios (resp. 2). Hoy A se ve casi gratis porque no carga los servidores, nodos, torniquetes, switches ni UPS del estadio. Con los torniquetes propios, A también pasaría del tope.
2. **No hay líneas de cómputo de la aplicación** en ninguno de los dos escenarios: API Gateway (USD 1,12 por preventa), Lambda o contenedores, y ElastiCache (2 nodos, USD 2.215 al año en us-east-1) están en `jacobo/entrega_para_el_equipo.md` §2.1 pero no en la hoja. En A la aplicación entera vive en AWS.
3. **El signo del "Saldo" está invertido** en `Resumen`: dice "presupuesto menos total", pero calcula total menos presupuesto (A año 1 da −274.681.500 cuando le sobran 274,7 M; B da +56.639.820 cuando se pasa por 56,6 M). David ya lo había señalado.
4. **Ubuntu Pro** está como COP 5.200.000 todos los años; según `david/estadio.md` §9.1 basta con el último año (de mayo de 2031 a inicios de 2032), o cambiar de versión sin licencia.
5. El archivo no guarda los valores calculados: al abrirlo con algunas herramientas los totales salen vacíos. Abrirlo y guardarlo en Excel o LibreOffice lo resuelve.
