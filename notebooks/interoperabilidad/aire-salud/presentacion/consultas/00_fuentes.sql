CREATE VIEW sinca_estaciones AS SELECT * FROM read_parquet('s3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=estaciones/version=v1/part-*.parquet');
CREATE VIEW sinca_estaciones_variables AS SELECT * FROM read_parquet('s3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=estaciones-variables/version=v1/part-*.parquet');
CREATE VIEW sinca_mediciones AS SELECT * FROM read_parquet('s3://do-datopia/categoria=medio-fisico/pais=cl/fuente=sinca/tipo=medicion-diaria/version=v1/part-*.parquet');
CREATE VIEW deis_hechos AS SELECT * FROM read_parquet(['s3://do-datopia/categoria=salud/pais=cl/fuente=deis/tipo=resumen-estadistico-mensual/version=v1/year=2023/part-*.parquet', 's3://do-datopia/categoria=salud/pais=cl/fuente=deis/tipo=resumen-estadistico-mensual/version=v1/year=2024/part-*.parquet']);
CREATE VIEW deis_establecimientos AS SELECT * FROM read_parquet('s3://do-datopia/categoria=salud/pais=cl/fuente=deis/tipo=establecimientos-salud/version=v1/*.parquet');
CREATE VIEW deis_codigos AS SELECT * FROM read_parquet('s3://do-datopia/categoria=salud/pais=cl/fuente=deis/tipo=codigos-rem/version=v1/part-00000.parquet');
CREATE VIEW ine_viviendas AS SELECT * FROM read_parquet('s3://do-datopia/categoria=sociologia/pais=cl/fuente=ine/tipo=censos-poblacionales/version=v1w/year=2024/tipo_registro=viviendas/*.parquet');
CREATE VIEW subdere_comunas AS SELECT * FROM read_parquet('s3://do-datopia/categoria=geografia-social/pais=cl/fuente=subdere/tipo=division-territorial/version=v2/snapshot_date=2018-09-06/part-*.parquet');
