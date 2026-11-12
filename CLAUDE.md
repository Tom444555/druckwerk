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

## Bibliothek & Werkstatt (werkstatt.js, seit 11.11.2026)
- Tab **Bibliothek**: alle Modelle aus `auftraege/index.json` (je Name einmal) + „Meine Modelle“ (IndexedDB `druckwerk/modelle`
  auf dem Gerät; Import STL/3MF/OBJ). Tippen öffnet die **Werkstatt** (`werkstatt:l:<ordner>` bzw. `werkstatt:e:<id>`).
- Werkstatt: skalieren (% oder mm, proportional/frei), drehen (X/Y/Z ±15/±90°), auf angetippte Fläche legen, spiegeln,
  4 Spulenfarben, Teil → Spule, Teile aus-/entfernen, Rückgängig. Alle Änderungen werden direkt in die Geometrie gerechnet
  und das Modell danach mittig auf die Platte gesetzt.
- Export: 3MF (Teile als eine Baugruppe, Spule je Teil in `Metadata/model_settings.config` – in OrcaSlicer 2.5 getestet,
  slict mehrfarbig), STL gesamt, STL einzeln (ZIP), OBJ+MTL (ZIP), GLB.
- **Auftrag aus der Werkstatt** („An Claude zum Slicen schicken“): Prompt nennt Lager-Ordner, Änderungsliste und eine
  3×4-Matrix (Zeilen mit ` | ` getrennt). Diese Matrix mit trimesh auf **alle** Original-STL des Ordners anwenden
  (`mesh.apply_transform`, 4. Zeile 0 0 0 1; bei negativer Determinante dreht trimesh die Flächen selbst), dann normal slicen.
  Bei eigenen Modellen hängt Tom die exportierte 3MF an.
- **Slicen aus der App (Stufe 2, seit 11.11.2026):** Werkstatt → „Slicen“ → Einstellungen (Voreinstellung, Schicht, Wände,
  Füllung/Muster, Deck-/Bodenschichten, Stützen, Brim, Naht, Bügeln, Material je Spule) → App legt per GitHub-API
  `eingang/<id>/auftrag.json` ab (Lager-Modelle: nur Pfade + Matrix; eigene: STL-Teile dazu). Workflow
  `.github/workflows/slicen.yml` startet `werkzeug/eingang.py` → `druck.py` → Ergebnis in `auftraege/`, Rückmeldung in
  `status/<id>.json`, App übernimmt den Auftrag automatisch (~1–3 Min.). Token (Fine-grained, Contents RW) liegt nur
  im Gerät (localStorage `druckwerk_token`). Erlaubte Extra-Schlüssel stehen in `EXTRA_OK` (eingang.py) – dort erweitern.
- Schichtvorschau: `schichten.js` (Knopf „Schichten ansehen“ im Auftrag) liest die .gcode und zeichnet jede Schicht.
- Noch offen: 1b schneiden/zusammensetzen/Text · 3 Filamentlager + Druckprotokoll · 4 „Mit Claude bauen“.

## Organische/feine Modelle (Erfahrung Gitarren-Reihe, 11.–12.11.2026)
- **Erst Bild, dann Druckdatei:** bei Deko/Entwürfen zuerst eine schnelle Vorschau schicken (Sekunden), Tom entscheidet, dann slicen (bis 10 Min.).
  Bei Geschmacksfragen 3–4 Varianten nebeneinander rechnen und die beste nehmen. Toms Fotos = Stilvorlage, kein 1:1-Nachbau fremder Motive.
- **Relief statt OpenSCAD** für Bäume, Blätter, Borke, Leder usw.: Höhenfeld in numpy → wasserdichtes Netz (manifold3d, bei y=0 abschneiden),
  eine Höhenkarte je Farbe, Farben überlappen nie. Vorlage: `werkzeug/baum_relief.py` (`--saat N`, `--nur-bild x.png`). Liegt flach auf dem Bett → keine Überhänge.
