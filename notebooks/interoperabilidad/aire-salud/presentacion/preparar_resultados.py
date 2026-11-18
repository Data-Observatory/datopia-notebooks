#!/usr/bin/env python3
"""Ejecuta las consultas de `consultas/*.sql` contra el Datopia Lakehouse y guarda los resultados
en `resultados/` para que `presentacion.qmd` se renderice sin red.

Uso (desde esta carpeta):
    python preparar_resultados.py

Credenciales: `../../../../config.json` (copia de config.example.json) o las variables
DATOPIA_EMAIL y DATOPIA_PASSWORD. Tarda del orden de 1 a 3 minutos (lecturas remotas).
"""
import json
import os
import pathlib
import time

import duckdb
import requests

RAIZ = pathlib.Path(__file__).resolve().parent
CONSULTAS = RAIZ / "consultas"
RESULTADOS = RAIZ / "resultados"
RESULTADOS.mkdir(exist_ok=True)

API_URL = "https://ee98cnfz7e.execute-api.us-west-2.amazonaws.com/prod"
CUT_COMUNA = "13110"   # La Florida (debe coincidir con los literales de consultas/*.sql)

# ── Conexión ────────────────────────────────────────────────────────────────
config = RAIZ / "../../../../config.json"
if config.exists():
    usuario = json.load(open(config))["test_user"]
    email, clave = usuario["email"], usuario["password"]
else:
    email, clave = os.environ["DATOPIA_EMAIL"], os.environ["DATOPIA_PASSWORD"]

token = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": clave}, timeout=30).json()["id_token"]
creds = requests.post(f"{API_URL}/auth/session/s3", headers={"Authorization": f"Bearer {token}"}, timeout=30).json()

con = duckdb.connect()
con.execute(f"""CREATE OR REPLACE SECRET s3 (
    TYPE S3, KEY_ID '{creds['access_key_id']}', SECRET '{creds['secret_access_key']}',
    SESSION_TOKEN '{creds['session_token']}', REGION '{creds['region']}')""")
con.execute("INSTALL spatial")
con.execute("LOAD spatial")
con.execute("SET threads=128")
con.execute("SET enable_progress_bar=false")
con.execute("SET TimeZone='America/Santiago'")

tiempos = {}


def ejecutar(archivo, etiqueta=None):
    """Ejecuta un archivo .sql (varias sentencias separadas por ';') y devuelve el resultado de la última."""
    t0 = time.time()
    resultado = None
    for sentencia in (s.strip() for s in (CONSULTAS / archivo).read_text(encoding="utf-8").split(";")):
        if sentencia:
            resultado = con.execute(sentencia)
    if etiqueta:
        tiempos[etiqueta] = round(time.time() - t0, 1)
        print(f"{tiempos[etiqueta]:6.1f} s  {etiqueta}")
    return resultado


# ── Consultas de la presentación (mismas que se muestran en las diapositivas) ──
ejecutar("00_fuentes.sql")
ejecutar("01_estaciones.sql", "Ubicar estaciones en comunas (SINCA, SUBDERE)")
ejecutar("02_aire.sql", "Leer MP2,5 diario (SINCA)")
ejecutar("03_salud.sql", "Leer consultas respiratorias y diccionario (DEIS)")
ejecutar("04_poblacion.sql", "Leer población (Censo 2024, INE)")

antes_despues = ejecutar("03b_diccionario.sql").df()
union = ejecutar("05_union.sql", "Unión de las cuatro fuentes").df()
mapa = ejecutar("06_mapa.sql", "Promedio de invierno por estación").df()

# ── Consultas de apoyo (solo para dibujar; no se muestran) ──────────────────
estaciones_total = con.execute("SELECT COUNT(*) FROM estaciones").fetchone()[0]
estaciones_rm = con.execute(
    "SELECT nom_com AS comuna, nombre AS estacion, lon, lat, cut_com FROM estaciones WHERE cut_reg = '13' ORDER BY nom_com").df()
aire_estacion = con.execute(
    f"SELECT a.fecha, a.valor FROM aire_diario a JOIN estaciones e USING (estacion_fk) WHERE e.cut_com = '{CUT_COMUNA}' ORDER BY 1").df()
poligono_comuna = con.execute(
    f"SELECT ST_AsText(ST_Simplify(geometry, 0.0004)) AS wkt FROM subdere_comunas WHERE cut_com = '{CUT_COMUNA}'").df()
estaciones_comuna = con.execute(f"SELECT COUNT(*) FROM estaciones WHERE cut_com = '{CUT_COMUNA}'").fetchone()[0]
assert estaciones_comuna == 1, "la consulta de unión asume una estación en la comuna"
mediciones = con.execute("SELECT COUNT(*) FROM aire_diario").fetchone()[0]
habitantes = int(con.execute("SELECT habitantes FROM poblacion").fetchone()[0])
poligonos = con.execute(
    "SELECT cut_com, ST_AsText(ST_Simplify(geometry, 0.003)) AS wkt FROM subdere_comunas WHERE cut_reg = '13'").df()

# ── Cifras de la respuesta ──────────────────────────────────────────────────
import pandas as pd

mensual = union.groupby("mes").agg(mp25=("mp25", "first"), consultas_por_mil=("consultas_por_mil", "sum"))
mes_num = pd.to_datetime(mensual.index).month
invierno, verano = mensual[mes_num.isin([5, 6, 7, 8])], mensual[mes_num.isin([12, 1, 2])]
resumen = {
    "comuna": "La Florida", "cut": CUT_COMUNA, "ventana": [2023, 2024],
    "meses": int(len(mensual)), "habitantes": habitantes, "mediciones": int(mediciones),
    "estaciones_pais": int(estaciones_total),
    "mp25_invierno": float(invierno.mp25.mean()), "mp25_verano": float(verano.mp25.mean()),
    "consultas_invierno": float(invierno.consultas_por_mil.mean()), "consultas_verano": float(verano.consultas_por_mil.mean()),
    "correlacion": float(mensual.mp25.corr(mensual.consultas_por_mil)),
}

# ── Guardar ─────────────────────────────────────────────────────────────────
union.to_csv(RESULTADOS / "union.csv", index=False)
mapa.to_csv(RESULTADOS / "mapa_puntos.csv", index=False)
poligonos.to_csv(RESULTADOS / "mapa_poligonos.csv", index=False)
antes_despues.to_csv(RESULTADOS / "antes_despues.csv", index=False)
estaciones_rm.to_csv(RESULTADOS / "estaciones_rm.csv", index=False)
aire_estacion.to_csv(RESULTADOS / "aire_estacion.csv", index=False)
poligono_comuna.to_csv(RESULTADOS / "poligono_comuna.csv", index=False)
json.dump(resumen, open(RESULTADOS / "resumen.json", "w"), ensure_ascii=False, indent=2)
json.dump(tiempos, open(RESULTADOS / "tiempos.json", "w"), ensure_ascii=False, indent=2)
print(f"\nTotal de lecturas y consultas: {sum(tiempos.values()):.1f} s")
print(json.dumps(resumen, ensure_ascii=False, indent=2))
