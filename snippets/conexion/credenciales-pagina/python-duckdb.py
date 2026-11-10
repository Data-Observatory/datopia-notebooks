# pip install duckdb

import duckdb

key, secret, token = "ASIA...", "...", "..."   # pegar desde la página (duran 1 h)

duckdb.sql(f"CREATE SECRET (TYPE S3, KEY_ID '{key}', SECRET '{secret}', SESSION_TOKEN '{token}', REGION 'us-west-2')")

mediciones = duckdb.read_parquet("s3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet")   # lazy: aún no lee datos
mediciones.filter("year >= 2020").aggregate("count(*) AS mediciones").show()
