#!/usr/bin/env python3
"""
Modelo de capacidad y volumetria - BoletaYa SAS (DynamoDB, AWS)
Autor: Jacobo (parte 5.1 / 5.4). Todas las cifras de los documentos de jacobo/ salen de este script.

Uso:  python3 -I modelo_capacidad.py            -> imprime las tablas en Markdown
Reglas:
  - DATO = viene del enunciado oficial.
  - SUPUESTO = lo define este grupo (se marca con A-xx y se documenta en capacidad_y_volumetria.md).
  - PRECIO = lista de precios oficial de AWS (API Price List), version 20260911124422 (DynamoDB),
             consultada el 2026-10-29. Ver precios/ y referencias.md.
"""
import math

GIB = 2 ** 30          # DynamoDB usa unidades binarias (1 GB = 1024 MB). Fuente: ServiceQuotas / Constraints.
KIB = 1024


def ceil(x):
    return math.ceil(x - 1e-12)


def fmt(n, d=0):
    if d == 0:
        return f"{round(n):,}".replace(",", ".")
    s = f"{n:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- DATOS DEL ENUNCIADO
G_USERS, G_TICKETS, G_QUEUE = 0.40, 0.30, 0.25
TICKETS_PER_ORDER = 2.5
REJECT_SHARE = 0.30
HOURS_DAY = 16
NORMAL_TICKETS_DAY = 8000
PRESALE_TICKETS, PRESALE_MIN, PRESALES_YEAR = 60000, 20, 25
QUEUE_Y1 = 250000
SCANS_BURST, SCANS_MIN = 45000, 90
LOCK_MIN = 8

# entidad: (bytes crudos, cantidad anio 1, clave de crecimiento)
RAW = {
    "usuarios": 1536,          # 1,5 KB
    "eventos": 4096,           # 4 KB
    "sillas": 100,
    "historial": 150,
    "ordenes": 2048,           # 2 KB
    "pagos": 1536,             # 1,5 KB
    "boletas": 1024,           # 1 KB
    "escaneos": 250,
    "cufe": 500,
    "auditoria": 300,
}
# Nota: el enunciado da "KB"; se toma 1 KB = 1024 B (convencion de DynamoDB) para el calculo de unidades.
# Para tamano de datos crudos se usa el mismo valor (diferencia 2,4 %, inmaterial).

Y1 = {
    "usuarios": 2_500_000,
    "eventos": 1_800,
    "ordenes": 1_600_000,
    "boletas": 4_000_000,
}
SEATS_PER_EVENT = 3000
HIST_PER_SEAT = 4
PAY_PER_ORDER = 1.3
SCANS_PER_TICKET = 1.2
CUFE_PER_ORDER = 1.0
AUDIT_PER_MONTH = 5_000_000

# ---------------------------------------------------------------- SUPUESTOS
G_EVENTS = 0.30       # A-01 eventos crecen como las boletas (si no, ocupacion > 100 % desde el anio 3; ver abajo)
G_AUDIT = 0.30        # A-02 auditoria crece con la actividad (boletas)
ITEM_OVERHEAD = 100   # A-03 sobrecarga de almacenamiento por item de tabla (AWS ya no publica la cifra; 100 B documentado para items de GSI)
GSI_OVERHEAD = 100    # DOCUMENTADO: GSI.html "100 bytes of overhead per index item"
# Retencion en linea (A-04, sujeta a validacion legal de Samuel/Miguel): anios
ONLINE_YEARS = {"usuarios": None, "eventos": 2, "sillas": 1, "historial": 2, "ordenes": 2, "pagos": 2,
                "boletas": 2, "escaneos": 1, "cufe": 2, "auditoria": 2}


def flows(n):
    """Cantidades por anio (flujo anual) para el anio n (1..5)."""
    g = lambda r: (1 + r) ** (n - 1)
    out = {}
    out["usuarios"] = round(Y1["usuarios"] * g(G_USERS))                # stock acumulado (A-05)
    out["eventos"] = round(Y1["eventos"] * g(G_EVENTS))
    out["sillas"] = out["eventos"] * SEATS_PER_EVENT
    out["historial"] = out["sillas"] * HIST_PER_SEAT
    out["ordenes"] = round(Y1["ordenes"] * g(G_TICKETS))
    out["pagos"] = round(out["ordenes"] * PAY_PER_ORDER)
    out["boletas"] = round(Y1["boletas"] * g(G_TICKETS))
    out["escaneos"] = round(out["boletas"] * SCANS_PER_TICKET)
    out["cufe"] = round(out["ordenes"] * CUFE_PER_ORDER)
    out["auditoria"] = round(AUDIT_PER_MONTH * 12 * g(G_AUDIT))
    return out


FL = {n: flows(n) for n in range(1, 6)}

# GSIs: (tabla logica, entidad base, bytes del item de indice SIN sobrecarga, nombre)
HUMAN_AUDIT_SHARE = 0.05   # A-07: 5 % de los registros de auditoria son acciones de personas (admin, DBA, soporte) -> indice DISPERSO
GSIS = [
    ("usuarios", "usuarios", 85, "gsi_email", 1.0),
    ("eventos", "eventos", 170, "gsi_org_fecha", 1.0),
    ("ordenes", "ordenes", 152, "gsi_usuario", 1.0),
    ("ordenes", "ordenes", 160, "gsi_evento", 1.0),
    ("boletas", "boletas", 170, "gsi_evento_boleta", 1.0),
    ("auditoria", "auditoria", 110, "gsi_actor", HUMAN_AUDIT_SHARE),
]
# gsi_pago_pendiente es dispersa (solo mientras el pago esta pendiente): almacenamiento en estado estable ~ 0.


def online_count(ent, n):
    k = ONLINE_YEARS[ent]
    if k is None:
        return FL[n][ent]
    return sum(FL[j][ent] for j in range(max(1, n - k + 1), n + 1))


