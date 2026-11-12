# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

## Qué es este repositorio

Notebooks públicos de acceso a datos del **DO Datopia Lakehouse** — lakehouse de producción en AWS
operado por Data Observatory (Chile). Dirigido a analistas de datos, no a ingenieros de
infraestructura.

**Idioma obligatorio: español** — toda documentación, comentarios de código, mensajes al usuario,
texto en celdas markdown y nombres de variables descriptivas deben estar en español. Sin excepciones.
El código técnico (nombres de funciones de librerías, parámetros de API, SQL, etc.) permanece en
inglés porque es la convención de cada herramienta.

---

## Estructura del repositorio

```
do-datopia-notebooks/
├── CLAUDE.md
├── README.md
├── config.example.json
├── index.json                  ← catálogo para el sitio (generado)
├── snippets.json               ← snippets para el sitio, todos los idiomas (generado)
├── notebooks/
│   ├── transporte/
│   │   └── red-movilidad/
│   │       └── demo.ipynb      ← dataset activo
│   ├── medio-fisico/
│   │   └── sinca/
│   ├── salud/
│   │   └── deis-rem/
│   ├── sociologia/
│   │   └── ine/
│   ├── geografia-social/
│   │   └── subdere/
│   └── <categoria>/            ← nuevas categorías se agregan aquí
│       └── <fuente>/
│           └── demo.ipynb
├── snippets/                   ← fuente de los snippets (un archivo por herramienta)
├── scripts/
└── docs/
```

Cada dataset vive en `notebooks/<categoria>/<fuente>/`. Al agregar un nuevo dataset:
1. Crear la carpeta `notebooks/<categoria>/<fuente>/`.
2. Copiar la estructura de `notebooks/transporte/red-movilidad/demo.ipynb` como plantilla.
3. Actualizar `README.md` raíz con el nuevo badge "Open in Colab".
4. Registrar el dataset en la sección **Datasets disponibles** de este archivo.
5. Crear `meta.json` junto al notebook (copiar uno existente) y correr
   `python scripts/build_index.py`; commitear `index.json` junto con el resto.
6. Opcional, si el texto de `coverage` usa cifras reales: agregar una función en
   `scripts/compute_stats.py` y correr `python scripts/compute_stats.py <fuente>`.

### Enlaces antiguos (notebooks que se movieron)

GitHub no redirige archivos movidos. Los notebooks vivían en `<categoria>/<fuente>/` y ahora están en
`notebooks/<categoria>/<fuente>/` (la categoría no cambia: carpeta, S3 y OCDE usan el mismo nombre).
En las rutas antiguas queda un `demo.ipynb` mínimo que dice dónde está el nuevo y trae
su badge de Colab. `scripts/check_moved.py` (CI) verifica que cada uno apunte a un notebook que existe.
Esos stubs son temporales: eliminarlos cuando ya no se usen los enlaces antiguos (a lo menos 6 meses).
**No** crear carpetas nuevas fuera de `notebooks/`, y **no** mover un notebook sin dejar su stub.

### Snippets de conexión

`snippets/` tiene el código (un archivo por herramienta y escenario). `snippets.json` (todos los
idiomas en un solo archivo) lo consume el sitio y sale de `python scripts/build_snippets.py` (CI corre
`--check`). Nunca editarlo a mano; ver `snippets/README.md`.

### Índice y cifras generadas

- `index.json` (raíz) lo lee el sitio web. **Nunca editarlo a mano**: sale de `meta.json` +
  `stats.json` vía `scripts/build_index.py` (solo biblioteca estándar, sin red). CI corre
  `--check` en cada PR y push a `main`.
- `meta.json` (`format`, `es`, `en`) es la fuente de los textos. `id` y `path` los deriva el script
  del nombre de carpeta.
- Cifras que cambian (estaciones, años, fechas) **no se escriben a mano**: `coverage` puede llevar
  campos `{entre_llaves}` que se rellenan desde `stats.json`, y `coverage_fallback` (obligatorio si
  hay campos) con texto aproximado ("+200 estaciones") que se usa si falta el `stats.json`.
