# Snippets de conexión

Leer Parquet del Datopia Lakehouse. Cada archivo es un snippet corto y ejecutable; la consulta de
ejemplo cuenta mediciones por año en `sinca / medicion-diaria`.

| Carpeta | Credenciales |
|---|---|
| `credenciales-pagina/` | Las copias desde la página: pega `key`, `secret`, `token` en la primera línea |
| `login-api/` | Se obtienen por código: reemplaza `tu-email@ejemplo.com` y `tu-contraseña` |

Son temporales (1 h).

| Archivo | Herramienta | Lazy |
|---|---|---|
| `python-duckdb.py` | DuckDB | `read_parquet` → relación |
| `python-polars.py` | Polars | `scan_parquet` → `LazyFrame` |
| `python-pyarrow.py` | PyArrow | `dataset` |
| `python-pandas.py` | pandas | no (`columns` y `filters` acotan la lectura) |
| `r-duckdb.R` | DuckDB + dplyr | `tbl()` → SQL |
| `r-arrow.R` | Arrow + dplyr | `open_dataset` |
| `julia-duckdb.jl` | DuckDB.jl | SQL con pushdown |
| `nodejs-duckdb.mjs` | `@duckdb/node-api` | SQL con pushdown |
| `duckdb-cli.sh` | CLI de DuckDB | SQL con pushdown |

## Notas

- Las carpetas del lakehouse traen `dataset.json` y `manifest.json` junto a los `.parquet`: PyArrow,
  Arrow (R) y pandas fallan con "Parquet magic bytes not found" si no se ignoran (`ignore_prefixes`).
  DuckDB y Polars usan el glob `part-*.parquet` y no lo necesitan.
- Julia: se fija DuckDB.jl 1.4; el build de desarrollo no incluye `httpfs` y no puede leer `s3://`.
