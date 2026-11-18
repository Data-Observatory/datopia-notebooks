"""Construye el grafo de relaciones entre los datasets de Datopia.

Entradas:
  - el modelo de datos público (`_meta/datamodel.json`): datasets, columnas, geometría y 39 llaves foráneas;
  - `relaciones-objetivo.json`: relaciones que se asumen cerradas (issues #56 a #59) más las que existen
    pero aún no están declaradas.

Reglas del grafo:
  - Tabular: dos datasets se relacionan solo si uno referencia al otro, o si ambos referencian una misma
    tabla. La tabla compartida es un nodo; no se dibujan aristas entre hermanos (eso se informa aparte en
    `comparten`).
  - Espacial: tener geometría es una insignia del nodo. La capa espacial dibuja una arista por dataset
    hacia el polígono de referencia (comunas). Todos los pares espaciales posibles (teóricos) son una
    capa aparte, apagada por defecto.
  - Cada arista lleva su estado: `hoy` (declarada en el modelo público) u `objetivo` (se asume cerrada),
    y una advertencia si tiene un problema conocido.

Solo biblioteca estándar.
"""
from __future__ import annotations

import json
import math
import random
from collections import defaultdict

URL_DATAMODEL = "https://datopia.dataobservatory.net/_meta/datamodel.json"

TIPOS_POLIGONO = {"Polygon", "MultiPolygon"}
TIPOS_LINEA = {"LineString", "MultiLineString"}
TIPOS_PUNTO = {"Point", "MultiPoint"}


def _clase(tipo_geometria):
    if tipo_geometria in TIPOS_POLIGONO:
        return "poligono"
    if tipo_geometria in TIPOS_LINEA:
        return "linea"
    if tipo_geometria in TIPOS_PUNTO:
        return "punto"
    return None


# predicado teórico de un cruce espacial entre dos clases de geometría
PREDICADO_PAR = {
    frozenset(["punto", "poligono"]): "dentro de",
    frozenset(["linea", "poligono"]): "cruza",
    frozenset(["poligono"]): "se solapa con",
    frozenset(["punto"]): "cerca de",
    frozenset(["punto", "linea"]): "cerca de",
    frozenset(["linea"]): "se cruza o está cerca de",
}


def cargar_datamodel(url=URL_DATAMODEL):
    """Descarga el modelo de datos público (no requiere credenciales)."""
    import urllib.request

    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def _etiqueta(d):
    return f"{d['fuente']} / {d['tipo']}" + ("" if d["version"] == "v1" else f" {d['version']}")


