"""Gráficos de la presentación (el código no se muestra en las diapositivas).

Reglas: un solo eje por gráfico (dos magnitudes distintas van en paneles separados), marcas finas,
grilla tenue, color por entidad (aire = naranja, consultas = azul, causas = paleta categórica validada).
"""
import matplotlib.dates as mdates
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import FuncFormatter
from shapely import wkt as wkt_shapely

# ── Paleta (validada: azul, aqua, violeta, magenta; naranja reservado para el aire) ──
AIRE = "#eb6834"
SALUD = "#2a78d6"
SALUD_CLARO = "#cde2fb"
AIRE_CLARO = "#fbd9c9"
CAUSA_COLOR = {
    "otras respiratorias": "#2a78d6",
    "síndrome bronquial obstructivo": "#e87ba4",
    "neumonía": "#1baf7a",
    "exacerbación asma": "#6250d6",
}
ORDEN_CAUSAS = list(CAUSA_COLOR)
TXT, TXT2 = "#0b0b0b", "#52514e"
GRIS, GRIS_CLARO, GRILLA = "#9a9993", "#e9e8e4", "#e5e4e0"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

plt.rcParams.update({
    "font.size": 14, "axes.edgecolor": GRILLA, "axes.labelcolor": TXT2, "xtick.color": TXT2, "ytick.color": TXT2,
    "text.color": TXT, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 110,
    "figure.facecolor": "white", "axes.facecolor": "white", "legend.frameon": False,
})


def coma(x, decimales=1):
    return f"{x:.{decimales}f}".replace(".", ",")


def miles(x):
    return f"{x:,.0f}".replace(",", ".")


def _ejes(ax, grilla="y"):
    ax.grid(axis=grilla, color=GRILLA, lw=.8)
    ax.set_axisbelow(True)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRILLA)


def _eje_meses(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{MESES[mdates.num2date(v).month - 1]} {mdates.num2date(v).year}"))


def _invierno(ax, anios, etiqueta=True):
    for i, anio in enumerate(anios):
        ax.axvspan(pd.Timestamp(f"{anio}-05-01"), pd.Timestamp(f"{anio}-08-31"), color=GRIS_CLARO, alpha=.8, lw=0,
                   label="invierno (may a ago)" if (etiqueta and i == 0) else None, zorder=0)


def _caja(ax, x, y, w, h, texto, fc, ec, fs=13, negrita=False, mono=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=fs, color=TXT,
            fontweight="bold" if negrita else "normal", family="monospace" if mono else None, linespacing=1.25)


def _flecha(ax, x0, y0, x1, y1, color=GRIS, lw=1.8, estilo="-|>"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=estilo, mutation_scale=16, color=color, lw=lw, shrinkA=0, shrinkB=0))


def _lienzo(ancho, alto, xlim, ylim):
    fig, ax = plt.subplots(figsize=(ancho, alto))
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_axis_off()
    return fig, ax


def _grupos(df):
    """geometrías de WKT -> lista de polígonos exteriores"""
    for fila in df.itertuples():
        g = wkt_shapely.loads(fila.wkt)
        yield fila, (list(g.geoms) if g.geom_type == "MultiPolygon" else [g])


# ── 1. Silos frente a datos estructurados ───────────────────────────────────────
def silos_vs_lakehouse(total_segundos):
    fig, ax = _lienzo(13, 5.6, (-1.2, 101.2), (0, 56))
    gris_fc, gris_ec = "#f3f2ef", "#c9c8c2"
    ax.text(0, 53, "Silos de datos (hoy)", fontsize=17, fontweight="bold", va="center")
    ax.text(0, 25, "Datos estructurados (Datopia Lakehouse)", fontsize=17, fontweight="bold", va="center")

    # carril de silos
    pasos = ["4 portales,\n4 formatos", "Descargar cada\narchivo", "Decodificar códigos\n(Col01, Col02...)",
             "Corregir nombres\nde comuna", "Cruzar en planillas\ny en mapas"]
    w, h, y = 14.4, 12, 34
    paso = 16.8
    xs = [i * paso for i in range(5)]
    for x, t in zip(xs, pasos):
        _caja(ax, x, y, w, h, t, gris_fc, gris_ec, fs=12.5)
    for a, b in zip(xs[:-1], xs[1:]):
        _flecha(ax, a + w + .4, y + h / 2, b - .4, y + h / 2)
    _flecha(ax, xs[-1] + w + .4, y + h / 2, 83.6, y + h / 2)
    _caja(ax, 84, y, 16, h, "Respuesta", gris_fc, TXT2, fs=14, negrita=True)
    ax.text(92, y - 2.4, "semanas (estimación)", ha="center", va="top", fontsize=12, color=TXT2)

    # carril del lakehouse
    y2 = 4
    _caja(ax, 0, y2, w, h, "4 fuentes\ndel Lakehouse", SALUD_CLARO, SALUD, fs=12.5)
    _flecha(ax, w + .4, y2 + h / 2, 16.4, y2 + h / 2, color=SALUD)
    _caja(ax, 16.8, y2, 63.2, h, "Una consulta SQL\nubica estaciones, traduce códigos y une aire, salud y población", SALUD_CLARO, SALUD, fs=13.5, negrita=True)
    _flecha(ax, 80.4, y2 + h / 2, 83.6, y2 + h / 2, color=SALUD)
    _caja(ax, 84, y2, 16, h, "Respuesta", SALUD_CLARO, SALUD, fs=14, negrita=True)
    ax.text(92, y2 - 2.4, f"{total_segundos:.0f} s en esta demostración", ha="center", va="top", fontsize=12, color=TXT2)
    plt.tight_layout()
    plt.show()


