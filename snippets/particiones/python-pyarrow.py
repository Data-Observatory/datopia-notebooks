# pip install pyarrow

import pyarrow as pa
import pyarrow.dataset as ds
from pyarrow import fs

key, secret, token = "ASIA...", "...", "..."   # pegar desde la página (duran 1 h)

s3 = fs.S3FileSystem(access_key=key, secret_key=secret, session_token=token, region="us-west-2")

# `year` debe declararse int64 (como en los archivos); con partitioning="hive" falla: "incompatible types"
rem = ds.dataset("do-datopia/categoria=salud/pais=cl/fuente=deis/tipo=resumen-estadistico-mensual/version=v1", filesystem=s3, format="parquet", ignore_prefixes=["dataset", "manifest"],
                 partitioning=ds.partitioning(pa.schema([("year", pa.int64())]), flavor="hive"))
print(rem.count_rows(filter=ds.field("year") == 2024))   # solo lee la carpeta year=2024/
