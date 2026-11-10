# pip install duckdb geopandas

import duckdb
import geopandas as gpd

key, secret, token = "ASIA...", "...", "..."   # pegar desde la página (duran 1 h)

duckdb.sql(f"CREATE SECRET (TYPE S3, KEY_ID '{key}', SECRET '{secret}', SESSION_TOKEN '{token}', REGION 'us-west-2')")
duckdb.execute("INSTALL spatial; LOAD spatial")   # `geometry` es GeoParquet (WKB, EPSG:4326)

# Filtrar en DuckDB (una hora + una caja) y traer a geopandas solo el resultado: un día son ~10 M de puntos
df = duckdb.sql("""
    SELECT plate, speed, ST_X(geometry) AS lon, ST_Y(geometry) AS lat
    FROM 's3://do-datopia/categoria=transporte/pais=cl/fuente=red-movilidad/tipo=posicion-diaria/version=v1/year=2025/month=10/day=15/part-*.parquet'
    WHERE timestamp_gps_utc BETWEEN '2025-10-15 12:00' AND '2025-10-15 13:00'
      AND ST_Within(geometry, ST_MakeEnvelope(-70.67, -33.46, -70.63, -33.42))   -- centro de Santiago
""").df()
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
print(gdf.head())
