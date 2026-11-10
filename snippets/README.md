# Snippets

Código mínimo para leer el Datopia Lakehouse. Para análisis, ver los notebooks de cada dataset.

| Carpeta | Para qué |
|---|---|
| [`conexion/`](conexion/) | Conectar y leer Parquet desde DuckDB, Polars, PyArrow, pandas, R, Julia, Node y CLI. Credenciales pegadas desde la página o por login. |
| [`particiones/`](particiones/) | Leer un dataset particionado (`year=YYYY/`) solo en las particiones necesarias. Ejemplo: `salud/deis-rem`. |
| [`geoespacial/`](geoespacial/) | Leer GeoParquet filtrando por caja geográfica y pasarlo a geopandas / sf. Ejemplo: `transporte/red-movilidad`. |

`particiones/` y `geoespacial/` usan credenciales pegadas desde la página; para login por código,
reemplaza la primera línea por el bloque de `conexion/login-api/`.

## JSON para el sitio

`snippets.es.json` y `snippets.en.json` (raíz del repo) se generan desde esta carpeta; **no se editan
a mano**: `python scripts/build_snippets.py`. Cada snippet se escribe en español; la versión en inglés
aplica las sustituciones de `traducciones-en.json`. Lenguajes, librerías y escenarios se declaran en
`meta.json`. Al agregar un snippet: crear el archivo, registrarlo en `meta.json`, generar y commitear.
