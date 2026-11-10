# pip install pyarrow

import pyarrow.dataset as ds
from pyarrow import fs
import requests

url = "https://ee98cnfz7e.execute-api.us-west-2.amazonaws.com/prod"
sesion = requests.post(f"{url}/auth/login", json={"email": "tu-email@ejemplo.com", "password": "tu-contraseña"}).json()
cred = requests.post(f"{url}/auth/session/s3", headers={"Authorization": f"Bearer {sesion['id_token']}"}).json()
key, secret, token = cred["access_key_id"], cred["secret_access_key"], cred["session_token"]

s3 = fs.S3FileSystem(access_key=key, secret_key=secret, session_token=token, region="us-west-2")

mediciones = ds.dataset("do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1", filesystem=s3, format="parquet",
                        ignore_prefixes=["dataset", "manifest"])   # lazy: solo descubre archivos; omite dataset.json y manifest.json
print(mediciones.count_rows(filter=ds.field("year") >= 2020))
