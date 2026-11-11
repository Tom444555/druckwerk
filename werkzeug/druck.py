#!/usr/bin/env python3
"""druckwerk – Modell(e) + Drucker + Einstellungen -> fertige USB-Druckdatei (.gcode) + Bericht.

Beispiel:
  python3 werkzeug/druck.py --drucker kobrax --name halter \
      --teil modelle/halter.scad:PLA --teil modelle/schrift.scad:PLA \
      --farben "schwarz,rot" --schicht 0.20 --infill 20
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, datetime
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
WERKZEUG = WURZEL / "werkzeug"
ORCA = Path(os.environ.get("ORCA", WERKZEUG / "orca" / "squashfs-root" / "AppRun"))
PROFILE = Path(os.environ.get("ORCA_PROFILE", WERKZEUG / "orca" / "profile" / "resources" / "profiles"))


# ---------- Profile auflösen (inherits-Kette -> vollständige JSON) ----------
_index = {}

def _baue_index():
    if _index:
        return
    for f in PROFILE.rglob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict) and "name" in d and "type" in d:
            # Hersteller-Ordner bevorzugen, Bibliothek nur als Rückfall
            alt = _index.get((d["type"], d["name"]))
            if alt is None or "OrcaFilamentLibrary" in str(alt):
                _index[(d["type"], d["name"])] = f
            _index.setdefault((d["type"], f.stem), f)

def aufloesen(typ, name, tiefe=0):
    _baue_index()
    f = _index.get((typ, name))
    if f is None:
        raise SystemExit(f"Profil nicht gefunden: {typ} '{name}'")
    d = json.loads(f.read_text(encoding="utf-8"))
    eltern = d.get("inherits")
    basis = aufloesen(typ, eltern, tiefe + 1) if eltern else {}
    basis.update(d)
    if tiefe == 0:
        basis.pop("inherits", None)
        basis["from"] = "system"
        basis["instantiation"] = "true"
    return basis


# ---------- Modelle vorbereiten ----------
def nach_stl(pfad: Path, ziel: Path) -> Path:
    if pfad.suffix.lower() == ".scad":
        out = ziel / (pfad.stem + ".stl")
        r = subprocess.run(["openscad", "-o", str(out), str(pfad)], capture_output=True, text=True)
        if r.returncode != 0 or not out.exists():
            raise SystemExit(f"OpenSCAD-Fehler bei {pfad}:\n{r.stderr[-2000:]}")
        return out
    return pfad


def index_neu(ordner: Path):
    """auftraege/index.json – Liste aller Aufträge, neueste zuerst (für die App)."""
    liste = []
    for f in ordner.glob("*/auftrag.json"):
        try:
            liste.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    liste.sort(key=lambda x: (x.get("datum", ""), x.get("ordner", "")), reverse=True)
    (ordner / "index.json").write_text(json.dumps(liste, ensure_ascii=False, indent=1), encoding="utf-8")


FARB_RGB = {"weiss": "[0.95,0.94,0.9]", "weiß": "[0.95,0.94,0.9]", "schwarz": "[0.13,0.13,0.13]", "rot": "[0.8,0.1,0.1]",
            "blau": "[0.15,0.35,0.9]", "gruen": "[0.13,0.64,0.28]", "grün": "[0.13,0.64,0.28]", "gelb": "[0.96,0.77,0.1]",
            "orange": "[0.97,0.45,0.09]", "grau": "[0.56,0.56,0.58]", "silber": "[0.75,0.75,0.75]", "gold": "[0.83,0.63,0.09]"}


def vorschau_bild(ziel: Path, teile_stl, slots_farben):
    """vorschau.png (900×700) aus den STLs, schräg von vorn – für die App und den Chat."""
    try:
        zeilen = []
        for st, fb in zip(teile_stl, slots_farben):
            rgb = FARB_RGB.get((fb or "").lower().strip(), "[0.6,0.6,0.62]")
            zeilen.append(f'color({rgb}) import("{Path(st).resolve()}");')
        scad = ziel / "_vorschau.scad"
        scad.write_text("\n".join(zeilen), encoding="utf-8")
        subprocess.run(["xvfb-run", "-a", "openscad", "-o", str(ziel / "vorschau.png"), "--viewall", "--autocenter",
                        "--camera=0,0,0,62,0,335,0", "--imgsize=900,700", "--colorscheme=Tomorrow", str(scad)],
                       capture_output=True, timeout=300)
        scad.unlink(missing_ok=True)
        return (ziel / "vorschau.png").exists()
    except Exception:
        return False


def app_stl(st: Path, ziel_flaechen=60000):
    """Leichte Kopie für die 3D-Vorschau in der App (Handy): große Netze auf ~60.000 Dreiecke reduzieren."""
    try:
        import pymeshlab
        ms = pymeshlab.MeshSet(); ms.load_new_mesh(str(st))
        if ms.current_mesh().face_number() <= ziel_flaechen * 1.3:
            return st.name
        ms.meshing_decimation_quadric_edge_collapse(targetfacenum=ziel_flaechen, preservenormal=True, preserveboundary=True)
        aus = st.with_name(st.stem + ".app.stl"); ms.save_current_mesh(str(aus), binary=True)
        return aus.name
    except Exception:
        return st.name


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drucker", required=True, help="kobrax | c5pro")
    ap.add_argument("--name", required=True, help="Auftragsname (ohne Leerzeichen)")
    ap.add_argument("--teil", action="append", required=True,
                    help="Datei[:Material[:Slot]]  z. B. modelle/a.scad:PLA:1  (Slot 1–4 = Farbe/Kopf)")
    ap.add_argument("--farben", default="", help="Farbnamen je Slot für den Bericht, z. B. 'schwarz,rot'")
    ap.add_argument("--schicht", default="0.20")
    ap.add_argument("--stufe", default="Standard")
    ap.add_argument("--infill", type=int, default=15, help="Füllung in %%")
    ap.add_argument("--waende", type=int, default=None, help="Anzahl Wände")
    ap.add_argument("--stuetzen", choices=["aus", "auto", "baum"], default="aus")
    ap.add_argument("--brim", choices=["aus", "auto", "an"], default="auto")
    ap.add_argument("--anordnen", action="store_true", default=True)
    ap.add_argument("--zusammen", action="store_true",
                    help="Teile als EIN Objekt behandeln (mehrfarbiges Teil aus mehreren Dateien)")
    ap.add_argument("--extra", action="append", default=[], help="Slicer-Einstellung überschreiben: schluessel=wert (mehrfach)")
    ap.add_argument("--quelle", default="", help="Link zum Original-Modell (MakerWorld, Printables …)")
    ap.add_argument("--ausgabe", default=None, help="Zielordner (Standard: auftraege/<datum>_<name>)")
    a = ap.parse_args()

    cfg = json.loads((WURZEL / "drucker" / f"{a.drucker}.json").read_text(encoding="utf-8"))
    if a.schicht not in cfg["schichten"]:
        raise SystemExit(f"Schicht {a.schicht} gibt es für {cfg['name']} nicht. Möglich: {cfg['schichten']}")

    teile = []  # (pfad, material, slot)
    for i, t in enumerate(a.teil):
        bits = t.split(":")
        pfad = Path(bits[0])
        mat = (bits[1] if len(bits) > 1 and bits[1] else "PLA").upper()
        slot = int(bits[2]) if len(bits) > 2 else None
        teile.append([pfad, mat, slot])

    # Slots vergeben: gleiches Material ohne Slotangabe -> Slot 1, sonst fortlaufend
    belegt = {}
    naechster = 1
    for t in teile:
        if t[2] is None:
            t[2] = 1 if len(teile) == 1 else None
    for t in teile:
        if t[2] is None:
            t[2] = naechster
        naechster = max(naechster, t[2] + 1)
        if t[2] in belegt and belegt[t[2]] != t[1]:
            raise SystemExit(f"Slot {t[2]} ist schon mit {belegt[t[2]]} belegt, nicht {t[1]}.")
        belegt[t[2]] = t[1]
    slots = max(belegt)
    if slots > cfg["farben_max"]:
        raise SystemExit(f"{cfg['name']} kann max. {cfg['farben_max']} Farben/Köpfe.")
    for s in range(1, slots + 1):
        belegt.setdefault(s, belegt[1])
        if belegt[s] not in cfg["filamente"]:
            raise SystemExit(f"Material {belegt[s]} unbekannt für {cfg['name']}. Möglich: {list(cfg['filamente'])}")

    datum = datetime.date.today().isoformat()
    ziel = Path(a.ausgabe) if a.ausgabe else WURZEL / "auftraege" / f"{datum}_{a.name}_{cfg['kurz']}"
    ziel.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="druckwerk_"))

    # Profile
    maschine = aufloesen("machine", cfg["maschine"])
    prozess = aufloesen("process", cfg["prozess_vorlage"].format(schicht=a.schicht, stufe=a.stufe))
    prozess["sparse_infill_density"] = f"{a.infill}%"
    if a.waende:
        prozess["wall_loops"] = str(a.waende)
    if a.stuetzen == "aus":
        prozess["enable_support"] = "0"
    else:
        prozess["enable_support"] = "1"
        prozess["support_type"] = "tree(auto)" if a.stuetzen == "baum" else "normal(auto)"
    prozess["brim_type"] = {"aus": "no_brim", "auto": "auto_brim", "an": "outer_only"}[a.brim]
    prozess["compatible_printers"] = []  # Kompatibilitätsprüfung abschalten
    for ex in a.extra:
        k, v = ex.split("=", 1); prozess[k.strip()] = v.strip()
    # Druckplatte: bestimmt die Betttemperatur (Cool Plate = 35 °C bei PLA!). Kommt aus drucker/*.json.
    platte = cfg.get("platte", "Textured PEI Plate")
    maschine["default_bed_type"] = platte
    prozess["curr_bed_type"] = platte
    fil_pfade = []
    for s in range(1, slots + 1):
        f = aufloesen("filament", cfg["filamente"][belegt[s]])
        f["compatible_printers"] = []
        f.setdefault("filament_is_support", ["0"])  # fehlt in manchen Herstellerprofilen
        p = tmp / f"filament{s}.json"
        p.write_text(json.dumps(f), encoding="utf-8")
        fil_pfade.append(str(p))
    mp, pp = tmp / "maschine.json", tmp / "prozess.json"
    mp.write_text(json.dumps(maschine), encoding="utf-8")
    pp.write_text(json.dumps(prozess), encoding="utf-8")

    stls = [nach_stl(t[0], tmp) for t in teile]
    for s in stls:
        if Path(s).resolve().parent != ziel.resolve():
            shutil.copy(s, ziel / Path(s).name)

    cmd = [str(ORCA), "--slice", "0", "--arrange", "1", "--orient", "0",
           "--load-settings", f"{mp};{pp}",
           "--load-filaments", ";".join(fil_pfade),
           "--load-filament-ids", ",".join(str(t[2]) for t in teile),
           "--allow-multicolor-oneplate", "--export-statistics",
           "--outputdir", str(tmp / "out"),
           "--export-3mf", "projekt.3mf"]   # Projektdatei (öffnen in Anycubic Slicer Next / OrcaSlicer)
    gemischt = len(set(belegt.values())) > 1
    if gemischt:
        cmd.append("--allow-mix-temp")
    if a.zusammen and len(stls) > 1:
        cmd.append("--assemble")
    cmd += [str(s) for s in stls]
    env = dict(os.environ)
    if not env.get("DISPLAY"):
        cmd = ["xvfb-run", "-a"] + cmd
    # Bis zu 5 Durchläufe: Werte außerhalb des erlaubten Bereichs (Profil-Altlasten) automatisch korrigieren
    korrigiert = []
    for _ in range(5):
        r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=1200)
        fehler = re.findall(r"(\w+): (\S+) not in range \[([\d.\-]+), ([\d.\-]+)\]", r.stdout + r.stderr)
        if r.returncode == 0 or not fehler:
            break
        for schluessel, wert_alt, lo, hi in fehler:
            for pfad in [mp, pp] + [Path(x) for x in fil_pfade]:
                d = json.loads(pfad.read_text(encoding="utf-8"))
                if schluessel in d:
                    neu_w = lo if "." not in lo else lo
                    d[schluessel] = [neu_w] * len(d[schluessel]) if isinstance(d[schluessel], list) else neu_w
                    pfad.write_text(json.dumps(d), encoding="utf-8")
                    korrigiert.append(f"{schluessel}: {wert_alt} -> {neu_w}")
    (ziel / "slicer.log").write_text("\n".join(korrigiert) + "\n---\n" + r.stdout[-20000:] + "\n---\n" + r.stderr[-20000:], encoding="utf-8")
    gcodes = sorted((tmp / "out").glob("*.gcode"))
    if not gcodes:
        raise SystemExit(f"Slicen fehlgeschlagen (Code {r.returncode}). Siehe {ziel/'slicer.log'}")

    gname = f"{a.name}_{cfg['kurz']}.gcode"
    for kandidat in [tmp / "out" / "projekt.3mf", tmp / "projekt.3mf", Path.cwd() / "projekt.3mf"]:
        if kandidat.exists():
            shutil.move(str(kandidat), ziel / f"{a.name}_{cfg['kurz']}.3mf"); break
    shutil.copy(gcodes[0], ziel / gname)
    stat = {}
    for sf in (tmp / "out").glob("*statistics.json"):
        try:
            stat = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Werte aus G-Code-Kommentaren (zuverlässig für alle Versionen)
    txt = (ziel / gname).read_text(encoding="utf-8", errors="ignore")
    def wert(muster):
        m = re.search(muster, txt)
        return m.group(1).strip() if m else "?"
    zeit = wert(r";\s*(?:estimated printing time \(normal mode\)|model printing time)\s*=\s*([^\n;]+)")
    gramm = wert(r";\s*filament used \[g\]\s*=\s*([^\n]+)")
    meter = wert(r";\s*filament used \[mm\]\s*=\s*([^\n]+)")
    try:
        meter = ", ".join(f"{float(x)/1000:.2f} m" for x in meter.split(","))
    except Exception:
        pass

    zeit = re.sub(r"^(0d\s*)?(0h\s*)?", "", zeit)
    duese = wert(r"; nozzle_temperature = ([^\n]+)")
    bett = wert(r"; (?:hot_plate_temp|textured_plate_temp|bed_temperature) = ([^\n]+)")
    farben = [x.strip() for x in a.farben.split(",")] if a.farben else []
    zeilen = [f"# Druckauftrag: {a.name}", "",
              f"**Drucker:** {cfg['name']}  ",
              f"**Datei für USB:** `{gname}`  ",
              f"**Druckzeit (geschätzt):** {zeit}  ",
              f"**Filament:** {gramm} g ({meter})  ",
              (f"**Original-Modell:** {a.quelle}" if a.quelle else ""), "",
              "## Spulen / Köpfe einlegen", "",
              "| Slot | Material | Farbe | Profil |", "|---|---|---|---|"]
    for s in range(1, slots + 1):
        fb = farben[s - 1] if s - 1 < len(farben) else "-"
        zeilen.append(f"| {s} | {belegt[s]} | {fb} | {cfg['filamente'][belegt[s]]} |")
    zeilen += ["", "## Einstellungen", "",
               f"- Schichthöhe: {a.schicht} mm ({a.stufe})",
               f"- Füllung: {a.infill} %",
               f"- Wände: {a.waende or 'Profil-Standard'}",
               f"- Stützen: {a.stuetzen}",
               f"- Brim: {a.brim}",
               f"- Düsentemperatur: {duese} °C, Bett: {bett} °C", "",
               "## Teile", ""]
    for t in teile:
        zeilen.append(f"- `{t[0].name}` → Slot {t[2]} ({t[1]})")
    zeilen += ["", "## Am Drucker", ""] + [f"- {h}" for h in cfg["hinweise"]] + [
        "- Vor dem Start: Druckplatte sauber und leer, richtige Spulen in den Slots."]
    if gemischt:
        zeilen += ["", "> ⚠ Unterschiedliche Materialien in einem Druck "
                   f"({', '.join(sorted(set(belegt.values())))}) – Haftung zwischen den Materialien "
                   "und Temperaturen prüfen."]
    # Daten für die App
    info = {"name": a.name, "drucker": cfg["kurz"], "drucker_name": cfg["name"], "datum": datum,
            "ordner": ziel.name, "gcode": gname, "zeit": zeit, "gramm": gramm, "meter": meter,
            "duese": duese, "bett": bett, "schicht": a.schicht, "stufe": a.stufe, "infill": a.infill,
            "waende": a.waende, "stuetzen": a.stuetzen, "brim": a.brim, "gemischt": gemischt,
            "slots": [{"slot": s_, "material": belegt[s_],
                       "farbe": farben[s_ - 1] if s_ - 1 < len(farben) else ""} for s_ in range(1, slots + 1)],
            "teile": [{"datei": Path(st).name, "slot": t[2]} for t, st in zip(teile, stls)],
            "quelle": a.quelle,
            "teile_app": [{"datei": app_stl(ziel / Path(st).name), "slot": t[2]} for t, st in zip(teile, stls)]}
    if vorschau_bild(ziel, [ziel / Path(st).name for st in stls],
                     [farben[t[2] - 1] if t[2] - 1 < len(farben) else "" for t in teile]):
        info["vorschau"] = "vorschau.png"
    pj = ziel / f"{a.name}_{cfg['kurz']}.3mf"
    if pj.exists():
        info["projekt"] = pj.name
    (ziel / "auftrag.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    index_neu(ziel.parent)
    (ziel / "BERICHT.md").write_text("\n".join(zeilen) + "\n", encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"OK  {ziel/gname}\n    Zeit {zeit} | {gramm} g")


if __name__ == "__main__":
    main()
