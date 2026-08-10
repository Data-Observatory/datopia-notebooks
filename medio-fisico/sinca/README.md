# SINCA — Calidad del Aire y Meteorología

Dataset de calidad del aire y meteorología de **SINCA** (Sistema de Información Nacional de
Calidad del Aire), operado por el Ministerio del Medio Ambiente de Chile. 212 estaciones activas
en las 16 regiones de Chile, cobertura desde 1971 (red completa desde 2000).

## Notas sobre los datos

**Layout plano, sin particiones (2026-08-09).** `tipo=medicion-diaria/version=v1/` ya no usa
`year=/month=/day=`. Son solo unos pocos archivos `part-NNNNN.parquet` (ver `manifest.json` en la
misma ruta para la lista exacta) — todos menos el último están permanentemente congelados; el
último es el "abierto" que el merger diario actualiza, y se sella en uno nuevo al acercarse a
~200MB. En la práctica: siempre glob `part-*.parquet` y filtra por fecha en el `WHERE`, sin
distinguir formatos ni usar `hive_partitioning`.

```python
con.execute(f"""
    SELECT * FROM read_parquet('{BASE}/tipo=medicion-diaria/version=v1/part-*.parquet')
    WHERE fecha >= DATE '2026-01-01' AND fecha < DATE '2026-07-01'
""")
```

**Formato long, con claves surrogate (2026-08-09).** Una fila por (`fecha`, `estacion_fk`,
`variable_fk`, `periodicidad_fk`). `estacion_fk`/`variable_fk` son enteros, no los códigos de
texto (`estacion_id`/`variable_code`) — hay que hacer `JOIN` contra `tipo=estaciones`/
`tipo=variables` para obtener los códigos legibles (ver `demo.ipynb`, sección 2, para el patrón).
Motivo: guardar el texto directamente inflaba ~48x el tamaño en memoria al procesar el archivo
completo. `periodicidad_fk`: `0=horario, 1=diario, 2=discreto` (sin tabla de referencia, son solo
3 valores fijos). El promedio diario de un día solo aparece una vez el día está completo — el día
en curso todavía no tiene filas `periodicidad_fk=1`.

Nota: `tipo=estaciones-variables` (el catálogo de qué variable mide cada estación) **no** cambió
de esquema — sigue usando `estacion_id`/`variable_code` como texto, sin fk. Solo `medicion-diaria`
migró a claves surrogate.

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
- **`tipo=estaciones-variables`: unificado el discovery para 837 (Nueva Libertad).** Antes se
  armaba con una regex más estricta que el extractor de mediciones, y por eso esta estación (con
  mediciones reales) no aparecía en el catálogo. *Corrección (2026-08-09): esto NO cubrió a D14 —
  ver más abajo, ese bug era otro y quedó sin corregir hasta ahora.*
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

## Notas de actualización 2026-08-09/10

- **`medicion-diaria` migró a layout plano + claves surrogate.** Ver las dos notas actualizadas
  arriba ("Layout plano" y "Formato long, con claves surrogate"). Motivo original: un full-corpus
  merge de 115M filas necesitaba ~17GB de RAM de trabajo (vs 360MB comprimido) para procesar el
  archivo completo, muy por sobre el límite del proceso diario -- separar en frozen/open + usar
  enteros en vez de texto lo resuelve.
- **Estación Parque O'Higgins (D14): catálogo `estaciones-variables` corregido.** Tenía cero
  variables declaradas pese a tener mediciones reales desde 1997 -- causa real: el nombre de la
  estación contiene un apóstrofe ("O'Higgins"), que rompía la regex que detecta el enlace en la
  página de SINCA (confundía el apóstrofe con el cierre de un atributo `href="..."`). Es un fix
  general (no específico de D14) que ahora maneja cualquier nombre de estación con comillas
  embebidas. D14 ahora muestra sus 26 combinaciones reales.
- **`tipo=estaciones-variables`: normalizados códigos numéricos heredados.** 134/73/85/72/79
  estaciones respectivamente tenían `0001`/`0002`/`0003`/`0004`/`0008` en vez de
  `SO2`/`NO`/`NO2`/`CO`/`O3` en esta tabla específicamente (el fix del 2026-08-05 solo cubrió
  `tipo=variables`, no este catálogo) -- rompía cualquier join contra el diccionario de variables
  para esas filas. Ya corregido.
- **`demo.ipynb` reescrito** para el nuevo esquema: todas las consultas sobre `medicion-diaria`
  ahora hacen `JOIN` contra `tipo=estaciones`/`tipo=variables` en vez de filtrar directamente por
  `estacion_id`/`variable_code` (ese filtro ya no funciona -- esas columnas no existen en
  `medicion-diaria`). Probado de punta a punta contra datos reales.

## Notas de actualización 2026-08-10

- **`demo.ipynb`: 5 celdas nuevas orientadas a analistas/testers**, en la sección de
  exploración del dataset:
  - Diccionario de variables: nota explícita sobre los 3 códigos sin documentar
    (`CORG`/`CTOT`/`TRSG`).
  - Ayuda de cobertura (`variables_de(estacion_id)` / `estaciones_que_miden(variable_code)`):
    responde directo "¿qué mide esta estación?" / "¿quién mide esta variable?" sin tener que
    escribir el `JOIN` a mano cada vez.
  - Frescura: última fecha disponible por estación y ranking de las más atrasadas.
  - Calidad: distribución global de `calidad_id` en mediciones diarias + ejemplo cuantificado
    de cuánto se pierde al filtrar a validado+preliminar.
  - Detector de huecos (`huecos_serie(...)`): días faltantes de una estación/variable en un
    rango de fechas dado.
  - Probado de punta a punta contra datos reales (`nbconvert --execute`).

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `demo.ipynb` | Notebook de demostración: autenticación, mapa, series de tiempo, EDA mínimo y modelo lineal simple |
