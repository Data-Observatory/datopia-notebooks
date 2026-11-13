# DTPM — GTFS: horarios y recorridos

Horarios y recorridos del transporte público de la Región Metropolitana (buses, Metro, tren), según los feeds
GTFS que publica el DTPM (Directorio de Transporte Público Metropolitano) desde 2014. El feed vigente se revisa
a diario y todos los feeds anteriores se conservan.

## Notas sobre los datos

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

**Relación con RED Movilidad.** Las posiciones GPS de la flota (`red-movilidad`) se particionan por día UTC;
para cruzarlas con `fecha_servicio` hay que convertir antes la hora UTC a hora de Santiago.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `demo.ipynb` | Notebook de demostración: feed vigente por fecha, rutas, paradas, frecuencias y trazados |
