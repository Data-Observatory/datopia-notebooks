#!/usr/bin/env python3
"""Calcula cifras agregadas de cada dataset y las guarda en `notebooks/<categoria>/<fuente>/stats.json`.

Uso:
    python scripts/compute_stats.py                  # todos los datasets
    python scripts/compute_stats.py sinca deis-rem   # solo algunos (por nombre de carpeta)

Después, `python scripts/build_index.py` usa esas cifras para rellenar `coverage` en `index.json`.

Credenciales (en este orden):
    1. Variables de entorno DATOPIA_EMAIL y DATOPIA_PASSWORD (y opcionalmente DATOPIA_API_URL).
    2. `config.json` en la raíz del repo (sección `test_user`, igual que los notebooks).

Costo: solo listados de S3 y footers de Parquet (más una tabla chica de estaciones). No se leen
tablas de hechos.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb
import requests

ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://ee98cnfz7e.execute-api.us-west-2.amazonaws.com/prod"

# Cuántos períodos sin datos se listan explícitamente en el texto antes de resumirlos
MAX_LISTED_GAPS = 3


def read_credentials():
    email = os.environ.get("DATOPIA_EMAIL")
    password = os.environ.get("DATOPIA_PASSWORD")
    if email and password:
        return email, password

    config_path = ROOT / "config.json"
    if not config_path.exists():
        sys.exit(
            "Faltan credenciales: define DATOPIA_EMAIL y DATOPIA_PASSWORD, "
            "o copia config.example.json → config.json."
        )
    user = json.loads(config_path.read_text(encoding="utf-8")).get("test_user", {})
    if not user.get("email") or not user.get("password"):
        sys.exit("config.json no tiene test_user.email y test_user.password.")
    return user["email"], user["password"]


def connect():
    """Autentica contra la API y devuelve (conexión DuckDB, bucket)."""
    api_url = os.environ.get("DATOPIA_API_URL", API_URL)
    email, password = read_credentials()

    login = requests.post(
        f"{api_url}/auth/login", json={"email": email, "password": password}, timeout=30
    )
    login.raise_for_status()
    token = login.json()["id_token"]

    session = requests.post(
        f"{api_url}/auth/session/s3", headers={"Authorization": f"Bearer {token}"}, timeout=30
    )
    session.raise_for_status()
    creds = session.json()

    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs")
    con.execute(f"""
        CREATE OR REPLACE SECRET s3 (
            TYPE          S3,
            KEY_ID        '{creds["access_key_id"]}',
            SECRET        '{creds["secret_access_key"]}',
            SESSION_TOKEN '{creds["session_token"]}',
            REGION        '{creds["region"]}'
        )
    """)
    return con, creds["bucket"]


def stats_sinca(con, bucket):
    base = f"s3://{bucket}/categoria=medio-fisico/pais=cl/fuente=sinca"

    # Estaciones activas (SCD-2: fecha_fin IS NULL) desde la tabla chica de estaciones
    (active_stations,) = con.execute(f"""
        SELECT count(*)
        FROM read_parquet('{base}/tipo=estaciones/version=v1/part-00000.parquet')
        WHERE fecha_fin IS NULL
    """).fetchone()

    # Rango de fechas desde los footers de medicion-diaria (no lee filas)
    first_date, last_date = con.execute(f"""
        SELECT min(stats_min), max(stats_max)
        FROM parquet_metadata('{base}/tipo=medicion-diaria/version=v1/part-*.parquet')
        WHERE path_in_schema = 'fecha'
    """).fetchone()

    return {
        "estaciones_activas": active_stations,
        "anio_inicio": int(first_date[:4]),
        "fecha_inicio": first_date[:10],
        "fecha_fin": last_date[:10],
    }


def stats_deis_rem(con, bucket):
    base = (
        f"s3://{bucket}/categoria=salud/pais=cl/fuente=deis"
        "/tipo=resumen-estadistico-mensual/version=v1"
    )

    # Años disponibles: se leen del nombre de las particiones year=YYYY (solo listado S3)
    first_year, last_year, n_years = con.execute(f"""
        SELECT min(year), max(year), count(*)
        FROM (
            SELECT regexp_extract(file, 'year=(\\d+)', 1)::INTEGER AS year
            FROM glob('{base}/year=*/part-*.parquet')
        )
    """).fetchone()

    return {"anio_inicio": first_year, "anio_fin": last_year, "anios_con_datos": n_years}


def stats_ine(con, bucket):
    base = (
        f"s3://{bucket}/categoria=sociologia/pais=cl/fuente=ine"
        "/tipo=censos-poblacionales/version=v1w"
    )

    # Años censales: se leen del nombre de las particiones year=YYYY (solo listado S3)
    years = [
        row[0]
        for row in con.execute(f"""
            SELECT DISTINCT regexp_extract(file, 'year=(\\d+)', 1)::INTEGER AS year
            FROM glob('{base}/year=*/tipo_registro=*/part-*.parquet')
            ORDER BY year
        """).fetchall()
    ]

    return {
        "anio_inicio": years[0],
        "anio_fin": years[-1],
        "censos": len(years),
        "anios_es": " y ".join([", ".join(map(str, years[:-1])), str(years[-1])]) if len(years) > 1 else str(years[0]),
        "anios_en": " and ".join([", ".join(map(str, years[:-1])), str(years[-1])]) if len(years) > 1 else str(years[0]),
    }


def format_gaps(ranges, template_one_day, template_range, template_many):
    """Texto corto de períodos sin datos; vacío si no hay."""
    if not ranges:
        return ""
    if len(ranges) > MAX_LISTED_GAPS:
        return template_many.format(n=len(ranges))
    parts = [
        template_one_day.format(desde=start) if start == end else template_range.format(desde=start, hasta=end)
        for start, end in ranges
    ]
    return "; ".join(parts)


def stats_dtpm_posiciones(con, bucket):
    base = (
        f"s3://{bucket}/categoria=transporte/pais=cl/fuente=red-movilidad"
        "/tipo=posicion-diaria/version=v1"
    )

    # Días con partición (solo listado S3); los huecos son días sin ninguna partición
    days_rows = con.execute(f"""
        SELECT DISTINCT make_date(
            regexp_extract(file, 'year=(\\d+)', 1)::INTEGER,
            regexp_extract(file, 'month=(\\d+)', 1)::INTEGER,
            regexp_extract(file, 'day=(\\d+)', 1)::INTEGER
        ) AS dia
        FROM glob('{base}/year=*/month=*/day=*/*.parquet')
        ORDER BY dia
    """).fetchall()
    days = [row[0] for row in days_rows]

    gap_rows = [
        ((before + timedelta(days=1)).isoformat(), (after - timedelta(days=1)).isoformat())
        for before, after in zip(days, days[1:])
        if (after - before).days > 1
    ]

    return {
        "fecha_inicio": days[0].isoformat(),
        "fecha_fin": days[-1].isoformat(),
        "dias_con_datos": len(days),
        "huecos_es": (
            "; " + format_gaps(gap_rows, "sin datos {desde}", "sin datos {desde} a {hasta}", "{n} períodos sin datos")
            if gap_rows
            else ""
        ),
        "huecos_en": (
            "; " + format_gaps(gap_rows, "no data {desde}", "no data {desde} to {hasta}", "{n} periods with no data")
            if gap_rows
            else ""
        ),
    }


# Carpeta del dataset (<categoria>/<fuente>) → función que calcula sus cifras
DATASETS = {
    "sinca": ("notebooks/medio-fisico/sinca", stats_sinca),
    "deis-rem": ("notebooks/salud/deis-rem", stats_deis_rem),
    "dtpm": ("notebooks/transporte/dtpm", stats_dtpm_posiciones),
    "ine": ("notebooks/sociologia/ine", stats_ine),
}


def write_stats(folder, new_stats):
    """Escribe stats.json; si nada cambió salvo `calculado`, deja el archivo intacto."""
    path = ROOT / folder / "stats.json"
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if {k: v for k, v in previous.items() if k != "calculado"} == new_stats:
            return False
    stats = {**new_stats, "calculado": datetime.now(timezone.utc).date().isoformat()}
    path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="Calcula stats.json de cada dataset")
    parser.add_argument("datasets", nargs="*", help=f"subconjunto de {sorted(DATASETS)}")
    args = parser.parse_args()

    selected = args.datasets or sorted(DATASETS)
    unknown = [name for name in selected if name not in DATASETS]
    if unknown:
        sys.exit(f"Datasets desconocidos: {unknown}. Disponibles: {sorted(DATASETS)}")

    con, bucket = connect()
    failures = 0
    for name in selected:
        folder, compute = DATASETS[name]
        try:
            stats = compute(con, bucket)
        except Exception as exc:  # un dataset que falla no debe impedir actualizar los demás
            failures += 1
            print(f"[{name}] ERROR: {exc}", file=sys.stderr)
            continue
        changed = write_stats(folder, stats)
        print(f"[{name}] {'actualizado' if changed else 'sin cambios'}: {stats}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