- **Fremde Ein-Körper-STL mehrfarbig machen:** `werkzeug/gitarre_farben.py` (Schnitte per Boolean, Splitter mit decompose filtern); lose Teile: `werkzeug/lose_teile.py`.
- **Passung zweier Teile** (z. B. Gitarre im Ständer) immer per Schnittvolumen prüfen (manifold `a ^ b`, soll 0 mm³ sein) – Maße der Gabel stehen in `baum_relief.py` oben.
- **Feine Stege < 0,45 mm:** `--extra wall_generator=arachne --extra min_bead_width=70% --extra min_feature_size=20%`, sonst lässt der Slicer sie weg.
  Stützen: `auto` (Baumstützen gaben Slicer-Fehler). Schicht 0.12 für feine Reliefs.
- **Dateigröße:** GitHub lehnt Dateien > 100 MB ab. Sehr feine Modelle: `--extra resolution=0.06` (G-Code wird ~20 % kleiner), Netze ≤ ~500.000 Dreiecke je Farbe.
  Große erzeugte STL in `modelle/` nicht einchecken (.gitignore), wenn ein Skript sie neu bauen kann. Alte Stände eines Auftrags ersetzen, nicht sammeln.
- **Farben:** Tom mag die Verstärker-Farben schwarz / gold / rot / weiß; Farben nur tauschen = gleiche STL, andere Slots, neu slicen (kein Neubau).
- **Git:** ein zweiter Chat schreibt ins selbe Repo. Reihenfolge: `git add -A && git commit` → `git fetch` → `git rebase origin/main` → **Status prüfen** (Konfliktmarker in
  UEBERGABE.md entfernen, beide Teile behalten) → `druck.index_neu(Path('auftraege'))` → commit → `git push origin HEAD:main`. Nie mitten im Rebase `git add -A`.

## Faustregeln Einstellungen
- Deko/Figur: 0.16–0.20, Infill 10–15 %, Baumstützen bei Überhängen.
- Funktionsteil/Halter: 0.20, Infill 25–40 %, `--waende 4`.
- Hitze/Draußen/Auto: ASA auf `c5pro`. ABS/ASA auf `kobrax` nur kleine Teile (offen → Verzug).
- TPU: langsam, nur ein Material pro Druck empfohlen.

## Technik-Notizen
- OrcaSlicer v2.5.0 CLI unter `xvfb-run`. Profile werden aus den Hersteller-JSON (inherits-Kette)
  aufgelöst; Werte außerhalb des erlaubten Bereichs korrigiert das Skript selbst (steht in slicer.log).
- Flashforge-Filamente: `filament_is_support` fehlt im Profil → Skript ergänzt es.
- **Druckplatte** (`platte` in drucker/*.json, Standard „Textured PEI Plate“) setzt `curr_bed_type` – sonst nimmt Orca
  „Cool Plate“ und heizt PLA nur auf 35 °C (Fehler vom 10.11.2026, Druck misslungen). Nach dem Slicen prüfen:
  Kobra `G9111 bedTemp=60`, Creator `M140 S55/60`.
- Jeder Auftrag bekommt zusätzlich `<name>_<drucker>.3mf` (Projekt mit Einstellungen, Feld `projekt`) – App-Knopf „3MF-Projekt laden“.
- `druck.py` rendert automatisch `vorschau.png` (OpenSCAD, Farben je Spule) → App zeigt es sofort, 3D lädt dahinter nach.
- Große Netze bekommen eine leichte Kopie `*.app.stl` (~60.000 Dreiecke, Feld `teile_app`) nur für die 3D-Ansicht am Handy.
- Drucker-Thumbnail im .gcode wird headless noch nicht erzeugt → Drucker zeigt kein Bild. Offen.
- Später (Stufe 2): Senden per LAN über Heim-Brücke (Kobra X: MQTT, grunna/ha-anycubic-kobra-x-lan;
  Flashforge: HTTP 8898, Parallel-7/flashforge-api-docs). Erst nach Kauf am echten Gerät testen.
