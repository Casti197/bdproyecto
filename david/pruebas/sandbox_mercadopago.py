"""
Pruebas de sandbox de Mercado Pago para BoletaYa (D-11, david/pasarelas.md §2).

Comprueba lo que el diseño necesita de la pasarela:
  1. metadata guarda y devuelve un objeto propio (evento, usuario, sillas).
  2. Repetir el cobro con la misma X-Idempotency-Key devuelve el MISMO pago.
  3. Una llave distinta crea otro pago (la llave es la que decide).
  4. La búsqueda por rango de fechas encuentra los pagos y trae su metadata
     (de esa búsqueda sale la lista de sillas en duda, alta_disponibilidad.md §5.0).
  5. Nombres reales de los estados: aprobado, pendiente, rechazado.
  6. Largo que acepta external_reference (idea de guardar ahí las sillas).

Solo usa la biblioteca estándar de Python 3. Uso (PowerShell):

  $env:MP_ACCESS_TOKEN = "..."   # credencial de PRUEBA del vendedor
  $env:MP_PUBLIC_KEY   = "..."   # public key de PRUEBA del mismo vendedor
  $env:MP_PAYER_EMAIL  = "..."   # email de la cuenta de prueba Comprador
  $env:MP_CONFIRMO_PRUEBA = "1"  # solo si el token empieza por APP_USR y es del entorno "Prueba"
  python sandbox_mercadopago.py

Genera resultados_sandbox.json junto a este archivo. Ese es el archivo que se comparte.
"""
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = os.environ.get("MP_API_BASE", "https://api.mercadopago.com")
TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")
PUBLIC_KEY = os.environ.get("MP_PUBLIC_KEY", "")
PAYER_EMAIL = os.environ.get("MP_PAYER_EMAIL", "")
METODO = os.environ.get("MP_PAYMENT_METHOD", "master")      # Mastercard de prueba
TARJETA = {"numero": "5254133674403564", "cvv": "123", "mes": 11, "anio": 2030}  # tarjeta de prueba de Colombia
DOC = {"type": "CC", "number": "123456789"}                  # documento de prueba de Mercado Pago
SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados_sandbox.json")

resultados = []


def registrar(nombre, paso, detalle=""):
    resultados.append({"prueba": nombre, "pasa": bool(paso), "detalle": detalle})
    print(("PASA " if paso else "FALLA") + "  " + nombre + (f"  | {detalle}" if detalle else ""))


def llamar(metodo, ruta, cuerpo=None, encabezados=None, con_token=True):
    url = BASE + ruta
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    h = {"Content-Type": "application/json"}
    if con_token:
        h["Authorization"] = f"Bearer {TOKEN}"
    h.update(encabezados or {})
    req = urllib.request.Request(url, data=datos, method=metodo, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}


def es_cuenta_de_prueba():
    """Freno de seguridad: no correr nunca con una cuenta real (cobraría de verdad)."""
    if TOKEN.startswith("TEST-"):
        return True, "credencial TEST-"
    st, yo = llamar("GET", "/users/me")
    if st != 200:
        return False, f"/users/me respondió {st}"
    etiquetas = yo.get("tags") or []
    if "test_user" in etiquetas:
        return True, f"usuario {yo.get('id')} con etiqueta test_user"
    # Las credenciales de prueba actuales también empiezan por APP_USR (documentación de Mercado Pago).
    # Se acepta solo si la persona confirma que copió las del entorno "Prueba"; además, cada token de
    # tarjeta se revisa: si Mercado Pago lo marca live_mode=true, el script se detiene (token_tarjeta).
    if os.environ.get("MP_CONFIRMO_PRUEBA") == "1":
        return True, "confirmado por MP_CONFIRMO_PRUEBA=1; se verifica live_mode=false en cada token"
    return False, (f"el usuario {yo.get('id')} no tiene la etiqueta test_user. Si copiaste las credenciales "
                   "del entorno 'Prueba', vuelve a correr con $env:MP_CONFIRMO_PRUEBA = \"1\"")


def token_tarjeta(titular):
    """Tokeniza la tarjeta de prueba. Cada token sirve para un solo pago."""
    cuerpo = {"card_number": TARJETA["numero"], "security_code": TARJETA["cvv"],
              "expiration_month": TARJETA["mes"], "expiration_year": TARJETA["anio"],
              "cardholder": {"name": titular, "identification": DOC}}
    st, r = llamar("POST", "/v1/card_tokens?public_key=" + urllib.parse.quote(PUBLIC_KEY), cuerpo, con_token=False)
    if st not in (200, 201) or "id" not in r:
        raise RuntimeError(f"no se pudo crear el token de tarjeta ({st}): {r}")
    if r.get("live_mode") is True:
        sys.exit("ALTO: Mercado Pago marcó el token como real (live_mode=true). Estas no son credenciales de prueba.")
    return r["id"]


def cuerpo_pago(token, oid, metadata, referencia=None):
    return {"transaction_amount": 50000, "token": token, "description": f"BoletaYa sandbox {oid}",
            "installments": 1, "payment_method_id": METODO,
            "payer": {"email": PAYER_EMAIL, "identification": DOC},
            "external_reference": referencia or f"{oid}#01", "metadata": metadata}


def pagar(cuerpo, llave):
    return llamar("POST", "/v1/payments", cuerpo, {"X-Idempotency-Key": llave})


def normalizar(x):
    """Mercado Pago puede cambiar mayúsculas o tipos al guardar metadata; se compara sin eso."""
    return json.loads(json.dumps(x, sort_keys=True).lower())


