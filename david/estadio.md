# Ingreso al estadio sin internet

**Autor:** David · **Fecha:** 2026-10-30, actualizado el 2026-11-04 con la respuesta 7 del profesor · **Rúbrica:** Ingreso al estadio sin internet (2 puntos)
**Insumos:** `jacobo/modelo_datos.md` §3.5 (`bya_tickets`), `jacobo/arquitectura.md` §7. Referencias `[R-xx]` en `jacobo/referencias.md`; `[D-xx]` en `david/concurrencia.md` §9 y al final de este documento.

> **Idea central:** cada boleta tiene **una sola puerta dueña**, y cada puerta tiene **un solo nodo** que decide con una escritura atómica. Dos puertas no pueden aceptar la misma boleta porque solo una tiene autoridad sobre ella, y dentro de la puerta el nodo serializa los escaneos. No hace falta internet ni conexión entre puertas para que esto se cumpla.

---

## 1. Resumen

| Pregunta | Respuesta |
|---|---|
| ¿Qué significa "sin internet"? (respuesta 7 del profesor) | El estadio pierde la conexión con AWS **y** con Bogotá, pero su red interna funciona. Hay que operar aislado **todo el ingreso: 4 horas**. La caída total de la red interna queda fuera del alcance |
| ¿Qué pasa si se cae internet? | Nada visible, durante las 4 horas o más. El ingreso funciona con datos locales; internet solo sirve para sincronizar |
| ¿Qué pasa si una puerta queda aislada de la red del estadio? | Sigue operando sola, porque ya tiene todo lo que necesita para sus boletas |
| ¿Y si un solo torniquete o lector pierde la red? | Ese carril se detiene y la gente pasa por los otros carriles **de la misma puerta**. El lector no decide solo, así que no puede dejar entrar dos veces (§6.2) |
| ¿Cómo se evita el doble ingreso entre dos puertas? | Asignación fija boleta → puerta. La otra puerta rechaza con "ingrese por la puerta X" |
| ¿Y dentro de la misma puerta, con dos torniquetes? | Un solo nodo por puerta marca la boleta con `UPDATE … WHERE st='VALID'`, que es atómico [D-05] |
| ¿Cuándo llega el registro a DynamoDB? | Apenas hay internet, con la transacción condicional de Jacobo; es idempotente y detecta duplicados [R-04] |

## 2. Supuestos

| ID | Supuesto | Por qué |
|---|---|---|
| E-01 | Cada localidad tiene **una puerta asignada**, impresa en la boleta ("Puerta 3") | Práctica habitual en estadios; es lo que hace posible la regla de autoridad |
| E-02 | Estadio de 45.000 personas con **12 puertas**, **4 torniquetes** por puerta | Para dimensionar el equipo; Juan Pablo puede ajustar las cantidades |
| E-03 | El ingreso dura 90 minutos: 45.000 / 5.400 s ≈ **8,3 escaneos/s** de promedio y **≈ 25/s** en el pico (×3, supuesto de Jacobo para AP-10) | Por puerta son ≈ 2/s en el pico: carga trivial para un nodo |
| E-04 | La red del estadio (cableado, energía) existe y la opera el estadio; BoletaYa instala sus equipos sobre ella | Fuera del alcance del curso |
| E-05 | El estadio opera **aislado durante 4 horas** (todo el ingreso), con su red interna funcionando | Respuesta 7 del profesor, 2026-11-04. Reemplaza los 40 minutos de la carta de Miguel |

## 3. Componentes

