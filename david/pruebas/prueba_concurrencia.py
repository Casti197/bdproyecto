"""
Pruebas de las transacciones de BoletaYa contra moto (simulador de AWS en Python).

Qué demuestra: que las expresiones de condición son válidas para la API de DynamoDB
y que deciden lo que dice el diseño (concurrencia.md §3 y §5, anexo escenarios 1 a 3,
alta_disponibilidad.md §5).

Qué NO demuestra: el comportamiento bajo carga real, la latencia, ni los errores
TransactionConflict de DynamoDB. moto ejecuta las transacciones una a la vez en memoria.

Uso:  python3 prueba_concurrencia.py
"""
import hashlib
import uuid

import boto3
from botocore.exceptions import ClientError
from moto import mock_aws

SKEW = 2
LOCK_S = 480
MAX_POR_USUARIO = 10
NSH = 8
EID = "1234"
REGION = "us-east-1"
CONC = "CONC#INC-1"   # dueño de las sillas congeladas por el incidente (alta_disponibilidad.md §5.0)

resultados = []


def ok(nombre, condicion, detalle=""):
    resultados.append((nombre, bool(condicion), detalle))
    print(("PASA " if condicion else "FALLA") + "  " + nombre + ("  | " + detalle if detalle else ""))


# ---------------------------------------------------------------- utilidades
def S(v):
    return {"S": str(v)}


def N(v):
    return {"N": str(v)}


def key_silla(loc, fila, nro):
    return {"pk": S(f"E{EID}#S{loc}#R{fila}"), "sk": S(f"S{nro}")}


def tid_de(oid, silla):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{oid}#{silla}"))


def token(oid, fase):
    return hashlib.sha256(f"{oid}#{fase}".encode()).hexdigest()[:36]


def motivos(e):
    return [r.get("Code", "None") for r in e.response.get("CancellationReasons", [])]


