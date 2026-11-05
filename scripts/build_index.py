#!/usr/bin/env python3
"""Genera `index.json` a partir de los `meta.json` y `stats.json` de cada notebook.

Uso:
    python scripts/build_index.py           # escribe index.json
    python scripts/build_index.py --check   # falla si index.json no está al día (para CI)

Solo usa la biblioteca estándar y no accede a la red: las cifras salen de los `stats.json`
generados antes con `scripts/compute_stats.py`.
"""

import argparse
import json
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "index.json"

TOP_LEVEL_KEYS = {"format", "es", "en"}
REQUIRED_TEXT_KEYS = ["name", "category", "source", "coverage", "description"]
OPTIONAL_TEXT_KEYS = ["coverage_fallback"]


def dataset_dirs():
    """Carpetas `<categoria>/<fuente>/` que tienen `meta.json` o `demo.ipynb`."""
    found = set()
    for pattern in ("*/*/meta.json", "*/*/demo.ipynb"):
        for path in ROOT.glob(pattern):
            relative = path.relative_to(ROOT)
            if any(part.startswith(".") for part in relative.parts):
                continue
            found.add(path.parent)
    return sorted(found)


def placeholders(text):
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def render_coverage(language_block, stats, where, errors):
    """Rellena los `{campos}` de `coverage` con `stats.json`; si faltan, usa `coverage_fallback`."""
    coverage = language_block["coverage"]
    fields = placeholders(coverage)
    if not fields:
        return coverage

    fallback = language_block.get("coverage_fallback")
    if not fallback:
        errors.append(f"{where}: 'coverage' usa campos {sorted(fields)}; falta 'coverage_fallback'")
        return coverage
    if placeholders(fallback):
        errors.append(f"{where}: 'coverage_fallback' no puede tener campos entre llaves")
        return coverage

    if fields <= stats.keys():
        return coverage.format_map({name: stats[name] for name in fields})
    return fallback


def validate_language_block(block, where, errors):
    if not isinstance(block, dict):
        errors.append(f"{where}: debe ser un objeto")
        return False

    ok = True
    for key in REQUIRED_TEXT_KEYS:
        value = block.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{where}: falta '{key}' o no es un texto no vacío")
            ok = False
    for key in OPTIONAL_TEXT_KEYS:
        if key in block and (not isinstance(block[key], str) or not block[key].strip()):
            errors.append(f"{where}: '{key}' debe ser un texto no vacío")
            ok = False
    unknown = set(block) - set(REQUIRED_TEXT_KEYS) - set(OPTIONAL_TEXT_KEYS)
    if unknown:
        errors.append(f"{where}: claves desconocidas {sorted(unknown)}")
        ok = False
    return ok


def load_json(path, errors):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: no se pudo leer ({exc})")
        return None


def build_entries():
    errors = []
    entries = []
    seen_ids = {}

    for folder in dataset_dirs():
        relative = folder.relative_to(ROOT)
        meta_path = folder / "meta.json"
        notebook_path = folder / "demo.ipynb"

        if not notebook_path.exists():
            errors.append(f"{relative}: existe meta.json pero falta demo.ipynb")
            continue
        if not meta_path.exists():
            errors.append(f"{relative}: existe demo.ipynb pero falta meta.json")
            continue

        meta = load_json(meta_path, errors)
        if meta is None:
            continue
        if not isinstance(meta, dict):
            errors.append(f"{relative}/meta.json: debe ser un objeto")
            continue

        missing = TOP_LEVEL_KEYS - set(meta)
        unknown = set(meta) - TOP_LEVEL_KEYS
        if missing:
            errors.append(f"{relative}/meta.json: faltan las claves {sorted(missing)}")
        if unknown:
            errors.append(f"{relative}/meta.json: claves desconocidas {sorted(unknown)}")
        if not isinstance(meta.get("format"), str) or not meta.get("format", "").strip():
            errors.append(f"{relative}/meta.json: 'format' debe ser un texto no vacío")

        blocks_ok = all(
            validate_language_block(meta.get(lang), f"{relative}/meta.json [{lang}]", errors)
            for lang in ("es", "en")
            if lang in meta
        )
        if missing or unknown or not blocks_ok or not isinstance(meta.get("format"), str):
            continue

        stats = {}
        stats_path = folder / "stats.json"
        if stats_path.exists():
            loaded = load_json(stats_path, errors)
            if isinstance(loaded, dict):
                stats = loaded
            elif loaded is not None:
                errors.append(f"{relative}/stats.json: debe ser un objeto")

        dataset_id = folder.name
        if dataset_id in seen_ids:
            errors.append(f"id duplicado '{dataset_id}': {seen_ids[dataset_id]} y {relative}")
            continue
        seen_ids[dataset_id] = relative

        entry = {"id": dataset_id, "path": f"{relative.as_posix()}/demo.ipynb", "format": meta["format"]}
        for lang in ("es", "en"):
            block = meta[lang]
            text = {key: block[key] for key in REQUIRED_TEXT_KEYS}
            text["coverage"] = render_coverage(block, stats, f"{relative}/meta.json [{lang}]", errors)
            entry[lang] = text
        entries.append(entry)

    entries.sort(key=lambda entry: entry["id"])
    return entries, errors


def main():
    parser = argparse.ArgumentParser(description="Genera o verifica index.json")
    parser.add_argument("--check", action="store_true", help="falla si index.json no está al día")
    args = parser.parse_args()

    entries, errors = build_entries()
    if errors:
        print("Errores al construir el índice:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    content = json.dumps(entries, ensure_ascii=False, indent=2) + "\n"

    if args.check:
        current = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else None
        if current != content:
            print(
                "index.json no coincide con meta.json/stats.json. "
                "Ejecuta `python scripts/build_index.py` y commitea el resultado.",
                file=sys.stderr,
            )
            return 1
        print(f"index.json al día ({len(entries)} entradas).")
        return 0

    INDEX_PATH.write_text(content, encoding="utf-8")
    print(f"index.json escrito ({len(entries)} entradas).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