def construir(datamodel, objetivo):
    """Devuelve el grafo como diccionario JSON-serializable."""
    renombres = objetivo.get("renombres_codigos", {})
    ds = {d["id"]: d for d in datamodel["datasets"]}
    grupos = {g["id"]: g for g in datamodel["dataset_groups"]}
    tabla_geo = objetivo["tabla_geografica"]

    # --- nodos
    geom_hoy = {}
    for d in datamodel["datasets"]:
        g = d.get("geometry")
        if g:
            geom_hoy[d["id"]] = g["geometry_type"]
    geom_obj = dict(geom_hoy)
    for g in objetivo.get("geometrias", []):
        geom_obj[g["dataset"]] = g["geometry_type"]
    for f in objetivo.get("fusiones", []):
        geom_obj.pop(f["desde"], None)  # la geometría de v2 pasa a v1

    fusionado = {f["desde"]: f["hacia"] for f in objetivo.get("fusiones", [])}
    nodos = []
    for d in datamodel["datasets"]:
        i = d["id"]
        grupo = grupos.get(d.get("dataset_group"), {})
        nodos.append({
            "id": i,
            "etiqueta": _etiqueta(d),
            "corta": d["tipo"] + ("" if d["version"] == "v1" else f" {d['version']}"),
            "titulo": d["i18n"]["es"]["title"],
            "descripcion": d["i18n"]["es"]["description"],
            "grupo": d.get("dataset_group"),
            "grupo_titulo": grupo.get("title", {}).get("es", d.get("dataset_group")),
            "categoria": d["categoria"],
            "grano": d.get("grain"),
            "llave": d.get("primary_key") or [],
            "geometria_hoy": _clase(geom_hoy.get(i)),
            "geometria_tipo_hoy": geom_hoy.get(i),
            "geometria_objetivo": _clase(geom_obj.get(i)),
            "geometria_tipo_objetivo": geom_obj.get(i),
            "geometria_issue": next((g["issue"] for g in objetivo.get("geometrias", []) if g["dataset"] == i), None),
            "se_fusiona_en": fusionado.get(i),
            "notebook": d.get("notebook_url"),
            "autoref": False,
        })
    por_id = {n["id"]: n for n in nodos}

    # --- aristas tabulares declaradas (hoy)
    aristas = []

    def renombrar(cols):
        return [renombres.get(c, c) for c in cols]

    for r in datamodel["relations"]:
        a, b = r["from"]["dataset_id"], r["to"]["dataset_id"]
        if a == b:
            por_id[a]["autoref"] = True  # autorreferencia (jerarquía padre-hijo): marca del nodo
            continue
        cols_d, cols_h = r["from"]["columns"], r["to"]["columns"]
        aristas.append({
            "id": r["id"], "tipo": "tabular", "estado": "hoy", "desde": a, "hacia": b,
            "columnas_desde_hoy": cols_d, "columnas_hacia_hoy": cols_h,
            "columnas_desde": renombrar(cols_d), "columnas_hacia": renombrar(cols_h),
            "calidad": r["status"], "issues": [], "advertencia": None, "vigencia": None,
            "nota": r.get("note"), "columnas_pendientes": [],
        })

    # --- aristas tabulares objetivo
    for r in objetivo["relaciones"]:
        a, b = r["desde"], r["hacia"]
        cols_hoy_d = r.get("columnas_desde_hoy", r["columnas_desde"])
        pend = [c for c in r["columnas_desde"] if c not in {x["name"] for x in ds[a]["columns"]}]
        pend += [c for c in r["columnas_hacia"] if c not in {x["name"] for x in ds[b]["columns"]} and b != tabla_geo]
        aristas.append({
            "id": r["id"], "tipo": "tabular", "estado": "objetivo", "desde": a, "hacia": b,
            "columnas_desde_hoy": cols_hoy_d, "columnas_hacia_hoy": r["columnas_hacia"],
            "columnas_desde": r["columnas_desde"], "columnas_hacia": r["columnas_hacia"],
            "calidad": "advertencia" if r.get("advertencia") else "planeada",
            "issues": r.get("issues", []), "advertencia": r.get("advertencia"), "vigencia": r.get("vigencia"),
            "nota": r.get("nota"), "columnas_pendientes": sorted(set(pend)),
        })

    # --- fusiones (v2 -> v1)
    for f in objetivo.get("fusiones", []):
        aristas.append({
            "id": f"fusion.{f['desde']}", "tipo": "fusion", "estado": "objetivo", "desde": f["desde"], "hacia": f["hacia"],
            "columnas_desde_hoy": [], "columnas_hacia_hoy": [], "columnas_desde": [], "columnas_hacia": [],
            "calidad": "planeada", "issues": [f["issue"]], "advertencia": None, "vigencia": None,
            "nota": "v2 se fusiona en v1: queda un solo dataset con geometría.", "columnas_pendientes": [],
        })

    # --- capa espacial: una arista por dataset con geometría hacia el polígono de referencia
    def espaciales(geom, estado, poligono):
        out = []
        for i, t in geom.items():
            c = _clase(t)
            if i == poligono or c is None:
                continue
            out.append({
                "id": f"esp.{estado}.{i}", "tipo": "espacial", "estado": estado, "desde": i, "hacia": poligono,
                "predicado": PREDICADO_PAR[frozenset([c, "poligono"])], "calidad": "derivada",
                "columnas_desde": [], "columnas_hacia": [], "columnas_desde_hoy": [], "columnas_hacia_hoy": [],
                "issues": [], "advertencia": None, "vigencia": None, "columnas_pendientes": [],
                "nota": "Derivada de las geometrías (EPSG:4326). El cruce vale para el instante que corresponda en cada tabla.",
            })
        return out

    poligono_hoy = next((i for i, t in geom_hoy.items() if _clase(t) == "poligono"), None)
    poligono_obj = tabla_geo
    esp = []
    if poligono_hoy:
        esp += espaciales(geom_hoy, "hoy", poligono_hoy)
    esp += espaciales(geom_obj, "objetivo", poligono_obj)

    # --- capa espacial teórica: todos los pares con geometría
    pares = []
    for estado, geom in (("hoy", geom_hoy), ("objetivo", geom_obj)):
        ids = sorted(geom)
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                a, b = ids[x], ids[y]
                pares.append({
                    "id": f"par.{estado}.{a}.{b}", "tipo": "espacial-par", "estado": estado, "desde": a, "hacia": b,
                    "predicado": PREDICADO_PAR[frozenset([_clase(geom[a]), _clase(geom[b])])],
                    "calidad": "teorica", "columnas_desde": [], "columnas_hacia": [], "columnas_desde_hoy": [],
                    "columnas_hacia_hoy": [], "issues": [], "advertencia": None, "vigencia": None,
                    "columnas_pendientes": [],
                    "nota": "Cruce posible por tener ambos geometría; el sentido del análisis y el filtro de tiempo los define quien consulta.",
                })

    todas = aristas + esp + pares

    # --- "comparten tabla": datasets que referencian una misma tabla (sin dibujar aristas entre hermanos)
    comparten = {"hoy": defaultdict(lambda: defaultdict(set)), "objetivo": defaultdict(lambda: defaultdict(set))}
    for e in aristas:
        if e["tipo"] != "tabular":
            continue
        for estado in ("hoy", "objetivo"):
            if estado == "hoy" and e["estado"] != "hoy":
                continue
            comparten[estado][e["hacia"]][e["desde"]] = True
    comp_salida = {}
    for estado in ("hoy", "objetivo"):
        comp_salida[estado] = {
            tabla: sorted(fuentes) for tabla, fuentes in ((t, set(v)) for t, v in comparten[estado].items()) if len(fuentes) >= 2
        }

    # --- grado de cada nodo como tabla compartida (para dibujarlo como centro)
    entrada = defaultdict(int)
    for e in aristas:
        if e["tipo"] == "tabular":
            entrada[e["hacia"]] += 1
    for n in nodos:
        n["referenciado_por"] = entrada[n["id"]]

    _distribuir(nodos, [e for e in todas if e["tipo"] in ("tabular", "fusion")])

    return {
        "generado_desde": datamodel.get("generator"),
        "esquema": datamodel.get("schema_version"),
        "nodos": nodos,
        "aristas": todas,
        "comparten": comp_salida,
        "grupos": [{"id": g["id"], "titulo": g["title"]["es"]} for g in datamodel["dataset_groups"]],
        "supuestos": objetivo.get("supuestos", []),
        "tabla_geografica": tabla_geo,
    }


