# pip install pyarrow

import pyarrow.dataset as ds
from pyarrow import fs

key, secret, token = "ASIA...", "...", "..."   # pegar desde la página (duran 1 h)

s3 = fs.S3FileSystem(access_key=key, secret_key=secret, session_token=token, region="us-west-2")

mediciones = ds.dataset("do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1", filesystem=s3, format="parquet",
                        ignore_prefixes=["dataset", "manifest"])   # lazy: solo descubre archivos; omite dataset.json y manifest.json
print(mediciones.count_rows(filter=ds.field("year") >= 2020))