def archived_count(ent, n):
    k = ONLINE_YEARS[ent]
    if k is None:
        return 0
    return sum(FL[j][ent] for j in range(1, n - k + 1))


# ---------------------------------------------------------------- ALMACENAMIENTO
def storage_table():
    rows = []
    for n in range(1, 6):
        raw_flow = {e: FL[n][e] * RAW[e] for e in RAW}
        raw_online = {e: online_count(e, n) * RAW[e] for e in RAW}
        billed_online = {e: online_count(e, n) * (RAW[e] + ITEM_OVERHEAD) for e in RAW}
        idx_online = sum(online_count(be, n) * fr * (b + GSI_OVERHEAD) for (_, be, b, _, fr) in GSIS)
        arch = {e: archived_count(e, n) * RAW[e] for e in RAW}
        rows.append((n, raw_flow, raw_online, billed_online, idx_online, arch))
    return rows


# ---------------------------------------------------------------- PRECIOS (USD) - AWS Price List API
PRICE = {
    "sa-east-1": dict(wru=0.9375e-6, rru=0.1875e-6, wcu_h=0.000975, rcu_h=0.000195, stor=0.375, stor_ia=0.15,
                      wru_ia=1.172e-6, rru_ia=0.2345e-6, pitr=0.30, exp=0.15, s3=0.0405, athena_tb=9.0,
                      ec_m7g_large_h=0.18, ec_t4g_medium_h=0.0976, cf_req=2.2e-6, cf_gb=0.11),
    "us-east-1": dict(wru=0.625e-6, rru=0.125e-6, wcu_h=0.00065, rcu_h=0.00013, stor=0.25, stor_ia=0.10,
                      wru_ia=0.78e-6, rru_ia=0.155e-6, pitr=0.20, exp=0.10, s3=0.023, athena_tb=5.0,
                      ec_m7g_large_h=0.1264, ec_t4g_medium_h=0.052, cf_req=2.2e-6, cf_gb=0.11),
}
# CloudFront: precio de la lista global, usagetype SA-* (Sudamerica) - SUPUESTO A-06: Colombia factura en la zona "South America".
TRM = 4000.0  # COP/USD, fija por el enunciado

# ---------------------------------------------------------------- CARGA POR ORDEN (unidades de escritura)
# Tamanos de item para redondeo (1 KB para escrituras, 4 KB para lecturas)
WU = lambda b: max(1, ceil(b / KIB))
RU = lambda b: max(1, ceil(b / (4 * KIB)))


def wru_per_order(seats=TICKETS_PER_ORDER, k_rej=1.0, fail_per_ok=0.0, abandon=0.0, ticket_wu=None,
                  idx_tx_factor=1.0, audit_per_order=2.0):
    """Devuelve dict con WRU por orden COMPLETADA, desglosado por tabla (base) y por indice (gsi).
    k_rej: rechazos por orden que tiene rechazo (el 30 % del enunciado). fail_per_ok: transacciones de bloqueo fallidas por bloqueo exitoso.
    abandon: fraccion de ordenes iniciadas que nunca se pagan (A_ratio = abandon/(1-abandon) por orden completada)."""
    tw = ticket_wu if ticket_wu is not None else WU(RAW["boletas"])
    seat_w, ord_w, pay_w, cnt_w = WU(RAW["sillas"]), WU(RAW["ordenes"]), WU(RAW["pagos"]), 1
    inv_w, hist_w, aud_w = WU(RAW["cufe"]), WU(RAW["historial"]), WU(RAW["auditoria"])
    a_ratio = abandon / (1 - abandon) if abandon < 1 else 0
    declines = REJECT_SHARE * k_rej
    out = {k: 0.0 for k in ["sillas", "ordenes", "limites", "contadores", "boletas", "historial", "auditoria",
                            "gsi_ordenes", "gsi_pendientes", "gsi_boletas"]}
    # --- TX de bloqueo (TransactWriteItems): sillas A->L, orden PENDIENTE, limite antibot. Cada item x2 (preparar+confirmar)
    lock = {"sillas": seats * seat_w * 2, "ordenes": ord_w * 2, "limites": cnt_w * 2}
    # --- TX de confirmacion: sillas L->S, orden PAGADA, intento APROBADO, contador +n, boletas, referencia factura
    conf = {"sillas": seats * seat_w * 2, "ordenes": (ord_w + pay_w + inv_w) * 2, "contadores": cnt_w * 2,
            "boletas": seats * tw * 2}
    for d in (lock, conf):
        for k, v in d.items():
            out[k] += v
    # indices (propagacion GSI: 1 WRU por entrada de indice; idx_tx_factor=2 para sensibilidad)
    out["gsi_ordenes"] += 2 * idx_tx_factor              # alta orden: gsi_usuario + gsi_evento
    out["gsi_ordenes"] += 2 * idx_tx_factor              # cambio de estado (status proyectado) en ambos indices
    out["gsi_pendientes"] += 1 * idx_tx_factor           # alta intento pendiente (dispersa)
    out["gsi_pendientes"] += 1 * idx_tx_factor           # baja al aprobar (dentro de la tx de confirmacion)
    out["gsi_pendientes"] += 1 * idx_tx_factor           # alta referencia de factura PENDIENTE (dentro de la tx de confirmacion)
    out["gsi_pendientes"] += 1                           # baja al emitirse la factura (UpdateItem no transaccional)
    out["ordenes"] += inv_w                              # UpdateItem INV -> EMITIDA con CUFE (proveedor DIAN, via SQS)
    out["gsi_boletas"] += seats * 1 * idx_tx_factor      # una entrada gsi_evento_boleta por boleta
    # intento aprobado: alta del intento (no transaccional, 1x)
    out["ordenes"] += pay_w
    # rechazos: alta intento + actualizar a DECLINADO + 2 escrituras de indice dispersa
    out["ordenes"] += declines * (pay_w * 2)
    out["gsi_pendientes"] += declines * 2
    # historial derivado por Streams: A->L y L->S
    out["historial"] += seats * 2 * hist_w
    # auditoria
    out["auditoria"] += audit_per_order * aud_w
    # fallos de bloqueo (transaccion cancelada igual consume capacidad - doc transaction-apis)
    out["sillas"] += fail_per_ok * lock["sillas"]
    out["ordenes"] += fail_per_ok * lock["ordenes"]
    out["limites"] += fail_per_ok * lock["limites"]
    # abandonadas: bloqueo exitoso + alta orden + historial A->L + auditoria 1
    for k, v in lock.items():
        out[k] += a_ratio * v
    out["gsi_ordenes"] += a_ratio * 2 * idx_tx_factor
    out["historial"] += a_ratio * seats * hist_w
    out["auditoria"] += a_ratio * aud_w
    out["_total"] = sum(v for k, v in out.items())
    return out


