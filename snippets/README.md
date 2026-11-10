# Snippets

Código mínimo para leer el Datopia Lakehouse. Para análisis, ver los notebooks de cada dataset.

| Carpeta | Para qué |
|---|---|
| [`conexion/`](conexion/) | Conectar y leer Parquet desde DuckDB, Polars, PyArrow, pandas, R, Julia, Node y CLI. Credenciales pegadas desde la página o por login. |
| [`particiones/`](particiones/) | Leer un dataset particionado (`year=YYYY/`) solo en las particiones necesarias. Ejemplo: `salud/deis-rem`. |
| [`geoespacial/`](geoespacial/) | Leer GeoParquet filtrando por caja geográfica y pasarlo a geopandas / sf. Ejemplo: `transporte/red-movilidad`. |
| [`catalogo/`](catalogo/) | Página HTML de ejemplo (un solo archivo, sin credenciales): muestra los datasets públicos, sus tablas y el diccionario de datos desde `datamodel.json`. |

`particiones/` y `geoespacial/` usan credenciales pegadas desde la página; para login por código,
reemplaza la primera línea por el bloque de `conexion/login-api/`.

## JSON para el sitio

`snippets.json` (raíz del repo) se genera desde esta carpeta; **no se edita a mano**:
`python scripts/build_snippets.py`. Trae todos los idiomas: cada texto y cada `code` es un objeto por
idioma (`{"es": ..., "en": ...}`) y `locales` los lista. Cada snippet se escribe en español; los demás
idiomas aplican las sustituciones de `traducciones-<idioma>.json`. Lenguajes, librerías y escenarios se
declaran en `meta.json`.

- **Agregar un snippet:** crear el archivo, registrarlo en `meta.json`, generar y commitear.
- **Agregar un idioma:** crear `traducciones-<idioma>.json` (copiar `traducciones-en.json`), agregar el
  idioma a cada texto de `meta.json` (`scenarios` y `lazy_note`) y generar. En idiomas que comparten
  palabras con el español (portugués) agregar `"omitir_chequeo_restos": true` al archivo de traducciones.
