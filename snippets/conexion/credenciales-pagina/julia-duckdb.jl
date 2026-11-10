# using Pkg; Pkg.add(["DataFrames", "DBInterface", "HTTP", "JSON3"]); Pkg.add(name="DuckDB", version="1.4")  # DuckDB.jl 1.4: la versión de desarrollo no trae httpfs (s3://)

using DuckDB, DBInterface, DataFrames

key, secret, token = "ASIA...", "...", "..."   # pegar desde la página (duran 1 h)

con = DBInterface.connect(DuckDB.DB, ":memory:")
DBInterface.execute(con, "CREATE SECRET (TYPE S3, KEY_ID '$key', SECRET '$secret', SESSION_TOKEN '$token', REGION 'us-west-2')")

resultado = DataFrame(DBInterface.execute(con, """
    SELECT count(*) AS mediciones FROM 's3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet' WHERE year >= 2020"""))
println(resultado)