- `stats.json` lo genera `scripts/compute_stats.py` con consultas baratas (listados S3, footers de
  Parquet, tablas chicas; **nunca** tablas de hechos). Credenciales: `config.json` o
  `DATOPIA_EMAIL`/`DATOPIA_PASSWORD`. Correrlo a mano cuando se quiera refrescar y commitear
  `stats.json` + `index.json`.
- En notebooks y READMEs, evitar cifras exactas que envejecen ("212 estaciones"): usar redondeos
  estables ("más de 200") o cifras con fecha.

---

## Autenticación (igual para todos los datasets)

```
POST /auth/login          → { access_token, id_token, refresh_token }
POST /auth/session/s3     → { access_key_id, secret_access_key, session_token,
                               bucket, region, expires_at, hints }
```

Credenciales STS temporales (1 h por defecto). Renovar 5 min antes de expirar
(`hints.refresh_before_seconds = 300`).

API Gateway URL: `https://ee98cnfz7e.execute-api.us-west-2.amazonaws.com/prod`
Región AWS: `us-west-2`
Bucket S3: `do-datopia`

---

## Patrón DuckDB estándar

```python
import duckdb, requests

token = requests.post(f"{API_URL}/auth/login",
    json={"email": EMAIL, "password": PASSWORD}).json()["id_token"]

creds = requests.post(f"{API_URL}/auth/session/s3",
    headers={"Authorization": f"Bearer {token}"}).json()

con = duckdb.connect()
con.execute(f"""
    CREATE OR REPLACE SECRET s3 (
        TYPE S3,
        KEY_ID        '{creds["access_key_id"]}',
        SECRET        '{creds["secret_access_key"]}',
        SESSION_TOKEN '{creds["session_token"]}',
        REGION        '{creds["region"]}'
    )
""")
```

---

## Datasets disponibles

### transporte / red-movilidad

**Ruta S3:**
```
s3://do-datopia/categoria=transporte/pais=cl/fuente=red-movilidad/tipo=posicion-diaria/version=v1/
```

**Particiones:** `year=YYYY/month=MM/day=DD/part-N.parquet`
**Cobertura:** 2025-09-09 → ayer (~275 días, actualización diaria ~02:30 UTC)
**Formato:** GeoParquet 1.0 — geometría WKB, requiere DuckDB (no Athena)
**Escala:** ~7–13 M filas/día · ~7 000–7 500 vehículos/día · ~140–260 MB/día

**Columnas:**

| Columna | Tipo | Descripción |
|---|---|---|
| `timestamp_gps_utc` | timestamp | Tiempo GPS (UTC). Sort key primario. |
| `timestamp_insertion_utc` | timestamp | Inserción en base DTP (UTC). |
| `plate` | string | Patente del bus, ej. `BJFP-93`. Sort key secundario. |
| `way` | string | Sentido: `I`=Ida, `R`=Retorno, vacío=sin sentido. |
| `bus_route_consle` | string | Ruta por consola del bus, ej. `T201 00I`. |
| `bus_route_assigned` | string | Ruta en Sinoptic (autoritativa), ej. `T201 03I`. |
| `operator_name` | string | Nombre de la concesionaria (empresa operadora), hermana de `operator_number`. |
| `speed` | float | Velocidad instantánea (km/h). |
| `direction` | int | Dirección cardinal 0–7: 0=N 1=NE 2=E 3=SE 4=S 5=SW 6=W 7=NW. |
| `operator_number` | int | ID empresa operadora (1–15 zonas RED). |
| `geometry` | binary | WKB Point EPSG:4326. Predicados espaciales solo vía DuckDB. |

No existe columna `hour` — usar `EXTRACT(HOUR FROM timestamp_gps_utc)::INTEGER`.
No hay columna con el código de servicio Sinoptic (ej. `T515`); solo `bus_route_consle`/`bus_route_assigned`.
La clave de particiones en `dataset.json` puede aparecer como `partition_keys` o `partitioned_by` según
el despliegue — al leer el catálogo, aceptar ambas: `meta.get("partitioned_by") or meta.get("partition_keys")`.

### salud / deis-rem

**Ruta S3 (hechos):**
```
s3://do-datopia/categoria=salud/pais=cl/fuente=deis/tipo=resumen-estadistico-mensual/version=v1/
```

