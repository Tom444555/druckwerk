#!/usr/bin/env python3
"""Nimmt aus fertigen c5pro-.gcode die Heizzeile ohne Kopf-Nummer im Startblock heraus (wie aktuelles Flash-Studio-Profil).
Aufruf: python3 werkzeug/startheiz.py auftraege/*_c5pro  (Ordner oder .gcode)"""
import re, sys
from pathlib import Path
def richten(g: Path) -> bool:
    kopf = b""
    with g.open("rb") as f:
        daten = f.read()
    a = daten.find(b";start_gcode\n"); e = daten.find(b";start_gcode end", a)
    if a < 0 or e < 0: return False
    block = daten[a:e]
    neu = re.sub(rb"(?m)^M104 S\d+[ \t]*\n", b"", block)
    if neu == block: return False
    g.write_bytes(daten[:a] + neu + daten[e:]); return True
if __name__ == "__main__":
    n = 0
    for p in map(Path, sys.argv[1:]):
        for g in ([p] if p.suffix == ".gcode" else sorted(p.glob("*.gcode"))):
            if richten(g): n += 1; print("gerichtet:", g)
    print(n, "Datei(en) geändert")
