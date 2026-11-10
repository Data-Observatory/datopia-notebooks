# install.packages(c("duckdb", "DBI", "dplyr", "dbplyr"))

library(DBI)
library(dplyr)
library(httr2)

url <- "https://ee98cnfz7e.execute-api.us-west-2.amazonaws.com/prod"
sesion <- request(paste0(url, "/auth/login")) |>
  req_body_json(list(email = "tu-email@ejemplo.com", password = "tu-contraseña")) |>
  req_perform() |> resp_body_json()
cred <- request(paste0(url, "/auth/session/s3")) |> req_auth_bearer_token(sesion$id_token) |>
  req_method("POST") |> req_perform() |> resp_body_json()
key <- cred$access_key_id; secret <- cred$secret_access_key; token <- cred$session_token

con <- dbConnect(duckdb::duckdb())
dbExecute(con, sprintf("CREATE SECRET (TYPE S3, KEY_ID '%s', SECRET '%s', SESSION_TOKEN '%s', REGION 'us-west-2')", key, secret, token))

mediciones <- tbl(con, sql("SELECT * FROM 's3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet'"))   # lazy: se traduce a SQL
mediciones |> filter(year >= 2020) |> count() |> collect()