```mermaid
flowchart LR
  subgraph AWS["AWS (us-east-1)"]
    DDB[("DynamoDB<br/>bya_tickets")]
  end
  subgraph EST["Estadio"]
    subgraph CEN["Sala técnica"]
      C1[("Servidor central<br/>primario")]
      C2[("Servidor central<br/>respaldo síncrono")]
      R["Router<br/>fibra + 4G/5G"]
    end
    subgraph P3["Puerta 3"]
      N3[("Nodo de puerta 3")]
      T31["Torniquetes 1..4"]
    end
    subgraph P7["Puerta 7"]
      N7[("Nodo de puerta 7")]
      T71["Torniquetes 1..4"]
    end
  end
  DDB -- "copia antes del evento y cambios" --> R
  R -- "escaneos cuando hay internet" --> DDB
  R --- C1
  C1 -- "réplica síncrona" --> C2
  C1 -- "boletas de la puerta 3" --> N3
  N3 -- "cada ingreso" --> C1
  C1 -- "boletas de la puerta 7" --> N7
  N7 -- "cada ingreso" --> C1
  T31 --> N3
  T71 --> N7
```

| Componente | Qué hace | Qué datos tiene |
|---|---|---|
| **Nodo de puerta** (uno por puerta) | **Única autoridad** sobre las boletas de su puerta. Valida el QR, marca la boleta usada y responde al torniquete | Las boletas de las localidades asignadas a su puerta y sus escaneos |
| **Servidor central** (primario + respaldo) | Descarga la copia del evento desde AWS y la reparte a los nodos. Recibe todos los ingresos, sube los escaneos a DynamoDB y muestra el tablero de aforo | Todas las boletas del evento y todos los escaneos |
| **Torniquete con lector QR** | Lee el QR, pregunta al nodo y abre o rechaza. No decide nada | Ninguno |
| **Router doble** | Salida a internet por fibra y por 4G/5G | — |

## 4. Antes del evento: la copia

1. **T − 24 h:** el servidor central descarga las boletas del evento con el patrón AP-18 de Jacobo: 8 consultas en paralelo a `gsi_evento_boleta`, ≈ 45.000 boletas ≈ 9 MB [R-07]. Recibe también la **clave HMAC** del QR (desde el gestor de secretos, nunca en la base) y la tabla **localidad → puerta** del catálogo.
2. El central reparte a cada nodo **solo las boletas de su puerta** (≈ 3.750 por puerta).
3. **Mientras haya internet**, el central recibe los **cambios** (boletas nuevas, anuladas por reembolso) y los reenvía al nodo dueño. Propuesta: Streams de `bya_tickets` → Lambda → una cola SQS por evento que el central consulta cada pocos segundos (los Streams retienen 24 h [R-11]). **Pendiente con Jacobo:** activar Streams en `bya_tickets`.

## 5. Durante el evento: un ingreso

En el nodo de la puerta, cada escaneo es **una sola sentencia**:

```sql
-- Nodo de la puerta 3. tid sale del QR después de verificar el HMAC.
UPDATE boletas
   SET st = 'USED', usado_en = now(), torniquete = $t
 WHERE tid = $tid
   AND st  = 'VALID'
   AND puerta = 3                -- solo boletas de esta puerta
RETURNING tid;
-- 1 fila  -> abrir torniquete
-- 0 filas -> rechazar: ya usada, anulada o de otra puerta (una lectura dice cuál, para el mensaje)
```

**Por qué dos torniquetes de la misma puerta no dejan entrar dos veces la misma boleta.** En PostgreSQL, si dos `UPDATE` llegan a la misma fila al mismo tiempo, el segundo **espera** a que el primero confirme y luego **vuelve a evaluar el `WHERE`** sobre la versión actualizada de la fila [D-05]. Como el primero ya dejó `st = 'USED'`, el segundo no encuentra la fila y devuelve 0 filas.

**Por qué dos puertas distintas no dejan entrar dos veces la misma boleta.** La boleta de la localidad Oriental solo existe con `st = 'VALID'` en el nodo de la puerta 3. Si alguien presenta una copia del QR en la puerta 7, el nodo 7 no tiene autoridad sobre ella y responde "ingrese por la puerta 3". No hace falta que las dos puertas se comuniquen.

