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
- **Consultas multi-período:** combinar varios meses/días en una sola query (`GROUP BY` sobre una
  lista de rutas) en vez de un loop de `con.execute()` por período — reduce el tiempo total
  notablemente y evita superar timeouts de ejecución no interactiva (nbconvert/CI).

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