def crear_tablas(ddb):
    for t in ["bya_seats", "bya_orders", "bya_counters", "bya_tickets"]:
        ddb.create_table(
            TableName=t,
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"},
                       {"AttributeName": "sk", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"},
                                  {"AttributeName": "sk", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )


def sembrar_sillas(ddb, loc="07", fila="12", nros=range(20, 30)):
    for n in nros:
        ddb.put_item(TableName="bya_seats",
                     Item={**key_silla(loc, fila, n), "st": S("A"), "v": N(0)})


def silla(ddb, loc, fila, nro):
    return ddb.get_item(TableName="bya_seats", Key=key_silla(loc, fila, nro),
                        ConsistentRead=True).get("Item")


def get(ddb, tabla, pk, sk):
    return ddb.get_item(TableName=tabla, Key={"pk": S(pk), "sk": S(sk)},
                        ConsistentRead=True).get("Item")


# ---------------------------------------------------------------- fase 1: bloqueo
def bloquear(ddb, uid, oid, sillas, now, con_token=True):
    """concurrencia.md §3. sillas = [(loc, fila, nro), ...]"""
    k = len(sillas)
    vals_silla = {":lx": N(now + LOCK_S), ":oid": S(oid), ":uno": N(1),
                  ":a": S("A"), ":l": S("L"), ":vencido_antes_de": N(now - SKEW)}
    acciones = []
    for (loc, fila, nro) in sillas:
        acciones.append({"Update": {
            "TableName": "bya_seats", "Key": key_silla(loc, fila, nro),
            "ConditionExpression": "attribute_exists(pk) AND (st = :a OR (st = :l AND lx < :vencido_antes_de))",
            "UpdateExpression": "SET st = :l, lx = :lx, lo = :oid ADD v :uno",
            "ExpressionAttributeValues": vals_silla}})
    acciones.append({"Put": {
        "TableName": "bya_orders",
        "Item": {"pk": S(f"ORD#{oid}"), "sk": S("ORDER"), "st": S("PENDING"), "uid": S(uid),
                 "eid": S(EID), "lx": N(now + LOCK_S),
                 "sil": {"L": [S(f"{l}|{f}|{n}") for (l, f, n) in sillas]}},
        "ConditionExpression": "attribute_not_exists(pk)"}})
    acciones.append({"Update": {
        "TableName": "bya_counters", "Key": {"pk": S(f"LIM#E{EID}#U{uid}"), "sk": S("P")},
        "ConditionExpression": "attribute_not_exists(n) OR n <= :max_menos_k",
        "UpdateExpression": "SET n = if_not_exists(n, :cero) + :k",
        "ExpressionAttributeValues": {":max_menos_k": N(MAX_POR_USUARIO - k), ":cero": N(0), ":k": N(k)}}})
    kw = {"ClientRequestToken": token(oid, "LOCK")} if con_token else {}
    try:
        ddb.transact_write_items(TransactItems=acciones, **kw)
        return "OK", []
    except ClientError as e:
        if e.response["Error"]["Code"] == "TransactionCanceledException":
            m = motivos(e)
            # Defensa sin depender del token: si la orden ya existe, la creó un intento
            # anterior de esta misma orden (el oid es único) y, por atomicidad, ese intento
            # también bloqueó todas las sillas y descontó el cupo.
            if m[len(sillas)] == "ConditionalCheckFailed":
                orden = get(ddb, "bya_orders", f"ORD#{oid}", "ORDER")
                if orden and orden["uid"]["S"] == uid:
                    return "OK_YA_APLICADO", m
            return "CANCELADA", m
        raise


def sillas_de(orden):
    return [tuple(x["S"].split("|")) for x in orden["sil"]["L"]]


# ---------------------------------------------------------------- fase 3: confirmación
def confirmar(ddb, oid, nn, gtx, now, con_token=True):
    """concurrencia.md §5"""
    orden = get(ddb, "bya_orders", f"ORD#{oid}", "ORDER")
    acciones, tids, por_loc = [], [], {}
    for (loc, fila, nro) in sillas_de(orden):
        tid = tid_de(oid, f"{loc}|{fila}|{nro}")
        tids.append(tid)
        por_loc[loc] = por_loc.get(loc, 0) + 1
        acciones.append({"Update": {
            "TableName": "bya_seats", "Key": key_silla(loc, fila, nro),
            "ConditionExpression": "st = :l AND lo = :oid",
            "UpdateExpression": "SET st = :s, so = :oid, tk = :tid ADD v :uno",
            "ExpressionAttributeValues": {":l": S("L"), ":s": S("S"), ":oid": S(oid),
                                          ":tid": S(tid), ":uno": N(1)}}})
        acciones.append({"Put": {
            "TableName": "bya_tickets",
            "Item": {"pk": S(f"TKT#{tid}"), "sk": S("T"), "st": S("VALID"), "oid": S(oid),
                     "seat": S(f"{loc}|{fila}|{nro}")},
            "ConditionExpression": "attribute_not_exists(pk)"}})
    acciones.append({"Update": {
        "TableName": "bya_orders", "Key": {"pk": S(f"ORD#{oid}"), "sk": S("ORDER")},
        "ConditionExpression": "st = :pending",
        "UpdateExpression": "SET st = :paid, tkt = :tids",
        "ExpressionAttributeValues": {":pending": S("PENDING"), ":paid": S("PAID"),
                                      ":tids": {"L": [S(t) for t in tids]}}}})
    acciones.append({"Update": {
        "TableName": "bya_orders", "Key": {"pk": S(f"ORD#{oid}"), "sk": S(f"PAY#{nn:02d}")},
        "ConditionExpression": "st IN (:initiated, :unknown)",
        "UpdateExpression": "SET st = :approved, gtx = :gtx REMOVE g3pk, g3sk",
        "ExpressionAttributeValues": {":initiated": S("INITIATED"), ":unknown": S("UNKNOWN"),
                                      ":approved": S("APPROVED"), ":gtx": S(gtx)}}})
    sh = int(hashlib.md5(oid.encode()).hexdigest(), 16) % NSH
    for loc, n in por_loc.items():
        acciones.append({"Update": {
            "TableName": "bya_counters", "Key": {"pk": S(f"CNT#E{EID}#S{loc}"), "sk": S(f"SH#{sh:02d}")},
            "UpdateExpression": "ADD sold :n", "ExpressionAttributeValues": {":n": N(n)}}})
    acciones.append({"Put": {
        "TableName": "bya_orders",
        "Item": {"pk": S(f"ORD#{oid}"), "sk": S("INV#1"), "st": S("PENDING")},
        "ConditionExpression": "attribute_not_exists(pk)"}})
    kw = {"ClientRequestToken": token(oid, "CONFIRM")} if con_token else {}
    try:
        ddb.transact_write_items(TransactItems=acciones, **kw)
        return "PAID", []
    except ClientError as e:
        if e.response["Error"]["Code"] != "TransactionCanceledException":
            raise
        m = motivos(e)
        orden = get(ddb, "bya_orders", f"ORD#{oid}", "ORDER")
        if orden["st"]["S"] == "PAID":
            return "PAID_YA", m
        # otro tomó una silla: FULFILL_FAIL + pago APPROVED + liberar las demás + reembolso
        ddb.transact_write_items(TransactItems=[
            {"Update": {"TableName": "bya_orders", "Key": {"pk": S(f"ORD#{oid}"), "sk": S("ORDER")},
                        "ConditionExpression": "st = :pending", "UpdateExpression": "SET st = :ff",
                        "ExpressionAttributeValues": {":pending": S("PENDING"), ":ff": S("FULFILL_FAIL")}}},
            {"Update": {"TableName": "bya_orders", "Key": {"pk": S(f"ORD#{oid}"), "sk": S(f"PAY#{nn:02d}")},
                        "ConditionExpression": "st IN (:initiated, :unknown)",
                        "UpdateExpression": "SET st = :approved, gtx = :gtx",
                        "ExpressionAttributeValues": {":initiated": S("INITIATED"), ":unknown": S("UNKNOWN"),
                                                      ":approved": S("APPROVED"), ":gtx": S(gtx)}}}])
        for (loc, fila, nro) in sillas_de(orden):
            try:
                ddb.update_item(TableName="bya_seats", Key=key_silla(loc, fila, nro),
                                ConditionExpression="st = :l AND lo = :oid",
                                UpdateExpression="SET st = :a REMOVE lx, lo",
                                ExpressionAttributeValues={":l": S("L"), ":a": S("A"), ":oid": S(oid)})
            except ClientError:
                pass
        return "FULFILL_FAIL", m


def registrar_pago(ddb, oid, nn):
    ddb.put_item(TableName="bya_orders",
                 Item={"pk": S(f"ORD#{oid}"), "sk": S(f"PAY#{nn:02d}"), "st": S("INITIATED"),
                       "g3pk": S("PEND#0"), "g3sk": S(oid)},
                 ConditionExpression="attribute_not_exists(pk)")


# ---------------------------------------------------------------- modo desastre
def confirmar_desastre(ddb, cobro, now):
    """alta_disponibilidad.md §5.2. cobro = dict(oid, nn, gtx, uid, sillas=[(loc,fila,nro)], monto)"""
    oid, nn = cobro["oid"], cobro["nn"]
    for _ in range(3):
        orden = get(ddb, "bya_orders", f"ORD#{oid}", "ORDER")
        pago = get(ddb, "bya_orders", f"ORD#{oid}", f"PAY#{nn:02d}")
        inv = get(ddb, "bya_orders", f"ORD#{oid}", "INV#1")
        conflicto, acciones = False, []
        for (loc, fila, nro) in cobro["sillas"]:
            s = silla(ddb, loc, fila, nro)
            st = s["st"]["S"]
            mia = st == "S" and s.get("so", {}).get("S") == oid
            libre = st == "A" or (st == "L" and (s.get("lo", {}).get("S") in (oid, CONC)
                                                or int(s["lx"]["N"]) < now - SKEW))
            if not (mia or libre):
                conflicto = True
            if not mia:
                tid = tid_de(oid, f"{loc}|{fila}|{nro}")
                acciones.append({"Update": {
                    "TableName": "bya_seats", "Key": key_silla(loc, fila, nro),
                    "ConditionExpression": "(st = :a) OR (st = :l AND (lo = :oid OR lo = :conc OR lx < :vencido_antes_de)) OR (st = :s AND so = :oid)",
                    "UpdateExpression": "SET st = :s, so = :oid, tk = :tid REMOVE lx, lo ADD v :uno",
                    "ExpressionAttributeValues": {":a": S("A"), ":l": S("L"), ":s": S("S"), ":oid": S(oid), ":conc": S(CONC),
                                                  ":vencido_antes_de": N(now - SKEW), ":tid": S(tid), ":uno": N(1)}}})
            tid = tid_de(oid, f"{loc}|{fila}|{nro}")
            if not get(ddb, "bya_tickets", f"TKT#{tid}", "T"):
                acciones.append({"Put": {
                    "TableName": "bya_tickets",
                    "Item": {"pk": S(f"TKT#{tid}"), "sk": S("T"), "st": S("VALID"), "oid": S(oid),
                             "seat": S(f"{loc}|{fila}|{nro}")},
                    "ConditionExpression": "attribute_not_exists(pk)"}})
        if conflicto:
            return "REEMBOLSO"
        sil = {"L": [S(f"{l}|{f}|{n}") for (l, f, n) in cobro["sillas"]]}
        if orden is None:
            acciones.append({"Put": {
                "TableName": "bya_orders",
                "Item": {"pk": S(f"ORD#{oid}"), "sk": S("ORDER"), "st": S("PAID"), "uid": S(cobro["uid"]),
                         "eid": S(EID), "sil": sil, "tot": N(cobro["monto"])},
                "ConditionExpression": "attribute_not_exists(pk)"}})
        elif orden["st"]["S"] != "PAID":
            acciones.append({"Update": {
                "TableName": "bya_orders", "Key": {"pk": S(f"ORD#{oid}"), "sk": S("ORDER")},
                "ConditionExpression": "st IN (:pending, :expired)",
                "UpdateExpression": "SET st = :paid, sil = :sil",
                "ExpressionAttributeValues": {":pending": S("PENDING"), ":expired": S("EXPIRED"),
                                              ":paid": S("PAID"), ":sil": sil}}})
        if pago is None:
            acciones.append({"Put": {
                "TableName": "bya_orders",
                "Item": {"pk": S(f"ORD#{oid}"), "sk": S(f"PAY#{nn:02d}"), "st": S("APPROVED"),
                         "gtx": S(cobro["gtx"])},
                "ConditionExpression": "attribute_not_exists(pk)"}})
        elif pago["st"]["S"] != "APPROVED":
            acciones.append({"Update": {
                "TableName": "bya_orders", "Key": {"pk": S(f"ORD#{oid}"), "sk": S(f"PAY#{nn:02d}")},
                "ConditionExpression": "st IN (:initiated, :unknown)",
                "UpdateExpression": "SET st = :approved, gtx = :gtx REMOVE g3pk, g3sk",
                "ExpressionAttributeValues": {":initiated": S("INITIATED"), ":unknown": S("UNKNOWN"),
                                              ":approved": S("APPROVED"), ":gtx": S(cobro["gtx"])}}})
        if inv is None:
            acciones.append({"Put": {
                "TableName": "bya_orders", "Item": {"pk": S(f"ORD#{oid}"), "sk": S("INV#1"), "st": S("PENDING")},
                "ConditionExpression": "attribute_not_exists(pk)"}})
        if not acciones:
            return "YA_COMPLETA"
        try:
            ddb.transact_write_items(TransactItems=acciones, ClientRequestToken=token(oid, "CONFIRM-D"))
            return "CONFIRMADA"
        except ClientError as e:
            if e.response["Error"]["Code"] != "TransactionCanceledException":
                raise
    return "ERROR_REVISAR_A_MANO"


def congelar_sillas_en_duda(ddb, pagos, T):
    """alta_disponibilidad.md §5.0. pagos = lista de dicts como los devuelve la pasarela."""
    congeladas = 0
    for p in pagos:
        if p["status"] in ("rejected", "cancelled"):
            continue
        for (loc, fila, nro) in p["sillas"]:
            try:
                ddb.update_item(TableName="bya_seats", Key=key_silla(loc, fila, nro),
                                ConditionExpression="st <> :s",
                                UpdateExpression="SET st = :l, lo = :conc, lx = :lejos ADD v :uno",
                                ExpressionAttributeValues={":s": S("S"), ":l": S("L"), ":conc": S(CONC),
                                                           ":lejos": N(T + 86400), ":uno": N(1)})
                congeladas += 1
            except ClientError as e:
                if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                    raise
    return congeladas


def liberar_congeladas(ddb, sillas):
    for (loc, fila, nro) in sillas:
        try:
            ddb.update_item(TableName="bya_seats", Key=key_silla(loc, fila, nro),
                            ConditionExpression="st = :l AND lo = :conc",
                            UpdateExpression="SET st = :a REMOVE lx, lo ADD v :uno",
                            ExpressionAttributeValues={":l": S("L"), ":conc": S(CONC), ":a": S("A"), ":uno": N(1)})
        except ClientError as e:
            if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise


# ---------------------------------------------------------------- verificador (para el simulacro)
def verificar_invariantes(ddb):
    """Lo que se revisa al final del simulacro de Miguel: 0 sillas con dos dueños,
    0 boletas sin silla vendida, 0 órdenes PAID incompletas."""
    def scan(t):
        items, kw = [], {}
        while True:
            r = ddb.scan(TableName=t, ConsistentRead=True, **kw)
            items += r["Items"]
            if "LastEvaluatedKey" not in r:
                return items
            kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]

    seats, tickets, orders = scan("bya_seats"), scan("bya_tickets"), scan("bya_orders")
    errores = []
    asiento_de = {}
    for s in seats:
        nombre = s["pk"]["S"] + "/" + s["sk"]["S"]
        if s["st"]["S"] == "S" and "so" not in s:
            errores.append(f"silla vendida sin dueño: {nombre}")
    por_silla = {}
    for t in tickets:
        por_silla.setdefault(t["seat"]["S"], set()).add(t["oid"]["S"])
    for seat, oids in por_silla.items():
        if len(oids) > 1:
            errores.append(f"silla {seat} con boletas de {len(oids)} órdenes: {sorted(oids)}")
    pagos = {}
    for o in orders:
        if o["sk"]["S"].startswith("PAY#") and o["st"]["S"] == "APPROVED":
            pagos[o["pk"]["S"]] = True
    estado = {o["pk"]["S"]: o for o in orders if o["sk"]["S"] == "ORDER"}
    for pk in pagos:
        o = estado.get(pk)
        if o is None:
            errores.append(f"pago aprobado sin orden: {pk}")
        elif o["st"]["S"] not in ("PAID", "FULFILL_FAIL", "REFUNDED"):
            errores.append(f"pago aprobado con orden en {o['st']['S']}: {pk}")
    for pk, o in estado.items():
        if o["st"]["S"] == "PAID":
            oid = pk.split("#", 1)[1]
            for x in o["sil"]["L"]:
                loc, fila, nro = x["S"].split("|")
                s = silla(ddb, loc, fila, nro)
                if not (s["st"]["S"] == "S" and s.get("so", {}).get("S") == oid):
                    errores.append(f"orden PAID {oid} con silla {x['S']} en {s['st']['S']}")
                if not get(ddb, "bya_tickets", f"TKT#{tid_de(oid, x['S'])}", "T"):
                    errores.append(f"orden PAID {oid} sin boleta de {x['S']}")
    return errores


# ---------------------------------------------------------------- pruebas
@mock_aws
def main():
    ddb = boto3.client("dynamodb", region_name=REGION)
    crear_tablas(ddb)
    sembrar_sillas(ddb)
    S24 = ("07", "12", 24)

    print("\n== Sintaxis: las condiciones originales con aritmética ==")
    for nombre, cond, vals in [
        ("lx < :now - :skew", "st = :l AND lx < :now - :skew", {":l": S("L"), ":now": N(100), ":skew": N(2)}),
        ("n + :k <= :max", "attribute_not_exists(n) OR n + :k <= :max", {":k": N(1), ":max": N(10)}),
    ]:
        try:
            ddb.update_item(TableName="bya_seats", Key=key_silla(*S24), ConditionExpression=cond,
                            UpdateExpression="SET v = v", ExpressionAttributeValues=vals)
            ok(f"'{nombre}' rechazada por la API", False, "moto la aceptó")
        except ClientError as e:
            ok(f"'{nombre}' rechazada por la API", e.response["Error"]["Code"] == "ValidationException",
               e.response["Error"]["Code"])
        except ValueError as e:
            # moto no traduce este error a ValidationException; AWS sí lo hace [D-01]
            ok(f"'{nombre}' rechazada (moto no la puede interpretar)", True, str(e)[:60])

    print("\n== Escenario 1: dos clientes, la misma silla ==")
    r_ana = bloquear(ddb, "ana", "O-ANA", [S24], now=0)
    r_beto = bloquear(ddb, "beto", "O-BETO", [S24], now=0)
    ok("Ana bloquea S24", r_ana[0] == "OK")
    ok("Beto es rechazado por condición en la acción de S24", r_beto[0] == "CANCELADA" and r_beto[1][0] == "ConditionalCheckFailed", str(r_beto[1]))
    ok("La orden de Beto no existe", get(ddb, "bya_orders", "ORD#O-BETO", "ORDER") is None)
    ok("El cupo de Beto no se descontó", get(ddb, "bya_counters", f"LIM#E{EID}#Ubeto", "P") is None)
    ok("S24 sigue siendo de Ana", silla(ddb, *S24)["lo"]["S"] == "O-ANA")

    print("\n== Escenario 1b: todo o nada con varias sillas ==")
    r = bloquear(ddb, "caro", "O-CARO", [("07", "12", 23), S24, ("07", "12", 25)], now=1)
    ok("Caro pide S23, S24, S25: se cancela todo", r[0] == "CANCELADA", str(r[1]))
    ok("S23 y S25 siguen libres", silla(ddb, "07", "12", 23)["st"]["S"] == "A" and silla(ddb, "07", "12", 25)["st"]["S"] == "A")
    ok("CancellationReasons señala solo la segunda acción", r[1][:3] == ["None", "ConditionalCheckFailed", "None"], str(r[1][:3]))

    print("\n== Reintento del bloqueo cuando la respuesta se perdió (escenario 3b) ==")
    # moto no implementa ClientRequestToken; se prueba la segunda defensa, que no depende de él
    r = bloquear(ddb, "ana", "O-ANA", [S24], now=5)
    ok("Repetir el bloqueo de Ana se reconoce como ya aplicado, no como silla ocupada", r[0] == "OK_YA_APLICADO", str(r))
    lim = get(ddb, "bya_counters", f"LIM#E{EID}#Uana", "P")
    ok("El cupo de Ana se descontó una sola vez", lim["n"]["N"] == "1", f"n = {lim['n']['N']}")

    print("\n== :skew protege al dueño cerca del vencimiento (lx = 480) ==")
    r = bloquear(ddb, "beto", "O-BETO-482", [S24], now=482)
    ok("En t = 482 (480 < 480 es falso) Beto no puede tomarla", r[0] == "CANCELADA")
    r = bloquear(ddb, "beto", "O-BETO", [S24], now=483, con_token=False)
    ok("En t = 483 (480 < 481) Beto sí la toma", r[0] == "OK", str(r))

    print("\n== Escenario 2b: venció y otro la tomó, Ana paga tarde ==")
    registrar_pago(ddb, "O-ANA", 1)
    r = confirmar(ddb, "O-ANA", 1, "gtx-ana", now=495)
    ok("La confirmación de Ana falla y termina en FULFILL_FAIL", r[0] == "FULFILL_FAIL", str(r[1]))
    ok("No se creó boleta para Ana", get(ddb, "bya_tickets", f"TKT#{tid_de('O-ANA', '07|12|24')}", "T") is None)
    ok("El pago de Ana queda APPROVED (para reembolso)", get(ddb, "bya_orders", "ORD#O-ANA", "PAY#01")["st"]["S"] == "APPROVED")
    ok("El contador no se incrementó", not any(
        get(ddb, "bya_counters", f"CNT#E{EID}#S07", f"SH#{i:02d}") for i in range(NSH)))
    ok("S24 sigue siendo de Beto", silla(ddb, *S24)["lo"]["S"] == "O-BETO")
    registrar_pago(ddb, "O-BETO", 1)
    ok("Beto confirma con normalidad", confirmar(ddb, "O-BETO", 1, "gtx-beto", now=530)[0] == "PAID")
    ok("S24 vendida a Beto", silla(ddb, *S24)["so"]["S"] == "O-BETO")

    print("\n== Escenario 2a: venció pero nadie la tomó ==")
    S26 = ("07", "12", 26)
    bloquear(ddb, "dani", "O-DANI", [S26], now=1000)
    registrar_pago(ddb, "O-DANI", 1)
    ok("Dani confirma en t = 1495, con el bloqueo vencido", confirmar(ddb, "O-DANI", 1, "gtx-dani", now=1495)[0] == "PAID")

    print("\n== Escenario 3: confirmación repetida (webhook duplicado, sin token) ==")
    r = confirmar(ddb, "O-DANI", 1, "gtx-dani", now=1500, con_token=False)
    ok("La segunda confirmación no cambia nada y reconoce PAID", r[0] == "PAID_YA", str(r[1]))
    tickets = ddb.scan(TableName="bya_tickets")["Items"]
    ok("Hay una sola boleta de S26", sum(1 for t in tickets if t["seat"]["S"] == "07|12|26") == 1)

    print("\n== Antibots: máximo 10 sillas por usuario y evento ==")
    sembrar_sillas(ddb, fila="13", nros=range(1, 15))
    r = bloquear(ddb, "eva", "O-EVA1", [("07", "13", n) for n in range(1, 9)], now=2000)
    ok("Eva bloquea 8", r[0] == "OK")
    r = bloquear(ddb, "eva", "O-EVA2", [("07", "13", n) for n in range(9, 12)], now=2001)
    ok("Eva no puede sumar 3 más (8 + 3 > 10)", r[0] == "CANCELADA" and r[1][-1] == "ConditionalCheckFailed", str(r[1]))
    r = bloquear(ddb, "eva", "O-EVA3", [("07", "13", n) for n in range(9, 11)], now=2002)
    ok("Eva sí puede sumar 2 (8 + 2 = 10)", r[0] == "OK")

    print("\n== Contención: 30 clientes por la misma silla (en serie) ==")
    # moto no es seguro con hilos, así que no sirve para medir concurrencia real.
    # Esto solo comprueba que la condición deja un único dueño sin importar cuántos lo intenten.
    sembrar_sillas(ddb, fila="14", nros=[1])
    res = [bloquear(ddb, f"u{i}", f"O-H{i}", [("07", "14", 1)], now=3000)[0] for i in range(30)]
    ok("Exactamente uno de 30 obtiene la silla", res.count("OK") == 1, f"OK = {res.count('OK')}")

    print("\n== Modo desastre (alta_disponibilidad.md §5) ==")
    sembrar_sillas(ddb, fila="20", nros=range(1, 6))
    # (a) la réplica perdió todo: orden, pago y bloqueo; la silla aparece libre
    cobro_a = dict(oid="O-D1", nn=1, gtx="g1", uid="fer", sillas=[("07", "20", 1), ("07", "20", 2)], monto=200)
    ok("(a) Orden y bloqueo perdidos: se reconstruye todo", confirmar_desastre(ddb, cobro_a, now=5000) == "CONFIRMADA")
    ok("(a) Repetir no cambia nada", confirmar_desastre(ddb, cobro_a, now=5001) == "YA_COMPLETA")
    # (b) compra a medias: ORDER en PAID pero la silla quedó en L y sin boleta
    ddb.put_item(TableName="bya_seats", Item={**key_silla("07", "20", 3), "st": S("L"), "lo": S("O-D2"), "lx": N(5480), "v": N(1)})
    ddb.put_item(TableName="bya_orders", Item={"pk": S("ORD#O-D2"), "sk": S("ORDER"), "st": S("PAID"),
                                               "sil": {"L": [S("07|20|3")]}})
    cobro_b = dict(oid="O-D2", nn=1, gtx="g2", uid="gina", sillas=[("07", "20", 3)], monto=100)
    ok("(b) PAID a medias se repara", confirmar_desastre(ddb, cobro_b, now=5002) == "CONFIRMADA")
    ok("(b) La silla queda vendida a O-D2", silla(ddb, "07", "20", 3)["so"]["S"] == "O-D2")
    # (c) la silla ya es de otra orden: reembolso
    cobro_c = dict(oid="O-D3", nn=1, gtx="g3", uid="hugo", sillas=[("07", "20", 1)], monto=100)
    ok("(c) Silla vendida a otra orden: reembolso, sin doble venta", confirmar_desastre(ddb, cobro_c, now=5003) == "REEMBOLSO")
    ok("(c) La silla sigue siendo de O-D1", silla(ddb, "07", "20", 1)["so"]["S"] == "O-D1")
    # (d) bloqueo vigente de otro cliente
    ddb.put_item(TableName="bya_seats", Item={**key_silla("07", "20", 4), "st": S("L"), "lo": S("O-OTRO"), "lx": N(9999), "v": N(1)})
    cobro_d = dict(oid="O-D4", nn=1, gtx="g4", uid="ivan", sillas=[("07", "20", 4)], monto=100)
    ok("(d) Bloqueo vigente de otro: reembolso", confirmar_desastre(ddb, cobro_d, now=5004) == "REEMBOLSO")

    print("\n== Congelar solo las sillas en duda y reabrir (respuesta 3b del profesor) ==")
    sembrar_sillas(ddb, fila="30", nros=range(1, 7))
    T = 8000
    # La región cayó en T. La réplica no alcanzó a recibir nada de estas compras: todas las sillas aparecen libres.
    pagos = [
        dict(oid="O-C1", nn=1, gtx="c1", uid="ana2", status="approved", sillas=[("07", "30", 1)], monto=100),
        dict(oid="O-C2", nn=1, gtx="c2", uid="beto2", status="in_process", sillas=[("07", "30", 2)], monto=100),
        dict(oid="O-C3", nn=1, gtx="c3", uid="caro2", status="rejected", sillas=[("07", "30", 3)], monto=100),
    ]
    n = congelar_sillas_en_duda(ddb, pagos, T)
    ok("Se congelan las 2 sillas en duda y no la del pago rechazado", n == 2, f"congeladas = {n}")
    r = bloquear(ddb, "otro", "O-OTRO1", [("07", "30", 1)], now=T + 300)
    ok("Con la venta reabierta, nadie puede bloquear una silla congelada", r[0] == "CANCELADA")
    r = bloquear(ddb, "otro", "O-OTRO2", [("07", "30", 3)], now=T + 300)
    ok("La silla del pago rechazado sí se puede comprar", r[0] == "OK")
    r = bloquear(ddb, "otro", "O-OTRO3", [("07", "30", 4)], now=T + 300)
    ok("Las sillas sin pago en duda siguen a la venta", r[0] == "OK")
    ok("La conciliación confirma el pago aprobado sobre la silla congelada",
       confirmar_desastre(ddb, pagos[0], now=T + 400) == "CONFIRMADA")
    ok("La silla queda vendida a O-C1", silla(ddb, "07", "30", 1)["so"]["S"] == "O-C1")
    # el pago in_process termina rechazado: la silla se libera al cerrar la conciliación
    liberar_congeladas(ddb, [("07", "30", 1), ("07", "30", 2)])
    ok("Al terminar, la silla del pago no aprobado vuelve a estar libre", silla(ddb, "07", "30", 2)["st"]["S"] == "A")
    ok("Liberar no toca la silla ya vendida", silla(ddb, "07", "30", 1)["st"]["S"] == "S")
    n = congelar_sillas_en_duda(ddb, [pagos[0]], T)
    ok("Congelar de nuevo no toca una silla vendida", n == 0 and silla(ddb, "07", "30", 1)["st"]["S"] == "S")

    print("\n== Verificador de invariantes (para el simulacro de Miguel) ==")
    errores = verificar_invariantes(ddb)
    ok("Estado final sin violaciones", not errores, "; ".join(errores[:3]))
    # se inyecta una violación para comprobar que el verificador la detecta
    ddb.put_item(TableName="bya_tickets", Item={"pk": S("TKT#falsa"), "sk": S("T"), "st": S("VALID"),
                                                "oid": S("O-X"), "seat": S("07|20|1")})
    errores = verificar_invariantes(ddb)
    ok("El verificador detecta una silla con boletas de dos órdenes", any("dos" in e or "2 órdenes" in e for e in errores), errores[0] if errores else "")

    total, pasan = len(resultados), sum(1 for r in resultados if r[1])
    print(f"\nResultado: {pasan} de {total} pruebas pasan.")
    return pasan == total


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
