#!/usr/bin/env python3
"""Genera `snippets.es.json` y `snippets.en.json` a partir de la carpeta `snippets/`.

Uso:
    python scripts/build_snippets.py           # escribe los dos JSON
    python scripts/build_snippets.py --check   # falla si no están al día (para CI)

Fuentes:
    snippets/meta.json             lenguajes, librerías y escenarios (textos ES/EN)
    snippets/<escenario>/<archivo> el código, escrito en español
    snippets/traducciones-en.json  sustituciones para generar la versión en inglés

Estructura de salida (la misma en ambos idiomas):
    scenarios[]                    {id, title, description}
    languages[].libraries[]        {id, name, lazy, lazy_note, snippets{<escenario>: {filename, code}}}

Solo usa la biblioteca estándar y no accede a la red.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNIPPETS_DIR = ROOT / "snippets"
OUTPUTS = {"es": ROOT / "snippets.es.json", "en": ROOT / "snippets.en.json"}
CODE_SUFFIXES = {".py", ".R", ".jl", ".mjs", ".sh"}
FORMAT_VERSION = 1

# Credenciales reales que nunca deben llegar a un snippet.
SECRET_PATTERNS = [re.compile(r"ASIA[A-Z0-9]{16}"), re.compile(r"eyJ[A-Za-z0-9_-]{20,}")]
# Restos de español que delatan una traducción incompleta.
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
    """Español → inglés: frases exactas (largas primero) y luego identificadores."""
    for spanish, english in sorted(translations["frases"], key=lambda pair: -len(pair[0])):
        if spanish in code:
            used.add(spanish)
            code = code.replace(spanish, english)
    for spanish, english in translations["palabras"].items():
        if re.search(rf"\b{re.escape(spanish)}\b", code):
            used.add(spanish)
            code = re.sub(rf"\b{re.escape(spanish)}\b", english, code)
    return code


def build():
    errors = []
    meta = load_json(SNIPPETS_DIR / "meta.json", errors)
    translations = load_json(SNIPPETS_DIR / "traducciones-en.json", errors)
    if errors:
        return None, errors

    scenarios = meta["scenarios"]
    registered = {}  # ruta relativa a snippets/ -> (lenguaje, librería)
    output = {lang: {"version": FORMAT_VERSION, "lang": lang, "scenarios": [], "languages": []} for lang in OUTPUTS}
    used_translations = set()

    for scenario in scenarios:
        for lang in OUTPUTS:
            text = scenario[lang]
            output[lang]["scenarios"].append(
                {"id": scenario["id"], "title": text["title"], "description": text["description"]}
            )

    for language in meta["languages"]:
        blocks = {lang: {"id": language["id"], "name": language["name"], "highlight": language["highlight"],
                         "libraries": []} for lang in OUTPUTS}
        for library in language["libraries"]:
            entries = {lang: {} for lang in OUTPUTS}
            for scenario in scenarios:
                path = SNIPPETS_DIR / scenario["dir"] / library["file"]
                if not path.exists():
                    continue
                registered[path.relative_to(SNIPPETS_DIR).as_posix()] = (language["id"], library["id"])
                code_es = path.read_text(encoding="utf-8").rstrip("\n")
                where = path.relative_to(ROOT).as_posix()
                for pattern in SECRET_PATTERNS:
                    if pattern.search(code_es):
                        errors.append(f"{where}: parece contener una credencial real")
                code_en = translate(code_es, translations, used_translations)
                leftover = SPANISH_LEFTOVERS.search(code_en)
                if leftover:
                    errors.append(f"{where}: la versión en inglés conserva español ('{leftover.group(0)}'); "
                                  "agrega la frase a snippets/traducciones-en.json")
                entries["es"][scenario["id"]] = {"filename": library["file"], "code": code_es}
                entries["en"][scenario["id"]] = {"filename": library["file"], "code": code_en}
            if not entries["es"]:
                errors.append(f"snippets/meta.json: '{library['file']}' no existe en ningún escenario")
                continue
            for lang in OUTPUTS:
                blocks[lang]["libraries"].append({
                    "id": library["id"],
                    "name": library["name"],
                    "lazy": library["lazy"],
                    "lazy_note": library["lazy_note"][lang],
                    "snippets": entries[lang],
                })
        for lang in OUTPUTS:
            output[lang]["languages"].append(blocks[lang])

    # Archivos de código en snippets/ que meta.json no conoce.
    for path in sorted(SNIPPETS_DIR.rglob("*")):
        if path.is_file() and path.suffix in CODE_SUFFIXES:
            if path.relative_to(SNIPPETS_DIR).as_posix() not in registered:
                errors.append(f"{path.relative_to(ROOT).as_posix()}: no está registrado en snippets/meta.json")

    # Traducciones que ya no se usan (señal de que el snippet cambió).
    known = {pair[0] for pair in translations["frases"]} | set(translations["palabras"])
    for stale in sorted(known - used_translations):
        errors.append(f"snippets/traducciones-en.json: '{stale}' ya no aparece en ningún snippet")

    return output, errors


def main():
    parser = argparse.ArgumentParser(description="Genera o verifica snippets.es.json y snippets.en.json")
    parser.add_argument("--check", action="store_true", help="falla si los JSON no están al día")
    args = parser.parse_args()

    output, errors = build()
    if errors:
        print("Errores al construir los snippets:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    status = 0
    for lang, path in OUTPUTS.items():
        content = json.dumps(output[lang], ensure_ascii=False, indent=2) + "\n"
        if args.check:
            current = path.read_text(encoding="utf-8") if path.exists() else None
            if current != content:
                print(f"{path.name} no está al día. Ejecuta `python scripts/build_snippets.py` y commitea.",
                      file=sys.stderr)
                status = 1
        else:
            path.write_text(content, encoding="utf-8")
            print(f"{path.name} escrito.")
    if args.check and status == 0:
        print("snippets.es.json y snippets.en.json al día.")
    return status


if __name__ == "__main__":
    sys.exit(main())
