"""Gráficos interactivos (Vega-Lite) de la presentación. Funcionan sin internet.

Cada función imprime un `<div class="vl" data-spec="...">`; `encabezado.html` (que lleva Vega,
Vega-Lite y Vega-Embed incrustados) los convierte en gráficos al abrir el HTML.
Mismas reglas y colores que `graficos.py`: un eje por panel, marcas finas, aire naranja,
consultas azules, causas con la paleta validada.
"""
import html
import json
import re

import pandas as pd
from shapely import wkt as wkt_shapely
from shapely.geometry import mapping

from graficos import AIRE, CAUSA_COLOR, GRIS, GRIS_CLARO, GRILLA, ORDEN_CAUSAS, SALUD, SALUD_CLARO, TXT, TXT2

ETIQUETA_MES = "['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'][month(datum.value)] + ' ' + year(datum.value)"
CONFIG = {
    "view": {"stroke": None},
    "font": "system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif",
    "axis": {"labelColor": TXT2, "titleColor": TXT2, "gridColor": GRILLA, "domainColor": GRILLA, "tickColor": GRILLA,
             "labelFontSize": 14, "titleFontSize": 14, "titleFontWeight": "normal"},
    "legend": {"labelColor": TXT2, "titleColor": TXT2, "labelFontSize": 13, "symbolSize": 110},
}
EJE_X = {"title": None, "format": "%b %Y", "labelExpr": ETIQUETA_MES, "tickCount": {"interval": "month", "step": 3}}


def _mostrar(spec):
    spec = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "config": CONFIG, **spec}
    crudo = json.dumps(spec, ensure_ascii=False, separators=(",", ":"))
    # Fechas sin zona horaria: Vega las lee y las muestra en hora local (sin esto, un día de menos en Chile).
    crudo = re.sub(r'"(\d{4}-\d{2}-\d{2})"', r'"\1T00:00:00"', crudo)
    texto = html.escape(crudo, quote=True)
    print(f'<div class="vl" data-spec="{texto}"></div>')


def _invierno(anios):
    """Franjas de invierno (1 may a 31 ago) como datos de un `rect`."""
    return [{"ini": f"{a}-05-01", "fin": f"{a}-09-01"} for a in anios]


def _color(nombre, escala):
    return {"datum": nombre, "scale": escala, "legend": {"title": None, "orient": "top", "direction": "horizontal", "symbolType": "square", "columnPadding": 24}}


def _franja(anios, etiqueta=None, escala=None):
    codificacion = {"x": {"field": "ini", "type": "temporal"}, "x2": {"field": "fin"}}
    if etiqueta:
        codificacion["color"] = _color(etiqueta, escala)
    return {"data": {"values": _invierno(anios)}, "mark": {"type": "rect", "opacity": 0.9, **({} if etiqueta else {"color": GRIS_CLARO})},
            "encoding": codificacion}


# ── Paso 2: MP2,5 diario ─────────────────────────────────────────────────────────
def aire_diario(aire, norma_diaria=50):
    aire = aire.assign(fecha=pd.to_datetime(aire.fecha))
    mensual = aire.set_index("fecha").valor.resample("MS").mean()
    diario = [{"fecha": f.strftime("%Y-%m-%d"), "valor": round(v, 1)} for f, v in zip(aire.fecha, aire.valor)]
    promedio = [{"fecha": (f + pd.Timedelta(days=14)).strftime("%Y-%m-%d"), "valor": round(v, 1)} for f, v in mensual.items()]
    anios = sorted(set(aire.fecha.dt.year))
    x = {"field": "fecha", "type": "temporal", "axis": EJE_X, "scale": {"domain": [f"{anios[0]}-01-01", f"{anios[-1] + 1}-01-01"]}}
    y = {"field": "valor", "type": "quantitative", "title": "MP2,5 (µg/m³)", "scale": {"domainMin": 0}}
    nombres = ["invierno (may a ago)", "valor de cada día", "promedio del mes"]
    escala = {"domain": nombres, "range": [GRIS_CLARO, AIRE, AIRE]}
    capas = [
        _franja(anios, nombres[0], escala),
        {"data": {"values": diario}, "mark": {"type": "line", "strokeWidth": 0.9, "opacity": 0.6},
         "encoding": {"x": x, "y": y, "color": _color(nombres[1], escala)}},
        {"data": {"values": diario}, "mark": {"type": "point", "filled": True, "size": 70, "color": AIRE, "stroke": "white", "strokeWidth": 1.2},
         "params": [{"name": "cerca", "select": {"type": "point", "on": "pointerover", "nearest": True, "fields": ["fecha"], "clear": "pointerout"}}],
         "encoding": {"x": x, "y": y, "opacity": {"condition": {"param": "cerca", "empty": False, "value": 1}, "value": 0},
                      "tooltip": [{"field": "fecha", "type": "temporal", "title": "día", "format": "%d de %b %Y"},
                                  {"field": "valor", "type": "quantitative", "title": "MP2,5 (µg/m³)", "format": ".0f"}]}},
        {"data": {"values": promedio}, "mark": {"type": "line", "strokeWidth": 2.4, "point": {"filled": True, "size": 60, "stroke": "white", "strokeWidth": 1.2}},
         "encoding": {"x": x, "y": y, "color": _color(nombres[2], escala), "tooltip": [{"field": "fecha", "type": "temporal", "title": "mes", "format": "%B %Y"},
                                                  {"field": "valor", "type": "quantitative", "title": "promedio del mes (µg/m³)", "format": ".1f"}]}},
        {"data": {"values": [{"y": norma_diaria}]}, "mark": {"type": "rule", "color": GRIS, "strokeWidth": 1}, "encoding": {"y": {"field": "y", "type": "quantitative"}}},
        {"data": {"values": [{"y": norma_diaria, "fecha": f"{anios[0]}-01-04", "texto": f"norma diaria chilena ({norma_diaria} µg/m³)"}]},
         "mark": {"type": "text", "align": "left", "baseline": "bottom", "dy": -4, "fontSize": 13, "color": TXT2},
         "encoding": {"x": {"field": "fecha", "type": "temporal"}, "y": {"field": "y", "type": "quantitative"}, "text": {"field": "texto"}}},
    ]
    _mostrar({"width": 1060, "height": 330, "layer": capas, "resolve": {"scale": {"color": "shared"}, "legend": {"color": "shared"}}})


