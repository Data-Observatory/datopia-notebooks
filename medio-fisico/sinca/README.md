# SINCA — Calidad del Aire y Meteorología

Dataset de calidad del aire y meteorología de **SINCA** (Sistema de Información Nacional de
Calidad del Aire), operado por el Ministerio del Medio Ambiente de Chile. 212 estaciones activas
en las 16 regiones de Chile, cobertura desde 1971 (red completa desde 2000).

## Notas sobre los datos

**Particionado NO uniforme — importante.** El mes en curso se almacena por día
(`year=/month=/day=/part-00000.parquet`); al cerrar el mes, `sinca-monthly-consolidator` fusiona
los archivos diarios en uno solo por mes (`year=/month=/part-00000.parquet`) y elimina los
diarios. Un mismo `tipo=medicion-diaria/version=v1/year=YYYY/` puede tener meses con ambas
profundidades simultáneamente.

**No usar `hive_partitioning=true` sobre rangos que mezclen ambas profundidades.** DuckDB exige
que todos los archivos leídos en una misma llamada `read_parquet` compartan el mismo conjunto de
claves Hive — falla con `Binder Error: Hive partition mismatch` si se combinan meses con `day=` y
meses sin él. La columna `fecha` (timestamp) ya está presente en cada archivo independientemente
del particionado físico: filtra con `WHERE fecha >= ... AND fecha < ...` en vez de columnas
`year`/`month`/`day` derivadas del path, y omite `hive_partitioning` (o pásalo en `false`).

```python
# Correcto — funciona sobre meses consolidados y meses en curso por igual
con.execute(f"""
    SELECT * FROM read_parquet('{BASE}/tipo=medicion-diaria/version=v1/year=2026/**/*.parquet')
    WHERE fecha >= DATE '2026-01-01' AND fecha < DATE '2026-07-01'
""")
```

**Formato long.** Una fila por (`fecha`, `estacion_id`, `variable_code`, `periodicidad`). Nunca
pivotado. `periodicidad` es `"diario"` (promedio diario) u `"horario"`. El promedio diario de un
día solo aparece una vez el día está completo — el día en curso todavía no tiene filas `diario`.

**Calidad del dato.** `calidad_id`: 1 = validado, 2 = preliminar, 3 = no validado (ver
`tipo=calidad`). Los días recientes suelen estar en preliminar/no validado — este notebook no
filtra por calidad para no perder los meses más recientes; para análisis riguroso, filtrar
`calidad_id IN (1, 2)`.

**No todas las estaciones miden todas las variables.** `tipo=estaciones-variables` indica qué
variables mide cada estación. PM2.5 es la más extendida (~96 de 212 estaciones activas), pero
gases específicos (p. ej. hidrocarburos NMHC/THCM/CH4, unidad ppm) solo se miden en unas pocas
estaciones industriales (zona de Quintero-Puchuncaví, Región de Valparaíso).

**Diccionario de variables incompleto.** `tipo=variables` cubre 23 de los 26 códigos que
realmente aparecen en `tipo=estaciones-variables` (faltan `CORG`, `CTOT`, `TRSG` — sin
nombre/unidad documentados; su significado no pudo confirmarse contra la fuente SINCA, así que
se dejaron fuera deliberadamente en vez de adivinar).

**Estaciones sin geometría.** 2 de las 212 estaciones activas (Punta Chungo, Rural 1) no tienen
coordenadas válidas en la fuente SINCA — `geometry`/`lon`/`lat` son nulos para esas filas; no
asumir que todas las estaciones tienen ubicación.

## Notas de actualización 2026-08-05

A raíz del EDA inicial (documento "EDA DO-SINCA") se encontraron y corrigieron varios problemas
reales en el pipeline. Resumen de lo que cambió — relevante si ya tenías queries o resultados
guardados de antes de esta fecha:

- **Variables meteorológicas: 6 de 7 ahora tienen mediciones.** `TEMP`, `RHUM`, `WSPD`, `PRES`,
  `RAIN`, `GLOB` ya aparecen en `medicion-diaria` (antes: cero filas para las 7, pese a estar
  bien catalogadas). Causa: bug de URL en el discovery de macropaths meteorológicos + un segundo
  bug en cómo se armaba el nombre del macro para pedirle datos al CGI de SINCA (las variables
  meteorológicas no siguen el mismo esquema que las de calidad del aire). **`WDIR` (dirección del
  viento) sigue sin datos** — es una limitación de la fuente (SINCA devuelve una rosa de los
  vientos, no una serie de tiempo, para esa variable puntual), no algo que podamos corregir
  nosotros por ahora.
- **`tipo=variables`: 5 códigos numéricos corregidos a su forma mnemónica.** `SO2`, `NO`, `NO2`,
  `CO`, `O3` estaban guardados con el código interno numérico de SINCA (`0001`-`0008`) en vez de
  la forma mnemónica que usan `estaciones-variables`/`medicion-diaria` — cualquier join contra
  esos 5 códigos no encontraba nada. Si filtraste alguna vez por `variable_code = '0008'`
  esperando O3 (como hacía este mismo notebook), ahora es `variable_code = 'O3'`.
- **Columna `tipo` renombrada a `variable_tipo`** en `tipo=variables` y `tipo=estaciones-variables`.
  Motivo: toda tabla de SINCA vive bajo un segmento de ruta S3 `tipo={nombre-tabla}` — un motor de
  consultas que autodetecta particionado Hive a partir de la ruta (DuckDB lo hace por defecto, sin
  necesidad de ningún flag) enmascaraba silenciosamente la columna real
  (`calidad_aire`/`meteorologico`) con el string del nombre de tabla derivado de la ruta, sin
  ningún error. **Si en tu EDA obtuviste `tipo == "estaciones-variables"` para todas las filas,
  era exactamente este bug** — no es un problema del dato en sí, era el propio motor de consultas
  enmascarando la columna real. Cualquier query anterior que hiciera `SELECT tipo` o
  `WHERE tipo = ...` sobre estas dos tablas debe actualizarse a `variable_tipo`.
- **`tipo=estaciones-variables`: unificado el discovery.** Antes se armaba con una regex más
  estricta que el extractor de mediciones, y por eso 2 estaciones con mediciones reales (D14
  Parque O'Higgins, 837 Nueva Libertad) no aparecían en este catálogo. Ya corregido.
- **Fecha `2099-12-29` en estación 819 corregida** (y cualquier otra fecha pre-2000 mal
  interpretada en `fecha_primer_registro`/`fecha_ultimo_registro`): bug de parseo de años de 2
  dígitos, mismo patrón que ya estaba bien resuelto en otro archivo del pipeline pero nunca se
  portó a este.
- **`tipo=estaciones`: reseteada, ya no acumula historia SCD-2 espuria.** Un bug de comparación
  hacía que casi todas las 212 estaciones se marcaran como "cambiadas" en cada actualización
  semanal, aunque nada hubiera cambiado realmente — esto inflaba la tabla con filas cerradas sin
  sentido semana tras semana. Corregido y verificado en vivo (0 cambios espurios en dos corridas
  consecutivas). La tabla se reseteó a una fila activa por estación; si alguna vez cargaste
  `tipo=estaciones` sin filtrar por `fecha_fin IS NULL` para mirar "historia", esa historia previa
  a esta fecha ya no está disponible (se guardó un respaldo en `_backup/` en S3 por si se necesita).
- **`demo.ipynb` corregido**: la sección 5 (perfil multi-variable) filtraba por el código viejo
  `variable_code = '0008'` esperando O3 — con el fix del punto 2, ese filtro nunca iba a encontrar
  nada. Ya usa `'O3'`.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `demo.ipynb` | Notebook de demostración: autenticación, mapa, series de tiempo, EDA mínimo y modelo lineal simple |
