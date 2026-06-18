# Datopia Notebooks

[![Licencia](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
[![Datasets](https://img.shields.io/badge/datasets-1-green.svg)]()
[![Actualización](https://img.shields.io/badge/actualización-diaria-brightgreen.svg)]()
[![Región](https://img.shields.io/badge/AWS-us--west--2-orange.svg)]()

Notebooks públicos de acceso y análisis de datos del **Datopia Lakehouse**, operado por
[Data Observatory](https://dataobservatory.net).

Los datos se consumen directamente desde S3 con credenciales temporales, sin descarga de archivos,
sin infraestructura propia. Compatible con Google Colab y entornos locales.

---

## Datasets disponibles

| Categoría | Fuente | Cobertura | Notebook |
|---|---|---|---|
| Transporte | RED Movilidad (RM) | Sep 2025 → hoy (diario) | [![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Data-Observatory/datopia-notebooks/blob/main/transporte/red-movilidad/demo.ipynb) |

---

## Cómo usar

### Google Colab

Haz clic en el badge **Abrir en Colab** de la tabla anterior. Solo necesitas tus credenciales de
acceso al Lakehouse. Las dependencias se instalan automáticamente.

### Local

```bash
git clone https://github.com/Data-Observatory/datopia-notebooks.git
cd datopia-notebooks
cp config.example.json config.json   # completar con tus credenciales
pip install duckdb requests pandas matplotlib
jupyter notebook
```

`config.json` nunca se commitea (está en `.gitignore`).

---

## Requisitos

| Paquete | Versión mínima | Uso |
|---|---|---|
| `duckdb` | 0.10+ | Consultas SQL sobre Parquet en S3 |
| `requests` | 2.28+ | Autenticación contra la API |
| `pandas` | 1.5+ | Manipulación de resultados |
| `matplotlib` | 3.5+ | Visualizaciones |

---

## Arquitectura

```
Google Colab / Jupyter local
        │
        ▼
  API Gateway (HTTPS)
  ├── POST /auth/login          → JWT access token
  └── POST /auth/session/s3    → credenciales STS temporales (1 h)
        │
        ▼
  Amazon S3  (us-west-2)
  └── s3://do-datopia/
      └── categoria=transporte/pais=cl/fuente=red-movilidad/...
              └── year=YYYY/month=MM/day=DD/part-N.parquet
```

DuckDB lee los archivos Parquet directamente desde S3 usando las credenciales STS.
No se descarga ningún archivo localmente.

---

## Acceso

Los notebooks requieren una cuenta en el Datopia Lakehouse.
Para solicitar acceso, contacta a [Data Observatory](https://dataobservatory.net).

---

## Licencia

[MIT](LICENSE) · Datos servidos por Data Observatory
