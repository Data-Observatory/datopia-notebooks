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

La infraestructura vive en un repo privado separado: `do-aws_cdk_apps` (`apps/lakehouse/`).
Si al probar un notebook aparece un bug o limitación en la API, documentarlo en la sección
**Issues encontrados** al final de este archivo y proponer el fix en términos del handler Lambda
o recurso CDK correspondiente.

---

## Estructura del repositorio

```
do-datopia-notebooks/
├── CLAUDE.md
├── README.md
├── config.example.json
├── .gitignore
├── transporte/
│   └── red-movilidad/
│       └── demo.ipynb          ← dataset activo
└── <categoria>/                ← nuevas categorías se agregan aquí
    └── <fuente>/
        └── demo.ipynb
```

Cada dataset vive en `<categoria>/<fuente>/`. Al agregar un nuevo dataset:
1. Crear la carpeta `<categoria>/<fuente>/`.
2. Copiar la estructura de `transporte/red-movilidad/demo.ipynb` como plantilla.
3. Actualizar `README.md` raíz con el nuevo badge "Open in Colab".
4. Registrar el dataset en la sección **Datasets disponibles** de este archivo.

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
| `bus_route_console` | string | Ruta por consola del bus, ej. `T201 00I`. |
| `bus_route_assigned` | string | Ruta en Sinoptic (autoritativa), ej. `T201 03I`. |
| `service_name` | string | Código de servicio Sinoptic, ej. `T515`. |
| `speed` | float | Velocidad instantánea (km/h). |
| `direction` | int | Dirección cardinal 0–7: 0=N 1=NE 2=E 3=SE 4=S 5=SW 6=W 7=NW. |
| `operator_number` | int | ID empresa operadora (1–15 zonas RED). |
| `hour` | int | **Ausente en datos actuales.** Usar `EXTRACT(HOUR FROM timestamp_gps_utc)`. |
| `geometry` | binary | WKB Point EPSG:4326. Predicados espaciales solo vía DuckDB. |

---

## Convenciones de notebooks

- **Idioma:** español en todo el texto visible al usuario.
- **Celdas de setup:** usar `# @title Título descriptivo` — Colab las colapsa; localmente es solo un comentario.
- **Detección de entorno:**
  ```python
  IN_COLAB = "google.colab" in sys.modules or os.path.exists("/content")
  ```
- **Config local:** leer `../../config.json` (copiado de `config.example.json`).
- **Config Colab:** `input()` para URL y email, `getpass.getpass()` para contraseña.
- **Nunca** comitear URLs reales, passwords ni tokens.
- **Estilo profesional:** badges en la primera celda markdown (ver abajo).
- **Glob completo** (`**/*.parquet`) solo en análisis de cobertura total — advertir que es lento.

### Badges estándar para cada notebook

Primera celda markdown del notebook:

```markdown
[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Data-Observatory/datopia-notebooks/blob/main/<categoria>/<fuente>/demo.ipynb)
[![Licencia](https://img.shields.io/badge/licencia-MIT-blue.svg)](../../LICENSE)
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

---

## Issues encontrados en testing

Registrar aquí bugs o limitaciones descubiertas al ejecutar notebooks. Indicar el fix sugerido
en el repo de infraestructura (`do-aws_cdk_apps/apps/lakehouse/`).

- [x] **`/auth/session/s3` requiere `id_token`, no `access_token`.**
      La documentación decía usar `access_token`, pero el endpoint Lambda valida el `id_token` de Cognito.
      Fix aplicado en notebooks y en este archivo. No requiere cambio en infraestructura.

- [ ] **Columna `hour` ausente en los archivos Parquet.**
      Documentada como columna desnormalizada pero no existe en los datos (verificado con `DESCRIBE` en DuckDB 1.5.3).
      Fix en notebooks: usar `EXTRACT(HOUR FROM timestamp_gps_utc)::INTEGER`.
      Fix sugerido en infraestructura: agregar `hour` al pipeline de ingesta en `do-aws_cdk_apps/apps/lakehouse/`.

- [x] **`dataset.json` (catálogo) desincronizado con el esquema real de los Parquet — `service_name` no existe.**
      `dataset.json` declara `service_name`, pero no existe en los Parquet reales (reemplazado por
      `operator_name`, semánticamente distinto — nombre de la concesionaria, no código de servicio).
      Ya corregido en notebook (`transporte/red-movilidad/demo.ipynb`, commit `b8c28c5`, usa
      `operator_name`). Sigue pendiente en infraestructura: decidir si `service_name` se reincorpora
      al pipeline o se retira formalmente del catálogo, y regenerar `dataset.json` para reflejar el
      esquema físico real.

- [ ] **Columna `bus_route_console` está mal escrita como `bus_route_consle` en los Parquet reales.**
      Verificado con `DESCRIBE` en DuckDB 1.5.3 sobre datos de `year=2026/month=05` (2026-08-27):
      el catálogo (`dataset.json`) declara `bus_route_console`, pero la columna física se llama
      `bus_route_consle` (falta la "o"). También aparecen `lon`/`lat` en los Parquet sin documentar
      en el catálogo. Rompe cualquier query que use el nombre correcto `bus_route_console` con
      `BinderException`.
      Confirmado el typo en TODO el histórico publicado (2025-09-09 → 2026-07-01, checkpoints en
      sep/dic/ene/mar/may/jul) — no es una regresión reciente, viene del handler de ingesta desde
      el día 1. Dado que ya hay ~275 días de Parquet publicados con el nombre `bus_route_consle`,
      reescribir todo el histórico es caro; más barato corregir el catálogo para que declare
      `bus_route_consle` (el nombre real) en vez de renombrar la columna en los archivos.
      Fix sugerido en infraestructura (`do-aws_cdk_apps/apps/lakehouse/`): opción A (recomendada,
      barata) — actualizar `dataset.json` para declarar `bus_route_consle` y documentar el typo
      histórico; opción B (cara) — corregir el handler de ingesta a partir de ahora y aceptar que
      el nombre de columna difiere entre Parquet viejos y nuevos, o reescribir el histórico. Incluir
      `lon`/`lat` en el catálogo si se mantienen.

- [x] **Clave de particiones en `dataset.json` inestable — cambió de `partition_keys` a `partitioned_by` y volvió a `partition_keys`.**
      El commit `b8c28c5` (2026-07-10) actualizó el notebook a `partitioned_by` porque el catálogo
      había sido renombrado. Verificado en vivo el 2026-08-27: el catálogo volvió a usar
      `partition_keys`. La clave del catálogo está flapping entre despliegues sin versionado.
      Fix aplicado en notebook: `meta.get("partitioned_by") or meta.get("partition_keys")` para
      tolerar ambas.
      Fix sugerido en infraestructura: fijar un nombre único y estable para esta clave en el
      generador de `dataset.json`, y versionar el esquema del catálogo para que cambios como este
      sean detectables antes de llegar a producción.

- [x] **Sección "Buses por día de semana" del notebook podía superar el timeout de celda (600 s).**
      La celda original hacía 4 queries DuckDB separadas (una por mes, 7 días cada una), cada una
      tomando ~65-70 s más overhead de replanificación — total >280 s, y en ejecuciones no
      interactivas (nbconvert/CI) esto se acerca o supera timeouts típicos de 300-600 s.
      Verificado con timing directo: una sola query combinada sobre los 28 días (`GROUP BY year,
      month, day` en vez de un loop de 4 llamadas a `con.execute`) hace el mismo escaneo en ~194-224 s
      — evita la replanificación repetida y aprovecha mejor los 16 threads de DuckDB.
      Fix aplicado en notebook: consolidada la celda de la sección 5 en una sola query.
      No requiere cambio en infraestructura — es un patrón de consulta del notebook, no del pipeline.