# ── 2. Qué hay que unir ────────────────────────────────────────────────────────
def diagrama_uniones():
    fig, ax = _lienzo(13, 5.4, (-1.2, 101.2), (0, 54))
    fc, ec = "#f3f2ef", "#c9c8c2"

    def institucion(x, y, w, h, titulo, tablas, aire=False, salud=False):
        color_ec = AIRE if aire else (SALUD if salud else ec)
        color_fc = AIRE_CLARO if aire else (SALUD_CLARO if salud else fc)
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=color_fc, ec=color_ec, lw=1.4))
        ax.text(x + w / 2, y + h - 3.6, titulo, ha="center", va="center", fontsize=14.5, fontweight="bold", linespacing=1.2)
        ax.text(x + w / 2, y + 4.6, tablas, ha="center", va="center", fontsize=10.5, family="monospace", color=TXT2, linespacing=1.4)

    ancho, alto = 23, 17
    institucion(2, 2, ancho, alto, "MMA (SINCA)\nCalidad del aire", "sinca_estaciones\nsinca_mediciones", aire=True)
    institucion(2, 35, ancho, alto, "SUBDERE\nLímites de comunas", "subdere_comunas")
    institucion(38.5, 2, ancho, alto, "MINSAL (DEIS)\nConsultas (REM)", "deis_hechos\ndeis_establecimientos", salud=True)
    institucion(38.5, 35, ancho, alto, "MINSAL (DEIS)\nDiccionario de códigos", "deis_codigos", salud=True)
    institucion(75, 2, ancho, alto, "INE (Censo 2024)\nPoblación", "ine_viviendas")

    def union_h(x0, x1, y, pregunta, detalle):
        _flecha(ax, x0, y, x1, y, color=TXT2, lw=2, estilo="<|-|>")
        ax.text((x0 + x1) / 2, y + 3.6, pregunta, ha="center", va="center", fontsize=15, fontweight="bold")
        ax.text((x0 + x1) / 2, y - 3.4, detalle, ha="center", va="center", fontsize=11.5, color=TXT2)

    def union_v(x, y0, y1, pregunta, detalle):
        _flecha(ax, x, y0, x, y1, color=TXT2, lw=2, estilo="<|-|>")
        ax.text(x + 2.5, (y0 + y1) / 2 + 2, pregunta, ha="left", va="center", fontsize=15, fontweight="bold")
        ax.text(x + 2.5, (y0 + y1) / 2 - 2.6, detalle, ha="left", va="center", fontsize=11.5, color=TXT2)

    union_v(13.5, 19.6, 34.4, "¿Dónde?", "la estación cae en una comuna")
    union_h(25.6, 37.9, 10.5, "¿Cuándo?", "mes a mes")
    union_h(62, 74.4, 10.5, "¿De quién?", "código de comuna")
    union_v(50, 19.6, 34.4, "¿Qué significa?", "código a nombre")
    plt.tight_layout()
    plt.show()