**Particiones:** `year=YYYY/part-00000.parquet` (una por año, 2009-2026).
**Diccionario:** dataset hermano `tipo=codigos-rem/version=v1/part-00000.parquet` (columna `year`), no
un subdirectorio de los hechos. Hermanos: `codigos-rem-prestaciones`, `codigos-rem-col-numericas`,
`establecimientos-salud`, `establecimientos-salud-historial` (todos `version=v1`).
**Cobertura:** 2009 → 2026 (mensual)
**Escala:** ~1 930 M filas en total · 55–240 MB por año

**Columnas (hechos):** `year`, `mes`, `tipo_serie` (`a`/`bs`/`bm`/`d`/`p`), `id_establecimiento`,
`cod_prestacion`, `cod_col_numerica`, `cantidad`, `flags_procesamiento`.

**`codigos-rem`** traduce los códigos por año: `cod_hoja`/`nombre_hoja` → `nombre_seccion` →
`cod_prestacion`/`nombre_prestacion` → `cod_col_numerica`/`nombre_col_numerica`. Etiquetas con
formato `dimensión| valor; dimensión| valor`. `cod_prestacion` va en minúscula en ambas tablas.
Unir por (`year`, `cod_prestacion`, `cod_col_numerica`).

- Buscar por texto en `codigos-rem` y bajar por la jerarquía hoja → sección → prestación → columna.
- Filtrar siempre por `year` y `cod_prestacion`; `SET threads=128` acelera la lectura remota.

### sociologia / ine

**Ruta S3 (base):** `s3://do-datopia/categoria=sociologia/pais=cl/fuente=ine/` — cuatro tablas:

| `tipo=` / `version=` | Contenido | Escala |
|---|---|---|
| `censos-poblacionales/version=v1w` | Microdatos Censos 2017 y 2024, formato **ancho** (una columna por variable) | ~62 M filas |
| `censos-poblacionales/version=v1l` | Los mismos registros, formato **largo** (`pregunta`, `respuesta`) | ~1 600 M filas |
| `division-territorial-censal/version=v1` | Geografía censal (2017: zona/localidad; 2024: comuna) | ~16 mil filas |
| `preguntas-respuestas-censo/version=v1` | Diccionario de preguntas y respuestas (`descripcion_pregunta` = `pregunta` del largo) | ~1 200 filas |

**Particiones (solo `censos-poblacionales`):** `year=YYYY/tipo_registro=<viviendas|hogares|personas>/part-NNNNN.parquet`.
Las otras dos tablas no tienen particiones (`part-00000.parquet`).
**Cobertura:** censos 2017 y 2024 (estático; sin actualización periódica).
**Cada año y cada `tipo_registro` guarda solo sus columnas**: leer con `hive_partitioning=true,
union_by_name=true` (lo ausente queda nulo). El `dataset.json` del ancho describe las ~100 columnas.

**Unir unidades (trampas):**
- Solo `viviendas` trae `cod_comuna`; hogares y personas llegan a la comuna por su vivienda.
- 2017: los ids son relativos a la zona → vivienda = (`id_zona_censal_local`, `id_vivienda`); `id_vivienda`
  solo no es único. 2024: `id_vivienda` es global. Unir con `IS NOT DISTINCT FROM` sobre
  `id_zona_censal_local` sirve para ambos años.
- Hogar = vivienda + `id_hogar`; persona = hogar + `id_persona`.
- `division-territorial-censal` en 2017 tiene una fila por zona: para comuna → región usar
  `SELECT DISTINCT cod_comuna, ..., cod_region, nombre_region` (346 comunas, 16 regiones).
- `tipo_registro` va en plural en los microdatos y en singular en el diccionario.

Otras notas: `grupo_etario` es texto (ordenar a mano: `'5-9'` queda tras `'45-49'`); nombres de región/comuna
vienen en minúscula y sin tildes; las etiquetas cambian entre censos (`departamento en edificio` 2017 →
`departamento` 2024); el largo de 2024 omite respuestas vacías pero el de 2017 trae filas con `respuesta` nula
(filtrar `respuesta IS NOT NULL` al comparar años); el diccionario da 10 preguntas de vivienda, 2 de hogar y 15 de persona con el mismo texto en ambos censos
(el largo de 2017 trae datos de 8 de las 10 de vivienda); misma pregunta ≠ mismas etiquetas de respuesta; **no recorrer `personas` largo completo** (>1 300 M filas).

