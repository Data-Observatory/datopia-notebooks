# pip install polars

import polars as pl

key, secret, token = "ASIA...", "...", "..."   # pegar desde la página (duran 1 h)

opciones = {"aws_access_key_id": key, "aws_secret_access_key": secret, "aws_session_token": token, "aws_region": "us-west-2"}

# hive_partitioning expone `year` (carpetas year=YYYY/) y solo lee las carpetas que pasan el filtro
rem = pl.scan_parquet("s3://do-datopia/categoria=salud/pais=cl/fuente=deis/tipo=resumen-estadistico-mensual/version=v1/year=*/part-*.parquet", hive_partitioning=True, storage_options=opciones)
print(rem.filter(pl.col("year") == 2024).select(pl.len()).collect())   # solo lee la carpeta year=2024/
