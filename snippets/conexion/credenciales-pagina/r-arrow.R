# install.packages(c("arrow", "dplyr"))

library(arrow)
library(dplyr)

key <- "ASIA..."; secret <- "..."; token <- "..."   # pegar desde la página (duran 1 h)

s3 <- S3FileSystem$create(access_key = key, secret_key = secret, session_token = token, region = "us-west-2")

mediciones <- open_dataset(s3$path("do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1"),   # lazy: solo descubre archivos
  factory_options = list(selector_ignore_prefixes = c("dataset", "manifest")))   # omite dataset.json y manifest.json
mediciones |> filter(year >= 2020) |> count() |> collect()
