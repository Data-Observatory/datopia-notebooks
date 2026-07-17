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
nombre/unidad documentados).

**Estaciones sin geometría.** 2 de las 212 estaciones activas (Punta Chungo, Rural 1) no tienen
coordenadas válidas en la fuente SINCA — `geometry`/`lon`/`lat` son nulos para esas filas; no
asumir que todas las estaciones tienen ubicación.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `demo.ipynb` | Notebook de demostración: autenticación, mapa, series de tiempo, EDA mínimo y modelo lineal simple |