Validaciones del QR (formato `v1.<tid>.<eid>.<hmac>` de Jacobo):

| Paso | Rechazo si… | Funciona sin red |
|---|---|---|
| 1. Firma HMAC | El QR fue alterado o inventado | Sí, el nodo tiene la clave |
| 2. Evento | `eid` no es el de hoy | Sí |
| 3. Puerta | La localidad de la boleta no es de esta puerta | Sí |
| 4. Estado | `UPDATE` devuelve 0 filas | Sí |

Luego el nodo envía el ingreso al servidor central. Si la red interna está caída, lo guarda en una cola local y lo envía cuando vuelva.

### Línea de tiempo: dos personas con la misma boleta (una es una captura de pantalla)

| t (s) | Puerta 3, torniquete 1 | Puerta 3, torniquete 2 | Puerta 7 | Boleta `TKT#01JC3B` en el nodo 3 |
|---|---|---|---|---|
| 0,000 | Escanea | Escanea | — | `VALID` |
| 0,002 | `UPDATE` toma la fila | `UPDATE` espera a que el primero termine [D-05] | — | `VALID` (bloqueada) |
| 0,004 | Confirma: 1 fila → **abre** | Vuelve a evaluar `st = 'VALID'`: falso → 0 filas | — | `USED` |
| 0,005 | — | **Rechaza**: "boleta ya usada a las 18:04:12 en el torniquete 1" | — | `USED` |
| 40,000 | — | — | Escanea la misma captura: localidad de la puerta 3 → **rechaza** "ingrese por la puerta 3" | `USED` |

## 6. Fallas y qué pasa en cada una

| Falla | Efecto en el ingreso | Por qué se mantiene la regla |
|---|---|---|
| **Sin internet** | Ninguno | Todo lo necesario está en el estadio. Los escaneos esperan en el central para subir |
| **Puerta aislada de la red interna** | Ninguno en esa puerta | El nodo es la autoridad de sus boletas; no necesita a nadie. Sus ingresos esperan en una cola local |
| **Cae el servidor central primario** | Ninguno en las puertas | El respaldo tiene todo, porque la réplica es síncrona: un `COMMIT` responde solo cuando el cambio está en el disco de ambos [D-06]. Los nodos se reconectan al respaldo |
| **Cae el respaldo del central** | Con réplica síncrona, el primario dejaría de confirmar | Al detectar la caída, se pasa la réplica a asíncrona y se genera una alerta. La autoridad de los ingresos está en los nodos, no en el central, así que el ingreso no se detiene |
| **Cae un nodo de puerta** | Esa puerta se detiene | Los torniquetes se pasan al servidor central, que toma la autoridad de esa puerta **solo cuando el operador confirma que el nodo está apagado** (se desconecta de la energía). Hasta ese momento hay dos posibles dueños y no se puede arriesgar. Si el nodo estaba aislado antes de caer, puede tener ingresos que no alcanzó a enviar: antes de que el central tome la puerta se recuperan desde su SSD. Hay un nodo de repuesto por cada 4 puertas |
| **Se va la luz en una puerta** | Esa puerta se detiene | UPS por puerta con autonomía para el ingreso |

**Por qué el cambio de nodo lo confirma una persona.** Un sistema no puede distinguir entre un nodo apagado y un nodo vivo pero desconectado. Si el central tomara la autoridad solo porque dejó de oír al nodo, y el nodo siguiera vivo atendiendo su puerta, habría dos dueños de las mismas boletas: es exactamente el doble ingreso que queremos evitar. Apagar el nodo antes de tomar su lugar garantiza que solo haya un dueño. Es un procedimiento manual de minutos, en una falla poco probable, que no arriesga la regla.

### 6.1 RPO y RTO del ingreso

El enunciado fija RPO 0 y RTO 15 minutos para la plataforma. Para el ingreso propongo estos valores, que Miguel pidió declarar:

