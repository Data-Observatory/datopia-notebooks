# install.packages(c("arrow", "dplyr"))

library(arrow)
library(dplyr)
library(httr2)

url <- "https://ee98cnfz7e.execute-api.us-west-2.amazonaws.com/prod"
sesion <- request(paste0(url, "/auth/login")) |>
  req_body_json(list(email = "tu-email@ejemplo.com", password = "tu-contraseña")) |>
  req_perform() |> resp_body_json()
cred <- request(paste0(url, "/auth/session/s3")) |> req_auth_bearer_token(sesion$id_token) |>
  req_method("POST") |> req_perform() |> resp_body_json()
key <- cred$access_key_id; secret <- cred$secret_access_key; token <- cred$session_token

s3 <- S3FileSystem$create(access_key = key, secret_key = secret, session_token = token, region = "us-west-2")

mediciones <- open_dataset(s3$path("do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1"),   # lazy: solo descubre archivos
  factory_options = list(selector_ignore_prefixes = c("dataset", "manifest")))   # omite dataset.json y manifest.json
mediciones |> filter(year >= 2020) |> count() |> collect()
