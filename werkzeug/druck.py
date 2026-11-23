#!/usr/bin/env python3
"""druckwerk – Modell(e) + Drucker + Einstellungen -> fertige USB-Druckdatei (.gcode) + Bericht.

Beispiel:
  python3 werkzeug/druck.py --drucker kobrax --name halter \
      --teil modelle/halter.scad:PLA --teil modelle/schrift.scad:PLA \
      --farben "schwarz,rot" --schicht 0.20 --infill 20

Bemalt (Farbe je Dreieck, z. B. aus werkzeug/textur_farben.py):
  python3 werkzeug/druck.py --drucker c5pro --name figur --bemalt /tmp/fig/figur_bemalt.3mf \
      --farben "schwarz,gold,rot,weiss" [--materialien "PLA,PLA-SILK,PLA,PLA"] --schicht 0.12 --stuetzen auto
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, datetime
import numpy as np
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


# ---------- Einstellungen eines fertigen Auftrags wiederverwenden (--wie) ----------
WIE_NICHT = ("filament", "printer_", "machine_", "nozzle_", "extruder", "default_", "upward_", "bed_", "host", "print_host", "thumbnails",
             "different_settings", "version", "name", "from", "inherits", "is_custom", "curr_bed_type", "compatible", "print_settings_id",
             "instantiation", "setting_id", "print_compatible", "wipe_tower_x", "wipe_tower_y", "flush_volumes", "flush_multiplier")


def wie_einstellungen(ordner: Path):
    """Liest Metadata/project_settings.config aus der Projekt-3MF eines Auftrags → (alle Einstellungen, auftrag.json)."""
    import zipfile
    info = json.loads((ordner / "auftrag.json").read_text(encoding="utf-8"))
    pj = ordner / str(info.get("projekt") or "")
    if not pj.is_file():
        raise SystemExit(f"--wie: Projekt-3MF fehlt in {ordner}")
    with zipfile.ZipFile(pj) as z:
        return json.loads(z.read("Metadata/project_settings.config").decode("utf-8")), info


def wie_zusammen(ordner: Path, info) -> bool:
    """War der Auftrag EIN mehrteiliges Objekt (--zusammen)? Steht in auftrag.json, sonst aus der 3MF gelesen."""
    import zipfile
    if "zusammen" in info:
        return bool(info["zusammen"])
    try:
        with zipfile.ZipFile(ordner / info["projekt"]) as z:
            ms = z.read("Metadata/model_settings.config").decode("utf-8", "ignore")
        return len(re.findall(r"<object\b", ms)) == 1 and len(re.findall(r"<part\b", ms)) > 1
    except Exception:
        return len(info.get("teile", [])) > 1


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


FARB_RGB = {"weiss": "[0.95,0.94,0.9]", "weiß": "[0.95,0.94,0.9]", "schwarz": "[0.13,0.13,0.13]", "rot": "[0.8,0.1,0.1]", "dunkelrot": "[0.42,0.05,0.09]", "weinrot": "[0.45,0.07,0.13]",
            "blau": "[0.15,0.35,0.9]", "gruen": "[0.13,0.64,0.28]", "grün": "[0.13,0.64,0.28]", "gelb": "[0.96,0.77,0.1]",
            "orange": "[0.97,0.45,0.09]", "grau": "[0.56,0.56,0.58]", "silber": "[0.75,0.75,0.75]", "gold": "[0.83,0.63,0.09]",
            "creme": "[0.95,0.91,0.78]", "holz": "[0.73,0.54,0.31]", "braun": "[0.55,0.35,0.17]", "natur": "[0.94,0.9,0.82]",
            "lila": "[0.55,0.36,0.96]", "pink": "[0.93,0.28,0.6]", "türkis": "[0.08,0.72,0.65]", "tuerkis": "[0.08,0.72,0.65]"}


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


# Raue Oberfläche (Fuzzy Skin): (Stärke mm, Punktabstand mm). Richtwerte – „mittel“ ist die Slicer-Vorgabe 0,3/0,8;
# die Stärke bleibt unter der Linienbreite der Außenwand (0,42 mm). Am Creator 5 Pro noch nicht gedruckt.
RAU = {"fein": (0.1, 0.4), "mittel": (0.3, 0.8), "grob": (0.4, 1.0)}
RAU_WO = {"kontur": "external", "loecher": "all", "alle": "allwalls"}


def bild_in_gcode(gcode: Path, png: Path, groessen):
    """Vorschaubild für die Drucker-Anzeige in die .gcode schreiben (Orca erzeugt es ohne Bildschirm nicht).
    Format wie OrcaSlicer: Block '; thumbnail begin BxH LÄNGE' mit base64-PNG direkt nach dem Kopfblock."""
    try:
        import base64, io
        from PIL import Image
        txt = gcode.read_text(encoding="utf-8", errors="surrogateescape")
        marke = "; HEADER_BLOCK_END\n"
        if "thumbnail begin" in txt or marke not in txt or not png.exists():
            return False
        quelle = Image.open(png).convert("RGBA")
        block = ["; THUMBNAIL_BLOCK_START"]
        for b, h in groessen:
            bild = quelle.copy(); bild.thumbnail((b, h), Image.LANCZOS)
            feld = Image.new("RGBA", (b, h), (0, 0, 0, 0)); feld.paste(bild, ((b - bild.width) // 2, (h - bild.height) // 2))
            puffer = io.BytesIO(); feld.save(puffer, "PNG", optimize=True)
            b64 = base64.b64encode(puffer.getvalue()).decode()
            block += [";", f"; thumbnail begin {b}x{h} {len(b64)}"] + [f"; {b64[i:i + 78]}" for i in range(0, len(b64), 78)] + ["; thumbnail end"]
        block += ["; THUMBNAIL_BLOCK_END", ""]
        i = txt.index(marke) + len(marke)
        gcode.write_text(txt[:i] + "\n" + "\n".join(block) + txt[i:], encoding="utf-8", errors="surrogateescape")
        return True
    except Exception:
        return False


def bemalt_umformen(quelle: Path, ziel: Path, groesse=None, skala=None, matrix=None):
    """Bemalte 3MF skalieren/drehen, ohne die Bemalung anzufassen: nur die Eckpunkte werden neu geschrieben.
    groesse = größtes Maß in mm, skala = Faktor, matrix = 12 Zahlen (3×4, zeilenweise; nur der 3×3-Teil zählt,
    die Lage auf der Platte bestimmt der Slicer). Gibt (Maße vorher, Maße nachher) zurück."""
    import zipfile
    L = np.eye(3)
    if matrix is not None:
        L = np.array(matrix, dtype=float).reshape(3, 4)[:, :3]
    with zipfile.ZipFile(quelle) as z:
        dateien = {n: z.read(n) for n in z.namelist()}
    modelle = [n for n in dateien if n.lower().endswith(".model")]
    muster = re.compile(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"')
    alle = [np.array(muster.findall(dateien[n].decode("utf-8")), float) for n in modelle]
    V = np.vstack([v for v in alle if len(v)])
    vorher = np.ptp(V, axis=0)
    W_ = V @ L.T
    f = float(skala) if skala else 1.0
    if groesse:
        f = float(groesse) / float(np.ptp(W_, axis=0).max())
    L = L * f
    spiegel = np.linalg.det(L) < 0
    W_ = V @ L.T
    versatz = np.array([-(W_[:, 0].min() + W_[:, 0].max()) / 2, -(W_[:, 1].min() + W_[:, 1].max()) / 2, -W_[:, 2].min()])
    for n in modelle:
        x = dateien[n].decode("utf-8")
        if spiegel:
            if re.search(r'paint_color="[0-9A-F]{3,}"', x):
                raise SystemExit("Spiegeln geht bei fein bemalten 3MF nicht (die Bemalung hängt an der Dreiecks-Richtung).")
            x = re.sub(r'<triangle v1="(\d+)" v2="(\d+)"', r'<triangle v1="\2" v2="\1"', x)
        def neu(m):
            q = L @ np.array([float(m.group(1)), float(m.group(2)), float(m.group(3))]) + versatz
            return f'<vertex x="{q[0]:.4f}" y="{q[1]:.4f}" z="{q[2]:.4f}"'
        dateien[n] = muster.sub(neu, x).encode("utf-8")
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in dateien.items():
            z.writestr(n, d)
    return vorher, np.ptp(W_, axis=0)


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
    ap.add_argument("--teil", action="append", default=[],
                    help="Datei[:Material[:Slot]]  z. B. modelle/a.scad:PLA:1  (Slot 1–4 = Farbe/Kopf)")
    ap.add_argument("--farben", default="", help="Farbnamen je Slot für den Bericht, z. B. 'schwarz,rot'")
    ap.add_argument("--schicht", default=None)
    ap.add_argument("--stufe", default="Standard")
    ap.add_argument("--infill", type=int, default=15, help="Füllung in %%")
    ap.add_argument("--waende", type=int, default=None, help="Anzahl Wände")
    ap.add_argument("--stuetzen", choices=["aus", "auto", "baum"], default="aus")
    ap.add_argument("--brim", choices=["aus", "auto", "an"], default="auto")
    ap.add_argument("--anordnen", action="store_true", default=True)
    ap.add_argument("--zusammen", action="store_true",
                    help="Teile als EIN Objekt behandeln (mehrfarbiges Teil aus mehreren Dateien)")
    ap.add_argument("--rau", choices=sorted(RAU), default=None,
                    help="Raue Oberfläche (Fuzzy Skin) an den Seitenwänden: fein = Schichtlinien kaschieren, mittel = Stein/Griff, grob = starke Struktur")
    ap.add_argument("--rau-wo", choices=sorted(RAU_WO), default="kontur",
                    help="kontur = nur außen (Standard), loecher = außen und in Bohrungen, alle = alle Wände")
    ap.add_argument("--schoen", action="store_true",
                    help="Sichtteil-Paket für PLA (Lehren aus videos/pla-einstellungen-bastlwastl.html): 3 Wände innen-außen-innen, Arachne, je 5 Deck-/Bodenschichten, "
                         "Außenwand 45 / Innenwand 100 / erste Schicht 30 mm/s, Überhänge und Brücken höchstens 30 mm/s, Fahrwege meiden Wände, Naht hinten, Schrägnaht. Druckt deutlich länger.")
    ap.add_argument("--schraegnaht", action="store_true",
                    help="Schrägnaht (Scarf Joint) an der Außenwand: Anfang und Ende jeder Runde laufen schräg ineinander statt stumpf aneinander "
                         "(videos/z-naht-bastlwastl.html). Ist in --schoen enthalten. Nur an runden Konturen; Ecken behalten die normale Naht.")
    ap.add_argument("--detail", action="store_true",
                    help="Maximale Details (vor allem 0,25-mm-Düse): Arachne 70 %%/20 %%, resolution 0.008, eine Wand oben, Außenwand 30 / Kleinumfang 20 / Oberfläche 40 mm/s, "
                         "Außenwand-Beschleunigung 3000, 8 Deckschichten, Stützen nur ab Platte. Ersetzt die bisher von Hand angehängten --extra-Werte.")
    ap.add_argument("--stuetz-kopf", type=int, default=None,
                    help="Kopf (1–4) für die KONTAKTSCHICHT der Stützen aus anderem Material (z. B. PETG unter PLA): Abstand 0, 3 Kontaktlagen, "
                         "Muster verschränkt; der Stützkörper bleibt im Hauptmaterial (Flashforge-Wiki Creator 5). Bei PVA/BVOH auch den Körper: --stuetz-koerper")
    ap.add_argument("--stuetz-koerper", action="store_true", help="mit --stuetz-kopf: auch der Stützkörper aus diesem Kopf (lösliches PVA/BVOH, HIPS)")
    ap.add_argument("--bett", type=int, default=None, help="Betttemperatur für ALLE Filamente erzwingen (z. B. 65 bei PLA + PETG gemischt)")
    ap.add_argument("--wie", default=None, help="Auftragsordner: ALLE Slicer-Einstellungen aus dessen Projekt-3MF übernehmen (nur Material/Kopf/Farbe neu) – für „An meine Köpfe anpassen“")
    ap.add_argument("--extra", action="append", default=[], help="Slicer-Einstellung überschreiben: schluessel=wert (mehrfach)")
    ap.add_argument("--duese", default=None, help="Düsengröße in mm für ALLE Köpfe (c5pro: 0.25 | 0.4 | 0.6 | 0.8; Standard 0.4)")
    ap.add_argument("--duesen", default=None,
                    help="Düse je Kopf, z. B. '0.4,0.25,0.4,0.4' (gemischt; Schicht richtet sich nach der kleinsten Düse)")
    ap.add_argument("--groesse", type=float, default=None, help="nur mit --bemalt: größtes Maß in mm (Meshy liefert 50 mm)")
    ap.add_argument("--skala", type=float, default=None, help="nur mit --bemalt: Faktor, z. B. 2.4")
    ap.add_argument("--matrix", default=None, help="nur mit --bemalt: 12 Zahlen (3×4, zeilenweise) aus der Werkstatt")
    ap.add_argument("--gruppe", default="", help="Projekt-Kennung (z. B. schecter370): Aufträge mit gleicher Gruppe bilden in der App EIN Projekt")
    ap.add_argument("--gruppe-titel", default="", help="Anzeigename des Projekts (z. B. 'Schecter 370 mm')")
    ap.add_argument("--nr", type=int, default=0, help="Druck-Reihenfolge des Teils im Projekt (1, 2, 3 …)")
    ap.add_argument("--titel", default="", help="Anzeigename des Teils (z. B. 'Korpus')")
    ap.add_argument("--datei", default="", help="Dateiname für .gcode/.3mf ohne Endung (z. B. Schecter_370_Korpus); nur Buchstaben, Ziffern, _ und -")
    ap.add_argument("--bereich", default="", help="Karteikarte fürs Lager (lager/karten.json): musik | foto | werkstatt | deko | drucker – bei jedem NEUEN Projekt angeben")
    ap.add_argument("--schlagworte", default="", help="Karteikarte: Schlagworte mit Komma, z. B. 'Gitarre,Miniatur'")
    ap.add_argument("--quelle", default="", help="Link zum Original-Modell (MakerWorld, Printables …)")
    ap.add_argument("--ausgabe", default=None, help="Zielordner (Standard: auftraege/<datum>_<name>)")
    ap.add_argument("--bemalt", default=None,
                    help="3MF mit Farbe je Dreieck (paint_color, Köpfe 1–4) statt --teil, z. B. aus textur_farben.py")
    ap.add_argument("--materialien", default="", help="nur mit --bemalt: Material je Kopf, z. B. 'PLA,PLA-SILK,PLA,PLA' (Standard PLA)")
    a = ap.parse_args()
    if bool(a.teil) == bool(a.bemalt):
        raise SystemExit("Entweder --teil … (eine oder mehrere Dateien) oder --bemalt <datei.3mf> angeben.")
    bemalt = None; bemalt_masse = None
    if (a.groesse or a.skala or a.matrix) and not a.bemalt:
        raise SystemExit("--groesse/--skala/--matrix gelten nur zusammen mit --bemalt.")
    if a.bemalt:                          # Köpfe aus der Bemalung lesen (0 = Grundfarbe = Kopf 1)
        if a.groesse or a.skala or a.matrix:
            neu_ = Path(tempfile.mkdtemp(prefix="druckwerk_bemalt_")) / Path(a.bemalt).name
            mx = [float(x) for x in re.split(r"[,\s|]+", a.matrix.strip())] if a.matrix else None
            if mx is not None and len(mx) != 12:
                raise SystemExit("--matrix braucht genau 12 Zahlen.")
            bemalt_masse = bemalt_umformen(Path(a.bemalt), neu_, a.groesse, a.skala, mx)
            a.bemalt = str(neu_)
        sys.path.insert(0, str(WERKZEUG))
        from textur_farben import lese_3mf
        bV, bF, bS = lese_3mf(a.bemalt)
        bS = np.where(bS == 0, 1, bS)
        mats = [x.strip().upper() for x in a.materialien.split(",") if x.strip()]
        n_kopf = int(bS.max())
        bemalt = {"V": bV, "F": bF, "S": bS, "koepfe": n_kopf,
                  "mat": [mats[i] if i < len(mats) else (mats[0] if mats else "PLA") for i in range(n_kopf)]}
        a.teil = [f"{a.bemalt}:{bemalt['mat'][0]}:1"]

    cfg = json.loads((WURZEL / "drucker" / f"{a.drucker}.json").read_text(encoding="utf-8"))
    duesen_mix = None
    if a.wie and not a.duese and not a.duesen:    # --wie: Düse des alten Auftrags behalten (sonst rechnet „anpassen“ einen 0,25er-Auftrag mit 0,4)
        try:
            _alt = json.loads((Path(a.wie) / "auftrag.json").read_text(encoding="utf-8"))
            if str(_alt.get("duese_mm") or "0.4") != "0.4":
                a.duese = str(_alt["duese_mm"]); print(f"--wie: Düse {a.duese} mm übernommen")
        except (OSError, ValueError):
            pass
    if a.schicht is None and a.wie:               # --wie: Schichthöhe des alten Auftrags behalten
        try:
            a.schicht = str(json.loads((Path(a.wie) / "auftrag.json").read_text(encoding="utf-8")).get("schicht") or "") or None
        except (OSError, ValueError):
            pass
    if a.schicht is None:
        a.schicht = "0.20"
    if a.duesen:
        dl = [("%g" % float(x)) for x in a.duesen.split(",") if x.strip()]
        if a.duese:
            raise SystemExit("Entweder --duese (alle Köpfe gleich) oder --duesen (je Kopf) angeben.")
        if len(set(dl)) == 1:
            a.duese = dl[0]
        else:
            duesen_mix = (dl + ["0.4"] * 4)[:cfg["farben_max"]]
            for d_ in duesen_mix:
                if d_ != "0.4" and d_ not in cfg.get("duesen", {}):
                    raise SystemExit(f"Düse {d_} mm ist für {cfg['name']} nicht hinterlegt. Möglich: 0.4, {', '.join(cfg.get('duesen', {}))}")
            kleinste = min(duesen_mix, key=float)
            maschinen_je_duese = {d_: (cfg["duesen"][d_]["maschine"] if d_ != "0.4" else cfg["maschine"]) for d_ in set(duesen_mix)}
            if kleinste != "0.4":         # Schichthöhen und Prozessprofil der kleinsten Düse
                cfg = {**cfg, **{k: v for k, v in cfg["duesen"][kleinste].items() if k != "maschine"}}
    if a.duese and a.duese != "0.4":      # andere Düse = andere Maschinen-/Prozessprofile und Schichthöhen (drucker/*.json → "duesen")
        if a.duese not in cfg.get("duesen", {}):
            raise SystemExit(f"Düse {a.duese} mm ist für {cfg['name']} nicht hinterlegt. Möglich: 0.4, {', '.join(cfg.get('duesen', {}))}")
        cfg = {**cfg, **cfg["duesen"][a.duese]}
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
    if bemalt:
        for s_ in range(1, bemalt["koepfe"] + 1):
            belegt[s_] = bemalt["mat"][s_ - 1]
        slots = bemalt["koepfe"]
    if slots > cfg["farben_max"]:
        raise SystemExit(f"{cfg['name']} kann max. {cfg['farben_max']} Farben/Köpfe.")
    for s in range(1, slots + 1):
        belegt.setdefault(s, belegt.get(1) or next(iter(belegt.values())))   # auch wenn Kopf 1 unbenutzt ist
        if belegt[s] not in cfg["filamente"]:
            raise SystemExit(f"Material {belegt[s]} unbekannt für {cfg['name']}. Möglich: {list(cfg['filamente'])}")

    bett_auto = False
    if a.bett is None and any(m_.startswith("PLA") for m_ in belegt.values()) and any(m_.startswith("PETG") for m_ in belegt.values()):
        a.bett = 65; bett_auto = True          # PLA + PETG: sonst nimmt Orca 85 °C vom PETG – zu heiß für PLA-Flächen
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
    if duesen_mix:
        # Maschine: je Kopf die Werte aus dem Profil der jeweiligen Düse (unterscheiden sich nur in Düse und max. Schicht)
        for i_, d_ in enumerate(duesen_mix):
            m_ = aufloesen("machine", maschinen_je_duese[d_])
            for k_ in ("nozzle_diameter", "max_layer_height", "min_layer_height"):
                if isinstance(maschine.get(k_), list) and isinstance(m_.get(k_), list) and i_ < len(maschine[k_]) and i_ < len(m_[k_]):
                    maschine[k_][i_] = m_[k_][i_]
        # Prozess: Linienbreiten als Prozent der Düse, damit jeder Kopf passend breit druckt
        prozess["bridge_line_width"] = kleinste            # in mm (Prozent nimmt Orca hier nicht): darf keine Düse übersteigen
        for k_, v_ in list(prozess.items()):
            if k_.endswith("line_width") and k_ != "bridge_line_width" and isinstance(v_, str) and not v_.endswith("%"):
                try:
                    if float(v_) > 0:
                        pz = round(float(v_) / float(kleinste) * 100)
                        prozess[k_] = f"{pz}%"
                except ValueError:
                    pass
    if bemalt:   # Farbe nur als Schale (1,2 mm) statt keilförmig bis in den Kern – spart Farbfilament, sauberere Kanten
        prozess["mmu_segmented_region_max_width"] = "1.2"
    schoen_text = None
    if a.schoen:                          # langsam und sauber: Außenwand ungestört, Wände kühlen zwischen den Bahnen aus (videos/pla-einstellungen-bastlwastl.html)
        def hoechstens(k_, grenze):
            v_ = prozess.get(k_); w_ = v_[0] if isinstance(v_, list) and v_ else v_
            try:
                if float(w_) > grenze: prozess[k_] = str(grenze)
            except (TypeError, ValueError):
                prozess[k_] = str(grenze)
        if a.waende is None and int(float(prozess.get("wall_loops", 2))) < 3:
            prozess["wall_loops"] = "3"; a.waende = 3
        if int(float(prozess.get("wall_loops", 2))) >= 3: prozess["wall_sequence"] = "inner-outer-inner wall"
        prozess.update({"wall_generator": "arachne", "reduce_crossing_wall": "1", "seam_position": "back"})
        for k_ in ("top_shell_layers", "bottom_shell_layers"):
            if int(float(prozess.get(k_, 3))) < 5: prozess[k_] = "5"
        for k_, g_ in (("outer_wall_speed", 45), ("inner_wall_speed", 100), ("initial_layer_speed", 30), ("initial_layer_infill_speed", 100),
                       ("overhang_1_4_speed", 30), ("overhang_2_4_speed", 30), ("overhang_3_4_speed", 30), ("overhang_4_4_speed", 30), ("bridge_speed", 30)):
            hoechstens(k_, g_)
        schoen_text = (f"Sichtteil-Paket: {prozess['wall_loops']} Wände ({'innen-außen-innen' if prozess.get('wall_sequence') == 'inner-outer-inner wall' else 'Reihenfolge wie Profil'}), Arachne, "
                       f"{prozess['top_shell_layers']} Deck- und {prozess['bottom_shell_layers']} Bodenschichten, Außenwand ≤ 45, Innenwand ≤ 100, erste Schicht ≤ 30, Überhänge/Brücken ≤ 30 mm/s, "
                       "Fahrwege meiden Wände, Naht hinten. Gerechnet, am Gerät noch nicht bestätigt.")
    naht_text = None
    if a.schraegnaht or a.schoen:         # Werte aus dem Video: Start bei 10 % der Schichthöhe, Rampe 8 mm; „nur glatte Konturen“ ist Orca-Standard und bleibt an
        prozess.update({"seam_slope_type": "external", "seam_slope_start_height": "10%", "seam_slope_min_length": "8", "seam_slope_conditional": "1"})
        naht_text = "Schrägnaht an der Außenkontur (Start 10 % der Schichthöhe, Rampe 8 mm, nur an runden Konturen, nicht in der ersten Schicht). Gerechnet, am Gerät nicht bestätigt."
    rau_text = None
    if a.rau:                             # raue Oberfläche: äußere Wand „zittert“ (Lehren aus videos/fuzzy-skin-bastlwastl.html)
        staerke, abstand = RAU[a.rau]
        prozess.update({"fuzzy_skin": RAU_WO[a.rau_wo], "fuzzy_skin_thickness": str(staerke), "fuzzy_skin_point_distance": str(abstand),
                        "fuzzy_skin_first_layer": "0",                      # erste Schicht glatt lassen → Haftung
                        "wall_sequence": "inner wall/outer wall"})         # raue Außenwand zuletzt, sonst drückt sie sich nach innen durch
        if int(float(prozess.get("wall_loops", 2))) < 3:
            prozess["wall_loops"] = "3"; a.waende = 3                                  # die raue Bahn liegt schlecht auf → eine Wand mehr für die Festigkeit
        rau_text = (f"{a.rau} ({ {'kontur': 'nur Außenkontur', 'loecher': 'außen und Bohrungen', 'alle': 'alle Wände'}[a.rau_wo]}) – "
                    f"Stärke {staerke} mm, Punktabstand {abstand} mm, {prozess['wall_loops']} Wände, Außenwand zuletzt. "
                    f"Trägt je Seite bis {staerke} mm auf – Passflächen und Bohrungen werden entsprechend enger. Deckflächen bleiben glatt.")
    if a.wie:                                 # alle Prozess-Werte des alten Auftrags übernehmen (Zusätze, „schön“, feine Details …)
        alt_ps, _ = wie_einstellungen(Path(a.wie))
        fil_keys = set(aufloesen("filament", cfg["filamente"][belegt[1]]))
        n_ = 0
        for k_, v_ in alt_ps.items():
            if k_ in maschine or k_ in fil_keys or k_.startswith(WIE_NICHT):
                continue
            if prozess.get(k_) != v_:
                prozess[k_] = v_; n_ += 1
        prozess["compatible_printers"] = []
        print(f"--wie: {n_} Einstellungen aus {Path(a.wie).name} übernommen")
    hinweise = []                             # landen im BERICHT.md
    if cfg.get("kurz") == "c5pro":            # Flash Studio release_0817 (Hersteller, Recherche 23.11.2026): wartende Köpfe −100 °C, Kopfwechsel-Rückzug 2 mm
        prozess["standby_temperature_delta"] = "-100"; prozess["ooze_prevention"] = "1"; prozess["enable_prime_tower"] = "1"
        if isinstance(maschine.get("retract_length_toolchange"), list):
            maschine["retract_length_toolchange"] = ["2"] * len(maschine["retract_length_toolchange"])
    if a.detail:                              # feinste Details – Werte aus den Gitarren-Miniaturen + Flash-Studio-Feinstufe (Außenwand-Beschleunigung 3000)
        prozess.update({"wall_generator": "arachne", "min_bead_width": "70%", "min_feature_size": "20%", "resolution": "0.008", "only_one_wall_top": "1",
                        "outer_wall_speed": "30", "small_perimeter_speed": "20", "top_surface_speed": "40", "outer_wall_acceleration": "3000",
                        "top_shell_layers": "8", "support_on_build_plate_only": "1"})
        hinweise.append("Detail-Paket: Arachne (70 %/20 %), Auflösung 0,008, eine Wand oben, Außenwand 30 / Kleinumfang 20 / Oberfläche 40 mm/s, "
                        "Außenwand-Beschleunigung 3000, 8 Deckschichten, Stützen nur ab Platte.")
    if a.stuetz_kopf:
        if not 1 <= a.stuetz_kopf <= slots:
            raise SystemExit(f"--stuetz-kopf {a.stuetz_kopf}: Kopf ist in diesem Auftrag nicht belegt (1–{slots})")
        prozess.update({"enable_support": "1", "support_interface_filament": str(a.stuetz_kopf),
                        "support_filament": str(a.stuetz_kopf) if a.stuetz_koerper else "0",
                        "support_top_z_distance": "0", "support_bottom_z_distance": "0", "support_interface_top_layers": "3",
                        "support_interface_bottom_layers": "0", "support_interface_spacing": "0", "support_interface_pattern": "rectilinear_interlaced",
                        "independent_support_layer_height": "0"})
        if a.stuetzen == "aus":
            prozess["support_type"] = "normal(auto)"; a.stuetzen = "auto"
        sm = belegt[a.stuetz_kopf]
        if sm in ("PVA", "BVOH") and "tree" in prozess.get("support_type", ""):
            prozess["support_type"] = "normal(auto)"
        hinweise.append(f"Stützen-Kontaktschicht aus Kopf {a.stuetz_kopf} ({sm}), Abstand 0, 3 Kontaktlagen, verschränkt; Stützkörper "
                        f"{'ebenfalls aus Kopf ' + str(a.stuetz_kopf) if a.stuetz_koerper else 'im Hauptmaterial'}. "
                        "Flashforge: bei PLA/PETG/PVA/TPU Deckel ab, Tür auf, Kammerheizung aus (über 45 °C verstopft die Düse).")
    for ex in a.extra:                        # Zusätze zuletzt: gelten auch gegenüber --wie
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
        d_slot = (duesen_mix[s - 1] if duesen_mix and s - 1 < len(duesen_mix) else (a.duese or "0.4"))
        fs = Path(__file__).resolve().parent.parent / "drucker" / "fs_025" / f"{cfg['filamente'][belegt[s]]} 0.25 nozzle.json"
        if str(d_slot) == "0.25" and fs.exists():   # Hersteller-Profil nur für 0,25-mm-Düse (Flash Studio release_0817): 220 °C PLA, PA 0.1, max. 2,8 mm³/s
            for k_, v_ in json.loads(fs.read_text(encoding="utf-8")).items():
                if k_ not in ("inherits", "name", "setting_id", "filament_settings_id", "from", "instantiation", "version", "is_custom_defined", "compatible_printers"):
                    f[k_] = v_
            if f"Kopf {s}: 0,25-Profil" not in " ".join(hinweise):
                hinweise.append(f"Kopf {s}: Hersteller-Filamentprofil für 0,25-mm-Düse ({f['nozzle_temperature'][0]} °C, höchstens {f['filament_max_volumetric_speed'][0]} mm³/s).")
        if a.stuetz_kopf and s != a.stuetz_kopf and belegt[s].startswith("PLA") and belegt[a.stuetz_kopf].startswith("PETG"):
            t_ = max(225, int(float(f["nozzle_temperature"][0])))   # Flashforge-Wiki: PLA auf PETG-Kontaktschicht mit 225–230 °C
            f["nozzle_temperature"] = [str(t_)]; f["nozzle_temperature_initial_layer"] = [str(t_)]
        if a.bett:                        # gemischte Materialien: ein gemeinsamer Bettwert statt des höchsten
            for k in ("hot_plate_temp", "hot_plate_temp_initial_layer", "textured_plate_temp", "textured_plate_temp_initial_layer",
                      "cool_plate_temp", "cool_plate_temp_initial_layer", "eng_plate_temp", "eng_plate_temp_initial_layer"):
                f[k] = [str(a.bett)]
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
           "--allow-multicolor-oneplate", "--export-statistics",
           "--outputdir", str(tmp / "out"),
           "--export-3mf", "projekt.3mf"]   # Projektdatei (öffnen in Anycubic Slicer Next / OrcaSlicer)
    gemischt = len(set(belegt.values())) > 1
    if not bemalt:                       # bei bemalter 3MF bricht Orca mit --load-filament-ids ab (Code -2)
        cmd[cmd.index("--allow-multicolor-oneplate"):cmd.index("--allow-multicolor-oneplate")] = [
            "--load-filament-ids", ",".join(str(t[2]) for t in teile)]
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
               ("- Düsen: " + ", ".join(f"Kopf {i_ + 1}: {d_} mm" for i_, d_ in enumerate(duesen_mix[:slots])) + " – am Drucker genau so einbauen!"
                if duesen_mix else f"- Düse: {a.duese or '0.4'} mm (alle Köpfe)"),
               f"- Schichthöhe: {a.schicht} mm ({a.stufe})",
               f"- Füllung: {a.infill} %",
               f"- Wände: {a.waende or 'Profil-Standard'}",
               *([f"- {schoen_text}"] if schoen_text else []),
               *[f"- {h_}" for h_ in hinweise],
               *([f"- {naht_text}"] if naht_text else []),
               *([f"- Raue Oberfläche (Fuzzy Skin): {rau_text}"] if rau_text else []),
               f"- Stützen: {a.stuetzen}",
               f"- Brim: {a.brim}",
               f"- Düsentemperatur: {duese} °C, Bett: {bett} °C", "",
               "## Teile", ""]
    for t in teile:
        zeilen.append(f"- `{t[0].name}` → " + (f"bemalt, Köpfe 1–{slots}" if bemalt else f"Slot {t[2]} ({t[1]})"))
    if bemalt_masse:
        zeilen.append("- Größe geändert: " + " × ".join(f"{x:.1f}" for x in bemalt_masse[0]) + " mm → "
                      + " × ".join(f"{x:.1f}" for x in bemalt_masse[1]) + " mm")
    elif bemalt:
        zeilen.append("- Größe: " + " × ".join(f"{x:.1f}" for x in np.ptp(bemalt["V"], axis=0)) + " mm (unverändert; ändern mit --groesse)")
    # Kontrolle: Welche Köpfe benutzt die .gcode wirklich? (Tn = Kopf n+1)
    t_befehle = re.findall(r"^T(\d+)\s*$", txt, re.M)
    benutzt = sorted({int(x) + 1 for x in t_befehle})
    fehlt = [s_ for s_ in range(1, slots + 1) if s_ not in benutzt]
    wechsel = sum(1 for x, y in zip(t_befehle, t_befehle[1:]) if x != y)
    zeilen += ["", f"Kopfwechsel in der .gcode: {wechsel}, benutzte Köpfe: {', '.join(map(str, benutzt)) or '-'}"]
    if fehlt:
        zeilen.append(f"> ⚠ Kopf {', '.join(map(str, fehlt))} wird nicht benutzt – Farbe/Slot prüfen.")
    zeilen += ["", "## Am Drucker", ""] + [f"- {h}" for h in cfg["hinweise"]] + [
        "- Vor dem Start: Druckplatte sauber und leer, richtige Spulen in den Slots."]
    if bett_auto:
        zeilen += ["", "Bett für alle Köpfe auf 65 °C gesetzt (PLA + PETG gemischt; das PETG-Profil allein wollte mehr)."]
    if gemischt:
        zeilen += ["", "> ⚠ Unterschiedliche Materialien in einem Druck "
                   f"({', '.join(sorted(set(belegt.values())))}) – Haftung zwischen den Materialien "
                   "und Temperaturen prüfen."]
    # Daten für die App
    info_koepfe = {"kopfwechsel": wechsel, "koepfe_benutzt": benutzt}
    info = {**info_koepfe, "name": a.name, "drucker": cfg["kurz"], "drucker_name": cfg["name"], "datum": datum,
            "ordner": ziel.name, "gcode": gname, "zeit": zeit, "gramm": gramm, "meter": meter,
            "duese": duese, "bett": bett, "schicht": a.schicht, "stufe": a.stufe, "infill": a.infill,
            "duese_mm": a.duese or "0.4", **({"duesen_mm": duesen_mix[:slots]} if duesen_mix else {}), "waende": a.waende, **({"rau": a.rau} if a.rau else {}), "stuetzen": a.stuetzen, "brim": a.brim, "gemischt": gemischt, "zusammen": bool(a.zusammen and len(teile) > 1), **({"detail": True} if a.detail else {}), **({"stuetz_kopf": a.stuetz_kopf} if a.stuetz_kopf else {}),
            "slots": [{"slot": s_, "material": belegt[s_],
                       "farbe": farben[s_ - 1] if s_ - 1 < len(farben) else ""} for s_ in range(1, slots + 1)],
            "teile": [{"datei": Path(st).name, "slot": t[2]} for t, st in zip(teile, stls)],
            "quelle": a.quelle,
            "teile_app": [] if bemalt else [{"datei": app_stl(ziel / Path(st).name), "slot": t[2]} for t, st in zip(teile, stls)]}
    vorschau_teile = [(ziel / Path(st).name, t[2]) for t, st in zip(teile, stls)]
    if bemalt:
        # Die App zeigt Teile je Slot (STL): je Kopf die bemalte Oberfläche als offene Schale (nur zur Ansicht)
        import trimesh
        info["bemalt"] = Path(a.bemalt).name; vorschau_teile = []; info["teile"] = []; info["teile_app"] = []
        for s_ in range(1, slots + 1):
            sel = bemalt["F"][bemalt["S"] == s_]
            if not len(sel):
                continue
            p_ = ziel / f"{a.name}_kopf{s_}.stl"
            trimesh.Trimesh(bemalt["V"], sel, process=True).export(p_)
            info["teile"].append({"datei": p_.name, "slot": s_})
            info["teile_app"].append({"datei": app_stl(p_), "slot": s_})
            vorschau_teile.append((p_, s_))
    if vorschau_bild(ziel, [p_ for p_, _ in vorschau_teile],
                     [farben[s_ - 1] if s_ - 1 < len(farben) else "" for _, s_ in vorschau_teile]):
        info["vorschau"] = "vorschau.png"
        gr = [tuple(int(z_) for z_ in g_.split("/")[0].split("x")) for g_ in re.findall(r"\d+x\d+(?:/\w+)?", str(maschine.get("thumbnails", "") or ""))]
        if bild_in_gcode(ziel / gname, ziel / "vorschau.png", gr or [(140, 110)]):
            info["bild_im_gcode"] = True
    pj = ziel / f"{a.name}_{cfg['kurz']}.3mf"
    if pj.exists():
        info["projekt"] = pj.name
    # Projekt-Angaben (Gruppe, Titel, Reihenfolge, Dateiname): aus den Argumenten, sonst vom Vorgänger (gleicher Ordner oder gleicher Name im Lager)
    alt = {}
    try:
        alt = json.loads((ziel / "auftrag.json").read_text(encoding="utf-8"))
    except Exception:
        try:
            alt = next((x for x in json.loads((ziel.parent / "index.json").read_text(encoding="utf-8")) if x.get("name") == a.name and x.get("gruppe")), {})
        except Exception:
            alt = {}
    if alt.get("geaendert"):
        g_ = alt["geaendert"]
        print(f"\n!!! ACHTUNG: Tom hat dieses Teil am {g_.get('datum')} selbst in Flash Studio geändert: „{g_.get('notiz') or 'ohne Notiz'}“.\n"
              f"!!! Diese neue Fassung ersetzt seine Datei – seine Änderung in den Einstellungen nachziehen und ihm das sagen.\n")
        zeilen += ["", f"Hinweis: ersetzt die von Tom am {g_.get('datum')} geänderte Fassung (seine Notiz: {g_.get('notiz') or '–'})."]
    for k_, v_ in (("gruppe", a.gruppe), ("gruppe_titel", a.gruppe_titel), ("nr", a.nr), ("titel", a.titel), ("datei", a.datei)):
        v_ = v_ or alt.get(k_)
        if v_:
            info[k_] = v_
    if info.get("datei"):
        basis = re.sub(r"[^A-Za-z0-9_-]", "_", info["datei"]); info["datei"] = basis
        for feld, endung in (("gcode", ".gcode"), ("projekt", ".3mf")):
            if info.get(feld) and info[feld] != basis + endung and (ziel / info[feld]).exists():
                (ziel / info[feld]).replace(ziel / (basis + endung))
                zeilen = [z_.replace(info[feld], basis + endung) for z_ in zeilen]
                info[feld] = basis + endung
        gname = info["gcode"]
    (ziel / "auftrag.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    index_neu(ziel.parent)
    kp = WURZEL / "lager" / "karten.json"          # Karteikarte anlegen/ergänzen (nur fürs öffentliche Lager)
    if kp.exists() and ziel.parent.resolve() == (WURZEL / "auftraege").resolve():
        try:
            kd = json.loads(kp.read_text(encoding="utf-8")); key = info.get("gruppe") or a.name; karte = kd["karten"].get(key)
            if a.bereich or a.schlagworte or karte is None:
                karte = karte or {"bereich": "sonstiges", "stand": "gerechnet", "herkunft": "", "schlagworte": []}
                if a.bereich: karte["bereich"] = a.bereich
                if a.schlagworte: karte["schlagworte"] = [x.strip() for x in a.schlagworte.split(",") if x.strip()]
                kd["karten"][key] = karte; kp.write_text(json.dumps(kd, ensure_ascii=False, indent=1), encoding="utf-8")
                if karte["bereich"] == "sonstiges": print(f"Hinweis: Projekt „{key}“ ist im Lager noch unsortiert – --bereich angeben oder in lager/karten.json eintragen.")
        except Exception as ex:
            print("Karteikarte nicht geschrieben:", ex)
    (ziel / "BERICHT.md").write_text("\n".join(zeilen) + "\n", encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"OK  {ziel/gname}\n    Zeit {zeit} | {gramm} g")


if __name__ == "__main__":
    main()
