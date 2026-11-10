# pip install polars

import polars as pl
import requests

url = "https://ee98cnfz7e.execute-api.us-west-2.amazonaws.com/prod"
sesion = requests.post(f"{url}/auth/login", json={"email": "tu-email@ejemplo.com", "password": "tu-contraseña"}).json()
cred = requests.post(f"{url}/auth/session/s3", headers={"Authorization": f"Bearer {sesion['id_token']}"}).json()
key, secret, token = cred["access_key_id"], cred["secret_access_key"], cred["session_token"]

opciones = {"aws_access_key_id": key, "aws_secret_access_key": secret, "aws_session_token": token, "aws_region": "us-west-2"}

mediciones = pl.scan_parquet("s3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet", storage_options=opciones)   # lazy: solo arma el plan
print(mediciones.filter(pl.col("year") >= 2020).select(pl.len()).collect())
