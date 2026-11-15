# KI-Modelle drucken (Rodin, TRELLIS, Hunyuan, Meshy …)

Ablauf: **GLB bekommen → `ki_rohling.py` → Vorschau zeigen → `textur_farben.py` → slicen → (optional) `foto.py`**.
Alles läuft in der Sandbox ohne GPU. Testordner immer unter `/tmp`, erst das fertige Ergebnis nach `auftraege/`.

## 1. Rohling: reparieren, aufstellen, Größe
```
python3 werkzeug/ki_rohling.py figur.glb --ziel-mm 80 --aus /tmp/figur
```
- Liest GLB/GLTF/OBJ/STL/PLY (alle Teile der Szene). GLB/OBJ gelten als Y-oben, STL als Z-oben (`--oben` ändert das).
- Macht wasserdicht über eine Voxel-Hülle (schließt Löcher, schluckt Innenflächen und Selbstschnitte) und zieht die Oberfläche
  danach zurück auf das Original → Details bleiben bis ca. 0,2 mm. Lose Splitter fliegen raus.
- Steht das Modell bis 25° schief, wird es gerade gestellt (`--aufrichten aus` / `--drehen 0,0,90` zum Korrigieren).
- `--boden auto` schneidet unten plan ab, bis die Standfläche reicht **und** der Schwerpunkt darüber liegt; sonst Sockel.
  Alternativ `schnitt:<mm>`, `sockel` (2,4 mm, 3 mm Rand), `aus`. `--ziel-mm` gilt für die Endhöhe inkl. Sockel (`--mass max` = längste Seite).
- Optional: `--glatt 1..3` (Taubin, gegen KI-Rauschen), `--hohl 2` (Hohlraum mit 2 mm Wand), `--verdicken` (Stellen < `--duenn` 0,8 mm aufdicken),
  `--max-dreiecke` (400.000).
- Ergebnis: `<name>.stl`, `<name>_farbig.glb` (nur wenn das Original Farbe hat), `info.json` (Maße, dicht, Standfläche, steht stabil,
  Überhang-Anteil, dünne Stellen, Warnungen), `vorschau.png` (zwei Ansichten, mit Farbe). **Vorschau Tom zeigen, bevor gefärbt/gesliced wird.**
- Dauer: ~50 s für 400.000 Dreiecke / 80 mm.

## 2. Farben: Textur → höchstens 4 Köpfe
```
python3 werkzeug/textur_farben.py /tmp/figur/figur_farbig.glb --farben "schwarz,gold,rot,weiss" --nur-bild /tmp/v.png   # erst ansehen
python3 werkzeug/textur_farben.py /tmp/figur/figur_farbig.glb --farben "schwarz,gold,rot,weiss" --aus /tmp/figur
```
- Palette in Slot-Reihenfolge, Werte anpassbar (`gold=#d4a017`) oder `--auto 3` (k-Means im Lab-Raum; Namen sind nur Vorschläge).
- Bereinigt: Inseln < `--min-flaeche` 1 mm², Stege < `--min-breite` 0,8 mm, Kanten geglättet (`--glaetten`). Feinheit: `--kante` 0,4 mm.
- Eingebrannte Schatten in der Textur machen Weiß grau → landet bei Schwarz. Dann `--hell 0.6` (Helligkeit zählt weniger) oder Farbwert anpassen.
- Gibt beide Wege aus und druckt die fertigen `druck.py`-Aufrufe (auch in `farben.json`). Dauer ~30 s (A) + ~70 s (B).

### Welcher Farbweg?
| | **A: bemalte 3MF** (`--weg A`) | **B: Farbkörper** (`--weg B`) |
|---|---|---|
| Datei | ein Körper, Farbe je Dreieck (`paint_color`) | je Farbe ein STL (Schale 1,2 mm, Kern = häufigste Farbe) |
| Slicen | `druck.py … --bemalt x_bemalt.3mf --farben "…"` | `druck.py … --teil a.stl:PLA:1 … --zusammen` |
| Vorteil | schneller, kleiner, Farbkanten exakt wie gemalt, in OrcaSlicer nachmalbar | klassisch, jede Farbe einzeln prüf-/tauschbar, App-Werkstatt kann damit arbeiten |
| Nachteil | App/Werkstatt sieht nur Oberflächen-Schalen je Kopf (zum Ansehen) | Kanten auf Voxel-Raster (~0,2 mm), mehr Dreiecke |
| Standard | **erste Wahl für Figuren** | wenn die Werkstatt den Auftrag weiter bearbeiten soll |

