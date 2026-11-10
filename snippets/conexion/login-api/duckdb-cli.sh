#!/usr/bin/env bash
# Requiere el CLI de DuckDB, curl y jq

URL="https://ee98cnfz7e.execute-api.us-west-2.amazonaws.com/prod"
TOKEN=$(curl -s -X POST "$URL/auth/login" -H "Content-Type: application/json" \
  -d '{"email": "tu-email@ejemplo.com", "password": "tu-contraseña"}' | jq -r .id_token)
CRED=$(curl -s -X POST "$URL/auth/session/s3" -H "Authorization: Bearer $TOKEN")
KEY_ID=$(jq -r .access_key_id <<<"$CRED") SECRET=$(jq -r .secret_access_key <<<"$CRED") SESSION_TOKEN=$(jq -r .session_token <<<"$CRED")

duckdb -c "
CREATE SECRET (TYPE S3, KEY_ID '$KEY_ID', SECRET '$SECRET', SESSION_TOKEN '$SESSION_TOKEN', REGION 'us-west-2');
SELECT count(*) AS mediciones FROM 's3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet' WHERE year >= 2020;"