| Falla | RPO de los ingresos | RTO de la puerta | Por qué |
|---|---|---|---|
| Sin internet | 0 | 0 | Los escaneos se guardan en el central y suben al volver (§7) |
| Puerta aislada de la red interna | 0 | 0 | El nodo confirma el `UPDATE` en su disco **antes** de abrir el torniquete |
| Cae el central primario | 0 | 0 en las puertas | Réplica síncrona: el respaldo tiene cada cambio confirmado [D-06] |
| Cae un nodo de puerta, con su disco sano | 0 | **Minutos** (supuesto: 5 a 10): apagar el nodo, recuperar su cola desde el SSD, el central toma la puerta | Paso manual a propósito (§6) |
| Cae un nodo **y se daña su disco** mientras estaba aislado | Los ingresos no enviados de ese aislamiento | Igual al anterior | Es el único caso con pérdida |
| Se va la luz en una puerta | 0 | 0 mientras dure la UPS | UPS por puerta |

**El único RPO distinto de 0** requiere dos fallas a la vez en la misma puerta: aislamiento de la red y daño del disco. Lo que se pierde no es dinero ni una venta, sino la marca de "usada" de esas boletas. Su efecto es que esas boletas podrían volver a entrar por **la misma** puerta. Para que esa ventana sea de segundos, el nodo envía cada ingreso al central apenas lo confirma, y la cola local solo crece mientras la puerta está aislada.

Los RTO son supuestos míos y se miden en el ensayo previo al evento (Miguel). No hay cifra publicada que citar: dependen del procedimiento.

### 6.2 Un punto de acceso pierde la red interna (respuesta 7 del profesor)

"Punto de acceso" puede ser tres cosas distintas, y en ninguna una boleta entra dos veces:

| Qué pierde la red | Qué pasa en esa puerta | Por qué no hay doble ingreso |
|---|---|---|
| **Un torniquete o lector** pierde la conexión con su nodo | Ese carril muestra "fuera de servicio" y la gente pasa por los otros 3 carriles de la puerta. El lector portátil de apoyo puede cubrir ese carril conectándose por Wi-Fi al mismo nodo | El lector **nunca** decide solo: sin respuesta del nodo no abre. La boleta sigue `VALID` en el nodo y se marca cuando la escanee otro carril |
| **Toda la puerta** (nodo, switch y torniquetes) pierde el enlace con el núcleo | La puerta sigue funcionando completa: el nodo es la autoridad de sus boletas y guarda los ingresos en su cola local | Las otras puertas no tienen esas boletas como `VALID`, así que rechazan con "ingrese por la puerta X" (§5) |
| **El nodo** de la puerta se cae | La puerta se detiene hasta que el operador apaga el nodo y el central toma la autoridad, o se instala uno de repuesto (5 a 10 min, §6.1) | Mientras el nodo no esté apagado, el central no toma la puerta: nunca hay dos autoridades para la misma boleta (§6) |

**Durante 4 horas aislado** nada de esto cambia: el nodo no necesita a nadie fuera de su puerta, y la cola local de ingresos de una puerta aislada mide unos KB por escaneo, con disco de 128 GB. Lo que sí crece con 4 horas es el riesgo E-R1 (boletas reembolsadas que el nodo no conoce): por eso se cierran los reembolsos 2 horas antes de abrir puertas.

## 7. Sincronización con DynamoDB

Cuando hay internet, el servidor central sube cada ingreso con la transacción de 2 ítems de Jacobo (`modelo_datos.md` §3.5), marcada como fuera de línea:

```text
TransactWriteItems   ClientRequestToken = H(tid, "SCAN")
  Update bya_tickets TKT#<tid> / T
         IF  st = 'VALID' AND eid = :eid
         SET st = 'USED', usa = :usado_en, pta = :puerta   ADD ver :uno
  Put    bya_tickets TKT#<tid> / SCAN#<usado_en>#<puerta>
         (res='OK', dis=:torniquete, off=true)
         IF attribute_not_exists(pk)
```

