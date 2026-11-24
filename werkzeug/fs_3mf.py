#!/usr/bin/env python3
"""Projekt-3MF so herrichten, dass Flash Studio (und OrcaSlicer) UNSERE Einstellungen übernimmt.

Ursache (Quelltext FlashForge/Orca-Flashforge, PresetBundle::load_config_file_config → PresetCollection::load_external_preset →
DynamicPrintConfig::update_non_diff_values_to_base_config): Heißt ein Profil in der 3MF wie ein System-Profil des Programms
(„0.08mm Standard @FF C5 0.25 nozzle“), setzt das Programm beim Öffnen ALLE Werte auf die des System-Profils zurück – außer denen,
die in `different_settings_to_system` aufgezählt sind. Die Orca-CLI schreibt dieses Feld leer → Stützen, Detailwerte, Wände usw. gingen verloren
(Toms Befund 19.11. und 24.11.2026: Warnung „floating regions“, 5 h 43 statt 7 h 17).

Was dieses Werkzeug an der 3MF ändert:
  1. `different_settings_to_system` = [Prozess-Schlüssel ; je Kopf Filament-Schlüssel ; Drucker leer] – unsere Prozess- und Filamentwerte gelten,
     das Druckerprofil bleibt das von Flash Studio (aktuelle Start-/Wechsel-Befehle des Herstellers, Senden an den Drucker).
  2. Eingebettete .gcode und der Verweis darauf fliegen heraus: die Datei öffnet als normales Projekt im Reiter „Prepare“ und wird dort neu geschnitten.

Aufruf:  python3 werkzeug/fs_3mf.py auftraege/<ordner> [...]      (druck.py ruft herrichten() nach jedem Slicen selbst auf)
"""
import json, re, shutil, sys, zipfile
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
NICHT = ("inherits", "compatible_printers", "compatible_printers_condition", "compatible_prints", "compatible_prints_condition", "print_settings_id",
         "filament_settings_id", "printer_settings_id", "setting_id", "filament_id", "name", "from", "version", "is_custom_defined")
WEG = re.compile(r"^Metadata/plate_\d+\.gcode(\.md5)?$")


def herrichten(pfad: Path) -> dict:
    """Schreibt die 3MF neu (gleicher Name). Rückgabe: kleine Statistik fürs Protokoll."""
    schl = json.loads((HIER / "drucker" / "fs_schluessel.json").read_text(encoding="utf-8"))
    tmp = pfad.with_suffix(".3mf.neu"); info = {"datei": pfad.name}
    with zipfile.ZipFile(pfad) as alt, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as neu:
        for e in alt.infolist():
            if WEG.match(e.filename):
                info["gcode_entfernt"] = info.get("gcode_entfernt", 0) + e.file_size; continue
            if e.filename == "Metadata/project_settings.config":
                c = json.loads(alt.read(e).decode("utf-8"))
                n = len(c.get("filament_settings_id") or c.get("filament_type") or [1])
                pk = [k for k in schl["prozess"] if k in c and k not in NICHT]
                fk = [k for k in schl["filament"] if k in c and k not in NICHT]
                c["different_settings_to_system"] = [";".join(pk)] + [";".join(fk)] * n + [""]
                info.update(prozess=len(pk), filament=len(fk), koepfe=n)
                neu.writestr(e.filename, json.dumps(c, indent=4, ensure_ascii=False)); continue
            if e.filename == "Metadata/model_settings.config":
                t = alt.read(e).decode("utf-8")
                t = re.sub(r'[ \t]*<metadata key="gcode_file" value="[^"]*"/>\r?\n', "", t)
                neu.writestr(e.filename, t); continue
            if e.filename in ("Metadata/slice_info.config", "Metadata/_rels/model_settings.config.rels") or e.filename.endswith(".statistics.json"):
                continue                                    # Schnitt-Ergebnis gehört zur entfernten .gcode
            zi = zipfile.ZipInfo(e.filename, date_time=e.date_time); zi.compress_type = zipfile.ZIP_DEFLATED
            with alt.open(e) as q, neu.open(zi, "w", force_zip64=True) as z:
                shutil.copyfileobj(q, z, 1 << 20)
    tmp.replace(pfad); info["groesse_mb"] = round(pfad.stat().st_size / 1e6, 1)
    return info


if __name__ == "__main__":
    for o in sys.argv[1:]:
        o = Path(o)
        for pj in ([o] if o.suffix == ".3mf" else sorted(o.glob("*.3mf"))):
            print(herrichten(pj))
