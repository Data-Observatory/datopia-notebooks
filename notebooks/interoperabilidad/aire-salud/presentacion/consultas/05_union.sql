WITH aire AS (          -- MMA: MP2,5 mensual de la estación ubicada dentro de La Florida
    SELECT DATE_TRUNC('month', fecha)::DATE AS mes, AVG(valor) AS mp25
    FROM aire_diario
    WHERE estacion_fk = (SELECT estacion_fk FROM estaciones WHERE cut_com = '13110')
    GROUP BY 1),
salud AS (              -- MINSAL: consultas del mes, con el nombre de cada enfermedad
    SELECT make_date(s.anio, s.mes, 1) AS mes, d.causa, SUM(s.cantidad) AS consultas
    FROM salud_bruto s
    JOIN diccionario d USING (anio, cod_prestacion)
    GROUP BY 1, 2)
SELECT a.mes, a.mp25, s.causa, s.consultas,
       s.consultas / p.habitantes * 1000 AS consultas_por_mil   -- INE: por cada mil habitantes
FROM aire a
JOIN salud s ON s.mes = a.mes                                    -- mes a mes
CROSS JOIN poblacion p
ORDER BY 1, 3;
