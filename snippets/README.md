# Snippets

Código mínimo para leer el Datopia Lakehouse. Para análisis, ver los notebooks de cada dataset.

| Carpeta | Para qué |
|---|---|
| [`conexion/`](conexion/) | Conectar y leer Parquet desde DuckDB, Polars, PyArrow, pandas, R, Julia, Node y CLI. Credenciales pegadas desde la página o por login. |
| [`particiones/`](particiones/) | Leer un dataset particionado (`year=YYYY/`) solo en las particiones necesarias. Ejemplo: `salud/deis-rem`. |
| [`geoespacial/`](geoespacial/) | Leer GeoParquet filtrando por caja geográfica y pasarlo a geopandas / sf. Ejemplo: `transporte/red-movilidad`. |

`particiones/` y `geoespacial/` usan credenciales pegadas desde la página; para login por código,
reemplaza la primera línea por el bloque de `conexion/login-api/`.
