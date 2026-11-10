# install.packages(c("duckdb", "DBI", "dplyr", "dbplyr"))

library(DBI)
library(dplyr)

key <- "ASIA..."; secret <- "..."; token <- "..."   # pegar desde la página (duran 1 h)

con <- dbConnect(duckdb::duckdb())
dbExecute(con, sprintf("CREATE SECRET (TYPE S3, KEY_ID '%s', SECRET '%s', SESSION_TOKEN '%s', REGION 'us-west-2')", key, secret, token))

mediciones <- tbl(con, sql("SELECT * FROM 's3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet'"))   # lazy: se traduce a SQL
mediciones |> filter(year >= 2020) |> count() |> collect()
