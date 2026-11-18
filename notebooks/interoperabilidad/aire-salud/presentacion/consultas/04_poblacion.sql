CREATE TEMP TABLE poblacion AS
SELECT SUM(total_personas) AS habitantes
FROM ine_viviendas
WHERE cod_comuna = '13110';
