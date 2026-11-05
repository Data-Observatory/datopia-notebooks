# INE — Censos de Población y Vivienda 2017 y 2024

Microdatos de los **Censos de Población y Vivienda** del INE (Instituto Nacional de Estadísticas de
Chile): una fila por vivienda, hogar o persona censada, para los censos 2017 y 2024. El notebook
`demo.ipynb` muestra cómo explorarlos y trae cuatro casos (población por región, pirámide de
población, tipo de vivienda e internet en el hogar).

## Notas sobre los datos

**Ruta S3:**
```
s3://do-datopia/categoria=sociologia/pais=cl/fuente=ine/
├── tipo=censos-poblacionales/
│   ├── version=v1w/                                   ← formato ANCHO (~62 M de filas)
│   │   ├── year=YYYY/tipo_registro=<viviendas|hogares|personas>/part-NNNNN.parquet
│   │   ├── dataset.json                               ← metadatos y descripción de cada columna
│   │   └── manifest.json                              ← filas y bytes por partición
│   └── version=v1l/                                   ← formato LARGO (~1.600 M de filas), mismas particiones
├── tipo=division-territorial-censal/version=v1/part-00000.parquet   ← geografía censal (~16 mil filas)
└── tipo=preguntas-respuestas-censo/version=v1/part-00000.parquet    ← diccionario (~1.200 filas)
```

Son **cuatro tablas**, dos de ellas los mismos datos en distinta forma: `censos-poblacionales` en
versión `v1w` (ancho) y `v1l` (largo). Las otras dos no tienen particiones (tablas chicas y estáticas).

**Formato ancho (`v1w`).** Una fila por vivienda, hogar o persona y una columna por variable
(`sexo`, `edad`, `tipo_vivienda`...), con las respuestas como etiqueta del diccionario del INE. Es el
formato para analizar. Cada año y cada `tipo_registro` guarda **solo sus propias columnas**: leer con
`union_by_name=true` y `hive_partitioning=true`; lo que no existe en una partición se lee nulo.

**Formato largo (`v1l`).** Una fila por registro y pregunta (`pregunta`, `respuesta`). Sirve para
consultar una pregunta por su texto sin saber cómo se llama su columna. `dataset.json` dice que no
publica respuestas vacías, pero **el largo de 2017 sí trae filas con `respuesta` nula** (~5 millones en
viviendas; el de 2024 no): filtrar `respuesta IS NOT NULL` antes de comparar años. `personas` pesa más
de 1.300 millones de filas: filtrar siempre por `year` y `tipo_registro`, y no recorrerlo completo.
Para analizar (cruces, números) conviene el ancho; el largo, para repetir una misma consulta sobre
preguntas que se llaman igual en ambos censos (el diccionario lista cuáles son).

**Diccionario (`preguntas-respuestas-censo`).** Una fila por año, tipo de registro, pregunta y código
de respuesta. Su `descripcion_pregunta` es el valor de `pregunta` del formato largo. Ojo: aquí
`tipo_registro` va en singular (`vivienda`, `hogar`, `persona`); en los microdatos va en plural.

**Cómo se conectan las unidades.**
- **Solo `viviendas` trae `cod_comuna`** (en ambos censos). Hogares y personas llegan a la comuna por
  su vivienda.
- **En 2017 los ids son relativos a la zona censal**: `id_vivienda` se repite entre zonas, por lo que
  la vivienda se identifica con (`id_zona_censal_local`, `id_vivienda`). En 2024 `id_vivienda` es
  global. Un `JOIN ... ON a.id_zona_censal_local IS NOT DISTINCT FROM b.id_zona_censal_local` resuelve
  ambos años con la misma consulta.
- Hogar = `id_vivienda` + `id_hogar`; persona = hogar + `id_persona`.
- `id_zona_censal_local` (2017) es clave foránea hacia `division-territorial-censal`. `cod_comuna` lo
  es hacia `division-territorial` de SUBDERE (`categoria=geografia-social`).

**Geografía (`division-territorial-censal`).** En 2017 una fila por zona censal (urbana) o localidad
(rural); en 2024, una por comuna, con `comuna_bajo_umbral_habitantes` (menos de 6.000 personas
censadas). Para comuna → provincia → región, quedarse con las comunas únicas.

**Dos censos, dos cuestionarios.** Muchas variables existen en un solo año y algunas cambian de
etiqueta (p. ej. `departamento en edificio` en 2017 es `departamento` en 2024). Los nombres de
región y comuna vienen en minúsculas y sin tildes. `flags_procesamiento` es una columna técnica del
ETL.

**Rendimiento.** Una agregación sobre una tabla ancha de un año toma segundos; cruzar personas con
viviendas en los dos censos, alrededor de un minuto. Subir `threads` en DuckDB (`SET threads=128`)
acelera la lectura remota.