# ── Paso 5: la unión, dos paneles con cursor compartido ─────────────────────────
def union_paneles(union):
    union = union.assign(mes=pd.to_datetime(union.mes))
    meses = sorted(union.mes.unique())
    anios = sorted(set(pd.DatetimeIndex(meses).year))
    fila_mes = {m: {"ini": m.strftime("%Y-%m-%d"), "fin": (m + pd.offsets.MonthBegin(1)).strftime("%Y-%m-%d"),
                    "centro": (m + pd.Timedelta(days=14)).strftime("%Y-%m-%d")} for m in map(pd.Timestamp, meses)}
    total = union.groupby("mes").consultas_por_mil.sum()
    mp25 = union.drop_duplicates("mes").set_index("mes").mp25
    aire = [{**fila_mes[pd.Timestamp(m)], "mp25": round(float(v), 1), "total": round(float(total[m]), 2)} for m, v in mp25.items()]
    causas, acumulado = [], {}
    for r in sorted(union.itertuples(), key=lambda r: (r.mes, ORDEN_CAUSAS.index(r.causa) if r.causa in ORDEN_CAUSAS else 99)):
        base = acumulado.get(r.mes, 0.0)
        acumulado[r.mes] = base + float(r.consultas_por_mil)
        causas.append({**fila_mes[r.mes], "causa": r.causa, "valor": round(float(r.consultas_por_mil), 2), "desde": round(base, 3), "hasta": round(acumulado[r.mes], 3),
                       "mp25": round(float(r.mp25), 1), "total": round(float(total[r.mes]), 2)})
    dominio = {"domain": [f"{anios[0]}-01-01", f"{anios[-1] + 1}-01-01"]}
    panel_aire = {
        "name": "v_aire", "width": 1000, "height": 120,
        "layer": [
            _franja(anios),
            {"data": {"values": aire}, "mark": {"type": "line", "strokeWidth": 2.4, "color": AIRE, "point": {"filled": True, "size": 60, "stroke": "white", "strokeWidth": 1.2, "color": AIRE}},
             "encoding": {"x": {"field": "centro", "type": "temporal", "axis": {**EJE_X, "labels": False, "ticks": False}, "scale": dominio},
                          "y": {"field": "mp25", "type": "quantitative", "title": "MP2,5 (µg/m³)", "scale": {"domainMin": 0}, "axis": {"tickCount": 3}},
                          "tooltip": [{"field": "centro", "type": "temporal", "title": "mes", "format": "%B %Y"},
                                      {"field": "mp25", "type": "quantitative", "title": "MP2,5 del mes (µg/m³)", "format": ".1f"},
                                      {"field": "total", "type": "quantitative", "title": "consultas por mil hab. en el mes", "format": ".1f"}]}},
        ]}
    barras = {"data": {"values": causas}, "mark": {"type": "bar", "stroke": "white", "strokeWidth": 1},
              "encoding": {"x": {"field": "ini", "type": "temporal", "scale": dominio, "axis": EJE_X}, "x2": {"field": "fin"},
                           "y": {"field": "desde", "type": "quantitative", "title": "consultas por mil habitantes"}, "y2": {"field": "hasta"},
                           "color": {"field": "causa", "type": "nominal", "title": None, "sort": ORDEN_CAUSAS,
                                     "scale": {"domain": ORDEN_CAUSAS, "range": [CAUSA_COLOR[c] for c in ORDEN_CAUSAS]}, "legend": {"orient": "bottom", "symbolType": "square", "labelLimit": 400}},
                           "tooltip": [{"field": "ini", "type": "temporal", "title": "mes", "format": "%B %Y"},
                                       {"field": "causa", "type": "nominal", "title": "causa"},
                                       {"field": "valor", "type": "quantitative", "title": "esta causa, por mil hab.", "format": ".2f"},
                                       {"field": "total", "type": "quantitative", "title": "total del mes, por mil hab.", "format": ".1f"},
                                       {"field": "mp25", "type": "quantitative", "title": "MP2,5 del mes (µg/m³)", "format": ".1f"}]}}
    panel_salud = {"name": "v_salud", "width": 1000, "height": 230, "layer": [_franja(anios), barras]}
    _mostrar({"vconcat": [panel_aire, panel_salud], "spacing": 8, "resolve": {"scale": {"x": "shared"}}})


