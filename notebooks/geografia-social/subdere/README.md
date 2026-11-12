# SUBDERE — División Político Administrativa (límites comunales)

Polígonos de las **comunas de Chile** con sus códigos CUT y los nombres oficiales de región,
provincia y comuna, en GeoParquet, más la tabla de cambios de la DPA desde 1992. El notebook
`demo.ipynb` compara la foto de **2000-05-08** (13 regiones) con la base **2018-09-06**
(16 regiones) y explica cada diferencia con la ley que la produjo.

## Notas sobre los datos

**Ruta S3:**
```
s3://do-datopia/categoria=geografia-social/pais=cl/fuente=subdere/
├── tipo=division-territorial/version=v2/
│   ├── snapshot_date=YYYY-MM-DD/part-<run_id>-00000.parquet   ← una foto por fecha (342–346 comunas)
│   └── manifest.json                                         ← partes vigentes, filas y bytes por foto
└── tipo=division-territorial-cambios/version=v1/
    ├── part-<run_id>-00000.parquet                           ← tabla de cambios (plana)
    └── manifest.json
```

**Fotos.** La base es `snapshot_date=2018-09-06` (edición DPA 2023 de geoportal.cl; su último
cambio es la creación de Ñuble). Las fotos `2000-05-08`, `2001-05-26`, `2004-03-13`, `2004-04-22`,
`2004-07-21`, `2007-10-02`, `2007-10-08` y `2010-03-11` se reconstruyen desde la base revirtiendo los
cambios de la tabla `division-territorial-cambios`. La foto de una fecha ya incluye los cambios
vigentes ese día.

**Leer desde el manifiesto.** El nombre de cada parte lleva el id de la ejecución que la escribió.
Para leer siempre la publicación vigente, tomar las rutas de `manifest.json` (campo `parts[].file`);
con un glob, usar `snapshot_date=*/part-*.parquet` y no el prefijo completo (ahí también está
`manifest.json`).

**GeoParquet 2.0.** La geometría usa el tipo `GEOMETRY` nativo de Parquet. La leen DuckDB ≥1.4
(con `spatial`), GeoPandas ≥1.1, pyarrow ≥20 y GDAL ≥3.11. **Polars todavía no** (falla al abrir el
archivo aunque no se pida la geometría), y DuckDB <1.4 con `spatial` cargado da error.

**Peso.** Cada foto pesa ~90 MB, casi todo en `geometry` (polígonos de alta resolución). Las
consultas sobre atributos (`cut_*`, `nom_*`, `superficie`, `bbox_*`) no leen la geometría. Para
mapas nacionales conviene simplificar en DuckDB (`ST_Simplify(geometry, 0.003)`) antes de pasar a
GeoPandas.

**Códigos y nombres.** `cut_reg` (2 dígitos), `cut_prov` (3) y `cut_com` (5) son texto con ceros a
la izquierda. Los nombres son los oficiales del Decreto 1.115 de 2018, con tildes, iguales en todas
las fotos. La tabla de cambios, en cambio, escribe los nombres tal como la ley (con erratas, p. ej.
`Hulapén`): para mostrar nombres, unir por código con una foto.

**Cambios de código.** Al crear una región, sus comunas cambian de código (Valdivia `10501` →
`14101`). Comparar fotos por `cut_com` sin la tabla de cambios confunde estos traslados con comunas
nuevas; el notebook arma el puente de códigos 2000 → 2018 con los `traslado` de la tabla.

**Superficie.** `superficie` (km²) es la cifra oficial de la fuente; `area_m2` se calcula sobre la
geometría publicada y no coincide exactamente. En DuckDB, para reproyectar:
`ST_Transform(geometry, 'EPSG:4326', 'EPSG:32719', always_xy := true)` (sin `always_xy` los ejes
quedan invertidos).

**Antártica Chilena** (`12202`) está en todas las fotos sin geometría ni superficie.

**Relación con otras tablas.** `cod_comuna` del censo (INE) apunta a la versión `v1` de
`division-territorial` (columnas `cod_*`/`nombre_*`); `v2` usa `cut_*`/`nom_*`. Ambas versiones
conviven mientras los consumidores migran.

Licencia de los datos: CC BY-NC-SA 4.0.