| Resultado | Significado | Acción |
|---|---|---|
| Éxito | Primera vez que se sube | Marcar sincronizado en el central |
| `ConditionalCheckFailed` y en la nube `usa` y `pta` son los mismos | Ya se había subido (reintento) | Marcar sincronizado |
| `ConditionalCheckFailed` y en la nube la boleta fue anulada (`VOID`) | Se reembolsó después de la última copia y alguien entró igual | Registrar `SCAN` con `res='DUPLICADA'` y reportarlo al organizador |
| `TransactionConflict` o *throttling* | Temporal | Reintento con *backoff* (mismas reglas de `concurrencia.md` §7) |

El orden de llegada no importa: cada boleta tiene un solo nodo que la marca, así que no hay dos versiones del ingreso que reconciliar.

**Volumen:** ≈ 45.000 transacciones por evento. A 25/s de pico son 100 WRU/s (2 ítems × 2 por transacción [R-02]), muy por debajo de lo que Jacobo dimensionó.

## 8. Riesgos y decisiones para el grupo

| # | Riesgo o decisión | Propuesta |
|---|---|---|
| E-R1 | **Boleta anulada (reembolso) sin internet:** el nodo no se entera y la deja entrar | Riesgo aceptado: se detecta en la sincronización (§7). Para reducirlo, cerrar reembolsos 2 h antes de abrir puertas. Con el aislamiento de 4 h del profesor, ese cierre es necesario: sin él, todo reembolso hecho durante el ingreso queda sin aplicar |
| E-R2 | **Boleta vendida después de la última copia, sin internet:** el nodo no la conoce | Si el HMAC es válido, el evento coincide y la localidad es de esa puerta, **aceptar** y marcarla "fuera de copia". La firma garantiza que la emitió BoletaYa. Decisión del grupo |
| E-R3 | Asignación fija de puerta: si una puerta se llena, no se puede desviar gente a otra | El organizador puede reasignar una localidad a otra puerta **antes** del evento. Durante el evento, solo con el procedimiento manual de §6 |
| E-R4 | Clave HMAC robada de un nodo | Clave por evento, rotada después de cada uno; los nodos sin disco extraíble. Coordinar con Samuel |

## 9. Equipo del estadio y base de costos

Cantidades con los supuestos E-02 y E-03. Los precios de referencia se registran en `entrega/costos_boletaya_final.xlsx`; la hoja adjunta las fuentes y fechas consultadas.

| Equipo | Cantidad | Especificación mínima | Para qué |
|---|---|---|---|
| Servidor central | 2 | 1U, 8 núcleos, 32 GB RAM, 2 SSD en RAID 1, 2 fuentes | Primario y respaldo síncrono |
| Nodo de puerta | 12 + 3 de repuesto | Mini PC industrial sin ventilador, 8 GB RAM, SSD 128 GB, Ethernet | Una autoridad por puerta |
| Torniquete con lector QR fijo, Ethernet PoE | 48 | Lector 2D que lea pantallas de celular | 4 por puerta |
| Terminal portátil con lector QR | 12 | Android con lector 2D, Ethernet por base o Wi-Fi | Una por puerta para apoyo y accesibilidad (F-23) |
| Switch PoE de puerta | 12 | 8 puertos PoE, 2 enlaces de subida | Conecta torniquetes y nodo |
| Switch de núcleo | 2 | 24 puertos, enlaces de fibra | Anillo redundante hacia las puertas |
| UPS de puerta | 12 | ≥ 2 h para nodo + switch + torniquetes | Corte de energía en una puerta |
| UPS de sala técnica | 2 | ≥ 2 h para servidores, núcleo y router | Corte en la sala técnica |
| Router con doble salida | 1 | Fibra + módem 4G/5G | Sincronización con AWS |
| Plan de datos 4G/5G | 1 | Bajo volumen (≈ 45.000 escaneos × ≈ 1 KB por evento) | Respaldo de internet |
| Rack, cableado, instalación | 1 lote | — | — |

