# DEIS — Resumen Estadístico Mensual (REM)

Actividad mensual de la red pública de salud de Chile, reportada por cada establecimiento al
**DEIS** (Departamento de Estadísticas e Información de Salud, Ministerio de Salud): consultas,
controles, procedimientos, programas (salud mental, PNAC, cardiovascular, etc.). Cobertura 2009 →
hoy, ~1.900 millones de filas.

## Notas sobre los datos

**Ruta S3:**
```
s3://do-datopia/categoria=salud/pais=cl/fuente=deis/tipo=resumen-estadistico-mensual/version=v1/
├── anio=YYYY/part-00000.parquet     ← tabla de hechos, una partición por año (2009-2026)
├── codigos-rem/part-*.parquet       ← diccionario de códigos (pocos MB)
├── codigos-rem-prestaciones/        ← jerarquía de etiquetas de prestaciones (clave/valor/nivel)
├── codigos-rem-col-numericas/       ← jerarquía de etiquetas de columnas (clave/valor/nivel)
├── dataset.json                     ← metadatos y esquema
└── manifest.json                    ← filas y bytes por partición
```

**Formato largo.** Una fila por (`anio`, `mes`, `id_establecimiento`, `cod_prestacion`,
`cod_col_numerica`) con su `cantidad`. Unifica las 5 series de origen (`tipo_serie`: `a`, `bs`,
`bm`, `d`, `p`), que DEIS publica como CSV anchos (una columna `ColNN` por corte).

**Los hechos solo traen códigos; `codigos-rem` los traduce, por año**, con la jerarquía del
formulario REM: `cod_hoja`/`nombre_hoja` (el formulario) → `nombre_seccion` → `cod_prestacion`/
`nombre_prestacion` (la fila) → `cod_col_numerica`/`nombre_col_numerica` (la columna: total, sexo,
edad...). Las etiquetas usan el formato `dimensión| valor`, con varias dimensiones separadas por
`;` (p. ej. `tipo de conteo| total; sexo| ambos sexos`). Unir por
(`anio`, `cod_prestacion`, `cod_col_numerica`).

**Flujo recomendado: buscar por texto, no por código.** `nombre_prestacion ILIKE '%...%'` en
`codigos-rem` → elegir hoja y sección → listar columnas → revisar años disponibles → recién ahí leer
los hechos filtrando por `anio` y `cod_prestacion`. `demo.ipynb` trae funciones para cada paso
(`buscar`, `prestaciones`, `columnas_de`, `anios_disponibles`, `serie`).

**Qué cuenta `cantidad`.** Depende de la prestación: consultas, kilos, personas... Las columnas que
cuentan **personas en un mes** (p. ej. personas que retiran leche del PNAC) no se pueden sumar a lo
largo de los meses sin contar a la misma persona varias veces; usar promedios o meses puntuales.
La serie P (población en control) se reporta solo en junio y diciembre.

**Rendimiento.** Cada partición anual pesa 55-240 MB. Leer una prestación en un año toma menos de un
minuto; 9 años, 1-2 minutos. Filtrar siempre por `anio` y `cod_prestacion`; subir `threads` en
DuckDB (`SET threads=128`) acelera mucho la lectura remota.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `demo.ipynb` | Autenticación, metadatos y cobertura, búsqueda paso a paso en `codigos-rem`, y dos casos: consultas médicas de salud mental (serie mensual por sexo y por edad) y personas que retiran leche del PNAC (serie mensual y por grupo) |