SCEN = {
    "Minimo":    dict(k_rej=1.0, fail_per_ok=0.0, abandon=0.0),
    "Planificacion": dict(k_rej=1.0, fail_per_ok=2.0, abandon=0.30),
    "Estres":    dict(k_rej=3.0, fail_per_ok=8.0, abandon=0.50, ticket_wu=2, idx_tx_factor=2.0, audit_per_order=5.0),
}


def rru_per_order(fail_per_ok=0.0, polls=10, seats=TICKETS_PER_ORDER):
    """Lecturas por orden en RRU. Lecturas fuertes de ORDEN (2 KB -> 1 RRU) x3, boletas BatchGet fuerte, sondeo eventual, precheck de silla."""
    ord_r = RU(RAW["ordenes"])
    strong = 3 * ord_r * 1.0
    tickets = seats * RU(RAW["boletas"]) * 1.0
    poll = polls * ord_r * 0.5
    precheck = (1 + fail_per_ok) * seats * 0.5
    return strong + tickets + poll + precheck


def main():
    P = []
    pr = P.append
    # -------------------------------------------------- 1. volumetria (cantidades)
    pr("## T1. Cantidad de registros por anio (formulas en capacidad_y_volumetria.md)\n")
    pr("| Entidad | Tam./registro (B) | Anio 1 | Anio 2 | Anio 3 | Anio 4 | Anio 5 |")
    pr("|---|---:|---:|---:|---:|---:|---:|")
    for e in RAW:
        pr(f"| {e} | {RAW[e]} | " + " | ".join(fmt(FL[n][e]) for n in range(1, 6)) + " |")
    # ocupacion
    pr("\n**Ocupacion implicita (boletas / sillas)** con eventos creciendo a 30 % vs. eventos constantes:\n")
    pr("| Anio | Boletas | Sillas (eventos +30 %) | Ocupacion | Sillas (eventos constantes) | Ocupacion |")
    pr("|---|---:|---:|---:|---:|---:|")
    for n in range(1, 6):
        b = FL[n]["boletas"]; s = FL[n]["sillas"]; s0 = Y1["eventos"] * SEATS_PER_EVENT
        pr(f"| {n} | {fmt(b)} | {fmt(s)} | {b / s * 100:.1f} % | {fmt(s0)} | {b / s0 * 100:.1f} % |")

    # -------------------------------------------------- 2. almacenamiento
    pr("\n## T2. Almacenamiento (GiB) - flujo anual crudo, en linea facturado, indices y archivado en S3\n")
    pr("| Anio | Crudo del anio (flujo) | En linea: crudo | En linea: facturado (crudo+sobrecarga) | Indices GSI | Total en linea (tablas+GSI) | Archivado acumulado S3 (crudo) |")
    pr("|---|---:|---:|---:|---:|---:|---:|")
    st = storage_table()
    for (n, rf, ro, bo, idx, ar) in st:
        pr(f"| {n} | {fmt(sum(rf.values()) / GIB, 1)} | {fmt(sum(ro.values()) / GIB, 1)} | {fmt(sum(bo.values()) / GIB, 1)} | "
           f"{fmt(idx / GIB, 1)} | {fmt((sum(bo.values()) + idx) / GIB, 1)} | {fmt(sum(ar.values()) / GIB, 1)} |")
    pr("\n**Desglose por entidad en el anio 5 (GiB):**\n")
    n = 5
    rf, ro, bo, idx, ar = st[4][1], st[4][2], st[4][3], st[4][4], st[4][5]
    pr("| Entidad | Crudo anual | En linea crudo | En linea facturado | GSI de la entidad | Archivado S3 |")
    pr("|---|---:|---:|---:|---:|---:|")
    for e in RAW:
        gi = sum(online_count(be, n) * fr * (b + GSI_OVERHEAD) for (_, be, b, _, fr) in GSIS if be == e)
        pr(f"| {e} | {fmt(rf[e] / GIB, 2)} | {fmt(ro[e] / GIB, 2)} | {fmt(bo[e] / GIB, 2)} | {fmt(gi / GIB, 2)} | {fmt(ar[e] / GIB, 2)} |")

    # -------------------------------------------------- 3. carga normal
    pr("\n## T3. Operacion normal (8.000 boletas/dia, 16 h) - anio 1 y anio 5\n")
    pr("| Metrica | Anio 1 | Anio 5 | Formula |")
    pr("|---|---:|---:|---|")
    for lab, f in [("Boletas/dia", lambda n: NORMAL_TICKETS_DAY * 1.3 ** (n - 1))]:
        pass
    def nrm(n):
        t = NORMAL_TICKETS_DAY * (1 + G_TICKETS) ** (n - 1)
        o = t / TICKETS_PER_ORDER
        m = SCEN["Minimo"]
        w = wru_per_order(**{**m, "abandon": 0.30})["_total"]
        r = rru_per_order(0.0)
        return dict(t=t, th=t / HOURS_DAY, tm=t / HOURS_DAY / 60, o=o, oh=o / HOURS_DAY, om=o / HOURS_DAY / 60, os=o / HOURS_DAY / 3600,
                    w=w, wps=o * w / (HOURS_DAY * 3600), r=r, rps=o * r / (HOURS_DAY * 3600), wday=o * w)
    a, b = nrm(1), nrm(5)
    rowsN = [
        ("Boletas por dia", "t", 0, "8.000 x 1,3^(n-1)"),
        ("Boletas por hora", "th", 1, "dia / 16"),
        ("Boletas por minuto", "tm", 2, "hora / 60"),
        ("Ordenes por dia", "o", 0, "boletas / 2,5"),
        ("Ordenes por hora", "oh", 1, "ordenes dia / 16"),
        ("Ordenes por minuto", "om", 2, "hora / 60"),
        ("Ordenes por segundo", "os", 4, "hora / 3600"),
        ("WRU por orden (camino feliz + 30 % abandono)", "w", 1, "T4 (escenario Minimo con abandono 30 %)"),
        ("WRU por segundo promedio", "wps", 2, "ordenes/s x WRU/orden"),
        ("WRU por dia", "wday", 0, "ordenes dia x WRU/orden"),
        ("RRU por orden", "r", 2, "T4b"),
        ("RRU por segundo promedio", "rps", 2, "ordenes/s x RRU/orden"),
    ]
    for lab, k, d, f in rowsN:
        pr(f"| {lab} | {fmt(a[k], d)} | {fmt(b[k], d)} | {f} |")
    pr("\nSensibilidad a la frase 'unos 100 ventas por minuto' del contexto del enunciado: 100 ordenes/min = 1,67 ordenes/s -> "
       f"{fmt(100/60*wru_per_order(**{**SCEN['Minimo'], 'abandon':0.3})['_total'],1)} WRU/s (todavia << 4.000 WRU/s de una tabla nueva on-demand).")

    # -------------------------------------------------- 4. WRU por orden
    pr("\n## T4. WRU por orden completada, por escenario (desglose por tabla)\n")
    names = ["sillas", "ordenes", "limites", "contadores", "boletas", "historial", "auditoria", "gsi_ordenes", "gsi_pendientes", "gsi_boletas"]
    pr("| Escenario | " + " | ".join(names) + " | **Total WRU/orden** |")
    pr("|---|" + "---:|" * (len(names) + 1))
    W = {}
    for s, p in SCEN.items():
        w = wru_per_order(**p); W[s] = w
        pr(f"| {s} | " + " | ".join(fmt(w[k], 2) for k in names) + f" | **{fmt(w['_total'], 2)}** |")
    pr("\n**T4b. RRU por orden:**\n")
    pr("| Escenario | RRU/orden |")
    pr("|---|---:|")
    R = {}
    for s, p in SCEN.items():
        R[s] = rru_per_order(p["fail_per_ok"]); pr(f"| {s} | {fmt(R[s], 2)} |")

    # -------------------------------------------------- 5. preventa
    orders = PRESALE_TICKETS / TICKETS_PER_ORDER
    secs = PRESALE_MIN * 60
    pr("\n## T5. Preventa grande - tasas\n")
    pr("| Concepto | Valor | Formula |")
    pr("|---|---:|---|")
    pr(f"| Boletas por minuto (promedio) | {fmt(PRESALE_TICKETS / PRESALE_MIN)} | 60.000 / 20 |")
    pr(f"| Boletas por segundo (promedio) | {fmt(PRESALE_TICKETS / secs, 1)} | 60.000 / 1.200 |")
    pr(f"| Ordenes en la preventa | {fmt(orders)} | 60.000 / 2,5 |")
    pr(f"| Ordenes por segundo (promedio) | {fmt(orders / secs, 1)} | 24.000 / 1.200 |")
    for k_, lab in [(1, "1 rechazo"), (2, "2 rechazos"), (3, "3 rechazos")]:
        att = 1 + REJECT_SHARE * k_
        pr(f"| Intentos de pago por orden si el 30 % tiene {lab} | {fmt(att,2)} | 1 + 0,30 x k |")
    pr(f"| Intentos de pago totales (k=1) | {fmt(orders * 1.3)} | 24.000 x 1,3 |")
    pr(f"| Intentos de pago por segundo (k=1) | {fmt(orders * 1.3 / secs, 1)} | /1.200 |")
    pr(f"| Intentos ADICIONALES (rechazados), k=1 | {fmt(orders * 0.3)} | 24.000 x 0,30 |")
    pr("\n**T5b. Escrituras de la preventa (WRU) por escenario y factor de rafaga:**\n")
    pr("| Escenario | WRU/orden | WRU totales preventa | WRU/s promedio (x1) | WRU/s rafaga x3 | WRU/s instantaneo x5 | +25 % margen sobre x5 |")
    pr("|---|---:|---:|---:|---:|---:|---:|")
    for s in SCEN:
        w = W[s]["_total"]; tot = orders * w; avg = tot / secs
        pr(f"| {s} | {fmt(w, 1)} | {fmt(tot)} | {fmt(avg)} | {fmt(avg * 3)} | {fmt(avg * 5)} | {fmt(avg * 5 * 1.25)} |")
    pr("\n**T5c. WRU/s por tabla en la rafaga x5, escenario Planificacion y Estres (comparar con 4.000 WRU/s de tabla on-demand nueva; 1.000 WRU/s por particion):**\n")
    pr("| Tabla/indice | Planificacion x5 | Estres x5 |")
    pr("|---|---:|---:|")
    for k in names:
        a1 = orders / secs * 5 * W["Planificacion"][k]; a2 = orders / secs * 5 * W["Estres"][k]
        pr(f"| {k} | {fmt(a1)} | {fmt(a2)} |")
    pr("\n**T5d. RRU/s en la preventa:**\n")
    pr("| Fuente | RRU/s | Formula |")
    pr("|---|---:|---|")
    for s in ("Planificacion", "Estres"):
        pr(f"| Ordenes ({s}, x5) | {fmt(orders / secs * 5 * R[s])} | ordenes/s x5 x RRU/orden |")
    seats_ev = 45000; rows_ev = ceil(seats_ev / 50); per_row_kb = 50 * RAW["sillas"] / KIB
    rr = ceil(per_row_kb / 4) * 0.5   # eventual
    for r_int in (2, 5):
        pr(f"| Constructor de mapa (estadio 45.000 sillas, {rows_ev} filas x {rr:.0f} RRU, refresco cada {r_int} s) | {fmt(rows_ev * rr / r_int)} | filas x RRU/fila / intervalo |")
    pr(f"| Contadores: BatchGet fuerte de 16 fragmentos x 20 localidades x 1 lectura/s | {fmt(16 * 20)} | 16 x 20 x 1 RRU |")
    pr(f"| Contadores: TransactGetItems 16 fragmentos x 20 localidades x 1/s | {fmt(16 * 20 * 2)} | x2 (transaccional) |")

    # -------------------------------------------------- 6. mapa de sillas
    pr("\n## T6. Mapa de sillas - 3 escenarios (anio 1) y proyeccion de la cola\n")
    pr("| Anio | Personas en cola (250.000 x 1,25^(n-1)) |")
    pr("|---|---:|")
    for n in range(1, 6):
        pr(f"| {n} | {fmt(QUEUE_Y1 * (1 + G_QUEUE) ** (n - 1))} |")
    sec_kb = 2250 * 100 / KIB     # una localidad de 2.250 sillas x 100 B (consulta directa a la base)
    direct_rru = ceil(sec_kb / 4) * 0.5
    pr(f"\nConsulta DIRECTA a la base de una localidad de 2.250 sillas: {sec_kb:.0f} KiB -> {direct_rru:.1f} RRU (eventual) por solicitud (supera 1 MB? no: {sec_kb:.0f} KiB < 1 MiB).\n")
    pr("| Escenario | Usuarios | Intervalo de consulta | Solicitudes/s | RRU/s si TODO fuera a DynamoDB | x cuota 40.000/tabla | Solicitudes en 20 min |")
    pr("|---|---:|---:|---:|---:|---:|---:|")
    MAPS = [("Moderada", 250000, 30), ("Alta", 250000, 10), ("Extrema", 250000, 3)]
    for nm, u, i in MAPS:
        rps = u / i
        pr(f"| {nm} | {fmt(u)} | {i} s | {fmt(rps)} | {fmt(rps * direct_rru)} | {rps * direct_rru / 40000:.1f}x | {fmt(rps * 1200)} |")
    u5 = QUEUE_Y1 * 1.25 ** 4
    pr(f"| Extrema, anio 5 | {fmt(u5)} | 3 s | {fmt(u5 / 3)} | {fmt(u5 / 3 * direct_rru)} | {u5 / 3 * direct_rru / 40000:.1f}x | {fmt(u5 / 3 * 1200)} |")
    pr("\n**T6b. Con arquitectura de lectura (instantaneas en CDN): carga residual en DynamoDB y costo CloudFront por preventa**\n")
    pr("Supuestos: carga util por consulta = 3 KB (resumen + mapa de bits de la localidad; 45.000 sillas x 2 bits = 11 KiB todo el estadio); TTL 2 s; 21 objetos (resumen + 20 localidades).\n")
    pr("| Escenario | Solicitudes/s | Ancho de banda (Mbps) | GB por preventa (20 min) | CloudFront solicitudes (USD/preventa, SA) | CloudFront salida (USD/preventa, SA) | Total USD/preventa | Total USD/anio (25) | Lecturas a DynamoDB (RRU/s) |")
    pr("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    payload_kb = 3.0
    for nm, u, i in MAPS + [("Extrema anio 5", u5, 3)]:
        rps = u / i
        gb = rps * payload_kb * 1000 / 1e9 * 1200   # GB decimal de transferencia (CloudFront factura GB decimales)
        mbps = rps * payload_kb * 8 / 1000
        req = rps * 1200 * PRICE["sa-east-1"]["cf_req"]
        out = gb * PRICE["sa-east-1"]["cf_gb"]
        pr(f"| {nm} | {fmt(rps)} | {fmt(mbps)} | {fmt(gb, 1)} | {fmt(req, 1)} | {fmt(out, 1)} | {fmt(req + out, 1)} | {fmt((req + out) * 25, 0)} | {fmt(rows_ev * rr / 2)} |")

    # -------------------------------------------------- 7. costos de las opciones de capacidad
    pr("\n## T7. Costo anual de DynamoDB (solo throughput) por opcion, region y anio - USD (planificacion)\n")
    pr("Normal: abandono 30 %, sin fallos de bloqueo. Preventa: escenario Planificacion con fallos de bloqueo creciendo con la cola (x1,25^(n-1)).\n")
    for reg in ("sa-east-1", "us-east-1"):
        p = PRICE[reg]
        pr(f"\n### {reg}\n")
        pr("| Anio | WRU normal (M) | WRU preventas (M) | RRU totales (M) | A) On-demand USD | B1) Provisionado fijo al pico USD | B2) Programado (base + 75 h de pico) USD | Umbral de uso para que provisionado gane |")
        pr("|---|---:|---:|---:|---:|---:|---:|---:|")
        for n in range(1, 6):
            tkt_day = NORMAL_TICKETS_DAY * 1.3 ** (n - 1)
            ord_norm = tkt_day / TICKETS_PER_ORDER * 365
            w_norm = ord_norm * wru_per_order(**{**SCEN["Minimo"], "abandon": 0.30})["_total"]
            pcfg = {**SCEN["Planificacion"]}
            pcfg["fail_per_ok"] = 2.0 * 1.25 ** (n - 1)
            w_pre = PRESALES_YEAR * orders * wru_per_order(**pcfg)["_total"]
            r_norm = ord_norm * rru_per_order(0.0)
            r_pre = PRESALES_YEAR * orders * rru_per_order(pcfg["fail_per_ok"])
            r_map = PRESALES_YEAR * (secs / 2) * rows_ev * rr         # constructor de mapa
            r_dash = PRESALES_YEAR * secs * 16 * 20
            r_tot = r_norm + r_pre + r_map + r_dash
            w_tot = w_norm + w_pre
            od = w_tot * p["wru"] + r_tot * p["rru"]
            # provisionado fijo: capacidad al pico planificada x5 +25 %
            peak_w = orders / secs * 5 * wru_per_order(**pcfg)["_total"] * 1.25
            peak_r = (orders / secs * 5 * rru_per_order(pcfg["fail_per_ok"]) + rows_ev * rr / 2 + 16 * 20) * 1.25
            b1 = (peak_w * p["wcu_h"] + peak_r * p["rcu_h"]) * 8760
            base_w = max(50.0, 3 * (ord_norm / (365 * HOURS_DAY * 3600)) * wru_per_order(**{**SCEN["Minimo"], "abandon": 0.30})["_total"])
            base_r = max(50.0, 3 * (ord_norm / (365 * HOURS_DAY * 3600)) * rru_per_order(0.0))
            hours_peak = PRESALES_YEAR * 3
            b2 = (base_w * p["wcu_h"] + base_r * p["rcu_h"]) * 8760 + ((peak_w - base_w) * p["wcu_h"] + (peak_r - base_r) * p["rcu_h"]) * hours_peak
            thr = p["wcu_h"] / (3600 * p["wru"])
            pr(f"| {n} | {fmt(w_norm / 1e6, 1)} | {fmt(w_pre / 1e6, 1)} | {fmt(r_tot / 1e6, 1)} | {fmt(od)} | {fmt(b1)} | {fmt(b2)} | {thr * 100:.1f} % |")
        # capacidades de pico anio 1 y 5
    pr("\n**Capacidad de pico a provisionar (planificacion x5 + 25 %):**\n")
    pr("| Anio | WCU pico | RCU pico | WCU base normal | RCU base normal |")
    pr("|---|---:|---:|---:|---:|")
    for n in range(1, 6):
        pcfg = {**SCEN["Planificacion"]}; pcfg["fail_per_ok"] = 2.0 * 1.25 ** (n - 1)
        peak_w = orders / secs * 5 * wru_per_order(**pcfg)["_total"] * 1.25
        peak_r = (orders / secs * 5 * rru_per_order(pcfg["fail_per_ok"]) + rows_ev * rr / 2 + 16 * 20) * 1.25
        ord_norm = NORMAL_TICKETS_DAY * 1.3 ** (n - 1) / TICKETS_PER_ORDER * 365
        bw = max(50.0, 3 * (ord_norm / (365 * HOURS_DAY * 3600)) * wru_per_order(**{**SCEN["Minimo"], "abandon": 0.30})["_total"])
        br = max(50.0, 3 * (ord_norm / (365 * HOURS_DAY * 3600)) * rru_per_order(0.0))
        pr(f"| {n} | {fmt(peak_w)} | {fmt(peak_r)} | {fmt(bw)} | {fmt(br)} |")

    # -------------------------------------------------- 8. almacenamiento: costo y clase de tabla
    pr("\n## T8. Costo mensual de almacenamiento anio 5 (USD/mes) por clase de tabla\n")
    n = 5
    ro5, bo5 = st[4][2], st[4][3]
    pr("| Entidad | GiB facturado en linea | Standard sa-east-1 | Standard-IA sa-east-1 | Standard us-east-1 | Standard-IA us-east-1 |")
    pr("|---|---:|---:|---:|---:|---:|")
    tot = 0
    for e in RAW:
        g = bo5[e] / GIB
        pr(f"| {e} | {fmt(g, 2)} | {fmt(g * PRICE['sa-east-1']['stor'], 1)} | {fmt(g * PRICE['sa-east-1']['stor_ia'], 1)} | {fmt(g * PRICE['us-east-1']['stor'], 1)} | {fmt(g * PRICE['us-east-1']['stor_ia'], 1)} |")
    gtot = sum(bo5.values()) / GIB + st[4][4] / GIB
    pr(f"\nTotal tablas+GSI anio 5 = {fmt(gtot, 1)} GiB. PITR (35 dias) factura aprox. el tamano de la tabla: {fmt(gtot * PRICE['sa-east-1']['pitr'], 1)} USD/mes (sa-east-1) vs {fmt(gtot * PRICE['us-east-1']['pitr'], 1)} (us-east-1).")

    # -------------------------------------------------- 9. cola y cuota
    pr("\n## T9. Little: compradores concurrentes en la fase transaccional\n")
    for sess in (120, 240, 480):
        pr(f"- Sesion de compra {sess} s x {orders / secs:.0f} ordenes/s promedio = {fmt(orders / secs * sess)} compradores simultaneos (x5 rafaga: {fmt(orders / secs * 5 * sess)})")

    # -------------------------------------------------- 10. contencion de contadores
    pr("\n## T10. Contencion del contador por fragmentos (modelo ilustrativo, NO medicion)\n")
    pr("lambda = ordenes/s en rafaga sobre una localidad; T = tiempo que una transaccion retiene el item (supuesto; no publicado por AWS). rho = lambda/N x T = probabilidad aproximada de encontrar el item ocupado.\n")
    pr("| N fragmentos | lambda por fragmento (100 ord/s) | rho con T=10 ms | rho con T=25 ms | rho con T=50 ms |")
    pr("|---:|---:|---:|---:|---:|")
    for N in (1, 4, 8, 16, 32):
        l = 100 / N
        pr(f"| {N} | {l:.1f}/s | {l * 0.010:.2f} | {l * 0.025:.2f} | {l * 0.050:.2f} |")
    pr("\nLimite duro por item: 1.000 WRU/s -> 500 transacciones/s sobre un mismo item (2 WRU c/u).")

    # -------------------------------------------------- 11. region
    pr("\n## T11. Comparacion de precios unitarios por region (USD, lista oficial 2026-09-11)\n")
    pr("| Concepto | sa-east-1 | us-east-1 | Diferencia sa vs us |")
    pr("|---|---:|---:|---:|")
    for lab, k, scale in [("1 M WRU on-demand", "wru", 1e6), ("1 M RRU on-demand", "rru", 1e6), ("WCU-hora", "wcu_h", 1),
                          ("RCU-hora", "rcu_h", 1), ("GB-mes Standard", "stor", 1), ("GB-mes PITR", "pitr", 1),
                          ("TB escaneado Athena", "athena_tb", 1), ("Nodo cache.m7g.large Valkey /h", "ec_m7g_large_h", 1)]:
        a_, b_ = PRICE["sa-east-1"][k] * scale, PRICE["us-east-1"][k] * scale
        pr(f"| {lab} | {a_:.6g} | {b_:.6g} | +{(a_ / b_ - 1) * 100:.0f} % |")

    # -------------------------------------------------- T7b: costo anual total de la capa de datos (on-demand)
    pr("\n## T7b. Costo anual total de la capa DynamoDB + archivo (USD, on-demand, Standard) - anio 1..5\n")
    pr("Incluye: throughput (T7-A), almacenamiento de fin de anio x 12 meses (conservador), PITR (~tamano de tablas x 12), exportaciones incrementales diarias (2 x flujo anual de tablas con TTL), archivo S3 Standard. NO incluye Streams/Lambda/Athena/KMS/CloudWatch (pendientes, ver documento).\n")
    pr("| Region | Anio | Throughput | Almacenamiento | PITR | Exportaciones | S3 archivo | **Total USD/anio** | **Total COP/anio (TRM 4.000)** |")
    pr("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for reg in ("sa-east-1", "us-east-1"):
        p = PRICE[reg]
        for n in range(1, 6):
            tkt_day = NORMAL_TICKETS_DAY * 1.3 ** (n - 1)
            ord_norm = tkt_day / TICKETS_PER_ORDER * 365
            w_norm = ord_norm * wru_per_order(**{**SCEN["Minimo"], "abandon": 0.30})["_total"]
            pcfg = {**SCEN["Planificacion"]}; pcfg["fail_per_ok"] = 2.0 * 1.25 ** (n - 1)
            w_pre = PRESALES_YEAR * orders * wru_per_order(**pcfg)["_total"]
            r_tot = ord_norm * rru_per_order(0.0) + PRESALES_YEAR * orders * rru_per_order(pcfg["fail_per_ok"]) \
                + PRESALES_YEAR * (secs / 2) * rows_ev * rr + PRESALES_YEAR * secs * 16 * 20
            thr = (w_norm + w_pre) * p["wru"] + r_tot * p["rru"]
            rf, ro, bo, idx, ar = st[n - 1][1], st[n - 1][2], st[n - 1][3], st[n - 1][4], st[n - 1][5]
            gib_tot = (sum(bo.values()) + idx) / GIB
            stor = gib_tot * p["stor"] * 12
            pitr = gib_tot * p["pitr"] * 12
            ttl_ents = ["historial", "ordenes", "pagos", "boletas", "cufe", "escaneos", "auditoria"]
            exp = 2 * sum(rf[e] for e in ttl_ents) / GIB * p["exp"]
            s3 = sum(ar.values()) / GIB * p["s3"] * 12
            tot = thr + stor + pitr + exp + s3
            pr(f"| {reg} | {n} | {fmt(thr)} | {fmt(stor)} | {fmt(pitr)} | {fmt(exp)} | {fmt(s3)} | **{fmt(tot)}** | **{fmt(tot * TRM)}** |")

    # -------------------------------------------------- T10b: dimensionamiento de fragmentos
    pr("\n## T10b. Cuantos fragmentos de contador hacen falta (limite duro 1.000 WRU/s por item; 2 WRU por transaccion)\n")
    pr("| Escenario (rafaga x5, todas las ventas en UNA localidad) | WRU/s sobre el contador (2 WRU x ordenes/s) | Fragmentos minimos con 50 % de holgura | Con N=1 |")
    pr("|---|---:|---:|---|")
    for nm, mult in (("x1 promedio", 1), ("x3", 3), ("x5 instantaneo", 5), ("x5 y 3 reintentos de confirmacion por orden", 15)):
        w = orders / secs * mult * 2
        pr(f"| {nm} | {fmt(w)} | {max(1, ceil(w / 500))} | {'supera' if w > 1000 else 'cabe'} el limite de 1.000 WRU/s |")

    # -------------------------------------------------- T12: componentes auxiliares (ordenes de magnitud para Juan Pablo)
    pr("\n## T12. Componentes auxiliares - cantidades y orden de magnitud (anio 1)\n")
    api_calls = orders * 20 + orders * 2.0 * 3 + 250000 * 2
    pr(f"- Llamadas dinamicas al API por preventa: ordenes x 20 + intentos de bloqueo fallidos x 3 + 2 llamadas de admision por persona en cola = {fmt(api_calls)} (supuesto de 20 llamadas por orden: bloqueo, pago x1,3, confirmacion, sondeos). Pico x5: {fmt(orders / secs * 5 * 20)} req/s (cuota por defecto de API Gateway: 10.000 req/s por cuenta y region).")
    for reg in ("sa-east-1", "us-east-1"):
        http = {"sa-east-1": 1.59e-6, "us-east-1": 1.00e-6}[reg]
        pr(f"- API Gateway HTTP API en {reg}: {fmt(api_calls * http, 2)} USD por preventa; {fmt(api_calls * http * 25, 0)} USD/anio por las 25 preventas (primeros 300 M solicitudes/mes) + trafico normal.")
        pr(f"- ElastiCache Valkey 2 nodos cache.m7g.large 24x7 en {reg}: {fmt(2 * PRICE[reg]['ec_m7g_large_h'] * 8760, 0)} USD/anio (precio de nodo; no incluye SyncDurability ni copias).")
    pr(f"- Publicacion de instantaneas a S3: 21 objetos x (1.200 s / 2 s) = {21 * 600} PUT por preventa por evento activo.")

    # -------------------------------------------------- T2b: crudo/facturado/indices por entidad y anio
    pr("\n## T2b. Datos crudos del anio (GiB) por entidad y anio (flujo anual; usuarios = existencias)\n")
    pr("| Entidad | Anio 1 | Anio 2 | Anio 3 | Anio 4 | Anio 5 |")
    pr("|---|---:|---:|---:|---:|---:|")
    for e in RAW:
        pr(f"| {e} | " + " | ".join(fmt(FL[n][e] * RAW[e] / GIB, 2) for n in range(1, 6)) + " |")
    pr("\n**T2c. Sobrecarga de indices GSI en linea por anio (GiB) y por indice, y espacio total facturado en linea por entidad (tabla + sus GSI)**\n")
    pr("| Indice (entidad base) | Bytes por entrada (sin sobrecarga) + 100 | Anio 1 | Anio 2 | Anio 3 | Anio 4 | Anio 5 |")
    pr("|---|---:|---:|---:|---:|---:|---:|")
    for (_, be, b, nm, fr) in GSIS:
        pr(f"| {nm} ({be}) | {b} + {GSI_OVERHEAD} | " + " | ".join(fmt(online_count(be, n) * fr * (b + GSI_OVERHEAD) / GIB, 2) for n in range(1, 6)) + " |")
    pr("\n**T2d. Espacio total facturado en linea (tabla + GSI) por entidad y anio (GiB)**\n")
    pr("| Entidad | Anio 1 | Anio 2 | Anio 3 | Anio 4 | Anio 5 |")
    pr("|---|---:|---:|---:|---:|---:|")
    for e in RAW:
        vals = []
        for n in range(1, 6):
            t = online_count(e, n) * (RAW[e] + ITEM_OVERHEAD)
            g = sum(online_count(be, n) * fr * (b + GSI_OVERHEAD) for (_, be, b, _, fr) in GSIS if be == e)
            vals.append(fmt((t + g) / GIB, 2))
        pr(f"| {e} | " + " | ".join(vals) + " |")

    # -------------------------------------------------- T5e: sensibilidad
    pr("\n## T5e. Sensibilidad del WRU por orden (planificacion como base)\n")
    pr("| Variante | WRU/orden | WRU/s promedio (20 ord/s) | WRU/s x5 | Intentos de pago por orden |")
    pr("|---|---:|---:|---:|---:|")
    base = dict(SCEN["Planificacion"])
    variants = [("Base (k=1, f=2, abandono 30 %)", {}),
                ("k=2 rechazos por orden afectada", {"k_rej": 2.0}),
                ("k=3 rechazos por orden afectada", {"k_rej": 3.0}),
                ("Boleta de 2 KB (2 WRU en vez de 1)", {"ticket_wu": 2}),
                ("Indices en transaccion cuentan doble", {"idx_tx_factor": 2.0}),
                ("f=8 bloqueos fallidos por exitoso", {"fail_per_ok": 8.0}),
                ("Abandono 50 %", {"abandon": 0.50}),
                ("5 auditorias por orden", {"audit_per_order": 5.0})]
    for nm, ch in variants:
        cfg = {**base, **ch}
        w = wru_per_order(**cfg)["_total"]
        att = 1 + REJECT_SHARE * cfg.get("k_rej", 1.0)
        pr(f"| {nm} | {fmt(w, 1)} | {fmt(orders / secs * w)} | {fmt(orders / secs * 5 * w)} | {fmt(att, 2)} |")

    # -------------------------------------------------- T7c: costo por preventa
    pr("\n## T7c. Costo de DynamoDB por preventa (throughput, anio 1, escenario Planificacion, on-demand)\n")
    w1 = orders * wru_per_order(**SCEN["Planificacion"])["_total"]
    r1 = orders * rru_per_order(2.0) + secs * rows_ev * rr / 2 + secs * 16 * 20
    pr("| Concepto | Unidades | sa-east-1 USD | us-east-1 USD |")
    pr("|---|---:|---:|---:|")
    pr(f"| Escrituras (WRU) | {fmt(w1)} | {fmt(w1 * PRICE['sa-east-1']['wru'], 2)} | {fmt(w1 * PRICE['us-east-1']['wru'], 2)} |")
    pr(f"| Lecturas (RRU): ordenes + constructor de mapa + tablero | {fmt(r1)} | {fmt(r1 * PRICE['sa-east-1']['rru'], 2)} | {fmt(r1 * PRICE['us-east-1']['rru'], 2)} |")
    pr(f"| **Total por preventa** | | **{fmt(w1 * PRICE['sa-east-1']['wru'] + r1 * PRICE['sa-east-1']['rru'], 2)}** | **{fmt(w1 * PRICE['us-east-1']['wru'] + r1 * PRICE['us-east-1']['rru'], 2)}** |")
    pw = 10546.4; pr_ = 2744
    for reg in ("sa-east-1", "us-east-1"):
        p = PRICE[reg]
        c = ((pw - 50) * p["wcu_h"] + (pr_ - 50) * p["rcu_h"]) * 3
        pr(f"\nProvisionado programado: sobrecosto de 3 h de capacidad de pico por preventa en {reg}: {fmt(c, 2)} USD (WCU 10.546 / RCU 2.744 menos la base de 50/50).")
    pr(f"\nUtilizacion media si se provisionara fijo al pico todo el anio (anio 1): {fmt(123472685.7 / (10546.4 * 8760 * 3600) * 100, 3)} % (umbral de equilibrio 28,9 %).")

    print("\n".join(P))


if __name__ == "__main__":
    main()