Beide sind mit OrcaSlicer 2.5 CLI geprüft (Testfigur 80 mm, 4 Farben, alle 4 Köpfe benutzt, ~740–760 Kopfwechsel).
Bei `--bemalt` setzt druck.py `mmu_segmented_region_max_width=1.2` (Farbe nur als 1,2-mm-Schale statt keilförmig bis zum Kern; überschreibbar mit `--extra`).
Material je Kopf bei A: `--materialien "PLA,PLA-SILK,PLA,PLA"`.

## 3. Foto zum Schluss (optional)
```
python3 werkzeug/foto.py /tmp/figur/figur_1_schwarz.stl /tmp/figur/figur_2_gold.stl … --farben schwarz,gold,… --aus foto.png
```
Cycles auf der CPU, Studio-Licht, Boden mit Schatten, gold/silber als Seidenglanz. ~55 s bei 48 Samples/900 px, ~15 s bei 24/600.
Geht auch mit den `*_kopf<n>.stl` eines bemalten Auftrags. Braucht `pip install --break-system-packages bpy` (~430 MB, nur Python 3.13).

## Grenzen
- **Nicht maßhaltig:** KI-Modelle sind Deko. Passungen, Schraublöcher, Maße → Baukasten/CAD.
- **Dünne Stellen:** unter 0,8 mm (Finger, Haare, Schwerter) brechen oder fehlen → `info.json` lesen, größer drucken oder `--verdicken`.
- **Überhänge:** Figuren haben fast immer welche (`ueberhang_anteil`) → `--stuetzen auto`; Baumstützen gaben bei feinen Reliefs Slicer-Fehler.
- **Farbe:** Schatten/Glanzlichter der Textur werden mitgefärbt; Details unter ~1 mm (Pupillen-Glanzpunkte) fallen weg.
- **Aufrichten** ist eine Heuristik: bei absichtlich schräger Pose `--aufrichten aus`.
- Bisher nur mit einer selbst gebauten Testfigur geprüft (Pinguin mit Schal, Löcher, Innenkugel, Splitter, 13° schief), nicht mit einem echten KI-Modell.

## Tipps für Eingabebilder (größter Hebel)
- Ein Objekt, freigestellt oder vor ruhigem Hintergrund, füllt > 50 % des Bildes, gleichmäßiges Licht ohne harte Schatten.
- Kompakte Pose: Arme am Körper, keine dünnen abstehenden Teile, breite Füße/Standfläche.
- Wenige, klare Farbflächen (passend zu 4 Filamenten) statt Verläufe und Muster; bei Rodin/Hunyuan „PBR/Albedo“-Textur wählen (ohne eingebranntes Licht).
- Mehrere Ansichten (vorn/seitlich/hinten), wenn der Generator das kann.

---

# Lehren aus zwei Bastlwastl-Videos (Auswertung 15.11.2026)

## Video 1 – Eigene STL-Dateien mit KI (youtube.com/watch?v=KbYygB1Xuzs)
**Eingabebild** (vor jeder Umwandlung)
- Genau ein Objekt je Bild, neutraler Hintergrund (05:07).
- Einfarbig grau oder sanfter Ton, matt; kein Glanz, auch nicht in den Augen (05:07–06:10).
- Kamera leicht schräg von oben, keine Extremwinkel, nicht frontal/seitlich (05:39, 07:15).
- Kompakt und zusammenhängend, nichts Schwebendes; wenig Hinterschneidungen (offener Mund, Zunge) (06:10, 09:52).
- Unterseite/Aufstellung festlegen: steht, hängt, Wand (06:42).
- Düse und Schichthöhe in den Bild-Prompt schreiben (08:16–08:48).
**Größe**
- Zielgröße immer in den Bild-Prompt: 5–6 cm → kaum Details mit 0,4-mm-Düse, 15–20 cm → scharf (07:15, 19:17).
- Serie: nach dem ersten Modell Größe messen und in den Prompt übernehmen (16:41).
**Teilung**
- Abstehende Teile (Schild, Flügel) getrennt erzeugen und kleben: weniger Stützen, aber je Teil eine Umwandlung (16:41–17:43).
**Fehlersuche**
- 3D-Ergebnis ohne Farbe (grau) prüfen: Finger zählen, krumme Klingen, erfundene Rückseite, Details (17:43–18:46).
- Fehler lieber im Bild korrigieren (Nachbessern: Teil entfernen, mehr Textur) als nachträglich (10:24–11:27).
**Boden schneiden**
- Im Slicer „Auf Fläche legen“; KI-Böden sind uneben → unten plan schneiden bis zur soliden Fläche, Reste löschen (21:53–22:25).
**Kosten**
- Jede Umwandlung kostet Punkte/Geld; mit 2–3 Versuchen rechnen, deshalb Bild vorher prüfen (07:46, 13:02).
- Im Video widersprüchlich: 80 bzw. 24 Punkte je Erzeugung, Download zusätzlich (13:02, 16:10, 20:21); Drittquellen 2026: 2 Credits je Export – vor dem Bestätigen in MakerLab ablesen.
- Hohle Objekte (Vase, Helm, Maske) gelingen kaum (02:31). Der Original-Prompt aus der Videobeschreibung liegt nicht vor.