def main():
    faltan = [n for n, v in [("MP_ACCESS_TOKEN", TOKEN), ("MP_PUBLIC_KEY", PUBLIC_KEY), ("MP_PAYER_EMAIL", PAYER_EMAIL)] if not v]
    if faltan:
        sys.exit("Faltan variables: " + ", ".join(faltan) + ". Ver SANDBOX.md.")
    prueba, por_que = es_cuenta_de_prueba()
    if not prueba:
        sys.exit("ALTO: la credencial no parece de prueba (" + por_que + "). No se ejecuta nada.")
    print("Cuenta de prueba confirmada:", por_que, "\n")
    inicio = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=2)
    corrida = uuid.uuid4().hex[:8]
    sillas = [f"07|12|{n}" for n in range(20, 30)]          # 10 sillas, el máximo por orden
    meta = {"eid": "1234", "uid": "usuario-prueba", "sillas": sillas, "corrida": corrida}

    # 1 y 2. Pago aprobado con metadata; luego, la misma llave otra vez
    oid_a = f"O-{corrida}-A"
    llave_a = f"{oid_a}#01"
    cuerpo_a = cuerpo_pago(token_tarjeta("APRO"), oid_a, meta)
    st1, p1 = pagar(cuerpo_a, llave_a)
    registrar("Pago aprobado creado (titular APRO)", st1 in (200, 201) and p1.get("status") == "approved",
              f"HTTP {st1}, status={p1.get('status')}, id={p1.get('id')}")
    id_a = p1.get("id")
    st2, p2 = pagar(cuerpo_a, llave_a)                       # mismo cuerpo, mismo token, misma llave
    registrar("Repetir con la misma X-Idempotency-Key devuelve el mismo pago",
              st2 in (200, 201) and p2.get("id") == id_a,
              f"HTTP {st2}, primer id={id_a}, segundo id={p2.get('id')}, error={p2.get('message')}")

    # 1. metadata leída de vuelta
    st, g = llamar("GET", f"/v1/payments/{id_a}")
    devuelta = g.get("metadata")
    registrar("metadata se guarda y se devuelve con las 10 sillas",
              st == 200 and normalizar(devuelta) == normalizar(meta),
              f"enviada={json.dumps(meta)} | devuelta={json.dumps(devuelta)}")
    registrar("external_reference se devuelve igual", g.get("external_reference") == f"{oid_a}#01",
              f"devuelta={g.get('external_reference')}")

    # 3. Otra llave: debe ser otro pago
    oid_b = f"O-{corrida}-B"
    st3, p3 = pagar(cuerpo_pago(token_tarjeta("APRO"), oid_b, meta), f"{oid_b}#01")
    registrar("Con otra llave se crea un pago distinto", st3 in (200, 201) and p3.get("id") not in (None, id_a),
              f"HTTP {st3}, id={p3.get('id')}")

    # 5. Estados: pendiente y rechazado
    estados = {}
    for titular, validos in [("CONT", ("pending", "in_process")), ("OTHE", ("rejected",))]:
        oid = f"O-{corrida}-{titular}"
        st, p = pagar(cuerpo_pago(token_tarjeta(titular), oid, meta), f"{oid}#01")
        estados[titular] = {"status": p.get("status"), "status_detail": p.get("status_detail"), "id": p.get("id")}
        registrar(f"Titular {titular}: estado {' o '.join(validos)}", st in (200, 201) and p.get("status") in validos,
                  f"HTTP {st}, status={p.get('status')}, status_detail={p.get('status_detail')}")

    # 6. Largo de external_reference
    largos = {}
    for n in (64, 128, 256, 512):
        oid = f"O-{corrida}-L{n}"
        ref = (oid + "#01|" + "|".join(sillas * 10))[:n]
        st, p = pagar(cuerpo_pago(token_tarjeta("APRO"), oid, meta, ref), f"{oid}#01")
        devuelta = None
        if p.get("id"):
            _, g2 = llamar("GET", f"/v1/payments/{p['id']}")
            devuelta = g2.get("external_reference")
        largos[n] = {"http": st, "acepta": st in (200, 201), "devuelve_completa": devuelta == ref, "error": p.get("message")}
        registrar(f"external_reference de {n} caracteres (informativa)", True,
                  f"HTTP {st}, acepta={st in (200, 201)}, se devuelve completa={devuelta == ref}")

    # 4. Búsqueda por fechas: ¿aparecen y traen metadata?
    time.sleep(5)
    q = urllib.parse.urlencode({"range": "date_created", "begin_date": inicio.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                                "end_date": "NOW", "sort": "date_created", "criteria": "desc", "limit": 100})
    st, s = llamar("GET", "/v1/payments/search?" + q)
    encontrados = [r for r in s.get("results", []) if (r.get("metadata") or {}).get("corrida") == corrida]
    ids_buscados = {id_a, p3.get("id")} | {e["id"] for e in estados.values()}
    ids_encontrados = {r.get("id") for r in encontrados}
    registrar("La búsqueda por fechas encuentra los pagos de esta corrida",
              st == 200 and ids_buscados <= ids_encontrados,
              f"HTTP {st}, buscados={len(ids_buscados)}, encontrados con metadata={len(ids_buscados & ids_encontrados)}")
    registrar("La búsqueda trae la metadata con las sillas (para congelar)",
              any(normalizar((r.get("metadata") or {}).get("sillas")) == normalizar(sillas) for r in encontrados),
              f"estados vistos en la búsqueda: {sorted({r.get('status') for r in encontrados})}")

    resumen = {"fecha": datetime.datetime.now().isoformat(timespec="seconds"), "corrida": corrida,
               "pasan": sum(r["pasa"] for r in resultados), "total": len(resultados),
               "resultados": resultados, "estados_por_titular": estados, "external_reference_por_largo": largos}
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    print(f"\n{resumen['pasan']} de {resumen['total']} pasan. Resultado guardado en {SALIDA}")


if __name__ == "__main__":
    main()
