// npm install @duckdb/node-api   (Node.js 18+)

import { DuckDBInstance } from "@duckdb/node-api";

const key = "ASIA...", secret = "...", token = "...";   // pegar desde la página (duran 1 h)

const con = await (await DuckDBInstance.create()).connect();
await con.run(`CREATE SECRET (TYPE S3, KEY_ID '${key}', SECRET '${secret}', SESSION_TOKEN '${token}', REGION 'us-west-2')`);

const resultado = await con.runAndReadAll(`SELECT count(*) AS mediciones FROM 's3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet' WHERE year >= 2020`);
console.table(resultado.getRowObjectsJson());
