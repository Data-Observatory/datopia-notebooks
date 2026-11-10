#!/usr/bin/env python3
"""Genera `snippets.json` (todos los idiomas en un solo archivo) a partir de la carpeta `snippets/`.

Uso:
    python scripts/build_snippets.py           # escribe snippets.json
    python scripts/build_snippets.py --check   # falla si no está al día (para CI)

Fuentes:
    snippets/meta.json                 lenguajes de programación, librerías y escenarios (textos por idioma)
    snippets/<escenario>/<archivo>     el código, escrito en español (idioma base)
    snippets/traducciones-<idioma>.json  sustituciones para generar el código en cada otro idioma

Idiomas de la interfaz ("locales"): `es` (base) más uno por cada `traducciones-<idioma>.json`.
Para agregar un idioma: crear ese archivo y agregar el idioma a cada texto de `meta.json`.

Estructura de salida:
    locales[], default_locale
    scenarios[]                      {id, title{<idioma>}, description{<idioma>}}
    languages[].libraries[]          {id, name, lazy, lazy_note{<idioma>},
                                      snippets{<escenario>: {filename, code{<idioma>}}}}

Solo usa la biblioteca estándar y no accede a la red.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNIPPETS_DIR = ROOT / "snippets"
OUTPUT = ROOT / "snippets.json"
BASE_LOCALE = "es"
CODE_SUFFIXES = {".py", ".R", ".jl", ".mjs", ".sh"}
FORMAT_VERSION = 2

# Credenciales reales que nunca deben llegar a un snippet.
SECRET_PATTERNS = [re.compile(r"ASIA[A-Z0-9]{16}"), re.compile(r"eyJ[A-Za-z0-9_-]{20,}")]
# Restos de español que delatan una traducción incompleta (se omite con "omitir_chequeo_restos": true,
# necesario en idiomas que comparten palabras con el español, como el portugués).
SPANISH_LEFTOVERS = re.compile(
    r"[áéíóúñ¿¡]|\b(solo|carpeta|carpetas|pegar|desde|omite|archivos|datos|caja|una|tu|mediciones|sesion|"
    r"resultado|opciones|filas)\b",
    re.IGNORECASE,
)


def load_json(path, errors):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: no se pudo leer ({exc})")
        return None


def translate(code, translations, used):
    """Español → otro idioma: frases exactas (largas primero) y luego identificadores."""
    for spanish, other in sorted(translations["frases"], key=lambda pair: -len(pair[0])):
        if spanish in code:
            used.add(spanish)
            code = code.replace(spanish, other)
    for spanish, other in translations["palabras"].items():
        if re.search(rf"\b{re.escape(spanish)}\b", code):
            used.add(spanish)
            code = re.sub(rf"\b{re.escape(spanish)}\b", other, code)
    return code


def localized(block, locales, where, errors):
    """Un texto por idioma: {"es": ..., "en": ...}; falla si falta alguno."""
    missing = [loc for loc in locales if not isinstance(block.get(loc), str) or not block[loc].strip()]
    if missing:
        errors.append(f"{where}: falta el texto en {missing}")
    return {loc: block.get(loc) for loc in locales}


def build():
    errors = []
    meta = load_json(SNIPPETS_DIR / "meta.json", errors)
    if errors:
        return None, errors

    # Traducciones disponibles: snippets/traducciones-<idioma>.json
    translations, locales = {}, [BASE_LOCALE]
    for path in sorted(SNIPPETS_DIR.glob("traducciones-*.json")):
        locale = path.stem.split("-", 1)[1]
        loaded = load_json(path, errors)
        if loaded is not None:
            translations[locale] = loaded
            locales.append(locale)
    if errors:
        return None, errors
    used = {loc: set() for loc in translations}

    output = {"version": FORMAT_VERSION, "default_locale": BASE_LOCALE, "locales": locales,
              "scenarios": [], "languages": []}

    scenarios = meta["scenarios"]
    for scenario in scenarios:
        where = f"snippets/meta.json [escenario {scenario['id']}]"
        output["scenarios"].append({
            "id": scenario["id"],
            "title": localized({loc: scenario.get(loc, {}).get("title") for loc in locales}, locales,
                               f"{where} title", errors),
            "description": localized({loc: scenario.get(loc, {}).get("description") for loc in locales}, locales,
                                     f"{where} description", errors),
        })

    registered = set()
    for language in meta["languages"]:
        block = {"id": language["id"], "name": language["name"], "highlight": language["highlight"],
                 "libraries": []}
        for library in language["libraries"]:
            entries = {}
            for scenario in scenarios:
                path = SNIPPETS_DIR / scenario["dir"] / library["file"]
                if not path.exists():
                    continue
                registered.add(path.relative_to(SNIPPETS_DIR).as_posix())
                where = path.relative_to(ROOT).as_posix()
                code_base = path.read_text(encoding="utf-8").rstrip("\n")
                for pattern in SECRET_PATTERNS:
                    if pattern.search(code_base):
                        errors.append(f"{where}: parece contener una credencial real")
                code = {BASE_LOCALE: code_base}
                for locale, table in translations.items():
                    code[locale] = translate(code_base, table, used[locale])
                    leftover = SPANISH_LEFTOVERS.search(code[locale])
                    if leftover and not table.get("omitir_chequeo_restos"):
                        errors.append(f"{where}: la versión '{locale}' conserva español ('{leftover.group(0)}'); "
                                      f"agrega la frase a snippets/traducciones-{locale}.json")
                entries[scenario["id"]] = {"filename": library["file"], "code": code}
            if not entries:
                errors.append(f"snippets/meta.json: '{library['file']}' no existe en ningún escenario")
                continue
            block["libraries"].append({
                "id": library["id"],
                "name": library["name"],
                "lazy": library["lazy"],
                "lazy_note": localized(library["lazy_note"], locales,
                                       f"snippets/meta.json [{library['file']}] lazy_note", errors),
                "snippets": entries,
            })
        output["languages"].append(block)

    # Archivos de código en snippets/ que meta.json no conoce.
    for path in sorted(SNIPPETS_DIR.rglob("*")):
        if path.is_file() and path.suffix in CODE_SUFFIXES:
            if path.relative_to(SNIPPETS_DIR).as_posix() not in registered:
                errors.append(f"{path.relative_to(ROOT).as_posix()}: no está registrado en snippets/meta.json")

    # Traducciones que ya no se usan (señal de que el snippet cambió).
    for locale, table in translations.items():
        known = {pair[0] for pair in table["frases"]} | set(table["palabras"])
        for stale in sorted(known - used[locale]):
            errors.append(f"snippets/traducciones-{locale}.json: '{stale}' ya no aparece en ningún snippet")

    return output, errors


def main():
    parser = argparse.ArgumentParser(description="Genera o verifica snippets.json")
    parser.add_argument("--check", action="store_true", help="falla si snippets.json no está al día")
    args = parser.parse_args()

    output, errors = build()
    if errors:
        print("Errores al construir los snippets:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    content = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
        if current != content:
            print("snippets.json no está al día. Ejecuta `python scripts/build_snippets.py` y commitea.",
                  file=sys.stderr)
            return 1
        print(f"snippets.json al día ({', '.join(output['locales'])}).")
        return 0

    OUTPUT.write_text(content, encoding="utf-8")
    print(f"snippets.json escrito ({', '.join(output['locales'])}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
