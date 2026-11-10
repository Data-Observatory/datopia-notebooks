# install.packages(c("duckdb", "DBI", "dplyr", "dbplyr"))

library(DBI)
library(dplyr)

key <- "ASIA..."; secret <- "..."; token <- "..."   # pegar desde la página (duran 1 h)

con <- dbConnect(duckdb::duckdb())
dbExecute(con, sprintf("CREATE SECRET (TYPE S3, KEY_ID '%s', SECRET '%s', SESSION_TOKEN '%s', REGION 'us-west-2')", key, secret, token))

# hive_partitioning expone `year` (carpetas year=YYYY/) y solo lee las carpetas que pasan el filtro
rem <- tbl(con, sql("SELECT * FROM read_parquet('s3://do-datopia/categoria=salud/pais=cl/fuente=deis/tipo=resumen-estadistico-mensual/version=v1/year=*/part-*.parquet', hive_partitioning = true)"))
rem |> filter(year == 2024) |> count() |> collect()   # solo lee la carpeta year=2024/
