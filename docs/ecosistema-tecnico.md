# Ecosistema DO: Guía técnica

Data Observatory opera tres servicios complementarios de datos. Este documento describe qué hace cada uno, cómo se accede y cuándo usar cuál.

---

## Portal institucional

**[www.dataobservatory.net](https://www.dataobservatory.net)**

Punto de entrada. Orienta hacia el servicio correcto según la necesidad.

---

## Catálogo DO

**[catalogo.dataobservatory.net](https://catalogo.dataobservatory.net)**

Meta-buscador de datasets con metadata enriquecida. El objetivo es construir un directorio comprehensivo de datos relevantes para Chile y Latinoamérica.

- **Los datos viven en su fuente original**, en sus formatos originales — DO no los hostea ni interfiere con la cadena de custodia. Excepción: datasets del Repositorio DO (ver más abajo) también aparecen en el Catálogo; el usuario no lo distingue necesariamente.
- La metadata se enriquece mediante un proceso semi-automático asistido por LLMs — no solo describe "qué hay" sino "para qué sirve, qué contiene, con qué se puede combinar". Los registros enriquecidos estarán pronto diferenciados con marcadores.
- Interfaz: web hoy; API programática en desarrollo.
- En mejora continua: motor de búsqueda, cobertura de datasets, funcionalidades y formas de visualizar y acceder a la información.

---

## Repositorio DO

Mismo modelo conceptual que el Catálogo — los datasets aparecen en el Catálogo con la misma visibilidad — pero **DO sí hostea los datos**.

- Casos de uso: generación de DOI, datasets sin infraestructura propia.
- Depuración disponible bajo demanda, no sistemática.
- Estado: pequeño; crece según demanda.

---

## Datopia (Lakehouse)

Datos seleccionados y procesados por DO para facilitar el acceso directo. El catálogo es curado, no exhaustivo.

**Arquitectura:**

```
Cliente (DuckDB / Athena)
    └── API Gateway  →  Lambda auth
            └── S3: do-datopia (us-west-2)
```

**Autenticación:**

```python
# 1. Login → id_token
token = requests.post(f"{API_URL}/auth/login",
    json={"email": EMAIL, "password": PASSWORD}).json()["id_token"]

# 2. Credenciales STS temporales (1 h)
creds = requests.post(f"{API_URL}/auth/session/s3",
    headers={"Authorization": f"Bearer {token}"}).json()
```

**Acceso con DuckDB** (recomendado para todos los datasets):

```python
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

> **Athena:** posible para Parquet estándar. Datasets con geometría (GeoParquet/WKB) requieren DuckDB para predicados espaciales.

**Características:**

- El usuario consulta SQL directamente sobre S3 — no es necesario descargar el dataset completo.
- Cada dataset tendrá DOI asignado (en proceso).
- **Interoperabilidad:** donde es posible, columnas estandarizadas (nombres de comunas, unidades, códigos) permiten JOINs entre datasets de distintas fuentes. No todos los datasets comparten dimensiones conectables.

**Etapas de acceso:**

| Etapa | Estado | Descripción |
|---|---|---|
| 1. API + notebooks | ✅ Disponible | Credenciales STS + DuckDB/Python. Ver notebooks de ejemplo en este repo. |
| 2. Autogestión de usuarios | 🔄 En desarrollo | Registro con correo válido sin coordinación con DO. |
| 3. Interfaz web de exploración | 🔬 En exploración | Selección y filtrado visual de datos; diseño pendiente — debe ser lo suficientemente flexible para funcionar con cualquier dataset. |
| 4. Consultas en lenguaje natural | 🔭 Visión | Portal que permita consultar datos en español sin escribir código. |

---

## ¿Cuándo usar cuál?

```
¿Buscas datos que ya existen en otro lugar?    → Catálogo DO
¿Tienes datos pero no tienes dónde alojarlos?  → Repositorio DO
¿Quieres consultar datos ya procesados?        → Datopia
```

---

## Colaboración

- **Sugerir datasets** para el Catálogo o Repositorio: abre un issue en este repositorio o contáctanos.
- **Contribuir pipelines** de procesamiento que queden corriendo (como el de transporte).
- **Compartir scripts de depuración** ya hechos — el próximo equipo no repite el mismo trabajo.
