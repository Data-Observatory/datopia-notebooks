# using Pkg; Pkg.add(["DataFrames", "DBInterface", "HTTP", "JSON3"]); Pkg.add(name="DuckDB", version="1.4")  # DuckDB.jl 1.4: la versión de desarrollo no trae httpfs (s3://)

using DuckDB, DBInterface, DataFrames
using HTTP, JSON3

url = "https://ee98cnfz7e.execute-api.us-west-2.amazonaws.com/prod"
sesion = JSON3.read(HTTP.post("$url/auth/login", ["Content-Type" => "application/json"],
    JSON3.write(Dict("email" => "tu-email@ejemplo.com", "password" => "tu-contraseña"))).body)
cred = JSON3.read(HTTP.post("$url/auth/session/s3", ["Authorization" => "Bearer $(sesion.id_token)"]).body)
key, secret, token = cred.access_key_id, cred.secret_access_key, cred.session_token

con = DBInterface.connect(DuckDB.DB, ":memory:")
DBInterface.execute(con, "CREATE SECRET (TYPE S3, KEY_ID '$key', SECRET '$secret', SESSION_TOKEN '$token', REGION 'us-west-2')")

resultado = DataFrame(DBInterface.execute(con, """
    SELECT count(*) AS mediciones FROM 's3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet' WHERE year >= 2020"""))
println(resultado)
