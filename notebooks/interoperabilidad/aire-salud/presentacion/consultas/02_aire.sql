CREATE TEMP TABLE aire_diario AS
SELECT estacion_fk, fecha::DATE AS fecha, valor
FROM sinca_mediciones
WHERE fecha >= DATE '2023-01-01' AND fecha < DATE '2025-01-01'
  AND variable_fk = 13        -- MP2,5
  AND periodicidad_fk = 1;    -- promedio diario
