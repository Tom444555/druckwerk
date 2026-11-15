# Modellqualität – Nachschlagen für den Assistenten (Stand 15.11.2026)

Ziel: technische Teile sehen aus wie gekauft und passen beim ersten Druck. Werkzeuge: `werkzeug/profi.py` (Regeln als Code),
`werkzeug/pruefen.py` (Druckbarkeit), `werkzeug/ansichten.py` (Prüfbild), `werkzeug/cad.py` (bauen + STL/STEP).
Vorzeige-Teile: `modelle/profi/gitarrenhalter.py`, `zahnradpaar.py`, `dose.py`. Quellen-Details: `wissen/recherche_modellqualitaet.md` Abschn. 5.

## Regeln (Creator 5 Pro, Düse 0,4) – Konstanten in profi.py

| Thema | Zahl | Konstante | Quelle |
|---|---|---|---|
| Linienbreite / Wände | 0,45 mm; Wand = n × 0,45 (2 → 0,9 · 3 → 1,35 · 4 → 1,8 · 5 → 2,25) | `LINIE`, `WAND[n]`, `wand(mm)` | Prusa |
| Mindestwand | < 0,8 mm Fehler, < 1,2 mm Hinweis | `WAND_MIN`, `WAND_GUT` | Stratasys (4 × Schicht), CLAUDE.md |
| Kleinstes Detail | 0,45 mm (schmaler lässt der Slicer weg) | `DETAIL_MIN` | Prusa |
| Spiel je Seite | Presssitz 0 · stramm 0,2 · normal (Schnapp/Gewinde) 0,3 · locker (Drehen, Print-in-Place) 0,4 | `SPIEL[...]` | Core77, Prusa; Presssitz Hausregel |
| Lochaufmaß | +0,2 mm auf Ø (Löcher drucken zu klein) | `LOCH_AUFMASS` | Hubs (Zahl Hausregel) |
| Überhang | ≤ 45° stützfrei | `UEBERHANG_MAX` | Hubs, Prusa |
| Brücke | ≤ 5 mm sauber | `BRUECKE_MAX` | Hubs |
| Bettkante | 45°-Fase 0,6 mm, **nie Rundung** (Rundung unten = Überhang) | `FASE_UNTEN`, `fase_unten()` | Prusa, Hubs |
| Innenradius | ≥ 0,2 mm (Düsenradius); Optik außen 1 / groß 3 mm | `R_INNEN_MIN`, `R_KANTE`, `R_GROSS` | Hubs; Optik Hausregel |
| Schrift | Strich ≥ 0,8 mm, Tiefe 0,6 mm (3 Schichten); DejaVu Sans Bold ab ~6,5 mm Höhe | `schrift()` prüft selbst | Stratasys (fett, ≥ 24 pt) |
| Einschmelzmutter | Ruthex M3 Ø4,0×5,7 · M4 Ø5,6×8,1 · M5 Ø6,4×9,5, Loch +1 mm tief, Wand ≥ 2 mm | `EINSATZ`, `einschmelz_loch()` | CNC Kitchen, Stratasys |
| Schnapphaken | Dehnung 1,5·d·y/L² ≤ PLA 2 % / PETG·ABS·ASA 3 % (in Z × 0,5), liegend drucken | `DEHNUNG_ZUL` (Richtwerte) | Core77 |
| Last | Hauptspannung in den Schichten (XY); Z ist die schwache Richtung | – | Hubs, Prusa |
| Stifte | Ø < 5 mm schwach → Ø ≥ 6–8 oder Metallstift | – | Hubs |

Alle Spiele/Aufmaße sind **rechnerisch**; nach Kalibrier-Teil 4 (Passung) anpassen und hier + in `wissen/c5pro.json` als „Gerät“ eintragen.

## Helfer in profi.py (alle mit Selbsttest: `python3 werkzeug/profi.py` → 21/21, ~30 s)

`sicher_runden(teil, kanten, r)` (fällt auf kleinere Radien/Einzelkanten zurück, meldet in `PROTOKOLL`) · `sicher_fasen` · `fase_unten` ·
`kanten_unten/kanten_oben_aussen/kanten_bei` · `senkloch` / `durchgangsloch` (waagrecht automatisch Tropfenform) · `einschmelz_loch` ·
`loch_waagrecht` + `tropfen_profil` · `rippe` · `raendel_zylinder` · `waben` (Rechteck oder Kreis) · `schrift` + `strich_verlust` ·
`einlegen` (Mehrfarb-Einlage, überlappungsfrei) · `schnapphaken` · `schwalbenschwanz` · `scharnier` (Print-in-Place, Kegelzapfen 45°) ·
`teilen` (Schnitt + Passstiftlöcher) · `gewinde_bolzen/gewinde_innen` (ISO 60°, bd_warehouse) · `druckgewinde` (45°-Flanken, stützfrei, für Deckel) ·
`normschraube` (bd_warehouse, zum Anprobieren) · `zahnradpaar` (py_gearworks, Evolvente, Flankenspiel + Achszugabe).

