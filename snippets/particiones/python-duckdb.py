# pip install duckdb

import duckdb

key, secret, token = "ASIA...", "...", "..."   # pegar desde la página (duran 1 h)

duckdb.sql(f"CREATE SECRET (TYPE S3, KEY_ID '{key}', SECRET '{secret}', SESSION_TOKEN '{token}', REGION 'us-west-2')")

# hive_partitioning expone `year` (carpetas year=YYYY/) y solo lee las carpetas que pasan el filtro
rem = duckdb.read_parquet("s3://do-datopia/categoria=salud/pais=cl/fuente=deis/tipo=resumen-estadistico-mensual/version=v1/year=*/part-*.parquet", hive_partitioning=True)
rem.filter("year = 2024").aggregate("count(*) AS filas").show()   # solo lee la carpeta year=2024/
