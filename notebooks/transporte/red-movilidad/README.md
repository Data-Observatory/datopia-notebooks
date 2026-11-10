# RED Movilidad — Posiciones GPS Diarias

Dataset de posiciones GPS del sistema de transporte público RED Movilidad (Región Metropolitana, Chile), provisto por la API del DTP Metropolitano (DTPM).

## Notas sobre los datos

**Tiempos en UTC.** El campo `timestamp_gps_utc` está en UTC. Para análisis en hora local usar la zona `America/Santiago`, que maneja el horario de verano automáticamente (UTC-3 en octubre–marzo, UTC-4 en abril–septiembre).

**Particionado por día UTC.** Los archivos están organizados en `year=/month=/day=` según día UTC, no local. Un día UTC comienza a las 20:00–21:00 hora chilena del día anterior, por lo que al filtrar por fecha local es necesario cargar el día UTC siguiente y aplicar el filtro en la consulta.

**Formato GeoParquet.** La columna `geometry` contiene puntos WKB en EPSG:4326 (WGS 84). Las consultas espaciales requieren la extensión `spatial` de DuckDB.

**Fuente de origen.** Los datos provienen directamente de la API `/posiciones` del DTPM y se consolidan diariamente en el Datopia Lakehouse. No se aplican correcciones ni imputaciones sobre los valores originales.

## Estrategias de consulta

Los datos se pueden consultar de dos formas:

**Ruta general** (`{BASE}/**/*.parquet` + filtros `WHERE`):
- DuckDB lista todos los prefijos S3 y luego aplica pruning de particiones
- Código más simple y flexible para rangos dinámicos
- Mayor overhead inicial por el listado de prefijos (costoso si hay muchos meses/días)

```python
con.execute("""
    SELECT * FROM read_parquet('s3://.../version=v1/**/*.parquet', hive_partitioning=true)
    WHERE year=2026 AND month=5 AND day=1
""")
```

**Rutas explícitas** (`{BASE}/year=.../month=.../day=.../**/*.parquet`):
- DuckDB abre únicamente los prefijos indicados, sin listado global
- Más rápido y predecible en costo de red/S3
- Recomendado para rangos conocidos, dashboards y producción

```python
con.execute("""
    SELECT * FROM read_parquet([
        's3://.../year=2026/month=05/day=01/**/*.parquet',
        's3://.../year=2026/month=05/day=02/**/*.parquet'
    ], hive_partitioning=true)
""")
```

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `demo.ipynb` | Notebook de demostración: autenticación, exploración, consultas y visualizaciones |
