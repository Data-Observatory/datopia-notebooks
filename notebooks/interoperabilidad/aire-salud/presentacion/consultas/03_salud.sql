CREATE TEMP TABLE salud_bruto AS
SELECT year AS anio, mes, cod_prestacion, SUM(cantidad) AS cantidad
FROM deis_hechos
WHERE cod_prestacion IN ('03020201', '03020301', '03020401', '03020402')
  AND cod_col_numerica = 'col01'                    -- total, ambos sexos
  AND id_establecimiento IN (SELECT id_establecimiento
                             FROM deis_establecimientos
                             WHERE cod_comuna = '13110')   -- La Florida
GROUP BY ALL;

CREATE TEMP TABLE diccionario AS
WITH nombres AS (
    SELECT year AS anio, cod_prestacion,
           MIN(REPLACE(nombre_prestacion, 'tipo de atención| ', '')) AS nombre
    FROM deis_codigos
    WHERE year BETWEEN 2023 AND 2024
      AND cod_prestacion IN ('03020201', '03020301', '03020401', '03020402')
      AND cod_col_numerica = 'col01'
    GROUP BY year, cod_prestacion)
SELECT anio, cod_prestacion,
       arg_max(nombre, anio) OVER (PARTITION BY cod_prestacion) AS causa  -- nombre más reciente
FROM nombres;
