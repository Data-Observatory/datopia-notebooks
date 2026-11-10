// npm install @duckdb/node-api   (Node.js 18+)

import { DuckDBInstance } from "@duckdb/node-api";

const url = "https://ee98cnfz7e.execute-api.us-west-2.amazonaws.com/prod";
const sesion = await (await fetch(`${url}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "tu-email@ejemplo.com", password: "tu-contraseña" }) })).json();
const cred = await (await fetch(`${url}/auth/session/s3`, { method: "POST",
  headers: { Authorization: `Bearer ${sesion.id_token}` } })).json();
const [key, secret, token] = [cred.access_key_id, cred.secret_access_key, cred.session_token];

const con = await (await DuckDBInstance.create()).connect();
await con.run(`CREATE SECRET (TYPE S3, KEY_ID '${key}', SECRET '${secret}', SESSION_TOKEN '${token}', REGION 'us-west-2')`);

const resultado = await con.runAndReadAll(`SELECT count(*) AS mediciones FROM 's3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet' WHERE year >= 2020`);
console.table(resultado.getRowObjectsJson());