## Video 2 – Jedes Foto in 3D drucken (youtube.com/watch?v=XZR_ALfpAKo)
- Werkzeug: Primed3D (primed3d.3drevolution.net, 3D Revolution, kostenlos) → gerasterte 3MF; Modi CMY, WCMY, KCMY, WKCMY, 2 Filamente.
- Foto als freigestelltes PNG auflegen, sonst wird der Bildrand mitgemalt (03:06); Grund vorher als Verlauf einfärben (05:40).
- Schichthöhe 0,08 mm für ein sauberes Bild (0,06 mm hohe Qualität); 0,20 mm war im Video der Fehler (08:16). Muss zum Export passen.
- Größenordnung (Schädel-Oberteil, Größe ungenannt, 2 Düsen): 0,08 mm → 4 T 15 h 15 min, 3224 Filamentwechsel; 0,20 mm → 1 T 14 h, unsauber (08:16–08:47).
- Düsenzahl entscheidet: „mindestens zwei, eher fünf“; eine Düse erheblich länger, mehr Düsen erheblich kürzer (01:33, 09:17) – keine Zahlen dafür.
- Creator 5 Pro: höchstens 4 Farben gleichzeitig → nur KCMY/WCMY/CMY oder Schwarz-Weiß denkbar; nicht erprobt, in druckwerk nicht eingebaut; druck.py nimmt heute keine gemalte 3MF.
- Slicer: Bambu Studio „Farbmischung“ ab 2.5.3 (14.04.2026); OrcaSlicer „mixed filaments“ ab 2.5.0 Alpha (experimentell); Primed3D nennt Orca inkl. Flashforge-Variante kompatibel.

Auswertungen mit Fundstellen: `videos/ki-stl-bastlwastl.html`, `videos/foto-in-3d-bastlwastl.html`.


## Gratis-Weg direkt im Chat: `ki_lokal.py` (seit 15.11.2026)

`python3 werkzeug/ki_lokal.py bild.png --name figur --ziel-mm 120 --aus /tmp/figur`

- Freies Modell **TripoSR** (Tripo AI & Stability AI, MIT-Lizenz, 1,7 GB von Hugging Face). Läuft ohne Grafikkarte in der Claude-Sitzung
  (2 Kerne, 7 GB): Einrichten beim ersten Mal ~2 Min., danach Freistellen ~10 s, Form ~15 s, Netz ~50 s (Auflösung 320), `ki_rohling.py` ~50 s.
- Getestet am 15.11.2026 mit zwei Beispielbildern des Modells (gerenderter Roboter, Foto eines Stofftiers): erkennbar, dicht, mit Punktfarben,
  Rückseite plausibel geraten. Grenzen: Oberfläche wellig/treppig, dünne Teile (Antennen, Finger) fehlen, Gesichter weich. **Noch nichts davon gedruckt.**
- Die großen Modelle (TRELLIS.2, Hunyuan3D, Rodin, Meshy) brauchen eine Grafikkarte mit 16–24 GB und laufen hier nicht – dafür weiter fal.ai,
  MakerLab oder Meshy. `ki_lokal.py` ist der Entwurfs-Weg: prüfen, ob ein Bild taugt, bevor eine bezahlte Umwandlung läuft.
- Technik: `torchmcubes` wird durch scikit-image ersetzt, die Gewichte des Bild-Teils werden für neuere `transformers` umbenannt, vor `ki_rohling.py`
  ersetzt sich der Prozess selbst (`os.execv`), sonst reicht der Speicher nicht. Eingabe wie bei jeder Bild-KI: ein Objekt, neutraler Hintergrund.
- Offen: Hunyuan3D-2mini (deutlich besser) könnte mit Umbau auf 7 GB passen – ungetestet.

## Meshy „Multi-Color Print“ (aus dem Video von Der Druckt Schon Wieder, 15.11.2026)
- Meshy liefert direkt eine bemalte 3MF (Weg A ohne `textur_farben.py`); Farbanzahl in Meshy auf höchstens 4 stellen, Farbtöne lassen sich dort und im Slicer ändern.
- Ungetestet: ob `lese_3mf` in `druck.py` Meshys Farbcodierung liest – beim ersten echten File Werkzeugwechsel und Gramm je Kopf im Bericht prüfen.
- Größe: Meshy exportiert ohne Angabe 50 mm hoch; im Video wurde im Slicer etwa vierfach vergrößert, ohne dass das Netz grob wirkte. Skalieren vor `--bemalt` ist noch offen.