# ── 3. Paso 1: estaciones en su comuna ──────────────────────────────────────────
def mapa_estaciones(estaciones, poligonos, poligono_comuna, cut):
    fig, (ax, az) = plt.subplots(1, 2, figsize=(13, 5.4), gridspec_kw={"width_ratios": [1.45, 1]})
    for fila, partes in _grupos(poligonos):
        propia = fila.cut_com == cut
        for p in partes:
            x, y = p.exterior.xy
            ax.fill(x, y, fc=SALUD_CLARO if propia else "#f1f0ed", ec=SALUD if propia else "#c9c8c2", lw=1.6 if propia else .7)
    desplaza = {"Pudahuel": (-58, -14), "Cerro Navia": (6, 7), "Cerrillos": (-62, -16)}
    etiquetadas = set()
    for fila in estaciones.itertuples():
        propia = str(fila.cut_com) == cut
        ax.scatter(fila.lon, fila.lat, s=95 if propia else 55, color=AIRE, ec="white", lw=1.5, zorder=3)
        if fila.comuna in etiquetadas:      # una etiqueta por comuna (hay comunas con varias estaciones)
            continue
        etiquetadas.add(fila.comuna)
        ax.annotate(fila.comuna, (fila.lon, fila.lat), xytext=desplaza.get(fila.comuna, (7, 6)), textcoords="offset points",
                    fontsize=11 if propia else 9.5, fontweight="bold" if propia else "normal", color=TXT if propia else TXT2, zorder=4)
    ax.set_xlim(estaciones.lon.min() - .3, estaciones.lon.max() + .25)
    ax.set_ylim(estaciones.lat.min() - .2, estaciones.lat.max() + .16)
    ax.set_aspect("equal"); ax.set_axis_off()
    ax.set_title("Estaciones de la Región Metropolitana, cada una en su comuna", fontsize=13.5, loc="left", color=TXT2)

    propia = estaciones[estaciones.cut_com.astype(str) == cut].iloc[0]
    for fila, partes in _grupos(poligono_comuna):
        for p in partes:
            x, y = p.exterior.xy
            az.fill(x, y, fc=SALUD_CLARO, ec=SALUD, lw=2)
    az.scatter(propia.lon, propia.lat, s=190, color=AIRE, ec="white", lw=2, zorder=3)
    az.annotate(propia.estacion, (propia.lon, propia.lat), xytext=(10, 12), textcoords="offset points", fontsize=12, fontweight="bold")
    az.set_aspect("equal"); az.set_axis_off()
    az.set_title("ST_Contains(polígono, punto) = verdadero", fontsize=13.5, loc="left", color=TXT2)
    plt.tight_layout()
    plt.show()


# ── 4. Paso 2: aire diario ───────────────────────────────────────────────────────


# ── 5. Paso 3: consultas por causa ───────────────────────────────────────────────
def _apilar(ax, tabla, columna):
    base = pd.Series(0.0, index=tabla.index)
    for causa in [c for c in ORDEN_CAUSAS if c in tabla.columns]:
        ax.bar(pd.to_datetime(tabla.index) + pd.Timedelta(days=14), tabla[causa], bottom=base, width=24, color=CAUSA_COLOR[causa], ec="white", lw=.9, label=causa)
        base = base + tabla[causa]


def salud_apilado(union):
    tabla = union.pivot_table(index="mes", columns="causa", values="consultas", aggfunc="sum")
    fig, ax = plt.subplots(figsize=(12.5, 4.9))
    _invierno(ax, sorted(set(tabla.index.year)))
    _apilar(ax, tabla, "consultas")
    ax.set_ylabel("consultas en el mes")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: miles(v)))
    _ejes(ax); _eje_meses(ax)
    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, loc="upper center", bbox_to_anchor=(.5, -.1), ncol=5, fontsize=11.5, columnspacing=1.2, handlelength=1.2)
    plt.tight_layout()
    plt.show()


# ── 6. Diccionario: antes y después ──────────────────────────────────────────────
def diccionario(antes_despues):
    n = len(antes_despues)
    fig, ax = _lienzo(12.5, 2.9, (0, 100), (0, 4.6 * (n + 1)))
    alto = 3.4
    ax.text(0, 4.6 * n + .8, "Lo que publica el REM", fontsize=13.5, fontweight="bold", color=TXT2, va="bottom")
    ax.text(60, 4.6 * n + .8, "Con el diccionario aplicado", fontsize=13.5, fontweight="bold", color=TXT2, va="bottom")
    for i, fila in enumerate(antes_despues.itertuples()):
        y = 4.6 * (n - 1 - i)
        _caja(ax, 0, y, 46, alto, f"{fila.codigo_publicado}     col01     {miles(fila.valor):>6}", "#f3f2ef", "#c9c8c2", fs=13, mono=True)
        _flecha(ax, 47, y + alto / 2, 59, y + alto / 2, color=SALUD)
        _caja(ax, 60, y, 40, alto, f"{fila.significado}   ({miles(fila.valor)})", SALUD_CLARO, SALUD, fs=13)
    plt.tight_layout()
    plt.show()


