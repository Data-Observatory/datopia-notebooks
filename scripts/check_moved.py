#!/usr/bin/env python3
"""Verifica los stubs de notebooks movidos: cada `demo.ipynb` con `datopia_movido_a` debe apuntar a un
notebook que existe. Los stubs viven en las rutas antiguas (`<categoria>/<fuente>/demo.ipynb`).

Solo usa la biblioteca estándar y no accede a la red.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    errors, count = [], 0
    for path in sorted(ROOT.glob("*/*/demo.ipynb")):
        relative = path.relative_to(ROOT)
        if relative.parts[0] == "notebooks":
            continue
        try:
            destination = json.loads(path.read_text(encoding="utf-8"))["metadata"]["datopia_movido_a"]
        except (OSError, KeyError, json.JSONDecodeError):
            errors.append(f"{relative}: notebook fuera de notebooks/ y sin 'datopia_movido_a'")
            continue
        count += 1
        if not (ROOT / destination).exists():
            errors.append(f"{relative}: apunta a {destination}, que no existe")
    if errors:
        print("Errores en notebooks movidos:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"{count} enlaces antiguos apuntan a notebooks que existen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
