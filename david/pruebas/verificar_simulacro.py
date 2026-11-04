"""
Verificador de invariantes para el simulacro de conmutación regional (Miguel, runbook 2b).

Se corre AL TERMINAR el simulacro, contra la región que quedó activa. Solo LEE: hace Scan y
GetItem con lectura fuerte; nunca escribe. Comprueba los criterios de éxito del plan de pruebas
de Miguel ("0 sillas con dos dueños; 0 pagos aprobados sin orden ni reembolso") y los del modo
desastre (alta_disponibilidad.md §5.0 y §5.2):

  1. Ninguna silla tiene boletas de dos órdenes distintas.          (doble venta, respuesta 5)
  2. Ninguna silla vendida (S) está sin dueño (so).
  3. Todo pago APPROVED tiene su orden en PAID, FULFILL_FAIL o REFUNDED.
  4. Toda orden PAID tiene todas sus sillas en S a su nombre y una boleta por silla.
  5. No quedan sillas congeladas por el incidente (lo = CONC#...), salvo las de pagos
     que Mercado Pago todavía tiene en proceso. Se listan para revisarlas a mano.
  6. Ningún intento del libro (bya_ledger) quedó en INTENT sin resolver.        (D-2b)

Uso:
  pip install boto3
  python verificar_simulacro.py --region us-east-2 [--evento 1234] [--incidente INC-1]

Requiere credenciales de AWS con permiso de LECTURA sobre las tablas. Sale con código 0 si no
hay violaciones y 1 si hay alguna. Escribe el detalle en verificacion_simulacro.json.
"""
import argparse
import json
import sys
import uuid

import boto3


def tid_de(oid, silla):
    """Debe ser la misma regla que la confirmación (concurrencia.md §5): UUIDv5(oid, silla)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{oid}#{silla}"))


def scan(ddb, tabla):
    items, kw = [], {}
    while True:
        r = ddb.scan(TableName=tabla, ConsistentRead=True, **kw)
        items += r["Items"]
        if "LastEvaluatedKey" not in r:
            return items
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]


def v(item, campo):
    x = item.get(campo, {})
    return x.get("S") or x.get("N")


def verificar(ddb, evento=None, incidente=None, tablas=None):
    t = {"seats": "bya_seats", "orders": "bya_orders", "tickets": "bya_tickets", "ledger": "bya_ledger"}
    t.update(tablas or {})
    errores, revisar = [], []

    seats = scan(ddb, t["seats"])
    if evento:
        seats = [s for s in seats if s["pk"]["S"].startswith(f"E{evento}#")]
    tickets = scan(ddb, t["tickets"])
    orders = scan(ddb, t["orders"])
    try:
        ledger = scan(ddb, t["ledger"])
    except ddb.exceptions.ResourceNotFoundException:
        ledger = None

    # 1. Boletas de dos órdenes para la misma silla
    por_silla = {}
    for tk in tickets:
        if "seat" in tk and "oid" in tk:
            por_silla.setdefault(v(tk, "seat"), set()).add(v(tk, "oid"))
    for silla, oids in por_silla.items():
        if len(oids) > 1:
            errores.append({"regla": 1, "silla": silla, "ordenes": sorted(oids)})

    # 2 y 5. Estado de las sillas
    for s in seats:
        nombre = s["pk"]["S"] + "/" + s["sk"]["S"]
        if v(s, "st") == "S" and not v(s, "so"):
            errores.append({"regla": 2, "silla": nombre})
        lo = v(s, "lo") or ""
        if v(s, "st") == "L" and lo.startswith("CONC#") and (incidente is None or lo == f"CONC#{incidente}"):
            revisar.append({"regla": 5, "silla": nombre, "congelada_por": lo,
                            "accion": "confirmar que su pago sigue in_process en Mercado Pago; si no, conciliar o liberar"})

    # 3 y 4. Pagos y órdenes
    estado_orden = {o["pk"]["S"]: o for o in orders if o["sk"]["S"] == "ORDER"}
    for o in orders:
        if o["sk"]["S"].startswith("PAY#") and v(o, "st") == "APPROVED":
            orden = estado_orden.get(o["pk"]["S"])
            if orden is None:
                errores.append({"regla": 3, "orden": o["pk"]["S"], "problema": "pago aprobado sin orden"})
            elif v(orden, "st") not in ("PAID", "FULFILL_FAIL", "REFUNDED"):
                errores.append({"regla": 3, "orden": o["pk"]["S"], "problema": f"pago aprobado con orden en {v(orden, 'st')}"})
    for pk, o in estado_orden.items():
        if v(o, "st") != "PAID" or "sil" not in o:
            continue
        oid = pk.split("#", 1)[1]
        for x in o["sil"]["L"]:
            loc, fila, nro = x["S"].split("|")
            key = {"pk": {"S": f"E{evento or v(o, 'eid')}#S{loc}#R{fila}"}, "sk": {"S": f"S{nro}"}}
            s = ddb.get_item(TableName=t["seats"], Key=key, ConsistentRead=True).get("Item")
            if not s or not (v(s, "st") == "S" and v(s, "so") == oid):
                errores.append({"regla": 4, "orden": oid, "silla": x["S"], "estado": v(s, "st") if s else "no existe"})
            tk = ddb.get_item(TableName=t["tickets"], Key={"pk": {"S": f"TKT#{tid_de(oid, x['S'])}"}, "sk": {"S": "T"}},
                              ConsistentRead=True).get("Item")
            if not tk:
                errores.append({"regla": 4, "orden": oid, "silla": x["S"], "problema": "sin boleta"})

    # 6. Libro de pagos
    if ledger is not None:
        for i in ledger:
            if v(i, "st") == "INTENT":
                revisar.append({"regla": 6, "intento": i["sk"]["S"], "accion": "sin id de pago: esperar la notificación de Mercado Pago o reembolsar"})

    return {"violaciones": errores, "para_revisar": revisar,
            "conteos": {"sillas": len(seats), "boletas": len(tickets), "items_ordenes": len(orders),
                        "intentos_libro": None if ledger is None else len(ledger)}}


def main():
    ap = argparse.ArgumentParser(description="Verificador de invariantes del simulacro (solo lectura)")
    ap.add_argument("--region", required=True, help="región que quedó activa, p. ej. us-east-2")
    ap.add_argument("--evento", help="eid del evento del simulacro, para no revisar otros")
    ap.add_argument("--incidente", help="identificador usado al congelar (CONC#<incidente>)")
    a = ap.parse_args()
    r = verificar(boto3.client("dynamodb", region_name=a.region), a.evento, a.incidente)
    with open("verificacion_simulacro.json", "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    print(f"Violaciones: {len(r['violaciones'])}  ·  Para revisar a mano: {len(r['para_revisar'])}  ·  {r['conteos']}")
    for e in r["violaciones"][:20]:
        print("  VIOLACIÓN", e)
    sys.exit(1 if r["violaciones"] else 0)


if __name__ == "__main__":
    main()