def _distribuir(nodos, aristas, ancho=1200, alto=800, iteraciones=600, semilla=7):
    """Posiciones determinísticas: un centro por grupo y un resorte (Fruchterman-Reingold) dentro y entre grupos."""
    rng = random.Random(semilla)
    grupos = sorted({n["grupo"] for n in nodos})
    cx, cy = ancho / 2, alto / 2
    centros = {}
    for k, g in enumerate(grupos):
        ang = 2 * math.pi * k / len(grupos) - math.pi / 2
        centros[g] = (cx + 0.34 * ancho * math.cos(ang), cy + 0.34 * alto * math.sin(ang))
    pos = {}
    for n in nodos:
        x0, y0 = centros[n["grupo"]]
        pos[n["id"]] = [x0 + rng.uniform(-40, 40), y0 + rng.uniform(-40, 40)]
    vecinos = [(e["desde"], e["hacia"]) for e in aristas]
    k = math.sqrt(ancho * alto / len(nodos)) * 0.8
    ids = [n["id"] for n in nodos]
    grupo = {n["id"]: n["grupo"] for n in nodos}
    temp = ancho / 12
    for it in range(iteraciones):
        desp = {i: [0.0, 0.0] for i in ids}
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                i, j = ids[a], ids[b]
                dx, dy = pos[i][0] - pos[j][0], pos[i][1] - pos[j][1]
                d = math.hypot(dx, dy) or 0.01
                f = k * k / d
                desp[i][0] += dx / d * f
                desp[i][1] += dy / d * f
                desp[j][0] -= dx / d * f
                desp[j][1] -= dy / d * f
        for i, j in vecinos:
            dx, dy = pos[i][0] - pos[j][0], pos[i][1] - pos[j][1]
            d = math.hypot(dx, dy) or 0.01
            f = d * d / k * 0.55
            desp[i][0] -= dx / d * f
            desp[i][1] -= dy / d * f
            desp[j][0] += dx / d * f
            desp[j][1] += dy / d * f
        for i in ids:  # atracción suave al centro del grupo
            x0, y0 = centros[grupo[i]]
            desp[i][0] += (x0 - pos[i][0]) * 0.35
            desp[i][1] += (y0 - pos[i][1]) * 0.35
        for i in ids:
            dx, dy = desp[i]
            d = math.hypot(dx, dy) or 0.01
            paso = min(d, temp)
            pos[i][0] += dx / d * paso
            pos[i][1] += dy / d * paso
        temp = max(1.5, temp * 0.985)
    # ajuste final: escala uniforme para que el grafo ocupe el lienzo con margen para las etiquetas
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    esc = min((ancho - 200) / ((max(xs) - min(xs)) or 1), (alto - 110) / ((max(ys) - min(ys)) or 1))
    ox = (ancho - esc * (max(xs) + min(xs))) / 2
    oy = (alto - esc * (max(ys) + min(ys))) / 2
    for n in nodos:
        n["x"], n["y"] = round(esc * pos[n["id"]][0] + ox, 1), round(esc * pos[n["id"]][1] + oy, 1)


