#!/usr/bin/env python3
"""spulenwechsel.py – fünfte Farbe: fügt in eine fertige .gcode eine Pause ein, in der an EINEM Kopf die Spule gewechselt wird.

  python3 werkzeug/spulenwechsel.py auftrag.gcode [--kopf 4] [--text "Kopf 4: Dunkelrot → Weiß"]

Voraussetzung: beide Farben liegen beim Slicen auf demselben Kopf (`--teil a.stl:PLA:4 --teil b.stl:PLA:4`) und werden in getrennten Höhen gedruckt.
Das Skript sucht die größte Höhen-Lücke, in der dieser Kopf am Modell nichts druckt (Reinigungsturm zählt nicht), und setzt den Pausenbefehl
des Maschinenprofils (`machine_pause_gcode`, beim Creator 5 Pro `M25`) an den Anfang der ersten Schicht nach der Lücke.
Am Gerät noch nicht erprobt (Stand 16.11.2026).
"""
import argparse, re, sys


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gcode"); ap.add_argument("--kopf", type=int, default=4); ap.add_argument("--text", default="Spule wechseln, dann fortsetzen")
    ap.add_argument("--min-luecke", type=float, default=0.3)
    a = ap.parse_args()
    L = open(a.gcode, errors="surrogateescape").read().split("\n")
    pause = next((l.split("=", 1)[1].strip() for l in L if l.startswith("; machine_pause_gcode")), "M25") or "M25"
    z, t, typ, zs = 0.0, 0, "", set()
    for ln in L:
        if ln.startswith(";TYPE:"): typ = ln[6:].lower()
        elif ln.startswith(";Z:"): z = float(ln[3:])
        elif re.match(r"T[0-3]\s*($|;)", ln): t = int(ln[1])
        elif t == a.kopf - 1 and ln.startswith(("G1 ", "G2 ", "G3 ")) and " E" in ln and "prime" not in typ and "tower" not in typ: zs.add(z)
    alle = sorted(zs); luecken = sorted(((b - x, x, b) for x, b in zip(alle[:-1], alle[1:]) if b - x >= a.min_luecke), reverse=True)
    if not luecken: sys.exit(f"Kopf {a.kopf}: keine Höhen-Lücke ≥ {a.min_luecke} mm gefunden – die zwei Farben überschneiden sich in der Höhe.")
    _, unten, oben = luecken[0]
    i = next(k for k, ln in enumerate(L) if ln.startswith(";Z:") and float(ln[3:]) > unten + 1e-6)
    L.insert(i + 1, f"{pause} ; druckwerk: PAUSE – {a.text}")
    open(a.gcode, "w", errors="surrogateescape").write("\n".join(L))
    print(f"Pause ({pause}) bei Z {L[i][3:]} mm: Kopf {a.kopf} druckt bis {unten} mm die erste Farbe, ab {oben} mm die zweite.")


if __name__ == "__main__":
    main()