# ── Mapa: MP2,5 de invierno por estación ─────────────────────────────────────────
def mapa_invierno(puntos, poligonos, cut, ancho=900, alto=470):
    import math
    comunas = [{"type": "Feature", "properties": {"cut": f.cut_com, "propia": f.cut_com == cut}, "geometry": mapping(wkt_shapely.loads(f.wkt))}
               for f in poligonos.itertuples()]
    lon0, lon1 = puntos.lon.min() - 0.3, puntos.lon.max() + 0.3
    lat0, lat1 = puntos.lat.min() - 0.2, puntos.lat.max() + 0.16
    centro = [(lon0 + lon1) / 2, (lat0 + lat1) / 2]
    escala = min(ancho / math.radians(lon1 - lon0), alto / (math.log(math.tan(math.pi / 4 + math.radians(lat1) / 2)) - math.log(math.tan(math.pi / 4 + math.radians(lat0) / 2))))
    # posición de las etiquetas (desplazamiento en grados, equivalente al de la versión estática)
    desplaza = {"Pudahuel": (-62, -16), "Cerro Navia": (8, 8), "Cerrillos": (-78, -4), "El Bosque": (-82, -4)}
    etiquetas = []
    for f in puntos.itertuples():
        dx, dy = desplaza.get(f.nom_com, (9, 7))
        etiquetas.append({"lon": f.lon + (0.012 if dx >= 0 else -0.012), "lat": f.lat + dy * 0.0007, "texto": f"{f.nom_com}  {f.mp25_invierno_2024:.0f}", "izq": dx < 0})
    datos_puntos = [{"comuna": f.nom_com, "lon": f.lon, "lat": f.lat, "mp25": round(float(f.mp25_invierno_2024), 1)} for f in puntos.itertuples()]
    base = {"type": "geoshape", "clip": True}
    texto = {"type": "text", "fontSize": 13, "color": TXT, "baseline": "middle"}
    codif_texto = {"longitude": {"field": "lon", "type": "quantitative"}, "latitude": {"field": "lat", "type": "quantitative"}, "text": {"field": "texto"}}
    _mostrar({
        "width": ancho, "height": alto,
        "projection": {"type": "mercator", "scale": escala, "center": centro, "translate": [ancho / 2, alto / 2]},
        "layer": [
            {"data": {"values": comunas}, "transform": [{"filter": "!datum.properties.propia"}], "mark": {**base, "fill": "#f1f0ed", "stroke": "#c9c8c2", "strokeWidth": 0.7}},
            {"data": {"values": comunas}, "transform": [{"filter": "datum.properties.propia"}], "mark": {**base, "fill": SALUD_CLARO, "stroke": SALUD, "strokeWidth": 2}},
            {"data": {"values": datos_puntos}, "mark": {"type": "circle", "size": 230, "stroke": TXT2, "strokeWidth": 0.8, "opacity": 1},
             "encoding": {"longitude": {"field": "lon", "type": "quantitative"}, "latitude": {"field": "lat", "type": "quantitative"},
                          "color": {"field": "mp25", "type": "quantitative", "title": "MP2,5 may a ago 2024 (µg/m³)",
                                    "scale": {"scheme": "oranges", "domain": [20, float(puntos.mp25_invierno_2024.max()) + 2]}, "legend": {"orient": "right", "gradientLength": 260, "titlePadding": 12}},
                          "tooltip": [{"field": "comuna", "title": "comuna"}, {"field": "mp25", "type": "quantitative", "title": "MP2,5 (µg/m³)", "format": ".0f"}]}},
            {"data": {"values": [e for e in etiquetas if not e["izq"]]}, "mark": {**texto, "align": "left"}, "encoding": codif_texto},
            {"data": {"values": [e for e in etiquetas if e["izq"]]}, "mark": {**texto, "align": "right"}, "encoding": codif_texto},
        ]})