def resumen(grafo):
    """Conteos útiles para revisar el grafo (por estado y tipo de arista, componentes conexos tabulares)."""
    cuenta = defaultdict(int)
    for e in grafo["aristas"]:
        cuenta[(e["tipo"], e["estado"])] += 1
    out = {"aristas": {f"{t}/{s}": n for (t, s), n in sorted(cuenta.items())}}
    for estado in ("hoy", "objetivo"):
        padre = {n["id"]: n["id"] for n in grafo["nodos"]}

        def raiz(x):
            while padre[x] != x:
                padre[x] = padre[padre[x]]
                x = padre[x]
            return x

        for e in grafo["aristas"]:
            if e["tipo"] in ("tabular", "fusion") and (estado == "objetivo" or e["estado"] == "hoy"):
                padre[raiz(e["desde"])] = raiz(e["hacia"])
        comp = defaultdict(list)
        for n in grafo["nodos"]:
            comp[raiz(n["id"])].append(n["etiqueta"])
        out[f"componentes_{estado}"] = sorted(((len(v), sorted(v)) for v in comp.values()), reverse=True)
    return out


def escribir_html(grafo, plantilla, destino):
    """Inserta el grafo en la plantilla del visor y escribe un HTML autocontenido (sin red)."""
    with open(plantilla, encoding="utf-8") as f:
        html = f.read()
    datos = json.dumps(grafo, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    assert "/*DATOS*/" in html
    with open(destino, "w", encoding="utf-8") as f:
        f.write(html.replace("/*DATOS*/null", datos))
    return destino
