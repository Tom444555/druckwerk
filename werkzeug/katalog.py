#!/usr/bin/env python3
"""Lager-Übersicht für Claude: liest lager/karten.json + auftraege/index.json und schreibt lager/KATALOG.md
(Bereich → Projekt → Teile, mit Modell-Quellen). Meldet Projekte ohne Karteikarte und Karten ohne Projekt.
Aufruf: python3 werkzeug/katalog.py [--privat ../druckwerk-modelle]"""
import json, sys, datetime
from pathlib import Path

W = Path(__file__).resolve().parent.parent


def main():
    K = json.loads((W / "lager" / "karten.json").read_text(encoding="utf-8"))
    I = json.loads((W / "auftraege" / "index.json").read_text(encoding="utf-8"))
    P = {}
    for a in I:
        P.setdefault(a.get("gruppe") or a["name"], []).append(a)
    namen = {b["id"]: b["name"] for b in K["bereiche"]}
    ohne = [k for k in P if k not in K["karten"]]
    verwaist = [k for k in K["karten"] if k not in P]
    z = ["# Lager-Katalog", "", f"Stand {datetime.date.today().isoformat()} – erzeugt von `werkzeug/katalog.py`, nicht von Hand ändern. Karteikarten: `lager/karten.json`.", ""]
    for b in K["bereiche"]:
        ps = [(k, t) for k, t in P.items() if K["karten"].get(k, {}).get("bereich", "sonstiges") == b["id"]]
        if not ps:
            continue
        z += [f"## {b['name']}", ""]
        for k, teile in sorted(ps, key=lambda x: x[0]):
            c = K["karten"].get(k, {})
            teile.sort(key=lambda t: (t.get("nr") or 99, t["ordner"]))
            titel = teile[0].get("gruppe_titel") or k
            z.append(f"### {titel} (`{k}`){' – ARCHIV' if c.get('archiv') else ''}")
            z.append(f"- Stand: {c.get('stand', 'gerechnet')} · Herkunft: {c.get('herkunft') or '–'} · Schlagworte: {', '.join(c.get('schlagworte', [])) or '–'}")
            if c.get("modell"):
                fehlt = [m for m in c["modell"] if not (W / m).exists()]
                z.append("- Modell: " + ", ".join(f"`{m}`" for m in c["modell"]) + (f"  ⚠ fehlt: {', '.join(fehlt)}" if fehlt else ""))
            for t in teile:
                z.append(f"  - {t.get('nr') or '–'}. {t.get('titel') or t['name']} → `auftraege/{t['ordner']}/` · {t.get('zeit')} · {t.get('gramm')} g · "
                         + ", ".join(f"K{s['slot']} {s['material']} {s['farbe']}" for s in t.get("slots", [])))
            z.append("")
    if len(sys.argv) > 2 and sys.argv[1] == "--privat":
        pi = json.loads((Path(sys.argv[2]) / "index.json").read_text(encoding="utf-8"))
        z += ["## Privates Lager (Tom444555/druckwerk-modelle) – nur Verweise", ""]
        for p in pi.get("projekte", []):
            z.append(f"- **{p.get('titel') or p['ordner']}** (`{p['ordner']}`) · {namen.get(p.get('bereich'), 'Unsortiert')} · {len(p.get('auftraege', []))} Druckdatei(en) · {', '.join(p.get('schlagworte', []))}")
        z.append("")
    (W / "lager" / "KATALOG.md").write_text("\n".join(z), encoding="utf-8")
    print(f"lager/KATALOG.md: {len(P)} Projekte, {len(I)} Aufträge")
    if ohne: print("OHNE Karteikarte (in lager/karten.json eintragen oder beim Slicen --bereich angeben):", ", ".join(ohne))
    if verwaist: print("Karte ohne Projekt:", ", ".join(verwaist))


if __name__ == "__main__":
    main()