### 9.2 Decisión de torniquetes y precios de referencia (actualizado 2026-11-04)

El profesor indicó que la solución del estadio es local tanto en A como en B. El grupo eligió **usar los torniquetes existentes** (F-14, opción 2) y conectar lectores QR fijos compatibles, en vez de comprar 48 cuerpos de torniquete. La autoridad contra doble ingreso sigue siendo el nodo de cada puerta; debe verificarse en sitio la compatibilidad de cada controladora con Wiegand/relé antes de instalar.

Los 48 torniquetes propios habrían costado COP 216,1 M solo por los cuerpos, sin lectores ni controladores, y no cabían en el presupuesto de B. La opción acordada elimina esa compra. La hoja final de Juan Pablo deja los lectores QR fijos con referencia pública de COP 334.000 por unidad y los demás equipos con precio, fuente, fecha y capturas en `entrega/evidencias/`. Estos son precios consultados, no ofertas vinculantes; confirmar stock, impuestos, instalación y garantía antes de comprar.

La capacidad de acceso sigue siendo la misma: con 48 carriles a 25 personas/minuto se procesan hasta 1.200/min, frente al pico de diseño de 1.500/min; se prevé una cola corta en el pico. El modelo de puerta no depende de la marca del torniquete mientras la interfaz entregue el identificador QR al nodo local.

**Decisiones finales de compra:**

- F-14: 48 lectores QR fijos sobre los torniquetes existentes; no se compran torniquetes propios.
- F-23: 12 terminales portátiles, uno por puerta, para accesibilidad y contingencia. Se acepta que no alcanzan para asistir dos carriles caídos en una misma puerta a la vez.
- F-24: fondo de reposición del 10 % anual del hardware desde el año 2, como supuesto de presupuesto ante la garantía limitada de precios de tienda; no sustituye una garantía escrita de cinco años.
- El presupuesto consolidado del estadio queda en ≈ COP 159,8 M el año 1 en ambos escenarios, incluyendo servidores, nodos, terminales, lectores, UPS, red, gabinete, energía y datos móviles. Los costos completos de A y B están en `entrega/costos_boletaya_final.xlsx`.

### 9.1 Sistema operativo y fin de soporte (regla de Miguel: al menos 5 años desde la compra)

Miguel dejó el sistema operativo de los servidores y del nodo de puerta sin definir y puso la regla de elegir uno con soporte de al menos 5 años desde la compra, o costear su actualización. Propuesta, con fechas consultadas el 2026-11-03 [D-15, D-16]. Supuesto mío: compra a inicios de 2027, por lo que 5 años llegan a inicios de 2032.

| Componente | Propuesta | Fin del soporte estándar | ¿Cubre 5 años desde 2027? | Qué hacer |
|---|---|---|---|---|
| Sistema operativo del servidor central y de los nodos de puerta | Ubuntu 26.04 LTS (lanzada en abril de 2026) | Mayo de 2031 | **No del todo** (≈ 4,4 años) | Contratar Ubuntu Pro (mantenimiento de seguridad ampliado hasta mayo de 2036) o planear el cambio de versión en 2031 |
| Alternativa | Ubuntu 24.04 LTS | Mayo de 2029 (ampliado hasta mayo de 2034) | No (≈ 2,4 años estándar) | Solo con Ubuntu Pro; no la recomiendo para equipo nuevo |
| Base local | PostgreSQL 18 | 14 de noviembre de 2030 | **No** (≈ 3,9 años) | Una migración a una versión mayor nueva en 2030; Miguel ya costea "migraciones de runtime", falta sumar esta |

