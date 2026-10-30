# Ingreso al estadio sin internet

**Autor:** David · **Fecha:** 2026-10-30 · **Rúbrica:** Ingreso al estadio sin internet (2 puntos)
**Insumos:** `jacobo/modelo_datos.md` §3.5 (`bya_tickets`), `jacobo/arquitectura.md` §7. Referencias `[R-xx]` en `jacobo/referencias.md`; `[D-xx]` en `david/concurrencia.md` §9 y al final de este documento.

> **Idea central:** cada boleta tiene **una sola puerta dueña**, y cada puerta tiene **un solo nodo** que decide con una escritura atómica. Dos puertas no pueden aceptar la misma boleta porque solo una tiene autoridad sobre ella, y dentro de la puerta el nodo serializa los escaneos. No hace falta internet ni conexión entre puertas para que esto se cumpla.

---

## 1. Resumen

| Pregunta | Respuesta |
|---|---|
| ¿Qué pasa si se cae internet? | Nada visible. El ingreso funciona con datos locales; internet solo sirve para sincronizar |
| ¿Qué pasa si una puerta queda aislada de la red del estadio? | Sigue operando sola, porque ya tiene todo lo que necesita para sus boletas |
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
| E-R1 | **Boleta anulada (reembolso) sin internet:** el nodo no se entera y la deja entrar | Riesgo aceptado: se detecta en la sincronización (§7). Para reducirlo, cerrar reembolsos 2 h antes de abrir puertas |
| E-R2 | **Boleta vendida después de la última copia, sin internet:** el nodo no la conoce | Si el HMAC es válido, el evento coincide y la localidad es de esa puerta, **aceptar** y marcarla "fuera de copia". La firma garantiza que la emitió BoletaYa. Decisión del grupo |
| E-R3 | Asignación fija de puerta: si una puerta se llena, no se puede desviar gente a otra | El organizador puede reasignar una localidad a otra puerta **antes** del evento. Durante el evento, solo con el procedimiento manual de §6 |
| E-R4 | Clave HMAC robada de un nodo | Clave por evento, rotada después de cada uno; los nodos sin disco extraíble. Coordinar con Samuel |

## 9. Equipo para costear (para Juan Pablo)

Cantidades con los supuestos E-02 y E-03. **Los precios los pone Juan Pablo.**

| Equipo | Cantidad | Especificación mínima | Para qué |
|---|---|---|---|
| Servidor central | 2 | 1U, 8 núcleos, 32 GB RAM, 2 SSD en RAID 1, 2 fuentes | Primario y respaldo síncrono |
| Nodo de puerta | 12 + 3 de repuesto | Mini PC industrial sin ventilador, 8 GB RAM, SSD 128 GB, Ethernet | Una autoridad por puerta |
| Torniquete con lector QR fijo, Ethernet PoE | 48 | Lector 2D que lea pantallas de celular | 4 por puerta |
| Lector QR portátil | 24 | Android con lector 2D, Ethernet por base o Wi-Fi | 2 por puerta para filas de apoyo y accesibilidad |
| Switch PoE de puerta | 12 | 8 puertos PoE, 2 enlaces de subida | Conecta torniquetes y nodo |
| Switch de núcleo | 2 | 24 puertos, enlaces de fibra | Anillo redundante hacia las puertas |
| UPS de puerta | 12 | ≥ 2 h para nodo + switch + torniquetes | Corte de energía en una puerta |
| UPS de sala técnica | 2 | ≥ 2 h para servidores, núcleo y router | Corte en la sala técnica |
| Router con doble salida | 1 | Fibra + módem 4G/5G | Sincronización con AWS |
| Plan de datos 4G/5G | 1 | Bajo volumen (≈ 45.000 escaneos × ≈ 1 KB por evento) | Respaldo de internet |
| Rack, cableado, instalación | 1 lote | — | — |

Costos recurrentes a considerar: garantía y soporte de los equipos, reposición de lectores, el plan de datos, el personal técnico el día del evento y el transporte si los equipos se mueven entre estadios.

## 10. Referencias propias

| ID | Fuente | Qué respalda |
|---|---|---|
| D-05 | [PostgreSQL: Transaction Isolation (Read Committed)](https://www.postgresql.org/docs/current/transaction-iso.html) | Un `UPDATE` sobre una fila que otra transacción está actualizando **espera**; si la primera confirma, el `WHERE` **se vuelve a evaluar** sobre la versión nueva |
| D-06 | [PostgreSQL: Log-Shipping Standby Servers, §26.2.8 Synchronous Replication](https://www.postgresql.org/docs/current/warm-standby.html) | Cada confirmación espera a que el cambio esté escrito en el disco del primario y del respaldo; solo hay pérdida si ambos fallan a la vez |

Consultadas el 2026-10-30.
