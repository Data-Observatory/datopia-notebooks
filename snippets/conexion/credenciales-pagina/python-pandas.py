# pip install pandas pyarrow s3fs

import pandas as pd

key, secret, token = "ASIA...", "...", "..."   # pegar desde la página (duran 1 h)

# pandas NO es lazy: carga lo que pides. `columns` y `filters` acotan la descarga.
mediciones = pd.read_parquet("s3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1", columns=["year"], filters=[("year", ">=", 2024)],
                             ignore_prefixes=["dataset", "manifest"],   # omite dataset.json y manifest.json
                             storage_options={"key": key, "secret": secret, "token": token,
                                              "client_kwargs": {"region_name": "us-west-2"}})
print(len(mediciones))