Conclusiones:
1. **Ninguna combinación llega a 5 años sin acción extra.** El modelo incluye Ubuntu Pro durante el último año y una migración mayor de PostgreSQL en 2030.
2. **En el costo final:** se incluye una migración de PostgreSQL (24 h de DBA) y Ubuntu Pro para dos servidores y doce nodos activos durante el último año del horizonte; validar precio y clase de licencia con proveedor:

   El modelo final incluye una migración mayor de PostgreSQL (24 h de DBA) y, para el último año del horizonte, Ubuntu Pro con una hipótesis de dos servidores más doce workstations: USD 1.300 (COP 5,2 M). La clase de licencia de los nodos y la contratación deben confirmarse con Canonical/proveedor. No se incluye soporte 24/7.

3. **Lectores y torniquetes:** su firmware y soporte dependen del fabricante, que aún no está elegido. No lo verifiqué; queda como requisito de compra: soporte y repuestos del fabricante por 5 años como mínimo, por escrito.
4. **Alcance modelado:** 12 nodos activos y 2 servidores; los 3 nodos de repuesto no se cuentan como equipos activos con licencia en el año final.

Costos recurrentes a considerar: garantía y soporte de los equipos, reposición de lectores, el plan de datos, el personal técnico el día del evento y el transporte si los equipos se mueven entre estadios.

## 10. Referencias propias

| ID | Fuente | Qué respalda |
|---|---|---|
| D-05 | [PostgreSQL: Transaction Isolation (Read Committed)](https://www.postgresql.org/docs/current/transaction-iso.html) | Un `UPDATE` sobre una fila que otra transacción está actualizando **espera**; si la primera confirma, el `WHERE` **se vuelve a evaluar** sobre la versión nueva |
| D-06 | [PostgreSQL: Log-Shipping Standby Servers, §26.2.8 Synchronous Replication](https://www.postgresql.org/docs/current/warm-standby.html) | Cada confirmación espera a que el cambio esté escrito en el disco del primario y del respaldo; solo hay pérdida si ambos fallan a la vez |
| D-15 | [Ubuntu release cycle](https://ubuntu.com/about/release-cycle) | Ubuntu 26.04 LTS: mantenimiento estándar hasta mayo de 2031 y ampliado hasta mayo de 2036; 24.04 LTS: mayo de 2029 y mayo de 2034; las LTS reciben 5 años de mantenimiento estándar |
| D-16 | [PostgreSQL versioning policy](https://www.postgresql.org/support/versioning/) | Cada versión mayor recibe 5 años de soporte; PostgreSQL 18 llega a fin de vida el 14 de noviembre de 2030 |
| D-17 | [Ubuntu Pro pricing](https://ubuntu.com/pricing/pro) | Ubuntu Pro: USD 500 por servidor al año (máquinas virtuales ilimitadas) y USD 25 por escritorio al año; soporte 24/7 aparte |
| D-19 | [ZKTeco T2000, ficha técnica (TVC)](https://cdn.tvc.mx/media/1825683/Torniquete-T2000-ZKTECO-TVC-Ficha-Tecnica-Español.pdf) | Torniquete de trípode: 25 personas por minuto |
| D-20 | [Hikvision DS-K3G530X, ficha técnica](https://assets.hikvision.com/prd/normal/all/doc/m000125280/es-la/DS-K3G530X_Datasheet_20251027.pdf) | 30 a 60 personas por minuto según la forma de paso; 2 entradas Wiegand para lectores externos |
| D-21 | [Zebra TC22 en LDLC (España)](https://www.ldlc.com/es-es/ficha/PB00746032.html) | 940,95 EUR; Android 13, lector 2D SE4710, Wi-Fi 6 (referencia de orden de magnitud, no de Colombia) |

Consultadas el 2026-10-30 (D-05, D-06) y el 2026-11-03 (D-15 a D-17) y el 2026-11-04 (D-19 a D-21).