# ── 7. Paso 4: la tasa por mil habitantes ────────────────────────────────────────
def ecuacion_tasa(consultas, habitantes, etiqueta_mes):
    fig, ax = _lienzo(12.5, 2.6, (0, 100), (0, 20))
    y, h = 5, 10
    _caja(ax, 0, y, 27, h, f"{miles(consultas)}\nconsultas de {etiqueta_mes}", SALUD_CLARO, SALUD, fs=14)
    ax.text(30, y + h / 2, "÷", fontsize=26, ha="center", va="center", color=TXT2)
    _caja(ax, 33, y, 27, h, f"{miles(habitantes)}\nhabitantes", "#f3f2ef", "#c9c8c2", fs=14)
    ax.text(63, y + h / 2, "× 1.000 =", fontsize=19, ha="left", va="center", color=TXT2)
    _caja(ax, 80, y, 20, h, f"{coma(consultas / habitantes * 1000)}\npor mil habitantes", SALUD_CLARO, SALUD, fs=14, negrita=True)
    plt.tight_layout()
    plt.show()


# ── 8. Paso 5: aire y consultas, dos paneles con el mismo eje de tiempo ──────────


# ── 9. Respuesta: invierno frente a verano ──────────────────────────────────────
def invierno_verano(resumen):
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.7))
    datos = [
        ("MP2,5 (µg/m³)", resumen["mp25_verano"], resumen["mp25_invierno"], AIRE, 0),
        ("Consultas respiratorias por mil habitantes, por mes", resumen["consultas_verano"], resumen["consultas_invierno"], SALUD, 1),
    ]
    for ax, (titulo, verano, invierno, color, d) in zip(axs, datos):
        ax.bar([0, 1], [verano, invierno], width=.5, color=[GRIS, color], ec="white")
        for x, v in ((0, verano), (1, invierno)):
            ax.text(x, v * 1.02, coma(v, 0 if d == 0 else 1), ha="center", va="bottom", fontsize=17, fontweight="bold")
        ax.set_xticks([0, 1]); ax.set_xticklabels(["verano\n(dic a feb)", "invierno\n(may a ago)"], fontsize=13.5)
        ax.set_ylim(0, invierno * 1.28)
        ax.set_title(titulo, loc="left", fontsize=14, color=TXT2)
        ax.text(.5, invierno * 1.2, f"{coma(invierno / verano)} veces", ha="center", fontsize=17, fontweight="bold", color=TXT)
        ax.set_yticks([]); ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(GRILLA)
    plt.tight_layout()
    plt.show()


# ── 10. Relación mes a mes ───────────────────────────────────────────────────────
def dispersion(union, correlacion):
    mensual = union.groupby("mes").agg(mp25=("mp25", "first"), consultas=("consultas_por_mil", "sum"))
    invierno = pd.to_datetime(mensual.index).month.isin([5, 6, 7, 8])
    fig, ax = plt.subplots(figsize=(9.2, 4.9))
    ax.scatter(mensual.mp25[~invierno], mensual.consultas[~invierno], s=95, color=GRIS, ec="white", lw=1.3, label="otros meses", zorder=3)
    ax.scatter(mensual.mp25[invierno], mensual.consultas[invierno], s=95, color=SALUD, ec="white", lw=1.3, label="invierno (may a ago)", zorder=3)
    pendiente, origen = np.polyfit(mensual.mp25.values, mensual.consultas.values, 1)
    xs = [mensual.mp25.min(), mensual.mp25.max()]
    ax.plot(xs, [origen + pendiente * x for x in xs], color=GRIS, lw=1.2, zorder=2)
    ax.text(.03, .94, f"correlación {coma(correlacion, 2)}", transform=ax.transAxes, fontsize=14, fontweight="bold", va="top")
    ax.set_xlabel("MP2,5 del mes (µg/m³)"); ax.set_ylabel("consultas por mil habitantes")
    ax.set_ylim(bottom=0)
    _ejes(ax, "both")
    ax.legend(loc="lower right", fontsize=12)
    plt.tight_layout()
    plt.show()


# ── 11. Mapa del invierno ─────────────────────────────────────────────────────────


# ── 12. Tiempos ───────────────────────────────────────────────────────────────────
def tiempos(datos):
    etiquetas = list(datos)[::-1]
    valores = [datos[e] for e in etiquetas]
    fig, ax = plt.subplots(figsize=(12, 4.3))
    ax.barh(etiquetas, valores, color=SALUD, height=.55)
    for i, v in enumerate(valores):
        ax.text(v + max(valores) * .012, i, "menos de 0,1 s" if v < .05 else f"{coma(v)} s", va="center", fontsize=13)
    ax.set_xlim(0, max(valores) * 1.12)
    ax.set_xlabel("segundos")
    _ejes(ax, "x"); ax.spines["bottom"].set_color(GRILLA)
    ax.tick_params(axis="y", length=0)
    plt.tight_layout()
    plt.show()
