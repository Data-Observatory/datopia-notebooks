# DTPM — Transporte público de la Región Metropolitana

Datos del sistema de transporte público de la Región Metropolitana (Chile) provistos por el DTPM (Directorio de
Transporte Público Metropolitano), en dos notebooks: las posiciones GPS de la flota de buses de RED Movilidad
(`posiciones.ipynb`) y los horarios y recorridos GTFS (`demo.ipynb`).

> Las posiciones GPS se publican hoy bajo `fuente=red-movilidad` en S3 (`tipo=posicion-diaria`) y se moverán a
> `fuente=dtpm` más adelante; el GTFS ya vive en `fuente=dtpm`.

## Posiciones GPS diarias (RED Movilidad) — `posiciones.ipynb`

Dataset de posiciones GPS del sistema de transporte público RED Movilidad (Región Metropolitana, Chile), provisto por la API del DTP Metropolitano (DTPM).

### Notas sobre los datos

**Tiempos en UTC.** El campo `timestamp_gps_utc` está en UTC. Para análisis en hora local usar la zona `America/Santiago`, que maneja el horario de verano automáticamente (UTC-3 en octubre–marzo, UTC-4 en abril–septiembre).

**Particionado por día UTC.** Los archivos están organizados en `year=/month=/day=` según día UTC, no local. Un día UTC comienza a las 20:00–21:00 hora chilena del día anterior, por lo que al filtrar por fecha local es necesario cargar el día UTC siguiente y aplicar el filtro en la consulta.

**Formato GeoParquet.** La columna `geometry` contiene puntos WKB en EPSG:4326 (WGS 84). Los archivos declaran GeoParquet 1.0.0 en su metadato `geo` (verificado el 2026-11-12 en los 377 archivos diarios); los datasets nuevos del Lakehouse usan 1.1. Las consultas espaciales requieren la extensión `spatial` de DuckDB.

**Fuente de origen.** Los datos provienen directamente de la API `/posiciones` del DTPM y se consolidan diariamente en el Datopia Lakehouse. No se aplican correcciones ni imputaciones sobre los valores originales.

### Estrategias de consulta

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

## Horarios y recorridos (GTFS) — `demo.ipynb`

Horarios y recorridos del transporte público de la Región Metropolitana (buses, Metro, tren), según los feeds
GTFS que publica el DTPM (Directorio de Transporte Público Metropolitano) desde 2014. El feed vigente se revisa
a diario y todos los feeds anteriores se conservan.

### Notas sobre los datos

**Ruta S3.** `s3://do-datopia/categoria=transporte/pais=cl/fuente=dtpm/tipo=gtfs-<nombre>/version=v1/`. Son 15
tablas planas, sin particiones por fecha: `gtfs-feeds`, `gtfs-vigencia`, `gtfs-agency`, `gtfs-routes`,
`gtfs-trips`, `gtfs-stop-times`, `gtfs-stops`, `gtfs-shapes`, `gtfs-shapes-lineas`, `gtfs-frequencies`,
`gtfs-calendar`, `gtfs-calendar-dates`, `gtfs-pathways`, `gtfs-levels` y `gtfs-transfers`.

**Una copia completa por feed.** Todas las tablas llevan `feed_id` y cada feed se guarda completo, sin
deduplicar. Filtrar siempre por `feed_id` antes de leer `gtfs-stop-times` o `gtfs-shapes`, que son muy grandes.
La clave es `feed_id`, no `feed_version` (esta se repite entre feeds distintos).

**Qué feed rige un día.** Resolverlo solo con `gtfs-vigencia` (`fecha_servicio` es el día calendario de
Santiago). Hay fechas sin feed y feeds de evento especial que rigen un solo día.

**Formato.** Solo `gtfs-stops` (puntos) y `gtfs-shapes-lineas` (una línea por `shape_id`) son GeoParquet
(versión 1.1); el resto es Parquet. Las consultas espaciales requieren la extensión `spatial` de DuckDB.

**Relación con las posiciones.** Las posiciones GPS de la flota (ver arriba) se particionan por día UTC;
para cruzarlas con `fecha_servicio` hay que convertir antes la hora UTC a hora de Santiago.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `demo.ipynb` | Horarios y recorridos GTFS (feeds del DTPM desde 2014): feed vigente por fecha, rutas, paradas, frecuencias y trazados |
| `posiciones.ipynb` | Posiciones GPS diarias de la flota de RED Movilidad: autenticación, exploración, consultas y visualizaciones |
