# pip install duckdb

import duckdb
import requests

url = "https://ee98cnfz7e.execute-api.us-west-2.amazonaws.com/prod"
sesion = requests.post(f"{url}/auth/login", json={"email": "tu-email@ejemplo.com", "password": "tu-contraseña"}).json()
cred = requests.post(f"{url}/auth/session/s3", headers={"Authorization": f"Bearer {sesion['id_token']}"}).json()
key, secret, token = cred["access_key_id"], cred["secret_access_key"], cred["session_token"]

duckdb.sql(f"CREATE SECRET (TYPE S3, KEY_ID '{key}', SECRET '{secret}', SESSION_TOKEN '{token}', REGION 'us-west-2')")

mediciones = duckdb.read_parquet("s3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet")   # lazy: aún no lee datos
mediciones.filter("year >= 2020").aggregate("count(*) AS mediciones").show()
