#!/usr/bin/env python3
"""Se ejecuta después de `quarto render`: quita del HTML las fuentes web incrustadas.

Quarto incrusta Source Sans Pro (unos 3 MB en base64) aunque el tema use fuentes del sistema
(ver tema.scss). Sin esas fuentes el archivo queda en torno a 1 MB y sigue siendo un solo archivo.
"""
import pathlib
import re
import urllib.parse

html = pathlib.Path(__file__).resolve().parent / "presentacion.html"
texto = html.read_text(encoding="utf-8")
antes = len(texto)


def limpiar(m):
    css = urllib.parse.unquote(m.group(1))
    css = re.sub(r"@font-face\s*\{[^}]*\}", "", css)
    return f'<style>{css}</style>'


texto = re.sub(r'<link href="data:text/css,([^"]*)" rel="stylesheet">', limpiar, texto)
html.write_text(texto, encoding="utf-8")
print(f"quitar_fuentes: {antes / 1e6:.1f} MB -> {len(texto) / 1e6:.1f} MB")
