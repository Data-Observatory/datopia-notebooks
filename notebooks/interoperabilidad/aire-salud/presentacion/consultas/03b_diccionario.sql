SELECT s.cod_prestacion AS codigo_publicado,
       s.cantidad::INT  AS valor,
       d.causa          AS significado
FROM salud_bruto s
JOIN diccionario d USING (anio, cod_prestacion)
WHERE s.anio = 2024 AND s.mes = 7
ORDER BY 1;
