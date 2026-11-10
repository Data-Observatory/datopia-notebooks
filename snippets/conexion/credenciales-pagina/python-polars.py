# pip install polars

import polars as pl

key, secret, token = "ASIA...", "...", "..."   # pegar desde la página (duran 1 h)

opciones = {"aws_access_key_id": key, "aws_secret_access_key": secret, "aws_session_token": token, "aws_region": "us-west-2"}

mediciones = pl.scan_parquet("s3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet", storage_options=opciones)   # lazy: solo arma el plan
print(mediciones.filter(pl.col("year") >= 2020).select(pl.len()).collect())
