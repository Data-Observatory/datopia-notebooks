# pip install pandas pyarrow s3fs

import pandas as pd
import requests

url = "https://ee98cnfz7e.execute-api.us-west-2.amazonaws.com/prod"
sesion = requests.post(f"{url}/auth/login", json={"email": "tu-email@ejemplo.com", "password": "tu-contraseña"}).json()
cred = requests.post(f"{url}/auth/session/s3", headers={"Authorization": f"Bearer {sesion['id_token']}"}).json()
key, secret, token = cred["access_key_id"], cred["secret_access_key"], cred["session_token"]

# pandas NO es lazy: carga lo que pides. `columns` y `filters` acotan la descarga.
mediciones = pd.read_parquet("s3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1", columns=["year"], filters=[("year", ">=", 2024)],
                             ignore_prefixes=["dataset", "manifest"],   # omite dataset.json y manifest.json
                             storage_options={"key": key, "secret": secret, "token": token,
                                              "client_kwargs": {"region_name": "us-west-2"}})
print(len(mediciones))