### geografia-social / subdere

**Ruta S3 (base):** `s3://do-datopia/categoria=geografia-social/pais=cl/fuente=subdere/` — dos tablas:

| `tipo=` / `version=` | Contenido | Escala |
|---|---|---|
| `division-territorial/version=v2` | Comunas con polígono (GeoParquet **2.0**), códigos CUT y nombres oficiales | 342–346 filas por foto, ~90 MB por foto |
| `division-territorial-cambios/version=v1` | Un registro por unidad cambiada por cada ley/decreto, con `norma_url` | ~900 filas |

**Particiones (solo `division-territorial`):** `snapshot_date=YYYY-MM-DD/part-<run_id>-00000.parquet`. Base
`2018-09-06`; fotos reconstruidas `2000-05-08` … `2010-03-11`. Leer las rutas de `manifest.json` (`parts[].file`),
o glob `snapshot_date=*/part-*.parquet` (no el prefijo completo).
**Columnas:** `cut_reg`, `cut_prov`, `cut_com` (texto con ceros), `nom_reg`, `abr_reg`, `nom_prov`, `nom_com`,
`superficie` (km² oficial), `geometry`, `bbox_*`, `area_m2`, `perimeter_m`.
**Cobertura:** estático (sin actualización periódica).

Trampas:
- GeoParquet 2.0: requiere DuckDB ≥1.4 con `spatial` (con <1.4 falla); Polars no lo abre.
- La geometría es pesada: no traerla entera a pandas; `ST_Simplify(geometry, 0.003)` en DuckDB para mapas
  (`ST_SimplifyPreserveTopology` es ~30 veces más lento).
- Al crear una región sus comunas cambian de código: comparar fotos con el puente de `traslado` de la tabla de cambios.
- La tabla de cambios escribe los nombres como la ley (con erratas); los nombres oficiales salen de las fotos.
- Antártica Chilena (`12202`) sin geometría ni superficie.
- `ST_Transform(geometry, 'EPSG:4326', 'EPSG:32719', always_xy := true)` (sin `always_xy` los ejes se invierten).

---

## Convenciones de notebooks

- **Idioma:** español en todo el texto visible al usuario.
- **Celdas de setup:** usar `# @title Título descriptivo` — Colab las colapsa; localmente es solo un comentario.
- **Detección de entorno:**
  ```python
  IN_COLAB = "google.colab" in sys.modules or os.path.exists("/content")
  ```
- **Config local:** leer `../../../config.json` (copiado de `config.example.json`).
- **Config Colab:** `input()` para URL y email, `getpass.getpass()` para contraseña.
- **Nunca** comitear URLs reales, passwords ni tokens.
- **Estilo profesional:** badges en la primera celda markdown (ver abajo).
- **Glob completo** (`**/*.parquet`) solo en análisis de cobertura total — advertir que es lento.
- **Consultas multi-período:** combinar varios meses/días en una sola query (`GROUP BY` sobre una
  lista de rutas) en vez de un loop de `con.execute()` por período — reduce el tiempo total
  notablemente y evita superar timeouts de ejecución no interactiva (nbconvert/CI).

### Badges estándar para cada notebook

Primera celda markdown del notebook:

```markdown
[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Data-Observatory/datopia-notebooks/blob/main/notebooks/<categoria>/<fuente>/demo.ipynb)
[![Licencia](https://img.shields.io/badge/licencia-MIT-blue.svg)](../../../LICENSE)
[![Dataset](https://img.shields.io/badge/dataset-<fuente>-green.svg)]()
[![Actualización](https://img.shields.io/badge/actualización-diaria-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
```

---

## Usuarios de prueba (Cognito `us-west-2_8RadTvuRS`)

| Usuario | Email |
|---|---|
| usm | `usm@localhost` |
| test | `do-lakehouse-datopia@dataobservatory.net` |

Contraseñas en gestión interna — nunca en este repo.
