#!/usr/bin/env python3
"""Auftrag mit allen bisherigen Einstellungen neu slicen (z. B. nach neuen Herstellerwerten in druck.py).

    python3 werkzeug/neu_rechnen.py auftraege/<ordner> [weitere Ordner …] [--detail-025] [--extra=schluessel=wert …]

- Übernimmt Teile, Köpfe, Farben und alle Prozess-Einstellungen aus der Projekt-3MF (druck.py --wie).
- Neu kommen nur die Werte, die druck.py inzwischen selbst setzt (z. B. 0,25-Filamentprofile, Kopfwechsel-Werte).
- --detail-025: 0,25er-Aufträge zusätzlich mit --detail (Außenwand-Beschleunigung 3000 usw.).
- Ordnername, Dateinamen, Projekt (gruppe/nr/titel) bleiben; Zeit/Gramm vorher → nachher wird ausgegeben.
"""
import json, shutil, subprocess, sys, tempfile
from pathlib import Path

W = Path(__file__).resolve().parent.parent


def neu(ordner: Path, detail025: bool, extra=()) -> str:
    info = json.loads((ordner / "auftrag.json").read_text(encoding="utf-8"))
    if info.get("bemalt") or info.get("duesen_mm"):
        return f"übersprungen ({'bemalt' if info.get('bemalt') else 'gemischte Düsen'})"
    if not info.get("projekt") or not (ordner / info["projekt"]).exists():
        return "übersprungen (Projekt-3MF fehlt)"
    if info.get("geaendert"):
        return "übersprungen (von Tom in Flash Studio geändert – im Chat klären)"
    tmp = Path(tempfile.mkdtemp(prefix="neu_")) / ordner.name
    shutil.copytree(ordner, tmp)
    cmd = [sys.executable, str(W / "werkzeug" / "druck.py"), "--drucker", info.get("drucker", "c5pro"), "--name", info["name"],
           "--ausgabe", str(tmp), "--wie", str(tmp)]
    slots = {int(s["slot"]): s for s in info.get("slots", [])}
    for t in info["teile"]:
        q = tmp / t["datei"]
        if not q.exists():
            shutil.rmtree(tmp.parent, ignore_errors=True)
            return f"übersprungen (Modell fehlt: {t['datei']})"
        cmd += ["--teil", f"{q}:{slots.get(int(t['slot']), {}).get('material', 'PLA')}:{t['slot']}"]
    sys.path.insert(0, str(W / "werkzeug")); import druck
    if druck.wie_zusammen(tmp, info): cmd.append("--zusammen")
    n = max(slots) if slots else 1
    cmd += ["--farben", ",".join(slots.get(i, {}).get("farbe") or "leer" for i in range(1, n + 1)),
            "--schicht", str(info.get("schicht", "0.20")), "--stufe", str(info.get("stufe", "Standard")), "--infill", str(int(info.get("infill", 15))),
            "--stuetzen", info.get("stuetzen") if info.get("stuetzen") in ("aus", "auto", "baum") else "aus",
            "--brim", info.get("brim") if info.get("brim") in ("aus", "auto", "an") else "auto"]
    if info.get("waende"): cmd += ["--waende", str(int(info["waende"]))]
    d = str(info.get("duese_mm") or "0.4")
    if d != "0.4": cmd += ["--duese", d]
    if detail025 and d == "0.25": cmd.append("--detail")
    if info.get("quelle"): cmd += ["--quelle", info["quelle"]]
    if info.get("stuetz_kopf"): cmd += ["--stuetz-kopf", str(info["stuetz_kopf"])]
    for e in extra: cmd += ["--extra", e]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=5400)
    if r.returncode != 0 or "OK  " not in r.stdout:
        shutil.rmtree(tmp.parent, ignore_errors=True)
        return "FEHLER: " + (r.stdout + r.stderr)[-400:].strip()
    nj = json.loads((tmp / "auftrag.json").read_text(encoding="utf-8"))
    nj["ordner"] = ordner.name; nj["datum"] = info.get("datum", nj.get("datum"))
    for k in ("angepasst",):
        if k in info: nj[k] = info[k]
    (tmp / "auftrag.json").write_text(json.dumps(nj, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.rmtree(ordner); shutil.move(str(tmp), str(ordner)); shutil.rmtree(tmp.parent, ignore_errors=True)
    return f"{info.get('zeit')} / {info.get('gramm')} g  →  {nj.get('zeit')} / {nj.get('gramm')} g"


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    det = "--detail-025" in sys.argv
    ex = [x.split("=", 1)[1] for x in sys.argv[1:] if x.startswith("--extra=")]
    for o in args:
        print(f"{Path(o).name}: {neu(Path(o), det, ex)}", flush=True)
