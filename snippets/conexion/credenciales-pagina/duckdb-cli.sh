#!/usr/bin/env bash
# Requiere el CLI de DuckDB

KEY_ID="ASIA..." SECRET="..." SESSION_TOKEN="..."   # pegar desde la página (duran 1 h)

duckdb -c "
CREATE SECRET (TYPE S3, KEY_ID '$KEY_ID', SECRET '$SECRET', SESSION_TOKEN '$SESSION_TOKEN', REGION 'us-west-2');
SELECT count(*) AS mediciones FROM 's3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet' WHERE year >= 2020;"
