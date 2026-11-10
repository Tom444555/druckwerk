# druckwerk – Arbeitsanleitung für Claude

Ziel: Tom gibt einen Prompt („Halter für …, rot/schwarz, auf der Kobra“) → Claude liefert eine
**fertige USB-Druckdatei (.gcode)** plus **BERICHT.md** (Spulen, Einstellungen, Zeit, Gramm).
Tom muss nur noch die Datei auf den USB-Stick ziehen und am Drucker starten.

## Drucker (Tom wählt vorher!)
| Kürzel | Drucker | Stärken |
|---|---|---|
| `kobrax` | Anycubic Kobra X (offen, 4 Farben im Kopf, ACE Gen 2) | PLA/PETG/TPU bunt, günstig |
| `c5pro` | Flashforge Creator 5 Pro (geschlossen, 4 Köpfe, Kammer 65 °C) | ABS/ASA/CF, Mischmaterial, kein Spülabfall |

Hat Tom keinen Drucker genannt: **kurz fragen** (eine Frage, mit Empfehlung). Nicht selbst wählen.

## Ablauf
1. `bash werkzeug/setup.sh` (einmal pro Sitzung, ~2 Min.)
2. Modell beschaffen:
   - Technische Teile: OpenSCAD in `modelle/<name>.scad` (Maße als Variablen oben, Kommentare deutsch).
     Mehrfarbig = **eine .scad-Datei pro Farbe**, gleiche Koordinaten (siehe `test_wuerfel`/`test_buchstabe`).
   - Fertige Modelle (Figuren usw.): Tom schickt STL/3MF oder Link (Printables/Thingiverse) → in `modelle/`.
3. Druckbarkeit prüfen: liegt flach auf, Überhänge < 45° oder Stützen, Wandstärke ≥ 1,2 mm, passt in 256 mm.
4. Slicen:
   ```
   python3 werkzeug/druck.py --drucker kobrax --name <name> \
     --teil modelle/a.scad:PLA:1 --teil modelle/b.scad:PLA:2 --farben "schwarz,rot" \
     --zusammen --schicht 0.20 --infill 15 [--waende 3] [--stuetzen auto|baum] [--brim an|aus]
   ```
   - `Datei:Material:Slot` – Slot 1–4 = Spule (Kobra) bzw. Kopf (Creator). Materialien: siehe `drucker/*.json`.
   - `--zusammen` = mehrere Dateien bilden EIN mehrfarbiges Teil. Ohne = getrennte Teile, werden verteilt.
   - Schichten: Kobra 0.08–0.28, Creator 0.12/0.20/0.24.
5. Ergebnis (auch `auftrag.json`; `auftraege/index.json` wird automatisch neu gebaut → erscheint in der App) liegt in `auftraege/<datum>_<name>_<drucker>/`: `.gcode`, `BERICHT.md`, STL, `slicer.log`.
6. Committen + pushen. An Tom: `.gcode` per SendUserFile + Kurzfassung aus BERICHT.md (Spulen, Zeit, Gramm)
   + **App-Link** `https://tom444555.github.io/druckwerk/#hinzu=<ordner>` (speichert den Auftrag in seiner App; Pages braucht ~1 Min.).

## App (index.html, GitHub Pages)
- Live: https://tom444555.github.io/druckwerk/ – liest `drucker/*.json` und `auftraege/index.json`.
- Tabs: Aufträge (3D-Vorschau der STL, Spulen, Einstellungen, .gcode-Download), Neu (klickt den Prompt zusammen),
  Drucker, USB. iOS-Stil, hell/dunkel. Prompts aus der App beginnen mit `druckwerk:`.
- Aufträge sind wie die Ideen im Looper **pro Gerät gespeichert** (localStorage `druckwerk_meine`): neue Besucher
  sehen eine leere Liste. Tom speichert einen Auftrag über den Link `https://tom444555.github.io/druckwerk/#hinzu=<ordner>`
  (mehrere mit Komma) oder über „Aus dem Lager hinzufügen“. „Auftrag löschen“ entfernt ihn nur aus seiner Liste.
  Dateien endgültig aus dem Repo löschen (nur auf Wunsch): `git rm -r auftraege/<ordner>` + `druck.index_neu(Path('auftraege'))`.
- Original-Modell verlinken: `--quelle <URL>` (MakerWorld, Printables …) → Knopf „Original auf … öffnen“ im Auftrag.
- Nach Änderung an index.html: lokal mit Playwright (390×844) prüfen, dann pushen.

## Faustregeln Einstellungen
- Deko/Figur: 0.16–0.20, Infill 10–15 %, Baumstützen bei Überhängen.
- Funktionsteil/Halter: 0.20, Infill 25–40 %, `--waende 4`.
- Hitze/Draußen/Auto: ASA auf `c5pro`. ABS/ASA auf `kobrax` nur kleine Teile (offen → Verzug).
- TPU: langsam, nur ein Material pro Druck empfohlen.

## Technik-Notizen
- OrcaSlicer v2.5.0 CLI unter `xvfb-run`. Profile werden aus den Hersteller-JSON (inherits-Kette)
  aufgelöst; Werte außerhalb des erlaubten Bereichs korrigiert das Skript selbst (steht in slicer.log).
- Flashforge-Filamente: `filament_is_support` fehlt im Profil → Skript ergänzt es.
- Vorschaubild (Thumbnail) wird headless noch nicht erzeugt → Drucker zeigt kein Bild. Offen.
- Später (Stufe 2): Senden per LAN über Heim-Brücke (Kobra X: MQTT, grunna/ha-anycubic-kobra-x-lan;
  Flashforge: HTTP 8898, Parallel-7/flashforge-api-docs). Erst nach Kauf am echten Gerät testen.
