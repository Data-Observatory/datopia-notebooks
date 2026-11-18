SELECT e.estacion_id, e.nom_com, e.lon, e.lat,
       AVG(a.valor) AS mp25_invierno_2024
FROM aire_diario a
JOIN estaciones e USING (estacion_fk)
WHERE e.cut_reg = '13'                                -- Región Metropolitana
  AND year(a.fecha) = 2024
  AND month(a.fecha) BETWEEN 5 AND 8                  -- mayo a agosto
GROUP BY ALL;
