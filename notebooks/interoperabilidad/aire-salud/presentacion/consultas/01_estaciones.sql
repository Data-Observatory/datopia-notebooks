CREATE TEMP TABLE estaciones AS
SELECT e.estacion_id, e.estacion_fk, e.nombre,
       c.cut_com, c.nom_com, c.cut_reg, e.lon, e.lat
FROM sinca_estaciones e
JOIN subdere_comunas c
  ON e.lon BETWEEN c.bbox_xmin AND c.bbox_xmax      -- filtro barato primero
 AND e.lat BETWEEN c.bbox_ymin AND c.bbox_ymax
 AND ST_Contains(c.geometry, ST_Point(e.lon, e.lat))  -- punto en polígono
WHERE e.fecha_fin IS NULL                            -- estaciones activas
  AND e.estacion_id IN (SELECT estacion_id
                        FROM sinca_estaciones_variables
                        WHERE variable_code = 'PM25');