## Wann was?

- **OpenSCAD + `modelle/baukasten/`**: einfache, kantige Teile, schnelle Varianten, keine STEP nötig.
- **build123d + `profi.py`** (über `cad.py`): sobald Rundungen/Fasen, Gewinde, Zahnräder, Schrift-Einlagen, STEP oder „Produkt-Optik“ gefragt sind.
- Organische Formen/Reliefs: weiter `baum_relief.py` / `bild_relief.py` (CLAUDE.md).

## Prüfschleife (Pflicht vor dem Slicen, höchstens 3 Runden)

1. **Bauen:** `python3 werkzeug/cad.py modelle/<x>.py --name <x> --ziel /tmp/<x> --pruefen --bild /tmp/<x>.png [--fein 0.02] [--arg zusammenbau=1]`
2. **pruefen.py** muss **0 Fehler** melden (Exit 0). Hinweise lesen und bewusst entscheiden.
3. **ansichten.py-Bild selbst ansehen** (Read auf die PNG): wirkt es gekauft? Kanten gerundet, Bettkanten gefast, nichts schwebt, Schrift lesbar?
4. Korrigieren → zurück zu 1. Erst danach `druck.py`. Bewegliche Teile zusätzlich im Zusammenbau prüfen (jedes Teil eigener Farbschlüssel
   → `pruefen.py` rechnet paarweise Schnittvolumen = 0 und zeigt Berührung).

## Typische Fehlerbilder → Abhilfe

| Bild / Meldung | Ursache | Abhilfe |
|---|---|---|
| Fillet schlägt fehl nach Vereinigung | viele Kanten, tangentiale Flächen | Rundungen **vor** der Vereinigung je Teil oder als 2D-`fillet` in der Skizze; `sicher_runden`; Kehlen als Drehkörper (Zylinder − Torus) |
| Überhang an Bettkante (pruefen: „Überhänge … bei z≈1“) | Rundung unten / gerundete Ecken einer stehenden Platte | unten nur Fase; stehende Platten nur oben runden |
| Überhang an waagrechtem Loch | runder Querschnitt | `senkloch(..., richtung waagrecht)` / `loch_waagrecht` → Tropfen mit Dach |
| „nicht wasserdicht“ trotz gültigem B-Rep | alte Vernetzung im Körper | `cad.stl_export` vernetzt frisch (BRepTools.Clean) und entfernt Einzeldreieck-Splitter |
| Lose Splitter / dünner Keil | Freischnitt mit Zylinder erzeugt spitze Keile; Bauteil ragt über Zahnfuß/Rand | Freiräume als Quader; Anbauteile innerhalb tragender Flächen halten |
| Schnittvolumen ≠ 0 bei Gewinden | Phase von Bolzen und Mutter | `gewinde_innen`/`druckgewinde(aussen=False)` sind schon um ½ Steigung versetzt; gleiche Startlage wählen |
| Schrift „zu fein“ | Strich < 0,8 mm | größer (≥ 6,5 mm) oder fetter; Sonderzeichen (·, :) sparsam |
| 2 getrennte Körper (Hinweis) | gewollt (Buchstaben, Deckel neben Dose) oder Fehlerrest | im Bild prüfen; ungewollte Reste entfernen |
| Wand < 1,2 mm an Gravur | Steg zwischen zwei Prägungen | unkritisch, wenn dahinter Material ist |

## Aufrufbeispiele

```
python3 werkzeug/profi.py                                    # Selbsttest aller Helfer
python3 werkzeug/pruefen.py /tmp/gh/gitarrenhalter_schwarz.stl /tmp/gh/gitarrenhalter_rot.stl [--json]
python3 werkzeug/ansichten.py /tmp/dose/dose_zb_*.stl --farben schwarz,schwarz,gold --schnitt y --bei 0 --aus /tmp/dose.png
python3 werkzeug/cad.py modelle/profi/zahnradpaar.py --name zahnradpaar --ziel /tmp/zr --arg zusammenbau=1 --pruefen --ohne-step
```
Laufzeiten (2 Kerne): Prüfung 300.000 Dreiecke ≈ 5 s, Prüfbild 2–6 s, Bauen 15 s (Halter) bis 65 s (Dose mit Gewinde + 77 Waben).
Große STL/STEP/PNG nach `/tmp`, nur Skripte einchecken. Benötigt: `bd_warehouse py_gearworks pyvista embreex rtree` (siehe setup.sh).
