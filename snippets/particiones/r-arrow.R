# install.packages(c("arrow", "dplyr"))

library(arrow)
library(dplyr)

key <- "ASIA..."; secret <- "..."; token <- "..."   # pegar desde la página (duran 1 h)

s3 <- S3FileSystem$create(access_key = key, secret_key = secret, session_token = token, region = "us-west-2")

# `year` debe declararse int64 (como en los archivos) o Arrow falla al unir los tipos
rem <- open_dataset(s3$path("do-datopia/categoria=salud/pais=cl/fuente=deis/tipo=resumen-estadistico-mensual/version=v1"), partitioning = hive_partition(year = int64()),
  factory_options = list(selector_ignore_prefixes = c("dataset", "manifest")))   # omite dataset.json y manifest.json
rem |> filter(year == 2024) |> count() |> collect()   # solo lee la carpeta year=2024/
