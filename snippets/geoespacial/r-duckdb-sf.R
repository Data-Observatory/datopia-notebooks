# install.packages(c("duckdb", "DBI", "sf"))

library(DBI)
library(sf)

key <- "ASIA..."; secret <- "..."; token <- "..."   # pegar desde la página (duran 1 h)

con <- dbConnect(duckdb::duckdb())
dbExecute(con, sprintf("CREATE SECRET (TYPE S3, KEY_ID '%s', SECRET '%s', SESSION_TOKEN '%s', REGION 'us-west-2')", key, secret, token))
dbExecute(con, "INSTALL spatial")
dbExecute(con, "LOAD spatial")   # `geometry` es GeoParquet (WKB, EPSG:4326)

# Filtrar en DuckDB (una hora + una caja) y traer a sf solo el resultado: un día son ~10 M de puntos
df <- dbGetQuery(con, "
    SELECT plate, speed, ST_X(geometry) AS lon, ST_Y(geometry) AS lat
    FROM 's3://do-datopia/categoria=transporte/pais=cl/fuente=red-movilidad/tipo=posicion-diaria/version=v1/year=2025/month=10/day=15/part-*.parquet'
    WHERE timestamp_gps_utc BETWEEN '2025-10-15 12:00' AND '2025-10-15 13:00'
      AND ST_Within(geometry, ST_MakeEnvelope(-70.67, -33.46, -70.63, -33.42))   -- centro de Santiago
")
st_as_sf(df, coords = c("lon", "lat"), crs = 4326)
