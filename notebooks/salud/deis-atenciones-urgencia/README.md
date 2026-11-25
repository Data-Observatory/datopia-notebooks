# DEIS — Atenciones de Urgencia

Atenciones de urgencia **diarias** de la red pública de salud de Chile, informadas por cada
establecimiento al **DEIS** (Departamento de Estadísticas e Información de Salud, Ministerio de
Salud), por causa y grupo de edad. Cobertura 2008 → hoy, más de 400 millones de filas; la fuente se
revisa cada semana.

## Notas sobre los datos

**Ruta S3:**
```
s3://do-datopia/categoria=salud/pais=cl/fuente=deis/
├── tipo=atenciones-urgencia/version=v1/
│   ├── part00000.parquet                ← tabla de hechos: todos los años en un archivo, ordenado por fecha
│   ├── dataset.json                     ← metadatos y esquema
│   └── manifest.json                    ← filas, bytes, primera y última fecha
├── tipo=causas-atencion-urgencia/version=v1/part-00000.parquet   ← diccionario de causas (35 filas)
└── tipo=establecimientos-salud/version=v1/                       ← establecimientos de salud (compartido con el REM)
```

**Sin particiones.** Todos los años van juntos en archivos `partNNNNN.parquet` de hasta 300 MB (hoy
uno solo, ~110 MB), ordenados por `fecha`, `id_establecimiento`, `id_causa` y `rango_etario`. Leer con
el glob `part*.parquet` (o los nombres de `manifest.json`). Como el orden es por `fecha`, filtrar por
un rango de fechas hace que DuckDB lea solo los bloques de ese rango.

**Formato largo.** Una fila por (`fecha`, `id_establecimiento`, `id_causa`, `rango_etario`) con sus
`atenciones`; además `year` (año calendario de `fecha`), `semana` (semana epidemiológica de la fuente),
`tipo_campana` y `flags_procesamiento`. `rango_etario` tiene cinco valores fijos (`menores 1`,
`de 1 a 4`, `de 5 a 14`, `de 15 a 64`, `de 65 y mas`).

**Los hechos solo traen códigos.** `causas-atencion-urgencia` traduce `id_causa` a `nombre_causa`,
`grupo_diagnostico`, `tipo_prestacion` (consulta, hospitalización, cirugía) y `codigo_cie10`;
`establecimientos-salud` da nombre, tipo, comuna (`cut_com`, `nom_com`) y región (`nom_reg`; los dos
primeros dígitos de `cut_com` son el código de región) por `id_establecimiento`.

**No sumar todas las causas.** La causa `34` (*total demanda*) es el total de las consultas; las de
nombre *total* (`07`, `22`, `23`) son totales de hospitalización por grupo; `28` es parte de `27`.
Sumar causas de un mismo tipo de prestación y sin mezclar un total con sus partes.

**Causas que aparecen con los años.** `34`, COVID-19 (`30` a `33`), salud mental (`37` a `42`) y
lesiones autoinfligidas (`35`) existen desde 2020; quemaduras (`43`) desde 2025. Antes de 2020 no hay
un total de consultas: una serie larga tiene que sumar causas que existan en todo el período.

**Semanas.** `semana` va de domingo a sábado; los últimos días de diciembre pueden ser la semana 1 del
año siguiente mientras `year` sigue siendo el año calendario. Para series semanales usar el año
epidemiológico (el del miércoles de la semana); `demo.ipynb` lo calcula como `anio_epi`.

**`flags_procesamiento`.** `1` es el valor normal; `33` (bit 5, valor 32) marca una clave que venía
repetida en la fuente, donde se dejó la última línea del archivo (unas 80 mil filas de 2009-2024).

**Rendimiento.** Un año de una causa toma unos segundos; 9 años, del orden de un minuto. Recorrer la
tabla completa funciona, pero es bastante más lento: filtrar siempre por `fecha`.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `demo.ipynb` | Autenticación, metadatos y cobertura (filas por año desde el pie del Parquet), el diccionario de causas, búsqueda paso a paso (`buscar_causas`, `atenciones`), y dos casos: el peak invernal de las consultas respiratorias por semana epidemiológica (2017-2025, y por causa en 2024-2025) y las consultas de urgencia por región y grupo de edad en 2025 (con los establecimientos de más consultas) |
