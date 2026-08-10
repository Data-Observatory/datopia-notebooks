# SINCA — Calidad del Aire y Meteorología

Dataset de calidad del aire y meteorología de **SINCA** (Sistema de Información Nacional de
Calidad del Aire), operado por el Ministerio del Medio Ambiente de Chile. 212 estaciones activas
en las 16 regiones de Chile, cobertura desde 1971 (red completa desde 2000).

## Notas sobre los datos

**Layout plano, sin particiones.** `tipo=medicion-diaria/version=v1/` no usa `year=/month=/day=`.
Son solo unos pocos archivos `part-NNNNN.parquet` (ver `manifest.json` en la misma ruta para la
lista exacta) — todos menos el último están permanentemente congelados; el último es el "abierto"
que el merger diario actualiza, y se sella en uno nuevo al acercarse a ~200MB. En la práctica:
siempre glob `part-*.parquet` y filtra por fecha en el `WHERE`, sin distinguir formatos ni usar
`hive_partitioning`.

```python
con.execute(f"""
    SELECT * FROM read_parquet('{BASE}/tipo=medicion-diaria/version=v1/part-*.parquet')
    WHERE fecha >= DATE '2026-01-01' AND fecha < DATE '2026-07-01'
""")
```

**Formato long, con claves surrogate.** Una fila por (`fecha`, `estacion_fk`, `variable_fk`,
`periodicidad_fk`). `estacion_fk`/`variable_fk` son enteros — hay que hacer `JOIN` contra
`tipo=estaciones`/`tipo=variables` para obtener los códigos legibles (`estacion_id`,
`variable_code`; ver `demo.ipynb`, sección 2, para el patrón). `periodicidad_fk`: `0=horario,
1=diario, 2=discreto` (sin tabla de referencia, son solo 3 valores fijos). El promedio diario de
un día solo aparece una vez el día está completo — el día en curso todavía no tiene filas
`periodicidad_fk=1`.

Nota: `tipo=estaciones-variables` (el catálogo de qué variable mide cada estación) usa
`estacion_id`/`variable_code` como texto, sin fk — solo `medicion-diaria` usa claves surrogate.
`variable_code` siempre está en su forma mnemónica (`SO2`, `NO`, `NO2`, `CO`, `O3`, etc.), nunca
el código interno numérico de SINCA.

**Calidad del dato.** `calidad_id`: 1 = validado, 2 = preliminar, 3 = no validado (ver
`tipo=calidad`). Los días recientes suelen estar en preliminar/no validado — este notebook no
filtra por calidad para no perder los meses más recientes; para análisis riguroso, filtrar
`calidad_id IN (1, 2)`. El pipeline nunca elimina filas: siempre corrige "in place" (sobrescribe
con el valor más reciente/mejor calidad para esa fecha-estación-variable-periodicidad).

**`tipo=estaciones` usa SCD-2.** `fecha_fin IS NULL` = fila activa. `fecha_inicio`/`fecha_fin`
son sobre la ficha de la estación (nombre, propietario, coordenadas, etc.), no sobre sus
mediciones — las fechas de cobertura real (`fecha_primer_registro`/`fecha_ultimo_registro`) están
en `tipo=estaciones-variables`, por combinación estación-variable-periodicidad.

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

**Variables meteorológicas.** 6 de 7 tienen mediciones: `TEMP`, `RHUM`, `WSPD`, `PRES`, `RAIN`,
`GLOB`, siempre en `periodicidad = 'horario'` (SINCA no publica agregado diario para meteo).
**`WDIR` (dirección del viento) no tiene datos** — limitación de la fuente: SINCA devuelve una
rosa de los vientos, no una serie de tiempo, para esa variable puntual.

**Columna `variable_tipo`** (no `tipo`) en `tipo=variables` y `tipo=estaciones-variables`.
Motivo: toda tabla de SINCA vive bajo un segmento de ruta S3 `tipo={nombre-tabla}` — un motor de
consultas que autodetecta particionado Hive a partir de la ruta (DuckDB lo hace por defecto, sin
necesidad de ningún flag) enmascararía la columna real (`calidad_aire`/`meteorologico`) con el
nombre de tabla derivado de la ruta si se llamara igual.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `demo.ipynb` | Notebook de demostración: autenticación, catálogo, cobertura, calidad, mapa, series de tiempo, EDA mínimo y modelo lineal simple |

## Historial de cambios

- **2026-08-05**: corregida la captura de variables meteorológicas (6/7 pasaron a tener datos);
  normalizados 5 códigos numéricos heredados en `tipo=variables`; renombrada `tipo` →
  `variable_tipo`; corregido el discovery de catálogo para la estación 837 (Nueva Libertad);
  corregido el parseo de años de 2 dígitos (fechas pre-2000); resuelto un bug de SCD-2 que
  reseteaba `tipo=estaciones` en cada actualización semanal sin cambios reales.
- **2026-08-09**: `medicion-diaria` migrada a layout plano + claves surrogate (ver "Notas sobre
  los datos" arriba); corregido el discovery de catálogo para Parque O'Higgins (D14, bug de
  apóstrofe en el nombre); normalizados códigos numéricos heredados en
  `tipo=estaciones-variables` (134/73/85/72/79 estaciones); `demo.ipynb` reescrito para el nuevo
  esquema.
- **2026-08-10**: agregadas a `demo.ipynb` celdas de cobertura (`variables_de`/
  `estaciones_que_miden`), frescura, distribución de calidad y detector de huecos
  (`huecos_serie`); cacheo de metadata S3/Parquet entre consultas.
